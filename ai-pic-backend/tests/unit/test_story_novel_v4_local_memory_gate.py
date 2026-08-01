from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_revision_local_memory import (
    local_memory_rows_complete,
)


def _entry():
    entry = {
        "chapter_business_id": "chapter-1",
        "source_hash": "source-1",
        "state_after": {"revision_local_entities": {"char-local": {}}},
        "state_delta": {
            "knowledge_grants": [
                {
                    "character_id": "char-local",
                    "fact_id": "fact-1",
                    "source_event_id": "event-1",
                }
            ],
            "knowledge_evidence": {
                "char-local|fact-1|event-1": "闻鹿亲眼看见封锁解除。"
            },
        },
        "revision_local_memories": [
            {
                "business_id": "",
                "character_business_id": "char-local",
                "typed_fact_id": "fact-1",
                "typed_source_event_id": "event-1",
                "source_chapter_business_id": "chapter-1",
                "source_hash": "source-1",
                "revision_local": True,
                "content": "闻鹿亲眼看见封锁解除。",
                "source_quote": "闻鹿亲眼看见封锁解除。",
            }
        ],
    }
    identity = {
        "chapter": "chapter-1",
        "character_id": "char-local",
        "fact_id": "fact-1",
        "source_event_id": "event-1",
        "source_hash": "source-1",
    }
    entry["revision_local_memories"][0][
        "business_id"
    ] = f"revision-memory-{value_hash(identity)[:24]}"
    return entry


def test_revision_local_character_knowledge_requires_exact_memory_row():
    entry = _entry()
    assert local_memory_rows_complete(entry)
    entry["revision_local_memories"] = []
    assert not local_memory_rows_complete(entry)


def test_revision_local_memory_must_match_current_source_hash():
    entry = _entry()
    entry["revision_local_memories"][0]["source_hash"] = "stale"
    assert not local_memory_rows_complete(entry)


def test_revision_local_memory_content_must_match_knowledge_evidence_and_id():
    entry = _entry()
    row = entry["revision_local_memories"][0]
    row["content"] = row["source_quote"] = "伪造内容"
    assert not local_memory_rows_complete(entry)
    entry = _entry()
    entry["revision_local_memories"][0]["business_id"] = "forged"
    assert not local_memory_rows_complete(entry)
