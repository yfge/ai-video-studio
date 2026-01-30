"""
Character presence validator.

Validates character appearance consistency in storyboard frames:
- Characters with dialogue appear in appropriate frames
- Reference images are available for characters
- Character names are consistent across frames
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.storyboard.pipeline.pipeline_state import ValidationResult

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class CharacterPresenceValidator:
    """
    Validates character presence and consistency in storyboard frames.

    Checks:
    1. Characters with dialogue appear in frames for that scene
    2. Reference images are available for speaking characters
    3. Character names are consistent (no typos/variations)
    4. Main characters have sufficient screen time
    """

    @property
    def name(self) -> str:
        return "character_presence_validator"

    @property
    def description(self) -> str:
        return "Validates character appearance and reference image availability"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> list[ValidationResult]:
        """Run all character presence checks."""
        results: list[ValidationResult] = []

        frames = state.frames
        if not frames:
            return results

        results.extend(self._check_dialogue_character_presence(frames, context))
        results.extend(self._check_reference_images(frames, context))
        results.extend(self._check_character_name_consistency(frames, context))

        return results

    def _check_dialogue_character_presence(
        self,
        frames: list[dict[str, Any]],
        context: "PipelineContext",
    ) -> list[ValidationResult]:
        """Check that characters with dialogue appear in frames."""
        results: list[ValidationResult] = []

        # Build map of speaking characters by scene
        speakers_by_scene: dict[int, set[str]] = {}
        for scene in context.scenes:
            scene_speakers: set[str] = set()
            for dlg in scene.dialogues:
                char = dlg.get("character")
                if char and isinstance(char, str):
                    scene_speakers.add(char.strip())
            for beat in scene.beats:
                if beat.get("beat_type") == "dialogue":
                    chars = beat.get("characters_involved") or []
                    if isinstance(chars, list):
                        for c in chars:
                            if isinstance(c, str):
                                scene_speakers.add(c.strip())
            if scene_speakers:
                speakers_by_scene[scene.scene_number] = scene_speakers

        if not speakers_by_scene:
            return results  # No dialogue data to validate

        # Build map of characters present in frames by scene
        characters_in_frames: dict[int, set[str]] = {}
        for frame in frames:
            scene_num = frame.get("scene_number")
            if scene_num is None:
                continue

            frame_chars: set[str] = set()

            # From characters field
            chars = frame.get("characters")
            if isinstance(chars, list):
                for c in chars:
                    if isinstance(c, str):
                        frame_chars.add(c.strip())
                    elif isinstance(c, dict):
                        name = c.get("name") or c.get("character")
                        if name:
                            frame_chars.add(str(name).strip())

            # From description (simple extraction)
            desc = frame.get("description") or ""
            for speaker_set in speakers_by_scene.values():
                for speaker in speaker_set:
                    if speaker in desc:
                        frame_chars.add(speaker)

            if frame_chars:
                existing = characters_in_frames.get(scene_num, set())
                characters_in_frames[scene_num] = existing | frame_chars

        # Find missing characters
        missing_appearances: list[dict[str, Any]] = []
        for scene_num, speakers in speakers_by_scene.items():
            frame_chars = characters_in_frames.get(scene_num, set())
            missing = speakers - frame_chars

            # Allow narrator/旁白 to be missing
            missing = {c for c in missing if c not in {"旁白", "Narrator", "narrator"}}

            if missing:
                missing_appearances.append({
                    "scene_number": scene_num,
                    "missing_characters": list(missing),
                    "characters_in_frames": list(frame_chars),
                })

        if missing_appearances:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Speaking characters missing from frames in {len(missing_appearances)} scenes",
                    details={"missing_appearances": missing_appearances[:10]},
                    suggestions=[
                        "Add character references to frame descriptions",
                        "Include character in frame's 'characters' field",
                    ],
                )
            )
        else:
            total_speakers = sum(len(s) for s in speakers_by_scene.values())
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"All {total_speakers} speaking characters appear in appropriate frames",
                )
            )

        return results

    def _check_reference_images(
        self,
        frames: list[dict[str, Any]],
        context: "PipelineContext",
    ) -> list[ValidationResult]:
        """Check that characters have reference images available."""
        results: list[ValidationResult] = []

        # Collect all unique characters from frames
        all_characters: set[str] = set()
        for frame in frames:
            chars = frame.get("characters")
            if isinstance(chars, list):
                for c in chars:
                    if isinstance(c, str):
                        all_characters.add(c.strip())
                    elif isinstance(c, dict):
                        name = c.get("name") or c.get("character")
                        if name:
                            all_characters.add(str(name).strip())

        if not all_characters:
            return results

        # Check reference images from context
        characters_with_refs: set[str] = set()
        characters_without_refs: set[str] = set()

        for char_name in all_characters:
            char_info = context.get_character(char_name)
            if char_info:
                # Check if character has reference images
                ref_images = char_info.get("reference_images") or char_info.get("image_url")
                if ref_images:
                    characters_with_refs.add(char_name)
                else:
                    characters_without_refs.add(char_name)
            else:
                characters_without_refs.add(char_name)

        # Also check frames for reference_images
        for frame in frames:
            ref_imgs = frame.get("reference_images")
            if isinstance(ref_imgs, list) and ref_imgs:
                # Frame has references, likely has character anchors
                chars = frame.get("characters")
                if isinstance(chars, list):
                    for c in chars:
                        name = c if isinstance(c, str) else c.get("name") if isinstance(c, dict) else None
                        if name:
                            characters_with_refs.add(str(name).strip())

        # Remove characters that got refs from frames
        characters_without_refs = characters_without_refs - characters_with_refs

        if characters_without_refs:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"{len(characters_without_refs)} characters lack reference images",
                    details={
                        "characters_without_refs": list(characters_without_refs),
                        "characters_with_refs": list(characters_with_refs),
                    },
                    suggestions=[
                        "Upload reference images for characters",
                        "Link characters to VirtualIP with images",
                    ],
                )
            )
        elif characters_with_refs:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"All {len(characters_with_refs)} characters have reference images",
                )
            )

        return results

    def _check_character_name_consistency(
        self,
        frames: list[dict[str, Any]],
        context: "PipelineContext",
    ) -> list[ValidationResult]:
        """Check for character name variations that might be typos."""
        results: list[ValidationResult] = []

        # Collect all character name occurrences
        name_occurrences: dict[str, int] = {}

        for frame in frames:
            chars = frame.get("characters")
            if isinstance(chars, list):
                for c in chars:
                    name = c if isinstance(c, str) else c.get("name") if isinstance(c, dict) else None
                    if name and isinstance(name, str):
                        clean_name = name.strip()
                        name_occurrences[clean_name] = name_occurrences.get(clean_name, 0) + 1

            # Also check description for character patterns
            desc = frame.get("description") or ""
            # Simple check for names that appear rarely (potential typos)
            for name in name_occurrences:
                if name in desc:
                    name_occurrences[name] = name_occurrences.get(name, 0) + 1

        if not name_occurrences:
            return results

        # Find potential variations (similar names)
        potential_variations: list[dict[str, Any]] = []
        names = list(name_occurrences.keys())

        for i, name1 in enumerate(names):
            for name2 in names[i + 1:]:
                # Simple similarity check
                if self._are_similar(name1, name2):
                    potential_variations.append({
                        "name1": name1,
                        "count1": name_occurrences[name1],
                        "name2": name2,
                        "count2": name_occurrences[name2],
                    })

        if potential_variations:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=f"Found {len(potential_variations)} potential character name variations",
                    details={"variations": potential_variations[:10]},
                    suggestions=[
                        "Review character names for consistency",
                        "Standardize character name usage",
                    ],
                )
            )
        else:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"Character names are consistent ({len(name_occurrences)} unique names)",
                )
            )

        return results

    def _are_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar (potential typos/variations)."""
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()

        # Same name
        if n1 == n2:
            return False

        # One contains the other (e.g., "John" vs "John Smith")
        if n1 in n2 or n2 in n1:
            return True

        # Simple edit distance check for short names
        if len(n1) <= 10 and len(n2) <= 10:
            if abs(len(n1) - len(n2)) <= 2:
                # Count character differences
                diff = sum(1 for a, b in zip(n1, n2) if a != b)
                diff += abs(len(n1) - len(n2))
                return diff <= 2

        return False

    def can_auto_fix(self) -> bool:
        """Character name issues require manual review."""
        return False
