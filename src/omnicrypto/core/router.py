import time
import asyncio
from collections import OrderedDict
from enum import StrEnum
from dataclasses import dataclass
from typing import Callable, Awaitable, Any
import httpx
from omnicrypto.core.schemas import OmniEnvelope, ResponseStatus
from omnicrypto.core.ratelimit import MultiWindowRateLimiter


class BreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ProviderCircuit:
    name: str
    failure_threshold: int = 3
    base_cooldown_sec: float = 30.0
    max_cooldown_sec: float = 600.0
    timeout_sec: float = 6.0
    cost_per_call: float = 1.0
    state: BreakerState = BreakerState.CLOSED
    consecutive_failures: int = 0
    opened_until: float = 0.0
    half_open_probe_in_flight: bool = False

    def try_acquire_execution_slot(self, now: float) -> bool:
        if self.state == BreakerState.CLOSED:
            return True
        if self.state == BreakerState.OPEN:
            if now >= self.opened_until:
                self.state = BreakerState.HALF_OPEN
                self.half_open_probe_in_flight = True
                return True
            return False
        if self.state == BreakerState.HALF_OPEN:
            # Strictly allow ONE probe request while HALF_OPEN
            if not self.half_open_probe_in_flight:
                self.half_open_probe_in_flight = True
                return True
            return False
        return False

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.state = BreakerState.CLOSED
        self.half_open_probe_in_flight = False

    def record_failure(self, now: float, retry_after_override: float | None = None) -> None:
        self.consecutive_failures += 1
        self.half_open_probe_in_flight = False
        if self.state == BreakerState.HALF_OPEN or self.consecutive_failures >= self.failure_threshold:
            self.state = BreakerState.OPEN
            if retry_after_override is not None:
                cooldown = min(retry_after_override, self.max_cooldown_sec)
            else:
                exp = max(0, self.consecutive_failures - self.failure_threshold)
                cooldown = min(self.base_cooldown_sec * (2 ** exp), self.max_cooldown_sec)
            self.opened_until = now + cooldown


class BoundedStaleCache:
    """
    Bounded LRU cache with separate `ttl_sec` (freshness) and `max_stale_sec` (hard expiration).
    Prevents unbounded memory growth and refuses to serve multi-day-old data as degraded.
    """

    def __init__(self, max_entries: int = 2048):
        self.max_entries = max_entries
        self._store: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> tuple[dict[str, Any] | None, str]:
        """Returns (entry, state: 'miss' | 'fresh' | 'stale')."""
        entry = self._store.get(key)
        if not entry:
            return None, "miss"
        now = time.monotonic()
        if now < entry["expires_at"]:
            self._store.move_to_end(key)
            return entry, "fresh"
        if now < entry["dead_at"]:
            return entry, "stale"
        # Beyond max_stale_sec -> hard evict
        del self._store[key]
        return None, "miss"

    def set(self, key: str, payload: Any, ttl_sec: float, max_stale_sec: float, source: str) -> None:
        now = time.monotonic()
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = {
            "payload": payload,
            "source": source,
            "created_at": now,
            "expires_at": now + ttl_sec,
            "dead_at": now + ttl_sec + max(0.0, max_stale_sec),
        }
        while len(self._store) > self.max_entries:
            self._store.popitem(last=False)


