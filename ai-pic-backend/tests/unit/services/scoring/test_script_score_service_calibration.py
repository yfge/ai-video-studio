"""
Calibration and provider-schema tests for ScriptScoreService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.providers.base import AIModelType, AIResponse, AITaskType
from app.services.scoring.script_score_schema import script_score_json_schema
from app.services.scoring.script_score_service import ScriptScoreService


@pytest.fixture
def mock_ai_service():
    service = MagicMock()
    service.ai_manager = MagicMock()
    service.ai_manager.generate_text = AsyncMock()
    return service


@pytest.fixture
def score_service(mock_ai_service):
    return ScriptScoreService(mock_ai_service)


@pytest.mark.asyncio
async def test_score_script_does_not_override_model_score_for_fixed_phrases(
    score_service, mock_ai_service
):
    mock_ai_service.ai_manager.generate_text.return_value = AIResponse(
        success=True,
        data="""
        ```json
        {
            "overall_score": 4.0,
            "dimension_scores": {
                "conflict_intensity": 4.0,
                "character_recognizability": 3.5,
                "cultural_fit": 4.5,
                "clip_ability": 4.0,
                "logic_coherence": 3.5
            },
            "verdict": "review",
            "strengths": ["开场冲突强"],
            "risks": ["角色动机不够明确", "第2场过渡略平"],
            "rewrite_guidance": ["男二动机需补充"],
            "suggested_ad_hooks": []
        }
        ```
        """,
        provider="mock",
        model="mock",
        task_type=AITaskType.SCRIPT_WRITING,
        model_type=AIModelType.TEXT_GENERATION,
    )

    script = """
    张总：60秒，合同作废！
    AP：数字不会撒谎，看时间戳。
    ▲小陈锁定云端日志，小陈横在门口挡住陈默。
    ▲陈默手指悬在删除确认键。
    ▲陈默手机通知栏跳出“改完给你20万”。
    ▲陈默手机弹出20万到账短信，下一条写着：女儿住院费我出，不做就裁你。
    ▲AP把原始文件、云端日志时间戳、录音、会议纪要和短信并排投屏。
    张总：15秒。
    ▲AP手机弹出匿名短信：原始文件将在30秒后删除，下一个停职的是你。
    """

    result = await score_service.score_script(
        script_content=script,
        story={"title": "AP全链路回归样片"},
        episode={"episode_number": 1, "title": "数据迷局"},
    )

    assert result.verdict == "review"
    assert result.overall_score == 4.0
    assert result.dimension_scores.character_recognizability == 3.5
    assert result.dimension_scores.logic_coherence == 3.5
    assert result.risks == ["角色动机不够明确", "第2场过渡略平"]
    assert result.rewrite_guidance == ["男二动机需补充"]


@pytest.mark.asyncio
async def test_score_script_does_not_calibrate_without_visible_motive_anchor(
    score_service, mock_ai_service
):
    mock_ai_service.ai_manager.generate_text.return_value = AIResponse(
        success=True,
        data="""
        ```json
        {
            "overall_score": 4.0,
            "dimension_scores": {
                "conflict_intensity": 4.0,
                "character_recognizability": 3.5,
                "cultural_fit": 4.5,
                "clip_ability": 4.0,
                "logic_coherence": 3.5
            },
            "verdict": "review",
            "strengths": [],
            "risks": ["角色动机不够明确"],
            "rewrite_guidance": ["补强陈默动机"],
            "suggested_ad_hooks": []
        }
        ```
        """,
        provider="mock",
        model="mock",
        task_type=AITaskType.SCRIPT_WRITING,
        model_type=AIModelType.TEXT_GENERATION,
    )

    script = """
    张总：60秒，合同作废！
    AP：数字不会撒谎，看时间戳。
    ▲小陈锁定云端日志，小陈横在门口挡住陈默。
    ▲陈默手指悬在删除确认键。
    ▲AP把原始文件、云端日志时间戳、录音、会议纪要和短信并排投屏。
    张总：15秒。
    ▲AP手机弹出匿名短信：原始文件将在30秒后删除，下一个停职的是你。
    """

    result = await score_service.score_script(
        script_content=script,
        story={"title": "AP全链路回归样片"},
        episode={"episode_number": 1, "title": "数据迷局"},
    )

    assert result.verdict == "review"
    assert result.overall_score == 4.0
    assert result.dimension_scores.character_recognizability == 3.5
    assert result.risks == ["角色动机不够明确"]


def test_script_score_schema_is_provider_compatible():
    schema = script_score_json_schema()
    schema_text = str(schema)

    assert "$defs" not in schema_text
    assert "allOf" not in schema_text
    assert schema["properties"]["dimension_scores"]["type"] == "object"
    assert "conflict_intensity" in schema["properties"]["dimension_scores"]["required"]
