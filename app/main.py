#from reports.report import make_report
from app.cli import run, format_task
from app.storage import encode_tasks, decode_tasks


def calculate_study_minutes(durations):
    total=0
    for duration in durations:
        total=total+duration
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



def main():
    tasks = []
    run(tasks)


if __name__ == '__main__':
    main()