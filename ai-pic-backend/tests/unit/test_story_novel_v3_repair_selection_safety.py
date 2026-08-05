from app.services.story.story_novel_v3_gate import select_failed_result


def _result(violations, *, future=None, world=None, state_contract_failed=False):
    return {
        "audit": {
            "passed": False,
            "failure_kind": "content",
            "state_contract_failed": state_contract_failed,
            "state_validation": {"status": "failed", "violations": violations},
            "future_audit": {
                "unexpected_claims": [],
                "future_hits": list(future or []),
                "world_rule_hits": list(world or []),
            },
        }
    }


def test_repair_with_fewer_but_different_failures_keeps_first_body():
    first = _result(
        [
            {
                "code": "canon_violation",
                "reason_code": "length_out_of_range",
                "message": "章节长度为 1655，要求 2000–3000",
            },
            {"code": "canon_violation", "message": "计划外人物参与"},
            {"code": "canon_violation", "message": "物件位置冲突"},
        ]
    )
    repaired = _result(
        [{"code": "canon_violation", "message": "遗漏当前事件明示参与者"}]
    )

    assert select_failed_result(first, repaired) is first


def test_repair_cannot_trade_safe_failures_for_new_future_or_world_violation():
    first = _result(
        [
            {
                "code": "canon_violation",
                "reason_code": "length_out_of_range",
                "message": "章节长度不足",
            },
            {"code": "canon_violation", "message": "遗漏当前事件"},
        ]
    )
    future = _result(
        [{"code": "canon_violation", "message": "提前完成未来事件"}],
        future=[{"claim_id": "future-9", "message": "提前完成未来事件"}],
    )
    world = _result(
        [{"code": "canon_violation", "message": "违反世界规则"}],
        world=[{"rule_id": "rule-1", "message": "违反世界规则"}],
    )

    assert select_failed_result(first, future) is first
    assert select_failed_result(first, world) is first


def test_repair_cannot_introduce_typed_state_contract_failure():
    first = _result(
        [
            {
                "code": "canon_violation",
                "reason_code": "length_out_of_range",
                "message": "章节长度不足",
            },
            {"code": "canon_violation", "message": "遗漏当前事件"},
        ]
    )
    repaired = _result(
        [{"code": "illegal_knowledge", "message": "角色提前知情"}],
        state_contract_failed=True,
    )

    assert select_failed_result(first, repaired) is first


def test_repair_cannot_replace_failures_with_a_different_reason_set():
    first = _result(
        [
            {
                "code": "canon_violation",
                "reason_code": "unexpected_claim",
                "message": "计划外人物参与",
            },
            {
                "code": "canon_violation",
                "reason_code": "unexpected_claim",
                "message": "物件位置冲突",
            },
            {
                "code": "canon_violation",
                "reason_code": "length_out_of_range",
                "message": "章节长度不足",
            },
        ]
    )
    repaired = _result(
        [
            {
                "code": "canon_violation",
                "reason_code": "unexpected_claim",
                "message": "遗漏当前事件参与者",
            }
        ]
    )

    assert select_failed_result(first, repaired) is first


def test_repair_is_selected_only_when_violation_keys_are_a_strict_subset():
    retained = {"code": "canon_violation", "message": "遗漏当前事件"}
    first = _result([retained, {"code": "canon_violation", "message": "地点冲突"}])
    repaired = _result([retained])

    assert select_failed_result(first, repaired) is repaired
