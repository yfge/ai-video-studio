from types import SimpleNamespace


def anchor():
    return SimpleNamespace(
        business_id="anchor-a",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="chapter-a",
        source_version=1,
        source_hash="source-hash",
    )


def characters():
    return [
        {
            "character_business_id": "li-yan",
            "virtual_ip_business_id": "vip-li-yan",
            "name": "黎雁",
        },
        {
            "character_business_id": "cen-ye",
            "virtual_ip_business_id": "vip-cen-ye",
            "name": "岑野",
        },
    ]


def memory_bindings():
    return {
        "li-yan": {
            "typed_character_id": "canon-li-yan",
            "names": ["黎雁"],
            "grants": [
                {
                    "character_id": "canon-li-yan",
                    "fact_id": "fact-key-received",
                    "source_event_id": "event-current",
                }
            ],
        }
    }


def event_evidence():
    return {"event-current": "黎雁确认零号风钥移交完成"}


def normalized():
    return {
        "events": [
            {
                "event_type": "action",
                "summary": "岑野第48章死亡",
                "typed_event_ids": ["event-current"],
                "participant_character_ids": ["li-yan", "cen-ye"],
                "occurred_at_anchor_business_id": "anchor-a",
                "presentation": "withheld",
                "audience_disclosure": "hidden",
                "evidence": "黎雁确认零号风钥移交完成",
            }
        ],
        "memories": [
            {
                "character_business_id": "li-yan",
                "virtual_ip_business_id": "vip-li-yan",
                "typed_character_id": "canon-li-yan",
                "typed_fact_id": "fact-key-received",
                "typed_source_event_id": "event-current",
                "memory_type": "witnessed",
                "content": "岑野第48章死亡",
                "belief": "未来已确定",
                "belief_confidence": 1.0,
                "perception": "未来画面",
                "emotional_impact": ["恐惧"],
                "salience": 0.8,
                "occurred_at_anchor_business_id": "anchor-a",
                "learned_at_anchor_business_id": "anchor-a",
                "effective_from_anchor_business_id": "anchor-a",
                "invalidated_at_anchor_business_id": None,
                "growth_delta": {"future": True},
                "evidence": "黎雁确认零号风钥移交完成",
            }
        ],
    }
