import importlib
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "garden_test.db"))
    monkeypatch.setenv("GARDEN_API_KEY", "test-key")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    if "game_api" in sys.modules:
        del sys.modules["game_api"]
    module = importlib.import_module("game_api")
    module.ensure_schema()
    return module, module.app.test_client()


def create_human_garden(client):
    response = client.post("/web/register", json={"name": "返回面测试花园"})
    assert response.status_code == 200
    payload = response.get_json()
    return payload["session_id"], {"X-Garden-Token": payload["garden_token"]}


def write_raw_state(module, session_id, state):
    payload = json.dumps(state, ensure_ascii=False)
    with module._get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE garden_saves SET state = ? WHERE session_id = ?",
            (payload, session_id),
        )
        conn.commit()


def test_api_cmd_uses_slim_ai_summary(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}

    response = client.post(
        "/api/cmd",
        headers=headers,
        json={"session_id": session_id, "command": "status"},
    )

    assert response.status_code == 200
    state = response.get_json()["state"]
    assert "inventory" not in state
    assert "encyclopedia" not in state
    assert "letters" not in state
    assert "letter_catalog" not in state
    assert "collectibles" not in state
    assert "collectible_catalog" not in state
    assert "garden_collectibles" not in state
    assert "garden_collectibles_count" not in state
    assert "garden_collectibles_total_found" not in state
    assert "garden_collectibles_capacity" not in state
    assert "garden_collectible_catalog" not in state
    assert "garden_collection_log" not in state
    assert "recent_events" not in state
    assert "cat_state" not in state
    assert "pots" not in state
    assert "inventory_counts" in state
    assert "pots_summary" in state
    assert "garden_events" in state


def test_api_status_uses_slim_ai_summary(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}

    response = client.get(f"/api/status?session_id={session_id}", headers=headers)

    assert response.status_code == 200
    state = response.get_json()["state"]
    assert "inventory" not in state
    assert "encyclopedia" not in state
    assert "letters" not in state
    assert "collectibles" not in state
    assert "recent_events" not in state
    assert "pots" not in state
    assert "inventory_counts" in state
    assert "cat_summary" in state


def test_web_status_keeps_wide_summary(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)

    response = client.get(f"/web/status?session_id={session_id}", headers=human_headers)

    assert response.status_code == 200
    state = response.get_json()["state"]
    assert "inventory" in state
    assert "encyclopedia" in state
    assert "letters" in state
    assert "letter_catalog" in state
    assert "collectibles" in state
    assert "recent_events" in state
    assert "pots" in state
    assert "garden_collectibles" not in state
    assert "garden_collectibles_count" not in state
    assert "garden_collectibles_total_found" not in state
    assert "garden_collectibles_capacity" not in state
    assert "garden_collectible_catalog" not in state
    assert "garden_collection_log" not in state


def test_web_cmd_keeps_wide_summary(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)

    response = client.post(
        "/web/cmd",
        headers=human_headers,
        json={"session_id": session_id, "command": "status"},
    )

    assert response.status_code == 200
    state = response.get_json()["state"]
    assert "inventory" in state
    assert "encyclopedia" in state
    assert "letters" in state
    assert "letter_catalog" in state
    assert "collectibles" in state
    assert "recent_events" in state
    assert "pots" in state
    assert "garden_collectibles" not in state
    assert "garden_collectibles_count" not in state
    assert "garden_collectibles_total_found" not in state
    assert "garden_collectibles_capacity" not in state
    assert "garden_collectible_catalog" not in state
    assert "garden_collection_log" not in state


def test_api_info_marks_api_state_as_disabled(api):
    module, client = api

    response = client.get("/api/info")

    assert response.status_code == 200
    endpoints = response.get_json()["endpoints"]
    state_help = next(value for key, value in endpoints.items() if "/api/state" in key)
    assert "停用" in state_help or "不再" in state_help
    assert "完整 JSON 存档" not in state_help


def test_ai_update_notice_is_shown_once_on_first_status_for_legacy_garden(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}
    legacy_state = module.db_load_state(session_id)
    legacy_state.pop("ai_v5_update_notice_seen", None)
    write_raw_state(module, session_id, legacy_state)

    first = client.get(f"/api/status?session_id={session_id}", headers=headers)
    second = client.get(f"/api/status?session_id={session_id}", headers=headers)

    assert first.status_code == 200
    assert module.AI_V5_UPDATE_NOTICE in first.get_json()["message"]
    assert "\n\n" in first.get_json()["message"]
    assert first.get_json()["message"].split("\n\n", 1)[1].strip()
    assert second.status_code == 200
    assert module.AI_V5_UPDATE_NOTICE not in second.get_json()["message"]
    assert module.db_load_state(session_id)["ai_v5_update_notice_seen"] is True


def test_ai_update_notice_is_shown_on_first_cmd_without_blocking_command(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}
    legacy_state = module.db_load_state(session_id)
    legacy_state["ai_v5_update_notice_seen"] = False
    module.db_save_state(session_id, legacy_state)

    response = client.post(
        "/api/cmd",
        headers=headers,
        json={"session_id": session_id, "command": "help"},
    )

    assert response.status_code == 200
    message = response.get_json()["message"]
    assert module.AI_V5_UPDATE_NOTICE in message
    assert "help" in message.lower()
    assert module.db_load_state(session_id)["ai_v5_update_notice_seen"] is True


def test_new_v5_garden_does_not_show_legacy_ai_update_notice(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}

    response = client.get(f"/api/status?session_id={session_id}", headers=headers)

    assert response.status_code == 200
    assert module.AI_V5_UPDATE_NOTICE not in response.get_json()["message"]
    assert module.get_default_state()["ai_v5_update_notice_seen"] is True


def test_web_routes_do_not_show_ai_update_notice(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    ai_headers = {"X-API-Key": "test-key"}
    legacy_state = module.db_load_state(session_id)
    legacy_state.pop("ai_v5_update_notice_seen", None)
    write_raw_state(module, session_id, legacy_state)

    ai_response = client.get(f"/api/status?session_id={session_id}", headers=ai_headers)
    web_response = client.get(f"/web/status?session_id={session_id}", headers=human_headers)

    assert ai_response.status_code == 200
    assert module.AI_V5_UPDATE_NOTICE in ai_response.get_json()["message"]
    assert web_response.status_code == 200
    assert module.AI_V5_UPDATE_NOTICE not in web_response.get_json()["message"]


def test_api_info_welcome_no_longer_mentions_saving_money_to_adopt(api):
    _module, client = api

    response = client.get("/api/info")

    assert response.status_code == 200
    welcome = response.get_json()["welcome"]
    assert "攒钱收养猫咪" not in welcome
    assert "等待猫咪来访" in welcome


def test_summary_recognizes_pest_active(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    pot = {
        "flower_id": "daisy",
        "growth_progress": 10.0,
        "last_growth_update": 0,
        "watered": True,
        "pest_active": True,
    }
    state["pots"][0] = pot
    module.db_save_state(session_id, state)

    summary = module._summary(state)

    assert summary["pots"][0]["has_pest"] is True
    assert summary["garden_events"]["has_pests"] is True
    assert summary["garden_events"]["pest_pots"] == [1]
