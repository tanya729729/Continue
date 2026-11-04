from tempfile import TemporaryDirectory
from app.services import PlannerService
from app.storage import CountingMemoryStorage,JsonStorage
from pathlib import Path

memory = CountingMemoryStorage()
service = PlannerService(memory)
task = service.add_task("Проверить запись", 2)
assert memory.saves == 1

with TemporaryDirectory() as folder:
    path = Path(folder) / "tasks.json"
    PlannerService(JsonStorage(path)).add_task("Восстановить", 3)
    reopened = PlannerService(JsonStorage(path))
    assert reopened.get_task(1).title == "восстановить"