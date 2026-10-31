
def normalize_title(title):
    return title.lower().lstrip().rstrip()


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
    if normalized == "":
        raise ValueError("Название не может быть пустым")
    return normalized

def validate_priority(priority):
    if type(priority) is not int:
        raise ValueError("Приоритет должен быть целым числом")
    if not 1 <= priority <= 5:
        raise ValueError("Приоритет должен быть от 1 до 5")
    return priority


from app.errors import SnapshotValidationError


def validate_snapshot(data):
    if not isinstance(data, list):
        raise SnapshotValidationError(
            "JSON-снимок должен быть списком задач"
        )

    seen_ids = set()

    for index, task in enumerate(data):
        if not isinstance(task, dict):
            raise SnapshotValidationError(
                f"Элемент {index} должен быть словарём"
            )

        required = {"id", "title", "priority", "is_done"}

        if not required.issubset(task):
            raise SnapshotValidationError(
                f"У задачи {index} отсутствуют обязательные поля"
            )

        try:
            validate_task_id(task["id"])
            validate_title(task["title"])
            validate_priority(task["priority"])
        except ValueError as error:
            raise SnapshotValidationError(
                f"Ошибка полей задачи {index}"
            ) from error

        if type(task["is_done"]) is not bool:
            raise SnapshotValidationError(
                f"Неверное поле is_done у задачи {index}"
            )

        if task["id"] in seen_ids:
            raise SnapshotValidationError(
                f"Повторяющийся ID: {task['id']}"
            )

        seen_ids.add(task["id"])

    return data

# app.validators, если такого helper ещё нет:
TASK_FIELDS = {"id", "title", "priority", "is_done"}

def validate_task_record(record, location="record"):
    if not isinstance(record, dict):
        raise ValueError(f"{location}: ожидается словарь")
    if set(record) != TASK_FIELDS:
        raise ValueError(f"{location}: ожидаются ровно {sorted(TASK_FIELDS)}")
    return record

def validate_tags(tags):
    if not isinstance(tags, list):
        raise ValueError('Метки должны быть списком')
    normalized = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValueError('Каждая метка должна быть строкой')
        clean = tag.strip()
        if not clean:
            raise ValueError('Метка не может быть пустой')
        normalized.append(clean)
    return normalized
