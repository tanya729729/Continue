from fastapi.testclient import TestClient
from app.api import app


def test_health_returns_ok():
    with TestClient(app) as client:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_create_then_read(api_client):
    response = api_client.post(
        "/tasks", json={"title": "Read", "priority": 2}
    )
    assert response.status_code == 201
    created = response.json()

    result = api_client.get(f"/tasks/{created['id']}")
    assert result.status_code == 200
    assert result.json() == created

def test_new_function_starts_empty(api_client):
    response = api_client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []



_original_planner = app.state.planner


def test_00_temporary_failure_after_yield(api_client):
    raise RuntimeError("controlled fixture failure")


def test_01_temporary_planner_was_restored():
    assert app.state.planner is _original_planner


def test_list_returns_seeded_tasks(api_client, api_service):
    task = api_service.add_task("Записать вывод", 2)

    response = api_client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": task.id,
            "title": "Записать вывод",
            "priority": 2,
            "is_done": False,
        }
    ]


def test_stats_reports_all_tasks(api_client, api_service):
    api_service.add_task("Открытая задача", 1)
    done_task = api_service.add_task("Готовая задача", 3)
    api_service.mark_done(done_task.id)

    response = api_client.get("/stats")

    assert response.status_code == 200
    assert response.json() == {"total": 2, "open": 1, "done": 1}


def test_item_returns_public_task_without_tags(api_client, api_service):
    task = api_service.add_task("Прочитать ответ", 4, tags=["внутренний"])

    response = api_client.get("/tasks/" + str(task.id))

    assert response.status_code == 200
    assert response.json() == {
        "id": task.id,
        "title": "Прочитать ответ",
        "priority": 4,
        "is_done": False,
    }

def test_create_then_read_uses_server_id(api_client):
    post_response = api_client.post(
        "/tasks",
        json={"title": "Записать вывод", "priority": 2},
    )

    assert post_response.status_code == 201
    created = post_response.json()
    assert created["title"] == "Записать вывод"
    assert created["priority"] == 2
    assert created["is_done"] is False

    read_response = api_client.get("/tasks/" + str(created["id"]))

    assert read_response.status_code == 200
    assert read_response.json() == created


def test_put_replaces_task(api_client, api_service):
    task = api_service.add_task("Старый заголовок", 1)
    api_service.mark_done(task.id)

    response = api_client.put(
        "/tasks/" + str(task.id),
        json={"title": "Новый заголовок", "priority": 4, "is_done": False},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": task.id,
        "title": "Новый заголовок",
        "priority": 4,
        "is_done": False,
    }

def test_patch_applies_false_and_keeps_other_values(api_client, api_service):
    task = api_service.add_task("Сверить ответ", 3)
    api_service.mark_done(task.id)

    response = api_client.patch(
        "/tasks/" + str(task.id),
        json={"is_done": False},
    )

    assert response.status_code == 200

    read_response = api_client.get("/tasks/" + str(task.id))
    assert read_response.status_code == 200
    assert read_response.json() == {
        "id": task.id,
        "title": "Сверить ответ",
        "priority": 3,
        "is_done": False,
    }

def test_delete_returns_empty_204_then_get_returns_404(api_client, api_service):
    task = api_service.add_task("Удалить задачу", 2)

    delete_response = api_client.delete("/tasks/" + str(task.id))

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    read_response = api_client.get("/tasks/" + str(task.id))

    assert read_response.status_code == 404