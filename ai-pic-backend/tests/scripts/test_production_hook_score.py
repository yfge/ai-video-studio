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


def test_structured_score_rejects_slow_provider_opening_hook() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    for beat, duration in zip(script["scenes"][0]["beats"], [5, 5, 5], strict=True):
        beat["duration_seconds"] = duration
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "opening_hook_duration" in result["failed_checks"]


def test_structured_score_rejects_provider_opening_hook_without_immediate_threat() -> (
    None
):
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    first_beat = script["scenes"][0]["beats"][0]
    first_beat["visible_event"] = "小蓝推开玻璃门，灯带依次亮起"
    first_beat["action"] = ["小蓝把背包放到桌面，整理围巾"]
    first_beat["dialogue"] = [{"speaker": "小蓝", "line": "我到了"}]
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "opening_hook_substance" in result["failed_checks"]


def test_structured_score_accepts_opening_warning_as_immediate_threat() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    first_beat = script["scenes"][0]["beats"][0]
    first_beat["visible_event"] = "小蓝盯着屏幕，系统弹出无钩子警告"
    first_beat["action"] = ["小蓝按住红色提示框，调出剪辑面板"]
    first_beat["dialogue"] = [{"speaker": "小蓝", "line": "警告来了"}]
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert "opening_hook_substance" not in result["failed_checks"]
