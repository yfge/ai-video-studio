from __future__ import annotations

from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.services.production_canvas.skill_planner import build_canvas_skill_plan


def _user(db, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_canvas_skill_plan_selects_existing_ip_and_environment_pool(db_session):
    user = _user(db_session, "canvas_skill_owner")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        description="程序员身边的轻喜剧女主",
        tags=["轻喜剧", "都市"],
        is_active=True,
    )
    environment = Environment(
        user_id=user.id,
        name="共享办公区",
        category="indoor",
        tags=["办公室", "白天"],
        description="适合程序员短剧的明亮办公环境",
        reference_images=["https://example.test/office.png"],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()
    db_session.refresh(virtual_ip)
    db_session.refresh(environment)
    db_session.add(
        VirtualIPEnvironment(
            user_id=user.id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            environment_id=environment.id,
            environment_business_id=environment.business_id,
            usage_type="main_scene",
            usage_note="优先用于第 4 集",
            sort_order=0,
            is_default=True,
        )
    )
    db_session.commit()
    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧，生成完整短剧链路",
            brief_overrides={"episode_count": 1},
            clarification_answers={
                "assets.virtual_ip_name": "林妹妹",
                "assets.environment_names": "共享办公区",
            },
        ),
    )
    assert plan.skill_manifest.version == "production_canvas.v2"
    assert [skill.id for skill in plan.skill_manifest.skills[:8]] == [
        "brief.compose",
        "content.plan",
        "asset.select",
        "virtual_ip.image",
        "environment.image",
        "script.generate",
        "timeline.assemble",
        "storyboard.plan",
    ]
    assert [result.skill for result in plan.skill_results[:8]] == [
        "brief.compose",
        "content.plan",
        "asset.select",
        "virtual_ip.image",
        "environment.image",
        "script.generate",
        "timeline.assemble",
        "storyboard.plan",
    ]
    script_result = next(
        result for result in plan.skill_results if result.skill == "script.generate"
    )
    virtual_ip_image_result = next(
        result for result in plan.skill_results if result.skill == "virtual_ip.image"
    )
    environment_image_result = next(
        result for result in plan.skill_results if result.skill == "environment.image"
    )
    assert script_result.reuse_targets[0].target == (
        "app.api.v1.endpoints.scripts_generation_queue.generate_script_async"
    )
    assert script_result.reuse_targets[1].target == (
        "app.services.script.production_pipeline.run_production_script_generation"
    )
    assert plan.selected_assets.virtual_ips[0].name == "林妹妹"
    assert plan.selected_assets.environments[0].name == "共享办公区"
    asset_node = next(node for node in plan.nodes if node.skill == "asset.select")
    assert "命中现有可访问资产" in asset_node.detail
    assert asset_node.outputs["environment_ids"] == [environment.id]
    assert asset_node.reuse_targets[0].target.endswith("VirtualIPRepository")
    assert asset_node.outputs["candidate_environment_ids"] == [environment.id]
    assert virtual_ip_image_result.status == "ready"
    assert virtual_ip_image_result.outputs["virtual_ip_ids"] == [virtual_ip.id]
    assert environment_image_result.status == "ready"
    assert environment_image_result.outputs["environment_ids"] == [environment.id]
    assert script_result.status == "ready"
    assert script_result.outputs["episode_id"] == plan.resolved_context.episode_id


