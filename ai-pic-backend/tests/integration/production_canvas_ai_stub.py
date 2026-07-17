from __future__ import annotations

from types import SimpleNamespace


class ProductionCanvasAIStub:
    def __init__(self) -> None:
        self.payloads = [_context_payload(), _planner_payload()]

    async def generate_text(self, **_kwargs):
        return SimpleNamespace(
            success=True,
            data=self.payloads.pop(0),
            error=None,
            provider="test-provider",
            model="production-canvas-test-model",
            usage={},
            metadata={},
        )

    async def list_models(self, **_kwargs):
        return []


def _context_payload() -> dict:
    return {
        "brief": {
            "source_prompt": "由后端绑定原始目标",
            "intent": {
                "kind": "story_series",
                "objective": "把用户目标整理成可执行的连续内容",
                "narrative_seed": "围绕用户指定的人物和事件持续推进",
            },
            "video_spec": {
                "episode_count": 1,
                "focus_episode_number": 1,
            },
            "assets": {
                "asset_policy": "reuse_preferred",
            },
        },
        "content_plan": {
            "title": "结构化生产测试",
            "premise": "围绕用户输入建立一条可执行故事线。",
            "synopsis": "主角面对当前问题，通过行动获得阶段性结果，并留下后续线索。",
            "main_conflict": "目标与现实阻力持续冲突。",
            "season_arc": "每集解决一个阶段问题，并积累到下一阶段。",
            "recurring_engine": "新问题、可见行动、阶段兑现和连续性线索。",
            "episodes": [
                {
                    "episode_number": 1,
                    "title": "第一集",
                    "logline": "主角处理当前问题并获得可见结果。",
                    "beats": ["问题出现", "行动升级", "阶段结果"],
                    "payoff": "当前问题获得阶段性解决。",
                    "cliffhanger": "新的具体任务出现。",
                    "continuity_handoff": ["保留新的任务状态"],
                }
            ],
        },
    }


def _planner_payload() -> dict:
    return {
        "objective": "按结构化生产上下文完成内容创建",
        "steps": [
            {
                "skill": "brief.compose",
                "reason": "确认结构化生产目标。",
                "depends_on": [],
            },
            {
                "skill": "content.plan",
                "reason": "形成故事和剧集合同。",
                "depends_on": ["brief.compose"],
            },
            {
                "skill": "asset.select",
                "reason": "关联或创建生产资产。",
                "depends_on": ["content.plan"],
            },
            {
                "skill": "script.generate",
                "reason": "把完整生产上下文交给剧本链路。",
                "depends_on": ["asset.select"],
            },
        ],
        "assumptions": [],
    }
