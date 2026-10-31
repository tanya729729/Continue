from app.operations import add_task, find_task, mark_task_done, search_tasks, handle_stats
from app.validators import  normalize_title

def format_task(task):
    if task["is_done"] == True:
        return f'[{task["id"]}] {task["title"]} | приоритет: {task["priority"]} | выполнена'

    return f'[{task["id"]}] {task["title"]} | приоритет: {task["priority"]} | не выполнена'

def show_tasks(tasks):
    if len(tasks) == 0:
        print("Список задач пока пуст.")
        return #дальнейший цикл не запускается,return передаёт управление обратно в место, откуда была вызвана функция
    for task in tasks:
        print(format_task(task))



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


#функция запрашивает у пользователя номер задачи
def read_task_id():
    while True:
        task_id = read_int("Номер задачи: ")
        if task_id > 0:
            return task_id
        print("Номер должен быть положительным")


#получает список tasks 
# сразу передаёт его функции show_tasks, которая должна вывести задачи
def handle_list(tasks):
    show_tasks(tasks)

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

