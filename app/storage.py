import json
from pathlib import Path
from app.errors import StorageError, SnapshotValidationError
from app.validators import validate_priority, validate_task_id, validate_title, validate_snapshot

def encode_tasks(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)

def decode_tasks(text):
    return json.loads(text)


def load_tasks(path):
    path = Path(path)

    # Открываем файл
    try:
        file = path.open("r", encoding="utf-8")

    except FileNotFoundError:
        return []

    except OSError as error:
        raise StorageError(
            f"Не удалось открыть файл: {path}"
        ) from error

    # Читаем содержимое
    try:
        with file:
            text = file.read()

    except (OSError, UnicodeError) as error:
        raise StorageError(
            f"Не удалось прочитать файл: {path}"
        ) from error

    # Декодируем JSON
    try:
        tasks = decode_tasks(text)

    except json.JSONDecodeError as error:
        raise StorageError(
            f"Некорректный JSON: {path}"
        ) from error

    # Проверяем форму снимка
    try:
        return validate_loaded_tasks(tasks)

    except ValueError as error:
        raise StorageError(
            f"Некорректная структура задач: {path}"
        ) from error


def save_tasks(path, tasks):
    path = Path(path)

    # Сохраняем существующую проверку данных
    try:
        validate_loaded_tasks(tasks)

    except ValueError as error:
        raise StorageError(
            "Некорректные данные для сохранения"
        ) from error

    text = encode_tasks(tasks)

    # Создаём каталог и записываем файл
    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with path.open("w", encoding="utf-8") as file:
            file.write(text)

    except OSError as error:
        raise StorageError(
            f"Не удалось сохранить файл: {path}"
        ) from error


TASK_FIELDS = {"id", "title", "priority", "is_done"}


def validate_loaded_tasks(tasks):
    if not isinstance(tasks, list):
        raise ValueError("Корень снимка должен быть списком")

    seen_ids = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise ValueError(f"tasks[{index}]: ожидался словарь")
        if set(task) != TASK_FIELDS:
            raise ValueError(f"tasks[{index}]: неверный набор полей")

        task_id = task["id"]
        title = task["title"]
        priority = task["priority"]
        is_done = task["is_done"]

        if type(task_id) is not int:
            raise ValueError(f"tasks[{index}].id: ожидался int")
        if type(priority) is not int:
            raise ValueError(f"tasks[{index}].priority: ожидался int")
        if type(title) is not str:
            raise ValueError(f"tasks[{index}].title: ожидался str")
        if type(is_done) is not bool:
            raise ValueError(f"tasks[{index}].is_done: ожидался bool")

        try:
            validate_task_id(task_id)
        except ValueError as error:
            raise ValueError(f"tasks[{index}].id: {error}") from error

        try:
            validate_priority(priority)
        except ValueError as error:
            raise ValueError(f"tasks[{index}].priority: {error}") from error

        try:
            normalized_title = validate_title(title)
        except ValueError as error:
            raise ValueError(f"tasks[{index}].title: {error}") from error
        if normalized_title != title:
            raise ValueError(f"tasks[{index}].title: строка не нормализована")

        if task_id in seen_ids:
            raise ValueError(f"tasks[{index}].id: повторяется значение {task_id}")
        seen_ids.add(task_id)

    return tasks



