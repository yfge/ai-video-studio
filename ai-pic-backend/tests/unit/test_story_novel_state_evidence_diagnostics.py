from app.services.story.story_novel_state_extraction import (
    _evidence_repair_diagnostics,
    _only_evidence_issues,
)


def test_evidence_diagnostics_report_every_fragment_offset_and_first_mismatch():
    exact_quote = (
        "“我，褚蓝，澄砂港路线调度员，现依水议会第417号决议，"
        "将零号风钥移交予旱海路线工程师黎雁。”"
    )
    missing = "褚蓝双手捧着金属盒，递到黎雁面前"
    body = f"2174年8月3日，交接开始。{exact_quote}见证人复诵：{exact_quote}"
    delta = {
        "evidence": {"event-1": f"{missing}……{exact_quote}"},
        "timeline_evidence": {"time-1": f"2174年8月3日……{missing}……{exact_quote}"},
    }
    issues = [
        {"message": "事件缺少可核对的正文证据: event-1"},
        {"message": "时间线缺少正文证据: time-1"},
    ]

    diagnostics = _evidence_repair_diagnostics(body, delta, issues)

    event, timeline = diagnostics
    expected_offsets = [body.index(exact_quote), body.rindex(exact_quote)]
    assert event["failure_kind"] == timeline["failure_kind"] == "quote_rewrite"
    assert event["fragments"] == [
        {"text": missing, "exact_offsets": []},
        {"text": exact_quote, "exact_offsets": expected_offsets},
    ]
    assert event["first_mismatch"] == {"fragment_index": 0, "text": missing}
    assert timeline["fragments"][0]["exact_offsets"] == [0]
    assert timeline["fragments"][1:] == event["fragments"]


def test_evidence_diagnostics_do_not_claim_an_unmatched_event_is_in_the_body():
    diagnostics = _evidence_repair_diagnostics(
        "2174年8月3日，现场只有空盒。",
        {"evidence": {"event-1": "褚蓝完成风钥移交"}},
        [{"message": "事件缺少可核对的正文证据: event-1"}],
    )

    assert diagnostics[0]["failure_kind"] == "body_event_unverified"
    assert diagnostics[0]["first_mismatch"] == {
        "fragment_index": 0,
        "text": "褚蓝完成风钥移交",
    }


def test_evidence_diagnostics_offer_exact_body_quote_without_fabricated_speaker():
    quote = "“2月22日，极夜潮汐合拢后，北辰群岛航路将永久封闭。”"
    body = f"陆峤开口：{quote}"
    diagnostics = _evidence_repair_diagnostics(
        body,
        {"evidence": {"event-1": f"陆峤说：{quote}"}},
        [{"message": "事件缺少可核对的正文证据: event-1"}],
    )

    candidate = diagnostics[0]["fragments"][0]["source_candidate"]
    offset, text = candidate["exact_offset"], candidate["text"]
    assert body[offset : offset + len(text)] == text
    assert quote.strip("“”") == text
    assert "陆峤说" not in text


def test_evidence_diagnostics_do_not_reassign_another_speakers_quote():
    quote = "“2月22日，极夜潮汐合拢后，北辰群岛航路将永久封闭。”"
    body = f"闻鹿看完三名见证者，然后开口：{quote}"
    diagnostics = _evidence_repair_diagnostics(
        body,
        {"evidence": {"event-1": f"陆峤说：{quote}"}},
        [{"message": "事件缺少可核对的正文证据: event-1"}],
    )

    assert "source_candidate" not in diagnostics[0]["fragments"][0]


def test_evidence_diagnostics_offer_unique_exact_suffix_for_rewritten_lead():
    exact = "把一根标尺用力插在陡坎边缘的裂缝里"
    body = f"老拐直起身，{exact}，确认锚定牢固。"
    diagnostics = _evidence_repair_diagnostics(
        body,
        {"evidence": {"event-2": f"将一根标尺用力插在陡坎边缘的裂缝里"}},
        [{"message": "事件缺少可核对的正文证据: event-2"}],
    )

    candidate = diagnostics[0]["fragments"][0]["source_candidate"]
    assert candidate == {
        "text": "一根标尺用力插在陡坎边缘的裂缝里",
        "exact_offset": body.index("一根标尺"),
    }


def test_evidence_diagnostics_bind_rewritten_action_to_same_sentence_actor():
    body = (
        "老拐把液压锁扣卡进锚栓，确认不松动，然后直起腰，"
        "从工装内袋里掏出终端，划开屏幕递到王明眼前。"
    )
    diagnostics = _evidence_repair_diagnostics(
        body,
        {"evidence": {"event-2": "老拐从工装内袋里掏出终端，划开屏幕递到王明眼前。"}},
        [{"message": "事件缺少可核对的正文证据: event-2"}],
    )

    candidate = diagnostics[0]["fragments"][0]["source_candidate"]
    assert candidate["text"] == "从工装内袋里掏出终端，划开屏幕递到王明眼前。"
    assert body[candidate["exact_offset"] :].startswith(candidate["text"])


def test_evidence_diagnostics_do_not_strip_a_wrong_action_actor():
    body = "王五检查完锚栓，然后拿起终端，划开屏幕递到王明眼前。"
    diagnostics = _evidence_repair_diagnostics(
        body,
        {"evidence": {"event-2": "老拐拿起终端，划开屏幕递到王明眼前。"}},
        [{"message": "事件缺少可核对的正文证据: event-2"}],
    )

    assert "source_candidate" not in diagnostics[0]["fragments"][0]


def test_only_source_evidence_errors_skip_body_repair():
    assert _only_evidence_issues(
        [
            {"message": "事件缺少可核对的正文证据: event-1"},
            {"message": "时间线证据未对应绑定事件: time-1"},
        ]
    )
    assert not _only_evidence_issues(
        [{"message": "正文缺少固定日期 2174年8月3日: time-1"}]
    )
