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


def test_structured_score_rejects_resolved_provider_final_cliffhanger() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    final_scene = script["scenes"][-1]
    final_beat = final_scene["beats"][-1]
    final_scene["turn"] = "小蓝拿回全部奖金后，控制台显示任务完成。"
    final_beat["beat_type"] = "cliffhanger"
    final_beat["visible_event"] = "小蓝拿回全部奖金，系统显示任务完成"
    final_beat["action"] = ["小蓝举起到账屏幕，警报灯全部熄灭"]
    final_beat["dialogue"][0]["line"] = "奖金全拿回"
    final_beat["cliffhanger_tag"] = "case_closed"
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    result = structured_script_score(payload)

    assert result["passed"] is False
    assert "cliffhanger_unresolved_threat" in result["failed_checks"]
