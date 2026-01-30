"""
Tests for polling utilities.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from app.services.providers.polling_utils import (
    TaskPoller,
    TaskStatus,
    keling_status_mapper,
    minimax_status_mapper,
)


class TestTaskStatus:
    """Test TaskStatus enum."""

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUING.value == "queuing"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"


class TestStatusMappers:
    """Test status mapper functions."""

    def test_keling_status_mapper_success(self):
        """Test Keling status mapper for success."""
        assert keling_status_mapper({"status": "succeed"}) == TaskStatus.SUCCESS
        assert keling_status_mapper({"status": "success"}) == TaskStatus.SUCCESS

    def test_keling_status_mapper_failed(self):
        """Test Keling status mapper for failure."""
        assert keling_status_mapper({"status": "failed"}) == TaskStatus.FAILED
        assert keling_status_mapper({"status": "fail"}) == TaskStatus.FAILED

    def test_keling_status_mapper_processing(self):
        """Test Keling status mapper for processing."""
        assert keling_status_mapper({"status": "processing"}) == TaskStatus.PROCESSING
        assert keling_status_mapper({"status": "submitted"}) == TaskStatus.PENDING

    def test_keling_status_mapper_default(self):
        """Test Keling status mapper for unknown status defaults to pending."""
        assert keling_status_mapper({"status": "unknown"}) == TaskStatus.PENDING
        assert keling_status_mapper({}) == TaskStatus.PENDING

    def test_minimax_status_mapper_success(self):
        """Test MiniMax status mapper for success."""
        assert minimax_status_mapper({"status": "Success"}) == TaskStatus.SUCCESS

    def test_minimax_status_mapper_failed(self):
        """Test MiniMax status mapper for failure."""
        assert minimax_status_mapper({"status": "Fail"}) == TaskStatus.FAILED
        assert minimax_status_mapper({"status": "Failed"}) == TaskStatus.FAILED

    def test_minimax_status_mapper_processing(self):
        """Test MiniMax status mapper for processing."""
        assert minimax_status_mapper({"status": "Processing"}) == TaskStatus.PROCESSING
        assert minimax_status_mapper({"status": "Queueing"}) == TaskStatus.QUEUING
        assert minimax_status_mapper({"status": "Preparing"}) == TaskStatus.PREPARING

    def test_minimax_status_mapper_default(self):
        """Test MiniMax status mapper for unknown status defaults to pending."""
        assert minimax_status_mapper({"status": "unknown"}) == TaskStatus.PENDING
        assert minimax_status_mapper({}) == TaskStatus.PENDING


class TestTaskPoller:
    """Test TaskPoller class."""

    @pytest.mark.asyncio
    async def test_poll_success(self):
        """Test successful polling."""
        responses = [
            {"status": "processing", "data": None},
            {"status": "processing", "data": None},
            {"status": "succeed", "data": {"result": "video_url"}},
        ]
        response_iter = iter(responses)
        mock_poll_fn = AsyncMock(side_effect=lambda: next(response_iter))

        def status_mapper(response):
            status = response.get("status", "").lower()
            if status == "succeed":
                return TaskStatus.SUCCESS
            return TaskStatus.PROCESSING

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=status_mapper,
            initial_delay=0.01,
            max_attempts=10,
        )

        result = await poller.poll()

        assert result == {"status": "succeed", "data": {"result": "video_url"}}
        assert mock_poll_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_poll_immediate_success(self):
        """Test immediate success without waiting."""
        mock_poll_fn = AsyncMock(
            return_value={"status": "succeed", "data": {"result": "completed"}}
        )

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.1,
        )

        result = await poller.poll()

        assert result == {"status": "succeed", "data": {"result": "completed"}}
        assert mock_poll_fn.call_count == 1

    @pytest.mark.asyncio
    async def test_poll_failure(self):
        """Test polling with task failure."""
        responses = [
            {"status": "processing"},
            {"status": "failed", "error": "Generation failed"},
        ]
        response_iter = iter(responses)
        mock_poll_fn = AsyncMock(side_effect=lambda: next(response_iter))

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.01,
        )

        result = await poller.poll()

        assert result is None  # Returns None on failure
        assert mock_poll_fn.call_count == 2

    @pytest.mark.asyncio
    async def test_poll_max_attempts_exceeded(self):
        """Test polling timeout after max attempts."""
        mock_poll_fn = AsyncMock(return_value={"status": "processing"})

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.01,
            max_attempts=3,
        )

        result = await poller.poll()

        assert result is None  # Returns None on timeout
        assert mock_poll_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_poll_with_keling_mapper(self):
        """Test polling with Keling status mapper."""
        responses = [
            {"status": "submitted"},
            {"status": "processing"},
            {"status": "succeed", "data": {"video_url": "https://example.com"}},
        ]
        response_iter = iter(responses)
        mock_poll_fn = AsyncMock(side_effect=lambda: next(response_iter))

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.01,
        )

        result = await poller.poll()

        assert result["status"] == "succeed"
        assert mock_poll_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_poll_with_minimax_mapper(self):
        """Test polling with MiniMax status mapper."""
        responses = [
            {"status": "Queueing"},
            {"status": "Processing"},
            {"status": "Success", "file_id": "file_123"},
        ]
        response_iter = iter(responses)
        mock_poll_fn = AsyncMock(side_effect=lambda: next(response_iter))

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=minimax_status_mapper,
            initial_delay=0.01,
        )

        result = await poller.poll()

        assert result["status"] == "Success"
        assert mock_poll_fn.call_count == 3

    @pytest.mark.asyncio
    async def test_poll_with_custom_interval(self):
        """Test polling respects custom interval."""
        call_times = []
        call_count = [0]

        async def mock_poll_fn():
            call_times.append(asyncio.get_event_loop().time())
            call_count[0] += 1
            if call_count[0] < 3:
                return {"status": "processing"}
            return {"status": "succeed"}

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.15,
        )

        await poller.poll()

        # Verify polling interval (with tolerance)
        assert len(call_times) == 3
        interval1 = call_times[1] - call_times[0]
        interval2 = call_times[2] - call_times[1]

        assert 0.12 < interval1 < 0.20  # ~0.15s ± tolerance
        assert 0.12 < interval2 < 0.20

    @pytest.mark.asyncio
    async def test_poll_with_result_extractor(self):
        """Test polling with custom result extractor."""
        mock_poll_fn = AsyncMock(
            return_value={"status": "succeed", "task_result": {"url": "video.mp4"}}
        )

        def result_extractor(response):
            return response.get("task_result")

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            result_extractor=result_extractor,
            initial_delay=0.01,
        )

        result = await poller.poll()

        assert result == {"url": "video.mp4"}

    @pytest.mark.asyncio
    async def test_poll_exception_in_fetch_retries(self):
        """Test polling retries on exceptions."""
        call_count = [0]

        async def mock_poll_fn():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Network error")
            return {"status": "succeed"}

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.01,
            max_attempts=3,
        )

        result = await poller.poll()

        assert result is not None
        assert call_count[0] == 2  # First failed, second succeeded

    @pytest.mark.asyncio
    async def test_poll_exception_max_attempts(self):
        """Test polling gives up after max attempts on exceptions."""
        mock_poll_fn = AsyncMock(side_effect=Exception("Network error"))

        poller = TaskPoller(
            poll_fn=mock_poll_fn,
            status_mapper=keling_status_mapper,
            initial_delay=0.01,
            max_attempts=2,
        )

        with pytest.raises(Exception) as exc_info:
            await poller.poll()

        assert "Network error" in str(exc_info.value)
        assert mock_poll_fn.call_count == 2
