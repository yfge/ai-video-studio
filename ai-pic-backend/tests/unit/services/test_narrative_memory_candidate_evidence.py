from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_service import CandidateService
from tests.unit.services.test_narrative_memory_system import (
    _anchor,
    _private_memory,
    _world,
)


def test_source_approval_can_require_verified_chapter_evidence(db_session):
    user, virtual_ip, stories, characters = _world(db_session)
    story = stories[0]
    repo = NarrativeMemoryRepository(db_session)
    anchor = _anchor(repo, story, sequence=100, source_id="chapter-a")
    unverified = _private_memory(
        repo,
        story,
        characters[0],
        virtual_ip,
        anchor,
        status="candidate",
        candidate_evidence={},
    )
    verified = _private_memory(
        repo,
        story,
        characters[0],
        virtual_ip,
        anchor,
        status="candidate",
        content="林夕记得钥匙的位置",
        candidate_evidence={
            "source_quote": "林夕记得钥匙的位置",
            "source_quote_verified": True,
        },
    )
    extra_verified = _private_memory(
        repo,
        story,
        characters[0],
        virtual_ip,
        anchor,
        status="candidate",
        content="另一条已验证记忆",
        candidate_evidence={
            "source_quote": "另一条已验证记忆",
            "source_quote_verified": True,
        },
    )
    repo.commit()

    promoted = CandidateService(repo).approve_source_candidates(
        story,
        valid_sources={"chapter-a": "hash-chapter-a"},
        user_id=user.id,
        require_verified_evidence=True,
        eligible_candidate_ids={verified.business_id},
    )

    assert promoted == [verified.business_id]
    assert unverified.status == "candidate"
    assert verified.status == "approved"
    assert extra_verified.status == "candidate"
