
from app.storage import JsonStorage
from app.services import PlannerService
from app.models import Task
import pytest
from app.errors import TaskNotFoundError



def test_added_task_uses_max_id_and_full_task_survives_new_service(tmp_path):
    from app.models import Task

    path = tmp_path / "tasks.json"
    storage = JsonStorage(path)
    storage.save(
        [
            Task(id=2, title="HTTP", priority=3, tags=["existing"]),
            Task(
                id=7,
                title="JSON",
                priority=4,
                is_done=True,
                tags=["keep"],
            ),
        ]
    )

    first_service = PlannerService(storage)
    created = first_service.add_task("Planner API", priority=5)

    second_service = PlannerService(JsonStorage(path))
    loaded = second_service.list_tasks()

    assert created.id == 8
    assert [
        (task.id, task.title, task.priority, task.is_done, task.tags)
        for task in loaded
    ] == [
        (2, "HTTP", 3, False, ["existing"]),
        (7, "JSON", 4, True, ["keep"]),
        (8, "Planner API", 5, False, []),
    ]




def test_replace_task_persists_full_task_for_new_service(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JsonStorage(path)
    original = [
        Task(id=4, title="Проверить API", priority=2, tags=["api"]),
        Task(id=11, title="Прочитать JSON", priority=3, tags=["storage", "review"]),
    ]
    storage.save(original)

    service = PlannerService(storage)
    updated = service.replace_task(
        11,
        title="Проверить сохранение",
        priority=5,
        is_done=True,
    )

    expected = Task(
        id=11,
        title="Проверить сохранение",
        priority=5,
        is_done=True,
        tags=["storage", "review"],
    )
    assert updated == expected

    restored = PlannerService(JsonStorage(path)).list_tasks()
    assert restored == [original[0], expected]



def test_replace_task_failures_do_not_change_storage(tmp_path):
    path = tmp_path / "tasks.json"
    storage = JsonStorage(path)
    before = [Task(id=11, title="Прочитать JSON", priority=3, tags=["keep"])]
    storage.save(before)
    service = PlannerService(storage)

    with pytest.raises(TaskNotFoundError):
        service.replace_task(
            404,
            title="Не добавлять",
            priority=2,
            is_done=False,
        )

    with pytest.raises(ValueError):
        service.replace_task(
            11,
            title="Не сохранять частично",
            priority=0,
            is_done=True,
        )

    after = PlannerService(JsonStorage(path)).list_tasks()
    assert after == before
