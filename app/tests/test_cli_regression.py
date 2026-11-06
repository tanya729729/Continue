from app.cli import execute_command,run
from app.services import PlannerService,JsonStorage
from app.storage import MemoryStorage
import pytest
from app.errors import StorageError
from pathlib import Path
import subprocess
import sys
import app.main as entry
from app.main import build_service
from tempfile import TemporaryDirectory

#вызывает команду с заранее заданными ответами и собирает её сообщения и запросы.
def invoke(service, command, answers=()):
    pending = list(answers) # создаёт изменяемую копию ответов.
    prompts = [] # создают списки для запросов и сообщений.
    messages = [] 


    def read(prompt):
        prompts.append(prompt) # сохраняет текст запроса.
        return pending.pop(0) #удаляет и возвращает первый ожидающий ответ.

    #запускает команду для service, передавая ей read и функцию записи.
    running = execute_command(
        service, command, read=read,
        #преобразует сообщение в строку и добавляет его в messages.
        write=lambda message: messages.append(str(message)),
    )
    assert pending == []  #проверяет, что все заданные ответы были использованы
    return running, messages, prompts # возвращает результат вызова, сообщения и запросы


#проверяет повторный ввод при ошибочных данных и успешное добавление задачи
def test_add_retries_bad_input():
    # создаёт сервис с хранилищем в памяти.
    service = PlannerService(MemoryStorage())
    running, messages, prompts = invoke( # вызывает команду " ADD " и передаёт пять заранее заданных ответов.
        service, " ADD ", ["   ", "Учить pytest", "слово", "8", "3"] #" " — пустое после удаления пробелов название; "Учить pytest" — корректное название
    )

    assert running is True # проверяет, что приложение должно продолжить работу.
    assert len(prompts) == 5 #проверяет, что пользователю задали пять запросов
    assert "Название не может быть пустым" in messages
    assert "Введите целое число" in messages
    assert "Приоритет должен быть от 1 до 5" in messages
    tasks = service.list_tasks() # получает список задач
    assert len(tasks) == 1
    assert (tasks[0].id, tasks[0].title, tasks[0].priority) == (
        1, "Учить pytest", 3
    )
    assert tasks[0].is_done is False #проверяет, что задача ещё не выполнена.
    assert "Учить pytest" in messages[-1] #последняя проверка убеждается, что название задачи содержится в последнем сообщении.

#проверяет маршрутизацию команд планировщика, их вывод и изменения состояния.
def test_all_commands_and_unknown_route():
    service = PlannerService(MemoryStorage())#cоздаёт сервис с хранилищем в памяти.
    # добавляет задачу «Ревью» с приоритетом 2
    running, messages, _ = invoke(service, "add", ["Ревью", "2"])
    assert running is True #Проверки убеждаются, что приложение продолжает работу и сообщения содержат [1] Ревью
    assert "[1] Ревью" in " ".join(messages)

    #list выводит задачи, find ищет задачу по ID, search ищет по фрагменту названия, а stats показывает общее число задач
    cases = [
        ("list", [], "Ревью"),
        ("find", ["1"], "Ревью"),
        ("search", ["ВЬЮ"], "Ревью"),
        ("stats", [], "Всего: 1"),
    ]
    #запускает каждый сценарий, проверяет вывод и убеждается, что задача осталась в хранилище
    for command, answers, expected in cases:
        #Строка вызывает команду и распаковывает результат функции invoke.
        running, messages, _ = invoke(service, command, answers) #сервис, к которому применяется команда, 
        #_ получает список запросов prompts, который в этом тесте не используется.
        assert running is True
        assert expected in " ".join(messages) #Строка проверяет наличие ожидаемого текста в сообщениях.
        assert len(service.list_tasks()) == 1

    running, messages, _ = invoke(service, "done", ["1"])
    assert running is True
    assert "Задача 1 выполнена" in messages
    assert service.get_task(1).is_done is True
    _, messages, _ = invoke(service, "stats") #_ — обычная переменная: ей сначала присваивается первое значение, а затем третье, но оба значения не используются.
    assert "Выполнено: 1" in messages

    running, messages, _ = invoke(service, "delete", ["1"])
    assert running is True
    assert "Задача удалена" in messages
    assert service.list_tasks() == []

    running, messages, _ = invoke(service, "surprise")
    assert running is True
    assert messages == ["Неизвестная команда"]
    assert service.list_tasks() == []

    running, messages, _ = invoke(service, "exit")
    assert running is False
    assert messages == ["Работу завершили"]


