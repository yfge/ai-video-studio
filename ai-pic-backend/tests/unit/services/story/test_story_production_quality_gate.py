from __future__ import annotations

import pytest
from app.services.story_quality_gate import evaluate_story_quality_gate


def _strong_story() -> dict:
    return {
        "premise": "林雪在公司发布会突然发现父亲旧案证据被公开，必须当场反击。",
        "synopsis": (
            "突然，林雪在发布会现场发现旧案证据被公开，危机和冲突立刻爆发。"
            "她顶住压力反查证据，紧张对抗不断升级，中段揭示陈默才是真正操盘者。"
            "最终高潮对决中真相曝光，林雪完成反击并收束阶段目标。"
        ),
        "main_conflict": "林雪必须在公开羞辱和旧案陷害中找出真相。",
        "resolution": "林雪夺回关键证据，逼陈默暴露下一层黑手。",
        "plot_structure": {
            "act1": "突然公开旧案证据，林雪被迫当场反击。",
            "act2": "危机升级，林雪和陈默围绕账本紧张对抗。",
            "act3": "高潮揭示真相，林雪解决危机并完成逆袭。",
        },
        "hook_plan": {
            "opening_hook": "突然，发布会大屏播放林雪父亲旧案视频。",
            "escalation_plan": "每三集推进一个证据目标。",
            "payoff_plan": "林雪用录音反击陈默。",
        },
        "cliffhanger_plan": ["账本最后一页露出父亲签名"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "旧案证据公开",
                "visual_summary": "大屏视频和林雪握紧手机的手",
                "call_to_action": "看她如何反击",
            }
        ],
    }


def _ap_regression_story() -> dict:
    story = {
        "premise": (
            "商业咨询公司项目负责人AP回归，在关键并购尽调会议上发现数据被篡改，"
            "她必须在客户、团队和对手的夹击下，用手机录音和投屏证据当场反击，"
            "夺回信任并揭露背叛。"
        ),
        "synopsis": (
            "AP回归在会议室主持并购尽调汇报，客户突然质疑数据异常，她发现自己的报告被人篡改。"
            "团队内部有人背叛，竞争对手暗中施压。AP冷静应对，用手机录音和原始数据投屏揭露篡改者，"
            "但代价是项目暂停和内部调查。她必须在24小时内找到真正幕后黑手，否则职业生涯终结。"
        ),
        "main_conflict": "AP回归遭遇数据篡改、客户质疑和团队背叛，必须用专业证据证明清白。",
        "resolution": "AP回归通过会议录音、邮件记录和投屏对比，锁定篡改者并当众揭穿，项目恢复，她赢得客户和公司信任，背叛者被解职。",
        "plot_structure": {
            "act1": "开场10秒：AP回归打开投屏，客户突然拍桌质疑数据造假，她发现报告被篡改，冲突爆发。",
            "act2": "AP回归用手机录音和原始数据投屏，逐条对比揭露篡改痕迹，团队内部出现分裂，竞争对手施压。",
            "act3": "AP回归在24小时内找到幕后黑手，用会议纪要和时间戳证据当众揭穿，项目恢复，她赢得客户道歉和公司嘉奖。",
        },
        "hook_plan": {
            "opening_hook": "AP回归打开投屏，客户突然拍桌：这数据是假的！她发现报告被篡改，全场哗然。",
            "escalation_plan": "每20秒插入反转：同事反咬、录音证据、新数据出现、对手施压、董事会介入。",
            "payoff_plan": "尾声AP回归用会议纪要时间戳揭穿对手，对方认罪，但镜头定格在她手机上新收到的威胁短信。",
        },
        "cliffhanger_plan": ["手机新收到的威胁短信显示内鬼还有同伙"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "客户拍桌质疑数据造假",
                "visual_summary": "会议室投屏、手机录音、AP回归眼神特写",
                "call_to_action": "看她如何当场反击",
            }
        ],
        "structured_story_contract": {
            "target_audience": "都市职场短剧用户",
            "core_emotional_pain": "专业能力被公开质疑，信任被团队背叛",
            "big_expectation": "AP回归查清数据篡改真相并夺回项目主导权",
            "small_expectation_ladder": ["前三集拿到会议录音", "第十集逼出篡改者"],
            "protagonist_goal": "24小时内找出篡改数据的人",
            "structural_conflict": "AP回归必须借质疑她的团队资源反查团队内部黑手",
            "information_gap": "观众知道录音存在，对手不知道关键镜头已被拍下",
            "first_three_episode_spine": "数据造假、手机录音、内鬼威胁前三集立住",
            "stage_highs": ["会议室反击", "投屏对比", "董事会翻盘"],
            "shootability": "会议室、走廊、工位、夜景办公室低成本可拍",
            "compliance_risks": [],
            "traffic_hooks": ["客户拍桌", "手机录音", "投屏反击"],
        },
    }
    return story


@pytest.mark.unit
def test_story_gate_requires_structured_contract_in_production() -> None:
    gate = evaluate_story_quality_gate(
        story=_strong_story(),
        require_story_contract=True,
    )

    assert gate["passed"] is False
    assert any(
        issue["id"] == "structured_story_contract_required"
        for issue in gate["blocking_issues"]
    )


@pytest.mark.unit
def test_story_gate_accepts_structured_contract_when_required() -> None:
    story = _strong_story()
    story["structured_story_contract"] = {
        "target_audience": "都市复仇女性用户",
        "core_emotional_pain": "父亲蒙冤、尊严被公开碾压",
        "big_expectation": "林雪查清旧案并夺回家族公司",
        "small_expectation_ladder": [
            "前三集拿到发布会录音",
            "第十集逼陈默交出账本",
        ],
        "protagonist_goal": "三天内拿到账本",
        "structural_conflict": "林雪必须借陈默的资源查陈默的罪证",
        "information_gap": "观众知道账本在保险箱，林雪只知道陈默撒谎",
        "first_three_episode_spine": "身份、旧案、核心冲突在前三集全部立住",
        "stage_highs": ["发布会反击", "账本争夺", "董事会翻盘"],
        "shootability": "办公室、发布会厅、走廊三类低成本场景",
        "compliance_risks": [],
        "traffic_hooks": ["大屏旧案视频", "手机录音反击"],
    }

    gate = evaluate_story_quality_gate(
        story=story,
        require_story_contract=True,
    )

    blocking_ids = {issue["id"] for issue in gate["blocking_issues"]}
    assert "structured_story_contract_required" not in blocking_ids


@pytest.mark.unit
def test_story_gate_accepts_ap_regression_commercial_outline() -> None:
    gate = evaluate_story_quality_gate(
        story=_ap_regression_story(),
        require_story_contract=True,
    )

    assert gate["passed"] is True
