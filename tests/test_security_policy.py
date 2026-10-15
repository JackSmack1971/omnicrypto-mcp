"""Security policy against real provider payloads (captured live, Oct 2026)."""
import json
import os
from pathlib import Path

import httpx
import pytest

from omnicrypto import security
from omnicrypto.core.schemas import SecurityVerdict

FIX = Path(__file__).parent / "fixtures"
PEPE = "0x6982508145454ce325ddbe47a25d4ec3d2311933"


def _goplus_pepe() -> dict:
    return json.loads((FIX / "goplus_pepe_eth.json").read_text())["result"][PEPE]


def _hpis_pepe() -> dict:
    return json.loads((FIX / "honeypot_is_pepe_eth.json").read_text())


def test_live_pepe_has_owner_flags_but_renounced_owner_passes():
    rec = _goplus_pepe()
    # The capture really does carry owner-power flags...
    assert rec["transfer_pausable"] == "1" and rec["is_blacklisted"] == "1"
    # ...but ownership is renounced, so they are inert.
    assert rec["owner_address"] == "0x0000000000000000000000000000000000000000"
    res = security.evaluate_goplus("ethereum", PEPE, rec)
    assert res.verdict == SecurityVerdict.PASS, res.reasons


def test_same_flags_with_live_owner_are_unsafe():
    rec = {**_goplus_pepe(), "owner_address": "0xfbfeaf0da0f2fde5c66df570133ae35f3eb58c9a"}
    res = security.evaluate_goplus("ethereum", PEPE, rec)
    assert res.verdict == SecurityVerdict.UNSAFE
    assert any("pause" in r for r in res.reasons) and any("blacklist" in r for r in res.reasons)


def test_live_pepe_honeypot_is_passes():
    res = security.evaluate_honeypot_is("ethereum", PEPE, _hpis_pepe())
    assert res.verdict == SecurityVerdict.PASS, res.reasons


def test_merge_of_live_pepe_is_tradeable():
    a = security.evaluate_goplus("ethereum", PEPE, _goplus_pepe())
    b = security.evaluate_honeypot_is("ethereum", PEPE, _hpis_pepe())
    m = security.merge("ethereum", PEPE, [a, b], expected=["goplus", "honeypot.is"], failures=[])
    assert m.verdict == SecurityVerdict.PASS and m.can_trade is True


def test_tax_units_differ_between_providers():
    # GoPlus: fraction (0.06 = 6%). Honeypot.is: percent (6 = 6%). Both must veto at 6%.
    g = security.evaluate_goplus("ethereum", PEPE, {**_goplus_pepe(), "sell_tax": "0.06"})
    h_body = _hpis_pepe()
    h_body = {**h_body, "simulationResult": {**h_body["simulationResult"], "sellTax": 6}}
    h = security.evaluate_honeypot_is("ethereum", PEPE, h_body)
    assert g.verdict == SecurityVerdict.UNSAFE and h.verdict == SecurityVerdict.UNSAFE
    # And 4% must not trip either.
    g4 = security.evaluate_goplus("ethereum", PEPE, {**_goplus_pepe(), "sell_tax": "0.04"})
    assert g4.verdict == SecurityVerdict.PASS


def test_unsafe_from_one_provider_vetoes_pass_from_other():
    a = security.evaluate_goplus("ethereum", PEPE, {**_goplus_pepe(), "cannot_sell_all": "1"})
    b = security.evaluate_honeypot_is("ethereum", PEPE, _hpis_pepe())
    m = security.merge("ethereum", PEPE, [a, b], expected=["goplus", "honeypot.is"], failures=[])
    assert m.verdict == SecurityVerdict.UNSAFE and m.can_trade is False


@pytest.mark.skipif(not os.getenv("OMNICRYPTO_LIVE"), reason="set OMNICRYPTO_LIVE=1 to hit real APIs")
async def test_live_end_to_end_pepe():
    import omnicrypto.server as srv
    srv.cache._store.clear()
    r = await srv.crypto_security_audit(chain="ethereum", contract_address=PEPE)
    assert r["data"]["providers_checked"] == ["goplus", "honeypot.is"], r
    assert r["data"]["verdict"] in ("pass", "unsafe", "unknown")
