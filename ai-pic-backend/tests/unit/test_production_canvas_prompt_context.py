import pytest
from app.models.script import Episode, Story, StoryCharacter
from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_brief import (
    ProductionCanvasModelChoice,
    ProductionCanvasModelPlan,
)
from app.schemas.production_canvas_content import ProductionCanvasProductionContext
from app.services.ai_service import ai_service
from app.services.production_canvas.production_context_builder import (
    build_production_planning_draft,
)
from app.services.production_canvas.production_model_selection import (
    select_production_models,
)
from app.services.production_canvas.script_context_compiler import (
    compile_canvas_script_context,
)
from app.services.production_canvas.skill_planner import (
    build_autonomous_canvas_skill_plan,
)
from app.services.providers.base import AIModelType
from tests.unit.production_canvas_context_fixtures import (
    PROMPT,
    ContextAndSkillPlannerModel,
    ContextModel,
)


@pytest.mark.asyncio
async def test_context_model_parses_prompt_into_executable_contract():
    manager = ContextModel()
    draft = await build_production_planning_draft(
        ProductionCanvasPlanRequest(prompt=PROMPT, planning_mode="single_video"),
        ai_manager=manager,
    )

    assert draft.brief.interpretation_status == "model_parsed"
    assert draft.brief.interpretation_warnings == []
    assert draft.brief.source_prompt == PROMPT
    assert draft.brief.intent.objective == "制作一条可直接进入生产的办公反转短剧"
    assert draft.brief.intent.narrative_seed == (
        "林妹妹在办公室吐槽 AI 落地，结尾发生反转"
    )
    assert draft.brief.video_spec.duration_seconds == 60
    assert draft.brief.video_spec.focus_episode_number is None
    assert draft.brief.video_spec.episode_count == 1
    assert draft.brief.video_spec.aspect_ratio is None
    assert draft.brief.video_spec.visual_style == ["3D卡通"]
    assert draft.brief.models.image.requested == "gpt-img-2"
    assert draft.brief.models.image.selected == "openai:gpt-image-2"
    assert draft.brief.models.video.requested == "seedance 2.0"
    assert draft.brief.models.video.selected == "volcengine:doubao-seedance-2-0-260128"
    assert draft.brief.assets.virtual_ip_name == "林妹妹"
    assert draft.content_plan.episodes[0].episode_number == 1

    compiled = compile_canvas_script_context(
        ProductionCanvasProductionContext(
            brief=draft.brief,
            content_plan=draft.content_plan,
        ),
        episode_number=1,
    )

    assert compiled.target_chars == 600
    assert PROMPT in compiled.requirements
    assert "当前第 1 集合同" in compiled.requirements
    assert '"duration_seconds": 60' in compiled.requirements
    assert "吐槽 AI 落地" in compiled.requirements
    assert "反转" in compiled.requirements
    model_prompt = manager.calls[0]["prompt"]
    assert '"brief": {' in model_prompt
    assert '"content_plan": {' in model_prompt
    assert '"image": {"requested":' in model_prompt
    assert "不得改成 mode、goal" in model_prompt


@pytest.mark.asyncio
async def test_fallback_preserves_prompt_without_fixed_name_parsing():
    draft = await build_production_planning_draft(
        ProductionCanvasPlanRequest(prompt=PROMPT, planning_mode="single_video"),
        ai_manager=None,
    )

    assert draft.brief.source_prompt == PROMPT
    assert draft.brief.interpretation_status == "failed"
    assert draft.brief.interpretation_warnings
    assert draft.brief.ready_for_execution is False
    assert draft.brief.intent.objective == PROMPT
    assert draft.brief.assets.virtual_ip_name is None
    assert draft.brief.models.image.requested is None
    assert draft.brief.models.video.requested is None
    assert draft.brief.video_spec.focus_episode_number is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("requested", "expected"),
    [
        ("gpt-img-2", "openai:gpt-image-2"),
        ("openai:gpt-img-2", "openai:gpt-image-2"),
        ("codex:gpt-img-2", "codex:gpt-image-2"),
    ],
)
async def test_image_model_alias_matches_requested_provider_directory(
    requested,
    expected,
):
    class MultiProviderCatalog:
        async def list_models(self, *, model_type, source):
            assert source == "static"
            if model_type == AIModelType.TEXT_TO_IMAGE:
                return [
                    {
                        "id": "gpt-image-2",
                        "name": "GPT Image 2",
                        "provider": "codex",
                    },
                    {
                        "id": "gpt-image-2",
                        "name": "GPT Image 2",
                        "provider": "openai",
                    },
                    {
                        "id": "chatgpt-img-2",
                        "name": "ChatGPT Image 2",
                        "provider": "openai",
                    },
                ]
            return []

    selected, questions = await select_production_models(
        ProductionCanvasModelPlan(
            image=ProductionCanvasModelChoice(requested=requested)
        ),
        MultiProviderCatalog(),
    )

    assert selected.image.requested == requested
    assert selected.image.selected == expected
    assert selected.image.status == "requested"
    assert not any(item.id == "models.image" for item in questions)


