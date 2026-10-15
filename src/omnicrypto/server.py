import hmac
import os
import asyncio
from contextlib import asynccontextmanager
import httpx
import ccxt.async_support as ccxt
from fastmcp import FastMCP
from starlette.middleware import Middleware
from omnicrypto.core.ratelimit import MultiWindowRateLimiter
from omnicrypto.core.router import WaterfallRouter, BoundedStaleCache
from omnicrypto.core.schemas import (
    OmniEnvelope,
    ResponseStatus,
    MarketOverviewPayload,
    FieldProvenance,
    PriceMethodology,
    SecurityAuditPayload,
    SecurityVerdict,
)
from omnicrypto import security
from omnicrypto.core.symbology import (
    SymbologyResolver,
    CANONICAL_MAJORS,
    SUPPORTED_EVM_CHAINS,
)

DB_PATH = os.getenv("OMNICRYPTO_DB_PATH", "omnicrypto_state.db")

http_client = httpx.AsyncClient(
    http2=True,
    headers={"User-Agent": "OmniCrypto-MCP-Gateway/0.2"},
    timeout=6.0,
)
cache = BoundedStaleCache(max_entries=2048)
limiter = MultiWindowRateLimiter(db_path=DB_PATH)
router = WaterfallRouter(cache=cache, limiter=limiter)
resolver = SymbologyResolver(http_client=http_client, router=router)

limiter.register_provider("coingecko", rpm=25.0)
limiter.register_provider("coinpaprika", rpm=30.0, monthly_credits=20_000.0)
limiter.register_provider("pyth_hermes", rps=10.0)
limiter.register_provider("dexscreener", rpm=280.0)
limiter.register_provider("coinbase_ccxt", rps=8.0)
limiter.register_provider("kraken_ccxt", rps=5.0)
limiter.register_provider("goplus", rpm=30.0)
limiter.register_provider("honeypot_is", rpm=30.0)
limiter.register_provider("rugcheck", rpm=30.0)

coinbase = ccxt.coinbase({"enableRateLimit": False, "timeout": 5000})
kraken = ccxt.kraken({"enableRateLimit": False, "timeout": 5000})


@asynccontextmanager
async def gateway_lifespan(server: FastMCP):
    """Preloads CCXT market maps outside tool timeouts and cleanly closes sockets on exit."""
    await limiter.init_db()
    await asyncio.gather(
        kraken.load_markets(),
        coinbase.load_markets(),
        return_exceptions=True,
    )
    try:
        yield
    finally:
        await asyncio.gather(
            kraken.close(),
            coinbase.close(),
            http_client.aclose(),
            limiter.close(),
            return_exceptions=True,
        )


mcp = FastMCP("OmniCrypto-Gateway", lifespan=gateway_lifespan)


async def _fetch_pyth_oracle_field(feed_id: str) -> FieldProvenance:
    """Fetches real-time Pyth Hermes oracle price to cross-check CEX spot."""
    r = await http_client.get(
        "https://hermes.pyth.network/v2/updates/price/latest",
        params={"ids[]": feed_id},
    )
    r.raise_for_status()
    parsed = (r.json().get("parsed") or [{}])[0].get("price") or {}
    raw_price = float(parsed["price"]) * (10 ** int(parsed["expo"]))
    return FieldProvenance(
        value=round(raw_price, 6),
        source="pyth_hermes",
        methodology=PriceMethodology.ORACLE_CONFIDENCE_INTERVAL,
        quote_currency="USD",
    )


