"""Context Specification System.

Provides structured context injection for agents with:
- Field validation and type checking
- Token budget awareness and truncation
- Priority-based content selection
- Consistent serialization
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

logger = logging.getLogger(__name__)

# Approximate tokens per character for Chinese/English mixed content
TOKENS_PER_CHAR_ZH = 0.6
TOKENS_PER_CHAR_EN = 0.25
DEFAULT_TOKENS_PER_CHAR = 0.5


class FieldPriority(str, Enum):
    """Priority levels for context fields."""

    CRITICAL = "critical"  # Never truncate
    HIGH = "high"  # Truncate only when necessary
    MEDIUM = "medium"  # Can be truncated
    LOW = "low"  # Truncate first


class TruncationStrategy(str, Enum):
    """Strategies for truncating content."""

    NONE = "none"  # No truncation allowed
    TAIL = "tail"  # Keep beginning, truncate end
    HEAD = "head"  # Keep end, truncate beginning
    MIDDLE = "middle"  # Keep beginning and end
    SUMMARIZE = "summarize"  # Replace with summary (requires callback)


@dataclass
class FieldSpec:
    """Specification for a context field."""

    name: str
    description: str
    priority: FieldPriority = FieldPriority.MEDIUM
    required: bool = False
    max_tokens: Optional[int] = None
    truncation: TruncationStrategy = TruncationStrategy.TAIL
    default: Any = None
    validator: Optional[Callable[[Any], bool]] = None
    transformer: Optional[Callable[[Any], Any]] = None

    def validate(self, value: Any) -> bool:
        """Validate field value."""
        if self.required and value is None:
            return False
        if value is not None and self.validator:
            return self.validator(value)
        return True

    def transform(self, value: Any) -> Any:
        """Transform field value."""
        if value is not None and self.transformer:
            return self.transformer(value)
        return value


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Uses heuristics based on character types.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Count Chinese vs ASCII characters
    chinese_chars = sum(1 for c in text if ord(c) > 127)
    ascii_chars = len(text) - chinese_chars

    # Chinese characters ~= 0.6 tokens each, ASCII ~= 0.25 tokens each
    return int(chinese_chars * TOKENS_PER_CHAR_ZH + ascii_chars * TOKENS_PER_CHAR_EN)


def truncate_text(
    text: str,
    max_tokens: int,
    strategy: TruncationStrategy = TruncationStrategy.TAIL,
) -> str:
    """Truncate text to fit within token budget.

    Args:
        text: Text to truncate
        max_tokens: Maximum token count
        strategy: How to truncate

    Returns:
        Truncated text
    """
    if not text or max_tokens <= 0:
        return ""

    current_tokens = estimate_tokens(text)
    if current_tokens <= max_tokens:
        return text

    # Estimate characters to keep
    ratio = max_tokens / current_tokens
    keep_chars = int(len(text) * ratio * 0.9)  # 10% safety margin

    if strategy == TruncationStrategy.NONE:
        return text  # Return as-is, validation will catch overflow

    elif strategy == TruncationStrategy.TAIL:
        truncated = text[:keep_chars]
        return truncated.rsplit("\n", 1)[0] + "\n..."

    elif strategy == TruncationStrategy.HEAD:
        truncated = text[-keep_chars:]
        return "..." + truncated.split("\n", 1)[-1]

    elif strategy == TruncationStrategy.MIDDLE:
        half = keep_chars // 2
        return text[:half] + "\n...\n" + text[-half:]

    elif strategy == TruncationStrategy.SUMMARIZE:
        # Summarize strategy requires external callback, fallback to tail
        return text[:keep_chars] + "\n..."

    return text[:keep_chars]


T = TypeVar("T", bound="ContextSpec")


@dataclass
class ContextSpec:
    """Base specification for agent context.

    Subclass to define specific context structures:

        class StoryContext(ContextSpec):
            FIELDS = [
                FieldSpec("title", "Story title", priority=FieldPriority.CRITICAL),
                FieldSpec("characters", "Character list", max_tokens=500),
            ]
    """

    FIELDS: List[FieldSpec] = field(default_factory=list)

    def __init__(self, **kwargs):
        """Initialize with field values."""
        self._values: Dict[str, Any] = {}
        self._field_map = {f.name: f for f in self.FIELDS}

        for name, value in kwargs.items():
            if name in self._field_map:
                self.set(name, value)

    def set(self, name: str, value: Any) -> None:
        """Set a field value.

        Args:
            name: Field name
            value: Field value
        """
        if name not in self._field_map:
            logger.warning(f"Unknown context field: {name}")
            return

        spec = self._field_map[name]
        transformed = spec.transform(value)

        if not spec.validate(transformed):
            raise ValueError(f"Invalid value for field {name}")

        self._values[name] = transformed

    def get(self, name: str, default: Any = None) -> Any:
        """Get a field value.

        Args:
            name: Field name
            default: Default if not set

        Returns:
            Field value or default
        """
        if name in self._values:
            return self._values[name]
        if name in self._field_map:
            return self._field_map[name].default
        return default

    def validate(self) -> List[str]:
        """Validate all fields.

        Returns:
            List of validation error messages
        """
        errors = []
        for spec in self.FIELDS:
            value = self._values.get(spec.name)
            if spec.required and value is None:
                errors.append(f"Required field missing: {spec.name}")
            elif value is not None and not spec.validate(value):
                errors.append(f"Invalid value for field: {spec.name}")
        return errors

    def estimate_total_tokens(self) -> int:
        """Estimate total token count for context.

        Returns:
            Estimated token count
        """
        total = 0
        for spec in self.FIELDS:
            value = self._values.get(spec.name)
            if value is not None:
                text = self._value_to_text(value)
                total += estimate_tokens(text)
        return total

    def pack(self, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Pack context into dictionary, applying truncation if needed.

        Args:
            max_tokens: Maximum total tokens (optional)

        Returns:
            Packed context dictionary
        """
        result = {}

        # Sort fields by priority (CRITICAL first)
        priority_order = {
            FieldPriority.CRITICAL: 0,
            FieldPriority.HIGH: 1,
            FieldPriority.MEDIUM: 2,
            FieldPriority.LOW: 3,
        }
        sorted_fields = sorted(
            self.FIELDS,
            key=lambda f: priority_order.get(f.priority, 2),
        )

        remaining_tokens = max_tokens

        for spec in sorted_fields:
            value = self._values.get(spec.name, spec.default)
            if value is None:
                continue

            text = self._value_to_text(value)
            tokens = estimate_tokens(text)

            # Apply field-level max_tokens
            if spec.max_tokens and tokens > spec.max_tokens:
                text = truncate_text(text, spec.max_tokens, spec.truncation)
                tokens = estimate_tokens(text)

            # Apply global budget for non-critical fields
            if remaining_tokens is not None and spec.priority != FieldPriority.CRITICAL:
                if tokens > remaining_tokens:
                    if spec.truncation != TruncationStrategy.NONE:
                        text = truncate_text(text, remaining_tokens, spec.truncation)
                        tokens = estimate_tokens(text)
                    else:
                        # Skip this field if it can't be truncated
                        continue

            result[spec.name] = self._text_to_value(text, value)

            if remaining_tokens is not None:
                remaining_tokens -= tokens
                if remaining_tokens <= 0:
                    break

        return result

    def _value_to_text(self, value: Any) -> str:
        """Convert value to text for token estimation."""
        if isinstance(value, str):
            return value
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _text_to_value(self, text: str, original: Any) -> Any:
        """Convert text back to original value type."""
        if isinstance(original, str):
            return text
        if isinstance(original, (list, dict)):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return original
        return text


# Common field validators
def is_non_empty_string(value: Any) -> bool:
    """Validate non-empty string."""
    return isinstance(value, str) and len(value.strip()) > 0


def is_non_empty_list(value: Any) -> bool:
    """Validate non-empty list."""
    return isinstance(value, list) and len(value) > 0


def is_positive_int(value: Any) -> bool:
    """Validate positive integer."""
    return isinstance(value, int) and value > 0


# Common field transformers
def strip_whitespace(value: str) -> str:
    """Strip leading/trailing whitespace."""
    return value.strip() if isinstance(value, str) else value


def normalize_newlines(value: str) -> str:
    """Normalize newlines to single newline."""
    if isinstance(value, str):
        import re

        return re.sub(r"\n{3,}", "\n\n", value)
    return value
