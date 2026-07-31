import json

from sqlalchemy import select

from app.models.story_novel_export import StoryNovelExport
from app.models.task import Task
from tests.integration.story_novel_process_support import persist_confirmed_seed
from tests.integration.story_novel_process_support import process_api as process_api


def test_continuity_request_queues_review_model_without_changing_revision(process_api):
    persist_confirmed_seed(process_api)
    created = process_api.client.post(
        f"/api/v1/stories/business/{process_api.story_business_id}/novel/revisions",
        json={
            "length_profile_id": "standard_serial",
            "model_policy": {
                "planning_model": "deepseek:plan",
                "prose_model": "deepseek:prose",
                "audit_model": "deepseek:audit",
            },
            "model": "deepseek:prose",
        },
    ).json()

    queued = process_api.client.post(
        "/api/v1/stories/novel/revisions/"
        f"{created['business_id']}/continuity-check-async",
        json={"review_model": " codex:gpt-5.6-sol "},
    )

    assert queued.status_code == 200, queued.text
    payload = process_api.queued[-1]["args"][1]
    assert payload["review_model"] == "codex:gpt-5.6-sol"
    with process_api.sessions() as db:
        revision = db.scalar(
            select(StoryNovelExport).where(
                StoryNovelExport.business_id == created["business_id"]
            )
        )
        task = db.get(Task, queued.json()["data"]["task_id"])
        assert revision.generation_plan["model_policy"]["audit_model"] == (
            "deepseek:audit"
        )
        assert json.loads(task.parameters)["review_model"] == "codex:gpt-5.6-sol"
