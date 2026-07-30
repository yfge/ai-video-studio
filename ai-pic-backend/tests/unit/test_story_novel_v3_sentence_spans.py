import pytest
from app.services.story.story_novel_sentence_spans import (
    audit_sentence_index,
    resolve_sentence_refs,
    sentence_spans,
)


def test_unicode_sentence_ids_offsets_and_source_hash_are_deterministic():
    body = "  苏砚说：‘出发。’\n王明答应！\n潮水退去"
    first = sentence_spans(body)
    second = sentence_spans(body)

    assert first == second
    assert [item["sentence_id"] for item in first] == ["S0001", "S0002", "S0003"]
    for item in first:
        assert body[item["start"] : item["end"]] == item["text"]
        assert item["source_hash"] == first[0]["source_hash"]


def test_sentence_refs_resolve_only_against_current_body_hash():
    body = "苏砚打开盒子。镜核发出蓝光！王明记录结果。"
    source_hash = sentence_spans(body)[0]["source_hash"]
    proof = resolve_sentence_refs(body, ["S0001", "S0003"], source_hash)

    assert proof["sentence_ids"] == ["S0001", "S0003"]
    assert proof["quote"] == "苏砚打开盒子。……王明记录结果。"
    assert proof["sentence_index_hash"]
    with pytest.raises(ValueError, match="source hash 已变化"):
        resolve_sentence_refs(body + "新增。", ["S0001"], source_hash)
    with pytest.raises(ValueError, match="未知 ID"):
        resolve_sentence_refs(body, ["S9999"], source_hash)


def test_audit_sentence_index_excludes_server_only_coordinates_and_hashes():
    rows = sentence_spans("苏砚查看秧苗。顾长庚记下叶色。")

    assert audit_sentence_index(rows) == [
        {"sentence_id": "S0001", "text": "苏砚查看秧苗。"},
        {"sentence_id": "S0002", "text": "顾长庚记下叶色。"},
    ]