def test_canvas_skill_plan_creates_prompt_assets_when_no_match_exists(db_session):
    user = _user(db_session, "canvas_skill_unmatched_owner")
    db_session.add_all(
        [
            VirtualIP(
                user_id=user.id,
                name="斌哥",
                description="大厂 PM",
                tags=["职场"],
                is_active=True,
            ),
            Environment(
                user_id=user.id,
                name="老拐工作室",
                category="indoor",
                tags=["直播间"],
            ),
        ]
    )
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧",
            brief_overrides={"episode_count": 1},
            clarification_answers={
                "assets.virtual_ip_name": "林妹妹",
                "assets.environment_names": "办公室",
            },
        ),
    )

    assert plan.selected_assets.virtual_ips[0].name == "林妹妹"
    assert plan.selected_assets.environments[0].name == "办公室"
    asset_node = next(node for node in plan.nodes if node.skill == "asset.select")
    assert "IP：新建 林妹妹" in asset_node.title
    assert "场景：新建 办公室" in asset_node.title
    assert asset_node.outputs["created_virtual_ip_ids"]
    assert asset_node.outputs["created_environment_ids"]
    assert (
        next(
            result for result in plan.skill_results if result.skill == "asset.select"
        ).status
        == "review"
    )
    virtual_ip_image_result = next(
        result for result in plan.skill_results if result.skill == "virtual_ip.image"
    )
    environment_image_result = next(
        result for result in plan.skill_results if result.skill == "environment.image"
    )
    assert virtual_ip_image_result.status == "ready"
    assert environment_image_result.status == "ready"
    assert (
        db_session.query(VirtualIPEnvironment)
        .filter(
            VirtualIPEnvironment.virtual_ip_id == plan.resolved_context.virtual_ip_id,
            VirtualIPEnvironment.environment_id == plan.resolved_context.environment_id,
            VirtualIPEnvironment.is_deleted.is_(False),
        )
        .count()
        == 1
    )


def test_canvas_skill_plan_links_existing_environment_to_created_ip(db_session):
    user = _user(db_session, "canvas_skill_created_ip_existing_environment_owner")
    environment = Environment(
        user_id=user.id,
        name="首创办公室",
        category="indoor",
    )
    db_session.add(environment)
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="创建一个名为首创IP的角色，以首创办公室为场景",
            brief_overrides={"episode_count": 1},
            clarification_answers={
                "assets.virtual_ip_name": "首创IP",
                "assets.environment_names": "首创办公室",
            },
        ),
    )

    asset_node = next(node for node in plan.nodes if node.skill == "asset.select")
    assert "IP：新建 首创IP" in asset_node.title
    assert "场景：复用 首创办公室" in asset_node.title
    assert asset_node.outputs["created_virtual_ip_ids"]
    assert asset_node.outputs["created_environment_ids"] == []
    assert (
        db_session.query(VirtualIPEnvironment)
        .filter(
            VirtualIPEnvironment.virtual_ip_id == plan.resolved_context.virtual_ip_id,
            VirtualIPEnvironment.environment_id == environment.id,
            VirtualIPEnvironment.is_deleted.is_(False),
        )
        .count()
        == 1
    )


def test_canvas_skill_plan_can_select_environment_without_ip(db_session):
    user = _user(db_session, "canvas_skill_environment_owner")
    environment = Environment(
        user_id=user.id,
        name="办公室",
        category="indoor",
        tags=["职场"],
    )
    db_session.add(environment)
    db_session.commit()
    db_session.refresh(environment)

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(prompt="做一个办公室轻喜剧短剧链路"),
    )

    assert plan.selected_assets.virtual_ips == []
    assert plan.selected_assets.environments[0].name == "办公室"
    asset_node = next(node for node in plan.nodes if node.skill == "asset.select")
    assert asset_node.title == "场景：复用 办公室"
    assert asset_node.status == "blocked"
    assert asset_node.outputs["environment_ids"] == [environment.id]
    assert plan.production_context.brief.clarifications[0].id == (
        "assets.virtual_ip_name"
    )


def test_canvas_skill_plan_links_explicit_prompt_environment_for_ip(db_session):
    user = _user(db_session, "canvas_skill_unlinked_environment_owner")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        is_active=True,
    )
    environment = Environment(
        user_id=user.id,
        name="办公室",
        category="indoor",
        tags=["职场"],
    )
    db_session.add_all([virtual_ip, environment])
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于林妹妹做一个办公室职场短剧",
            brief_overrides={"episode_count": 1},
            clarification_answers={
                "assets.virtual_ip_name": "林妹妹",
                "assets.environment_names": "办公室",
            },
        ),
    )

    assert plan.resolved_context.virtual_ip_id == virtual_ip.id
    assert plan.resolved_context.environment_id == environment.id
    assert plan.selected_assets.environments[0].id == environment.id
    assert (
        db_session.query(VirtualIPEnvironment)
        .filter(
            VirtualIPEnvironment.virtual_ip_id == virtual_ip.id,
            VirtualIPEnvironment.environment_id == environment.id,
            VirtualIPEnvironment.is_deleted.is_(False),
        )
        .count()
        == 1
    )
