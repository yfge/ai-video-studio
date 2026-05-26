from app.models.script import Episode, Script, Story
from app.models.timeline import Timeline
from app.services.audio.storyboard_from_timeline_spec import (
    build_storyboard_frames_from_timeline_spec,
    generate_storyboard_support_from_timeline_spec,
)


def _timeline_spec(script: Script, episode: Episode, *, timeline_id: int | None = 7):
    return {
        "spec_version": "timeline.v1",
        "timeline_id": timeline_id,
        "episode_id": episode.id,
        "script_id": script.id,
        "version": 3,
        "source_audio_timeline_version": 8,
        "tracks": [
            {
                "track_type": "dialogue",
                "clips": [
                    {
                        "clip_id": "dialogue_scene_1_beat_2_001",
                        "track_type": "dialogue",
                        "scene_id": 1,
                        "scene_number": 1,
                        "beat_id": 2,
                        "beat_type": "dialogue",
                        "speaker_name": "A",
                        "text": "hello",
                        "start_ms": 0,
                        "end_ms": 1200,
                        "source": {
                            "kind": "audio_timeline_beat",
                            "scene_id": 1,
                            "beat_id": 2,
                            "audio_timeline_version": 8,
                        },
                    }
                ],
            }
        ],
    }


def _timeline_spec_with_shot_plan(
    script: Script, episode: Episode, *, timeline_id: int | None = 7
):
    spec = _timeline_spec(script, episode, timeline_id=timeline_id)
    dialogue_track = spec["tracks"][0]
    spec["tracks"] = [
        dialogue_track,
        {
            "track_type": "video",
            "clips": [
                {
                    "clip_id": "video_scene_1_beat_2_001",
                    "track_type": "video",
                    "scene_id": 1,
                    "scene_number": 1,
                    "beat_id": 2,
                    "beat_type": "dialogue",
                    "start_ms": 0,
                    "end_ms": 1200,
                    "duration_ms": 1200,
                    "text": "A discovers the locked door.",
                    "source": {
                        "kind": "audio_timeline_beat",
                        "scene_id": 1,
                        "beat_id": 2,
                        "audio_timeline_version": 8,
                    },
                    "source_refs": {
                        "scene_beat_id": 2,
                        "audio_timeline_version": 8,
                        "timeline_shot_plan": {
                            "clip_id": "video_scene_1_beat_2_001",
                            "duration_ms": 1200,
                            "plot": "A discovers the locked door.",
                            "dialogue_source": "A: hello",
                            "visual_prompt": "Cartoon robot studies a locked door.",
                            "video_prompt": "Cartoon robot studies a locked door, 1.2s.",
                            "character_anchor": "blue cartoon robot",
                            "camera": "slow push-in",
                            "action": "studies the lock",
                            "style": "3d_cartoon",
                            "provider": "deepseek",
                            "model": "deepseek-v4-flash",
                        },
                    },
                }
            ],
        },
    ]
    return spec


def test_build_storyboard_frames_from_timeline_spec_marks_source():
    story = Story(title="Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")

    frames = build_storyboard_frames_from_timeline_spec(
        timeline_spec=_timeline_spec(script, episode)
    )

    assert len(frames) == 1
    assert frames[0]["generation_source"] == "timeline_spec"
    assert frames[0]["generation_method"] == "timeline_spec"
    assert frames[0]["timeline_clip_id"] == "dialogue_scene_1_beat_2_001"
    assert frames[0]["source"]["kind"] == "timeline_clip"
    assert "画面主体:" in frames[0]["prompt_description"]
    assert "竖屏短剧单镜头" in frames[0]["prompt_description"]
    assert "禁止项:" in frames[0]["prompt_description"]
    assert "hello" not in frames[0]["prompt_description"]


def test_build_storyboard_frames_from_timeline_spec_prefers_shot_plan():
    story = Story(title="Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")

    frames = build_storyboard_frames_from_timeline_spec(
        timeline_spec=_timeline_spec_with_shot_plan(script, episode)
    )

    assert len(frames) == 1
    assert frames[0]["generation_source"] == "timeline_spec"
    assert frames[0]["generation_method"] == "timeline_shot_plan"
    assert frames[0]["timeline_clip_id"] == "video_scene_1_beat_2_001"
    assert frames[0]["source"]["kind"] == "timeline_clip"
    assert frames[0]["source"]["shot_plan"] == "timeline_shot_plan"
    assert frames[0]["timeline_shot_plan"]["provider"] == "deepseek"
    assert frames[0]["prompt_description"] == "Cartoon robot studies a locked door."


def test_generate_storyboard_support_from_timeline_spec_persists_meta(db_session):
    story = Story(title="Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")
    db_session.add_all([story, episode, script])
    db_session.commit()
    db_session.refresh(episode)
    db_session.refresh(script)

    timeline = Timeline(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        script_id=script.id,
        script_business_id=script.business_id,
        title="Timeline",
        status="draft",
        version=3,
        source_audio_timeline_version=8,
        spec=_timeline_spec(script, episode, timeline_id=None),
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)
    timeline.spec = {**timeline.spec, "timeline_id": timeline.id}
    db_session.commit()

    result = generate_storyboard_support_from_timeline_spec(
        db_session,
        script=script,
        episode=episode,
        timeline=timeline,
        overwrite_existing=True,
    )

    assert result["meta"]["generation_source"] == "timeline_spec"
    assert result["meta"]["timeline_id"] == timeline.id
    assert result["meta"]["timeline_version"] == 3
    assert result["meta"]["source_audio_timeline_version"] == 8
    frame = script.extra_metadata["storyboard"]["frames"][0]
    assert frame["timeline_clip_id"]
    assert frame["source"]["kind"] == "timeline_clip"
    assert "画面主体:" in frame["prompt_description"]
    assert "短剧竖屏镜头提示:" in frame["ai_prompt"]
    assert "统一要求:" in frame["ai_prompt"]


def test_generate_storyboard_support_from_timeline_spec_persists_shot_plan_meta(
    db_session,
):
    story = Story(title="Story", genre="drama")
    episode = Episode(story=story, episode_number=1, title="Episode")
    script = Script(episode=episode, title="Script", content="")
    db_session.add_all([story, episode, script])
    db_session.commit()
    db_session.refresh(episode)
    db_session.refresh(script)

    timeline = Timeline(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        script_id=script.id,
        script_business_id=script.business_id,
        title="Timeline",
        status="draft",
        version=3,
        source_audio_timeline_version=8,
        spec=_timeline_spec_with_shot_plan(script, episode, timeline_id=None),
    )
    db_session.add(timeline)
    db_session.commit()
    db_session.refresh(timeline)
    timeline.spec = {**timeline.spec, "timeline_id": timeline.id}
    db_session.commit()

    result = generate_storyboard_support_from_timeline_spec(
        db_session,
        script=script,
        episode=episode,
        timeline=timeline,
        overwrite_existing=True,
    )

    assert result["meta"]["generation_method"] == "timeline_shot_plan"
    frame = script.extra_metadata["storyboard"]["frames"][0]
    assert frame["timeline_clip_id"] == "video_scene_1_beat_2_001"
    assert frame["timeline_shot_plan"]["model"] == "deepseek-v4-flash"
