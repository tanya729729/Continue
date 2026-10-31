#В operations.py переносим  get_task.
from app.errors import TaskNotFoundError
from app.models import create_task
from app.validators import validate_priority, validate_title

#функция определяения следующего свободного идентификатора для новой задачи
def get_next_id(tasks):
    largest_id = 0
    for task in tasks:
        task_id = task["id"] #получает значение поля id текущей задачи
        if task_id > largest_id: #сравнение с текущим максимумом и обновление
            largest_id = task_id
    return largest_id + 1 #новый уникальный id, который еще не используется

def add_task(tasks, title, priority):
    task_id = get_next_id(tasks)
    new_task = create_task(task_id, title, priority)
    tasks.append(new_task)
    return new_task #возвращает только что созданный объект задачи

#функция ищет задачу по её идентификатору
def find_task(tasks, task_id): 
    for task in tasks:
        if task['id'] == task_id: #Проверяется, совпадает ли поле id текущей задачи с искомым task_id
            return task #При совпадении функция сразу возвращает найденный объект
    return None # ни одна задача не имеет указанного id

#функция помечает задачу как выполненную      
def mark_task_done(tasks, task_id):
    task = find_task(tasks, task_id)
    if task is None: #задача не найдена
        return False 
    task["is_done"] = True  #при найденной задаче изменяется поле is_done на True, тем самым отмечая её как выполненную.   
    return True 

#функция по запросу ищет совпадающие задачи
def search_tasks(tasks, query):
    normalized_query = query.strip().lower()
    if normalized_query == "":
        return []

    matches = []
    for task in tasks:
        if normalized_query in task["title"].lower(): #если запрос содержится в названии задачи
            matches.append(task)  #задача добавляется в список matches 
    return matches

def build_statistics(tasks):
    total = len(tasks)
    completed = sum(task["is_done"] for task in tasks)

    return {
        "total": total,
        "completed": completed,
        "left": total - completed,
    }


def completion_percent(statistics):
    if statistics["total"] == 0:
        return 0

    return round(
        statistics["completed"] / statistics["total"] * 100,
        2
    )

#функция принимает список tasks, формирует статистику и выводит её
#создаёт словарь с ключами total, completed и left
def handle_stats(tasks):
    statistics = build_statistics(tasks)
    percent = completion_percent(statistics) #completed / total * 100
    print(f"Всего: {statistics['total']}")
    print(f"Выполнено: {statistics['completed']}")
    print(f"Осталось: {statistics['left']}")
    print(f'Процент выполнения: {percent}%')

