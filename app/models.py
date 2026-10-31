
from dataclasses import dataclass, field
from app.validators import (
    validate_task_id,
    validate_title,
    validate_priority,
    validate_tags,
)


def create_task(task_id, title, priority=2):
    task_id = validate_task_id(task_id)
    title = validate_title(title)
    priority = validate_priority(priority)

    return {
        "id": task_id,
        "title": title,
        "priority": priority,
        "is_done": False,
    }


@dataclass
class Task:
    id: int
    title: str
    priority: int = 2
    is_done: bool = False
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.id = validate_task_id(self.id)
        self.title = validate_title(self.title)
        self.priority = validate_priority(self.priority)

        if type(self.is_done) is not bool:
            raise ValueError("is_done должен быть bool")

        self.tags = validate_tags(self.tags)

    def mark_done(self) -> None:
        self.is_done = True

    def rename(self, new_title: str) -> None:
        self.title = validate_title(new_title)

    def set_priority(self, new_priority: int) -> None:
        self.priority = validate_priority(new_priority)

    @property
    def status_label(self) -> str:
        if self.is_done:
            return "выполнена"
        return "не завершена"

    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.title} | "
            f"приоритет: {self.priority} | "
            f"{self.status_label}"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "is_done": self.is_done,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, record):
        if not isinstance(record, dict):
            raise ValueError(
                "Запись задачи должна быть словарём"
            )

        old_fields = {
            "id", "title", "priority", "is_done"
        }

        fields = set(record)

        if fields == old_fields:
            tags = []
        elif fields == old_fields | {"tags"}:
            tags = record["tags"]
        else:
            raise ValueError("Неверный набор полей задачи")

        return cls(
            id=record["id"],
            title=record["title"],
            priority=record["priority"],
            is_done=record["is_done"],
            tags=tags,
        )



