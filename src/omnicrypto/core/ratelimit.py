import time
import asyncio
import datetime
import aiosqlite
from dataclasses import dataclass, field


@dataclass
class WindowBucket:
    capacity: float
    refill_period_sec: float
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None:
        self.tokens = self.capacity

    def projected_tokens(self, now: float) -> float:
        elapsed = max(0.0, now - self.last_refill)
        return min(self.capacity, self.tokens + (elapsed / self.refill_period_sec) * self.capacity)

    def consume(self, cost: float, now: float) -> None:
        self.tokens = self.projected_tokens(now) - cost
        self.last_refill = now


class MultiWindowRateLimiter:
    """
    Enforces in-memory sub-hour token buckets (RPS/RPM) and SQLite-persisted
    calendar-month credit budgets that survive daemon restarts.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._buckets: dict[str, list[WindowBucket]] = {}
        self._monthly_limits: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._db: aiosqlite.Connection | None = None
        self._db_init_lock = asyncio.Lock()

    async def init_db(self) -> None:
        if self._db is not None:
            return
        async with self._db_init_lock:
            if self._db is not None:
                return
            conn = aiosqlite.connect(self.db_path)
            # Daemonize the worker thread before it starts, so a missed close()
            # can never block interpreter exit.
            conn._thread.daemon = True
            self._db = await conn
            await self._db.execute(
                """
                CREATE TABLE IF NOT EXISTS monthly_quotas (
                    provider TEXT NOT NULL,
                    year_month TEXT NOT NULL,
                    used_credits REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (provider, year_month)
                )
                """
            )
            await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    def register_provider(
        self,
        provider: str,
        rps: float | None = None,
        rpm: float | None = None,
        monthly_credits: float | None = None,
    ) -> None:
        windows: list[WindowBucket] = []
        if rps:
            windows.append(WindowBucket(capacity=rps, refill_period_sec=1.0))
        if rpm:
            windows.append(WindowBucket(capacity=rpm, refill_period_sec=60.0))
        self._buckets[provider] = windows
        if monthly_credits is not None:
            self._monthly_limits[provider] = monthly_credits
        self._locks[provider] = asyncio.Lock()

    @staticmethod
    def _current_year_month() -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m")

    async def acquire(self, provider: str, cost: float = 1.0) -> bool:
        if provider not in self._locks:
            return True
        if provider in self._monthly_limits:
            await self.init_db()

        async with self._locks[provider]:
            now = time.monotonic()
            windows = self._buckets.get(provider, [])

            # 1. Check short-window token buckets
            for w in windows:
                if w.projected_tokens(now) < cost:
                    return False

            # 2. Check persistent monthly budget if configured
            monthly_cap = self._monthly_limits.get(provider)
            ym = self._current_year_month()
            if monthly_cap is not None:
                assert self._db is not None
                async with self._db.execute(
                    "SELECT used_credits FROM monthly_quotas WHERE provider = ? AND year_month = ?",
                    (provider, ym),
                ) as cursor:
                    row = await cursor.fetchone()
                    used = float(row[0]) if row else 0.0
                if used + cost > monthly_cap:
                    return False

            # 3. Deduct from short windows and commit monthly usage
            for w in windows:
                w.consume(cost, now)

            if monthly_cap is not None:
                await self._db.execute(
                    """
                    INSERT INTO monthly_quotas (provider, year_month, used_credits)
                    VALUES (?, ?, ?)
                    ON CONFLICT(provider, year_month)
                    DO UPDATE SET used_credits = used_credits + excluded.used_credits
                    """,
                    (provider, ym, cost),
                )
                await self._db.commit()

            return True

