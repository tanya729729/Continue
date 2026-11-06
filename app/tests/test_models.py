from app.models import Task
from app.storage import MemoryStorage,JsonStorage
import pytest
from app.errors import TaskNotFoundError
from app.services import PlannerService

#проверка,что задача "прочитать главу" еще не выполнена
def test_task_normalizes_my_title():
    task = Task(1, "  Прочитать главу  ", priority=3)

    assert task.title == "прочитать главу"
    assert task.is_done is False

#проверка мин и макс приоритетов
def test_priority_boundaries():
    assert Task(1, "A", priority=1).priority == 1
    assert Task(2, "B", priority=5).priority == 5

#проверяет, что конструктор Task корректно отклоняет неверные аргументы, генерируя ValueError.
def test_invalid_values():
    with pytest.raises(ValueError):
        # попытка создать задачу с приоритетом 0, ниже допустимого минимума
        Task(1, "A", priority=0)
    #контекст‑менеджер из библиотеки pytest, ожидающий, что внутри будет исключение 
    with pytest.raises(ValueError):
        Task(1, "A", priority=6)
    #задаётся идентификатор 0, который считается недопустимым 
    with pytest.raises(ValueError):
        Task(0, "A", priority=3)
    with pytest.raises(ValueError):
        Task(1, "   ", priority=3)

#проверка,что у разных экземпляров Task нет общей mutable‑состояния.
def test_tasks_do_not_share_tags_or_done():
    first = Task(1, "A")
    second = Task(2, "B")
    # к списку tags первой задачи добавляется строка "study"
    first.tags.append("study")
    #вызывается метод, помечающий первую задачу выполненной
    first.mark_done()
    #проверяется, что у второй задачи список tags остался пустым
    assert second.tags == []
    assert first.is_done is True
    #проверка, что вторая задача не помечена как выполненная
    assert second.is_done is False


#проверка, что при неудачной переименовке заголовок задачи остаётся неизменным
def test_failed_rename_keeps_title():
    task = Task(1, "Old")
    with pytest.raises(ValueError):
        #попытка переименовать задачу в строку, содержащую только пробелы; метод rename должен бросить ValueError
        task.rename("   ")
    assert task.title == "old"

#проверка,что MemoryStorage создаёт собственную копию передаваемого контейнера и не зависит от дальнейших внешних изменений
def test_init_and_load_copy_the_container():
    task = Task(1, "Python")
    #формируется список, содержащий единственную задачу
    incoming = [task]
    #сохраняет содержимое в собственном внутреннем контейнере (обычно делая копию)
    storage = MemoryStorage(incoming)
    # очищаем исходный список incoming; если MemoryStorage вёл бы прямую ссылку, его содержимое сразу бы исчезло.
    incoming.clear()
    #возвращает список из хранилища
    outside = storage.load()
    # убедимся, что load() возвращает копию, а не ссылку на внутренний контейнер.
    outside.clear()
    #проверяем, что внутри хранилища всё ещё находится оригинальная задача, независимо от очистки incoming и outside.
    assert storage.load() == [task]

# проверка,что метод save в MemoryStorage делает копию передаваемого списка, а не сохраняет ссылку на него.
def test_save_copies_the_container():
    task = Task(1, "Python")
    source = [task]
    storage = MemoryStorage()
    # вызывается метод save, который должен скопировать содержимое source в внутреннее хранилище.
    storage.save(source)
    # очищаем исходный список source,данные в хранилище не исчезли, потому что скопировано содержимое, а не ссылка
    source.clear()
    #проверяем, что внутри хранилища всё ещё находится оригинальная задача, доказательство того, что при save была сделана копия, а не ссылка.
    assert storage.load() == [task]

#проверка, что MemoryStorage.load() возвращает тот же объект Task, а не его копию
def test_load_shares_task_references():
    task = Task(1, "Python")
    #инициализируется хранилище, получив список, содержащий только эту задачу
    storage = MemoryStorage([task])
    # вызывается load и возвращается ссылка на внутренний список задач
    outside = storage.load()
    #через полученную ссылку помечаем первую задачу выполненной
    outside[0].mark_done()
    #повторный вызов load должен увидеть то же самое состояние задачи, то есть задача уже отмечена как выполненная.
    assert storage.load()[0].is_done is True

