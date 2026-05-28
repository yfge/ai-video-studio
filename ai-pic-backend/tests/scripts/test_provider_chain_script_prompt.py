import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
sys.path.append(str(REPO_ROOT))
sys.path.append(str(BACKEND_ROOT))

from tests.scripts.provider_chain_fixtures import provider_payload  # noqa: E402

from scripts.harness.production_quality_script import (  # noqa: E402
    provider_chain_script_text,
)
from scripts.harness.provider_chain_payloads import build_script_prompt  # noqa: E402


def test_build_script_prompt_accepts_optional_premise() -> None:
    prompt = build_script_prompt("full-30s", "奖金清零，机器人必须找出真相")

    assert "奖金清零" in prompt
    assert "Create exactly 2 scene" in prompt
    assert "<= 15 visible" in prompt
    assert "one stable protagonist" in prompt
    assert "visible action" in prompt
    assert "specific story turn" in prompt
    assert "Do not use generic speaker names" in prompt
    assert "Scene-level dialogue must not copy any beat dialogue" in prompt
    assert "data already lost" in prompt


def test_build_script_prompt_aligns_with_script_score_pass_rubric() -> None:
    prompt = build_script_prompt("full-30s", "剪辑师发现客户验收文件被改")

    assert "ScriptScore pass" in prompt
    assert "character_recognizability" in prompt
    assert "logic_coherence" in prompt
    assert "clip_ability" in prompt
    assert "角色标签" in prompt
    assert "because/therefore" in prompt
    assert "seed every hidden code, password, account, or backdoor" in prompt
    assert "visual shock + subtitle-friendly dialogue" in prompt
    assert "opposition must literally include" in prompt


def test_build_script_prompt_includes_repair_notes_for_retry() -> None:
    prompt = build_script_prompt(
        "full-30s",
        "剪辑师发现客户验收文件被改",
        repair_notes=[
            "角色辨识度不足：主角缺少固定口头禅",
            "逻辑一致性有漏洞：隐藏密码缺少前置铺垫",
        ],
    )

    assert "Rewrite the previous failed script" in prompt
    assert "角色辨识度不足" in prompt
    assert "隐藏密码缺少前置铺垫" in prompt
    assert "Do not repeat the same plot structure" in prompt


def test_build_script_prompt_blocks_unseeded_backdoor_solutions() -> None:
    prompt = build_script_prompt("full-30s", "剪辑师发现客户验收文件被改")

    assert "different color/material/silhouette" in prompt
    assert "their motive must be visible" in prompt
    assert (
        "Do not use hidden code, password, account, or backdoor as the solution"
        in prompt
    )
    assert "who created it, why it exists, and what limitation it has" in prompt
    assert "secondary character cannot simply reveal the answer" in prompt
    assert "non-screen physical action" in prompt
    assert "opposition motive must be planted before confrontation" in prompt
    assert "do not make an antagonist confess" in prompt
    assert "do not put 删除完成" in prompt
    assert "unknown operator must be seeded in scene 1" in prompt
    assert "permission or account action must name the access rule" in prompt


def test_provider_chain_script_text_preserves_scene_conflict_metadata() -> None:
    text = provider_chain_script_text(provider_payload())

    assert "【冲突】问题：谁把小蓝的奖金倒计时清零？" in text
    assert "代价：15秒内找不到编号，奖金永久清零。" in text
    assert "阻力：时间轴系统拒绝小蓝权限。" in text
    assert "转折：权限拒绝后，日志反向跳出操作者编号。" in text


def test_provider_chain_script_text_preserves_all_character_roles() -> None:
    payload = provider_payload()
    script = json.loads(payload["key_artifacts"]["script"]["raw_content"])
    script["characters"].append(
        {
            "name": "红盾",
            "role": "冷静审核员要维护权限规则",
            "appearance_prompt": "红色方形机器人，绿色扫描眼",
            "consistency_anchor": "red square robot, green scanner eye",
        }
    )
    payload["key_artifacts"]["script"]["raw_content"] = json.dumps(
        script, ensure_ascii=False
    )

    text = provider_chain_script_text(payload)

    assert "▲角色标签：小蓝｜主角｜蓝色卡通机器人，橙色围巾" in text
    assert "▲角色标签：红盾｜冷静审核员要维护权限规则" in text
    assert "red square robot, green scanner eye" in text
