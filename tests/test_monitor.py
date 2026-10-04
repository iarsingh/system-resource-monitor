from fastapi.testclient import TestClient

from monitor.main import app

client = TestClient(app)


def sample(cpu=10, memory=20, disk=30):
    return {"cpu_percent": cpu, "memory_percent": memory, "disk_percent": disk}


def series(samples, **extra):
    return client.post("/check/series", json={"samples": samples, **extra}).json()


def test_cpu_alert():
    payload = client.post("/check", json=sample(cpu=95)).json()
    assert payload["alerts"] == ["cpu_percent"]
    assert payload["paged"] is False


def test_healthy():
    assert client.post("/check", json=sample()).json()["healthy"] is True


def test_custom_threshold_on_a_single_check():
    payload = client.post("/check", json={**sample(disk=75), "thresholds": {"disk_percent": 70}}).json()
    assert payload["alerts"] == ["disk_percent"]


def test_out_of_range_and_missing_readings_are_refused():
    assert client.post("/check", json=sample(cpu=120)).status_code == 422
    assert client.post("/check", json={"cpu_percent": 10}).status_code == 422


def test_one_spike_does_not_fire():
    body = series([sample(cpu=95), sample(cpu=20), sample(cpu=96), sample(cpu=20)])
    assert body["firing"] == []


def test_three_in_a_row_fires():
    body = series([sample(cpu=95), sample(cpu=96), sample(cpu=97)])
    assert body["firing"] == ["cpu_percent"]
    assert body["resources"]["cpu_percent"]["fired_at"] == 2


def test_it_stays_firing_until_ten_points_below_the_threshold():
    breach = [sample(cpu=95)] * 3
    body = series(breach + [sample(cpu=85)])
    assert body["firing"] == ["cpu_percent"]
    body = series(breach + [sample(cpu=79)])
    assert body["firing"] == []
    assert body["resources"]["cpu_percent"]["recovered_at"] == 3


def test_window_of_one_behaves_like_a_single_check():
    assert series([sample(memory=91)], window=1)["firing"] == ["memory_percent"]


def test_bad_sample_in_a_series_is_refused():
    response = client.post("/check/series", json={"samples": [sample(), {"cpu_percent": "high"}]})
    assert response.status_code == 422
