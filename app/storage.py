import json
import os
import tempfile
from pathlib import Path

from app.errors import StorageError
from app.validators import validate_snapshot
from tempfile import TemporaryDirectory
from app.services import PlannerService
from app.models import Task

def list_tasks(storage):
    return storage.load()


def mark_task_done(storage, task_id):
    tasks = storage.load()
    task = get_task(tasks, task_id)
    if not task.is_done:
        task.mark_done()
        storage.save(tasks)
    return True

def encode_tasks(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)


def decode_tasks(text):
    return json.loads(text)


def validate_loaded_tasks(tasks):
    return validate_snapshot(tasks)


def load_tasks(path):
    path = Path(path)
    try:
        file = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as error:
        raise StorageError(f"Не удалось открыть файл: {path}") from error

    try:
        with file:
            text = file.read()
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось прочитать файл: {path}") from error

    try:
        tasks = decode_tasks(text)
    except json.JSONDecodeError as error:
        raise StorageError(f"Некорректный JSON: {path}") from error

    try:
        return validate_loaded_tasks(tasks)
    except ValueError as error:
        raise StorageError(f"Некорректная структура задач: {path}") from error


def save_tasks(path, tasks):
    path = Path(path)
    try:
        validate_loaded_tasks(tasks)
    except ValueError as error:
        raise StorageError("Некорректные данные для сохранения") from error

    try:
        text = encode_tasks(tasks)
    except (TypeError, ValueError) as error:
        raise StorageError("Не удалось сериализовать задачи") from error

    temp_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temp_path = Path(file.name)
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        temp_path = None
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось сохранить файл: {path}") from error
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

       



class JsonStorage:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[Task]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError) as error:
            raise StorageError("Не удалось прочитать задачи") from error

        try:
            records = json.loads(text)
            validate_loaded_tasks(records)
            return [Task.from_dict(record) for record in records]
        except (ValueError, TypeError) as error:
            raise StorageError("Неверный JSON или структура задач") from error

    def save(self, tasks: list[Task]) -> None:
        try:
            records = [task.to_dict() for task in tasks]
            validate_loaded_tasks(records)
            text = json.dumps(records, ensure_ascii=False, indent=2)
        except (ValueError, TypeError) as error:
            raise StorageError("Неверный список задач") from error

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(text, encoding="utf-8")
        except OSError as error:
            raise StorageError("Не удалось сохранить задачи") from error

class MemoryStorage:
    def __init__(self, tasks=None):
        self._tasks = list(tasks) if tasks is not None else []

    def load(self):
        return list(self._tasks)

    def save(self, tasks):
        self._tasks = list(tasks)


class SaveCounter:
    def __init__(self, storage):
        self.storage = storage
        self.save_calls = 0

    def load(self):
        return self.storage.load()

    def save(self, tasks):
        self.save_calls += 1
        return self.storage.save(tasks)





class CountingMemoryStorage(MemoryStorage):
    def __init__(self):
        super().__init__()
        self.saves = 0

    def save(self, tasks):
        self.saves += 1
        super().save(tasks)


memory = CountingMemoryStorage()
service = PlannerService(memory)
task = service.add_task("Проверить запись", 2)
assert memory.saves == 1
service.list_tasks()
assert memory.saves == 1
service.mark_done(task.id)
assert memory.saves == 2
service.mark_done(task.id)
assert memory.saves == 2

with TemporaryDirectory() as folder:
    path = Path(folder) / "tasks.json"
    PlannerService(JsonStorage(path)).add_task("Восстановить", 3)
    reopened = PlannerService(JsonStorage(path))
    assert reopened.get_task(1).title == "Восстановить"