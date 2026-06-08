"""Video generation capabilities registry.

Centralizes provider/model/resolution → allowed durations mapping and provides
auditable capability resolution for video generation tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger()


@dataclass(frozen=True)
class VideoCapability:
    """Capability specification for a video generation configuration."""

    provider: str
    model_pattern: str  # Substring match against model_id
    allowed_durations: tuple[int, ...]
    min_duration: int
    max_duration: int
    resolution_constraints: Optional[Dict[str, tuple[int, ...]]] = None
    notes: str = ""


@dataclass
class CapabilityMatch:
    """Result of capability lookup with audit information."""

    provider: str
    model: str
    resolution: Optional[str]
    target_duration_seconds: float
    provider_duration_seconds: int
    allowed_durations: List[int]
    needs_split: bool
    capability_source: str  # e.g. "veo-3.1@1080p", "keling-v2", "default"
    audit_notes: List[str] = field(default_factory=list)


# =============================================================================
# Capability Registry
# =============================================================================

# Google Veo models
GOOGLE_VEO_CAPABILITIES: List[VideoCapability] = [
    VideoCapability(
        provider="google",
        model_pattern="veo-3.1",
        allowed_durations=(4, 6, 8),
        min_duration=4,
        max_duration=8,
        resolution_constraints={
            "1080p": (8,),  # 1080p only supports 8s
        },
        notes="Veo 3.1 supports 4/6/8s at 720p, only 8s at 1080p",
    ),
    VideoCapability(
        provider="google",
        model_pattern="veo-3.0",
        allowed_durations=(8,),
        min_duration=8,
        max_duration=8,
        notes="Veo 3.0 only supports 8s",
    ),
    VideoCapability(
        provider="google",
        model_pattern="veo-2.0",
        allowed_durations=(5, 6, 8),
        min_duration=5,
        max_duration=8,
        notes="Veo 2.0 supports 5/6/8s",
    ),
]

# Keling models
KELING_CAPABILITIES: List[VideoCapability] = [
    VideoCapability(
        provider="keling",
        model_pattern="kling",
        allowed_durations=(5, 10),
        min_duration=5,
        max_duration=10,
        notes="Keling supports 5s or 10s video generation",
    ),
]

# MiniMax models
MINIMAX_CAPABILITIES: List[VideoCapability] = [
    VideoCapability(
        provider="minimax",
        model_pattern="hailuo",
        allowed_durations=(6, 10),
        min_duration=6,
        max_duration=10,
        notes="MiniMax Hailuo supports 6s or 10s",
    ),
    VideoCapability(
        provider="minimax",
        model_pattern="minimax",
        allowed_durations=(6, 10),
        min_duration=6,
        max_duration=10,
        notes="MiniMax default supports 6s or 10s",
    ),
]

# Volcengine models
VOLCENGINE_CAPABILITIES: List[VideoCapability] = [
    VideoCapability(
        provider="volcengine",
        model_pattern="",  # Match all volcengine models
        allowed_durations=(4, 6, 8),
        min_duration=4,
        max_duration=8,
        notes="Volcengine default video durations",
    ),
]

# Default fallback
DEFAULT_CAPABILITY = VideoCapability(
    provider="default",
    model_pattern="",
    allowed_durations=(4, 6, 8),
    min_duration=4,
    max_duration=8,
    notes="Default video generation capability",
)

# Combined registry
ALL_CAPABILITIES: List[VideoCapability] = (
    GOOGLE_VEO_CAPABILITIES
    + KELING_CAPABILITIES
    + MINIMAX_CAPABILITIES
    + VOLCENGINE_CAPABILITIES
)


def _normalize_provider(provider: Optional[str]) -> str:
    """Normalize provider name for lookup."""
    if not provider:
        return ""
    return str(provider).lower().strip()


def _normalize_model(model: Optional[str]) -> str:
    """Normalize model ID for pattern matching."""
    if not model:
        return ""
    return str(model).lower().strip()


def _normalize_resolution(resolution: Optional[str]) -> Optional[str]:
    """Normalize resolution string."""
    if not resolution:
        return None
    res = str(resolution).lower().strip()
    if res.endswith("p"):
        return res
    if "x" in res:
        parts = res.split("x", 1)
        try:
            width = int(parts[0])
            height = int(parts[1])
        except (TypeError, ValueError):
            return None
        if (width, height) == (1280, 720):
            return "720p"
        if (width, height) == (1920, 1080):
            return "1080p"
    return res


def find_capability(
    *,
    provider: Optional[str],
    model: Optional[str],
    resolution: Optional[str] = None,
) -> VideoCapability:
    """Find the best matching capability for provider/model/resolution.

    Returns the most specific capability match or DEFAULT_CAPABILITY.
    """
    norm_provider = _normalize_provider(provider)
    norm_model = _normalize_model(model)

    for cap in ALL_CAPABILITIES:
        if cap.provider != norm_provider:
            continue
        if cap.model_pattern and cap.model_pattern not in norm_model:
            continue
        return cap

    return DEFAULT_CAPABILITY


def get_allowed_durations(
    *,
    provider: Optional[str],
    model: Optional[str],
    resolution: Optional[str] = None,
) -> List[int]:
    """Get allowed durations for provider/model/resolution combination.

    Handles resolution-specific constraints (e.g., Veo 3.1 at 1080p only supports 8s).
    """
    cap = find_capability(provider=provider, model=model, resolution=resolution)
    norm_resolution = _normalize_resolution(resolution)

    # Check resolution-specific constraints
    if cap.resolution_constraints and norm_resolution:
        res_durations = cap.resolution_constraints.get(norm_resolution)
        if res_durations:
            return list(res_durations)

    return list(cap.allowed_durations)


def resolve_video_duration(
    *,
    provider: Optional[str],
    model: Optional[str],
    target_duration_seconds: float,
    resolution: Optional[str] = None,
) -> CapabilityMatch:
    """Resolve target duration to provider-compatible duration with full audit info.

    This is the main entry point for the capabilities registry. It returns
    a CapabilityMatch with:
    - provider_duration_seconds: The duration to send to the provider
    - needs_split: Whether the target exceeds max allowed and needs splitting
    - capability_source: Identifier for the capability used
    - audit_notes: Human-readable notes about the resolution
    """
    cap = find_capability(provider=provider, model=model, resolution=resolution)
    allowed = get_allowed_durations(
        provider=provider, model=model, resolution=resolution
    )
    norm_resolution = _normalize_resolution(resolution)

    # Build capability source identifier
    if cap.resolution_constraints and norm_resolution in (
        cap.resolution_constraints or {}
    ):
        source = f"{cap.provider}/{cap.model_pattern or 'default'}@{norm_resolution}"
    elif cap.model_pattern:
        source = f"{cap.provider}/{cap.model_pattern}"
    else:
        source = cap.provider or "default"

    # Normalize target
    try:
        target = float(target_duration_seconds)
    except (TypeError, ValueError):
        target = 5.0
    if target <= 0:
        target = 5.0

    # Apply ceil-to-allowed strategy
    min_allowed = min(allowed) if allowed else 4
    max_allowed = max(allowed) if allowed else 8
    needs_split = target > max_allowed

    audit_notes: List[str] = []

    if target <= min_allowed:
        provider_seconds = min_allowed
        audit_notes.append(f"Target {target}s below min, using {min_allowed}s")
    elif needs_split:
        provider_seconds = max_allowed
        audit_notes.append(
            f"Target {target}s exceeds max {max_allowed}s, using max (needs split)"
        )
    else:
        # Find smallest allowed >= target
        provider_seconds = max_allowed
        for candidate in sorted(allowed):
            if candidate >= target:
                provider_seconds = candidate
                break
        if abs(provider_seconds - target) > 0.01:
            audit_notes.append(f"Target {target}s ceiled to {provider_seconds}s")

    if cap.notes:
        audit_notes.append(cap.notes)

    match = CapabilityMatch(
        provider=_normalize_provider(provider) or "unknown",
        model=_normalize_model(model) or "unknown",
        resolution=norm_resolution,
        target_duration_seconds=target,
        provider_duration_seconds=provider_seconds,
        allowed_durations=allowed,
        needs_split=needs_split,
        capability_source=source,
        audit_notes=audit_notes,
    )

    # Log for audit
    logger.info(
        "video_capability_resolved",
        extra={
            "provider": match.provider,
            "model": match.model,
            "resolution": match.resolution,
            "target_duration": match.target_duration_seconds,
            "provider_duration": match.provider_duration_seconds,
            "allowed_durations": match.allowed_durations,
            "needs_split": match.needs_split,
            "capability_source": match.capability_source,
        },
    )

    return match


def get_capability_summary() -> Dict[str, Any]:
    """Get a summary of all registered capabilities for debugging/documentation."""
    return {
        "providers": {
            "google": [
                {
                    "pattern": c.model_pattern,
                    "durations": c.allowed_durations,
                    "resolution_constraints": c.resolution_constraints,
                    "notes": c.notes,
                }
                for c in GOOGLE_VEO_CAPABILITIES
            ],
            "keling": [
                {
                    "pattern": c.model_pattern,
                    "durations": c.allowed_durations,
                    "notes": c.notes,
                }
                for c in KELING_CAPABILITIES
            ],
            "minimax": [
                {
                    "pattern": c.model_pattern,
                    "durations": c.allowed_durations,
                    "notes": c.notes,
                }
                for c in MINIMAX_CAPABILITIES
            ],
            "volcengine": [
                {
                    "pattern": c.model_pattern,
                    "durations": c.allowed_durations,
                    "notes": c.notes,
                }
                for c in VOLCENGINE_CAPABILITIES
            ],
        },
        "default": {
            "durations": DEFAULT_CAPABILITY.allowed_durations,
            "notes": DEFAULT_CAPABILITY.notes,
        },
    }
