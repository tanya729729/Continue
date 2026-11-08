def test_task_workflow_uses_one_state(api_client):
    baseline_stats = api_client.get("/stats").json()

    control_response = api_client.post(
        "/tasks", json={"title": "Control task", "priority": 1}
    )
    target_response = api_client.post(
        "/tasks", json={"title": "Workflow task", "priority": 2}
    )
    assert control_response.status_code == 201
    assert target_response.status_code == 201
    control = control_response.json()
    target = target_response.json()
    control_id = control["id"]
    target_id = target["id"]
    target_path = f"/tasks/{target_id}"

    assert control_id != target_id
    assert api_client.get("/stats").json() == {
        "total": baseline_stats["total"] + 2,
        "open": baseline_stats["open"] + 2,
        "done": baseline_stats["done"],
    }
    read = api_client.get(target_path)
    assert read.status_code == 200
    assert read.json() == target

    put = api_client.put(
        target_path,
        json={"title": "Reviewed workflow", "priority": 3, "is_done": True},
    )
    assert put.status_code == 200
    completed = put.json()
    assert completed == {
        "id": target_id,
        "title": "Reviewed workflow",
        "priority": 3,
        "is_done": True,
    }
    assert api_client.get(target_path).json() == completed
    assert api_client.get(f"/tasks/{control_id}").json() == control
    assert api_client.get("/stats").json() == {
        "total": baseline_stats["total"] + 2,
        "open": baseline_stats["open"] + 1,
        "done": baseline_stats["done"] + 1,
    }

    before_invalid_tasks = api_client.get("/tasks").json()
    before_invalid_stats = api_client.get("/stats").json()
    invalid = api_client.patch(target_path, json={"priority": 99})
    assert invalid.status_code == 422
    assert api_client.get("/tasks").json() == before_invalid_tasks
    assert api_client.get("/stats").json() == before_invalid_stats
    assert api_client.get(target_path).json() == completed
    assert api_client.get(f"/tasks/{control_id}").json() == control

    reopened = api_client.patch(target_path, json={"is_done": False})
    assert reopened.status_code == 200
    assert reopened.json() == {
        "id": target_id,
        "title": "Reviewed workflow",
        "priority": 3,
        "is_done": False,
    }
    assert api_client.get(target_path).json() == reopened.json()
    assert api_client.get("/stats").json() == {
        "total": baseline_stats["total"] + 2,
        "open": baseline_stats["open"] + 2,
        "done": baseline_stats["done"],
    }

    deleted = api_client.delete(target_path)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert api_client.get(target_path).status_code == 404
    assert api_client.get(f"/tasks/{control_id}").json() == control
    assert api_client.get("/stats").json() == {
        "total": baseline_stats["total"] + 1,
        "open": baseline_stats["open"] + 1,
        "done": baseline_stats["done"],
    }