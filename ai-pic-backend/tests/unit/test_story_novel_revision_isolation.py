from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from tests.unit.test_story_novel_longform import _plan_row, _setup


def _chapter_candidates(repo, story, user, chapter, virtual_ip, character, label):
    source_hash = novel_chapter_source_hash(chapter)
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        chapter_business_id=chapter.business_id,
        narrative_sequence=chapter.position * 1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    event = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary=f"{label}事实",
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
        created_by=user.id,
    )
    memory = repo.create_memory(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        character_business_id=character.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        scope="story_private",
        memory_type="witnessed",
        content=f"{label}记忆",
        occurred_at_anchor_business_id=anchor.business_id,
        learned_at_anchor_business_id=anchor.business_id,
        effective_from_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
        created_by=user.id,
    )
    repo.flush()
    return event, memory, anchor


def _ready_for_approval(db, revision, chapter, event, memory):
    source_hash = novel_chapter_source_hash(chapter)
    revision.continuity_ledger = {
        "chapters": {
            "1": {
                "status": "ready",
                "body_hash": chapter.content_hash,
                "source_hash": source_hash,
                "extraction_status": "ready",
                "event_ids": [event.business_id],
                "memory_ids": [memory.business_id],
            }
        }
    }
    revision.continuity_report = {
        "coverage": [
            {
                "business_id": chapter.business_id,
                "content_hash": chapter.content_hash,
                "position": 1,
            }
        ],
        "issues": [],
    }
    revision.continuity_status = "passed"
    db.commit()


def test_new_canonical_revision_retires_old_facts_memories_and_snapshots(db_session):
    user, story, service, first, _task, virtual_ip, character = _setup(
        db_session, with_character=True
    )
    first.generation_plan = {
        "status": "ready",
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [_plan_row()],
    }
    first.chapter_count = 1
    first_chapter = service.checkpoint_chapter(
        first,
        position=1,
        title="第一版",
        content_text="旧" * 3000,
        summary="旧版",
        cliffhanger=None,
    )
    repo = NarrativeMemoryRepository(db_session)
    old_event, old_memory, old_anchor = _chapter_candidates(
        repo, story, user, first_chapter, virtual_ip, character, "旧版"
    )
    _ready_for_approval(db_session, first, first_chapter, old_event, old_memory)
    service.approve(first.business_id)
    snapshot = repo.create_snapshot(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        character_business_id=character.business_id,
        virtual_ip_business_id=virtual_ip.business_id,
        as_of_anchor_business_id=old_anchor.business_id,
        shared_baseline_version=0,
        approved_memory_watermark=story.memory_ledger_version,
        included_memory_ids=[old_memory.business_id],
        growth_state={},
        snapshot_hash="old-snapshot",
    )
    repo.commit()

    second = service.clone(first.business_id)
    second_chapter = second.chapters[0]
    second_chapter.title = "第二版"
    second_chapter.content_text = "新" * 3000
    second_chapter.content_hash = service.checkpoint_chapter(
        second,
        position=1,
        title="第二版",
        content_text="新" * 3000,
        summary="新版",
        cliffhanger=None,
    ).content_hash
    new_event, new_memory, _ = _chapter_candidates(
        repo, story, user, second_chapter, virtual_ip, character, "新版"
    )
    unrelated = repo.create_event(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        event_type="reveal",
        summary="其他草稿",
        occurred_at_anchor_business_id=old_anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="other-draft-chapter",
        source_version=1,
        source_hash="other-draft-hash",
        created_by=user.id,
    )
    repo.flush()
    _ready_for_approval(db_session, second, second_chapter, new_event, new_memory)

    service.approve(second.business_id)

    assert first.lifecycle_status == "superseded"
    assert story.canonical_novel_export_id == second.id
    assert old_event.status == old_memory.status == "superseded"
    assert new_event.status == new_memory.status == "approved"
    assert unrelated.status == "candidate"
    assert snapshot.is_stale is True
    assert {
        item.business_id for item in repo.list_events(story.id, status="approved")
    } == {new_event.business_id}
    assert {
        item.business_id
        for item in repo.list_private_memories(story.id, status="approved")
    } == {new_memory.business_id}
