import pytest


@pytest.mark.unit
def test_task_update_returns_serialized_parameters(client):
    # Create a task with parameters as dict
    create_payload = {
        "title": "Test Task",
        "description": "desc",
        "task_type": "image_generation",
        "prompt": "hello",
        "parameters": {"platform": "gpt", "size": 2},
    }
    r = client.post("/api/v1/tasks/", json=create_payload)
    assert r.status_code == 200, r.text
    data = r.json()
    task_id = data["id"]
    assert isinstance(data.get("parameters"), dict)
    assert data["parameters"].get("platform") == "gpt"

    # Update parameters
    update_payload = {
        "parameters": {"platform": "keling", "size": 4}
    }
    r2 = client.put(f"/api/v1/tasks/{task_id}", json=update_payload)
    assert r2.status_code == 200, r2.text
    updated = r2.json()
    # Ensure parameters is a dict (serialized by API) not a JSON string
    assert isinstance(updated.get("parameters"), dict)
    assert updated["parameters"].get("platform") == "keling"


@pytest.mark.unit
def test_task_list_sorted_desc_and_progress_detail(client):
    payload = {
        "title": "Task A",
        "description": "desc a",
        "task_type": "image_generation",
        "prompt": "p1",
    }
    r1 = client.post("/api/v1/tasks/", json=payload)
    assert r1.status_code == 200, r1.text
    payload["title"] = "Task B"
    r2 = client.post("/api/v1/tasks/", json=payload)
    assert r2.status_code == 200, r2.text

    rlist = client.get("/api/v1/tasks?limit=2&skip=0")
    assert rlist.status_code == 200, rlist.text
    data = rlist.json()
    ids = [t["id"] for t in data["tasks"]]
    assert ids == sorted(ids, reverse=True)
    assert "progress_detail" in data["tasks"][0]
