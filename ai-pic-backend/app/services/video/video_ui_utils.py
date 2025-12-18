"""
Video UI utilities.

Provides helper functions for computing video generation UI options
based on provider capabilities.
"""

from typing import Any, Dict, List


def compute_video_ui(
    provider: str,
    model_id: str,
    caps: List[str],
) -> Dict[str, Any]:
    """
    Infer video generation UI options from capabilities and provider rules.

    Args:
        provider: Provider name (e.g., 'keling', 'volcengine', 'minimax').
        model_id: Model identifier.
        caps: List of capability strings.

    Returns:
        Dictionary with UI options including resolution, duration, and feature support.
    """
    resolution_options: List[str] = []
    duration_options: List[int] = []
    supports_watermark = True
    supports_camera_control = "camera_control" in caps
    supports_camera_fixed = "camera_control" in caps

    # Parse capabilities for resolution and duration
    for cap in caps:
        lower = cap.lower()
        # Resolution (e.g., "720p", "1080p")
        if lower.endswith("p") and lower[:-1].isdigit():
            val = lower.upper()
            if val not in resolution_options:
                resolution_options.append(val)
        # Duration (e.g., "5s", "10s")
        if lower.endswith("s"):
            try:
                val = int(lower[:-1])
                if val not in duration_options:
                    duration_options.append(val)
            except ValueError:
                continue

    # Check for end frame support
    supports_end_frame = (
        "image_to_video_start_end_frame" in caps or "first_last_frame" in caps
    )

    # Apply provider-specific defaults
    if provider == "keling":
        resolution_options, duration_options, supports_end_frame, \
            supports_camera_control, supports_watermark = _apply_keling_defaults(
                resolution_options, duration_options, supports_end_frame,
                supports_camera_control
            )

    elif provider == "volcengine":
        resolution_options, duration_options, supports_end_frame, \
            supports_camera_control, supports_camera_fixed, supports_watermark = \
            _apply_volcengine_defaults(
                resolution_options, duration_options, supports_end_frame,
                supports_camera_control, supports_camera_fixed, caps
            )

    elif provider == "minimax":
        resolution_options, duration_options, supports_end_frame, \
            supports_camera_control, supports_camera_fixed, supports_watermark = \
            _apply_minimax_defaults(
                resolution_options, duration_options, supports_end_frame,
                supports_camera_control, supports_camera_fixed, caps
            )

    # Normalize resolution casing
    resolution_options = [r.upper() for r in resolution_options]

    # Default options
    ratio_options = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]
    default_resolution = resolution_options[0] if resolution_options else "720P"
    default_ratio = ratio_options[0]

    return {
        "resolution_options": resolution_options,
        "ratio_options": ratio_options,
        "duration_options": duration_options,
        "supports_end_frame": supports_end_frame,
        "supports_camera_fixed": supports_camera_fixed,
        "supports_camera_control": supports_camera_control,
        "supports_watermark": supports_watermark,
        "default_resolution": default_resolution,
        "default_ratio": default_ratio,
        "default_watermark": False,
    }


def _apply_keling_defaults(
    resolution_options: List[str],
    duration_options: List[int],
    supports_end_frame: bool,
    supports_camera_control: bool,
) -> tuple:
    """Apply Keling provider defaults."""
    if not resolution_options:
        resolution_options = ["1080p", "720p"]
    if not duration_options:
        duration_options = [5, 10]
    supports_end_frame = True
    supports_camera_control = True
    supports_watermark = False
    return resolution_options, duration_options, supports_end_frame, \
        supports_camera_control, supports_watermark


def _apply_volcengine_defaults(
    resolution_options: List[str],
    duration_options: List[int],
    supports_end_frame: bool,
    supports_camera_control: bool,
    supports_camera_fixed: bool,
    caps: List[str],
) -> tuple:
    """Apply Volcengine provider defaults."""
    if not resolution_options:
        resolution_options = ["480p", "720p", "1080p"]
    if not duration_options:
        duration_options = [2, 12]
    supports_camera_fixed = True
    supports_camera_control = supports_camera_control or supports_camera_fixed
    supports_watermark = True
    supports_end_frame = supports_end_frame or "image_to_video_start_end_frame" in caps
    return resolution_options, duration_options, supports_end_frame, \
        supports_camera_control, supports_camera_fixed, supports_watermark


def _apply_minimax_defaults(
    resolution_options: List[str],
    duration_options: List[int],
    supports_end_frame: bool,
    supports_camera_control: bool,
    supports_camera_fixed: bool,
    caps: List[str],
) -> tuple:
    """Apply MiniMax provider defaults."""
    if not resolution_options:
        resolution_options = [
            cap.upper() for cap in caps if cap.endswith("p")
        ] or ["720P", "1080P"]
    if not duration_options:
        duration_options = [6, 10]
    supports_end_frame = supports_end_frame or "first_last_frame" in caps
    supports_camera_fixed = supports_camera_fixed or "camera_control" in caps
    supports_camera_control = supports_camera_control or "camera_control" in caps
    supports_watermark = True
    return resolution_options, duration_options, supports_end_frame, \
        supports_camera_control, supports_camera_fixed, supports_watermark


def compute_image_ui(
    provider: str,
    model_id: str,
    caps: List[str],
) -> Dict[str, Any]:
    """
    Infer image generation UI options (size / aspect ratios).

    Args:
        provider: Provider name.
        model_id: Model identifier.
        caps: List of capability strings.

    Returns:
        Dictionary with size options and aspect ratio support.
    """
    size_options: List[str] = []
    aspect_options = ["1:1", "16:9", "9:16", "4:3", "3:4"]
    supports_aspect_ratio = False

    if provider == "openai":
        if "dall-e-3" in model_id:
            size_options = ["1024x1024", "1024x1792", "1792x1024"]
        elif "dall-e-2" in model_id:
            size_options = ["256x256", "512x512", "1024x1024"]
    elif provider == "volcengine" and "seedream" in model_id:
        size_options = ["2K"]
    elif provider == "keling" and "kling-image" in model_id:
        size_options = ["2k", "1k"]
        supports_aspect_ratio = True
    elif provider == "google":
        supports_aspect_ratio = True

    return {
        "size_options": size_options,
        "aspect_options": aspect_options if supports_aspect_ratio else [],
        "supports_aspect_ratio": supports_aspect_ratio,
        "default_size": size_options[0] if size_options else None,
    }
