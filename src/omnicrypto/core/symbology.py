import re
import httpx
from omnicrypto.core.router import WaterfallRouter
from omnicrypto.core.schemas import (
    CandidateToken,
    AmbiguousAssetResponse,
    OmniEnvelope,
    ResponseStatus,
)

EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOL_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

SUPPORTED_EVM_CHAINS: dict[str, str] = {
    "ethereum": "1",
    "eth": "1",
    "bsc": "56",
    "arbitrum": "42161",
    "base": "8453",
    "polygon": "137",
    "optimism": "10",
    "avalanche": "43114",
}

CANONICAL_MAJORS: dict[str, dict[str, str]] = {
    "BTC": {
        "coingecko_id": "bitcoin",
        "coinpaprika_id": "btc-bitcoin",
        "ccxt_usd": "BTC/USD",
        "pyth_id": "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    },
    "ETH": {
        "coingecko_id": "ethereum",
        "coinpaprika_id": "eth-ethereum",
        "ccxt_usd": "ETH/USD",
        "pyth_id": "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace",
    },
    "SOL": {
        "coingecko_id": "solana",
        "coinpaprika_id": "sol-solana",
        "ccxt_usd": "SOL/USD",
        "pyth_id": "0xef0d8b6fda2ceba41da15d4095d1da392a0d2f8ed0c6c7bc0f4cfac8c280b56d",
    },
}


class SymbologyResolver:
    def __init__(self, http_client: httpx.AsyncClient, router: WaterfallRouter):
        self.http = http_client
        self.router = router

    @staticmethod
    def is_evm_address(address: str) -> bool:
        return bool(EVM_ADDRESS_RE.match(address.strip()))

    @staticmethod
    def is_solana_address(address: str) -> bool:
        s = address.strip()
        return not s.startswith("0x") and bool(SOL_ADDRESS_RE.match(s))

    @classmethod
    def is_explicit_contract(cls, address: str) -> bool:
        return cls.is_evm_address(address) or cls.is_solana_address(address)

    async def disambiguate_onchain_symbol(self, symbol: str) -> OmniEnvelope[AmbiguousAssetResponse]:
        """Routes disambiguation through WaterfallRouter so it inherits rate limits, cache & circuit breaker."""
        clean_sym = symbol.strip().upper()

        async def _fetch_candidates() -> AmbiguousAssetResponse:
            resp = await self.http.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": clean_sym},
            )
            resp.raise_for_status()
            pairs = resp.json().get("pairs") or []
            pairs.sort(
                key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0.0),
                reverse=True,
            )

            seen: set[tuple[str, str]] = set()
            candidates: list[CandidateToken] = []
            for p in pairs:
                base = p.get("baseToken") or {}
                chain_id = p.get("chainId", "unknown")
                addr = base.get("address", "")
                if not addr or (chain_id, addr.lower()) in seen:
                    continue
                if base.get("symbol", "").upper() == clean_sym:
                    seen.add((chain_id, addr.lower()))
                    candidates.append(
                        CandidateToken(
                            symbol=base.get("symbol", clean_sym),
                            name=base.get("name", ""),
                            chain=chain_id,
                            contract_address=addr,
                            liquidity_usd=float((p.get("liquidity") or {}).get("usd") or 0.0),
                            volume_24h_usd=float((p.get("volume") or {}).get("h24") or 0.0),
                        )
                    )
                if len(candidates) >= 8:
                    break
            return AmbiguousAssetResponse(query=symbol, candidates=candidates)

        env = await self.router.execute(
            cache_key=f"disambiguate:{clean_sym}",
            ttl_sec=300,
            max_stale_sec=600,
            providers=[("dexscreener", _fetch_candidates)],
        )
        if env.status in (ResponseStatus.OK, ResponseStatus.DEGRADED) and env.data:
            return OmniEnvelope(
                status=ResponseStatus.AMBIGUOUS,
                data=env.data,
                meta=env.meta,
            )
        # Fail closed even if DexScreener is down during disambiguation
        return OmniEnvelope(
            status=ResponseStatus.AMBIGUOUS,
            data=AmbiguousAssetResponse(
                query=symbol,
                warning="AMBIGUOUS_SYMBOL_AND_DISAMBIGUATION_UNAVAILABLE: Provide explicit chain and contract_address.",
                candidates=[],
            ),
            meta=env.meta,
        )

