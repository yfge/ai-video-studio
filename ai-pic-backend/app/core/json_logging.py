"""JSONL logging handler for harness trace collection."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from app.core.log_context import get_log_context

STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys())


class JsonlLogHandler(logging.Handler):
    """Write structured log events as JSON lines."""

    def __init__(self, path: str):
        super().__init__()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        payload.update(get_log_context())
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in STANDARD_ATTRS and not key.startswith("_")
            }
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
