from enum import StrEnum
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PriceMethodology(StrEnum):
    ORACLE_CONFIDENCE_INTERVAL = "pyth_oracle_price"
    VWAP_AGGREGATE = "vwap_global_aggregate"
    CEX_SPOT_LAST = "cex_spot_last_trade"
    DEX_POOL_SPOT = "dex_single_pool_spot"


class SecurityVerdict(StrEnum):
    PASS = "pass"          # Verified clean across security providers
    UNSAFE = "unsafe"      # Honeypot, high tax (>5%), mintable, or freeze authority active
    UNKNOWN = "unknown"    # Provider error, unindexed contract, or ambiguous input -> DO NOT TRADE


class FieldProvenance(BaseModel):
    value: Any | None = None
    source: str | None = None
    methodology: str | None = None
    quote_currency: str | None = None
    null_reason: str | None = None


class MarketOverviewPayload(BaseModel):
    canonical_id: str
    symbol: str
    price: FieldProvenance
    oracle_price: FieldProvenance | None = None
    market_cap: FieldProvenance
    fdv: FieldProvenance
    volume_24h: FieldProvenance
    change_24h_pct: FieldProvenance


class SecurityAuditPayload(BaseModel):
    chain: str
    contract_address: str
    verdict: SecurityVerdict
    can_trade: bool = False
    reasons: list[str] = Field(default_factory=list)
    buy_tax_pct: float | None = None
    sell_tax_pct: float | None = None
    is_honeypot: bool | None = None
    is_open_source: bool | None = None
    providers_checked: list[str] = Field(default_factory=list)


class CandidateToken(BaseModel):
    symbol: str
    name: str
    chain: str
    contract_address: str
    liquidity_usd: float | None = None
    volume_24h_usd: float | None = None


class AmbiguousAssetResponse(BaseModel):
    verdict: SecurityVerdict = SecurityVerdict.UNKNOWN
    can_trade: bool = False
    warning: str = (
        "AMBIGUOUS_SYMBOL: Multiple on-chain contracts match this ticker. "
        "Re-invoke with explicit chain and contract_address."
    )
    query: str
    candidates: list[CandidateToken]


class ResponseStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    AMBIGUOUS = "ambiguous"
    ERROR = "error"


class OmniEnvelope(BaseModel, Generic[T]):
    status: ResponseStatus
    data: T | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

