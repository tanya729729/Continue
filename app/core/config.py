from pathlib import Path
import os
from dotenv import load_dotenv
from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path



PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_PATH = Path("data/tasks.json")
DEFAULT_APP_NAME = "StudyHub Planner"


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JSON_PATH = PROJECT_ROOT / 'data' / 'tasks.json'
ENV_FILE = PROJECT_ROOT / '.env'


def get_json_path() -> Path:
    load_dotenv(dotenv_path=ENV_FILE, override=False)
    value = os.getenv('JSON_PATH')
    if value is None:
        return DEFAULT_JSON_PATH
    return Path(value)

@dataclass
class Settings:
    json_path: Path
    app_name: str


def load_settings(
    environ: Mapping[str, str] | None = None,
    project_root: Path = PROJECT_ROOT,
) -> Settings:

    values = os.environ if environ is None else environ



    raw_path = values.get("JSON_PATH")
    if raw_path is None:
        raw_path = str(DEFAULT_JSON_PATH)

    elif not raw_path.strip():
        raise ValueError("JSON_PATH must not be empty")



    json_path = Path(raw_path)
    if not json_path.is_absolute():
        json_path = (project_root / json_path).resolve()

    if json_path.exists() and json_path.is_dir():
        raise ValueError("JSON_PATH must point to a file, not a directory")



    raw_name = values.get("APP_NAME")

    if raw_name is None:
        app_name = DEFAULT_APP_NAME

    elif not raw_name.strip():
        raise ValueError("APP_NAME must not be empty")

    else:
        app_name = raw_name


    return Settings(json_path=json_path, app_name=app_name)