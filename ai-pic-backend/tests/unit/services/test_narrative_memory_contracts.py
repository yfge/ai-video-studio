from types import SimpleNamespace

import pytest
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.schemas.narrative_memory import CharacterMemoryCandidateCreate
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.narrative_memory.dramatic_state_service import DramaticStateService
from pydantic import ValidationError as PydanticValidationError
from tests.unit.services.test_narrative_memory_system import _world


def test_story_private_memory_requires_occurrence_anchor():
    with pytest.raises(PydanticValidationError):
        CharacterMemoryCandidateCreate.model_validate(
            {
                "character_business_id": "character-a",
                "virtual_ip_business_id": "virtual-ip-a",
                "memory_type": "inferred",
                "content": "角色推断出有人撒谎",
                "learned_at_anchor_business_id": "anchor-a",
                "effective_from_anchor_business_id": "anchor-a",
                "source_artifact_type": "novel_chapter",
                "source_artifact_business_id": "chapter-a",
                "source_hash": "hash-a",
            }
        )


def test_shared_memory_is_filtered_by_canon_branch(db_session):
    _user, virtual_ip, stories, _characters = _world(db_session)
    repo = NarrativeMemoryRepository(db_session)
    promotion_repo = NarrativePromotionRepository(db_session)
    promotion_repo.create_shared_memory(
        story_id=None,
        story_business_id=None,
        canon_branch_id="alternate",
        character_business_id=None,
        virtual_ip_id=virtual_ip.id,
        virtual_ip_business_id=virtual_ip.business_id,
        scope="character_shared",
        memory_type="remembered",
        content="只属于平行连续性的经历",
        learned_at_anchor_business_id="shared_baseline",
        effective_from_anchor_business_id="shared_baseline",
        status="approved",
        source_artifact_type="test",
        source_artifact_business_id="alternate-source",
        source_hash="alternate-hash",
        version=1,
    )
    promotion_repo.commit()

    baseline = BaselineService(repo, promotion_repo).freeze(stories[0])

    assert baseline["characters"][0]["memories"] == []
    assert (
        len(
            promotion_repo.list_shared_memories(
                virtual_ip.id, canon_branch_id="alternate"
            )
        )
        == 1
    )


def test_dramatic_state_gate_separates_subtext_and_disclosure():
    state = {
        "must_not_reveal": ["密门在井下"],
        "character_intents": [
            {
                "character_business_id": "char-a",
                "hidden_goal": "逼他交出钥匙",
                "expression_policy": "subtext_only",
            }
        ],
    }
    script = SimpleNamespace(
        dialogues=[{"scene_number": 1, "content": "密门在井下，逼他交出钥匙"}]
    )
    gate = DramaticStateService._quality_gate(state, script, {"scene_number": 1})
    assert gate["passed"] is False
    assert {item["id"] for item in gate["blocking_issues"]} == {
        "must_not_reveal",
        "subtext_spoken_directly",
    }
