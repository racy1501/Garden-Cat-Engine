import importlib
import os


def load_app(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "garden.db")
    os.environ["GARDEN_API_KEY"] = "test-key"
    import game_api
    return importlib.reload(game_api)


def test_registration_and_independent_saves(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    headers = {"X-API-Key": "test-key"}

    first = client.post("/api/register", headers=headers, json={"name": "一号"})
    second = client.post("/api/register", headers=headers, json={"name": "二号"})
    assert first.status_code == 200
    assert second.status_code == 200
    sid1 = first.json["session_id"]
    sid2 = second.json["session_id"]
    assert sid1 != sid2

    result = client.post(
        "/api/cmd",
        headers=headers,
        json={"session_id": sid1, "command": "buy daisy 1"},
    )
    assert result.json["ok"] is True

    state1 = client.get(f"/api/state?session_id={sid1}", headers=headers).json["state"]
    state2 = client.get(f"/api/state?session_id={sid2}", headers=headers).json["state"]
    assert state1["money"] == 47
    assert state2["money"] == 50


def test_api_key_is_required_when_configured(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    assert client.post("/api/register", json={}).status_code == 401
