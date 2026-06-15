"""Shared text-generation payloads for the mock AI service fixture."""

from __future__ import annotations

from typing import Any

from tests.fixtures.mock_ai_script_payloads import mock_passing_script_payload


def mock_generate_text_payload(prompt: str, json_schema: Any) -> dict[str, Any]:
    schema_name = json_schema.get("name") if isinstance(json_schema, dict) else ""
    if schema_name == "script_cliffhanger_judgement":
        return {
            "passed": True,
            "score": 0.95,
            "reason": "mock script ends on an unresolved question",
            "evidence": "Which door does the key open?",
            "suggestion": "",
        }
    if "The generated script JSON failed strict quality gate validation" in prompt:
        return _script_repair_payload()
    if "投流表" in prompt or "Traffic Sheet" in prompt:
        return _traffic_sheet_payload()
    return _script_score_payload()


def mock_passing_story_outline_payload() -> dict[str, Any]:
    return {
        "premise": "突然，Hero在发布会发现背叛证据公开，必须当场反击。",
        "synopsis": (
            "突然，Hero在发布会现场发现背叛视频被公开，危机和冲突立刻爆发。"
            "Hero顶住压力反查证据，紧张对抗不断升级，中段揭示Guide掌握关键线索。"
            "最终高潮对决中真相揭示，Hero解决危机并完成阶段性逆袭。"
        ),
        "main_conflict": "Hero必须在公开羞辱和证据争夺中找出真相。",
        "resolution": "Hero拿到证据，解决第一轮危机并逼出下一层黑手。",
        "main_characters": [
            {"name": "Hero", "role": "protagonist"},
            {"name": "Guide", "role": "mentor"},
        ],
        "character_relationships": {"Hero": {"Guide": "mentor"}},
        "plot_structure": {
            "act1": "突然公开证据，Hero当场反击。",
            "act2": "危机升级，Hero围绕证据与对手紧张对抗。",
            "act3": "高潮揭示真相，Hero完成逆袭并解决阶段危机。",
        },
        "hook_plan": {
            "opening_hook": "突然，发布会大屏播放Hero被陷害的视频。",
            "escalation_plan": "证据争夺不断升级。",
            "payoff_plan": "Hero用录音反击并拿回主动权。",
        },
        "cliffhanger_plan": ["证据背面出现新签名"],
        "ad_snippets": [
            {
                "duration_seconds": 15,
                "hook": "发布会证据公开",
                "visual_summary": "大屏视频和Hero握紧手机的手",
                "call_to_action": "看Hero如何反击",
            }
        ],
        "structured_story_contract": {
            "target_audience": "都市复仇用户",
            "core_emotional_pain": "尊严被公开碾压",
            "big_expectation": "Hero查清陷害真相并夺回主动权",
            "small_expectation_ladder": ["前三集拿到录音", "第十集逼出账本"],
            "protagonist_goal": "拿到发布会陷害证据",
            "structural_conflict": "Hero必须借Guide的资源查Guide隐瞒的线索",
            "information_gap": "观众知道证据在手机里，对手不知道已被录音",
            "first_three_episode_spine": "身份、旧案、核心冲突前三集立住",
            "stage_highs": ["发布会反击", "证据争夺", "董事会翻盘"],
            "shootability": "发布会厅、走廊、办公室低成本可拍",
            "compliance_risks": [],
            "traffic_hooks": ["大屏公开", "手机录音反击"],
        },
    }


