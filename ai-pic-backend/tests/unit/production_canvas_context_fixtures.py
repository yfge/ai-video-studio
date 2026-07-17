from types import SimpleNamespace

from app.services.providers.base import AIModelType

PROMPT = (
    "基于林妹妹做一分钟办公短剧，3D 卡通风格，吐槽 AI 落地 "
    "要有反转 使用gpt-img-2 生图，使用seedance 2.0 生视频"
)


class ContextModel:
    def __init__(self):
        self.generation_payloads = [_structured_draft()]
        self.calls = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        payload = self.generation_payloads.pop(0)
        return SimpleNamespace(
            success=True,
            data=payload,
            error=None,
            provider="test-provider",
            model="context-parser",
            usage={},
            metadata={},
        )

    async def list_models(self, *, model_type, source):
        assert source == "static"
        if model_type == AIModelType.TEXT_TO_IMAGE:
            return [
                {
                    "id": "gpt-image-2",
                    "name": "GPT Image 2",
                    "provider": "openai",
                }
            ]
        if model_type == AIModelType.TEXT_TO_VIDEO:
            return [
                {
                    "id": "doubao-seedance-2-0-260128",
                    "name": "Seedance 2.0",
                    "provider": "volcengine",
                }
            ]
        return []


class ContextAndSkillPlannerModel(ContextModel):
    def __init__(self):
        super().__init__()
        self.generation_payloads.append(_skill_proposal())


def _structured_draft() -> dict:
    return {
        "brief": {
            "source_prompt": "模型不得改写这个字段",
            "intent": {
                "kind": "single_video",
                "objective": "制作一条可直接进入生产的办公反转短剧",
                "narrative_seed": "林妹妹在办公室吐槽 AI 落地，结尾发生反转",
                "genre": "职场轻喜剧",
                "tone": ["轻快", "讽刺"],
                "must_include": [
                    "林妹妹",
                    "gpt-img-2",
                    "seedance 2.0",
                    "3D卡通",
                    "AI 落地",
                    "反转",
                ],
            },
            "video_spec": {
                "duration_seconds": 60,
                "episode_count": 1,
                "focus_episode_number": None,
                "aspect_ratio": None,
                "visual_style": ["3D卡通"],
            },
            "models": {
                "image": {"requested": "gpt-img-2"},
                "video": {"requested": "seedance 2.0"},
            },
            "assets": {
                "virtual_ip_name": "林妹妹",
                "environment_names": ["办公室"],
                "asset_policy": "reuse_preferred",
            },
        },
        "content_plan": {
            "title": "林妹妹吐槽 AI 落地",
            "premise": "林妹妹在办公室吐槽看似热闹却没有解决问题的 AI 落地。",
            "synopsis": "她用轻松吐槽拆穿形式主义，结尾却发现真正被 AI 优化的是自己。",
            "main_conflict": "表面的 AI 提效宣传与真实办公体验持续冲突。",
            "characters": [
                {
                    "name": "林妹妹",
                    "role": "protagonist",
                    "description": "观察敏锐、擅长用吐槽指出 AI 落地问题。",
                    "season_arc": "持续追问技术宣传与真实价值之间的差距。",
                }
            ],
            "environments": [
                {
                    "name": "办公室",
                    "purpose": "承载 AI 工具进入日常工作的短剧冲突。",
                }
            ],
            "season_arc": "林妹妹持续检验各种 AI 落地承诺，并遭遇出人意料的结果。",
            "recurring_engine": "一个新的 AI 应用进入办公室，林妹妹先吐槽再发现反转。",
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "AI 到底落在哪儿",
                    "logline": "林妹妹吐槽 AI 落地只会增加流程，却在结尾发现自己才是被优化的对象。",
                    "beats": [
                        "办公室宣布上线新的 AI 提效流程。",
                        "林妹妹发现工作没有减少，填表步骤反而增加。",
                        "她吐槽 AI 没有落地，系统却弹出她的岗位优化通知。",
                    ],
                    "payoff": "AI 的确完成了落地，但落在了林妹妹自己的岗位上。",
                    "cliffhanger": "林妹妹发现优化名单还有下一页。",
                    "continuity_handoff": ["保留优化名单作为后续办公短剧线索。"],
                }
            ],
            "continuity_rules": ["林妹妹始终以真实办公价值检验 AI 宣传。"],
            "future_threads": ["优化名单下一页是谁。"],
        },
    }


def _skill_proposal() -> dict:
    return {
        "objective": PROMPT,
        "steps": [
            {
                "skill": "brief.compose",
                "reason": "解析结构化生产合同。",
                "depends_on": [],
            },
            {
                "skill": "content.plan",
                "reason": "形成当前剧集内容计划。",
                "depends_on": ["brief.compose"],
            },
            {
                "skill": "asset.select",
                "reason": "关联合同要求的真实资产。",
                "depends_on": ["content.plan"],
            },
            {
                "skill": "script.generate",
                "reason": "按结构化合同生成剧本。",
                "depends_on": ["asset.select"],
            },
        ],
        "assumptions": [],
    }
