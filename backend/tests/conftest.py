import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


# ── Single session-wide event loop ───────────────────────────────────────────
# asyncpg binds its protocol to the loop that first opens a connection.
# Every test must run in the SAME loop to avoid "Future attached to a
# different loop" errors.
@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped asyncio event loop shared by all async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── Session-scoped HTTPX client with lifespan ────────────────────────────────
# Using a single AsyncClient with lifespan=True ensures:
#   • The FastAPI lifespan (DB init + seed_admin) runs exactly once.
#   • All DB connections are created on the session loop.
@pytest_asyncio.fixture(scope="session")
async def client():
    """Shared HTTPX async client that boots the FastAPI app once per session."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
