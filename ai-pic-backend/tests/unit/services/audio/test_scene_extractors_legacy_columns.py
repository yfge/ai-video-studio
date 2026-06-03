from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.audio.dialogue_processing.scene_extractors import (
    extract_dialogues_for_scene,
    extract_stage_for_scene,
)


@pytest.mark.unit
def test_reads_script_dialogues_when_content_is_legacy_text() -> None:
    script = MagicMock()
    script.content = "# screenplay\nlegacy rendered text"
    script.dialogues = [
        {"scene_number": 1, "character": "A", "content": "Hello"},
        {"scene_number": 2, "character": "B", "content": "World"},
    ]

    result = extract_dialogues_for_scene(script, 1)

    assert result == [{"scene_number": 1, "character": "A", "content": "Hello"}]


@pytest.mark.unit
def test_reads_script_stage_directions_when_content_is_legacy_text() -> None:
    script = MagicMock()
    script.content = "# screenplay\nlegacy rendered text"
    script.stage_directions = [
        {"scene_number": 1, "content": "Stage direction 1"},
        {"scene_number": 2, "content": "Stage direction 2"},
    ]

    result = extract_stage_for_scene(script, 1)

    assert result == [{"scene_number": 1, "content": "Stage direction 1"}]
