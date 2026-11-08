import pytest
from app.main import build_service
from app.storage import JsonStorage
from fastapi.testclient import TestClient
from app.api import app


@pytest.fixture(scope="function")
def api_service(tmp_path):
    storage = JsonStorage(tmp_path / "tasks.json")
    return build_service(storage)




@pytest.fixture(scope="function")
def api_client(api_service):
    previous_planner = app.state.planner
    try:
        app.state.planner = api_service
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.state.planner = previous_planner


# tests/test_api.py
def test_health(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}