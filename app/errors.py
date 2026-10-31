#В errors.py переносим определение TaskNotFoundError.
class TaskNotFoundError(Exception):
    """Исключение, возникающее, когда задача с указанным ID не найдена."""

    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Задача с ID {task_id} не найдена")