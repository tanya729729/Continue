from app.cli import execute_command
from app.services import PlannerService
from app.storage import MemoryStorage
import pytest
from app.errors import StorageError
from pathlib import Path
import subprocess
import sys
import app.main as entry
from app.main import build_service
from app.storage import JsonStorage

def invoke(service, command, answers=()):
    pending = list(answers)
    prompts = []
    messages = []

    def read(prompt):
        prompts.append(prompt)
        return pending.pop(0)

    running = execute_command(
        service, command, read=read,
        write=lambda message: messages.append(str(message)),
    )
    assert pending == []  # Тест задал ровно нужные ответы.
    return running, messages, prompts


def test_add_retries_bad_input():
    service = PlannerService(MemoryStorage())
    running, messages, prompts = invoke(
        service, " ADD ", ["   ", "Учить pytest", "слово", "8", "3"]
    )

    assert running is True
    assert len(prompts) == 5
    assert "Название не может быть пустым" in messages
    assert "Введите целое число" in messages
    assert "Приоритет должен быть от 1 до 5" in messages
    tasks = service.list_tasks()
    assert len(tasks) == 1
    assert (tasks[0].id, tasks[0].title, tasks[0].priority) == (
        1, "Учить pytest", 3
    )
    assert tasks[0].is_done is False
    assert "Учить pytest" in messages[-1]

def test_all_commands_and_unknown_route():
    service = PlannerService(MemoryStorage())
    running, messages, _ = invoke(service, "add", ["Ревью", "2"])
    assert running is True
    assert "[1] Ревью" in " ".join(messages)

    cases = [
        ("list", [], "Ревью"),
        ("find", ["1"], "Ревью"),
        ("search", ["ВЬЮ"], "Ревью"),
        ("stats", [], "Всего: 1"),
    ]
    for command, answers, expected in cases:
        running, messages, _ = invoke(service, command, answers)
        assert running is True
        assert expected in " ".join(messages)
        assert len(service.list_tasks()) == 1

    running, messages, _ = invoke(service, "done", ["1"])
    assert running is True
    assert "Задача 1 выполнена" in messages
    assert service.get_task(1).is_done is True
    _, messages, _ = invoke(service, "stats")
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


class ObservedStorage:
    def __init__(self, inner):
        self.inner = inner
        self.events = []

    def load(self):
        self.events.append("load")
        return self.inner.load()

    def save(self, tasks):
        self.events.append("save")
        return self.inner.save(tasks)


def test_observer_delegates_without_second_storage():
    inner = MemoryStorage()
    observed = ObservedStorage(inner)
    service = PlannerService(observed)
    assert service.storage is observed
    running, messages, _ = invoke(service, "add", ["Проверка", "4"])

    assert running is True
    assert "Проверка" in " ".join(messages)
    assert observed.events == ["load", "save"]
    assert [(task.id, task.title, task.priority)
            for task in inner.load()] == [(1, "Проверка", 4)]

def test_no_save_on_reads_errors_and_repeated_done():
    observed = ObservedStorage(MemoryStorage())
    service = PlannerService(observed)
    invoke(service, "add", ["Задача", "2"])
    assert observed.events.count("save") == 1

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
        observed.events.clear()
        running, messages, _ = invoke(service, command, answers)
        assert running is True
        assert expected in " ".join(messages)
        assert observed.events.count("save") == 0

    observed.events.clear()
    invoke(service, "done", ["1"])
    assert observed.events.count("save") == 1
    assert service.get_task(1).is_done is True

    observed.events.clear()
    running, messages, _ = invoke(service, "done", ["1"])
    assert running is True
    assert "Задача 1 выполнена" in messages
    assert observed.events.count("save") == 0
    assert service.get_task(1).is_done is True




class FailingStorage:
    def __init__(self, failure, error):
        self.failure = failure
        self.error = error

    def load(self):
        if self.failure == "load":
            raise self.error
        return []

    def save(self, tasks):
        if self.failure == "save":
            raise self.error


@pytest.mark.parametrize(
    "command, answers, failure",
    [
        ("list", [], "load"),
        ("add", ["Новая задача", "2"], "save"),
    ],
)
def test_storage_failure_never_prints_success(command, answers, failure):
    storage = FailingStorage(failure, StorageError("диск недоступен"))
    service = PlannerService(storage)
    pending = iter(answers)
    messages = []
    with pytest.raises(StorageError, match="диск недоступен"):
        execute_command(
            service, command,
            read=lambda _prompt: next(pending),
            write=lambda message: messages.append(str(message)),
        )
    assert messages == []


def test_unexpected_bug_is_not_masked_as_storage_error():
    service = PlannerService(
        FailingStorage("load", RuntimeError("ошибка в программе"))
    )
    with pytest.raises(RuntimeError, match="ошибка в программе"):
        execute_command(service, "list", write=lambda _: None)




class EmptyObserved(ObservedStorage):
    def __len__(self):
        return 0


def test_build_preserves_falsy_injected_storage():
    injected = EmptyObserved(MemoryStorage())
    service = build_service(injected)
    assert service.storage is injected
    assert injected.events == []
    invoke(service, "add", ["Подключено", "1"])
    assert injected.events == ["load", "save"]


def test_default_build_does_not_read_or_write(tmp_path, monkeypatch):
    path = tmp_path / "tasks.json"
    path.write_text("{ некорректный JSON", encoding="utf-8")
    before = path.read_bytes()
    monkeypatch.setattr(entry, "DATA_PATH", path)

    service = entry.build_service()
    assert isinstance(service.storage, JsonStorage)
    assert service.storage.path == path
    assert path.read_bytes() == before


def test_import_does_not_start_cli():
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=project_root,
        input="", capture_output=True, text=True,
        timeout=5, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""

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
    from tempfile import TemporaryDirectory
    from pathlib import Path
    from app.cli import run
    from app.main import build_service
    from app.storage import JsonStorage

    with TemporaryDirectory() as directory:
        storage = JsonStorage(Path(directory) / "tasks.json")
        run(build_service(storage))
    # Во время работы введите: add → название → 2 → list → done → 1 → exit.


