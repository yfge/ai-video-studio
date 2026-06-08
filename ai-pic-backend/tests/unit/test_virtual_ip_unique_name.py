from uuid import uuid4


def test_create_virtual_ip_duplicate_name_returns_400(client):
    name = f"dup-vip-{uuid4().hex}"
    payload = {
        "name": name,
        "description": "first",
        "tags": [],
        "background_story": "",
        "biography": "",
    }

    first = client.post("/api/v1/virtual-ips/", json=payload)
    assert first.status_code == 200

    second = client.post("/api/v1/virtual-ips/", json=payload)
    assert second.status_code == 400
    assert second.json().get("detail") == "虚拟IP名称已存在"


def test_update_virtual_ip_duplicate_name_returns_400(client):
    name_a = f"vip-a-{uuid4().hex}"
    name_b = f"vip-b-{uuid4().hex}"

    res_a = client.post("/api/v1/virtual-ips/", json={"name": name_a})
    assert res_a.status_code == 200

    res_b = client.post("/api/v1/virtual-ips/", json={"name": name_b})
    assert res_b.status_code == 200
    vip_b_id = res_b.json()["data"]["id"]

    update_res = client.put(f"/api/v1/virtual-ips/{vip_b_id}", json={"name": name_a})
    assert update_res.status_code == 400
    assert update_res.json().get("detail") == "虚拟IP名称已存在"


def test_create_virtual_ip_same_name_after_soft_delete_succeeds(client):
    name = f"softdel-vip-{uuid4().hex}"
    payload = {
        "name": name,
        "description": "first",
        "tags": [],
        "background_story": "",
        "biography": "",
    }

    first = client.post("/api/v1/virtual-ips/", json=payload)
    assert first.status_code == 200
    vip_id = first.json()["data"]["id"]

    delete_res = client.delete(f"/api/v1/virtual-ips/{vip_id}")
    assert delete_res.status_code == 200

    second = client.post("/api/v1/virtual-ips/", json=payload)
    assert second.status_code == 200
