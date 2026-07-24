import json
from copy import deepcopy

from app.models.script import Story
from app.models.task import Task, TaskStatus
from app.services.story import story_novel_task_processor as processor
from tests.integration.story_novel_process_support import outline
from tests.integration.story_novel_process_support import process_api as process_api


def test_structure_worker_persists_draft_then_confirmation_freezes_revision_snapshot(
    process_api, monkeypatch
):
    client = process_api.client
    structure = client.post(
        f"/api/v1/stories/business/{process_api.story_business_id}"
        "/story-seed/structure-async"
    )
    assert structure.status_code == 200, structure.text
    task_id = structure.json()["data"]["task_id"]
    assert process_api.queued[0]["name"] == "tasks.story_novel_generate"

    blocked = client.put(
        f"/api/v1/stories/business/{process_api.story_business_id}/story-seed",
        json={
            "outline_text": "第1章至第2章",
            "structured_outline": outline("draft"),
            "story_seed_status": "draft",
            "story_seed_version": 1,
        },
    )
    assert blocked.status_code == 409
    assert str(task_id) in blocked.json()["detail"]
    create_blocked = client.post(
        f"/api/v1/stories/business/{process_api.story_business_id}/novel/revisions",
        json={"length_profile_id": "standard_serial"},
    )
    assert create_blocked.status_code == 409

    async def fixed_structure(_carrier, _prompt, **_kwargs):
        return json.dumps(
            {"structured_outline": outline("draft")},
            ensure_ascii=False,
        )

    monkeypatch.setattr(processor, "SessionLocal", process_api.sessions)
    monkeypatch.setattr(processor, "_generate_text", fixed_structure)
    processor.process_story_novel_task(
        task_id,
        process_api.queued[0]["args"][1],
        process_api.user_id,
    )
    with process_api.sessions() as db:
        story = db.get(Story, process_api.story_id)
        task = db.get(Task, task_id)
        assert task.status == TaskStatus.COMPLETED, task.error_message
        assert story.story_seed_status == "draft"
        assert story.story_seed_version == 2
        assert story.story_seed["structured_outline"]["status"] == "draft"

    confirmed = client.put(
        f"/api/v1/stories/business/{process_api.story_business_id}/story-seed",
        json={
            "outline_text": "第1章至第2章",
            "structured_outline": outline("confirmed"),
            "story_seed_status": "confirmed",
            "story_seed_version": 2,
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["story_seed_version"] == 3
    assert confirmed.json()["story_seed"]["structured_outline"]["status"] == "frozen"

    created = client.post(
        f"/api/v1/stories/business/{process_api.story_business_id}/novel/revisions",
        json={"length_profile_id": "standard_serial"},
    )
    assert created.status_code == 200, created.text
    revision_id = created.json()["business_id"]
    frozen_snapshot = deepcopy(created.json()["story_snapshot"])
    assert frozen_snapshot["story_seed"]["structured_outline"]["status"] == "frozen"

    changed_outline = outline("confirmed", version=2)
    changed_outline["chapters"][0]["goal"] = "用户后来修改的目标"
    changed = client.put(
        f"/api/v1/stories/business/{process_api.story_business_id}/story-seed",
        json={
            "outline_text": "第1章至第2章（已修改）",
            "structured_outline": changed_outline,
            "story_seed_status": "confirmed",
            "story_seed_version": 3,
        },
    )
    assert changed.status_code == 200, changed.text
    stored = client.get(f"/api/v1/stories/novel/revisions/{revision_id}")
    assert stored.status_code == 200
    assert stored.json()["story_snapshot"] == frozen_snapshot
