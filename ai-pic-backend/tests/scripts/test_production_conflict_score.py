import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
sys.path.append(str(REPO_ROOT))
sys.path.append(str(BACKEND_ROOT))

from tests.scripts.provider_chain_fixtures import provider_payload  # noqa: E402

from scripts.harness.production_quality_script import (  # noqa: E402
    structured_script_score,
)


def test_structured_score_requires_provider_scene_question_and_turn() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene_index, scene in enumerate(script["scenes"], start=1):
        scene["dialogue"][0]["line"] = f"场{scene_index}先查谁"
        for beat_index, beat in enumerate(scene["beats"], start=1):
            beat["dialogue"][0]["line"] = f"线索{scene_index}{beat_index}变了"
        scene["question"] = "推进剧情"
        scene["turn"] = ""
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_conflict_question" in result["failed_checks"]
    assert "scene_conflict_turn" in result["failed_checks"]


def test_structured_score_rejects_abstract_provider_stakes_and_opposition() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        scene["stakes"] = "小蓝压力越来越大"
        scene["opposition"] = "混乱局面阻止小蓝继续查"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "scene_conflict_stakes" in result["failed_checks"]
    assert "scene_conflict_opposition" in result["failed_checks"]
