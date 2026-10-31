#В errors.py переносим определение TaskNotFoundError.
class TaskNotFoundError(Exception):
    """задача с указанным ID не найдена."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Задача с ID {task_id} не найдена")


class StorageError(Exception):
    """Ожидаемая ошибка файлового хранилища."""


class SnapshotValidationError(ValueError):
    """Неверная структура JSON-снимка задач."""