#проверка основные операции сервиса PlannerService при работе с задачами
#функция‑теста без параметров
def test_add_list_and_get():
    #создаётся объект PlannerService, которому передаётся пустое хранилище MemoryStorage
    service = PlannerService(MemoryStorage())
    #метод должен создать новый объект Task, удалить лишние пробелы и нормализовать заголовок.
    created = service.add_task("  Python  ", priority=3)
    #проверяется, что идентификатор первой созданной задачи равен 1
    assert created.id == 1
    #проверяется заголовок задачи после нормализации
    assert created.title == "Python"
    #проверяется, что новая задача по умолчанию не помечена выполненной
    assert created.is_done is False
    #проверяется, что метод list_tasks возвращает список, содержащий единственную только что созданную задачу
    assert service.list_tasks() == [created]
    #проверяется, что по идентификатору 1 метод get_task возвращает ту же задачу, подтверждая корректную работу поиска по id.
    assert service.get_task(1) == created

# проверяет работу поиска задач 
def test_search_and_empty_search():
    service = PlannerService(MemoryStorage())
    # добавляется задача с заголовком "Read Python"; метод возвращает созданный объект Task
    task = service.add_task("Read Python")
    #вызывается поиск по строке. Ожидается список, содержащий  task, так как её заголовок содержит слово Python
    assert service.search_tasks("PYTHON") == [task]
    assert service.search_tasks("nothing") == []

def test_done_and_statistics():
    service = PlannerService(MemoryStorage())
    created = service.add_task("Write tests")
    #проверяется, что сервис считает 1 задачу в целом, 1 открытую и 0 выполненных
    assert service.get_statistics() == {"all": 1, "open": 1, "done": 0}
    service.mark_done(created.id)
    #повторный вызов, который не должен изменить состояние или вызвать ошибку
    service.mark_done(created.id)
    #проверяется, что первая (и единственная) задача теперь помечена как выполненная
    assert service.list_tasks()[0].is_done is True
    #убеждаемся, что количество задач в сервисе осталось 1
    assert len(service.list_tasks()) == 1
    #проверяем обновлённую статистику: 1 задача всего, 0 открытых, 1 выполненная
    assert service.get_statistics() == {"all": 1, "open": 0, "done": 1}

def test_delete_keeps_other_id():
    service = PlannerService(MemoryStorage())
    first = service.add_task("A")
    second = service.add_task("B")
    service.delete_task(first.id)
    #проверяется, что после удаления в сервисе осталась единственная задача с id = 2
    assert [task.id for task in service.list_tasks()] == [second.id]
    #подтверждается, что у оставшейся задачи заголовок остаётся "B", то есть данные не затронуты
    assert service.get_task(second.id).title == "B"

#проверка, что при возникновении исключений состояние сервиса не изменяется.
def test_errors_do_not_change_state():
    service = PlannerService(MemoryStorage())
    created = service.add_task("A",1)
    with pytest.raises(TaskNotFoundError):
        #попытка получить задачу с несуществующим id = 999; должна вызвать TaskNotFoundError
        service.get_task(999)
    with pytest.raises(ValueError):
        service.get_task(0)
    #после обработанных ошибок проверяется, что список задач сервиса остаётся неизменным
    assert service.list_tasks() == [created]

# создает хранилище в памяти для теста.
#создаёт MemoryStorage и передаёт его тестам, которым нужно хранилище.
#По умолчанию каждый тест получает отдельный экземпляр, что помогает сохранять независимость тестов.
@pytest.fixture
def memory_storage(): #объявляет функцию фикстурой
    return MemoryStorage() #возвращает новый экземпляр хранилища

#функция‑фикстура для для подготовки тестового окружения 
@pytest.fixture
def service(memory_storage):
    return PlannerService(memory_storage)


def test_add_task(service, memory_storage):
    created = service.add_task("Python", priority=3)

    assert created.title == "Python"
    assert [task.title for task in memory_storage.load()] == ["Python"]