@mcp.tool()
async def crypto_market_overview(
    symbol_or_address: str,
    chain: str | None = None,
) -> dict:
    """
    Fetch spot price, oracle price, 24h volume, market cap, and FDV with explicit field provenance.
    Pass `chain` + `symbol_or_address` (contract address) for non-major tokens.
    """
    query = symbol_or_address.strip()
    upper = query.upper()

    if upper not in CANONICAL_MAJORS and not resolver.is_explicit_contract(query):
        ambiguous_env = await resolver.disambiguate_onchain_symbol(query)
        return ambiguous_env.model_dump()

    if upper in CANONICAL_MAJORS:
        meta_ids = CANONICAL_MAJORS[upper]
        pair_symbol = meta_ids["ccxt_usd"]

        async def fetch_coingecko() -> MarketOverviewPayload:
            r = await http_client.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={"vs_currency": "usd", "ids": meta_ids["coingecko_id"]},
            )
            r.raise_for_status()
            row = r.json()[0]
            return MarketOverviewPayload(
                canonical_id=meta_ids["coingecko_id"],
                symbol=upper,
                price=FieldProvenance(
                    value=row.get("current_price"),
                    source="coingecko",
                    methodology=PriceMethodology.VWAP_AGGREGATE,
                    quote_currency="USD",
                ),
                market_cap=FieldProvenance(
                    value=row.get("market_cap"), source="coingecko", quote_currency="USD"
                ),
                fdv=FieldProvenance(
                    value=row.get("fully_diluted_valuation"), source="coingecko", quote_currency="USD"
                ),
                volume_24h=FieldProvenance(
                    value=row.get("total_volume"),
                    source="coingecko",
                    methodology="rolling_24h_global_vwap_volume",
                    quote_currency="USD",
                ),
                change_24h_pct=FieldProvenance(
                    value=row.get("price_change_percentage_24h"),
                    source="coingecko",
                    methodology="rolling_24h_pct_change",
                ),
            )

        async def fetch_coinpaprika() -> MarketOverviewPayload:
            r = await http_client.get(
                f"https://api.coinpaprika.com/v1/tickers/{meta_ids['coinpaprika_id']}"
            )
            r.raise_for_status()
            row = r.json()
            usd = row["quotes"]["USD"]
            return MarketOverviewPayload(
                canonical_id=meta_ids["coinpaprika_id"],
                symbol=upper,
                price=FieldProvenance(
                    value=usd.get("price"),
                    source="coinpaprika",
                    methodology=PriceMethodology.VWAP_AGGREGATE,
                    quote_currency="USD",
                ),
                market_cap=FieldProvenance(
                    value=usd.get("market_cap"), source="coinpaprika", quote_currency="USD"
                ),
                fdv=FieldProvenance(
                    value=None,
                    source="coinpaprika",
                    null_reason="CoinPaprika v1 ticker does not expose unlocked FDV",
                ),
                volume_24h=FieldProvenance(
                    value=usd.get("volume_24h"),
                    source="coinpaprika",
                    methodology="rolling_24h_global_volume",
                    quote_currency="USD",
                ),
                change_24h_pct=FieldProvenance(
                    value=usd.get("percent_change_24h"),
                    source="coinpaprika",
                    methodology="rolling_24h_pct_change",
                ),
            )

        async def fetch_coinbase_spot() -> MarketOverviewPayload:
            ticker = await coinbase.fetch_ticker(pair_symbol)
            return MarketOverviewPayload(
                canonical_id=meta_ids["coingecko_id"],
                symbol=upper,
                price=FieldProvenance(
                    value=ticker.get("last"),
                    source="coinbase",
                    methodology=PriceMethodology.CEX_SPOT_LAST,
                    quote_currency="USD",
                ),
                market_cap=FieldProvenance(
                    value=None,
                    null_reason="CEX spot ticker (Coinbase) does not track circulating supply",
                ),
                fdv=FieldProvenance(
                    value=None,
                    null_reason="CEX spot ticker (Coinbase) does not track total supply",
                ),
                volume_24h=FieldProvenance(
                    value=ticker.get("quoteVolume"),
                    source="coinbase",
                    methodology=f"single_exchange_pair_24h_volume ({pair_symbol})",
                    quote_currency="USD",
                ),
                change_24h_pct=FieldProvenance(
                    value=ticker.get("percentage"),
                    source="coinbase",
                    methodology="rolling_24h_exchange_pair_pct_change",
                ),
            )

        async def fetch_kraken_plus_pyth() -> MarketOverviewPayload:
            ticker_task = kraken.fetch_ticker(pair_symbol)
            pyth_task = _fetch_pyth_oracle_field(meta_ids["pyth_id"])
            ticker, oracle_field = await asyncio.gather(
                ticker_task, pyth_task, return_exceptions=True
            )
            if isinstance(ticker, BaseException):
                raise ticker
            resolved_oracle = (
                oracle_field if isinstance(oracle_field, FieldProvenance) else None
            )
            return MarketOverviewPayload(
                canonical_id=meta_ids["coingecko_id"],
                symbol=upper,
                price=FieldProvenance(
                    value=ticker.get("last"),
                    source="kraken",
                    methodology=PriceMethodology.CEX_SPOT_LAST,
                    quote_currency="USD",
                ),
                oracle_price=resolved_oracle,
                market_cap=FieldProvenance(
                    value=None,
                    null_reason="CEX spot ticker (Kraken) does not track circulating supply",
                ),
                fdv=FieldProvenance(
                    value=None,
                    null_reason="CEX spot ticker (Kraken) does not track total supply",
                ),
                volume_24h=FieldProvenance(
                    value=ticker.get("quoteVolume"),
                    source="kraken",
                    methodology=f"single_exchange_pair_24h_volume ({pair_symbol})",
                    quote_currency="USD",
                ),
                change_24h_pct=FieldProvenance(
                    value=ticker.get("percentage"),
                    source="kraken",
                    methodology="change_since_0000_utc_open (Kraken open is midnight UTC, not rolling 24h)",
                ),
            )

        envelope = await router.execute(
            cache_key=f"mkt_overview:{upper}",
            ttl_sec=15,
            max_stale_sec=60,
            providers=[
                ("coingecko", fetch_coingecko),
                ("coinpaprika", fetch_coinpaprika),
                ("coinbase_ccxt", fetch_coinbase_spot),
                ("kraken_ccxt", fetch_kraken_plus_pyth),
            ],
        )
        return envelope.model_dump()

    # Explicit Contract Address Path -> DexScreener
    async def fetch_dexscreener_contract() -> MarketOverviewPayload:
        r = await http_client.get(f"https://api.dexscreener.com/latest/dex/tokens/{query}")
        r.raise_for_status()
        pairs = r.json().get("pairs") or []
        if chain:
            pairs = [p for p in pairs if p.get("chainId", "").lower() == chain.lower()]
        if not pairs:
            raise ValueError(f"No indexed DEX pools found for contract {query}")
        pairs.sort(key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0.0), reverse=True)
        top = pairs[0]
        base = top.get("baseToken", {})
        return MarketOverviewPayload(
            canonical_id=f"{top.get('chainId')}:{base.get('address')}",
            symbol=base.get("symbol", "UNKNOWN"),
            price=FieldProvenance(
                value=float(top["priceUsd"]) if top.get("priceUsd") else None,
                source=f"dexscreener:{top.get('dexId')}",
                methodology=PriceMethodology.DEX_POOL_SPOT,
                quote_currency="USD",
            ),
            market_cap=FieldProvenance(value=top.get("marketCap"), source="dexscreener", quote_currency="USD"),
            fdv=FieldProvenance(value=top.get("fdv"), source="dexscreener", quote_currency="USD"),
            volume_24h=FieldProvenance(
                value=(top.get("volume") or {}).get("h24"),
                source=f"dexscreener:{top.get('dexId')}",
                methodology=f"single_pool_24h_volume ({top.get('pairAddress')})",
                quote_currency="USD",
            ),
            change_24h_pct=FieldProvenance(
                value=(top.get("priceChange") or {}).get("h24"),
                source="dexscreener",
                methodology="rolling_24h_pool_pct_change",
            ),
        )

    envelope = await router.execute(
        cache_key=f"mkt_contract:{chain or 'any'}:{query.lower()}",
        ttl_sec=10,
        max_stale_sec=45,
        providers=[("dexscreener", fetch_dexscreener_contract)],
    )
    return envelope.model_dump()


