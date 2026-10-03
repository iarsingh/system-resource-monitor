from fastapi.testclient import TestClient
from monitor.main import app

def test_cpu_alert():
    body = {"cpu_percent": 95, "memory_percent": 10, "disk_percent": 10}
    payload = TestClient(app).post("/check", json=body).json()
    assert payload["alerts"] == ["cpu_percent"]
    assert payload["paged"] is False

def test_healthy():
    body = {"cpu_percent": 10, "memory_percent": 20, "disk_percent": 30}
    assert TestClient(app).post("/check", json=body).json()["healthy"] is True