def mock_passing_episode_plan_payload(episode_count: int = 1) -> dict[str, Any]:
    return {
        "episodes": [
            {
                "episode_number": idx + 1,
                "title": f"Mock Episode {idx + 1}",
                "summary": (
                    "Hero撞开会议室发现证据被抢，立刻用手机录音反击，"
                    "逼对手交出钥匙，却在证据背面看到新签名。"
                ),
                "plot_points": [
                    {
                        "order": 1,
                        "description": "开场钩子：Hero撞开门，证据正被塞进保险箱。",
                    },
                    {
                        "order": 2,
                        "description": "爽点落点：Hero播放录音，逼对手交出钥匙。",
                    },
                    {"order": 3, "description": "结尾卡点：证据背面出现新签名。"},
                ],
                "character_arcs": {"Hero": "Learns trust"},
                "conflicts": [
                    {
                        "type": "mock",
                        "description": "Hero和对手争夺陷害证据",
                        "intensity": "high",
                    }
                ],
                "scene_count": 3,
                "payoff": "Hero播放录音，逼对手交出保险箱钥匙。",
                "cliffhanger": "证据背面出现新签名。",
                "hook_plan": {
                    "opening_hook": "Hero撞开门发现证据被抢。",
                    "escalation_plan": "对手反咬Hero偷窃。",
                    "payoff_plan": "Hero用录音反击。",
                },
                "cliffhanger_plan": ["证据背面出现新签名", "Guide沉默离场"],
                "ad_snippets": [
                    {
                        "duration_seconds": 15,
                        "hook": "她录下了所有陷害",
                        "visual_summary": "手机录音界面和钥匙特写",
                        "call_to_action": "看她如何翻盘",
                    }
                ],
                "scenes": [
                    {
                        "scene_number": 1,
                        "slug_line": "INT. 会议室 - 日",
                        "location": "会议室",
                        "time_of_day": "day",
                        "summary": "开场钩子：Hero撞开门，证据正被塞进保险箱。",
                        "visual_anchor": "Hero盯住保险箱的眼神特写",
                        "dialogue_function": "reveal",
                    },
                    {
                        "scene_number": 2,
                        "slug_line": "INT. 会议室 - 日",
                        "location": "会议室",
                        "time_of_day": "day",
                        "summary": "爽点：Hero播放录音，逼对手交出钥匙。",
                        "visual_anchor": "手机录音界面特写",
                        "dialogue_function": "counterattack",
                    },
                    {
                        "scene_number": 3,
                        "slug_line": "INT. 走廊 - 日",
                        "location": "走廊",
                        "time_of_day": "day",
                        "summary": "卡点：证据背面出现新签名。",
                        "visual_anchor": "Hero攥紧证据的手部特写",
                        "dialogue_function": "reveal",
                    },
                ],
                "structured_episode_contract": {
                    "episode_goal": "Hero拿到陷害证据",
                    "ignition_0_3s": "Hero撞开门，证据被塞进保险箱。",
                    "first_30s_reason": "观众知道证据决定Hero能否翻案。",
                    "midpoint_jolt": "对手反咬Hero偷窃。",
                    "payoff": "Hero用录音反击，拿到钥匙。",
                    "final_button_cliffhanger": "证据背面露出新签名。",
                    "visual_anchor": "手机录音界面、Hero攥紧证据的手。",
                    "information_delta": "新签名指向更高层黑手。",
                    "dialogue_functions": [
                        "reveal",
                        "threat",
                        "counterattack",
                        "payoff",
                    ],
                },
            }
            for idx in range(episode_count or 1)
        ]
    }


def _script_repair_payload() -> dict[str, Any]:
    return mock_passing_script_payload()


def _traffic_sheet_payload() -> dict[str, Any]:
    return {
        "episode_id": 1,
        "script_id": 1,
        "market_region": "NA",
        "micro_genre": "test",
        "assets": [
            {
                "asset_id": "ep1_asset01_15s",
                "duration_seconds": 15,
                "market_region": "NA",
                "micro_genre": "test",
                "hook_type": "reveal",
                "source_episode": 1,
                "source_timecode_start": "00:00:00",
                "source_timecode_end": "00:00:15",
                "key_line": "mock line",
                "visual_hook": "mock visual",
                "shot_list": ["shot 1"],
                "cliff_or_cta": "mock cta",
                "music_reference": None,
                "compliance_flags": [],
            }
        ],
    }


def _script_score_payload() -> dict[str, Any]:
    return {
        "overall_score": 4.6,
        "dimension_scores": {
            "conflict_intensity": 4.6,
            "character_recognizability": 4.4,
            "cultural_fit": 4.5,
            "clip_ability": 4.6,
            "logic_coherence": 4.4,
        },
        "verdict": "pass",
        "strengths": ["mock strength"],
        "risks": [],
        "rewrite_guidance": [],
        "suggested_ad_hooks": ["mock hook"],
    }