@mcp.tool()
async def crypto_security_audit(chain: str, contract_address: str) -> dict:
    """
    Fail-closed pre-execution token security gate.
    Never serves stale data (max_stale_sec=0).
    Always returns `verdict`: 'pass' | 'unsafe' | 'unknown' and `can_trade`: bool.
    """
    addr = contract_address.strip()
    chain_lower = chain.strip().lower()

    # 1. Reject bare symbols via router-protected disambiguation
    if not resolver.is_explicit_contract(addr):
        ambiguous_env = await resolver.disambiguate_onchain_symbol(addr)
        return ambiguous_env.model_dump()

    # 2. Enforce strict chain whitelist & address format cross-check
    if chain_lower in ("solana", "sol"):
        if not resolver.is_solana_address(addr):
            return OmniEnvelope(
                status=ResponseStatus.ERROR,
                data=SecurityAuditPayload(
                    chain=chain_lower,
                    contract_address=addr,
                    verdict=SecurityVerdict.UNKNOWN,
                    can_trade=False,
                    reasons=["ADDRESS_CHAIN_MISMATCH: EVM 0x address passed with chain='solana'"],
                ),
            ).model_dump()

        async def fetch_rugcheck() -> SecurityAuditPayload:
            r = await http_client.get(f"https://api.rugcheck.xyz/v1/tokens/{addr}/report/summary")
            r.raise_for_status()
            body = r.json()
            risks = body.get("risks") or []
            score = int(body.get("score") or 0)
            danger_reasons = [
                f"{rk.get('name')}: {rk.get('description')}"
                for rk in risks
                if rk.get("level") in ("danger", "warn")
            ]
            is_unsafe = score > 500 or any(rk.get("level") == "danger" for rk in risks)
            verdict = SecurityVerdict.UNSAFE if is_unsafe else SecurityVerdict.PASS
            return SecurityAuditPayload(
                chain="solana",
                contract_address=addr,
                verdict=verdict,
                can_trade=(verdict == SecurityVerdict.PASS),
                reasons=danger_reasons,
                providers_checked=["rugcheck"],
            )

        env = await router.execute(
            cache_key=f"sec:sol:{addr}",
            ttl_sec=300,
            max_stale_sec=0,  # Never serve stale security audits
            providers=[("rugcheck", fetch_rugcheck)],
        )
        if env.status != ResponseStatus.OK or env.data is None:
            return OmniEnvelope(
                status=ResponseStatus.ERROR,
                data=SecurityAuditPayload(
                    chain="solana",
                    contract_address=addr,
                    verdict=SecurityVerdict.UNKNOWN,
                    can_trade=False,
                    reasons=["SECURITY_PROVIDER_UNAVAILABLE: Fail-closed — do not trade"],
                ),
                meta=env.meta,
            ).model_dump()
        return env.model_dump()

    # 3. EVM Chain Whitelist Check
    if chain_lower not in SUPPORTED_EVM_CHAINS:
        return OmniEnvelope(
            status=ResponseStatus.ERROR,
            data=SecurityAuditPayload(
                chain=chain_lower,
                contract_address=addr,
                verdict=SecurityVerdict.UNKNOWN,
                can_trade=False,
                reasons=[
                    f"UNSUPPORTED_CHAIN: '{chain}' not in supported whitelist {list(SUPPORTED_EVM_CHAINS.keys()) + ['solana']}"
                ],
            ),
        ).model_dump()

    if not resolver.is_evm_address(addr):
        return OmniEnvelope(
            status=ResponseStatus.ERROR,
            data=SecurityAuditPayload(
                chain=chain_lower,
                contract_address=addr,
                verdict=SecurityVerdict.UNKNOWN,
                can_trade=False,
                reasons=["ADDRESS_CHAIN_MISMATCH: Non-EVM address passed for EVM chain"],
            ),
        ).model_dump()

    chain_id = SUPPORTED_EVM_CHAINS[chain_lower]
    addr_lower = addr.lower()

    async def fetch_goplus() -> SecurityAuditPayload:
        r = await http_client.get(
            f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}",
            params={"contract_addresses": addr_lower},
        )
        r.raise_for_status()
        record = (r.json().get("result") or {}).get(addr_lower)
        if not record:
            raise ValueError("Contract not indexed by GoPlus")
        return security.evaluate_goplus(chain_lower, addr_lower, record)

    async def fetch_honeypot_is() -> SecurityAuditPayload:
        r = await http_client.get(
            "https://api.honeypot.is/v2/IsHoneypot",
            params={"address": addr_lower, "chainID": chain_id},
        )
        r.raise_for_status()
        return security.evaluate_honeypot_is(chain_lower, addr_lower, r.json())

    # Both providers go through the router so each is rate-limited and circuit-broken.
    gp_env, hp_env = await asyncio.gather(
        router.execute(
            cache_key=f"sec:goplus:{chain_id}:{addr_lower}",
            ttl_sec=300,
            max_stale_sec=0,
            providers=[("goplus", fetch_goplus)],
        ),
        router.execute(
            cache_key=f"sec:hpis:{chain_id}:{addr_lower}",
            ttl_sec=300,
            max_stale_sec=0,
            providers=[("honeypot_is", fetch_honeypot_is)],
        ),
    )

    results: list[SecurityAuditPayload] = []
    failures: list[str] = []
    for name, env in (("goplus", gp_env), ("honeypot.is", hp_env)):
        if env.status == ResponseStatus.OK and env.data is not None:
            results.append(env.data)
        else:
            failures.append(f"{name}: {', '.join(env.meta.get('errors', [])) or env.status}")

    merged = security.merge(
        chain_lower, addr_lower, results, expected=["goplus", "honeypot.is"], failures=failures
    )
    status = ResponseStatus.OK if results else ResponseStatus.ERROR
    return OmniEnvelope(
        status=status,
        data=merged,
        meta={"goplus_meta": gp_env.meta, "honeypot_is_meta": hp_env.meta},
    ).model_dump()


