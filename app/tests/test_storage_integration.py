from tempfile import TemporaryDirectory
from app.services import PlannerService
from app.storage import CountingMemoryStorage,JsonStorage
from pathlib import Path
import json
import pytest
from app.errors import StorageError



memory = CountingMemoryStorage()
service = PlannerService(memory)
task = service.add_task("Проверить запись", 2)
assert memory.saves == 1

with TemporaryDirectory() as folder:
    path = Path(folder) / "tasks.json"
    PlannerService(JsonStorage(path)).add_task("Восстановить", 3)
    reopened = PlannerService(JsonStorage(path))
    assert reopened.get_task(1).title == "восстановить"



#проверяет загрузку отсутствующего файла
def test_missing_file_starts_empty(tmp_path):
    path = tmp_path / "tasks.json" #формирует путь к файлу.
    assert not path.exists()

    #создаёт хранилище и загружает задачи
    tasks = JsonStorage(path).load()
    #проверяет, что результат — пустой список
    assert tasks == []
    assert not path.exists() #проверяет, что загрузка не создала файл.



def test_legacy_record_has_independent_tags(tmp_path):
    path = tmp_path / "legacy.json"
    records = [
        {"id": 3, "title": "Позвонить", "priority": 2, "is_done": False},
        {"id": 8, "title": "Занятие", "priority": 1, "is_done": True},
    ]
    path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    first, second = JsonStorage(path).load()
    assert (first.id, first.title, first.priority, first.is_done) == (3, "Позвонить", 2, False)
    assert (second.id, second.title, second.priority, second.is_done) == (8, "Занятие", 1, True)
    assert first.tags == []
    assert second.tags == []
    first.tags.append("новая")
    assert second.tags == []


def test_legacy_record_without_id_is_invalid(tmp_path):
    path = tmp_path / "missing-id.json"
    path.write_text('[{"title": "Без id", "priority": 2, "is_done": false}]', encoding="utf-8")

    with pytest.raises(StorageError):
        JsonStorage(path).load()


@pytest.mark.parametrize("content", [
    "{сломано",
    "",
    '[{"title": "Без id", "priority": 2, "is_done": false}]',
    '[{"id": 3, "title": "Статус", "priority": 2, "is_done": "false", "tags": []}]',
    '[{"id": 3, "title": "Метки", "priority": 2, "is_done": false, "tags": null}]',
    '[{"id": 3, "title": "Первая", "priority": 2, "is_done": false}, {"id": 3, "title": "Вторая", "priority": 1, "is_done": true}]',
    '{"id": 3, "title": "Не список", "priority": 2, "is_done": false}',
])

#проверяет, что при ошибке загрузки файл не изменяется
def test_invalid_json_is_not_replaced(tmp_path, content):
    path = tmp_path / "tasks.json"
    path.write_text(content, encoding="utf-8")
    before = path.read_bytes()

    with pytest.raises(StorageError):
        JsonStorage(path).load() #проверяет, что load() выбрасывает StorageError.

    assert path.read_bytes() == before 


def test_directory_cannot_be_read_as_file(tmp_path):
    path = tmp_path / "tasks.json"
    path.mkdir()#создаёт по этому пути каталог

    with pytest.raises(StorageError):
        JsonStorage(path).load()

    assert path.is_dir() # проверяет, что после ошибки путь по-прежнему является каталогом.