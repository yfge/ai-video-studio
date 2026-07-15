from __future__ import annotations

import copy

from app.services.storyboard.storyboard_image_autogen import (
    queue_storyboard_image_generation,
)
from tests.factories import ScriptFactory, UserFactory, setup_factories


def test_storyboard_image_checkpoint_outputs_do_not_change_active_request(
    db_session,
    monkeypatch,
) -> None:
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "frame_id": "frame-1",
                        "description": "Environment insert",
                        "characters": [],
                    }
                ]
            }
        }
    )
    db_session.commit()
    dispatched: list[int] = []
    monkeypatch.setattr(
        "app.services.storyboard.storyboard_image_autogen."
        "storyboard_image_generate_task.delay",
        lambda task_id, _payload, _user_id: dispatched.append(task_id),
    )
    first = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
    )
    metadata = copy.deepcopy(script.extra_metadata)
    frame = metadata["storyboard"]["frames"][0]
    frame.update(
        {
            "image_url": "https://example.com/generated.png",
            "start_image_url": "https://example.com/generated.png",
            "start_image_urls": ["https://example.com/generated.png"],
            "image_gen": {"provider": "codex"},
            "storyboard_prompt_v2": {"version": 2},
            "canvas_candidate_lineage": [{"url": frame.get("image_url")}],
        }
    )
    script.extra_metadata = metadata
    db_session.commit()

    repeated = queue_storyboard_image_generation(
        db_session,
        script_id=script.id,
        user_id=user.id,
    )

    assert repeated.status == "reused"
    assert repeated.child_task_id == first.child_task_id
    assert dispatched == [first.child_task_id]
