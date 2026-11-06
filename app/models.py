
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

#@dataclass автоматически создаёт конструктор и другие стандартные методы.
@dataclass
class Task:
    id: int
    title: str
    priority: int = 2
    is_done: bool = False
    tags: list[str] = field(default_factory=list) # создаёт отдельный список тегов для каждой задачи.

    # вызывается после конструктора и проверяет поля
    def __post_init__(self) -> None:
        self.id = validate_task_id(self.id)
        self.title = validate_title(self.title)
        self.priority = validate_priority(self.priority)

        # неверный is_done вызывает ValueError
        if type(self.is_done) is not bool:
            raise ValueError("is_done должен быть bool")

        self.tags = validate_tags(self.tags) #сохраняет результат в поле задачи self.tags.

 #отмечает задачу выполненной, метод не возвращает полезного значения.
 #self — ссылка на конкретный объект, у которого вызывают метод.
#Через self.is_done метод изменяет статус именно этой задачи.
#каждый экземпляр Task — отдельный объект со своими значениями полей
    def mark_done(self) -> None:
        self.is_done = True

    #передаёт new_title в validate_title и записывает результат в self.title текущего объекта.
    def rename(self, new_title: str) -> None:
        self.title = validate_title(new_title)

    def set_priority(self, new_priority: int) -> None:
        self.priority = validate_priority(new_priority)

    #@property делает метод свойством: к нему обращаются как к атрибуту, без скобок.
    #@property нужен, когда значение удобно получать как обычное поле, но для его вычисления требуется метод.
    @property
    def status_label(self) -> str: # объявляет метод, который получает текущий объект и возвращает строку.
        if self.is_done: # проверяет, выполнена ли задача.
            return "выполнена"
        return "не завершена"

    # определяет строковое представление объекта, которое используется при вызове str() или print().
    #Первая строка добавляет id и название задачи.
    def __str__(self) -> str:
        return (
            f"[{self.id}] {self.title} | "
            f"приоритет: {self.priority} | "
            f"{self.status_label}"
        )

    #Метод преобразует объект в словарь.
    #записывает в словарь соответствующие поля объекта.
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "is_done": self.is_done,
            "tags": list(self.tags), 
        }

    #объявляет метод класса: вместо объекта первым аргументом он получает класс.
    #С @classmethod метод получает класс автоматически через cls, поэтому при вызове через подкласс создаст объект подкласса.
    #@classmethod позволяет вызвать from_dict у самого класса
    #@classmethod удобен, когда нужно создать объект не обычным способом, а из заранее подготовленных данных.
    #cls позволяет использовать тот же метод и в подклассе: он создаст объект именно того класса, через который вызван метод.
    @classmethod
    def from_dict(cls, record): #объявляет метод с аргументами  класс и  данные записи.
        if not isinstance(record, dict): #проверяет, что record не является словарём.
            raise ValueError(
                "Запись задачи должна быть словарём"
            )

        old_fields = {
            "id", "title", "priority", "is_done"
        }

        fields = set(record) #собирает ключи словаря record в множество.

        if fields == old_fields:
            tags = [] #задаёт пустой список тегов для старой записи.
        elif fields == old_fields | {"tags"}: #объединение множеств: все старые поля плюс tags.
            tags = record["tags"] # получает значение тегов из словаря.
        else: #отклоняют запись, если набор полей не совпадает ни с одним из форматов.
            raise ValueError("Неверный набор полей задачи")

        # создаёт и возвращает объект класса
        return cls( # ссылка на класс, переданная в метод через @classmethod.
            id=record["id"],
            title=record["title"],
            priority=record["priority"],
            is_done=record["is_done"],
            tags=tags,
        )






