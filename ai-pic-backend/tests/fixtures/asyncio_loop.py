import asyncio

import pytest


@pytest.fixture
def event_loop():
    """Create a fresh event loop per test for pytest-asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
