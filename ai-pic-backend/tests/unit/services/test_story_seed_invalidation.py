from app.models.script import Episode, Script, Story
from app.models.story_novel_export import StoryNovelChapter, StoryNovelExport
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.story_seed import StorySeedModel
from app.services.story.story_seed_service import StorySeedService


def _seed(*, outline: str) -> StorySeedModel:
    return StorySeedModel(
        title="长篇故事",
        premise="角色寻找失踪的同伴",
        outline=outline,
        protagonists=[
            {
                "virtual_ip_business_id": "vip-hero",
                "initial_state": "尚不知道同伴去了哪里",
            }
        ],
        world_constraints=["线索必须能追溯到已发生事件"],
        central_conflict="寻找真相会伤害现有关系",
        content_constraints=[],
    )


def test_story_seed_edit_marks_novel_episode_and_script_for_review(db_session):
    user = User(
        username="seed-owner",
        email="seed-owner@example.com",
        hashed_password="unused",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="长篇故事",
        genre="drama",
        workflow_mode="novel_adaptation_v1",
        memory_mode="story_scoped_memory_v1",
        story_seed=_seed(outline="旧大纲").model_dump(by_alias=True),
        story_seed_status="confirmed",
        story_seed_version=1,
    )
    db_session.add(story)
    db_session.flush()
    revision = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        user_id=user.id,
        style="prose",
        target_words=10000,
        chapter_count=1,
        content_text="旧小说",
        continuity_status="passed",
        adaptation_plan_status="ready",
    )
    db_session.add(revision)
    db_session.flush()
    chapter = StoryNovelChapter(
        novel_export_id=revision.id,
        novel_export_business_id=revision.business_id,
        position=1,
        title="第一章",
        content_text="旧章节",
        review_status="ready",
    )
    episode = Episode(
        story_id=story.id,
        story_business_id=story.business_id,
        episode_number=1,
        title="第一集",
        memory_snapshot_evidence={"schema": "narrative_generation_context.v1"},
    )
    db_session.add_all([chapter, episode])
    db_session.flush()
    script = Script(
        episode_id=episode.id,
        episode_business_id=episode.business_id,
        title="第一集剧本",
        extra_metadata={"narrative_memory": {}},
    )
    db_session.add(script)
    db_session.commit()

    StorySeedService(NarrativeMemoryRepository(db_session)).apply_local_update(
        story, _seed(outline="新大纲"), requested_status="draft"
    )
    db_session.commit()

    assert revision.continuity_status == "review_required"
    assert revision.adaptation_plan_status == "stale"
    assert chapter.review_status == "review_required"
    assert episode.memory_snapshot_stale is True
    assert script.extra_metadata["narrative_memory_stale"]["reason_code"] == (
        "story_seed_changed"
    )


def test_story_seed_local_update_accepts_endpoint_dumped_dict(db_session):
    user = User(
        username="seed-dict-owner",
        email="seed-dict-owner@example.com",
        hashed_password="unused",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    story = Story(
        user_id=user.id,
        title="旧标题",
        genre="drama",
        story_seed=_seed(outline="旧大纲").model_dump(by_alias=True),
        story_seed_status="draft",
        story_seed_version=1,
    )
    db_session.add(story)
    db_session.commit()

    next_seed = _seed(outline="连续第1章至第48章").model_dump(by_alias=True)
    StorySeedService(NarrativeMemoryRepository(db_session)).apply_local_update(
        story, next_seed, requested_status="draft"
    )

    assert story.story_seed["outline"] == "连续第1章至第48章"
    assert story.story_seed_schema == "story_seed_v1"
