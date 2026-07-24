from types import SimpleNamespace

import pytest
from app.core.exceptions import ServiceError
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.schemas.narrative_memory import CharacterMemoryCandidateCreate
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.narrative_memory.extraction_evidence import (
    normalize_extraction_evidence,
)
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_evidence import (
    align_source_evidence,
    source_contains_evidence,
)
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


def test_extraction_prompt_bounds_per_chapter_candidate_volume():
    prompt = NarrativeExtractionService._prompt(
        "正文",
        [{"name": "主角"}],
        [
            SimpleNamespace(
                business_id="anchor-a", source_artifact_business_id="chapter-a"
            )
        ],
    )
    assert "events 最多 8 条" in prompt
    assert "memories 总计最多 6 条" in prompt
    assert "允许 events 或 memories 为空数组" in prompt
    assert '"event_type":"action|reveal|relationship|state_change|world_fact"' in prompt
    assert '"presentation":"on_screen|offscreen|withheld"' in prompt
    assert '"evidence":"正文逐字证据"' in prompt
    assert '"typed_fact_id":"事实ID"' in prompt
    assert "不得用角色在别处出现的姓名拼接他人对话" in prompt


def test_candidate_evidence_must_exist_in_source():
    source = "褚蓝打开保险箱，取出零号风钥。黎雁确认接收。"

    assert source_contains_evidence(
        source, "褚蓝打开保险箱，取出零号风钥……黎雁确认接收"
    )
    assert not source_contains_evidence(source, "裴衡承认制造旱潮")


def test_extraction_evidence_aligns_only_ordered_source_fragments():
    source = (
        "黎雁站在露台上，看着天光变白。"
        "风里带着盐和锈的味道。"
        "她低头看表，2174年8月3日，07:23。"
    )
    evidence = "黎雁站在露台上，看着天光变白。她低头看表，2174年8月3日，07:23。"

    aligned = align_source_evidence(source, evidence)

    assert aligned == ("黎雁站在露台上，看着天光变白……她低头看表，2174年8月3日，07:23")
    assert source_contains_evidence(source, aligned)
    assert align_source_evidence(source, "裴衡承认制造旱潮") == "裴衡承认制造旱潮"


def test_extraction_evidence_restores_short_dialogue_attribution():
    source = (
        "我可以告诉你，数据来自三个独立的气象站。"
        "“可以。”他说，“但你必须在一周内完成验证。九月二十日不会等你。”"
    )
    normalized = {
        "events": [],
        "memories": [
            {"evidence": "可以。但你必须在一周内完成验证。九月二十日不会等你。"}
        ],
    }

    normalize_extraction_evidence(normalized, source)

    assert normalized["memories"][0]["evidence"] == (
        "可以。”他说，“但你必须在一周内完成验证。九月二十日不会等你"
    )


def test_extraction_evidence_expands_multiple_short_source_fragments():
    source = (
        "“议长。”她说，“我要求对数据进行独立验证。在验证完成之前，我不会使用风钥。”"
        "裴衡沉默了很久，最后点了点头。"
        "“可以。”他说，“但你必须在一周内完成验证。”"
    )
    evidence = (
        "议长。……我要求对数据进行独立验证。在验证完成之前，我不会使用风钥。"
        "……可以。……但你必须在一周内完成验证。"
    )

    aligned = align_source_evidence(source, evidence)

    assert source_contains_evidence(source, aligned)
    assert "议长。”她" in aligned
    assert "可以。”他" in aligned


def test_extraction_evidence_rejects_multi_fragment_speaker_attribution():
    source = (
        "“移交完成。”裴衡说，签收灯由红转绿。"
        "裴衡把风钥匣推到黎雁面前。"
        "“黎工程师，从现在开始，你就是零号风钥的合法保管人。”"
    )
    evidence = (
        "裴衡说：“移交完成。……黎工程师，从现在开始，你就是零号风钥的合法保管人。”"
    )

    aligned = align_source_evidence(source, evidence)

    assert aligned == evidence
    assert not source_contains_evidence(source, aligned)


@pytest.mark.parametrize(
    "source",
    (
        "裴衡宣布：“九月二十日之后，季风窗口将永久关闭。”大厅里一片寂静。",
        "“九月二十日之后，季风窗口将永久关闭。”裴衡宣布。",
    ),
)
def test_extraction_evidence_strips_attribution_from_long_direct_quote(source):
    evidence = "裴衡说：“九月二十日之后，季风窗口将永久关闭。”"

    aligned = align_source_evidence(source, evidence)

    assert aligned == "九月二十日之后，季风窗口将永久关闭。"
    assert source_contains_evidence(source, aligned)


@pytest.mark.parametrize(
    "source_prefix",
    (
        "裴衡看着王五。王五说：",
        "裴衡问王五，王五说：",
        "裴衡示意王五，王五宣布：",
        "王五说：",
    ),
)
def test_extraction_evidence_rejects_nested_delegated_or_wrong_speaker(
    source_prefix,
):
    quote = "九月二十日之后，季风窗口将永久关闭，所有运输线路也会停止运行。"
    evidence = f"裴衡说：“{quote}”"

    assert align_source_evidence(f"{source_prefix}“{quote}”", evidence) == evidence
    assert not source_contains_evidence(f"{source_prefix}“{quote}”", evidence)


def test_extraction_evidence_does_not_join_different_speakers():
    source = (
        "裴衡说：“季风窗口将在九月二十日永久关闭。”"
        "王五说：“零号风钥必须在今晚交给黎雁保管。”"
    )
    evidence = (
        "裴衡说：“季风窗口将在九月二十日永久关闭……零号风钥必须在今晚交给黎雁保管。”"
    )

    assert align_source_evidence(source, evidence) == evidence
    assert not source_contains_evidence(source, evidence)


def test_extraction_evidence_does_not_strip_attribution_around_false_claims():
    source = (
        "“移交完成。”签收灯由红转绿。"
        "“黎工程师，从现在开始，你就是零号风钥的合法保管人。”"
    )
    invalid_evidence = (
        "裴衡说：“黎工程师，从现在开始，你就是零号风钥的合法保管人。……移交完成。”",
        "裴衡说：“移交完成。……黎工程师，你就是零号风钥的唯一继承人。”",
        "裴衡说：“移交完成。”",
    )

    for evidence in invalid_evidence:
        assert align_source_evidence(source, evidence) == evidence
        assert not source_contains_evidence(source, evidence)


def test_extraction_evidence_rejects_reordered_or_fabricated_claims():
    source = "黎雁明确接收零号风钥并签字。褚蓝随后核对完整维护记录并封存。"
    for evidence in (
        "褚蓝随后核对完整维护记录并封存……黎雁明确接收零号风钥并签字",
        "伪。黎雁明确接收零号风钥并签字。褚蓝随后核对完整维护记录并封存。",
        "虚构。黎雁明确接收零号风钥并签字。褚蓝随后核对完整维护记录并封存。",
        "裴衡销毁零号风钥并删除全部记录",
    ):
        normalized = {"events": [{"evidence": evidence}], "memories": []}
        with pytest.raises(ServiceError, match="正文证据无效"):
            normalize_extraction_evidence(normalized, source)


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
