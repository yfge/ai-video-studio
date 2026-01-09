import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for pytest-asyncio."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