@pytest.mark.asyncio
async def test_video_model_family_uses_catalog_recommended_full_capability_model():
    class SeedanceCatalog:
        async def list_models(self, *, model_type, source):
            assert source == "static"
            if model_type == AIModelType.IMAGE_TO_VIDEO:
                return [
                    {
                        "id": "seedance-2.0-i2v",
                        "name": "Seedance 2.0 图生视频（推荐）",
                        "provider": "volcengine",
                        "capabilities": ["image_to_video"],
                    }
                ]
            if model_type == AIModelType.TEXT_TO_VIDEO:
                return [
                    {
                        "id": "doubao-seedance-2-0-260128",
                        "name": "豆包 Seedance 2.0（推荐）",
                        "provider": "volcengine",
                        "capabilities": ["text_to_video", "image_to_video"],
                    },
                    {
                        "id": "doubao-seedance-2-0-fast-260128",
                        "name": "豆包 Seedance 2.0 Fast",
                        "provider": "volcengine",
                        "capabilities": ["text_to_video", "image_to_video"],
                    },
                ]
            return []

    selected, questions = await select_production_models(
        ProductionCanvasModelPlan(
            video=ProductionCanvasModelChoice(requested="seedance 2.0")
        ),
        SeedanceCatalog(),
    )

    assert selected.video.requested == "seedance 2.0"
    assert selected.video.selected == "volcengine:doubao-seedance-2-0-260128"
    assert selected.video.status == "requested"
    assert not any(item.id == "models.video" for item in questions)


@pytest.mark.asyncio
async def test_model_contract_drives_assets_episode_and_script_skill(
    db_session,
    monkeypatch,
):
    user = User(
        username="canvas_model_first_owner",
        email="canvas-model-first@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    virtual_ip = VirtualIP(user_id=None, name="林妹妹", is_active=True)
    environment = Environment(
        user_id=None,
        name="办公室",
        category="indoor",
    )
    db_session.add(user)
    db_session.flush()
    virtual_ip.user_id = user.id
    environment.user_id = user.id
    db_session.add_all([virtual_ip, environment])
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="林妹妹办公短剧",
        genre="comedy",
        duration_minutes=3,
        default_aspect_ratio="9:16",
    )
    db_session.add(story)
    db_session.flush()
    episode = Episode(
        id=194,
        story_id=story.id,
        episode_number=1,
        title="AI 落地吐槽",
        duration_minutes=3,
        aspect_ratio="9:16",
    )
    db_session.add_all(
        [
            StoryCharacter(
                story_id=story.id,
                virtual_ip_id=virtual_ip.id,
                character_name=virtual_ip.name,
            ),
            VirtualIPEnvironment(
                user_id=user.id,
                virtual_ip_id=virtual_ip.id,
                virtual_ip_business_id=virtual_ip.business_id,
                environment_id=environment.id,
                environment_business_id=environment.business_id,
                is_default=True,
            ),
            episode,
        ]
    )
    db_session.commit()

    manager = ContextAndSkillPlannerModel()
    monkeypatch.setattr(ai_service, "ai_manager", manager)
    plan = await build_autonomous_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt=PROMPT,
            planning_mode="single_video",
            story_id=story.id,
            episode_id=194,
        ),
    )

    assert plan.resolved_context.virtual_ip_id == virtual_ip.id
    assert plan.resolved_context.environment_id == environment.id
    assert plan.resolved_context.story_id == story.id
    assert plan.resolved_context.episode_id == episode.id
    assert plan.planner.mode == "autonomous"
    assert plan.planner.selected_skills == [
        "brief.compose",
        "content.plan",
        "asset.select",
        "script.generate",
    ]
    script = next(
        item for item in plan.skill_results if item.skill == "script.generate"
    )
    assert script.status == "ready"
    context = script.outputs["production_context"]
    assert context["brief"]["assets"]["virtual_ip_name"] == "林妹妹"
    assert context["brief"]["video_spec"]["focus_episode_number"] is None
    assert context["brief"]["video_spec"]["duration_seconds"] == 60
    assert context["brief"]["video_spec"]["aspect_ratio"] == "9:16"
    assert any(
        item["field"] == "video_spec.duration_seconds"
        and item["resolution"] == "user_prompt_overrides_persisted_spec"
        for item in context["brief"]["conflicts"]
    )
