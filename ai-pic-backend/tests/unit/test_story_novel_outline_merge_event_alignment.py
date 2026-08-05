import pytest
from app.services.story.story_novel_outline_merge import merge_frozen_chapters
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_restores_one_paraphrase_anchored_by_other_exact_events():
    generated = [_plan_row(37)]
    generated[0]["key_events"] = [
        "七月初二，牛车往返北湾共四个时辰运来木料",
        "途中一根主梁开裂，导致仓房建设计划被迫缩小",
    ]
    generated[0]["required_event_ids"] = ["event-37-1", "event-37-2"]
    frozen = {"chapters": [_plan_row(37)]}
    frozen["chapters"][0]["key_events"] = [
        "七月初二，牛车往返北湾共四个时辰运来木料",
        "途中一根主梁开裂，导致仓房规模被迫缩小",
    ]

    merged = merge_frozen_chapters(generated, frozen, _canon(), validate=False)

    assert merged[0]["key_events"] == frozen["chapters"][0]["key_events"]
    assert merged[0]["required_event_ids"] == ["event-37-1", "event-37-2"]


def test_rejects_multiple_paraphrased_events_without_exact_anchor():
    generated = [_plan_row(37)]
    generated[0]["key_events"] = ["木料运抵", "主梁损坏"]
    generated[0]["required_event_ids"] = ["event-37-1", "event-37-2"]
    frozen = {"chapters": [_plan_row(37)]}
    frozen["chapters"][0]["key_events"] = ["牛车运来木料", "主梁开裂"]

    with pytest.raises(ValueError, match="key_events 必须逐字、同序复制"):
        merge_frozen_chapters(generated, frozen, _canon(), validate=False)


@pytest.mark.parametrize(
    "replacement", ["牛车运来木料", "牛车运来木料后另作安排", "牛车运来"]
)
def test_rejects_single_mismatch_that_repeats_another_frozen_event(replacement):
    generated = [_plan_row(37)]
    generated[0]["key_events"] = ["牛车运来木料", replacement]
    generated[0]["required_event_ids"] = ["event-37-1", "event-37-2"]
    frozen = {"chapters": [_plan_row(37)]}
    frozen["chapters"][0]["key_events"] = ["牛车运来木料", "主梁开裂"]

    with pytest.raises(ValueError, match="key_events 必须逐字、同序复制"):
        merge_frozen_chapters(generated, frozen, _canon(), validate=False)
