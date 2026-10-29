import importlib
import os


def load_app(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "garden.db")
    os.environ["GARDEN_API_KEY"] = "test-key"
    import game_api
    return importlib.reload(game_api)


def test_api_registration_is_disabled_and_web_gardens_are_independent(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    headers = {"X-API-Key": "test-key"}

    disabled = client.post("/api/register", headers=headers, json={"name": "一号"})
    assert disabled.status_code == 403
    assert "人类网页端" in disabled.get_json()["error"]

    first = client.post("/web/register", json={"name": "一号"})
    second = client.post("/web/register", json={"name": "二号"})
    assert first.status_code == 200
    assert second.status_code == 200
    sid1 = first.json["session_id"]
    sid2 = second.json["session_id"]
    assert sid1 != sid2

    result = client.post(
        "/web/cmd",
        headers={"X-Garden-Token": first.json["garden_token"]},
        json={"session_id": sid1, "command": "buy daisy 1"},
    )
    assert result.json["ok"] is True

    state1 = client.get(
        f"/web/status?session_id={sid1}", headers={"X-Garden-Token": first.json["garden_token"]},
    ).json["state"]
    state2 = client.get(
        f"/web/status?session_id={sid2}", headers={"X-Garden-Token": second.json["garden_token"]},
    ).json["state"]
    assert state1["money"] == 47
    assert state2["money"] == 50


def test_api_key_is_required_when_configured(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    assert client.post("/api/register", json={}).status_code == 401
