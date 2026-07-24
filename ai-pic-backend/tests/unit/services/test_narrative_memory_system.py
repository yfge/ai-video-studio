from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.schemas.narrative_memory import CandidateDeltaCreate
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.narrative_memory.candidate_service import CandidateService
from app.services.narrative_memory.generation_context_service import (
    NarrativeGenerationContextService,
)
from app.services.narrative_memory.invalidation_service import (
    NarrativeMemoryInvalidationService,
)
from app.services.narrative_memory.promotion_service import PromotionService
from app.services.narrative_memory.snapshot_service import SnapshotService


def _world(db_session):
    user = User(
        username="memory-owner",
        email="memory-owner@example.com",
        hashed_password="not-used",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    virtual_ip = VirtualIP(user_id=user.id, name="林夕")
    db_session.add(virtual_ip)
    db_session.flush()
    stories = []
    characters = []
    for title in ("Story A", "Story B"):
        story = Story(
            user_id=user.id,
            title=title,
            genre="drama",
            memory_mode="story_scoped_memory_v1",
            shared_memory_baseline={"version": 0, "characters": []},
        )
        db_session.add(story)
        db_session.flush()
        character = StoryCharacter(
            story_id=story.id,
            story_business_id=story.business_id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            character_name="林夕",
        )
        db_session.add(character)
        db_session.flush()
        stories.append(story)
        characters.append(character)
    db_session.commit()
    return user, virtual_ip, stories, characters


def _anchor(repo, story, *, sequence, source_id):
    anchor = repo.create_anchor(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        narrative_sequence=sequence,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=source_id,
        source_version=1,
        source_hash=f"hash-{source_id}",
    )
    repo.flush()
    return anchor


def _private_memory(repo, story, character, virtual_ip, anchor, **values):
    memory = repo.create_memory(
        story_id=story.id,
        story_business_id=story.business_id,
        canon_branch_id="main",
        character_business_id=character.business_id,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        scope="story_private",
        memory_type="witnessed",
        content=values.get("content", "林夕看见了密门"),
        learned_at_anchor_business_id=anchor.business_id,
        effective_from_anchor_business_id=anchor.business_id,
        status=values.get("status", "approved"),
        source_artifact_type="novel_chapter",
        source_artifact_business_id=anchor.source_artifact_business_id,
        source_version=1,
        source_hash=anchor.source_hash,
        candidate_evidence=values.get(
            "candidate_evidence",
            {"growth_delta": {"current_goals": ["守住密门"]}},
        ),
    )
    repo.flush()
    return memory


def test_snapshot_is_temporal_deterministic_and_story_isolated(db_session):
    _user, virtual_ip, stories, characters = _world(db_session)
    repo = NarrativeMemoryRepository(db_session)
    early = _anchor(repo, stories[0], sequence=100, source_id="a-early")
    learned = _anchor(repo, stories[0], sequence=200, source_id="a-learned")
    other = _anchor(repo, stories[1], sequence=300, source_id="b-current")
    memory = _private_memory(repo, stories[0], characters[0], virtual_ip, learned)
    repo.commit()

    service = SnapshotService(repo)
    before = service.rebuild(
        stories[0],
        character_business_id=characters[0].business_id,
        as_of_anchor_business_id=early.business_id,
    )
    after = service.rebuild(
        stories[0],
        character_business_id=characters[0].business_id,
        as_of_anchor_business_id=learned.business_id,
    )
    repeated = service.rebuild(
        stories[0],
        character_business_id=characters[0].business_id,
        as_of_anchor_business_id=learned.business_id,
    )
    isolated = service.rebuild(
        stories[1],
        character_business_id=characters[1].business_id,
        as_of_anchor_business_id=other.business_id,
    )

    assert memory.business_id not in before.included_memory_ids
    assert memory.business_id in after.included_memory_ids
    assert repeated.snapshot_hash == after.snapshot_hash
    assert memory.business_id not in isolated.included_memory_ids
    assert after.growth_state["current_goals"] == ["守住密门"]


def test_approval_freeze_and_source_change_propagate_stale(db_session):
    user, virtual_ip, stories, characters = _world(db_session)
    story = stories[0]
    repo = NarrativeMemoryRepository(db_session)
    anchor = _anchor(repo, story, sequence=100, source_id="chapter-a")
    memory = _private_memory(
        repo, story, characters[0], virtual_ip, anchor, status="candidate"
    )
    memory.source_artifact_type = "episode"
    repo.commit()
    CandidateService(repo).review(
        story,
        memory.business_id,
        expected_version=1,
        approved=True,
        user_id=user.id,
        reason=None,
    )
    episode = Episode(story_id=story.id, episode_number=1, title="第一集")
    db_session.add(episode)
    db_session.flush()
    NarrativeGenerationContextService(repo).freeze_episode(story, episode)
    evidence = episode.memory_snapshot_evidence

    result = NarrativeMemoryInvalidationService(repo).mark_source_changed(
        story,
        artifact_business_id="chapter-a",
        source_before_hash="hash-chapter-a",
        source_after_hash="changed-hash",
    )
    assert story.memory_ledger_version == 1
    assert evidence["character_snapshots"][0]["snapshot_hash"]
    assert memory.business_id in result["affected_candidate_ids"]
    assert anchor.business_id in result["stale_anchor_ids"]
    assert anchor.status == "stale"
    assert repo.get_anchor(story.id, anchor.business_id) is None
    assert anchor not in repo.list_anchors(story.id)
    assert memory.status == "stale"
    assert episode.memory_snapshot_stale is True


def test_shared_memory_requires_manual_promotion_and_frozen_baseline(db_session):
    user, virtual_ip, stories, characters = _world(db_session)
    repo = NarrativeMemoryRepository(db_session)
    promotion_repo = NarrativePromotionRepository(db_session)
    anchor = _anchor(repo, stories[0], sequence=100, source_id="chapter-a")
    memory = _private_memory(repo, stories[0], characters[0], virtual_ip, anchor)
    repo.commit()

    service = PromotionService(repo, promotion_repo)
    promotion = service.create_candidate(
        memory.business_id, [memory.business_id], "林夕长期害怕封闭空间", user
    )
    assert promotion.status == "pending"
    assert promotion_repo.list_shared_memories(virtual_ip.id) == []
    service.review(
        promotion.business_id,
        expected_version=1,
        approved=True,
        reason="人工确认可跨 Story 复用",
        user=user,
    )
    baseline = BaselineService(repo, promotion_repo).freeze(stories[1])
    assert baseline["characters"][0]["memories"][0]["content"] == "林夕长期害怕封闭空间"
    assert repo.list_private_memories(stories[1].id) == []


def test_offscreen_event_is_persisted_but_hidden_from_audience(db_session):
    user, _virtual_ip, stories, _characters = _world(db_session)
    story = stories[0]
    repo = NarrativeMemoryRepository(db_session)
    anchor = _anchor(repo, story, sequence=100, source_id="chapter-offscreen")
    payload = CandidateDeltaCreate.model_validate(
        {
            "events": [
                {
                    "event_type": "reveal",
                    "summary": "反派在画外调换了证物",
                    "occurred_at_anchor_business_id": anchor.business_id,
                    "presentation": "offscreen",
                    "audience_disclosure": "hidden",
                    "source_artifact_type": "episode",
                    "source_artifact_business_id": "chapter-offscreen",
                    "source_hash": "hash-chapter-offscreen",
                }
            ]
        }
    )
    event = CandidateService(repo).ingest(story, payload, user)["events"][0]
    CandidateService(repo).review(
        story,
        event.business_id,
        expected_version=1,
        approved=True,
        user_id=user.id,
        reason="事件已发生，但当前不向观众展示",
    )
    episode = Episode(story_id=story.id, episode_number=1, title="第一集")
    db_session.add(episode)
    db_session.flush()

    context = NarrativeGenerationContextService(repo).freeze_episode(story, episode)

    assert context["approved_events"][0]["presentation"] == "offscreen"
    assert event.business_id in context["audience_disclosure"]["must_hide"]
