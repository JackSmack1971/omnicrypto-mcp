"""Adversarial probes: each test asserts the SAFE behavior. A failure is a real defect."""
import asyncio

import httpx
import pytest
import respx

import omnicrypto.server as srv
from omnicrypto.core.ratelimit import MultiWindowRateLimiter
from omnicrypto.core.router import BoundedStaleCache, WaterfallRouter
from omnicrypto.core.schemas import ResponseStatus

ADDR = "0x1111111111111111111111111111111111111111"
GOPLUS = f"https://api.gopluslabs.io/api/v1/token_security/1"
HPIS = "https://api.honeypot.is/v2/IsHoneypot"

CLEAN_GOPLUS = {
    "is_honeypot": "0", "is_open_source": "1", "is_mintable": "0",
    "buy_tax": "0", "sell_tax": "0", "cannot_sell_all": "0",
    "hidden_owner": "0", "transfer_pausable": "0", "is_blacklisted": "0",
    "owner_change_balance": "0", "slippage_modifiable": "0",
}
CLEAN_HPIS = {
    "honeypotResult": {"isHoneypot": False},
    "simulationSuccess": True,
    "simulationResult": {"buyTax": 0, "sellTax": 0},
    "contractCode": {"openSource": True},
}


@pytest.fixture(autouse=True)
def _fresh_gateway_state():
    # Each test gets a clean cache and circuit table on the shared server router.
    srv.cache._store.clear()
    srv.router.circuits.clear()
    yield


def _goplus(record):
    return httpx.Response(200, json={"code": 1, "result": {ADDR: record}})


async def _audit():
    return await srv.crypto_security_audit(chain="ethereum", contract_address=ADDR)


@respx.mock
async def test_control_both_clean_passes():
    respx.get(GOPLUS).mock(return_value=_goplus(CLEAN_GOPLUS))
    respx.get(HPIS).mock(return_value=httpx.Response(200, json=CLEAN_HPIS))
    r = await _audit()
    assert r["data"]["verdict"] == "pass" and r["data"]["can_trade"] is True


@respx.mock
async def test_single_provider_pass_must_not_be_tradeable():
    """GoPlus clean, Honeypot.is down. Only half the gate ran: must not be can_trade."""
    respx.get(GOPLUS).mock(return_value=_goplus(CLEAN_GOPLUS))
    respx.get(HPIS).mock(return_value=httpx.Response(502))
    r = await _audit()
    assert r["data"]["can_trade"] is False, r["data"]


@respx.mock
async def test_goplus_unknown_fields_must_not_pass():
    """GoPlus returns empty strings for fields it could not determine."""
    respx.get(GOPLUS).mock(return_value=_goplus({k: "" for k in CLEAN_GOPLUS}))
    respx.get(HPIS).mock(return_value=httpx.Response(200, json=CLEAN_HPIS))
    r = await _audit()
    assert r["data"]["can_trade"] is False, r["data"]


@pytest.mark.parametrize("flag", ["cannot_sell_all", "hidden_owner", "transfer_pausable",
                                  "is_blacklisted", "owner_change_balance", "slippage_modifiable"])
@respx.mock
async def test_goplus_dangerous_flags_veto(flag):
    respx.get(GOPLUS).mock(return_value=_goplus({**CLEAN_GOPLUS, flag: "1"}))
    respx.get(HPIS).mock(return_value=httpx.Response(200, json=CLEAN_HPIS))
    r = await _audit()
    assert r["data"]["can_trade"] is False, f"{flag}=1 passed the gate"


@respx.mock
async def test_honeypot_simulation_failure_must_not_pass():
    """Honeypot.is could not simulate a sell: absence of evidence is not a pass."""
    respx.get(GOPLUS).mock(return_value=_goplus(CLEAN_GOPLUS))
    respx.get(HPIS).mock(return_value=httpx.Response(200, json={
        "honeypotResult": {}, "simulationSuccess": False, "contractCode": {}}))
    r = await _audit()
    assert r["data"]["can_trade"] is False, r["data"]


async def test_cancelled_leader_does_not_cancel_waiters():
    """A client disconnect cancels the leader; other callers must still get an answer."""
    router = WaterfallRouter(BoundedStaleCache(), MultiWindowRateLimiter())
    started = asyncio.Event()

    async def slow():
        started.set()
        await asyncio.sleep(0.2)
        return {"ok": 1}

    leader = asyncio.create_task(router.execute("k", 10, [("p", slow)]))
    await started.wait()
    waiter = asyncio.create_task(router.execute("k", 10, [("p", slow)]))
    await asyncio.sleep(0)
    leader.cancel()
    result = await asyncio.wait_for(waiter, 2)
    assert result.status == ResponseStatus.OK
    assert result.data == {"ok": 1}
    with pytest.raises(asyncio.CancelledError):
        await leader
    assert router._inflight_futures == {}
