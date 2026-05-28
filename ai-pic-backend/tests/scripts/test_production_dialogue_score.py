import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
sys.path.append(str(REPO_ROOT))
sys.path.append(str(BACKEND_ROOT))

from tests.scripts.provider_chain_fixtures import provider_payload  # noqa: E402

from scripts.harness.production_dialogue_score import (  # noqa: E402
    dialogue_failed_checks,
)
from scripts.harness.production_quality_script import (  # noqa: E402
    structured_script_score,
)


def test_structured_score_rejects_repeated_provider_dialogue_lines() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for scene in script["scenes"]:
        scene["dialogue"][0]["line"] = "证据在这里"
        for beat in scene["beats"]:
            beat["dialogue"][0]["line"] = "证据在这里"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "dialogue_progression_repetition" in result["failed_checks"]


def test_dialogue_score_allows_scene_dialogue_source_to_mirror_unique_beats() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    scene = script["scenes"][0]
    scene["dialogue"] = [
        {"speaker": "小蓝", "line": "时间轴谁改"},
        {"speaker": "小蓝", "line": "权限没了"},
    ]

    failed_checks = dialogue_failed_checks(script["scenes"])

    assert "dialogue_progression_repetition" not in failed_checks


def test_structured_score_rejects_long_provider_dialogue_line() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    line = script["scenes"][0]["beats"][0]["dialogue"][0]
    line["line"] = "这条线索必须马上交给审计员核对签名"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "dialogue_line_length" in result["failed_checks"]
