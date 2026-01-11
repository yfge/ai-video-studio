from __future__ import annotations

from typing import Any, Dict

from .manager import AIModelType


class ModelUiMixin:
    @staticmethod
    def _apply_ui_metadata(model: Dict[str, Any]) -> Dict[str, Any]:
        """Attach UI-facing defaults/options based on provider/model id/capabilities."""
        provider = (model.get("provider") or "").lower()
        mid = (model.get("id") or model.get("model_id") or "").lower()
        caps = [str(c).lower() for c in model.get("capabilities") or []]
        model_type = (model.get("type") or "").lower()

        metadata = dict(model.get("metadata") or {})
        ui_meta = dict(metadata.get("ui") or {})

        if model_type == AIModelType.IMAGE_TO_VIDEO.value:
            computed = ModelUiMixin._compute_video_ui(provider, mid, caps)
            ui_meta = {**computed, **ui_meta} if computed else ui_meta
        elif model_type in (
            AIModelType.TEXT_TO_IMAGE.value,
            AIModelType.IMAGE_TO_IMAGE.value,
        ):
            computed = ModelUiMixin._compute_image_ui(provider, mid, caps)
            ui_meta = {**computed, **ui_meta} if computed else ui_meta

        if ui_meta:
            metadata["ui"] = ui_meta
            model["metadata"] = metadata
        return model

    @staticmethod
    def _compute_video_ui(
        provider: str, model_id: str, caps: list[str]
    ) -> Dict[str, Any]:
        """Infer video generation UI options from capabilities and provider rules."""
        resolution_options: list[str] = []
        duration_options: list[int] = []
        supports_watermark = True
        supports_camera_control = "camera_control" in caps

        for cap in caps:
            lower = cap.lower()
            if lower.endswith("p") and lower[:-1].isdigit():
                val = lower.upper()
                if val not in resolution_options:
                    resolution_options.append(val)
            if lower.endswith("s"):
                try:
                    val = int(lower[:-1])
                    if val not in duration_options:
                        duration_options.append(val)
                except ValueError:
                    continue

        supports_end_frame = (
            "image_to_video_start_end_frame" in caps or "first_last_frame" in caps
        )
        supports_camera_fixed = "camera_control" in caps

        # Provider specific defaults
        if provider == "keling":
            if not resolution_options:
                resolution_options = ["1080p", "720p"]
            if not duration_options:
                duration_options = [5, 10]
            supports_end_frame = True
            supports_camera_control = True
            supports_watermark = False
        if provider == "volcengine":
            if not resolution_options:
                resolution_options = ["480p", "720p", "1080p"]
            if not duration_options:
                duration_options = [2, 12]
            supports_camera_fixed = True
            supports_camera_control = supports_camera_control or supports_camera_fixed
            supports_watermark = True
            supports_end_frame = (
                supports_end_frame or "image_to_video_start_end_frame" in caps
            )
        if provider == "minimax":
            if not resolution_options:
                resolution_options = [
                    cap.upper() for cap in caps if cap.endswith("p")
                ] or ["720P", "1080P"]
            if not duration_options:
                duration_options = [6, 10]
            supports_end_frame = supports_end_frame or "first_last_frame" in caps
            supports_camera_fixed = supports_camera_fixed or "camera_control" in caps
            supports_camera_control = (
                supports_camera_control or "camera_control" in caps
            )
            supports_watermark = True

        # Normalize casing
        resolution_options = [r.upper() for r in resolution_options]

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

    @staticmethod
    def _compute_image_ui(
        provider: str, model_id: str, caps: list[str]
    ) -> Dict[str, Any]:
        """Infer image generation UI options (size / aspect ratios)."""
        size_options: list[str] = []
        aspect_options = ["1:1", "16:9", "9:16", "4:3", "3:4"]
        supports_aspect_ratio = False

        if provider == "openai":
            if "dall-e-3" in model_id:
                size_options = ["1024x1024", "1024x1792", "1792x1024"]
            elif "dall-e-2" in model_id:
                size_options = ["256x256", "512x512", "1024x1024"]
        elif provider == "volcengine" and "seedream" in model_id:
            size_options = ["2K"]
        elif provider == "keling" and (
            "kling-image" in model_id or model_id.startswith("kling-v")
        ):
            size_options = ["2k", "1k"]
            supports_aspect_ratio = True
        elif provider == "google":
            supports_aspect_ratio = True

        return {
            "size_options": size_options,
            "aspect_ratio_options": aspect_options,
            "supports_aspect_ratio": supports_aspect_ratio,
            "supports_reference_image": "image_to_image" in caps
            or "image_to_image" in provider
            or provider == "keling",
        }
