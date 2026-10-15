import asyncio
import httpx
import pytest
import respx
from omnicrypto.core.ratelimit import MultiWindowRateLimiter
from omnicrypto.core.router import (
    WaterfallRouter,
    BoundedStaleCache,
    ProviderCircuit,
    BreakerState,
)
from omnicrypto.core.schemas import ResponseStatus, SecurityVerdict
from omnicrypto.server import crypto_security_audit


@pytest.mark.asyncio
async def test_single_flight_coalesces_failure_without_amplification():
    """
    20 concurrent callers hitting a failing waterfall must only trigger ONE
    attempt per provider, share the error result, and clean up _inflight_futures.
    """
    cache = BoundedStaleCache()
    limiter = MultiWindowRateLimiter()
    router = WaterfallRouter(cache=cache, limiter=limiter)

    primary_calls = 0
    fallback_calls = 0

    async def failing_primary():
        nonlocal primary_calls
        primary_calls += 1
        await asyncio.sleep(0.05)
        raise httpx.ConnectError("Connection refused")

    async def failing_fallback():
        nonlocal fallback_calls
        fallback_calls += 1
        await asyncio.sleep(0.05)
        raise httpx.ConnectError("Backup down")

    tasks = [
        router.execute(
            cache_key="cold_key_fail",
            ttl_sec=10,
            providers=[("p1", failing_primary), ("p2", failing_fallback)],
        )
        for _ in range(20)
    ]
    results = await asyncio.gather(*tasks)

    assert primary_calls == 1, f"Expected 1 primary call, got {primary_calls}"
    assert fallback_calls == 1, f"Expected 1 fallback call, got {fallback_calls}"
    assert all(r.status == ResponseStatus.ERROR for r in results)
    assert sum(1 for r in results if r.meta.get("coalesced") is True) == 19
    assert len(router._inflight_futures) == 0, "Memory leak: _inflight_futures not cleaned up"


@pytest.mark.asyncio
async def test_connect_error_and_timeout_trip_circuit_breaker():
    """ConnectError and TimeoutError must increment failures and open the circuit."""
    cache = BoundedStaleCache()
    limiter = MultiWindowRateLimiter()
    router = WaterfallRouter(cache=cache, limiter=limiter)
    router.register_circuit(
        ProviderCircuit(name="flaky_rpc", failure_threshold=2, base_cooldown_sec=60.0, timeout_sec=0.05)
    )

    async def conn_fail():
        raise httpx.ConnectError("DNS lookup failed")

    async def hang_forever():
        await asyncio.sleep(5.0)

    await router.execute("k1", 10, [("flaky_rpc", conn_fail)])
    assert router.circuits["flaky_rpc"].state == BreakerState.CLOSED

    await router.execute("k2", 10, [("flaky_rpc", hang_forever)])
    assert router.circuits["flaky_rpc"].state == BreakerState.OPEN


@pytest.mark.asyncio
async def test_half_open_allows_strictly_one_concurrent_probe():
    """When cooldown expires, only 1 concurrent caller may probe HALF_OPEN; others skip immediately."""
    cache = BoundedStaleCache()
    limiter = MultiWindowRateLimiter()
    router = WaterfallRouter(cache=cache, limiter=limiter)
    circuit = ProviderCircuit(name="probed_api", failure_threshold=1, base_cooldown_sec=0.05)
    router.register_circuit(circuit)

    async def fail_once():
        raise httpx.ConnectError("boom")

    await router.execute("trip", 10, [("probed_api", fail_once)])
    assert circuit.state == BreakerState.OPEN

    await asyncio.sleep(0.06)  # Cooldown elapsed -> ready for HALF_OPEN

    probe_calls = 0
    fallback_calls = 0

    async def slow_probe():
        nonlocal probe_calls
        probe_calls += 1
        await asyncio.sleep(0.08)
        return {"ok": True}

    async def fast_fallback():
        nonlocal fallback_calls
        fallback_calls += 1
        return {"fallback": True}

    # Fire 5 DIFFERENT cache keys concurrently so single-flight doesn't coalesce them
    results = await asyncio.gather(
        *[
            router.execute(
                f"key_{i}",
                10,
                [("probed_api", slow_probe), ("backup", fast_fallback)],
            )
            for i in range(5)
        ]
    )

    assert probe_calls == 1, f"Expected strictly 1 half-open probe, got {probe_calls}"
    assert fallback_calls == 4, f"Expected 4 callers to spill over to backup, got {fallback_calls}"
    assert circuit.state == BreakerState.CLOSED


