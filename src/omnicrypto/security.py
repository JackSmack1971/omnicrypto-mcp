"""Fail-closed token security policy.

Pure functions over provider payloads, so the policy is testable without a network.
Field names were checked against live GoPlus and Honeypot.is responses (Oct 2026).

Verdict rules:
  * UNSAFE  - any provider found an intrinsic trap, a high tax, unverified source,
              or an owner-controlled power while ownership is NOT renounced.
  * UNKNOWN - a critical field is missing/blank, a sell simulation failed, or not
              every expected provider produced a result. Never tradeable.
  * PASS    - every expected provider ran and none raised a concern.
"""
from __future__ import annotations

from omnicrypto.core.schemas import SecurityAuditPayload, SecurityVerdict

MAX_TAX_PCT = 5.0

RENOUNCED_OWNERS = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}

# Dangerous regardless of who owns the contract.
GOPLUS_INTRINSIC_FLAGS = {
    "is_honeypot": "flagged as honeypot",
    "cannot_sell_all": "holders cannot sell their full balance",
    "hidden_owner": "contract has a hidden owner",
    "can_take_back_ownership": "ownership can be reclaimed after renouncing",
    "selfdestruct": "contract can self-destruct",
    "honeypot_with_same_creator": "creator has deployed honeypots before",
}

# Powers only an owner can use; inert once ownership is renounced.
GOPLUS_OWNER_FLAGS = {
    "is_mintable": "owner can mint new supply",
    "transfer_pausable": "owner can pause transfers",
    "is_blacklisted": "owner can blacklist addresses",
    "owner_change_balance": "owner can change balances",
    "slippage_modifiable": "owner can change trading tax",
    "personal_slippage_modifiable": "owner can set per-address tax",
    "trading_cooldown": "owner-enforced trading cooldown",
}

# If any of these are blank the provider did not finish its analysis.
GOPLUS_CRITICAL_FIELDS = ("is_honeypot", "cannot_sell_all", "buy_tax", "sell_tax", "is_open_source")


def _flag(record: dict, field: str) -> bool:
    return str(record.get(field, "")).strip() == "1"


def _blank(record: dict, field: str) -> bool:
    return str(record.get(field, "")).strip() == ""


def _pct(raw) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_goplus(chain: str, address: str, record: dict) -> SecurityAuditPayload:
    reasons: list[str] = []
    unknowns: list[str] = []

    missing = [f for f in GOPLUS_CRITICAL_FIELDS if _blank(record, f)]
    if missing:
        unknowns.append(f"GoPlus did not report: {', '.join(missing)}")

    for field, why in GOPLUS_INTRINSIC_FLAGS.items():
        if _flag(record, field):
            reasons.append(f"GoPlus: {why}")

    if str(record.get("is_open_source", "")).strip() == "0":
        reasons.append("GoPlus: contract source is not verified")

    owner = str(record.get("owner_address", "")).strip().lower()
    owner_powers = [why for field, why in GOPLUS_OWNER_FLAGS.items() if _flag(record, field)]
    if owner_powers:
        if owner in RENOUNCED_OWNERS:
            pass  # powers exist in code but nobody can use them
        elif owner == "":
            unknowns.append("GoPlus: owner powers present but owner status unknown")
        else:
            reasons.extend(f"GoPlus: {why} (owner {owner} not renounced)" for why in owner_powers)

    # GoPlus reports tax as a fraction (0.05 == 5%).
    buy = _pct(record.get("buy_tax"))
    sell = _pct(record.get("sell_tax"))
    buy_pct = None if buy is None else buy * 100.0
    sell_pct = None if sell is None else sell * 100.0
    if (buy_pct or 0) > MAX_TAX_PCT or (sell_pct or 0) > MAX_TAX_PCT:
        reasons.append(f"GoPlus: tax above {MAX_TAX_PCT:.0f}% (buy={buy_pct}%, sell={sell_pct}%)")

    return _payload(chain, address, "goplus", reasons, unknowns, buy_pct, sell_pct,
                    is_honeypot=_flag(record, "is_honeypot"),
                    is_open_source=None if _blank(record, "is_open_source") else _flag(record, "is_open_source"))


