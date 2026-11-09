#В errors.py переносим определение TaskNotFoundError.
class TaskNotFoundError(Exception):
    """задача с указанным ID не найдена."""

    def __init__(self, task_id: int): #инициализирует объект, принимая идентификатор задачи task_id
        self.task_id = task_id # сохраняет идентификатор в атрибуте объекта.
        super().__init__(f"Задача с ID {task_id} не найдена") # вызывает конструктор родительского класса, передавая ему сообщение о том, что задача не найдена.


class StorageError(Exception): #StorageError наследуется от Exception
    """Ожидаемая ошибка файлового хранилища."""


class SnapshotValidationError(ValueError):
    """Неверная структура JSON-снимка задач."""