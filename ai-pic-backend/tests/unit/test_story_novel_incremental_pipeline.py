import json

import anyio
from app.services.story import story_novel_planning_invocations
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_incremental_plan import (
    build_chapter_skeletons,
    incremental_plan_fields,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from tests.unit.story_novel_v3_test_support import (
    _planning_evidence,
    persisted_stage_text,
)
from tests.unit.test_story_novel_incremental_planning import _outline_row, _package
from tests.unit.test_story_novel_longform import _canon, _setup


def _blocks(count: int) -> list[dict]:
    passages = [
        "主角开垦第一块薄田。她挥锄翻开板结土层，把草根逐条拣到田埂外。",
        "顾砚沿东渠插下竹签，重新测量高差，再把偏斜的支沟向南修正。",
        "午后风紧，二人用碎石压住新土，试着放入一股细水观察渗漏。",
        "水线绕过低洼处，沈禾立刻截断缺口，并用湿泥补实松动的沟壁。",
        "邻田老人带来旧木耙，三人轮流打散土块，让表土渐渐变得细匀。",
        "日落前最后一畦终于合拢，沈禾记下水位，也留下明早复测的竹标。",
    ]
    return [
        {
            "block_id": f"B{index:02d}",
            "content_text": passages[index - 1] * 13,
        }
        for index in range(1, count + 1)
    ]


def test_incremental_chapter_uses_package_prose_audit_and_ready_resume_is_free(
    db_session,
):
    _user, _story, service, revision, task, *_ = _setup(db_session, with_character=True)
    canon = normalize_canon({**_canon(), "timeline": []})
    skeletons = build_chapter_skeletons(
        canon,
        {"chapters": [_outline_row(1, "主角开垦第一块薄田")]},
        [],
    )
    plan = {
        "schema": "story_novel_generation_plan.v3",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "outline-one",
        "model_policy": {
            "planning_model": "deepseek:planning",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 1,
        "chapters": skeletons,
        "thread_payoffs": [],
    }
    plan.update(incremental_plan_fields(canon, skeletons))
    revision.generation_plan = plan
    story_novel_planning_invocations.record_attempt(
        revision,
        "canon",
        _planning_evidence(
            revision,
            300,
            "canon",
            "story_novel_canon_v3",
            db=db_session,
        ),
        result_hash=canon["canon_hash"],
    )
    plan = dict(revision.generation_plan)
    story_novel_planning_invocations.finalize(plan, canon, skeletons)
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.chapter_count = 1
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v4",
        "state_status": "empty",
        "chapters": {},
    }
    db_session.commit()
    calls = []
    invocation_id = 300

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        nonlocal invocation_id
        invocation_id += 1
        calls.append(stage)
        rendered_template = None
        if stage.startswith("chapter_planning"):
            payload = _package(skeletons[0])
            templates = plan["prompt_templates"]["templates"]
            rendered_template = {
                **templates["story_novel_chapter_package_v3"],
                "rendered_hash": "package-rendered",
                "system_prompt": {
                    **templates["story_novel_system_v3"],
                    "rendered_hash": "system-rendered",
                },
            }
        elif stage.startswith("prose"):
            payload = {"blocks": _blocks(6)}
        else:
            payload = {
                "proofs": [
                    {
                        "contract_id": "event:event-1-1",
                        "sentence_ids": ["S0001"],
                    }
                ],
                "unexpected_claims": [],
                "future_hits": [],
                "world_rule_hits": [],
            }
        return persisted_stage_text(
            db_session,
            revision,
            stage,
            json.dumps(payload, ensure_ascii=False),
            invocation_id,
            rendered_template=rendered_template,
        )

    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        skeletons[0],
        generate,
    )

    assert calls[:2] == ["chapter_planning.1", "prose.1"]
    assert len(calls) == 3
    assert calls[2].startswith("audit.1.")
    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "ready"
    assert entry["extraction_status"] == "ready"
    body_hash = revision.chapters[0].content_hash
    calls.clear()

    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        skeletons[0],
        generate,
    )

    assert calls == []
    assert revision.chapters[0].content_hash == body_hash