#обёртка над хранилищем, которая записывает вызовы load и save.
class ObservedStorage:
    def __init__(self, inner): #принимает исходное хранилище.
        self.inner = inner # сохраняет его
        self.events = [] # cоздаёт список событий

    #добавляет "load" в список событий
    def load(self):
        self.events.append("load") 
        return self.inner.load() #вызывает метод загрузки исходного хранилища.

    def save(self, tasks):
        self.events.append("save")
        return self.inner.save(tasks)


def test_observer_delegates_without_second_storage():
    inner = MemoryStorage() # создаёт исходное хранилище в памяти.
    observed = ObservedStorage(inner)  #оборачивает его в наблюдаемое хранилище.
    service = PlannerService(observed) #передаёт обёртку сервису
    assert service.storage is observed # проверяет, что сервис хранит именно тот же объект обёртки.
    running, messages, _ = invoke(service, "add", ["Проверка", "4"])

    assert running is True
    assert "Проверка" in " ".join(messages)
    assert observed.events == ["load", "save"] # проверяет вызовы загрузки и сохранения в этом порядке.
    assert [(task.id, task.title, task.priority)
            for task in inner.load()] == [(1, "Проверка", 4)] 
    # загружает задачи напрямую из inner, формирует кортежи из ID, названия и приоритета и сравнивает их с [(1, "Проверка", 4)].


#Тест проверяет, когда вызывается сохранение: при изменении данных оно происходит, 
# а при чтении, ошибках и повторном выполнении задачи — нет
def test_no_save_on_reads_errors_and_repeated_done():
    observed = ObservedStorage(MemoryStorage()) #cоздаёт хранилище, записывающее вызовы load и save.
    service = PlannerService(observed) # передаёт его сервису
    invoke(service, "add", ["Задача", "2"]) # добавляет задачу
    assert observed.events.count("save") == 1 # подтверждает один вызов save.

    #задаёт команды, ответы и ожидаемые фрагменты сообщений для чтения и ошибочных запросов.
    read_cases = [
        ("list", [], "Задача"),
        ("find", ["1"], "Задача"),
        ("search", ["зада"], "Задача"),
        ("stats", [], "Всего: 1"),
        ("find", ["abc", "-1", "404"], "Задача не найдена"),
        ("search", ["  "], "Введите непустой фрагмент"),
        ("search", ["несуществующее"], "Совпадений не найдено"),
        ("delete", ["404"], "Задача не найдена"),
    ]
    for command, answers, expected in read_cases:
        observed.events.clear() # очищает историю вызовов
        running, messages, _ = invoke(service, command, answers)
        assert running is True
        assert expected in " ".join(messages)
        assert observed.events.count("save") == 0 #проверяет, что во время сценария не было вызовов сохранения.

    observed.events.clear()
    invoke(service, "done", ["1"])
    assert observed.events.count("save") == 1
    assert service.get_task(1).is_done is True # проверяет, что признак выполнения задачи равен True.

    observed.events.clear()
    running, messages, _ = invoke(service, "done", ["1"])
    assert running is True
    assert "Задача 1 выполнена" in messages
    assert observed.events.count("save") == 0
    assert service.get_task(1).is_done is True

# имитирует ошибки хранилища при загрузке или сохранении.
class FailingStorage:
    def __init__(self, failure, error): # принимает имя операции и объект исключения.
        self.failure = failure
        self.error = error

    def load(self):
        if self.failure == "load": # проверяет значение failure: если это "load", инструкция raise выбрасывает заданное исключение.
            raise self.error
        return []# иначе возвращает пустой список задач.

#save ничего не сохраняет и неявно возвращает None
    def save(self, tasks):
        if self.failure == "save":
            raise self.error

#задаёт два набора параметров для одного теста
@pytest.mark.parametrize(
    "command, answers, failure", #В каждом запуске значения передаются тестовой функции через параметры command, answers и failure.
    #Тест будет запущен дважды: для команды list с ошибкой загрузки и для add с ошибкой сохранения.
    [
        ("list", [], "load"),
        ("add", ["Новая задача", "2"], "save"),
    ],
)


