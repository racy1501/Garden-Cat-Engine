import importlib
import json
import sys
from pathlib import Path

import pytest

import game_engine as ge


@pytest.fixture()
def cat_clock(monkeypatch):
    clock = [1_790_985_600]
    monkeypatch.setattr(ge.time, "time", lambda: clock[0])
    monkeypatch.setattr(ge.random, "randint", lambda low, high: (low + high) // 2)
    monkeypatch.setattr(ge.random, "random", lambda: 1.0)
    return clock


def adopted_cat_state():
    state = ge.get_default_state()
    state["cat"] = {"name": "栗子"}
    state["cat_stats"] = ge._default_v5_cat_stats()
    state["cat_state"].update(phase=ge.CAT_PHASE_WAITING_NAME, location=ge.CAT_LOCATION_GARDEN)
    assert "成功收养" in ge.process_command(state, "adopt 栗子")
    return state


def test_cat_offline_events_use_transition_times(cat_clock, monkeypatch):
    state = adopted_cat_state()
    start = cat_clock[0]
    recorded = []
    original = ge.add_event

    def record(state, text, *, now=None):
        original(state, text, now=now)
        if "出门" in text or "回家" in text:
            recorded.append(dict(state["events"][-1]))

    monkeypatch.setattr(ge, "add_event", record)
    cat_clock[0] += 6 * 3600
    ge.apply_offline_progress(state)
    assert [event["time"] - start for event in recorded] == [5400, 6600, 12000, 13200, 18600, 19800]
    assert state["cat_state"]["location"] == "home"
    assert state["cat_state"]["next_outing_at"] == start + 25200
    assert len(state["events"]) == 5  # 原有历史保留上限不变。
    for delta in (0, 60, 180):
        cat_clock[0] = start + 21600 + delta
        ge.process_command(state, "status")
        ge.apply_offline_progress(state)
        assert len(recorded) == 6
        assert state["cat_state"]["next_outing_at"] == start + 25200


@pytest.mark.parametrize("phase,location", [
    (ge.CAT_PHASE_VISITOR, ge.CAT_LOCATION_AWAY),
    (ge.CAT_PHASE_VISITOR, ge.CAT_LOCATION_GARDEN),
    (ge.CAT_PHASE_WAITING_NAME, ge.CAT_LOCATION_GARDEN),
    (ge.CAT_PHASE_ADOPTED, ge.CAT_LOCATION_HOME),
    (ge.CAT_PHASE_ADOPTED, ge.CAT_LOCATION_AWAY),
])
def test_ai_cat_summary_uses_phase_location(api, cat_clock, phase, location):
    module, _ = api
    state = ge.get_default_state()
    state["cat_state"].update(phase=phase, location=location)
    if phase != ge.CAT_PHASE_VISITOR:
        state["cat"] = {"name": "栗子"}
        state["cat_stats"] = ge._default_v5_cat_stats()
    summary = module._ai_summary(state)["cat_summary"]
    assert summary["stage"] == phase
    assert summary["location"] == location
    assert summary["is_present"] == (location in ("garden", "home"))
    assert summary["has_cat"] == (state.get("cat") is not None)


@pytest.mark.parametrize("endpoint", ["status", "cmd"])
def test_api_latest_event_excludes_offline_request_history(api, cat_clock, endpoint):
    module, client = api
    state = adopted_cat_state()
    state["events"] = [{"time": cat_clock[0], "text": "旧事件"}] * 5
    module.db_save_state("cat-events", state)
    start = cat_clock[0]

    def query():
        headers = {"X-API-Key": "test-key"}
        if endpoint == "status":
            response = client.get("/api/status?session_id=cat-events", headers=headers)
        else:
            response = client.post("/api/cmd", headers=headers,
                                   json={"session_id": "cat-events", "command": "status"})
        assert response.status_code == 200
        return response.get_json()

    assert query()["state"]["latest_event"] == ""
    cat_clock[0] = start + 21600
    assert query()["state"]["latest_event"] == ""
    for delta in (0, 60, 180):
        cat_clock[0] = start + 21600 + delta
        result = query()
        assert result["state"]["latest_event"] == ""
        assert "出门" not in result["message"] and "回家" not in result["message"]
    loaded = module.db_load_state("cat-events")
    assert loaded["cat_state"]["next_outing_at"] == start + 25200
    assert loaded["events"][-1] == {
        "time": start + 19800,
        "text": "栗子回家了。",
        "source": "system",
    }
    assert not any("events_before" in key for key in loaded)


def test_new_event_with_same_time_and_text_is_not_suppressed(api, cat_clock):
    module, client = api
    state = adopted_cat_state()
    state["inventory"]["flowers"]["rose"] = 1
    state["events"] = [{"time": cat_clock[0], "text": "把玫瑰插进花瓶"}]
    module.db_save_state("same-event", state)
    response = client.post("/api/cmd", headers={"X-API-Key": "test-key"},
                           json={"session_id": "same-event", "command": "arrange rose"})
    assert response.status_code == 200
    assert response.get_json()["state"]["latest_event"] == "把玫瑰插进花瓶"
    assert module._ai_summary(module.db_load_state("same-event"))["latest_event"] == ""


@pytest.mark.parametrize("storage", ["json", "sqlite"])
def test_cat_boundaries_and_save_reload(api, cat_clock, tmp_path, monkeypatch, storage):
    module, _ = api
    monkeypatch.setattr(ge, "SAVE_FILE", str(tmp_path / "cat-test.json"))
    state = adopted_cat_state()
    start = cat_clock[0]
    for delta in (0, 120, 5399, 5400, 5400, 5520, 6599, 6600, 6600, 6720):
        cat_clock[0] = start + delta
        ge.process_command(state, "status")
        home = delta < 5400 or delta >= 6600
        assert state["cat_state"]["location"] == ("home" if home else "away")
        assert state["cat_state"]["next_outing_at"] == (start + 5400 if delta < 5400 else start + 12000 if delta >= 6600 else 0)
        assert state["cat_state"]["outing_return_at"] == (0 if home else start + 6600)
        assert state["cat_state"]["location_changed_at"] == (start if delta < 5400 else start + 5400 if delta < 6600 else start + 6600)
        assert state["last_active_at"] == cat_clock[0]
        assert state["cat_state"]["last_lifecycle_settled_at"] == cat_clock[0]
        before = dict(state["cat_state"])
        if storage == "json":
            ge.save_game(state)
            state = ge.load_game()
        else:
            module.db_save_state("cat-reload", state)
            state = module.db_load_state("cat-reload")
        assert state["cat_state"] == before
        assert module._ai_summary(state)["latest_event"] == ""


def test_regular_events_keep_current_time_and_history_limit(cat_clock):
    state = ge.get_default_state()
    for number in range(7):
        ge.add_event(state, f"普通事件{number}")
    assert len(state["events"]) == 5
    assert all(event["time"] == cat_clock[0] for event in state["events"])


@pytest.mark.parametrize("stay", [False, True])
def test_visitor_lifecycle_events_use_historical_times(cat_clock, stay):
    state = ge.get_default_state()
    start = cat_clock[0]
    ge.settle_cat_lifecycle(state, start)
    leave_at = state["cat_state"]["current_visit_leave_at"]
    if stay:
        state["cat_stats"]["affection"] = 30
        ge.update_cat_max_affection(state)
    cat_clock[0] = leave_at + 60
    ge.settle_cat_lifecycle(state, cat_clock[0])
    assert state["events"][0]["time"] == start
    assert state["events"][-1]["time"] == leave_at
    assert ("决定留下" if stay else "离开了花园") in state["events"][-1]["text"]


@pytest.mark.parametrize("home,away", [(3600, 600), (7200, 1800)])
def test_cat_duration_endpoints_are_unchanged(cat_clock, monkeypatch, home, away):
    monkeypatch.setattr(ge.random, "randint", lambda low, high: home if (low, high) == (3600, 7200) else away if (low, high) == (600, 1800) else (low + high) // 2)
    state = adopted_cat_state()
    start = cat_clock[0]
    assert state["cat_state"]["next_outing_at"] == start + home
    cat_clock[0] += home
    ge.process_command(state, "status")
    assert state["cat_state"]["location"] == "away"
    assert state["cat_state"]["outing_return_at"] == start + home + away
    cat_clock[0] += away
    ge.process_command(state, "status")
    assert state["cat_state"]["location"] == "home"
    assert state["cat_state"]["next_outing_at"] == start + home + away + home


def test_return_care_collectible_and_letter_events_keep_node_time(cat_clock, monkeypatch):
    state = adopted_cat_state()
    start = cat_clock[0]
    state["cat_stats"].update(hunger=0, thirst=0)
    state["cat_care"]["food_bowl"]["remaining_portions"] = 1
    state["cat_care"]["water_bowl"]["remaining_portions"] = 1
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    cat_clock[0] = start + 7200
    ge.settle_cat_lifecycle(state, cat_clock[0])
    care = [event for event in state["events"] if "吃了" in event["text"] or "喝了" in event["text"]]
    assert len(care) == 2
    assert all(event["time"] == start + 6600 for event in care)
    ge.award_cat_collectible(state, ge.CAT_COLLECTIBLES[0], now=start + 6600)
    assert state["events"][-1]["time"] == start + 6600
    state["cat_stats"]["affection"] = 100
    ge.update_cat_max_affection(state)
    state["letter_affection_progress"] = ge.LETTER_PROGRESS_BATCH
    assert ge._resolve_letter_progress(state, now=start + 6600)
    assert state["events"][-1]["time"] == start + 6600


@pytest.mark.parametrize("route", ["/api/cmd", "/web/cmd"])
def test_api_request_shares_letter_limit_between_offline_and_command(cat_clock, monkeypatch, route):
    import sqlite3
    from contextlib import contextmanager

    monkeypatch.setenv("SQLITE_PATH", ":memory:")
    monkeypatch.setenv("GARDEN_API_KEY", "test-key")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delitem(sys.modules, "game_api", raising=False)
    api = importlib.import_module("game_api")
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row

    @contextmanager
    def memory_connection():
        yield connection

    monkeypatch.setattr(api, "_get_conn", memory_connection)
    api.ensure_schema()
    now = cat_clock[0]
    state = ge.get_default_state()
    ge.apply_move_with_cat_reset(state, "栗子", now=now)
    state["cat_stats"].update(hunger=20.0, thirst=20.0, affection=100.0)
    state["cat_state"]["stats"] = dict(state["cat_stats"])
    state["cat_max_affection"] = 100.0
    state["cat_state"]["next_outing_at"] = now + 100000
    state["weather_change_time"] = state["next_butterfly_at"] = now + 100000
    state["letter_affection_progress"] = 40
    state["cat_care"]["food_bowl"]["remaining_portions"] = 3
    state["cat_care"]["water_bowl"]["remaining_portions"] = 3
    token = api._issue_web_token(state)
    api.db_save_state("letter-test", state)
    cat_clock[0] += 3600
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    client = api.app.test_client()
    headers = {"X-API-Key": "test-key", "X-Garden-Token": token}

    response = client.post(route, json={"session_id": "letter-test", "command": "status"}, headers=headers)
    assert response.status_code == 200
    saved = api.db_load_state("letter-test")
    assert saved["letters_received"] == [0]
    assert saved["letter_affection_progress"] == 42
    response = client.post(route, json={"session_id": "letter-test", "command": "status"}, headers=headers)
    assert response.status_code == 200
    saved = api.db_load_state("letter-test")
    assert saved["letters_received"] == [0, 1]
    assert saved["letter_affection_progress"] == 38
    connection.close()


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


def prepare_letter_notice_state(module, session_id, cat_clock):
    state = module.db_load_state(session_id)
    start = cat_clock[0]
    ge.apply_move_with_cat_reset(state, "栗子", now=start)
    state["events"] = []
    state["cat_stats"].update(hunger=100.0, thirst=100.0, affection=100.0)
    state["cat_state"]["stats"] = dict(state["cat_stats"])
    state["cat_state"].update(next_outing_at=start + 100000, last_lifecycle_settled_at=start)
    state["cat_max_affection"] = 100.0
    state["letter_affection_progress"] = ge.LETTER_PROGRESS_BATCH
    state["cat_care"]["food_bowl"]["remaining_portions"] = 0
    state["cat_care"]["water_bowl"]["remaining_portions"] = 0
    state["weather_change_time"] = state["next_butterfly_at"] = start + 100000
    write_raw_state(module, session_id, state)


def test_legacy_shop_pending_is_saved_without_offline_changes(api, cat_clock):
    from datetime import datetime

    module, client = api
    def at(day, hour=0):
        return int(datetime(2026, 10, day, hour, tzinfo=ge.DISPLAY_TIMEZONE).timestamp())

    cat_clock[0] = at(29, 11)
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["flower_shop"].update(
        established_at=at(28), launched_at=at(28),
        business_start_minute=0, shelf_capacity=3, slots=[None] * 3,
        pending_business_start_minute=14 * 60,
        pending_business_effective_at=at(29, 14),
    )
    state["last_active_at"] = state["last_update"] = cat_clock[0]
    write_raw_state(module, session_id, state)

    first = module.db_load_state(session_id)
    assert first["flower_shop"]["pending_business_effective_at"] == at(30)
    # Read the stored JSON directly: another normalized load could conceal a missed save.
    with module._get_conn() as conn:
        row = conn.execute("SELECT state FROM garden_saves WHERE session_id = ?", (session_id,)).fetchone()
    persisted = json.loads(row["state"])["flower_shop"]
    assert persisted["business_start_minute"] is None
    assert persisted["pending_business_effective_at"] == at(30)

    cat_clock[0] = at(30, 1)
    second = module.db_load_state(session_id)
    assert second["flower_shop"]["pending_business_effective_at"] == at(30)
    assert second["flower_shop"]["business_start_minute"] == 14 * 60
    assert second["flower_shop"]["pending_business_start_minute"] is None


@pytest.mark.parametrize("route", ["/web/cmd", "/api/cmd"])
def test_flower_shop_hours_response_announces_next_date_and_new_window(api, cat_clock, route):
    from datetime import datetime

    module, client = api
    cat_clock[0] = int(datetime(2026, 10, 29, 11, tzinfo=ge.DISPLAY_TIMEZONE).timestamp())
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["flower_shop"].update(
        established_at=cat_clock[0] - 86400, launched_at=cat_clock[0] - 86400,
        business_start_minute=0, shelf_capacity=3, slots=[None] * 3,
    )
    write_raw_state(module, session_id, state)
    response = client.post(
        route,
        headers=human_headers if route.startswith("/web/") else {"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "set_flower_shop_hours 14:00"},
    )
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"]
    assert "下一自然日生效" in payload["message"]
    assert "今天剩余时间花店保持闭店" in payload["message"]
    assert "14:00–24:00" in payload["message"]
    assert payload["state"]["flower_shop"]["is_open"] is False
    assert payload["state"]["flower_shop"]["pending_business_start_minute"] == 14 * 60


def test_silent_resume_notifies_new_letter_once(api, cat_clock, monkeypatch):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    prepare_letter_notice_state(module, session_id, cat_clock)
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    cat_clock[0] += 6 * 3600
    headers = {**human_headers, "X-Garden-Live": "0"}

    response = client.get(f"/web/status?session_id={session_id}", headers=headers)
    payload = response.get_json()
    notices = [event["text"] for event in payload["state"]["new_events"]]
    letter_title = ge.CAT_LETTERS[0]["title"]

    assert response.status_code == 200
    assert payload["state"]["letters_received"] == [0]
    assert sum(letter_title in notice and "收到新信" in notice for notice in notices) == 1

    again = client.get(f"/web/status?session_id={session_id}", headers=headers).get_json()
    assert again["state"]["letters_received"] == [0]
    assert not any("收到新信" in event["text"] for event in again["state"]["new_events"])


def test_live_letter_event_is_not_duplicated_with_synthetic_notice(api, cat_clock, monkeypatch):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    prepare_letter_notice_state(module, session_id, cat_clock)
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    headers = {**human_headers, "X-Garden-Live": "1"}

    response = client.get(f"/web/status?session_id={session_id}", headers=headers)
    payload = response.get_json()
    letter_events = [
        event["text"] for event in payload["state"]["new_events"]
        if "收到" in event["text"] and "封信" in event["text"]
    ]

    assert response.status_code == 200
    assert payload["state"]["letters_received"] == [0]
    assert len(letter_events) == 1
    assert not any("收到新信：" in event["text"] for event in payload["state"]["new_events"])


def test_silent_resume_without_new_letter_has_no_letter_notice(api, cat_clock, monkeypatch):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    prepare_letter_notice_state(module, session_id, cat_clock)
    state = module.db_load_state(session_id)
    state["letter_affection_progress"] = 0
    write_raw_state(module, session_id, state)
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    cat_clock[0] += 6 * 3600

    response = client.get(
        f"/web/status?session_id={session_id}",
        headers={**human_headers, "X-Garden-Live": "0"},
    )
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["state"]["letters_received"] == []
    assert not any("收到新信" in event["text"] for event in payload["state"]["new_events"])


@pytest.mark.parametrize("endpoint,live", [
    ("web_status", True), ("web_status", False), ("web_cmd", True),
    ("api_status", False), ("api_cmd", False), ("web_notes", False),
    ("api_notes", False), ("bouquet_read", False),
])
def test_first_cat_collectible_notified_by_settling_request(api, cat_clock, monkeypatch, endpoint, live):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    start = cat_clock[0]
    ge.apply_move_with_cat_reset(state, "栗子", now=start)
    state["events"] = []
    state["cat_collectibles_unlocked"] = True
    state["cat_state"].update(location=ge.CAT_LOCATION_AWAY, outing_return_at=start + 60,
                              next_outing_at=0, last_lifecycle_settled_at=start)
    state["weather_change_time"] = state["next_butterfly_at"] = start + 100000
    write_raw_state(module, session_id, state)
    item = ge.CAT_COLLECTIBLES[0]
    calls = []

    def first_drop(state, context, now=None, source=None):
        calls.append(now)
        return ge.award_cat_collectible(state, item, now=now, source=source) if len(calls) == 1 else None

    monkeypatch.setattr(ge, "maybe_drop_cat_collectible", first_drop)
    cat_clock[0] += 60 if live else 6 * 3600
    headers = {**human_headers, "X-Garden-Live": "1" if live else "0"}
    if endpoint == "web_status":
        response = client.get(f"/web/status?session_id={session_id}", headers=headers)
    elif endpoint == "web_cmd":
        response = client.post("/web/cmd", headers=headers, json={"session_id": session_id, "command": "status"})
    elif endpoint == "api_status":
        response = client.get(f"/api/status?session_id={session_id}", headers={"X-API-Key": "test-key"})
    elif endpoint == "api_cmd":
        response = client.post("/api/cmd", headers={"X-API-Key": "test-key"}, json={"session_id": session_id, "command": "status"})
    elif endpoint == "web_notes":
        response = client.get(f"/web/notes?session_id={session_id}", headers=headers)
    elif endpoint == "api_notes":
        response = client.get(f"/api/notes?session_id={session_id}", headers={"X-API-Key": "test-key"})
    else:
        response = client.post("/web/bouquets/read", headers=headers, json={"session_id": session_id})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["message"].count(item["name"]) == 1
    assert "发现新藏品" in payload["message"]
    if endpoint.startswith("web_") or endpoint == "bouquet_read":
        if "state" in payload:
            notices = [event["text"] for event in payload["state"]["new_events"]]
            assert sum(item["name"] in text for text in notices) == 1
            assert "发现新藏品" in notices[0]
    elif "state" in payload:
        assert item["name"] in payload["state"]["offline_summary"]["message"]
    saved = module.db_load_state(session_id)
    assert saved["collectibles"][item["id"]] == 1
    assert saved["collectible_first_found"][item["id"]] == start + 60
    if not live:
        assert all(item["name"] not in event["text"] for event in saved["events"])
    assert not any("discovery" in key or "collectible_notice" in key for key in saved)

    again = client.get(f"/web/status?session_id={session_id}", headers=headers).get_json()
    assert "发现新藏品" not in again["message"]
    assert not any("发现新藏品" in event["text"] for event in again["state"]["new_events"])


@pytest.mark.parametrize("already_owned", [False, True])
def test_multiple_and_repeat_cat_collectibles_notice(api, cat_clock, monkeypatch, already_owned):
    module, client = api
    session_id, headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    start = cat_clock[0]
    ge.apply_move_with_cat_reset(state, "栗子", now=start)
    state["events"] = []
    state["cat_collectibles_unlocked"] = True
    state["cat_state"].update(location=ge.CAT_LOCATION_AWAY, outing_return_at=start + 60,
                              next_outing_at=0, last_lifecycle_settled_at=start)
    state["weather_change_time"] = state["next_butterfly_at"] = start + 100000
    items = ge.CAT_COLLECTIBLES[:2]
    if already_owned:
        state["collectibles"][items[0]["id"]] = 1
        state["collectible_first_found"][items[0]["id"]] = start - 100
    write_raw_state(module, session_id, state)
    calls = []

    def drop(state, context, now=None, source=None):
        calls.append(now)
        item = items[0] if already_owned else items[min(len(calls) - 1, 1)]
        return ge.award_cat_collectible(state, item, now=now, source=source)

    monkeypatch.setattr(ge, "maybe_drop_cat_collectible", drop)
    cat_clock[0] += 60 if already_owned else 6 * 3600
    response = client.get(f"/web/status?session_id={session_id}", headers={**headers, "X-Garden-Live": "1"})
    payload = response.get_json()
    saved = module.db_load_state(session_id)
    if already_owned:
        assert saved["collectibles"][items[0]["id"]] == 2
        assert saved["collectible_first_found"][items[0]["id"]] == start - 100
        assert "发现新藏品" not in payload["message"]
        assert any(items[0]["name"] in e["text"] for e in payload["state"]["new_events"])
    else:
        assert all(saved["collectibles"][item["id"]] > 0 for item in items)
        assert all(payload["message"].count(item["name"]) == 1 for item in items)
        notices = [e["text"] for e in payload["state"]["new_events"] if "发现新藏品" in e["text"]]
        assert len(notices) == 1 and all(item["name"] in notices[0] for item in items)


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


def test_ai_bouquet_command_and_web_collection_state(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["encyclopedia"] = ["tulip", "baby_breath"]
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    module.db_save_state(session_id, state)
    ai_headers = {"X-API-Key": "test-key"}

    created = client.post(
        "/api/cmd",
        headers=ai_headers,
        json={
            "session_id": session_id,
            "command": "make_bouquet bouquet_id=first_meeting message=给你的春天",
        },
    )
    assert created.status_code == 200
    assert created.get_json()["ok"] is True
    assert len(created.get_json()["state"]["bouquet_options"]) == 1

    web_state = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert len(web_state["bouquet_gifts"]) == 1
    assert web_state["bouquet_gifts"][0]["message"] == "给你的春天"
    assert web_state["bouquet_options"] == created.get_json()["state"]["bouquet_options"]
    assert web_state["bouquet_gifts"][0]["components"] == {"tulip": 2, "baby_breath": 1}
    assert web_state["recent_events"][-1] == "💐 小机送给你一束「初见」，还附了一张小卡片。"
    gift_events = [
        event["text"]
        for event in module.db_load_state(session_id)["events"]
        if "送给你一束「初见」" in event.get("text", "")
    ]
    assert gift_events == ["💐 小机送给你一束「初见」，还附了一张小卡片。"]
    assert all("返回面测试花园" not in event for event in gift_events)

    catalog = client.get("/api/catalog").get_json()
    assert len(catalog["bouquets"]) == 12


def test_flower_shop_and_bouquet_inventory_have_public_summary_only(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["money"] = 4000
    state["encyclopedia"] = list(module.FLOWERS)[:10]
    state["flower_harvest_counts"] = {"daisy": 42}
    state["direct_flower_sale_earned"] = 3000
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    state["encyclopedia"].extend(["tulip", "baby_breath"])
    module.db_save_state(session_id, state)
    ai_headers = {"X-API-Key": "test-key"}

    crafted = client.post(
        "/api/cmd", headers=ai_headers,
        json={"session_id": session_id, "command": "craft_bouquet bouquet_id=first_meeting"},
    ).get_json()
    assert crafted["ok"] is True
    item = crafted["state"]["bouquet_inventory"][0]
    assert set(item) == {"id", "bouquet_id", "name", "components"}

    established = client.post(
        "/web/cmd", headers=human_headers,
        json={"session_id": session_id, "command": "establish_flower_shop"},
    ).get_json()["state"]
    shop = established["flower_shop"]
    assert shop["eligible"] is True
    assert shop["capacity"] == 3
    assert shop["empty_slots"] == 3
    assert shop["can_upgrade_shelf"] is True
    assert shop["next_shelf_capacity"] == 6
    assert shop["next_shelf_upgrade_cost"] == 1500
    assert shop["has_freshener"] is False
    assert shop["freshener_cost"] == 1800
    assert shop["shop_buff_active"] is False
    assert shop["shop_buff_until"] is None
    assert shop["shop_buff_remaining_seconds"] == 0
    assert "established_at" not in shop
    assert "flower_shop" not in established["inventory"]

    ai_state = client.get(f"/api/status?session_id={session_id}", headers=ai_headers).get_json()["state"]
    assert ai_state["flower_shop"]["eligibility_progress"]["direct_flower_sale_earned"] == 3000
    assert ai_state["bouquet_inventory"][0]["id"] == item["id"]

    saved = module.db_load_state(session_id)
    buff_until = int(ge.time.time()) + 3600
    saved["flower_shop"]["shop_buff_until"] = buff_until
    module.db_save_state(session_id, saved)
    active_shop = client.get(
        f"/api/status?session_id={session_id}", headers=ai_headers
    ).get_json()["state"]["flower_shop"]
    assert active_shop["shop_buff_active"] is True
    assert active_shop["shop_buff_until"] == buff_until
    assert 0 < active_shop["shop_buff_remaining_seconds"] <= 3600
    assert active_shop["shop_buff_effect"] == "成交金额 +10%"
    assert "shop_buff_windows" not in active_shop
    assert "buff_roll" not in active_shop


def test_flower_shop_listing_summary_exposes_price_but_hides_random_facts(api, monkeypatch):
    module, client = api
    session_id, _ = create_human_garden(client)
    now = int(ge.time.time())
    local_now = ge.datetime.fromtimestamp(now, ge.DISPLAY_TIMEZONE)
    state = module.db_load_state(session_id)
    state["flower_shop"] = {
        "established_at": now - 100,
        "launched_at": now - 50,
        "shelf_capacity": 3,
        "business_start_minute": (local_now.hour * 60 + local_now.minute - 60) % (24 * 60),
        "pending_business_start_minute": None,
        "pending_business_effective_at": None,
        "slots": [None, None, None],
    }
    state["bouquet_inventory"] = [
        {"instance_id": "api-listing", "bouquet_id": "first_meeting", "components": {"tulip": 2, "baby_breath": 1}}
    ]
    module.db_save_state(session_id, state)
    monkeypatch.setattr(ge, "_roll_flower_shop_sale_plan", lambda: (True, 7200))

    response = client.post(
        "/api/cmd",
        headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "list_bouquet instance_id=api-listing slot=1"},
    )
    assert response.status_code == 200
    public_state = response.get_json()["state"]
    public_slot = public_state["flower_shop"]["slots"][0]
    assert public_slot["empty"] is False
    assert public_slot["name"] == "初见"
    assert public_slot["current_price"] == 55
    assert public_slot["expires_in_seconds"] <= 24 * 3600
    assert "will_sell" not in public_slot
    assert "sale_business_seconds_remaining" not in public_slot
    assert "pricing_profile" not in public_slot
    assert public_state["bouquet_inventory"] == []

    saved_slot = module.db_load_state(session_id)["flower_shop"]["slots"][0]
    assert saved_slot["will_sell"] is True
    assert saved_slot["sale_business_seconds_remaining"] <= 7200


def test_bouquet_unread_cursor_is_durable_and_legacy_gifts_are_read(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    ai_headers = {"X-API-Key": "test-key"}
    state = module.db_load_state(session_id)
    state["bouquet_gifts"] = [
        {
            "bouquet_id": "first_meeting",
            "components": {"tulip": 2, "rose": 2},
            "sent_at": 1_700_000_000,
            "message": None,
        }
    ]
    old_event_text = "💐 我的小花园送给你一束「小花园」，还附了一张小卡片。"
    state["events"] = [{"time": 1_700_000_000, "text": old_event_text}]
    state.pop("human_last_read_bouquet_gift_count", None)
    write_raw_state(module, session_id, state)

    legacy = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert legacy["has_unread_bouquet_gifts"] is False
    assert legacy["unread_bouquet_gift_count"] == 0
    assert old_event_text in legacy["recent_events"]

    state = module.db_load_state(session_id)
    state["encyclopedia"] = ["tulip", "baby_breath"]
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    module.db_save_state(session_id, state)
    created = client.post(
        "/api/cmd",
        headers=ai_headers,
        json={"session_id": session_id, "command": "make_bouquet bouquet_id=first_meeting"},
    )
    assert created.get_json()["state"]["bouquet_options"]
    first_gift_events = [
        event["text"]
        for event in module.db_load_state(session_id)["events"]
        if "送给你一束「初见」" in event.get("text", "")
    ]
    assert first_gift_events == ["💐 小机送给你一束「初见」。"]
    assert all("返回面测试花园" not in event for event in first_gift_events)
    assert old_event_text in [event["text"] for event in module.db_load_state(session_id)["events"]]
    unread = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert unread["has_unread_bouquet_gifts"] is True
    assert unread["unread_bouquet_gift_count"] == 1

    viewed = client.post(
        "/web/bouquets/read",
        headers=human_headers,
        json={"session_id": session_id},
    )
    assert viewed.status_code == 200
    assert viewed.get_json()["state"]["has_unread_bouquet_gifts"] is False
    assert viewed.get_json()["state"]["unread_bouquet_gift_count"] == 0
    assert client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]["has_unread_bouquet_gifts"] is False

    state = module.db_load_state(session_id)
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    module.db_save_state(session_id, state)
    client.post(
        "/api/cmd",
        headers=ai_headers,
        json={"session_id": session_id, "command": "make_bouquet bouquet_id=first_meeting"},
    )
    all_gift_events = [
        event["text"]
        for event in module.db_load_state(session_id)["events"]
        if "送给你一束「初见」" in event.get("text", "")
    ]
    assert all_gift_events == [
        "💐 小机送给你一束「初见」。",
        "💐 小机送给你一束「初见」。",
    ]
    assert all("返回面测试花园" not in event for event in all_gift_events)
    unread_again = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert unread_again["has_unread_bouquet_gifts"] is True
    assert unread_again["unread_bouquet_gift_count"] == 1
