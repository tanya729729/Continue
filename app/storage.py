import json
import os
import tempfile
from pathlib import Path

from app.errors import StorageError
from app.validators import validate_snapshot
from app.models import Task


#json.dumps(tasks, ...) — преобразует данные в строку JSON.
#ensure_ascii=False — сохраняет русские буквы в читаемом виде.
#indent=2 — добавляет отступы в 2 пробела.
def encode_tasks(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)

# принимает строку с JSON, преобразует её в объекты Python, например список и словари.
def decode_tasks(text):
    return json.loads(text)

def validate_loaded_tasks(tasks):
    return validate_snapshot(tasks)


def load_tasks(path): #принимает путь к файлу.
    path = Path(path) #преобразует путь в объект Path.
    try:
        file = path.open("r", encoding="utf-8") #открывает файл для чтения в кодировке UTF-8.
    except FileNotFoundError: # обрабатывает отсутствие файла.
        return []
    except OSError as error:
        # сообщает об ошибке хранилища
        raise StorageError(f"Не удалось открыть файл: {path}") from error

    try:
        with file:
            text = file.read()
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось прочитать файл: {path}") from error

    try:
        tasks = decode_tasks(text)
    except json.JSONDecodeError as error: #перехватывает ошибку некорректного JSON.
        raise StorageError(f"Некорректный JSON: {path}") from error

    try:
        return validate_loaded_tasks(tasks)
    except ValueError as error:
        raise StorageError(f"Некорректная структура задач: {path}") from error


def save_tasks(path, tasks):
    path = Path(path)
    try:
        validate_loaded_tasks(tasks)
    except ValueError as error:
        raise StorageError("Некорректные данные для сохранения") from error

    try:
        text = encode_tasks(tasks)
    except (TypeError, ValueError) as error:
        raise StorageError("Не удалось сериализовать задачи") from error

    temp_path = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)# создаёт родительскую и недостающие промежуточные папки.
        with tempfile.NamedTemporaryFile( # создаёт временный файл в папке целевого файла
            mode="w", encoding="utf-8", dir=path.parent, delete=False #оставляет файл после закрытия, чтобы его можно было переместить.
        ) as file: #открывает его для записи текста в UTF-8.
            temp_path = Path(file.name) #запоминает путь временного файла.
            file.write(text)
            file.flush() #передаёт данные из буфера Python операционной системе.
            os.fsync(file.fileno()) #запрашивает сохранение данных файла на носителе.
        os.replace(temp_path, path) # заменяет целевой файл временным.
        temp_path = None # отмечает, что временный файл перемещён.
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось сохранить файл: {path}") from error
    finally:
        if temp_path is not None: #проверяет, нужно ли удалить временный файл
            try:
                temp_path.unlink(missing_ok=True) #удаляет его, не считая отсутствие файла ошибкой.
            except OSError:
                pass # игнорирует ошибку очистки, чтобы не скрыть основную ошибку.

       
def replace_task(self, task_id, *, title, priority, is_done):
    tasks = self.storage.load()
    current = self._find_task(tasks, task_id)
    index = tasks.index(current)
    updated = Task(
        id=current.id,
        title=title,
        priority=priority,
        is_done=is_done,
        tags=current.tags.copy(),
    )
    tasks[index] = updated
    self.storage.save(tasks)
    return updated

# сохраняет задачи в JSON-файле и восстанавливает их как объекты Task
class JsonStorage:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)  # сохраняет путь в объекте

    def load(self) -> list[Task]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError) as error:
            raise StorageError("Не удалось прочитать задачи") from error

        try:
            records = json.loads(text) #преобразует текст JSON в объекты Python.
            validate_loaded_tasks(records)
            return [Task.from_dict(record) for record in records] #создаёт задачу из каждой записи и возвращает список.
        except (ValueError, TypeError) as error:
            raise StorageError("Неверный JSON или структура задач") from error

    def save(self, tasks: list[Task]) -> None: # принимает список задач и не возвращает результат.
        try:
            records = [task.to_dict() for task in tasks] #преобразует каждую задачу в словарь
        except (AttributeError, TypeError, ValueError) as error: #перехватывает указанные ошибки преобразования.
            raise StorageError("Неверный список задач") from error 
        save_tasks(self.path, records) #передаёт путь и записи функции сохранения.

# хранит задачи в памяти и копирует список при загрузке и сохранении.
class MemoryStorage:
    def __init__(self, tasks=None): #принимает необязательный список задач.
        self._tasks = list(tasks) if tasks is not None else [] # создаёт копию переданной коллекции или пустой список.

    def load(self):
        return list(self._tasks) #возвращает копию списка задач.

    def save(self, tasks):
        self._tasks = list(tasks) #заменяет хранимый список копией переданной коллекции.

#оборачивает хранилище и считает вызовы сохранения.
class SaveCounter:
    def __init__(self, storage): #принимает исходное хранилище.
        self.storage = storage #сохраняет ссылку на него.
        self.save_calls = 0 #создаёт счётчик вызовов.

    def load(self): #объявляет метод загрузки
        return self.storage.load() 

    def save(self, tasks):
        self.save_calls += 1
        return self.storage.save(tasks) #вызывает сохранение у хранилища и возвращает его результат.



#создаёт класс, который наследуется от MemoryStorage.
# определяет инициализацию нового объекта.
# вызывает инициализацию родительского класса.
class CountingMemoryStorage(MemoryStorage):
    def __init__(self):
        super().__init__()
        self.saves = 0 # создаёт счётчик сохранений с начальным значением 0.

    def save(self, tasks): #переопределяет метод сохранения и принимает задачи.
        self.saves += 1 #увеличивает счётчик на 1 при каждом вызове.
        super().save(tasks) #вызывает метод родительского класса, который сохраняет задачи.