#проверяет, что Task принимает граничные значения приоритета.
@pytest.mark.parametrize("priority", [1, 5])  #запускает тест дважды: для 1 и 5.
def test_task_accepts_priority_boundaries(priority):
    task = Task(1, "Python", priority=priority)
    assert task.priority == priority #проверяет, что созданная задача сохранила переданное значение.


@pytest.mark.parametrize("priority", [0, 6])#запускает тест отдельно для значений 0 и 6.
def test_task_rejects_priority_outside_range(priority):
    with pytest.raises(ValueError):
        Task(1, "Python", priority=priority)


@pytest.mark.parametrize("title", ["", "   "])
def test_task_rejects_blank_title(title):
    with pytest.raises(ValueError):# проверяет, что создание Task вызывает ValueError; если исключения нет, тест не проходит.
        Task(1, title)


@pytest.mark.parametrize(
    ("query", "expected_titles"),#имена параметров: поисковый запрос и ожидаемые названия задач.
    [("PYTHON", ["Python"]), ("ReAdMe", ["README"])], #две пары входных и ожидаемых значений.
)
#проверяет поиск без учёта регистра
def test_search_is_case_insensitive(service, query, expected_titles):
    service.add_task("Python")
    service.add_task("README")
    found = service.search_tasks(query) #выполняет поиск по текущему запросу.
    assert [task.title for task in found] == expected_titles #сравнивает список названий найденных задач с expected_titles; при несовпадении тест не проходит.

#проверяет состояние после ошибки поиска несуществующей задачи
def test_unknown_task_does_not_change_state(service):
    service.add_task("Python")
    before = [task.title for task in service.list_tasks()]

    with pytest.raises(TaskNotFoundError): #проверяет, что вызов service.get_task(99) выбрасывает TaskNotFoundError.
        service.get_task(99)

    assert [task.title for task in service.list_tasks()] == before #сравнивает текущий список названий с сохранённым.

# проверяет, что завершение одной задачи не меняет статус другой.
def test_mark_done_changes_only_the_selected_task(service):
    first = service.add_task("Python")
    second = service.add_task("Tests")

    service.mark_done(first.id)  #отмечает первую задачу выполненной

    assert service.get_task(first.id).is_done is True
    assert service.get_task(second.id).is_done is False

#проверяет независимость списков тегов у разных задач
def test_task_tags_are_independent():
    first = Task(1, "Python")
    second = Task(2, "Tests")
    first.tags.append("pytest")#добавляет тег в список первой задачи

    assert first.tags == ["pytest"]
    assert second.tags == [] #проверяет, что список второй задачи остался пустым.


#проверяет сохранение и восстановление задач через JSON-хранилище.
def test_round_trip_restores_tasks(tmp_path):
    path = tmp_path / "tasks.json"
    first = PlannerService(JsonStorage(path))
    created = first.add_task("Учёба: тесты", priority=4, tags=["pytest", "файлы"])
    other = first.add_task("Проверить схему", priority=2, tags=[])
    first.mark_done(created.id)

    # Новые объекты получают только общий путь к файлу.
    second = PlannerService(JsonStorage(path))
    restored = second.get_task(created.id)
    restored_other = second.get_task(other.id)

    assert restored.id == created.id
    assert restored.title == "Учёба: тесты"
    assert restored.priority == 4
    assert restored.is_done is True
    assert restored.tags == ["pytest", "файлы"]
    assert restored_other.id == other.id
    assert restored_other.title == "Проверить схему"
    assert restored_other.is_done is False

    assert [task.id for task in second.list_tasks()] == [created.id, other.id]# проверяет порядок идентификаторов восстановленных задач.
    assert [task.id for task in second.search_tasks("УЧЁБА")] == [created.id] #проверяет поиск восстановленной задачи
    assert second.get_statistics() == {"all": 2, "open": 1, "done": 1}#две задачи, одна открытая и одна выполнен

    later = second.add_task("После восстановления", priority=1)
    assert later.id == max(created.id, other.id) + 1 #проверяет, что  идентификатор новой задачи на единицу больше максимального среди прежних.