@pytest.mark.asyncio
async def test_max_stale_sec_evicts_ancient_cache_instead_of_serving_degraded():
    """Stale data within max_stale_sec returns DEGRADED; beyond max_stale_sec returns ERROR."""
    cache = BoundedStaleCache()
    limiter = MultiWindowRateLimiter()
    router = WaterfallRouter(cache=cache, limiter=limiter)

    async def ok_provider():
        return {"price": 100.0}

    async def dead_provider():
        raise httpx.ConnectError("offline")

    # Seed cache with 0.05s fresh TTL and 0.10s max_stale_sec
    res1 = await router.execute("btc", ttl_sec=0.05, max_stale_sec=0.10, providers=[("p1", ok_provider)])
    assert res1.status == ResponseStatus.OK

    # Wait 0.07s -> stale but within max_stale_sec (0.05 + 0.10 = 0.15s)
    await asyncio.sleep(0.07)
    res2 = await router.execute("btc", ttl_sec=0.05, max_stale_sec=0.10, providers=[("p1", dead_provider)])
    assert res2.status == ResponseStatus.DEGRADED
    assert res2.data == {"price": 100.0}

    # Wait another 0.12s -> past dead_at (0.19s > 0.15s) -> must refuse stale data
    await asyncio.sleep(0.12)
    res3 = await router.execute("btc", ttl_sec=0.05, max_stale_sec=0.10, providers=[("p1", dead_provider)])
    assert res3.status == ResponseStatus.ERROR
    assert res3.data is None


@pytest.mark.asyncio
async def test_sqlite_monthly_quota_persists_across_restarts(tmp_path):
    """Monthly credit deductions must persist in SQLite across limiter instances."""
    db_file = str(tmp_path / "quotas.db")

    limiter1 = MultiWindowRateLimiter(db_path=db_file)
    limiter1.register_provider("coinpaprika", monthly_credits=2.0)
    assert await limiter1.acquire("coinpaprika", cost=1.0) is True
    assert await limiter1.acquire("coinpaprika", cost=1.0) is True
    assert await limiter1.acquire("coinpaprika", cost=1.0) is False
    await limiter1.close()

    # Simulate process restart with new MultiWindowRateLimiter instance pointing to same DB
    limiter2 = MultiWindowRateLimiter(db_path=db_file)
    limiter2.register_provider("coinpaprika", monthly_credits=2.0)
    assert await limiter2.acquire("coinpaprika", cost=1.0) is False, "Monthly quota reset on restart!"
    await limiter2.close()


@pytest.mark.asyncio
@respx.mock
async def test_security_audit_fails_closed_on_chain_mismatch_and_outage():
    """
    1. Passing EVM 0x address with chain='solana' fails closed immediately.
    2. Passing unknown chain fails closed immediately.
    3. Upstream 500 on both GoPlus and Honeypot.is returns verdict='unknown', can_trade=False.
    """
    evm_addr = "0x6982508145454ce325ddbe47a25d4ec3d2311933"

    # 1. EVM address on Solana
    mismatch = await crypto_security_audit(chain="solana", contract_address=evm_addr)
    assert mismatch["data"]["verdict"] == SecurityVerdict.UNKNOWN
    assert mismatch["data"]["can_trade"] is False

    # 2. Unknown chain
    bad_chain = await crypto_security_audit(chain="fantom_testnet", contract_address=evm_addr)
    assert bad_chain["data"]["verdict"] == SecurityVerdict.UNKNOWN
    assert bad_chain["data"]["can_trade"] is False

    # 3. Both EVM security providers return HTTP 502
    respx.get("https://api.gopluslabs.io/api/v1/token_security/1").mock(
        return_value=httpx.Response(502)
    )
    respx.get("https://api.honeypot.is/v2/IsHoneypot").mock(
        return_value=httpx.Response(502)
    )

    outage = await crypto_security_audit(chain="ethereum", contract_address=evm_addr)
    assert outage["status"] == ResponseStatus.ERROR
    assert outage["data"]["verdict"] == SecurityVerdict.UNKNOWN
    assert outage["data"]["can_trade"] is False

