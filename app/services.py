class PlannerService:
    def __init__(self, storage):
        self.storage = storage

    def list_tasks(self):
        return self.storage.load()

    def get_task(self, task_id):
        if type(task_id) is not int:
            raise ValueError('Номер задачи должен быть целым числом')
        task_id = validate_task_id(task_id)
        for task in self.storage.load():
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f'Задача {task_id} не найдена')

    def search_tasks(self, query):
        query = query.strip().lower()
        if not query:
            return []
        return [task for task in self.storage.load() if query in task.title.lower()]

    def get_statistics(self):
        tasks = self.storage.load()
        done = sum(task.is_done for task in tasks)
        total = len(tasks)
        return {'all': total, 'open': total - done, 'done': done}

    def add_task(self, title, priority, tags=None):
        tasks = self.storage.load()
        task = Task(id=max((t.id for t in tasks), default=0) + 1,
                    title=title, priority=priority, is_done=False,
                    tags=list(tags) if tags is not None else [])
        tasks.append(task)
        self.storage.save(tasks)
        return task

    def mark_done(self, task_id):
        tasks = self.storage.load()
        task = self._get_task(tasks, task_id)
        if task.is_done:
            return task
        task.mark_done()
        self.storage.save(tasks)
        return task

    def delete_task(self, task_id):
        tasks = self.storage.load()
        task = self._get_task(tasks, task_id)
        tasks.remove(task)
        self.storage.save(tasks)
        return None

    def delete_command(service, raw_id):
        try:
            service.delete_task(int(raw_id))
        except (ValueError, TaskNotFoundError) as error:
            print(f"Ошибка: {error}")
            return
        print("Задача удалена")
