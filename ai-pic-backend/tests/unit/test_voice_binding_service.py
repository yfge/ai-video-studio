import pytest
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.virtual_ip import VirtualIP
from app.services.ai_service import ai_service
from app.services.voice_binding_service import (
    ensure_derived_character_voice_binding,
    ensure_virtual_ip_voice_config,
)


@pytest.mark.asyncio
async def test_ensure_virtual_ip_voice_config_fallback_when_ai_missing(
    db_session, monkeypatch
):
    monkeypatch.setattr(ai_service, "ai_manager", None, raising=False)

    vip = VirtualIP(name="测试角色", description="勇敢的年轻人")
    db_session.add(vip)
    db_session.commit()
    db_session.refresh(vip)

    cfg = await ensure_virtual_ip_voice_config(db_session, vip)
    assert cfg["provider"] == "minimax"
    assert cfg["tts_model"] == "speech-2.6-hd"
    assert isinstance(cfg.get("voice_id"), str) and cfg["voice_id"]
    assert cfg["selected_by"] in {"agent", "fallback"}

    refreshed = db_session.query(VirtualIP).filter(VirtualIP.id == vip.id).first()
    assert refreshed
    assert isinstance(refreshed.voice_config, dict)
    assert refreshed.voice_config.get("voice_id") == cfg["voice_id"]


@pytest.mark.asyncio
async def test_ensure_derived_character_voice_binding_fallback_scope_episode(
    db_session, monkeypatch
):
    monkeypatch.setattr(ai_service, "ai_manager", None, raising=False)

    story = Story(title="S", genre="G")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    ep = Episode(story_id=story.id, episode_number=1, title="E1")
    db_session.add(ep)
    db_session.commit()
    db_session.refresh(ep)

    script = Script(
        episode_id=ep.id,
        title="Script",
        dialogues=[
            {"scene_number": 1, "character": "路人", "content": "你好"},
            {"scene_number": 1, "character": "路人", "content": "再见"},
        ],
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)

    scope, cfg = await ensure_derived_character_voice_binding(
        db_session,
        story=story,
        episode=ep,
        scene=None,
        script_dialogues=script.dialogues,
        character_name="路人",
    )
    assert scope == "episode"
    assert cfg.get("voice_id")

    refreshed = db_session.query(Episode).filter(Episode.id == ep.id).first()
    assert refreshed
    bindings = (refreshed.extra_metadata or {}).get(
        "derived_character_voice_bindings"
    ) or {}
    assert isinstance(bindings, dict)
    assert any(isinstance(v, dict) and v.get("voice_config") for v in bindings.values())


@pytest.mark.asyncio
async def test_ensure_derived_character_voice_binding_fallback_scope_story(
    db_session, monkeypatch
):
    monkeypatch.setattr(ai_service, "ai_manager", None, raising=False)

    story = Story(title="S", genre="G")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    ep1 = Episode(story_id=story.id, episode_number=1, title="E1")
    ep2 = Episode(story_id=story.id, episode_number=2, title="E2")
    db_session.add_all([ep1, ep2])
    db_session.commit()
    db_session.refresh(ep1)
    db_session.refresh(ep2)

    # Latest script for ep1 contains the derived character
    db_session.add(
        Script(
            episode_id=ep1.id,
            title="S1",
            dialogues=[{"scene_number": 1, "character": "店员", "content": "欢迎光临"}],
        )
    )
    # Latest script for ep2 also contains the same derived character
    db_session.add(
        Script(
            episode_id=ep2.id,
            title="S2",
            dialogues=[{"scene_number": 1, "character": "店员", "content": "这边请"}],
        )
    )
    db_session.commit()

    scope, cfg = await ensure_derived_character_voice_binding(
        db_session,
        story=story,
        episode=ep2,
        scene=None,
        script_dialogues=[
            {"scene_number": 1, "character": "店员", "content": "这边请"}
        ],
        character_name="店员",
    )
    assert scope == "story"
    assert cfg.get("voice_id")

    refreshed = db_session.query(Story).filter(Story.id == story.id).first()
    assert refreshed
    bindings = (refreshed.extra_metadata or {}).get(
        "derived_character_voice_bindings"
    ) or {}
    assert isinstance(bindings, dict)
    assert any(isinstance(v, dict) and v.get("voice_config") for v in bindings.values())


@pytest.mark.asyncio
async def test_ensure_derived_character_voice_binding_fallback_scope_scene(
    db_session, monkeypatch
):
    monkeypatch.setattr(ai_service, "ai_manager", None, raising=False)

    story = Story(title="S", genre="G")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    ep = Episode(story_id=story.id, episode_number=1, title="E1")
    db_session.add(ep)
    db_session.commit()
    db_session.refresh(ep)

    script = Script(episode_id=ep.id, title="Script", dialogues=[])
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)

    scene = Scene(script_id=script.id, scene_number="1", slug_line="INT. TEST - DAY")
    db_session.add(scene)
    db_session.commit()
    db_session.refresh(scene)

    scope, cfg = await ensure_derived_character_voice_binding(
        db_session,
        story=story,
        episode=ep,
        scene=scene,
        script_dialogues=[
            {"scene_number": 1, "character": "路人甲", "content": "（沉默）"}
        ],
        character_name="路人甲",
    )
    assert scope == "scene"
    assert cfg.get("voice_id")

    refreshed = db_session.query(Scene).filter(Scene.id == scene.id).first()
    assert refreshed
    bindings = (refreshed.extra_metadata or {}).get(
        "derived_character_voice_bindings"
    ) or {}
    assert isinstance(bindings, dict)
    assert any(isinstance(v, dict) and v.get("voice_config") for v in bindings.values())
