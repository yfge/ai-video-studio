"""
Unified Task Polling Utilities

Provides standardized task polling logic for async AI generation tasks
across different providers (Keling, MiniMax, etc.).
"""

import asyncio
from typing import Callable, Optional, Dict, Any, Awaitable
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Standardized task status across providers."""
    PENDING = "pending"
    QUEUING = "queuing"
    PREPARING = "preparing"
    PROCESSING = "processing"
    RUNNING = "running"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskPoller:
    """
    Unified task poller with exponential backoff support.

    Handles async polling of long-running tasks (video/image generation)
    with configurable retry strategy and status mapping.

    Example usage:
        poller = TaskPoller(
            poll_fn=lambda: client.get_task_status(task_id),
            max_attempts=60,
            initial_delay=5,
            status_mapper=lambda data: TaskStatus.SUCCESS if data["status"] == "done" else TaskStatus.PROCESSING
        )
        result = await poller.poll()
    """

    def __init__(
        self,
        poll_fn: Callable[[], Awaitable[Dict[str, Any]]],
        status_mapper: Callable[[Dict[str, Any]], TaskStatus],
        result_extractor: Optional[Callable[[Dict[str, Any]], Any]] = None,
        max_attempts: int = 60,
        initial_delay: float = 5.0,
        max_delay: float = 30.0,
        backoff_factor: float = 1.0,  # 1.0 = no backoff, >1.0 = exponential backoff
        task_id: Optional[str] = None,
        task_type: str = "unknown"
    ):
        """
        Initialize task poller.

        Args:
            poll_fn: Async function that polls the task status (returns dict)
            status_mapper: Function that maps provider response to TaskStatus
            result_extractor: Optional function to extract result from response
            max_attempts: Maximum number of polling attempts
            initial_delay: Initial delay between polls in seconds
            max_delay: Maximum delay between polls (for exponential backoff)
            backoff_factor: Backoff multiplier (1.0=constant, >1.0=exponential)
            task_id: Task ID for logging (optional)
            task_type: Task type for logging (e.g., "image", "video")
        """
        self.poll_fn = poll_fn
        self.status_mapper = status_mapper
        self.result_extractor = result_extractor or (lambda x: x)
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.task_id = task_id or "unknown"
        self.task_type = task_type

        self._start_time: Optional[datetime] = None
        self._attempt_count = 0

    def _calculate_delay(self) -> float:
        """Calculate delay for next polling attempt."""
        if self.backoff_factor <= 1.0:
            # Constant delay
            return self.initial_delay

        # Exponential backoff
        delay = self.initial_delay * (self.backoff_factor ** self._attempt_count)
        return min(delay, self.max_delay)

    async def poll(self) -> Optional[Any]:
        """
        Poll task until completion, failure, or timeout.

        Returns:
            Extracted result if task succeeds, None if task fails or times out

        Raises:
            Exception: Any unhandled exceptions from poll_fn (after logging)
        """
        self._start_time = datetime.now()
        self._attempt_count = 0

        logger.info(
            f"Starting {self.task_type} task polling for task {self.task_id}, "
            f"max_attempts={self.max_attempts}, initial_delay={self.initial_delay}s"
        )

        for attempt in range(self.max_attempts):
            self._attempt_count = attempt + 1

            try:
                # Poll task status
                response = await self.poll_fn()

                # Map provider status to standardized status
                status = self.status_mapper(response)

                # Log progress
                elapsed = (datetime.now() - self._start_time).total_seconds()
                logger.debug(
                    f"Poll attempt {self._attempt_count}/{self.max_attempts} for task {self.task_id}: "
                    f"status={status}, elapsed={elapsed:.1f}s"
                )

                # Handle terminal states
                if status in (TaskStatus.SUCCESS, TaskStatus.COMPLETED):
                    logger.info(
                        f"Task {self.task_id} completed successfully after {self._attempt_count} attempts "
                        f"({elapsed:.1f}s)"
                    )
                    return self.result_extractor(response)

                elif status == TaskStatus.FAILED:
                    error_msg = response.get("error") or response.get("message") or "Unknown error"
                    logger.warning(
                        f"Task {self.task_id} failed after {self._attempt_count} attempts "
                        f"({elapsed:.1f}s): {error_msg}"
                    )
                    return None

                # Continue polling for non-terminal states
                elif status in (
                    TaskStatus.PENDING,
                    TaskStatus.QUEUING,
                    TaskStatus.PREPARING,
                    TaskStatus.PROCESSING,
                    TaskStatus.RUNNING
                ):
                    if attempt < self.max_attempts - 1:
                        delay = self._calculate_delay()
                        logger.debug(
                            f"Task {self.task_id} still {status.value}, waiting {delay:.1f}s before next poll"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Max attempts reached
                        logger.warning(
                            f"Task {self.task_id} timeout after {self.max_attempts} attempts "
                            f"({elapsed:.1f}s), last status: {status.value}"
                        )
                        return None

                else:
                    # Unknown status
                    logger.warning(
                        f"Task {self.task_id} returned unknown status: {status.value}, "
                        f"treating as failure"
                    )
                    return None

            except Exception as e:
                logger.error(
                    f"Error polling task {self.task_id} (attempt {self._attempt_count}): {e}",
                    exc_info=True
                )

                # Retry on transient errors if not last attempt
                if attempt < self.max_attempts - 1:
                    delay = self._calculate_delay()
                    logger.info(f"Retrying after {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Last attempt, give up
                    logger.error(
                        f"Task {self.task_id} polling failed after {self.max_attempts} attempts"
                    )
                    raise

        # Should not reach here, but handle just in case
        logger.warning(f"Task {self.task_id} polling exhausted all attempts without resolution")
        return None


def keling_status_mapper(response: Dict[str, Any]) -> TaskStatus:
    """
    Map Keling AI task status to standardized TaskStatus.

    Keling statuses: submitted, processing, succeed, failed
    """
    status_str = (
        response.get("task_status")
        or response.get("status")
        or response.get("taskStatus")
        or ""
    )
    status_str = status_str.lower()

    status_map = {
        "submitted": TaskStatus.PENDING,
        "processing": TaskStatus.PROCESSING,
        "succeed": TaskStatus.SUCCESS,
        "success": TaskStatus.SUCCESS,
        "failed": TaskStatus.FAILED,
        "fail": TaskStatus.FAILED
    }

    return status_map.get(status_str, TaskStatus.PENDING)


def minimax_status_mapper(response: Dict[str, Any]) -> TaskStatus:
    """
    Map MiniMax task status to standardized TaskStatus.

    MiniMax statuses: Preparing, Queueing, Processing, Success, Fail
    """
    status_str = response.get("status", "")

    status_map = {
        "Preparing": TaskStatus.PREPARING,
        "Queueing": TaskStatus.QUEUING,
        "Processing": TaskStatus.PROCESSING,
        "Success": TaskStatus.SUCCESS,
        "Fail": TaskStatus.FAILED,
        "Failed": TaskStatus.FAILED
    }

    return status_map.get(status_str, TaskStatus.PENDING)


def google_operation_status_mapper(response: Dict[str, Any]) -> TaskStatus:
    """
    Map Google long-running operation status to TaskStatus.

    Google operations: done=false (running), done=true with error (failed).
    """
    if response.get("done") is True:
        if response.get("error"):
            return TaskStatus.FAILED
        return TaskStatus.SUCCESS
    return TaskStatus.PROCESSING