def test_storage_failure_never_prints_success(command, answers, failure):
    #создаёт хранилище, которое выбросит StorageError для указанной операции.
    storage = FailingStorage(failure, StorageError("диск недоступен"))
    service = PlannerService(storage) #создаёт сервис с этим хранилищем.
    pending = iter(answers) # создаёт итератор подготовленных ответов.
    messages = []
    # проверяет, что внутри блока возникнет StorageError с подходящим текстом.
    with pytest.raises(StorageError, match="диск недоступен"):
        execute_command( #начинает вызов функции выполнения команды
            service, command, #передаёт функции сервис и имя команды.
            read=lambda _prompt: next(pending), #подменяет ввод: вместо чтения от пользователя возвращается следующий подготовленный ответ.
            write=lambda message: messages.append(str(message)),#подменяет вывод: сообщение преобразуется в строку и добавляется в список.
        )
    assert messages == [] # проверяет, что не было выведено ни одного сообщения, в том числе сообщения об успехе.


def test_unexpected_bug_is_not_masked_as_storage_error():
    service = PlannerService(
        FailingStorage("load", RuntimeError("ошибка в программе")) # создаёт хранилище, которое при загрузке выбросит RuntimeError с заданным сообщением.
    )
    with pytest.raises(RuntimeError, match="ошибка в программе"): # проверяет, что внутри блока возникнет RuntimeError с указанным текстом.
        execute_command(service, "list", write=lambda _: None)# выполняет команду списка задач; функция write игнорирует вывод.



class EmptyObserved(ObservedStorage):
    def __len__(self): #Метод __len__ возвращает 0, поэтому экземпляр считается пустым и приводится к False в логических проверках.
        return 0


def test_build_preserves_falsy_injected_storage():
    injected = EmptyObserved(MemoryStorage()) #создаёт обёртку, которая из-за __len__ приводится к False.
    service = build_service(injected)
    assert service.storage is injected # проверяет идентичность объектов: фабрика не заменила хранилище.
    assert injected.events == [] #проверяет, что при создании сервиса вызовов хранилища не было.
    invoke(service, "add", ["Подключено", "1"]) # добавляет задачу через сервис.
    assert injected.events == ["load", "save"] # подтверждает, что сервис вызвал загрузку и сохранение именно через переданную обёртку.


def test_default_build_does_not_read_or_write(tmp_path, monkeypatch):
    path = tmp_path / "tasks.json"
    path.write_text("{ некорректный JSON", encoding="utf-8") # записывает в файл некорректный JSON.
    before = path.read_bytes()
    monkeypatch.setattr(entry, "DATA_PATH", path) # временно заменяет entry.DATA_PATH на этот путь.

    service = entry.build_service()
    assert isinstance(service.storage, JsonStorage) #проверяет, что используется JsonStorage.
    assert service.storage.path == path # проверяет путь хранилища.
    assert path.read_bytes() == before # подтверждает, что содержимое файла не изменилось.

# проверяет, что импорт модуля завершается успешно и не выводит сообщений
def test_import_does_not_start_cli():
    project_root = Path(__file__).resolve().parents[1] # определяет корневой каталог проекта относительно файла теста.
    result = subprocess.run( #запускает отдельный процесс и сохраняет результат в result.
        [sys.executable, "-c", "import app.main"], # запускает текущий интерпретатор Python и импортирует app.main.
        cwd=project_root, #задаёт рабочий каталог процесса.
        input="", capture_output=True, text=True, #capture_output=True перехватывает вывод
        timeout=5, check=False, # ограничивает ожидание пятью секундами, а check=False не выбрасывает исключение при ненулевом коде завершения.
    )
    assert result.returncode == 0, result.stderr #проверяет успешное завершение процесса
    assert result.stdout == "" # проверяет, что стандартный вывод пуст.
    assert result.stderr == ""# проверяет, что поток ошибок пуст.

def test_read_only_does_not_save():
    observed = ObservedStorage(MemoryStorage())
    service = PlannerService(observed)
    running, messages, _ = invoke(service, "list")
    saves = observed.events.count("save")
    assert running is True
    assert "Список задач пока пуст." in messages
    assert saves == 0  # Для красного прогона ВРЕМЕННО замените 0 на 1.

# Для smoke в интерактивной Python-консоли из корня StudyHub
# вызовите smoke_cli_in_temp_file(). При импорте pytest он не запускается.
def smoke_cli_in_temp_file():
    with TemporaryDirectory() as directory:
        storage = JsonStorage(Path(directory) / "tasks.json")
        run(build_service(storage))
    # Во время работы введите: add → название → 2 → list → done → 1 → exit.


