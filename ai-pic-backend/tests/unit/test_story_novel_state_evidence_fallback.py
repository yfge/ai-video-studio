from app.services.narrative_memory.source_evidence import source_contains_evidence
from app.services.story.story_novel_state_evidence_repair import (
    _apply_diagnostic_fallbacks,
)


def test_repair_drops_unfixed_middle_rewrite_between_exact_fragments():
    first = "他取出三根钛合金潮位标尺。"
    middle = "他拿起手持冲击钻，对着第一个定位点打孔。"
    last = "第三根标尺锁紧后，拓扑图上亮起闭环。"
    body = first + middle + last
    patch = {
        "evidence": {
            "event-2-1": (
                f"{first}……王明拿起手持冲击钻，对着第一个定位点打孔。……{last}"
            )
        }
    }
    diagnostics = [
        {
            "field": "evidence",
            "id": "event-2-1",
            "fragments": [
                {"text": first, "exact_offsets": [0]},
                {
                    "text": "王明拿起手持冲击钻，对着第一个定位点打孔。",
                    "exact_offsets": [],
                },
                {"text": last, "exact_offsets": [len(first + middle)]},
            ],
        }
    ]

    _apply_diagnostic_fallbacks(patch, diagnostics, body)

    aligned = patch["evidence"]["event-2-1"]
    assert aligned == f"{first}……{last}"
    assert source_contains_evidence(body, aligned)