class WaterfallRouter:
    def __init__(self, cache: BoundedStaleCache, limiter: MultiWindowRateLimiter):
        self.cache = cache
        self.limiter = limiter
        self.circuits: dict[str, ProviderCircuit] = {}
        self._inflight_futures: dict[str, asyncio.Future[OmniEnvelope[Any]]] = {}

    def register_circuit(self, circuit: ProviderCircuit) -> None:
        self.circuits[circuit.name] = circuit

    @staticmethod
    def _parse_retry_after(response: httpx.Response) -> float | None:
        header = response.headers.get("Retry-After") or response.headers.get("retry-after")
        if not header:
            return None
        try:
            return max(0.0, float(header))
        except ValueError:
            return None

    async def execute(
        self,
        cache_key: str,
        ttl_sec: float,
        providers: list[tuple[str, Callable[[], Awaitable[Any]]]],
        max_stale_sec: float = 120.0,
    ) -> OmniEnvelope[Any]:
        # 1. Fast path: fresh cache hit
        entry, cache_state = self.cache.get(cache_key)
        if entry and cache_state == "fresh":
            age_ms = round((time.monotonic() - entry["created_at"]) * 1000)
            return OmniEnvelope(
                status=ResponseStatus.OK,
                data=entry["payload"],
                meta={
                    "source_used": entry["source"],
                    "cached": True,
                    "coalesced": False,
                    "cache_age_ms": age_ms,
                },
            )

        # 2. Single-flight: one waterfall task per key; every caller awaits it shielded,
        #    so a cancelled caller (e.g. a disconnected client) never cancels the others.
        task = self._inflight_futures.get(cache_key)
        coalesced = task is not None
        if task is None:
            task = asyncio.ensure_future(
                self._run_waterfall(cache_key, ttl_sec, max_stale_sec, providers)
            )
            self._inflight_futures[cache_key] = task
            task.add_done_callback(lambda t, k=cache_key: self._release(k, t))

        outcome = await asyncio.shield(task)
        if not coalesced:
            return outcome
        return OmniEnvelope(
            status=outcome.status,
            data=outcome.data,
            meta={**outcome.meta, "coalesced": True},
        )

    def _release(self, cache_key: str, task: "asyncio.Future[OmniEnvelope[Any]]") -> None:
        if self._inflight_futures.get(cache_key) is task:
            del self._inflight_futures[cache_key]
        if not task.cancelled():
            task.exception()  # mark retrieved; avoids "exception never retrieved" noise

    async def _run_waterfall(
        self,
        cache_key: str,
        ttl_sec: float,
        max_stale_sec: float,
        providers: list[tuple[str, Callable[[], Awaitable[Any]]]],
    ) -> OmniEnvelope[Any]:
        errors: list[str] = []

        for idx, (provider_name, fetcher) in enumerate(providers):
            circuit = self.circuits.setdefault(provider_name, ProviderCircuit(name=provider_name))
            now = time.monotonic()

            if not circuit.try_acquire_execution_slot(now):
                errors.append(f"{provider_name}: circuit_open")
                continue

            if not await self.limiter.acquire(provider_name, circuit.cost_per_call):
                # Release half-open probe flag if rate limiter blocked before network call
                if circuit.state == BreakerState.HALF_OPEN:
                    circuit.half_open_probe_in_flight = False
                errors.append(f"{provider_name}: rate_limit_exhausted")
                continue

            t0 = time.perf_counter()
            try:
                result = await asyncio.wait_for(fetcher(), timeout=circuit.timeout_sec)
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
                circuit.record_success()
                self.cache.set(cache_key, result, ttl_sec, max_stale_sec, source=provider_name)
                return OmniEnvelope(
                    status=ResponseStatus.OK,
                    data=result,
                    meta={
                        "source_used": provider_name,
                        "fallback_triggered": idx > 0,
                        "cached": False,
                        "coalesced": False,
                        "latency_ms": latency_ms,
                        "prior_attempts": errors,
                    },
                )

            except asyncio.TimeoutError:
                circuit.record_failure(time.monotonic())
                errors.append(f"{provider_name}: asyncio_timeout ({circuit.timeout_sec}s)")

            except httpx.TimeoutException as exc:
                circuit.record_failure(time.monotonic())
                errors.append(f"{provider_name}: httpx_timeout ({type(exc).__name__})")

            except httpx.TransportError as exc:
                # Catches ConnectError, ReadError, WriteError, RemoteProtocolError, PoolTimeout
                circuit.record_failure(time.monotonic())
                errors.append(f"{provider_name}: transport_error ({type(exc).__name__})")

            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                retry_after = self._parse_retry_after(exc.response)
                if code == 429:
                    circuit.consecutive_failures = max(
                        circuit.consecutive_failures, circuit.failure_threshold
                    )
                    circuit.record_failure(time.monotonic(), retry_after_override=retry_after)
                elif code in (403, 451):
                    circuit.consecutive_failures = circuit.failure_threshold
                    circuit.record_failure(
                        time.monotonic(), retry_after_override=circuit.max_cooldown_sec
                    )
                elif 500 <= code < 600:
                    circuit.record_failure(time.monotonic(), retry_after_override=retry_after)
                else:
                    # 400/404 client error: release half-open probe without tripping breaker
                    if circuit.state == BreakerState.HALF_OPEN:
                        circuit.half_open_probe_in_flight = False
                errors.append(f"{provider_name}: HTTP_{code}")

            except Exception as exc:
                if circuit.state == BreakerState.HALF_OPEN:
                    circuit.half_open_probe_in_flight = False
                errors.append(f"{provider_name}: {type(exc).__name__} ({exc})")

        # Stale-While-Revalidate fallback (only if within max_stale_sec)
        stale_entry, state = self.cache.get(cache_key)
        if stale_entry and state == "stale":
            stale_age_ms = round((time.monotonic() - stale_entry["created_at"]) * 1000)
            return OmniEnvelope(
                status=ResponseStatus.DEGRADED,
                data=stale_entry["payload"],
                meta={
                    "source_used": stale_entry["source"],
                    "cached": True,
                    "stale": True,
                    "coalesced": False,
                    "stale_age_ms": stale_age_ms,
                    "errors": errors,
                },
            )

        return OmniEnvelope(
            status=ResponseStatus.ERROR,
            data=None,
            meta={"coalesced": False, "errors": errors},
        )

