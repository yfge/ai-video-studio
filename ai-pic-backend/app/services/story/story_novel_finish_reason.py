"""Shared provider finish-reason contract for recoverable truncation."""

TRUNCATED_FINISH_REASONS = frozenset(
    {"content_filter", "length", "max_output_tokens", "max_tokens", "token_limit"}
)
RECOVERABLE_LENGTH_FINISH_REASONS = TRUNCATED_FINISH_REASONS - {"content_filter"}


def is_truncated_finish_reason(value) -> bool:
    return str(value or "").strip().lower() in TRUNCATED_FINISH_REASONS


def is_recoverable_length_finish_reason(value) -> bool:
    return str(value or "").strip().lower() in RECOVERABLE_LENGTH_FINISH_REASONS
