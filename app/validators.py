from app.errors import SnapshotValidationError

REQUIRED_FIELDS = {"id", "title", "priority", "is_done"}
ALLOWED_FIELDS = REQUIRED_FIELDS | {"tags"}
TASK_FIELDS = REQUIRED_FIELDS  


def normalize_title(title):
    return title.strip()

def validate_task_id(task_id):
    if type(task_id) is not int:
        raise ValueError("Номер задачи должен быть целым числом")
    if task_id <= 0:
        raise ValueError("Номер задачи должен быть положительным")
    return task_id


def validate_title(title):
    if not isinstance(title, str):
        raise ValueError("Название должно быть строкой")
    normalized = normalize_title(title)
    if not normalized:
        raise ValueError("Название не может быть пустым")
    return normalized


def validate_priority(priority):
    if type(priority) is not int:
        raise ValueError("Приоритет должен быть целым числом")
    if not 1 <= priority <= 5:
        raise ValueError("Приоритет должен быть от 1 до 5")
    return priority


def validate_tags(tags):
    if not isinstance(tags, list):
        raise ValueError("Метки должны быть списком")
    normalized = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValueError("Каждая метка должна быть строкой")
        clean = tag.strip()
        if not clean:
            raise ValueError("Метка не может быть пустой")
        normalized.append(clean)
    return normalized


def validate_task_record(record, location="record"):
    if not isinstance(record, dict):
        raise ValueError(f"{location}: ожидается словарь")
    #сравнивает множество ключей записи с каждым из двух допустимых множеств.
    if set(record) not in (REQUIRED_FIELDS, ALLOWED_FIELDS):
        raise ValueError(f"{location}: неверный набор полей") # сообщает об ошибке, если набор ключей не совпал ни с одним из них.
    return record


def validate_snapshot(data):
    if not isinstance(data, list):
        raise SnapshotValidationError("JSON-снимок должен быть списком задач")

    seen_ids = set()
    for index, task in enumerate(data):
        try:
            validate_task_record(task, f"tasks[{index}]")
            task_id = validate_task_id(task["id"])
            title = validate_title(task["title"])
            validate_priority(task["priority"])
            if title != task["title"]:
                raise ValueError("Название не нормализовано")
            if type(task["is_done"]) is not bool:
                raise ValueError("is_done должен быть bool")
            if "tags" in task:
                tags = validate_tags(task["tags"])
                if tags != task["tags"]: #сравнивает проверенные метки с исходными.
                    raise ValueError("Метки не нормализованы")
            if task_id in seen_ids: #проверяет, встречался ли уже этот идентификатор.
                raise ValueError(f"Повторяющийся ID: {task_id}")
            seen_ids.add(task_id) # добавляет идентификатор в множество.
        except ValueError as error:
            raise SnapshotValidationError(f"Ошибка задачи {index}: {error}") from error
    return data
