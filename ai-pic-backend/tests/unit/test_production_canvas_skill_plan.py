from __future__ import annotations

from app.models.script import Episode, Script, Story
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
        ),
    )

    assert plan.skill_manifest.version == "production_canvas.v1"
    assert [skill.id for skill in plan.skill_manifest.skills[:7]] == [
        "brief.compose",
        "asset.select",
        "virtual_ip.image",
        "environment.image",
        "script.generate",
        "timeline.assemble",
        "storyboard.plan",
    ]
    assert [result.skill for result in plan.skill_results[:7]] == [
        "brief.compose",
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
    assert "复用现有 IP" in plan.nodes[1].detail
    assert plan.nodes[1].outputs["environment_ids"] == [environment.id]
    assert plan.nodes[1].reuse_targets[0].target.endswith("VirtualIPRepository")
    assert plan.nodes[1].outputs["candidate_environment_ids"] == [environment.id]
    assert virtual_ip_image_result.status == "ready"
    assert virtual_ip_image_result.outputs["virtual_ip_ids"] == [virtual_ip.id]
    assert environment_image_result.status == "ready"
    assert environment_image_result.outputs["environment_ids"] == [environment.id]
    assert script_result.status == "blocked"
    assert script_result.outputs["required_inputs"] == ["episode_id"]


def test_canvas_skill_plan_does_not_fallback_to_unmatched_assets(db_session):
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
        ProductionCanvasPlanRequest(prompt="基于林妹妹做第 4 集，办公室轻喜剧"),
    )

    assert plan.selected_assets.virtual_ips == []
    assert plan.selected_assets.environments == []
    assert plan.nodes[1].title == "待确认 IP 和环境资产"
    assert plan.nodes[1].outputs == {
        "virtual_ip_ids": [],
        "environment_ids": [],
        "candidate_virtual_ip_ids": [],
        "candidate_environment_ids": [],
    }
    assert plan.skill_results[1].status == "blocked"
    virtual_ip_image_result = next(
        result for result in plan.skill_results if result.skill == "virtual_ip.image"
    )
    environment_image_result = next(
        result for result in plan.skill_results if result.skill == "environment.image"
    )
    assert virtual_ip_image_result.status == "blocked"
    assert virtual_ip_image_result.outputs["required_inputs"] == ["virtual_ip_id"]
    assert environment_image_result.status == "blocked"
    assert environment_image_result.outputs["required_inputs"] == ["environment_id"]


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
    assert plan.nodes[1].title == "IP 待确认；已选择环境：办公室"
    assert plan.nodes[1].outputs["environment_ids"] == [environment.id]


def test_canvas_skill_plan_marks_downstream_ready_with_episode_context(db_session):
    user = _user(db_session, "canvas_skill_episode_owner")
    virtual_ip = VirtualIP(
        user_id=user.id,
        name="林妹妹",
        tags=["轻喜剧"],
        is_active=True,
    )
    db_session.add(virtual_ip)
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于林妹妹做第 4 集，办公室轻喜剧",
            episode_id=123,
        ),
    )
    script_result = next(
        result for result in plan.skill_results if result.skill == "script.generate"
    )

    assert script_result.status == "ready"
    assert script_result.outputs["episode_id"] == 123
    assert "required_inputs" not in script_result.outputs


def test_canvas_skill_plan_carries_script_context_for_downstream_execution(
    db_session,
):
    user = _user(db_session, "canvas_skill_script_owner")
    story = Story(
        user_id=user.id,
        title="程序员轻喜剧",
        genre="comedy",
    )
    db_session.add(story)
    db_session.commit()
    episode = Episode(
        story_id=story.id,
        episode_number=4,
        title="智能生活入门",
    )
    db_session.add(episode)
    db_session.commit()
    script = Script(
        episode_id=episode.id,
        title="第 4 集剧本",
        content="办公室轻喜剧",
    )
    db_session.add(script)
    db_session.commit()

    plan = build_canvas_skill_plan(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="基于现有剧本继续生成分镜和时间线",
            episode_id=episode.id,
            script_id=script.id,
        ),
    )

    storyboard_result = next(
        result for result in plan.skill_results if result.skill == "storyboard.plan"
    )
    timeline_result = next(
        result for result in plan.skill_results if result.skill == "timeline.assemble"
    )

    assert storyboard_result.status == "ready"
    assert storyboard_result.outputs["script_id"] == script.id
    assert storyboard_result.outputs["episode_id"] == episode.id
    assert timeline_result.status == "ready"
    assert timeline_result.outputs["script_id"] == script.id
