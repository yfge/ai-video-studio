import json

from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    content_hash,
    normalize_canon,
)
from app.services.story.story_novel_continuity_contract import (
    continuity_prompt,
    normalize_continuity_report,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_state_service import (
    apply_state_delta,
    initial_story_state,
    quality_metrics,
    state_hash,
)
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup

HARD_METRICS = {
    "canon_violation_count",
    "state_reversion_count",
    "duplicate_milestone_count",
    "illegal_knowledge_count",
    "unexplained_location_transition_count",
    "hard_constraint_truncation_count",
    "overdue_open_thread_count",
}


def _delta(event_id: str) -> dict:
    return {
        "occurred_event_ids": [event_id],
        "state_transitions": [],
        "knowledge_grants": [],
        "location_transitions": [],
        "milestones_consumed": [],
        "opened_thread_ids": [],
        "resolved_thread_ids": [],
        "world_rule_violations": [],
        "evidence": {event_id: "正文证据"},
    }


def _ready_v2_revision(db_session):
    user, _story, service, revision, _task, *_ = _setup(db_session)
    canon = normalize_canon(_canon())
    plan_row = _plan_row()
    snapshot = dict(revision.story_snapshot or {})
    story_seed = dict(snapshot.get("story_seed") or {})
    story_seed["structured_outline"] = {}
    snapshot["story_seed"] = story_seed
    revision.story_snapshot = snapshot
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 2,
        "status": "ready",
        "phase": "ready",
        "story_seed_version": int(snapshot.get("story_seed_version") or 0),
        "outline_hash": content_hash({}),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "chapter_count": 1,
        "target_chars": 3000,
        "chapters": [plan_row],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.chapter_count = 1
    chapter = service.checkpoint_chapter(
        revision,
        position=1,
        title="第一章",
        content_text="正文" * 1500,
        summary="主角发现裂缝",
        cliffhanger=None,
    )
    state_before = initial_story_state(canon)
    delta = _delta("event-1")
    state_after = apply_state_delta(state_before, delta)
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v3",
        "state_status": "ready",
        "current_state": state_after,
        "chapters": {
            "1": {
                "status": "ready",
                "body_hash": chapter.content_hash,
                "source_hash": novel_chapter_source_hash(chapter),
                "extraction_status": "ready",
                "canon_hash": canon["canon_hash"],
                "state_before_hash": state_hash(state_before),
                "state_after_hash": state_hash(state_after),
                "state_delta": delta,
                "state_validation": {"status": "passed", "violations": []},
                "event_ids": [],
                "memory_ids": [],
            }
        },
    }
    report = {
        "schema": "story_novel_continuity_review.v3",
        "summary": "通过",
        "coverage": [
            {
                "business_id": chapter.business_id,
                "content_hash": chapter.content_hash,
                "position": 1,
            }
        ],
        "window_reports": [],
        "issues": [],
        "hard_metrics": quality_metrics(revision),
        "quality_scores": {},
        "repair_groups": [],
        "canon_hash": canon["canon_hash"],
        "status": "passed",
        "plan_version": plan["version"],
        "plan_hash": plan["plan_hash"],
    }
    report["report_hash"] = content_hash(report)
    revision.continuity_report = report
    revision.continuity_status = "passed"
    db_session.commit()
    return user, service, revision, chapter, canon


def test_v3_editorial_output_normalizes_independent_overall_score():
    report = normalize_continuity_report(
        json.dumps(
            {
                "summary": "需要修复",
                "issues": [
                    {
                        "id": "issue-1",
                        "severity": "blocking",
                        "chapter_business_ids": ["chapter-2"],
                        "message": "时间冲突",
                    }
                ],
                "overall_score": 123,
                "quality_scores": {
                    "structure": {"score": 12, "rationale": "结构完整"},
                    "character": {"score": -3, "rationale": "人物偏弱"},
                    "prose": {"score": "7.5", "rationale": "语言顺畅"},
                    "total": {"score": 99, "rationale": "不得采纳"},
                },
                "major_strengths": ["主题鲜明", ""],
                "blocking_issues": ["时间冲突"],
                "revision_priorities": [
                    {"priority": "P0", "items": ["统一时间线"]},
                    {"priority": "", "items": ["无效项"]},
                ],
                "repair_groups": [
                    {
                        "id": "timeline-fix",
                        "title": "统一日期",
                        "issue_ids": ["issue-1"],
                        "canon_target": {
                            "section": "timeline",
                            "item_id": "time-1",
                            "field": "story_time",
                        },
                        "suggested_value": "第一日",
                        "affected_chapter_business_ids": ["chapter-2"],
                        "earliest_position": 2,
                    },
                    {
                        "id": "unknown-fix",
                        "issue_ids": ["issue-1"],
                        "canon_target": {
                            "section": "invented_section",
                            "item_id": "x",
                            "field": "value",
                        },
                    },
                ],
            },
            ensure_ascii=False,
        ),
        "global",
        include_editorial=True,
    )

    assert report["issues"][0]["id"] == "global-issue-1"
    assert report["overall_score"] == 100.0
    assert report["quality_scores"] == {
        "structure": {"score": 10.0, "rationale": "结构完整"},
        "character": {"score": 0.0, "rationale": "人物偏弱"},
        "prose": {"score": 7.5, "rationale": "语言顺畅"},
    }
    assert report["major_strengths"] == ["主题鲜明"]
    assert report["blocking_issues"] == ["时间冲突"]
    assert report["revision_priorities"] == [
        {"priority": "P0", "items": ["统一时间线"]}
    ]
    assert report["repair_groups"] == [
        {
            "id": "global-repair-timeline-fix",
            "title": "统一日期",
            "issue_ids": ["global-issue-1"],
            "canon_target": {
                "section": "timeline",
                "item_id": "time-1",
                "field": "story_time",
            },
            "suggested_value": "第一日",
            "affected_chapter_business_ids": ["chapter-2"],
            "earliest_position": 2,
        }
    ]


def test_editorial_normalizer_keeps_legacy_model_output_readable():
    report = normalize_continuity_report(
        '{"summary":"旧格式","issues":[]}',
        "global",
        include_editorial=True,
    )

    assert report["overall_score"] is None
    assert report["quality_scores"] == {}
    assert report["major_strengths"] == []
    assert report["blocking_issues"] == []
    assert report["revision_priorities"] == []


def test_global_prompt_records_acceptance_thresholds_without_auto_approval():
    prompt = continuity_prompt(
        "全局检查",
        {"chapters": []},
        issue_limit=40,
        include_editorial=True,
    )

    assert "overall_score >= 75" in prompt
    assert "structure、\ncharacter、world 均 >= 7" in prompt
    assert "blocking_issues 为空" in prompt
    assert "不得由分项分数加权或平均计算" in prompt
    assert "不得据此\n输出审批结论或自动批准" in prompt
