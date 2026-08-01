from copy import deepcopy

from app.models.story_novel_export import StoryNovelExport
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from tests.integration.story_novel_process_support import persist_confirmed_seed
from tests.integration.story_novel_process_support import process_api as process_api


def test_length_http_contract_and_legacy_generation_warnings(process_api):
    persist_confirmed_seed(process_api)
    profiles = process_api.client.get("/api/v1/novel/length-profiles")
    assert profiles.status_code == 200
    assert [item["profile_id"] for item in profiles.json()["items"]] == [
        "commercial_serial",
        "short_serial",
        "standard_serial",
        "long_chapter",
    ]

    created = process_api.client.post(
        f"/api/v1/stories/business/{process_api.story_business_id}/novel/revisions",
        json={
            "length_profile_id": "standard_serial",
            "chapter_length_overrides": {
                "2": {"min_chars": 3800, "target_chars": 4600, "max_chars": 5200}
            },
        },
    )
    assert created.status_code == 200, created.text
    revision_id = created.json()["business_id"]
    plan = created.json()["generation_plan"]
    assert (plan["chapter_count"], plan["planned_target_chars"]) == (2, 8600)
    assert plan["chapters"][1]["length_source"] == "chapter_override"

    patched = process_api.client.patch(
        f"/api/v1/stories/novel/revisions/{revision_id}/length-spec",
        json={
            "length_profile_id": "custom",
            "custom_length_profile": {
                "min_chars": 1800,
                "target_chars": 2000,
                "max_chars": 2400,
            },
            "chapter_length_overrides": {
                "2": {"min_chars": 2100, "target_chars": 2300, "max_chars": 2500}
            },
            "expected_plan_version": 4,
        },
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["generation_plan"]["version"] == 5
    assert patched.json()["target_words"] == 4300

    generated = process_api.client.post(
        f"/api/v1/stories/novel/revisions/{revision_id}/generate-async",
        json={"target_words": 99999, "chapter_count": 99},
    )
    assert generated.status_code == 200, generated.text
    assert generated.json()["data"]["warnings"] == [
        "prose 已忽略旧字段: target_words, chapter_count"
    ]
    assert process_api.queued[-1]["args"][1] == {
        "operation": "generate_revision",
        "revision_business_id": revision_id,
    }
    stored = process_api.client.get(f"/api/v1/stories/novel/revisions/{revision_id}")
    assert stored.json()["chapter_count"] == 2
    assert stored.json()["target_words"] == 4300
    blocked = process_api.client.patch(
        f"/api/v1/stories/novel/revisions/{revision_id}/length-spec",
        json={"length_profile_id": "short_serial", "expected_plan_version": 5},
    )
    assert blocked.status_code == 409
    assert "正在运行" in blocked.json()["detail"]


def test_two_persisted_revisions_keep_length_plans_and_ledgers_isolated(process_api):
    persist_confirmed_seed(process_api)
    create_path = (
        f"/api/v1/stories/business/{process_api.story_business_id}/novel/revisions"
    )
    first = process_api.client.post(
        create_path, json={"length_profile_id": "short_serial"}
    ).json()
    second = process_api.client.post(
        create_path, json={"length_profile_id": "long_chapter"}
    ).json()
    assert first["business_id"] != second["business_id"]
    assert (first["revision_number"], second["revision_number"]) == (1, 2)

    with process_api.sessions() as db:
        service = StoryNovelRevisionService(db, process_api.current_user)
        first_row = service.revision(first["business_id"])
        second_row = service.revision(second["business_id"])
        service.checkpoint_chapter(
            first_row,
            position=1,
            title="短版第一章",
            content_text="短" * 2000,
            summary="短版",
            cliffhanger=None,
        )
        service.checkpoint_chapter(
            second_row,
            position=1,
            title="长版第一章",
            content_text="长" * 6000,
            summary="长版",
            cliffhanger=None,
        )
        first_row.continuity_ledger = {
            "schema": "story_novel_continuity.v3",
            "chapters": {
                "1": {
                    "extraction_status": "ready",
                    "event_ids": ["event-short"],
                    "memory_ids": ["memory-short"],
                }
            },
        }
        second_row.continuity_ledger = {
            "schema": "story_novel_continuity.v3",
            "chapters": {
                "1": {
                    "extraction_status": "ready",
                    "event_ids": ["event-long"],
                    "memory_ids": ["memory-long"],
                }
            },
        }
        db.commit()
        second_plan = deepcopy(second_row.generation_plan)
        second_ledger = deepcopy(second_row.continuity_ledger)

    patched = process_api.client.patch(
        f"/api/v1/stories/novel/revisions/{first['business_id']}/length-spec",
        json={
            "length_profile_id": "custom",
            "custom_length_profile": {
                "min_chars": 1800,
                "target_chars": 2000,
                "max_chars": 2400,
            },
            "expected_plan_version": 4,
        },
    )
    assert patched.status_code == 200, patched.text

    with process_api.sessions() as db:
        rows = {
            row.business_id: row
            for row in db.query(StoryNovelExport)
            .filter(StoryNovelExport.story_id == process_api.story_id)
            .all()
        }
        first_row = rows[first["business_id"]]
        second_row = rows[second["business_id"]]
        assert first_row.generation_plan["version"] == 5
        assert first_row.continuity_ledger["chapters"]["1"]["event_ids"] == [
            "event-short"
        ]
        assert second_row.generation_plan == second_plan
        assert second_row.continuity_ledger == second_ledger
