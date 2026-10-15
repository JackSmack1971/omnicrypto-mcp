# OmniCrypto-MCP 0.2.1: verified build

This is the pasted v0.2.0 scaffold, actually run, with the defects that running it exposed fixed.
Python 3.13, FastMCP 4.1.0, ccxt 4.5.88, httpx 0.28.1, numpy 2.5.4.

## Run

```bash
uv venv && uv pip install -e '.[dev]'
uv run pytest -q                                  # 28 passed, 1 skipped
OMNICRYPTO_LIVE=1 uv run pytest -q -k live        # optional: hits real GoPlus + Honeypot.is
uv run omnicrypto                                 # http://127.0.0.1:8900/mcp
```

Binding off loopback requires `OMNICRYPTO_BEARER_TOKEN` (24+ chars), and every request must
send `Authorization: Bearer <token>`.

## Defects found by running v0.2.0, and fixes

| Defect | Evidence | Fix |
|---|---|---|
| Package would not install | hatchling: "Unable to determine which files to ship" | Declared `src/omnicrypto` wheel target |
| No `omnicrypto` command | v0.2.0 dropped `[project.scripts]` from v0.1 | Restored entry point |
| Test run hung forever after passing | aiosqlite worker thread is non-daemon and never closed outside the server lifespan | DB opened only for monthly-capped providers; init is locked (it could double-open and leak a thread); thread daemonized |
| Bearer token never enforced | Server on 0.0.0.0 with token set served `tools/list` to a client with no auth header | Constant-time ASGI middleware: 401 on missing/wrong/prefix token, verified on a live server |
| One provider passing made a token tradeable | GoPlus clean + Honeypot.is 502 returned `pass`, `can_trade: true` | `pass` requires every expected provider; otherwise `unknown` |
| Six GoPlus danger flags ignored | `cannot_sell_all`, `hidden_owner`, `transfer_pausable`, `is_blacklisted`, `owner_change_balance`, `slippage_modifiable` = 1 all passed | New `security.py` policy (below) |
| Failed sell simulation passed | Honeypot.is `simulationSuccess: false` with empty results returned `pass` | Failed or missing simulation is `unknown` |
| Cancelling one caller cancelled all coalesced callers | Leader cancellation propagated `CancelledError` into every waiter | Waterfall runs as its own task; each caller awaits it shielded |
| Suite advertised 7 tests | File contained 6 | Now 28, including the adversarial cases above |

## Security policy (`src/omnicrypto/security.py`)

Field names and units were checked against live API responses captured into `tests/fixtures/`.

- **Always veto:** honeypot, cannot sell full balance, hidden owner, reclaimable ownership, selfdestruct, creator with prior honeypots, unverified source, tax above 5%.
- **Veto only while an owner exists:** mint, pause, blacklist, balance edits, tax edits, per-address tax, cooldown. Live PEPE data carries `transfer_pausable=1` and `is_blacklisted=1`, but its owner is `0x0`, so it passes. The same flags with a real owner are `unsafe`.
- **Fail closed:** blank critical fields, unknown owner status alongside owner powers, or a missing provider give `unknown`, and `can_trade` is false.
- **Tax units differ:** GoPlus reports a fraction (0.05) and Honeypot.is reports a percent (5). Both are tested.

## Still open (not changed here)

- Proxy contracts (`is_proxy=1`) are not vetoed. Upgradeable logic is a real risk, but vetoing it would block tokens like USDC. Decide per strategy.
- RugCheck's `score > 500` cutoff is a policy guess. Field names were checked live (BONK: score 101, one warning).
- The stale cache is in-memory only. v0.2.0 described SQLite cache persistence but didn't implement it.
- `ta_engine.py` is untested. RSI returns `None` instead of 100 when there are no losses, and `period_vwap` covers the whole window, not a session.
- Timing-based router tests use 50–120 ms sleeps. They passed 3 of 3 runs, but may be flaky on a loaded CI box.
