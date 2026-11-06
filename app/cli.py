from app.operations import add_task, find_task, mark_task_done, search_tasks, handle_stats
from app.validators import  normalize_title
from app.errors import TaskNotFoundError

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
def show_menu(write=print):
    write("")
    write("StudyHub Planner")
    write("add - добавить задачу")
    write("list - показать задачи")
    write("find - найти задачу по id")
    write("done - отметить задачу выполненной")
    write("search - искать по названию")
    write("stats - показать статистику")
    write("exit - завершить работу")
    write("delete - удалить задачу")


#функция позволяет пользоваться программой, пока пользователь не выберет exit
#запросить данные и добавить новую задачу
#найти задачу по id и вывести её
#пометить задачу выполненной
""" def run(tasks=None):
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
 """


# Показывает все задачи через сервис.
def handle_list(service, read=input, write=print):
    tasks = service.list_tasks()

    if not tasks:
        write("Список задач пока пуст.")
        return

    for task in tasks:
        write(str(task))


# Добавляет новую задачу.
def handle_add(service, read=input, write=print):
    while True:
        title = read("Название задачи: ")

        try:
            from app.validators import validate_title
            validate_title(title)
            break
        except ValueError as error:
            write(str(error))

    while True:
        raw_priority = read("Приоритет от 1 до 5: ")

        try:
            priority = int(raw_priority)
        except ValueError:
            write("Введите целое число")
            continue

        if not 1 <= priority <= 5:
            write("Приоритет должен быть от 1 до 5")
            continue

        break

    task = service.add_task(title, priority)
    write(str(task))


# Ищет задачи по названию.
def handle_search(service, read=input, write=print):
    query = read("Фрагмент названия: ").strip()

    if not query:
        write("Введите непустой фрагмент")
        return

    tasks = service.search_tasks(query)

    if not tasks:
        write("Совпадений не найдено")
        return

    for task in tasks:
        write(str(task))

# Находит задачу по ID.
def handle_find(service, read=input, write=print):
    while True:
        raw_id = read("Номер задачи: ")

        try:
            task_id = int(raw_id)

            if task_id <= 0:
                write("Номер должен быть положительным")
                continue

        except ValueError:
            write("Введите целое число")
            continue

        try:
            task = service.get_task(task_id)
        except TaskNotFoundError:
            write("Задача не найдена")
            return

        write(str(task))
        return


# Отмечает задачу выполненной.
def handle_done(service, read=input, write=print):
    raw_id = read("Номер задачи: ")

    try:
        task = service.mark_done(int(raw_id))
    except (ValueError, TaskNotFoundError) as error:
        write(f"Ошибка: {error}")
        return

    write(f"Задача {task.id} выполнена")


# Показывает статистику задач.
def handle_stats(service, read=input, write=print):
    statistics = service.get_statistics()

    total = statistics["all"]
    completed = statistics["done"]
    left = statistics["open"]

    percent = round(completed / total * 100, 2) if total else 0

    write(f"Всего: {total}")
    write(f"Выполнено: {completed}")
    write(f"Осталось: {left}")
    write(f"Процент выполнения: {percent}%")

def handle_delete(service, read=input, write=print):
    raw_id = read("Номер задачи: ")

    try:
        service.delete_task(int(raw_id))
    except TaskNotFoundError:
        write("Задача не найдена")
        return
    except ValueError:
        write("Введите корректный ID задачи")
        return
    write("Задача удалена")

COMMAND_HANDLERS = {
    "add": handle_add,
    "list": handle_list,
    "find": handle_find,
    "done": handle_done,
    "search": handle_search,
    "stats": handle_stats,
    "delete": handle_delete,
}

def execute_command(service, command, read=input, write=print):
    name = command.strip().lower()
    if name == "exit":
        write("Работу завершили")  # сохраните прежнее сообщение
        return False #завершает функцию и возвращает сигнал остановки для вызывающего кода.
    handler = COMMAND_HANDLERS.get(name)  # существующая маршрутизация, ищет обработчик команды в словаре; если ключа нет, возвращает None.
    if handler is None:
        write("Неизвестная команда")  #  сообщает об ошибке ввода
        return True #завершает функцию с сигналом продолжения работы
    handler(service, read=read, write=write)
    return True# сообщает вызывающему коду, что работу можно продолж


def run(service, read=input, write=print):
    while True: #запускает бесконечный цикл обработки команд.
        show_menu(write)  # существующее меню
        command = read("Команда: ")#запрашивает команду и сохраняет введённую строку
        if not execute_command(service, command, read, write): #проверяет, вернула ли обработка False, то есть сигнал завершения.
            break # выходит из цикла, после чего функция run заканчивается

def read_number(raw):
    try:
        value = int(raw)
    except ValueError:
        print("Нужны цифры")
    else: #выполняется, когда блок try завершился без исключения, либо сверху ошибка либо выводим число
        print(f"Номер: {value}") #f-строка подставляет значение value вместо выражения в фигурных скобках.
    finally:
        print("Попытка закончена")

def read_int(prompt):
    while True: # запускает цикл, который повторяется до успешного ввода.
        raw_value = input(prompt)
        try:
            value = int(raw_value)
        except ValueError:
            print("Введите целое число")
            continue # начинает следующую итерацию цикла и повторно запрашивает ввод.
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




def fake_read(prompt): #функция принимает prompt и возвращает первый элемент answers, одновременно удаляя его из списка
    return answers.pop(0) #Если answers пуст, pop(0) вызовет IndexError.

