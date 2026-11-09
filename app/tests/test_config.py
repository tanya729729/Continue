import pytest
from app.core.config import load_settings
from app.main import build_service
from app.storage import JsonStorage

def test_relative_path_is_stable_across_working_directories(tmp_path, monkeypatch):
    first_cwd = tmp_path / "first"
    second_cwd = tmp_path / "second"
    first_cwd.mkdir()
    second_cwd.mkdir()
    monkeypatch.chdir(first_cwd)
    first = load_settings({}, project_root=tmp_path)
    monkeypatch.chdir(second_cwd)
    second = load_settings({}, project_root=tmp_path)
    expected = (tmp_path / "data" / "tasks.json").resolve()
    assert first.json_path == expected
    assert second.json_path == expected
    assert first.app_name == "StudyHub Planner"


@pytest.mark.parametrize(
    ("environ", "key"),
    [({"JSON_PATH": "  "}, "JSON_PATH"), ({"APP_NAME": ""}, "APP_NAME")],

)

def test_explicit_empty_values_are_rejected(tmp_path, environ, key):
    with pytest.raises(ValueError, match=key):
        load_settings(environ, project_root=tmp_path)


def test_absolute_path_is_not_rebased(tmp_path):
    absolute = (tmp_path / "external.json").resolve()
    settings = load_settings(
        {"JSON_PATH": str(absolute)},
        project_root=tmp_path / "other",
    )
    assert settings.json_path == absolute


def test_directory_is_not_a_json_file(tmp_path):
    directory = tmp_path / "tasks"
    directory.mkdir()
    with pytest.raises(ValueError, match="JSON_PATH"):
        load_settings({"JSON_PATH": str(directory)}, project_root=tmp_path)


def test_build_service_keeps_injected_storage(tmp_path):
    storage = JsonStorage(tmp_path / "tasks.json")
    service = build_service(storage)
    assert service.storage is storage

def test_process_value_wins_over_env_file(monkeypatch, tmp_path):
    env_file = tmp_path / '.env'
    env_file.write_text(f'JSON_PATH={tmp_path / "from_file.json"}\n', encoding='utf-8')
    process_path = tmp_path / 'from_process.json'
    monkeypatch.setattr(config, 'ENV_FILE', env_file)
    monkeypatch.setenv('JSON_PATH', str(process_path))

    assert config.get_json_path() == process_path