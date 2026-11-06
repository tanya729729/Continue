from app.models import Task
from app.validators import validate_task_id
from app.errors import TaskNotFoundError

class PlannerService:
    #обращается к хранилищу через storage
    def __init__(self, storage):
        self.storage = storage #сохраняет переданное хранилище в объекте.

    def list_tasks(self): #метод получения всех задач
        return self.storage.load()

    def _get_task(self, tasks, task_id): #объявляет внутренний метод поиска задачи в уже загруженном списке
        task_id = validate_task_id(task_id) 

        for task in tasks:
            if task.id == task_id: #равнивает идентификатор текущей задачи с искомым.
                return task #возвращает найденную задачу.

        raise TaskNotFoundError(task_id) #вызывает ошибку, если после перебора задача не найдена.

    def get_task(self, task_id): #объявляет метод получения одной задачи
        tasks = self.storage.load() #загружает задачи.
        return self._get_task(tasks, task_id) # ищет и возвращает задачу по идентификатору.

    def search_tasks(self, query): #объявляет поиск по названию
        query = query.strip().lower()
        if not query: #проверяет, пуст ли запрос
            return [] #возвращает пустой список для пустого запроса.
        return [task for task in self.storage.load() if query in task.title.lower()]#загружает задачи и возвращает те, чьи названия содержат запрос без учёта регистра.

    def get_statistics(self):
        tasks = self.storage.load()
        done = sum(task.is_done for task in tasks) #считает выполненные задачи
        total = len(tasks)
        return {'all': total, 'open': total - done, 'done': done}

    def add_task(self, title, priority, tags=None):
        tasks = self.storage.load() # загружает существующие задачи.
        task = Task(id=max((t.id for t in tasks), default=0) + 1, # берёт максимальный текущий идентификатор и увеличивает его на один.
                    title=title, priority=priority, is_done=False, # задаёт название, приоритет и начальный статус «не выполнена».
                    tags=list(tags) if tags is not None else []) #копирует переданные теги в список или создаёт пустой список.
        tasks.append(task)
        self.storage.save(tasks) # сохраняет обновлённый список
        return task

    #объявляет метод завершения задачи
    def mark_done(self, task_id):
        tasks = self.storage.load()
        task = self._get_task(tasks, task_id) #находит задачу по идентификатору
        if task.is_done:
            return task # если выполнена, возвращает её без изменений и сохранения
        task.mark_done() #иначе вызывает метод задачи, отмечающий её выполненной
        self.storage.save(tasks) 
        return task

    def delete_task(self, task_id):
        tasks = self.storage.load()
        # находит нужную задачу
        task = self._get_task(tasks, task_id)
        tasks.remove(task)
        # сохраняет обновлённый список
        self.storage.save(tasks)
        return None #явно возвращает отсутствие результата

    def delete_command(service, raw_id):
        try:
            service.delete_task(int(raw_id))
        except (ValueError, TaskNotFoundError) as error: #перехватывает ошибку преобразования или отсутствия задачи
            print(f"Ошибка: {error}")
            return # прекращает выполнение после ошибки
        print("Задача удалена")
