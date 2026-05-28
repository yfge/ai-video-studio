import json
from types import SimpleNamespace


def provider_payload() -> dict:
    script = {
        "title": "奖金清零",
        "logline": "机器人发现奖金倒计时清零，最后一秒反转真相。",
        "characters": [
            {
                "name": "小蓝",
                "role": "主角",
                "appearance_prompt": "蓝色卡通机器人，橙色围巾",
                "consistency_anchor": "blue cartoon robot, orange scarf, LED eyes",
            }
        ],
        "scenes": [
            _scene_one(),
            _scene_two(),
        ],
    }
    return {
        "ok": True,
        "request_chain": [
            {"label": "deepseek-script", "duration_seconds": 1.0},
            {"label": "timeline-create", "duration_seconds": 0.1},
            {"label": "timeline-shot-plan", "duration_seconds": 1.0},
            {"label": "openai-character-image", "duration_seconds": 2.0},
            {"label": "seedance-video-1", "duration_seconds": 10.0},
            {"label": "seedance-video-2", "duration_seconds": 10.0},
            {"label": "timeline-assets-update", "duration_seconds": 0.1},
            {"label": "timeline-render-queue", "duration_seconds": 0.1},
        ],
        "key_artifacts": {
            "script": {"raw_content": json.dumps(script, ensure_ascii=False)},
            "image": {"oss_url": "https://example.com/robot.png"},
            "timeline_seed": {"id": 23, "version": 1},
            "timeline_shot_plan": {"id": 23, "seed_version": 1, "version": 2},
            "timeline": {"id": 23, "version": 3},
            "render_job": {
                "output_url": "https://example.com/render.mp4",
                "status": "succeeded",
            },
            "render_media_probe": {
                "ok": True,
                "expected_duration_seconds": 30,
                "format_duration_seconds": 30.1,
                "video_duration_seconds": 30.1,
                "audio_duration_seconds": 30.0,
                "checks": {
                    "has_video_stream": True,
                    "has_audio_stream": True,
                    "format_duration_matches_timeline": True,
                    "video_duration_matches_timeline": True,
                    "audio_duration_matches_timeline": True,
                    "scene_frames_extracted": True,
                },
            },
            "videos": [
                _video("video_s1_provider_chain_1_001", 1),
                _video("video_s2_provider_chain_2_002", 2),
            ],
        },
    }


def passing_script_score() -> dict:
    return {
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "verdict": "pass",
        "overall_score": 4.2,
        "dimension_scores": {
            "conflict_intensity": 4.0,
            "character_recognizability": 4.2,
            "cultural_fit": 4.1,
            "clip_ability": 4.0,
            "logic_coherence": 4.3,
        },
    }


class CliffhangerManager:
    async def generate_text(self, **kwargs):
        return SimpleNamespace(
            success=True,
            provider="deepseek",
            model=kwargs.get("model") or "deepseek-v4-flash",
            data={
                "passed": True,
                "score": 1.0,
                "reason": "结尾继续抛问题",
                "evidence": "最后一句留下证据疑问",
                "suggestion": "",
            },
        )


def sample(
    sample_id: str,
    attempt: int,
    *,
    passed: bool,
    hard_failures: list[str] | None = None,
    failure_categories: list[str] | None = None,
) -> dict:
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "passed": passed,
        "hard_failures": hard_failures or [],
        "failure_categories": failure_categories or [],
        "script_lint": {"overall_score": 9.2},
        "structured_script_score": {"average": 3.8},
    }


def _scene_one() -> dict:
    return {
        "scene_id": "s1",
        "duration_seconds": 15,
        "question": "谁把小蓝的奖金倒计时清零？",
        "stakes": "15秒内找不到编号，奖金永久清零。",
        "opposition": "时间轴系统拒绝小蓝权限。",
        "turn": "权限拒绝后，日志反向跳出操作者编号。",
        "plot": "小蓝发现奖金被清零，警报响起。",
        "dialogue": [{"speaker": "小蓝", "line": "谁清空奖金"}],
        "beats": [
            _beat(
                1,
                "hook",
                "抛出异常",
                "奖金清零警报亮起",
                "时间轴谁改",
                "小蓝冲向控制台",
                duration_seconds=3,
            ),
            _beat(
                2,
                "conflict",
                "增加阻力",
                "权限被系统拒绝",
                "权限没了",
                "控制台弹出拒绝提示",
                duration_seconds=6,
            ),
            _beat(
                3,
                "reveal",
                "放大谜团",
                "日志出现倒退一秒",
                "时间在倒退",
                "倒计时反向闪烁",
                duration_seconds=6,
            ),
        ],
        "image_prompt": "cartoon robot in studio",
        "video_prompt": "blue robot sees countdown alarm",
    }


def _scene_two() -> dict:
    return {
        "scene_id": "s2",
        "duration_seconds": 15,
        "question": "小蓝能不能在日志删除前拿到证据？",
        "stakes": "日志删除前拿不到证据，客户验收会失败。",
        "opposition": "黑影在后台删除最后日志。",
        "turn": "奖金记录恢复一半后，黑影删除最后日志。",
        "plot": "小蓝发现真相，最后一秒反转。",
        "dialogue": [{"speaker": "小蓝", "line": "证据指向黑影"}],
        "beats": [
            _beat(
                1,
                "conflict",
                "继续追查真相",
                "隐藏文件夹自动打开",
                "证据在这里",
                "小蓝抓住闪烁文件",
            ),
            {
                **_beat(
                    2,
                    "payoff",
                    "证明主角找到关键证据",
                    "奖金记录恢复一半",
                    "找到了",
                    "屏幕恢复奖金记录",
                ),
                "payoff_tag": "proof_found",
            },
            {
                **_beat(
                    3,
                    "cliffhanger",
                    "留下新的操作者威胁",
                    "黑影删除最后日志",
                    "谁还在线",
                    "日志末行消失",
                ),
                "cliffhanger_tag": "hidden_operator",
            },
        ],
        "image_prompt": "cartoon robot finds proof",
        "video_prompt": "blue robot reveals proof",
    }


def _beat(
    order: int,
    beat_type: str,
    purpose: str,
    event: str,
    line: str,
    action: str,
    *,
    duration_seconds: int = 5,
) -> dict:
    return {
        "order_index": order,
        "beat_type": beat_type,
        "dramatic_purpose": purpose,
        "visible_event": event,
        "dialogue": [{"speaker": "小蓝", "line": line}],
        "action": [action],
        "duration_seconds": duration_seconds,
    }


def _video(clip_id: str, ordinal: int) -> dict:
    return {
        "ordinal": ordinal,
        "clip_id": clip_id,
        "duration_seconds": 15,
        "video_url": f"https://example.com/video-{ordinal}.mp4",
        "image_url": "https://example.com/robot.png",
        "provider": "volcengine",
        "model": "doubao-seedance-2-0-260128",
        "task_id": f"task-{ordinal}",
        "timeline_shot_plan": {
            "character_anchor": "blue cartoon robot, orange scarf, LED eyes",
            "dialogue_source": "小蓝: 证据在这里",
            "video_prompt": "blue robot acts with clear story beat",
        },
    }