class BearerAuthMiddleware:
    """Pure-ASGI bearer check. Constant-time compare; every HTTP request must carry the token."""

    def __init__(self, app, token: str):
        self.app = app
        self._expected = f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            supplied = dict(scope.get("headers") or []).get(b"authorization", b"")
            if not hmac.compare_digest(supplied, self._expected):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json"),
                                        (b"www-authenticate", b"Bearer")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def build_app(bearer_token: str = ""):
    """HTTP app; when a token is given, every request must present it."""
    middleware = [Middleware(BearerAuthMiddleware, token=bearer_token)] if bearer_token else None
    return mcp.http_app(path="/mcp", middleware=middleware)


def main() -> None:
    import uvicorn

    host = os.getenv("OMNICRYPTO_HOST", "127.0.0.1")
    port = int(os.getenv("OMNICRYPTO_PORT", "8900"))
    bearer_token = os.getenv("OMNICRYPTO_BEARER_TOKEN", "").strip()

    if host not in ("127.0.0.1", "localhost", "::1") and not bearer_token:
        raise RuntimeError(
            f"Refusing to bind to non-loopback host '{host}' without OMNICRYPTO_BEARER_TOKEN set."
        )
    if bearer_token and len(bearer_token) < 24:
        raise RuntimeError("OMNICRYPTO_BEARER_TOKEN must be at least 24 characters.")

    uvicorn.run(build_app(bearer_token), host=host, port=port)


if __name__ == "__main__":
    main()
