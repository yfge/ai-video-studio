"""
Frame integrity validator.

Validates structural integrity of storyboard frames, ensuring:
- Required fields are present
- URL fields are valid when set
- Each scene has minimum required frames
- Frame numbering is correct
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.services.storyboard.pipeline.pipeline_state import ValidationResult

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class FrameIntegrityValidator:
    """
    Validates structural integrity of storyboard frames.

    Checks:
    1. Required fields: frame_id, description, scene_number
    2. URL fields are valid when present
    3. Each scene has minimum frames (configurable)
    4. Frame numbering is sequential and unique
    """

    # Minimum frames per scene (can be overridden)
    MIN_FRAMES_PER_SCENE = 1

    # Required fields for each frame
    REQUIRED_FIELDS = ["frame_id", "description"]

    # Optional but recommended fields
    RECOMMENDED_FIELDS = ["scene_number", "duration_seconds"]

    # URL fields to validate
    URL_FIELDS = [
        "image_url",
        "start_image_url",
        "end_image_url",
        "video_url",
        "video_thumbnail_url",
    ]

    # Simple URL pattern
    URL_PATTERN = re.compile(
        r"^https?://[^\s<>\"{}|\\^`\[\]]+$|^data:image/[a-zA-Z]+;base64,",
        re.IGNORECASE,
    )

    @property
    def name(self) -> str:
        return "frame_integrity_validator"

    @property
    def description(self) -> str:
        return "Validates frame structure and required fields"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        min_frames_per_scene: int | None = None,
        **kwargs: Any,
    ) -> list[ValidationResult]:
        """Run all frame integrity checks."""
        results: list[ValidationResult] = []

        frames = state.frames
        if not frames:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message="No frames to validate",
                    suggestions=["Generate storyboard frames first"],
                )
            )
            return results

        min_frames = min_frames_per_scene or self.MIN_FRAMES_PER_SCENE

        results.extend(self._check_required_fields(frames))
        results.extend(self._check_recommended_fields(frames))
        results.extend(self._check_url_fields(frames))
        results.extend(self._check_frame_numbering(frames))
        results.extend(self._check_frames_per_scene(frames, min_frames))

        return results

    def _check_required_fields(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check that all required fields are present."""
        results: list[ValidationResult] = []
        missing_by_field: dict[str, list[int]] = {}

        for i, frame in enumerate(frames):
            for field in self.REQUIRED_FIELDS:
                value = frame.get(field)
                if value is None or (isinstance(value, str) and not value.strip()):
                    missing_by_field.setdefault(field, []).append(i + 1)

        if missing_by_field:
            for field, frame_indices in missing_by_field.items():
                results.append(
                    ValidationResult.error(
                        validator_name=self.name,
                        message=f"Missing required field '{field}' in {len(frame_indices)} frames",
                        details={
                            "field": field,
                            "frame_indices": frame_indices[:20],
                            "total_missing": len(frame_indices),
                        },
                        suggestions=[
                            f"Populate '{field}' for all frames",
                            "Re-generate frames with complete data",
                        ],
                    )
                )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"All {len(frames)} frames have required fields",
                    details={"required_fields": self.REQUIRED_FIELDS},
                )
            )

        return results

    def _check_recommended_fields(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check recommended fields and warn if missing."""
        results: list[ValidationResult] = []
        missing_by_field: dict[str, int] = {}

        for frame in frames:
            for field in self.RECOMMENDED_FIELDS:
                if frame.get(field) is None:
                    missing_by_field[field] = missing_by_field.get(field, 0) + 1

        for field, count in missing_by_field.items():
            if count > len(frames) * 0.5:  # More than 50% missing
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=f"Field '{field}' missing in {count}/{len(frames)} frames",
                        details={"field": field, "missing_count": count},
                        suggestions=[f"Consider populating '{field}' for better timeline accuracy"],
                    )
                )

        return results

    def _check_url_fields(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check that URL fields contain valid URLs when set."""
        results: list[ValidationResult] = []
        invalid_urls: list[dict[str, Any]] = []

        for i, frame in enumerate(frames):
            for field in self.URL_FIELDS:
                url = frame.get(field)
                if url and isinstance(url, str):
                    if not self.URL_PATTERN.match(url):
                        invalid_urls.append({
                            "frame_index": i + 1,
                            "field": field,
                            "url_preview": url[:100],
                        })

            # Check URL list fields
            for list_field in ["reference_images", "start_image_urls", "end_image_urls"]:
                urls = frame.get(list_field)
                if isinstance(urls, list):
                    for j, url in enumerate(urls):
                        if url and isinstance(url, str):
                            if not self.URL_PATTERN.match(url):
                                invalid_urls.append({
                                    "frame_index": i + 1,
                                    "field": f"{list_field}[{j}]",
                                    "url_preview": url[:100],
                                })

        if invalid_urls:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Found {len(invalid_urls)} potentially invalid URLs",
                    details={"invalid_urls": invalid_urls[:10]},
                    suggestions=[
                        "Verify URL format and accessibility",
                        "Remove invalid URLs or regenerate assets",
                    ],
                )
            )
        else:
            # Count frames with generated assets
            frames_with_images = sum(
                1 for f in frames if f.get("image_url") or f.get("start_image_url")
            )
            frames_with_video = sum(1 for f in frames if f.get("video_url"))

            if frames_with_images or frames_with_video:
                results.append(
                    ValidationResult.success(
                        validator_name=self.name,
                        message="All URL fields are valid",
                        details={
                            "frames_with_images": frames_with_images,
                            "frames_with_video": frames_with_video,
                        },
                    )
                )

        return results

    def _check_frame_numbering(
        self, frames: list[dict[str, Any]]
    ) -> list[ValidationResult]:
        """Check frame numbering is sequential and unique."""
        results: list[ValidationResult] = []

        frame_numbers = []
        frame_ids = set()
        duplicate_ids: list[str] = []

        for frame in frames:
            fn = frame.get("frame_number")
            if fn is not None:
                frame_numbers.append(fn)

            fid = frame.get("frame_id")
            if fid:
                if fid in frame_ids:
                    duplicate_ids.append(fid)
                frame_ids.add(fid)

        if duplicate_ids:
            results.append(
                ValidationResult.error(
                    validator_name=self.name,
                    message=f"Found {len(duplicate_ids)} duplicate frame_id values",
                    details={"duplicate_ids": duplicate_ids[:10]},
                    suggestions=["Regenerate frame IDs to ensure uniqueness"],
                )
            )

        if frame_numbers:
            sorted_numbers = sorted(frame_numbers)
            expected = list(range(1, len(frame_numbers) + 1))

            if sorted_numbers != expected:
                # Find issues
                missing = set(expected) - set(sorted_numbers)
                duplicates = [n for n in sorted_numbers if sorted_numbers.count(n) > 1]

                if missing or duplicates:
                    results.append(
                        ValidationResult.warning(
                            validator_name=self.name,
                            message="Frame numbering is not sequential",
                            details={
                                "missing_numbers": list(missing)[:10],
                                "duplicate_numbers": list(set(duplicates))[:10],
                                "actual_range": f"{min(sorted_numbers)}-{max(sorted_numbers)}",
                            },
                            suggestions=[
                                "Renumber frames sequentially",
                                "Use auto_fix to correct numbering",
                            ],
                        )
                    )
            else:
                results.append(
                    ValidationResult.success(
                        validator_name=self.name,
                        message="Frame numbering is sequential and valid",
                        details={"frame_count": len(frame_numbers)},
                    )
                )

        return results

    def _check_frames_per_scene(
        self,
        frames: list[dict[str, Any]],
        min_frames: int,
    ) -> list[ValidationResult]:
        """Check that each scene has minimum required frames."""
        results: list[ValidationResult] = []

        frames_by_scene: dict[int, int] = {}
        for frame in frames:
            scene_num = frame.get("scene_number")
            if scene_num is not None:
                frames_by_scene[scene_num] = frames_by_scene.get(scene_num, 0) + 1

        if not frames_by_scene:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message="No frames have scene_number assigned",
                    suggestions=["Assign scene numbers to frames"],
                )
            )
            return results

        insufficient_scenes: list[dict[str, int]] = []
        for scene_num, count in sorted(frames_by_scene.items()):
            if count < min_frames:
                insufficient_scenes.append({
                    "scene_number": scene_num,
                    "frame_count": count,
                    "minimum": min_frames,
                })

        if insufficient_scenes:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"{len(insufficient_scenes)} scenes have fewer than {min_frames} frames",
                    details={"insufficient_scenes": insufficient_scenes},
                    suggestions=[
                        "Generate additional frames for scenes below minimum",
                        "Consider reducing minimum frames requirement",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"All {len(frames_by_scene)} scenes have >= {min_frames} frames",
                    details={
                        "scenes": len(frames_by_scene),
                        "total_frames": len(frames),
                        "frames_per_scene": dict(frames_by_scene),
                    },
                )
            )

        return results

    def can_auto_fix(self) -> bool:
        """Frame numbering issues can be auto-fixed."""
        return True

    def auto_fix(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        issues: list[ValidationResult],
    ) -> tuple["PipelineState", list[str]]:
        """Auto-fix frame numbering and missing frame IDs."""
        from uuid import uuid4

        fixes: list[str] = []

        # Fix missing frame_ids
        for frame in state.frames:
            if not frame.get("frame_id"):
                frame["frame_id"] = str(uuid4())
                fixes.append("Generated missing frame_id")

        # Renumber frames sequentially
        for i, frame in enumerate(state.frames, 1):
            if frame.get("frame_number") != i:
                frame["frame_number"] = i
                fixes.append(f"Renumbered frame to {i}")

        return state, fixes
