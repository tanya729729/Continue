#from reports.report import make_report
from app.cli import run, format_task
from app.models import Task
from pathlib import Path
from app.storage import load_tasks, save_tasks
from app.errors import StorageError
from app.services import PlannerService
from app.storage import JsonStorage

# Путь к файлу с задачами
TASKS_FILE = Path(__file__).resolve().parent / "tasks.json"

def expect_value_error(make_task):
    try:#начинает блок, в котором ожидается ошибка.
        make_task() 
    except ValueError: # перехватывает ValueError, если он возник при вызове.
        return #завершает проверку: ожидаемая ошибка получена, None — результат по умолчанию 
    raise AssertionError("конструктор принял некорректные данные") # вызывает AssertionError, если make_task() завершился без ошибки.

#lambda — конструкция для создания функции без имени.
#В этом списке каждая функция принимает ноль аргументов и при вызове создаёт Task с указанными значениями.
invalid_calls = [
    lambda: Task(True, "Проверить id"),
    lambda: Task("2", "Проверить id"),
    lambda: Task(0, "Проверить диапазон"),
    lambda: Task(2, "Проверить priority", True),
    lambda: Task(3, "Проверить priority", False),
    lambda: Task(3, "Проверить диапазон", 0),
    lambda: Task(3, "Проверить диапазон", 6),
    lambda: Task(3, "Проверить тип", "3"),
    lambda: Task(4, ""),
    lambda: Task(4, "   "),
    lambda: Task(5, "Проверить статус", 2, "False"),
]

for make_task in invalid_calls:
    expect_value_error(make_task)


def calculate_study_minutes(durations):
    total=0
    for duration in durations: # перебирает длительности по одной
        total=total+duration #добавляет текущую длительность к сумме.
    return total

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

def make_notifier(channel):
    def notify(items):
        print(channel, items)
    return notify #return notify возвращает саму функцию, не вызывая её,
#Это замыкание: возвращённая функция сохраняет доступ к channel после завершения make_notifier.


DATA_PATH = Path('data') / 'tasks.json'

#функция создаёт сервис PlannerService с переданным хранилищем.
def build_service(storage=None):
    if storage is None:
        storage = JsonStorage(DATA_PATH) #создаётся JsonStorage с путём DATA_PATH.
    return PlannerService(storage)

#точка входа в программу. Он определяет, что произойдёт при запуске main.py
def main():
    try:
        # Загружаем ранее сохранённые задачи
        tasks = load_tasks(TASKS_FILE)

        # Запускаем меню приложения
        run(tasks)

        # Сохраняем изменения после выхода из меню
        save_tasks(TASKS_FILE,tasks)

    except StorageError as error:
        print(f"Ошибка хранилища: {error}")

""" def main():
    service = build_service()
    try:
        run(service)
    except StorageError as error:
        print(f"Ошибка хранилища: {error}") """


if __name__ == "__main__":
    main()
