from __future__ import annotations

from app.core.middleware import get_current_active_user
from app.main import app
from app.models.user import User
from tests.integration.test_production_canvas_candidate_review_api import (
    _create_script,
    _review_state,
)


def _user(db, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _as(user: User) -> None:
    app.dependency_overrides[get_current_active_user] = lambda: user


def test_canvas_collaboration_roles_comments_and_activity(client, db_session):
    owner = db_session.query(User).filter(User.username == "test_admin").one()
    collaborators = {
        role: _user(db_session, f"canvas_{role}")
        for role in ("viewer", "commenter", "editor", "approver")
    }
    outsider = _user(db_session, "canvas_outsider")

    _as(owner)
    created = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "验证画布协作权限"},
    )
    assert created.status_code == 200
    run_id = created.json()["data"]["run_id"]
    state = {
        "graph_version": 2,
        "nodes": [],
        "edges": [],
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }
    assert (
        client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state).json()[
            "data"
        ]["access_role"]
        == "owner"
    )

    for role, user in collaborators.items():
        response = client.put(
            f"/api/v1/production-canvas/runs/{run_id}/collaborators",
            json={"username": user.username, "role": role},
        )
        assert response.status_code == 200

    for role, user in collaborators.items():
        _as(user)
        response = client.get(f"/api/v1/production-canvas/runs/{run_id}")
        assert response.status_code == 200
        assert response.json()["data"]["access_role"] == role

    _as(collaborators["viewer"])
    denied_comment = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/comments",
        json={"target_type": "node", "target_id": "brief", "body": "只读意见"},
    )
    assert denied_comment.status_code == 403
    denied_execute = client.post(
        "/api/v1/production-canvas/execute",
        json={
            "prompt": "只读用户不能执行",
            "skill": "brief.compose",
            "run_id": run_id,
            "node_id": "brief",
        },
    )
    assert denied_execute.status_code == 403

    _as(collaborators["commenter"])
    added_comment = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/comments",
        json={"target_type": "node", "target_id": " brief ", "body": " 保留镜头 "},
    )
    assert added_comment.status_code == 200
    assert added_comment.json()["data"]["comments"][0]["body"] == "保留镜头"
    assert (
        client.put(
            f"/api/v1/production-canvas/runs/{run_id}/state", json=state
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"/api/v1/production-canvas/runs/{run_id}/collaborators",
            json={"username": outsider.username, "role": "viewer"},
        ).status_code
        == 403
    )

    _as(collaborators["editor"])
    edited = client.put(f"/api/v1/production-canvas/runs/{run_id}/state", json=state)
    assert edited.status_code == 200
    assert edited.json()["data"]["access_role"] == "editor"

    _as(collaborators["approver"])
    assert (
        client.put(
            f"/api/v1/production-canvas/runs/{run_id}/state", json=state
        ).status_code
        == 403
    )

    collaboration = client.get(f"/api/v1/production-canvas/runs/{run_id}/collaboration")
    assert collaboration.status_code == 200
    data = collaboration.json()["data"]
    assert data["access_role"] == "approver"
    assert len(data["collaborators"]) == 4
    assert data["comments"][0]["target_id"] == "brief"
    assert [item["action"] for item in data["activity"]].count(
        "collaborator.updated"
    ) == 4
    assert data["activity"][-1]["action"] == "comment.added"

    _as(outsider)
    assert client.get(f"/api/v1/production-canvas/runs/{run_id}").status_code == 404
    assert (
        client.get(f"/api/v1/production-canvas/runs/{run_id}/collaboration").status_code
        == 403
    )


def test_canvas_collaboration_rejects_blank_text(client, db_session):
    owner = db_session.query(User).filter(User.username == "test_admin").one()
    _as(owner)
    run_id = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "验证画布协作输入"},
    ).json()["data"]["run_id"]

    collaborator = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/collaborators",
        json={"username": "   ", "role": "viewer"},
    )
    comment = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/comments",
        json={"target_type": "node", "target_id": "brief", "body": "   "},
    )

    assert collaborator.status_code == 422
    assert comment.status_code == 422


def test_canvas_approver_reviews_owner_candidates(client, db_session):
    owner = db_session.query(User).filter(User.username == "test_admin").one()
    approver = _user(db_session, "canvas_shared_approver")
    script = _create_script(db_session, owner)

    _as(owner)
    run_id = client.post(
        "/api/v1/production-canvas/plan",
        json={"prompt": "共享候选审批", "script_id": script.id},
    ).json()["data"]["run_id"]
    saved = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/state",
        json=_review_state(script.id),
    )
    assert saved.status_code == 200
    shared = client.put(
        f"/api/v1/production-canvas/runs/{run_id}/collaborators",
        json={"username": approver.username, "role": "approver"},
    )
    assert shared.status_code == 200

    _as(approver)
    listed = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/candidates"
    )
    assert listed.status_code == 200
    candidate_id = listed.json()["data"]["candidates"][0]["asset_id"]
    approved = client.post(
        f"/api/v1/production-canvas/runs/{run_id}/nodes/image-review/approval",
        json={"candidate_id": candidate_id},
    )

    assert approved.status_code == 200
    assert approved.json()["data"]["access_role"] == "approver"
    image = next(
        node
        for node in approved.json()["data"]["saved_state"]["nodes"]
        if node["id"] == "image-review"
    )
    assert image["selected_output_id"] == candidate_id
    assert image["selected_output_reviewed_by"] == approver.id
    collaboration = client.get(
        f"/api/v1/production-canvas/runs/{run_id}/collaboration"
    ).json()["data"]
    assert collaboration["activity"][-1]["action"] == "candidate.approved"
    assert collaboration["activity"][-1]["actor_id"] == approver.id
