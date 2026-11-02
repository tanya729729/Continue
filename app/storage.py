import json
import os
import tempfile
from pathlib import Path

from app.errors import StorageError
from app.validators import validate_snapshot


def encode_tasks(tasks):
    return json.dumps(tasks, ensure_ascii=False, indent=2)


def decode_tasks(text):
    return json.loads(text)


def validate_loaded_tasks(tasks):
    return validate_snapshot(tasks)


def load_tasks(path):
    path = Path(path)
    try:
        file = path.open("r", encoding="utf-8")
    except FileNotFoundError:
        return []
    except OSError as error:
        raise StorageError(f"Не удалось открыть файл: {path}") from error

    try:
        with file:
            text = file.read()
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось прочитать файл: {path}") from error

    try:
        tasks = decode_tasks(text)
    except json.JSONDecodeError as error:
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
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temp_path = Path(file.name)
            file.write(text)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
        temp_path = None
    except (OSError, UnicodeError) as error:
        raise StorageError(f"Не удалось сохранить файл: {path}") from error
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