def evaluate_honeypot_is(chain: str, address: str, body: dict) -> SecurityAuditPayload:
    reasons: list[str] = []
    unknowns: list[str] = []

    hp = body.get("honeypotResult") or {}
    sim = body.get("simulationResult") or {}
    code = body.get("contractCode") or {}

    if body.get("simulationSuccess") is not True:
        unknowns.append("Honeypot.is: buy/sell simulation did not succeed")

    is_hp = hp.get("isHoneypot")
    if is_hp is True:
        reasons.append(f"Honeypot.is: honeypot ({hp.get('honeypotReason', 'no reason given')})")
    elif is_hp is not False:
        unknowns.append("Honeypot.is: honeypot result missing")

    open_source = code.get("openSource")
    if open_source is False:
        reasons.append("Honeypot.is: contract source is not verified")

    # Honeypot.is reports tax as a percentage (5 == 5%).
    buy_pct = _pct(sim.get("buyTax"))
    sell_pct = _pct(sim.get("sellTax"))
    if body.get("simulationSuccess") is True and (buy_pct is None or sell_pct is None):
        unknowns.append("Honeypot.is: simulated tax missing")
    if (buy_pct or 0) > MAX_TAX_PCT or (sell_pct or 0) > MAX_TAX_PCT:
        reasons.append(f"Honeypot.is: simulated tax above {MAX_TAX_PCT:.0f}% (buy={buy_pct}%, sell={sell_pct}%)")

    return _payload(chain, address, "honeypot.is", reasons, unknowns, buy_pct, sell_pct,
                    is_honeypot=is_hp if isinstance(is_hp, bool) else None,
                    is_open_source=open_source if isinstance(open_source, bool) else None)


def _payload(chain, address, provider, reasons, unknowns, buy, sell, *, is_honeypot, is_open_source):
    if reasons:
        verdict = SecurityVerdict.UNSAFE
    elif unknowns:
        verdict = SecurityVerdict.UNKNOWN
    else:
        verdict = SecurityVerdict.PASS
    return SecurityAuditPayload(
        chain=chain, contract_address=address, verdict=verdict,
        can_trade=verdict == SecurityVerdict.PASS,
        reasons=reasons + unknowns,
        buy_tax_pct=None if buy is None else round(buy, 2),
        sell_tax_pct=None if sell is None else round(sell, 2),
        is_honeypot=is_honeypot, is_open_source=is_open_source,
        providers_checked=[provider],
    )


def merge(chain: str, address: str, results: list[SecurityAuditPayload],
          expected: list[str], failures: list[str]) -> SecurityAuditPayload:
    """UNSAFE from anyone vetoes. PASS needs every expected provider to have passed."""
    reasons = [r for res in results for r in res.reasons] + failures
    checked = [p for res in results for p in res.providers_checked]

    if any(r.verdict == SecurityVerdict.UNSAFE for r in results):
        verdict = SecurityVerdict.UNSAFE
    elif set(checked) >= set(expected) and all(r.verdict == SecurityVerdict.PASS for r in results):
        verdict = SecurityVerdict.PASS
    else:
        verdict = SecurityVerdict.UNKNOWN
        missing = sorted(set(expected) - set(checked))
        if missing:
            reasons.append(f"INCOMPLETE_AUDIT: no result from {', '.join(missing)}; fail-closed")

    def _max(attr):
        vals = [getattr(r, attr) for r in results if getattr(r, attr) is not None]
        return max(vals) if vals else None

    honeypot_vals = [r.is_honeypot for r in results if r.is_honeypot is not None]
    source_vals = [r.is_open_source for r in results if r.is_open_source is not None]
    return SecurityAuditPayload(
        chain=chain, contract_address=address, verdict=verdict,
        can_trade=verdict == SecurityVerdict.PASS, reasons=reasons,
        buy_tax_pct=_max("buy_tax_pct"), sell_tax_pct=_max("sell_tax_pct"),
        is_honeypot=any(honeypot_vals) if honeypot_vals else None,
        is_open_source=all(source_vals) if source_vals else None,
        providers_checked=checked,
    )
