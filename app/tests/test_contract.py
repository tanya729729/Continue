import pytest


def test_put_uses_positive_id(api_client):
    created = api_client.post(
        "/tasks", json={"title": "Before", "priority": 3}
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert task_id > 0

    response = api_client.put(
        f"/tasks/{task_id}",
        json={"title": "After", "priority": 4, "is_done": True},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": task_id,
        "title": "After",
        "priority": 4,
        "is_done": True,
    }

def _error_field(response):
    return response.json()["detail"][0]["loc"][-1]


@pytest.mark.parametrize(
    ("title", "expected_status", "expected_title"),
    [
        ("A", 200, "A"),
        ("A" * 120, 200, "A" * 120),
        ("  " + "A" * 120 + "  ", 200, "A" * 120),
        ("", 422, None),
        ("   ", 422, None),
        ("A" * 121, 422, None),
        (123, 422, None),
    ],
)
def test_put_title_boundaries(
    api_client, title, expected_status, expected_title
):
    created = api_client.post(
        "/tasks", json={"title": "Before", "priority": 3}
    )
    task_id = created.json()["id"]
    response = api_client.put(
        f"/tasks/{task_id}",
        json={"title": title, "priority": 3, "is_done": False},
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["title"] == expected_title
        assert response.json()["id"] == task_id
    else:
        assert _error_field(response) == "title"

@pytest.mark.parametrize(
    ("priority", "expected_status"),
    [
        (1, 200),
        (5, 200),
        (0, 422),
        (6, 422),
        ("high", 422),
    ],
)
def test_put_priority_boundaries(
    api_client, priority, expected_status
):
    created = api_client.post(
        "/tasks", json={"title": "Before", "priority": 3}
    )
    task_id = created.json()["id"]
    response = api_client.put(
        f"/tasks/{task_id}",
        json={
            "title": "Valid title",
            "priority": priority,
            "is_done": False,
        },
    )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["priority"] == priority
        assert response.json()["id"] == task_id
    else:
        assert _error_field(response) == "priority"


@pytest.mark.parametrize(
    "path_value",
    ["not-an-integer", 0, -1],
)
def test_get_rejects_invalid_task_id(api_client, path_value):
    created = api_client.post(
        "/tasks", json={"title": "Before", "priority": 3}
    )
    task_id = created.json()["id"]
    assert task_id > 0
    assert api_client.get(f"/tasks/{task_id}").status_code == 200
    response = api_client.get(f"/tasks/{path_value}")

    assert response.status_code == 422
    assert _error_field(response) == "task_id"


def test_get_returns_404_for_missing_positive_id(api_client):
    created = api_client.post(
        "/tasks", json={"title": "Before", "priority": 3}
    )
    task_id = created.json()["id"]
    missing_id = task_id + 1
    response = api_client.get(f"/tasks/{missing_id}")

    assert missing_id > 0
    assert response.status_code == 404


def _create_contract_pair(api_client):
    target_response = api_client.post(
        "/tasks", json={"title": "Целевая", "priority": 2}
    )
    control_response = api_client.post(
        "/tasks", json={"title": "Контрольная", "priority": 4}
    )

    assert target_response.status_code == 201
    assert control_response.status_code == 201
    return target_response.json(), control_response.json()


def _contract_state(api_client, target_id, control_id):
    return {
        "target": api_client.get(f"/tasks/{target_id}").json(),
        "control": api_client.get(f"/tasks/{control_id}").json(),
        "stats": api_client.get("/stats").json(),
    }


def test_contract_baseline_captures_both_records(api_client):
    target, control = _create_contract_pair(api_client)
    before = _contract_state(api_client, target["id"], control["id"])

    assert before["target"] == target
    assert before["control"] == control
    assert before["stats"] == {"total": 2, "open": 2, "done": 0}

def test_invalid_writes_preserve_public_state(api_client):
    target, control = _create_contract_pair(api_client)
    target_path = f"/tasks/{target['id']}"
    before = _contract_state(api_client, target["id"], control["id"])

    response = api_client.post(
        "/tasks", json={"title": "   ", "priority": 2}
    )
    assert response.status_code == 422
    assert _error_field(response) == "title"
    assert _contract_state(api_client, target["id"], control["id"]) == before

    response = api_client.put(
        target_path,
        json={"title": "", "priority": 4, "is_done": True},
    )
    assert response.status_code == 422
    assert _error_field(response) == "title"
    assert _contract_state(api_client, target["id"], control["id"]) == before

    response = api_client.patch(target_path, json={"title": " "})
    assert response.status_code == 422
    assert _error_field(response) == "title"
    assert _contract_state(api_client, target["id"], control["id"]) == before

    missing_id = max(target["id"], control["id"]) + 1
    missing_path = f"/tasks/{missing_id}"

    response = api_client.put(
        missing_path,
        json={"title": "Valid title", "priority": 3, "is_done": False},
    )
    assert response.status_code == 404
    assert _contract_state(api_client, target["id"], control["id"]) == before

    response = api_client.patch(missing_path, json={"is_done": False})
    assert response.status_code == 404
    assert _contract_state(api_client, target["id"], control["id"]) == before

    response = api_client.delete(missing_path)
    assert response.status_code == 404
    assert _contract_state(api_client, target["id"], control["id"]) == before

@pytest.mark.parametrize(
    "missing_field",
    ["title", "priority", "is_done"],
)
def test_put_requires_every_editable_field(
    api_client, missing_field
):
    target, control = _create_contract_pair(api_client)
    target_path = f"/tasks/{target['id']}"
    before = _contract_state(api_client, target["id"], control["id"])
    payload = {
        "title": "Обновлённая задача",
        "priority": 1,
        "is_done": True,
    }
    payload.pop(missing_field)

    response = api_client.put(target_path, json=payload)

    assert response.status_code == 422
    assert _error_field(response) == missing_field
    assert _contract_state(api_client, target["id"], control["id"]) == before


@pytest.mark.parametrize("payload", [{}, {"title": None}])
def test_patch_omission_and_null_keep_state(
    api_client, payload
):
    target, control = _create_contract_pair(api_client)
    target_path = f"/tasks/{target['id']}"
    before = _contract_state(api_client, target["id"], control["id"])

    response = api_client.patch(target_path, json=payload)

    assert response.status_code == 200
    assert response.json() == before["target"]
    assert _contract_state(api_client, target["id"], control["id"]) == before


def test_patch_false_changes_only_done_state(api_client):
    target, control = _create_contract_pair(api_client)
    target_path = f"/tasks/{target['id']}"
    ready = api_client.put(
        target_path,
        json={
            "title": target["title"],
            "priority": target["priority"],
            "is_done": True,
        },
    )
    assert ready.status_code == 200
    before = _contract_state(api_client, target["id"], control["id"])
    assert before["target"]["is_done"] is True

    response = api_client.patch(
        target_path, json={"is_done": False}
    )

    expected_target = {
        "id": target["id"],
        "title": before["target"]["title"],
        "priority": before["target"]["priority"],
        "is_done": False,
    }
    assert response.status_code == 200
    assert response.json() == expected_target
    after = _contract_state(api_client, target["id"], control["id"])
    assert after["target"] == expected_target
    assert after["control"] == before["control"]
    assert after["stats"] == {
        "total": before["stats"]["total"],
        "open": before["stats"]["open"] + 1,
        "done": before["stats"]["done"] - 1,
    }


def test_query_defaults_and_filter_sort_limit_do_not_change_source(
    api_service, api_client
):
    api_service.mark_done(created[-1].id)
    all_ids = [task.id for task in created]
    assert created[-1].id == max(all_ids)
    open_ids = [task.id for task in created[:-1]]
    done_ids = [created[-1].id]

    descending_open = api_client.get(
        "/tasks",
        params={"is_done": False, "sort_desc": True, "limit": 1},
    )
    assert descending_open.status_code == 200
    assert [task["id"] for task in descending_open.json()] == sorted(
        open_ids, reverse=True
    )[:1]

    completed = api_client.get(
        "/tasks",
        params={"is_done": True, "sort_desc": False, "limit": 50},
    )
    assert [task["id"] for task in completed.json()] == done_ids

    default_page = api_client.get("/tasks")
    assert default_page.status_code == 200
    assert [task["id"] for task in default_page.json()] == sorted(all_ids)[:10]

    all_statuses = api_client.get("/tasks", params={"limit": 50})
    assert [task["id"] for task in all_statuses.json()] == sorted(all_ids)

    ascending_open = api_client.get(
        "/tasks",
        params={"is_done": False, "sort_desc": False, "limit": 50},
    )
    descending_open = api_client.get(
        "/tasks",
        params={"is_done": False, "sort_desc": True, "limit": 50},
    )
    assert [task["id"] for task in ascending_open.json()] == sorted(open_ids)
    assert [task["id"] for task in descending_open.json()] == sorted(
        open_ids, reverse=True
    )

    path = api_service.storage.path
    stats_before = api_client.get("/stats").json()
    bytes_before = path.read_bytes()

    # Здесь выполняются успешные query-запросы из предыдущих шагов.

    assert api_client.get("/stats").json() == stats_before
    assert path.read_bytes() == bytes_before



def test_openapi_contract(api_client):
    # Получаем автоматически сгенерированную OpenAPI-схему.
    document = api_client.get("/openapi.json").json()
    paths = document["paths"]
    assert set(paths) == {"/health", "/tasks", "/tasks/{task_id}", "/stats"}
    assert set(paths["/health"]) == {"get"}
    assert set(paths["/tasks"]) == {"get", "post"}
    assert set(paths["/tasks/{task_id}"]) == {"get", "put", "patch", "delete"}
    assert set(paths["/stats"]) == {"get"}

    expected_statuses = {
        "/health": {"get": "200"},
        "/tasks": {"get": "200", "post": "201"},
        "/tasks/{task_id}": {
            "get": "200", "put": "200", "patch": "200", "delete": "204"
        },
        "/stats": {"get": "200"},
    }
    for path, methods in expected_statuses.items():
        for method, status in methods.items():
            assert status in paths[path][method]["responses"]

    query = {
        item["name"]: item
        for item in paths["/tasks"]["get"]["parameters"]
    }
    assert query["is_done"]["required"] is False
    assert query["sort_desc"]["schema"]["default"] is False
    assert query["limit"]["schema"]["default"] == 10
    assert query["limit"]["schema"]["minimum"] == 1
    assert query["limit"]["schema"]["maximum"] == 50

    item_parameters = {
        item["name"]: item
        for item in paths["/tasks/{task_id}"]["get"]["parameters"]
    }
    task_id = item_parameters["task_id"]
    assert task_id["required"] is True
    id_schema = task_id["schema"]
    assert id_schema.get("minimum", 0) >= 1 or id_schema.get("exclusiveMinimum", -1) >= 0

    schemas = document["components"]["schemas"]
    assert set(schemas["TaskRead"]["properties"]) == {
        "id", "title", "priority", "is_done"
    }