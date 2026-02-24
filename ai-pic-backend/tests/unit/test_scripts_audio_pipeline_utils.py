import asyncio
import threading

import pytest
from app.api.v1.endpoints.scripts.audio_pipeline_utils import run_async_task_sync


async def _async_value(value: int) -> int:
    return value


def test_run_async_task_sync_without_running_loop() -> None:
    assert run_async_task_sync(lambda: _async_value(42)) == 42


def test_run_async_task_sync_with_running_loop_uses_worker_thread() -> None:
    caller_thread_id = threading.get_ident()

    async def _call() -> int:
        async def _current_thread_id() -> int:
            return threading.get_ident()

        return run_async_task_sync(_current_thread_id)

    worker_thread_id = asyncio.run(_call())
    assert worker_thread_id != caller_thread_id


def test_run_async_task_sync_with_running_loop_propagates_exception() -> None:
    class Boom(RuntimeError):
        pass

    async def _boom() -> None:
        raise Boom("boom")

    async def _call() -> None:
        with pytest.raises(Boom, match="boom"):
            run_async_task_sync(_boom)

    asyncio.run(_call())
