from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.schemas.production_canvas import (
    ProductionCanvasPlanResponse,
    ProductionCanvasResolvedContext,
    ProductionCanvasSelectedAssets,
)
from app.services.production_canvas.autonomous_planner import plan_canvas_skills
from app.services.production_canvas.run_response import _current_run_payload


class FakePlannerManager:
    def __init__(self, payloads: list[dict]) -> None:
        self.payloads = payloads
        self.calls: list[dict] = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        payload = self.payloads[min(len(self.calls) - 1, len(self.payloads) - 1)]
        return SimpleNamespace(
            success=payload.get("success", True),
            data=payload.get("data"),
            error=payload.get("error"),
            provider="test-provider",
            model="test-planner",
            usage={},
            metadata={},
        )


def _valid_proposal() -> dict:
    return {
        "objective": "生成可评审的视频候选",
        "steps": [
            {
                "skill": "brief.compose",
                "reason": "确认生产目标。",
                "depends_on": [],
            },
            {
                "skill": "script.generate",
                "reason": "生成视频所需剧本。",
                "depends_on": ["brief.compose"],
            },
            {
                "skill": "image.candidates",
                "reason": "提供可人工选用的起始帧。",
                "depends_on": ["script.generate"],
            },
            {
                "skill": "video.candidates",
                "reason": "基于选中图片生成视频候选。",
                "depends_on": ["image.candidates"],
            },
        ],
        "assumptions": ["媒体候选继续保留人工选用门槛。"],
    }


async def _plan(manager):
    return await plan_canvas_skills(
        prompt="生成一条可评审的视频候选",
        resolved_context=ProductionCanvasResolvedContext(),
        selected_assets=ProductionCanvasSelectedAssets(),
        ai_manager=manager,
    )


@pytest.mark.asyncio
async def test_autonomous_planner_compiles_a_typed_skill_subset():
    manager = FakePlannerManager([{"data": _valid_proposal()}])

    decision = await _plan(manager)

    assert decision.evidence.mode == "autonomous"
    assert decision.evidence.provider == "test-provider"
    assert decision.selected_skills == [
        "brief.compose",
        "script.generate",
        "image.candidates",
        "video.candidates",
    ]
    assert len(decision.edges) == 3
    video_edge = decision.edges[-1]
    assert video_edge.from_port == "approved_image"
    assert video_edge.to_port == "start_frame"
    assert video_edge.binding_type == "selected_output"


@pytest.mark.asyncio
async def test_autonomous_planner_repairs_one_invalid_proposal():
    invalid = {
        "objective": "错误方案",
        "steps": [
            {
                "skill": "unknown.skill",
                "reason": "不存在。",
                "depends_on": [],
            }
        ],
        "assumptions": [],
    }
    manager = FakePlannerManager([{"data": invalid}, {"data": _valid_proposal()}])

    decision = await _plan(manager)

    assert len(manager.calls) == 2
    assert decision.evidence.mode == "autonomous"
    assert decision.evidence.repair_count == 1
    assert "上一次的输出不符合 JSON Schema" in manager.calls[1]["prompt"]


@pytest.mark.asyncio
async def test_autonomous_planner_falls_back_after_bounded_repair():
    invalid = {
        "objective": "不可执行方案",
        "steps": [
            {
                "skill": "video.candidates",
                "reason": "缺少所有前置。",
                "depends_on": [],
            }
        ],
        "assumptions": [],
    }
    manager = FakePlannerManager([{"data": invalid}, {"data": invalid}])

    decision = await _plan(manager)

    assert decision.evidence.mode == "deterministic_fallback"
    assert decision.evidence.fallback_reason == "invalid_plan"
    assert decision.evidence.repair_count == 1
    assert decision.evidence.validation_errors
    assert decision.selected_skills[0] == "brief.compose"
    assert decision.selected_skills[-1] == "report.summarize"
    assert len(decision.edges) == 10


@pytest.mark.asyncio
async def test_autonomous_planner_falls_back_when_ai_is_unavailable():
    decision = await _plan(None)

    assert decision.evidence.mode == "deterministic_fallback"
    assert decision.evidence.fallback_reason == "ai_manager_unavailable"
    assert len(decision.selected_skills) == 12


def test_run_restore_preserves_the_planner_selected_subset_and_edges():
    edge = {
        "edge_id": "brief-to-script",
        "from_node": "skill-brief-compose",
        "from_port": "production_brief",
        "to_node": "skill-script-generate",
        "to_port": "production_brief",
        "binding_type": "value",
        "required": True,
    }
    payload = {
        "prompt": "只生成剧本",
        "resolved_context": {},
        "selected_assets": {"virtual_ips": [], "environments": []},
        "skill_manifest": {
            "version": "production_canvas.v1",
            "entry_skill": "production_canvas.create",
            "skills": [],
            "reuse_policy": "backend_reuses_existing_services_and_tasks",
        },
        "skill_results": [
            {
                "skill": skill,
                "label": skill,
                "status": "ready",
                "title": skill,
                "detail": skill,
                "outputs": {},
                "reuse_targets": [],
            }
            for skill in ("brief.compose", "script.generate")
        ],
        "nodes": [],
        "edges": [edge],
        "planner": {
            "mode": "autonomous",
            "version": "production_canvas.planner.v1",
            "objective": "只生成剧本",
            "selected_skills": ["brief.compose", "script.generate"],
        },
    }

    current = _current_run_payload(payload)
    plan = ProductionCanvasPlanResponse.model_validate(current)

    assert [result.skill for result in plan.skill_results] == [
        "brief.compose",
        "script.generate",
    ]
    assert [node.skill for node in plan.nodes] == [
        "brief.compose",
        "script.generate",
    ]
    assert plan.edges[0].edge_id == "brief-to-script"
