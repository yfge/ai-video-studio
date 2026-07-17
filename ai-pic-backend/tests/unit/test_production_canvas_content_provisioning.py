from __future__ import annotations

import pytest
from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from app.services.production_canvas.production_context_resolution import (
    resolve_production_context,
)


def _user(db_session, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _planning(
    *,
    virtual_ip_name: str,
    asset_policy: str = "create_if_missing",
) -> ProductionCanvasPlanningDraft:
    return ProductionCanvasPlanningDraft.model_validate(
        {
            "brief": {
                "source_prompt": "让小夏在海边经营一家会移动的咖啡车，先做两集。",
                "intent": {
                    "kind": "story_series",
                    "objective": "创建可持续发展的海边咖啡车系列短剧",
                    "narrative_seed": "小夏用移动咖啡车解决海边游客的临时难题",
                    "must_include": ["小夏", "海边", "移动咖啡车", "两集"],
                },
                "video_spec": {
                    "duration_seconds": 90,
                    "episode_count": 2,
                    "focus_episode_number": 1,
                    "aspect_ratio": "9:16",
                },
                "assets": {
                    "virtual_ip_name": virtual_ip_name,
                    "environment_names": ["海边咖啡车"],
                    "asset_policy": asset_policy,
                },
            },
            "content_plan": {
                "title": "移动咖啡车",
                "premise": "小夏开着会移动的咖啡车，在海边遇见不同游客。",
                "synopsis": "每一集都由一位游客的临时难题触发，小夏用咖啡车和观察力解决问题。",
                "main_conflict": "游客的即时需求与海边有限条件持续冲突。",
                "characters": [
                    {
                        "name": "小夏",
                        "role": "主角",
                        "description": "移动咖啡车店主，擅长观察游客真正需要什么。",
                        "season_arc": "从独自经营逐步建立海边互助网络。",
                        "continuity_anchors": ["移动咖啡车", "手写订单本"],
                    }
                ],
                "environments": [
                    {
                        "name": "海边咖啡车",
                        "purpose": "承载每集问题、行动和阶段性兑现。",
                        "reuse_across_episodes": True,
                    }
                ],
                "season_arc": "小夏通过一次次临时委托认识海边社区，并找到长期经营方向。",
                "recurring_engine": "新游客提出难题，小夏用咖啡车资源完成一次可见解决。",
                "episodes": [
                    {
                        "episode_number": 1,
                        "title": "没有冰的冰咖啡",
                        "logline": "停电时，小夏必须为中暑游客做出一杯真正降温的咖啡。",
                        "beats": ["游客中暑", "冰柜停电", "小夏改用海水降温桶"],
                        "payoff": "游客喝到降温咖啡并恢复精神。",
                        "cliffhanger": "订单本出现一张没有署名的长期订单。",
                        "continuity_handoff": ["保留匿名长期订单"],
                    },
                    {
                        "episode_number": 2,
                        "title": "匿名订单",
                        "logline": "小夏追查长期订单来源，却发现整片海滩都需要夜间补给。",
                        "beats": ["追查订单", "发现夜间工人", "决定试运营夜班"],
                        "payoff": "咖啡车完成第一次夜间配送。",
                        "cliffhanger": "远处灯塔发来新的求助信号。",
                        "continuity_handoff": ["咖啡车开始夜间运营"],
                    },
                ],
                "continuity_rules": ["小夏保留手写订单本记录每次委托。"],
                "future_threads": ["灯塔求助", "海边夜间社区"],
            },
        }
    )


@pytest.mark.unit
def test_structured_content_plan_creates_story_episodes_and_assets(db_session):
    user = _user(db_session, "canvas_content_provisioning_owner")
    prompt = "让小夏在海边经营一家会移动的咖啡车，先做两集。"

    resolved = resolve_production_context(
        db_session,
        user,
        ProductionCanvasPlanRequest(prompt=prompt, planning_mode="series"),
        _planning(virtual_ip_name="小夏"),
    )

    assert resolved.context.brief.ready_for_execution is True
    assert len(resolved.context.created_story_ids) == 1
    assert len(resolved.context.created_episode_ids) == 2
    assert resolved.request.story_id == resolved.context.created_story_ids[0]
    assert resolved.request.episode_id == resolved.context.created_episode_ids[0]
    assert {item.decision for item in resolved.context.asset_associations} == {
        "created"
    }

    story = db_session.get(Story, resolved.request.story_id)
    assert story is not None
    assert story.title == "移动咖啡车"
    assert story.generation_prompt == prompt
    assert story.extra_metadata["content_plan"]["recurring_engine"].startswith(
        "新游客提出难题"
    )
    episodes = (
        db_session.query(Episode)
        .filter(Episode.story_id == story.id)
        .order_by(Episode.episode_number)
        .all()
    )
    assert [item.title for item in episodes] == ["没有冰的冰咖啡", "匿名订单"]
    assert episodes[1].extra_metadata["episode_plan"]["cliffhanger"] == (
        "远处灯塔发来新的求助信号。"
    )
    assert (
        db_session.query(StoryCharacter)
        .filter(StoryCharacter.story_id == story.id)
        .one()
        .character_name
        == "小夏"
    )


@pytest.mark.unit
def test_ambiguous_asset_match_blocks_and_reports_ambiguity(db_session):
    user = _user(db_session, "canvas_ambiguous_asset_owner")
    db_session.add_all(
        [
            VirtualIP(
                user_id=user.id,
                name="双生角色甲",
                tags=["双生角色"],
                is_active=True,
            ),
            VirtualIP(
                user_id=user.id,
                name="双生角色乙",
                tags=["双生角色"],
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    resolved = resolve_production_context(
        db_session,
        user,
        ProductionCanvasPlanRequest(
            prompt="让双生角色制作一部连续短剧。",
            planning_mode="series",
        ),
        _planning(
            virtual_ip_name="双生角色",
            asset_policy="reuse_preferred",
        ),
    )

    assert resolved.context.brief.ready_for_execution is False
    assert any(
        item.id == "context.virtual_ip_id"
        for item in resolved.context.brief.clarifications
    )
    association = next(
        item
        for item in resolved.context.asset_associations
        if item.kind == "virtual_ip"
    )
    assert association.decision == "ambiguous"
    assert len(association.candidate_ids) == 2
    assert resolved.context.created_story_ids == []
    assert resolved.context.created_episode_ids == []
