#from errors import TaskNotFoundError
from app.validators import normalize_title, validate_priority, validate_task_id, validate_title
from app.operations import (
    add_task,
    find_task,
    mark_task_done,
    search_tasks,
    build_statistics,
    completion_percent,
    handle_stats,
)
from reports.report import make_report
print(make_report("Weekly"))  # Отчёт: Weekly

#функция запрашивает у пользователя номер задачи
def read_task_id():
    while True:
        task_id = read_int("Номер задачи: ")
        if task_id > 0:
            return task_id
        print("Номер должен быть положительным")

def format_task(task):
    if task["is_done"] == True:
        return f'[{task["id"]}] {task["title"]} | приоритет: {task["priority"]} | выполнена'

    return f'[{task["id"]}] {task["title"]} | приоритет: {task["priority"]} | не выполнена'


def calculate_study_minutes(durations):
    total=0
    for duration in durations:
        total=total+duration
    return total


def show_tasks(tasks):
    if len(tasks) == 0:
        print("Список задач пока пуст.")
        return #дальнейший цикл не запускается,return передаёт управление обратно в место, откуда была вызвана функция
    for task in tasks:
        print(format_task(task))

# функция ввода названия задачи,после нормализации проверяется, осталась ли строка пустой. 
def read_title():
    while True:
        raw_title = input("Название задачи: ")
        title = normalize_title(raw_title)
        if title == "":   
            print("Название не должно быть пустым.")
            continue  #все,что ниже не выполняется,управление переходит к while True
        return title

def read_priority():
    while True:
        priority = read_int("Приоритет от 1 до 5: ")
        if 1 <= priority <= 5:
            return priority
        print("Приоритет должен быть от 1 до 5")


# функция отвечает только за оркестрацию, а все детали валидации и формирования задачи вынесены в отдельные функции
def handle_add(tasks):
    title = read_title()
    priority = read_priority()
    try:
        task = add_task(tasks, title, priority)
    except ValueError as error:
        print(error)
    else:
        print(format_task(task))

def handle_search(tasks):
    query = input("Введите название для поиска: ").strip()

    found_tasks = search_tasks(tasks, query)

    if not found_tasks:
        print("Задачи не найдены")
        return

    show_tasks(found_tasks)        


def handle_find(tasks):
    task_id = read_task_id()
    task = find_task(tasks, task_id)
    if task is None:
        print('Задача не найдена')
    else:
        print(format_task(task))


#функция помечает задачу как выполненную
def handle_done(tasks):
    task_id = read_task_id()
    was_found = mark_task_done(tasks, task_id)
    if was_found:
        print("Задача выполнена")
    else:
        print("Задача не найдена")

#функция выводит пользователю список доступных команд
def show_menu():
    print()
    print("StudyHub Planner")
    print("add - добавить задачу")
    print("list - показать задачи")
    print("find - найти задачу по id")
    print("done - отметить задачу выполненной")
    print("search - искать по названию")
    print("stats - показать статистику")
    print("exit - завершить работу")

#функция позволяет пользоваться программой, пока пользователь не выберет exit
#запросить данные и добавить новую задачу
#найти задачу по id и вывести её
#пометить задачу выполненной
def run(tasks=None):
    if tasks is None:
        tasks = []

    handlers = {
        "add": handle_add,
        "list": handle_list,
        "find": handle_find,
        "done": handle_done,
        "search": handle_search,
        "stats": handle_stats,
    }

    while True:
        show_menu()

        command = input("Команда: ").strip().lower()

        if command == "exit":
            print("Работу завершили")
            break

        if command not in handlers:
            print("Неизвестная команда")
            continue

        handlers[command](tasks)

    return tasks

#получает список tasks 
# сразу передаёт его функции show_tasks, которая должна вывести задачи
def handle_list(tasks):
    show_tasks(tasks)

def change_level(level):
    level = 8
    print(level)

def add_stop(route):
    route.append('сад')

def replace_route(route):
    route = ['парк']

def add_then_replace(route):
    route.append('сад')
    route = ['парк']
    route.append('лес')

def choose_view(items):
    items = ['новая']
    return items

#функция использует изменяемый параметр actions со значением по умолчанию
#возвращает текущий список действий.
def log_action(action, actions=None):
    if actions is None:
        actions = []

    actions.append(action)
    return actions

#возвращает кортеж из двух переданных аргументов 
def connect(start, finish):
    return start, finish

#принимает аргумент category, произвольное количество дополнительных позиционных аргументов (*marks)
# и произвольное количество именованных аргументов (**options)
# возвращает кортеж 
def observe(category, *marks, **options):
    return category, marks, options

# функция собирает все позиционные аргументы в кортеж и передаёт их в connect через *args
# и собирает все именованные аргументы в словарь и передаёт их в connect через **kwargs
def relay(*args, **kwargs):
    return connect(*args, **kwargs)

def notify():
    print('Сработало')

#функция‑фабрика, создающая обёртку (wrapper) для любой переданной функции 
#operation — вызываемая функция, которую нужно трассировать.
#prefix — строка, используемая в выводе для обозначения начала и завершения операции
def make_trace(operation, prefix):
    def wrapper(*args, **kwargs):
        print(f"{prefix} START")
        result = operation(*args, **kwargs)
        print(f"{prefix} DONE {result}")
        return result
    return wrapper

#принимает метку label и список events
#добавляет переданную метку в конец списка
def record_event(label, events):
    events.append(label)
    return 'accepted'

calls = []
#функция добавляет идентификатор задачи task['id'] в список calls
def counted_format_task(task):
    calls.append(task['id'])
    return format_task(task)

def read_number(raw):
    try:
        value = int(raw)
    except ValueError:
        print("Нужны цифры")
    else:
        print(f"Номер: {value}")
    finally:
        print("Попытка закончена")

def read_int(prompt):
    while True:
        raw_value = input(prompt)
        try:
            value = int(raw_value)
        except ValueError:
            print("Введите целое число")
            continue
        return value


if __name__ == "__main__":
    run()