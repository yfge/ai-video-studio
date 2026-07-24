import pytest
from app.core.exceptions import ConflictError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.candidate_service import CandidateService
from tests.unit.services.test_narrative_memory_system import (
    _anchor,
    _private_memory,
    _world,
)


def test_novel_candidate_cannot_be_approved_before_revision(db_session):
    user, virtual_ip, stories, characters = _world(db_session)
    story = stories[0]
    repo = NarrativeMemoryRepository(db_session)
    anchor = _anchor(repo, story, sequence=100, source_id="novel-chapter")
    memory = _private_memory(
        repo,
        story,
        characters[0],
        virtual_ip,
        anchor,
        status="candidate",
    )
    repo.commit()

    with pytest.raises(ConflictError, match="整部小说审批"):
        CandidateService(repo).review(
            story,
            memory.business_id,
            expected_version=1,
            approved=True,
            user_id=user.id,
            reason=None,
        )

    assert memory.status == "candidate"
