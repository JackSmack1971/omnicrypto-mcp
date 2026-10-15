import httpx
import pytest

from omnicrypto.server import BearerAuthMiddleware

TOKEN = "correct-horse-battery-staple-9f3a"


async def _ok_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


@pytest.mark.parametrize("headers,expected", [
    ({}, 401),
    ({"authorization": "Bearer wrong"}, 401),
    ({"authorization": TOKEN}, 401),                 # missing "Bearer " scheme
    ({"authorization": f"Bearer {TOKEN}x"}, 401),    # prefix match must not pass
    ({"authorization": f"Bearer {TOKEN}"}, 200),
])
async def test_bearer_middleware(headers, expected):
    app = BearerAuthMiddleware(_ok_app, token=TOKEN)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.post("/mcp", headers=headers)
    assert r.status_code == expected
