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
    assert len(state["events"]) == 6  # 六次出门/归来都保留。
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
    assert len(state["events"]) == 7
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


@pytest.mark.parametrize("route", ["/api/cmd", "/web/cmd"])
@pytest.mark.parametrize("command, expected_ok", [
    ("buy daisy", True),
    ("buy missing_item", False),
    ("buy red_spider_lily", False),
    ("buy daisy 999", False),
    ("pet", False),
    ("harvest 1", False),
    ("notes invalid_page", False),
    ("notes", True),
    ("note", False),
])
def test_command_response_uses_business_outcome(api, route, command, expected_ok):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["cat"] = None
    state["cat_state"].update(phase=ge.CAT_PHASE_VISITOR, location=ge.CAT_LOCATION_AWAY,
                              next_visit_at=int(ge.time.time()) + 3600)
    module.db_save_state(session_id, state)
    headers = {"X-API-Key": "test-key"} if route.startswith("/api/") else human_headers
    response = client.post(route, headers=headers,
                           json={"session_id": session_id, "command": command})
    assert response.status_code == 200
    assert response.get_json()["ok"] is expected_ok


@pytest.mark.parametrize("command, expected_ok", [("buy missing_item", False), ("buy daisy", True)])
@pytest.mark.parametrize("with_event", [False, True])
@pytest.mark.parametrize("with_update_notice", [False, True])
def test_api_command_outcome_survives_extra_notices(
    api, monkeypatch, command, expected_ok, with_event, with_update_notice,
):
    module, client = api
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["ai_v5_update_notice_seen"] = not with_update_notice
    module.db_save_state(session_id, state)
    event_text = "🌤️ 天气发生了变化"
    if with_event:
        monkeypatch.setattr(ge, "get_weather_info", lambda state, now: (ge.WEATHER[state["weather"]], [event_text]))
    response = client.post("/api/cmd", headers={"X-API-Key": "test-key"},
                           json={"session_id": session_id, "command": command})
    payload = response.get_json()
    assert response.status_code == 200
    assert payload["ok"] is expected_ok
    assert (module.AI_V5_UPDATE_NOTICE in payload["message"]) is with_update_notice
    assert (event_text in payload["message"]) is with_event
    assert ("买了1包" if expected_ok else "商店没有这个东西") in payload["message"]


@pytest.mark.parametrize("ok, message", [(False, "操作没有完成"), (True, "❌ 仅用于验证文本不决定结果")])
def test_api_command_does_not_infer_outcome_from_message(api, monkeypatch, ok, message):
    module, client = api
    session_id, _ = create_human_garden(client)
    monkeypatch.setattr(module, "execute_command", lambda *args, **kwargs: ge.CommandResult(ok, message))
    payload = client.post("/api/cmd", headers={"X-API-Key": "test-key"},
                          json={"session_id": session_id, "command": "status"}).get_json()
    assert payload["ok"] is ok
    assert payload["message"] == message


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


@pytest.mark.parametrize("route", ["/web/cmd", "/api/cmd", "/api/cmd?compact=1"])
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


@pytest.mark.parametrize("operation, expected_status, expected_ok", [
    ("read", 200, True), ("write", 200, True),
    ("invalid_page", 400, False), ("invalid_content", 400, False),
    ("cooldown", 429, False),
])
def test_api_notes_reports_settlement_letter_once(
    api, cat_clock, monkeypatch, operation, expected_status, expected_ok,
):
    module, client = api
    session_id, _ = create_human_garden(client)
    prepare_letter_notice_state(module, session_id, cat_clock)
    if operation == "cooldown":
        module.db_add_note(session_id, "ai", "已有便签", now=cat_clock[0])
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    # 本次提示必须来自正式信件记录，不依赖引擎消息的措辞或格式。
    monkeypatch.setattr(ge, "_build_letter_messages", lambda *args: ["信件提示格式已变化"])
    cat_clock[0] += 3600
    headers = {"X-API-Key": "test-key"}
    if operation in ("write", "invalid_content", "cooldown"):
        response = client.post("/api/notes", headers=headers, json={
            "session_id": session_id,
            "content": "" if operation == "invalid_content" else "给小猫留言",
        })
    else:
        page = "invalid" if operation == "invalid_page" else "1"
        response = client.get(f"/api/notes?session_id={session_id}&page={page}", headers=headers)
    payload = response.get_json()
    notice = f"✉️ 收到新信：《{ge.CAT_LETTERS[0]['title']}》"
    assert response.status_code == expected_status
    assert payload["ok"] is expected_ok
    assert payload["message"].splitlines().count(notice) == 1
    assert module.db_load_state(session_id)["letters_received"] == [0]
    if operation == "write":
        assert "📝 便签已贴好。" in payload["message"]
        assert payload["note"]["content"] == "给小猫留言"
    again = client.get(f"/api/notes?session_id={session_id}", headers=headers).get_json()
    assert "收到新信" not in again.get("message", "")
    assert module.db_load_state(session_id)["letters_received"] == [0]


def test_api_notes_without_new_letter_keeps_original_response(api, cat_clock):
    module, client = api
    session_id, _ = create_human_garden(client)
    expected = {"ok": True, **module.db_list_notes(session_id, "ai", page=1)}
    response = client.get(f"/api/notes?session_id={session_id}", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
    assert response.get_json() == expected


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
        return (item["id"], ge.award_cat_collectible(state, item, now=now, source=source)) if len(calls) == 1 else None

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
        assert sum(item["name"] in event["text"] for event in saved["events"]) == 1
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
        return item["id"], ge.award_cat_collectible(state, item, now=now, source=source)

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
    assert all(set(pot) == {"slot", "flower_id", "status"} for pot in state["pots"])
    assert all(pot["status"] in {"empty", "needs_water", "growing", "pest_blocked", "ready", "withered"}
               for pot in state["pots"])
    assert "inventory_counts" in state
    assert "pots_summary" in state
    assert "garden_events" in state


def test_pots_summary_ready_pots_matches_harvestability_on_all_ai_routes(api, cat_clock):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    now = cat_clock[0]
    mature = {
        "flower_id": "daisy",
        "growth_progress": ge.FLOWERS["daisy"]["grow_time"],
        "last_growth_update": now,
        "watered": True,
    }
    state = module.db_load_state(session_id)
    state["max_pots"] = 5
    state["pots"] = [
        dict(mature),
        {**mature, "pest_active": True},
        {**mature, "growth_progress": 10},
        {**mature, "withered": True},
        None,
    ]
    headers = {"X-API-Key": "test-key"}

    for route in ("/api/status", "/api/cmd", "/api/cmd?compact=1"):
        module.db_save_state(session_id, state)
        if route == "/api/status":
            response = client.get(route, headers=headers, query_string={"session_id": session_id})
        else:
            response = client.post(route, headers=headers,
                                   json={"session_id": session_id, "command": "status"})
        assert response.status_code == 200
        summary = response.get_json()["state"]["pots_summary"]
        assert summary["ready_pots"] == 1
        assert summary["pest_pots"] == 1
        assert summary["growing_pots"] == 1
        assert summary["withered_pots"] == 1


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
    assert all(set(pot) == {"slot", "flower_id", "status"} for pot in state["pots"])
    assert all(pot["status"] in {"empty", "needs_water", "growing", "pest_blocked", "ready", "withered"}
               for pot in state["pots"])
    assert "inventory_counts" in state
    assert "cat_summary" in state


@pytest.mark.parametrize(("seeds", "flowers", "expected_seeds", "expected_flowers"), [
    ({}, {}, {}, {}),
    ({"daisy": 3}, {"rose": 2}, {"daisy": 3}, {"rose": 2}),
    ({"daisy": 3, "rose": 1, "lily": 0}, {"daisy": 5, "rose": 2, "lily": 0},
     {"daisy": 3, "rose": 1}, {"daisy": 5, "rose": 2}),
])
def test_ai_inventory_gardening_details_are_positive_and_read_only(api, seeds, flowers, expected_seeds, expected_flowers):
    module, _ = api
    state = ge.get_default_state()
    state["inventory"]["seeds"] = seeds.copy()
    state["inventory"]["flowers"] = flowers.copy()
    original = json.loads(json.dumps(state))
    counts = module._build_inventory_counts_for_ai(state)
    assert counts["seeds"] == expected_seeds
    assert counts["flowers"] == expected_flowers
    assert state == original


def test_ai_gardening_details_match_across_routes_without_changing_save(api, cat_clock):
    module, client = api
    session_id, _ = create_human_garden(client)
    now = cat_clock[0]
    pot = {"flower_id": "daisy", "growth_progress": 0, "watered": True, "last_growth_update": now}
    state = module.db_load_state(session_id)
    state["max_pots"] = 6
    state["pots"] = [
        None,
        {**pot, "watered": False},
        dict(pot),
        {**pot, "pest_active": True},
        {**pot, "growth_progress": ge.FLOWERS["daisy"]["grow_time"]},
        {**pot, "withered": True},
    ]
    state["inventory"]["seeds"] = {"daisy": 3, "rose": 1}
    state["inventory"]["flowers"] = {"daisy": 5, "rose": 2}
    ge.normalize_state(state, now)
    expected_pots = [
        {"slot": index, "flower_id": None if index == 1 else "daisy", "status": status}
        for index, status in enumerate(("empty", "needs_water", "growing", "pest_blocked", "ready", "withered"), 1)
    ]
    original = json.loads(json.dumps(state))
    assert module._build_pots_for_ai(state) == expected_pots
    assert module._build_inventory_counts_for_ai(state)["seeds"] == {"daisy": 3, "rose": 1}
    assert state == original
    module._ai_summary(state)
    assert state["pots"] == original["pots"]
    assert state["inventory"] == original["inventory"]
    headers = {"X-API-Key": "test-key"}
    for route in ("/api/status", "/api/cmd", "/api/cmd?compact=1"):
        module.db_save_state(session_id, state)
        before = module.db_load_state(session_id)
        if route == "/api/status":
            response = client.get(route, headers=headers, query_string={"session_id": session_id})
        else:
            response = client.post(route, headers=headers, json={"session_id": session_id, "command": "status"})
        assert response.status_code == 200
        result = response.get_json()["state"]
        assert result["pots"] == expected_pots
        assert result["inventory_counts"]["seeds"] == {"daisy": 3, "rose": 1}
        assert result["inventory_counts"]["flowers"] == {"daisy": 5, "rose": 2}
        after = module.db_load_state(session_id)
        assert after["pots"] == before["pots"]
        assert after["inventory"] == before["inventory"]


def test_ai_pot_status_respects_harvest_priority_and_legacy_pest(api):
    module, _ = api
    state = ge.get_default_state()
    mature = {"flower_id": "daisy", "growth_progress": ge.FLOWERS["daisy"]["grow_time"], "watered": False}
    state["pots"] = [dict(mature), {**mature, "pest_time": 1}, {**mature, "pest_time": 1, "pest_resolved": True}]
    assert [pot["status"] for pot in module._build_pots_for_ai(state)] == ["ready", "pest_blocked", "ready"]


@pytest.mark.parametrize(("pest_fields", "blocked"), [
    ({"pest_active": True}, True),
    ({"pest_active": False, "pest_resolved": True}, False),
    ({"pest_time": 1}, True),
    ({"pest_time": 4_000_000_000}, True),
    ({"pest_time": 1, "pest_resolved": True}, False),
])
def test_ai_pest_summaries_follow_harvest_blocker_before_normalization(pest_fields, blocked):
    import game_api as module

    state = ge.get_default_state()
    state["pots"][0] = {
        "flower_id": "daisy", "growth_progress": 10, "watered": True, **pest_fields,
    }
    pot = state["pots"][0]
    assert (ge.get_pot_harvest_blocker(state, 0, pot) == "pest") is blocked
    events = ge.refresh_garden_events(state, now=2_000_000_000)
    assert events["has_pests"] is blocked
    assert events["pest_pots"] == ([1] if blocked else [])
    assert module._build_pot_summary_for_ai(state)["pest_pots"] == int(blocked)


def test_ai_pest_summary_matches_pot_status_after_normalization():
    import game_api as module

    now = int(ge.time.time())
    state = ge.get_default_state()
    state["max_pots"] = 5
    pot = {"flower_id": "daisy", "growth_progress": 10, "watered": True,
           "last_growth_update": now}
    state["pots"] = [
        {**pot, "pest_active": True},
        {**pot, "pest_time": 1},
        {**pot, "pest_time": now + 100, "pest_resolved": True},
        {**pot, "pest_active": True, "pest_resolved": True},
        {**pot, "pest_active": True, "withered": True},
    ]
    summary = module._ai_summary(state)
    blocked_slots = [pot["slot"] for pot in summary["pots"] if pot["status"] == "pest_blocked"]
    assert blocked_slots == [1, 2]
    assert summary["garden_events"]["pest_pots"] == blocked_slots
    assert summary["garden_events"]["has_pests"] is True
    assert summary["pots_summary"]["pest_pots"] == len(blocked_slots)
    assert state["pots"][3]["pest_active"] is False
    assert ge.get_pot_harvest_blocker(state, 3, state["pots"][3]) != "pest"


def test_ai_pest_summaries_clear_after_treat_with_isolated_sqlite(monkeypatch):
    import sqlite3
    from contextlib import contextmanager
    import game_api as module

    now = int(ge.time.time())
    monkeypatch.setattr(ge.time, "time", lambda: now)
    monkeypatch.setattr(module, "API_KEY", "isolated-test-key")
    monkeypatch.setattr(module, "USE_POSTGRES", False)
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row

    @contextmanager
    def isolated_connection():
        yield connection

    monkeypatch.setattr(module, "_get_conn", isolated_connection)
    try:
        state = ge.get_default_state()
        state["ai_v5_update_notice_seen"] = True
        state["weather"] = "sunny"
        state["weather_change_time"] = now + 3600
        state["pots"][0] = {
            "flower_id": "daisy", "growth_progress": 10, "watered": True,
            "last_growth_update": now, "pest_active": True,
        }
        module.db_save_state("isolated-pest", state)
        client = module.app.test_client()
        headers = {"X-API-Key": "isolated-test-key"}
        before = client.get("/api/status?session_id=isolated-pest", headers=headers).get_json()["state"]
        assert before["garden_events"]["pest_pots"] == [1]
        assert before["pots_summary"]["pest_pots"] == 1
        response = client.post("/api/cmd?compact=1", headers=headers,
                               json={"session_id": "isolated-pest", "command": "treat 1"})
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["ok"] is True
        after = payload["state"]
        assert after["garden_events"]["pest_pots"] == []
        assert after["garden_events"]["has_pests"] is False
        assert after["pots_summary"]["pest_pots"] == 0
        assert after["pots"][0]["status"] != "pest_blocked"
    finally:
        connection.close()


def test_web_pot_status_matches_formal_status_on_both_routes(monkeypatch):
    import sqlite3
    from contextlib import contextmanager
    import game_api as module

    now = int(ge.time.time())
    monkeypatch.setattr(ge.time, "time", lambda: now)
    monkeypatch.setattr(module, "USE_POSTGRES", False)
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    connection.row_factory = sqlite3.Row

    @contextmanager
    def isolated_connection():
        yield connection

    monkeypatch.setattr(module, "_get_conn", isolated_connection)
    try:
        client = module.app.test_client()
        session_id, headers = create_human_garden(client)
        state = module.db_load_state(session_id)
        state["weather"] = "sunny"
        state["weather_change_time"] = now + 3600
        state["max_pots"] = 6
        pot = {"flower_id": "daisy", "growth_progress": ge.FLOWERS["daisy"]["grow_time"],
               "last_growth_update": now, "watered": True}
        state["pots"] = [
            dict(pot),
            {**pot, "pest_active": True},
            {**pot, "growth_progress": 10, "pest_active": True},
            {**pot, "growth_progress": 10, "watered": False},
            {**pot, "withered": True},
            {**pot, "growth_progress": 10},
        ]
        module.db_save_state(session_id, state)
        status = client.get(f"/web/status?session_id={session_id}", headers=headers)
        command = client.post("/web/cmd", headers=headers,
                              json={"session_id": session_id, "command": "status"})
        assert status.status_code == command.status_code == 200
        pots = status.get_json()["state"]["pots"]
        assert command.get_json()["state"]["pots"] == pots
        assert [pot["status"] for pot in pots] == [
            "ready", "pest_blocked", "pest_blocked", "needs_water", "withered", "growing",
        ]
        assert [(pot["ready"], pot["has_pest"]) for pot in (pots[0], pots[1], pots[2], pots[3])] == [
            (True, False), (False, True), (False, True), (False, False),
        ]
        assert pots[1]["remaining_seconds"] is None
        assert pots[2]["remaining_seconds"] is None

        for slot, expected in ((2, "ready"), (3, "growing")):
            response = client.post("/web/cmd", headers=headers,
                                   json={"session_id": session_id, "command": f"treat {slot}"})
            payload = response.get_json()
            assert response.status_code == 200 and payload["ok"] is True
            treated = payload["state"]["pots"][slot - 1]
            assert treated["status"] == expected
            assert treated["ready"] is (expected == "ready")
            assert treated["has_pest"] is False
            refreshed = client.get(f"/web/status?session_id={session_id}", headers=headers).get_json()
            assert refreshed["state"]["pots"][slot - 1] == treated
    finally:
        connection.close()


def test_compact_command_preserves_default_state_and_status(api, monkeypatch):
    module, client = api
    now = int(ge.time.time())
    monkeypatch.setattr(module.time, "time", lambda: now)
    session_id, _ = create_human_garden(client)
    saved = module.db_load_state(session_id)
    saved["cottage"]["items"]["ottoman"] = {"acquired_at": now, "source": "human"}
    saved["cottage"]["items"]["potted_plant"] = {"acquired_at": now, "source": "system"}
    saved["cat_care"]["water_bowl"]["remaining_portions"] = 2
    saved["inventory"]["seeds"] = {"daisy": 3, "rose": 1}
    saved["inventory"]["flowers"] = {"daisy": 5, "rose": 2}
    original_items = json.loads(json.dumps(saved["cottage"]["items"]))
    expected_owned = ge.get_cottage_public_summary(saved)["owned_items"]
    expected_ids = [item["id"] for item in expected_owned]
    module.db_save_state(session_id, saved)
    headers = {"X-API-Key": "test-key"}
    body = {"session_id": session_id, "command": "status"}

    client.get("/api/status", headers=headers, query_string={"session_id": session_id})
    default = client.post("/api/cmd", headers=headers, json=body).get_json()
    compact = client.post("/api/cmd?compact=1", headers=headers, json=body).get_json()
    status = client.get("/api/status", headers=headers, query_string={"session_id": session_id}).get_json()
    assert default["ok"] is compact["ok"] is True
    assert default["message"] == compact["message"]
    assert default["session_id"] == compact["session_id"] == session_id
    assert "purchasable_items" in default["state"]["cottage"]
    assert "pricing_profiles" in default["state"]["flower_shop"]
    assert "purchasable_items" in status["state"]["cottage"]
    assert "pricing_profiles" in status["state"]["flower_shop"]
    complete_owned_fields = {"id", "name", "category", "slot_key", "asset_key", "acquired_at", "source"}
    for payload in (status, default):
        owned_items = payload["state"]["cottage"]["owned_items"]
        assert [item["id"] for item in owned_items] == expected_ids
        assert all(complete_owned_fields <= item.keys() for item in owned_items)
        assert "water_servings" in payload["state"]["inventory_counts"]
        assert "weather_emoji" in payload["state"]
        assert payload["state"]["inventory_counts"]["seeds"] == {"daisy": 3, "rose": 1}
        assert payload["state"]["inventory_counts"]["flowers"] == {"daisy": 5, "rose": 2}
        assert all(set(pot) == {"slot", "flower_id", "status"} for pot in payload["state"]["pots"])
        assert payload["state"]["cottage"]["cat_area"]["water_bowl"]["remaining_portions"] == 2
    assert "purchasable_items" not in compact["state"]["cottage"]
    assert "pricing_profiles" not in compact["state"]["flower_shop"]
    assert "water_servings" not in compact["state"]["inventory_counts"]
    assert "weather_emoji" not in compact["state"]
    assert "weather" in compact["state"]
    assert "is_open" in compact["state"]["flower_shop"]
    assert "slots" in compact["state"]["flower_shop"]
    assert all("is_open" not in slot for slot in compact["state"]["flower_shop"]["slots"])
    assert compact["state"]["cottage"]["cat_area"]["water_bowl"]["remaining_portions"] == 2
    assert all(set(pot) == {"slot", "flower_id", "status"} for pot in compact["state"]["pots"])
    assert compact["state"]["inventory_counts"]["seeds"] == {"daisy": 3, "rose": 1}
    assert compact["state"]["inventory_counts"]["flowers"] == {"daisy": 5, "rose": 2}
    compact_owned_items = compact["state"]["cottage"]["owned_items"]
    assert compact_owned_items == [{"id": item_id} for item_id in expected_ids]
    assert all(set(item) == {"id"} for item in compact_owned_items)
    assert {"ottoman", "potted_plant"} <= set(expected_ids)
    assert len(expected_ids) == len(set(expected_ids))
    assert module.db_load_state(session_id)["cottage"]["items"] == original_items
    expected_compact_state = json.loads(json.dumps(default["state"]))
    expected_compact_state["cottage"].pop("purchasable_items")
    expected_compact_state["flower_shop"].pop("pricing_profiles")
    expected_compact_state["inventory_counts"].pop("water_servings")
    expected_compact_state.pop("weather_emoji")
    expected_compact_state["cottage"]["owned_items"] = compact_owned_items
    expected_compact_state["bouquet_options"] = [
        {"bouquet_id": option["bouquet_id"], "can_make": option["can_make"], "missing": option["missing"]}
        for option in expected_compact_state["bouquet_options"]
    ]
    for slot in expected_compact_state["flower_shop"]["slots"]:
        slot.pop("is_open", None)
    assert compact["state"] == expected_compact_state


def test_compact_command_returns_empty_owned_items_array(api):
    module, client = api
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["cottage"]["items"] = {}
    state["encyclopedia"] = []
    module.db_save_state(session_id, state)

    response = client.post("/api/cmd?compact=1", headers={"X-API-Key": "test-key"},
                           json={"session_id": session_id, "command": "status"})

    assert response.status_code == 200
    assert response.get_json()["state"]["cottage"]["owned_items"] == []


def test_compact_command_only_removes_audited_display_fields(api, monkeypatch):
    module, client = api
    now = int(ge.time.time())
    monkeypatch.setattr(module.time, "time", lambda: now)
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["inventory"]["items"]["water"] = 7
    state["cat_care"]["water_bowl"]["remaining_portions"] = 2
    state["flower_shop"] = {
        "established_at": now - 1000,
        "launched_at": now - 50,
        "shelf_capacity": 2,
        "business_start_minute": ge.datetime.fromtimestamp(now, ge.DISPLAY_TIMEZONE).hour * 60
        + ge.datetime.fromtimestamp(now, ge.DISPLAY_TIMEZONE).minute,
        "pending_business_start_minute": None,
        "pending_business_effective_at": None,
        "slots": [
            {
                "instance_id": "compact-audit-bouquet",
                "bouquet_id": "first_meeting",
                "components": {"tulip": 2, "rose": 1},
                "listed_at": now - 10,
                "last_settled_at": now - 10,
                "base_price": 55,
                "will_sell": False,
                "sale_business_seconds_remaining": 0,
            },
            None,
        ],
    }
    module.db_save_state(session_id, state)
    saved_before = module.db_load_state(session_id)
    headers = {"X-API-Key": "test-key"}
    query = {"session_id": session_id}
    body = {"session_id": session_id, "command": "status"}

    status = client.get("/api/status", headers=headers, query_string=query).get_json()["state"]
    default = client.post("/api/cmd", headers=headers, json=body).get_json()["state"]
    compact = client.post("/api/cmd?compact=1", headers=headers, json=body).get_json()["state"]

    for full in (status, default):
        assert full["inventory_counts"]["water_servings"] == 7
        assert "weather_emoji" in full
        assert "weather" in full
        assert full["flower_shop"]["is_open"] is True
        assert full["flower_shop"]["slots"][0]["is_open"] is True
        assert full["flower_shop"]["slots"][1] == {"slot": 2, "empty": True}
        assert full["cottage"]["cat_area"]["water_bowl"]["remaining_portions"] == 2

    assert "water_servings" not in compact["inventory_counts"]
    assert "weather_emoji" not in compact
    assert compact["weather"] == status["weather"]
    assert compact["flower_shop"]["is_open"] is True
    assert compact["flower_shop"]["slots"][0]["empty"] is False
    assert compact["flower_shop"]["slots"][1] == {"slot": 2, "empty": True}
    assert all("is_open" not in slot for slot in compact["flower_shop"]["slots"])
    assert compact["cottage"]["cat_area"]["water_bowl"]["remaining_portions"] == 2

    saved_after = module.db_load_state(session_id)
    assert saved_after["inventory"]["items"]["water"] == saved_before["inventory"]["items"]["water"] == 7
    assert saved_after["flower_shop"]["slots"] == saved_before["flower_shop"]["slots"]
    assert saved_after["cat_care"]["water_bowl"] == saved_before["cat_care"]["water_bowl"]


def test_compact_command_success_and_failure_keep_dynamic_state(api):
    module, client = api
    session_id, _ = create_human_garden(client)
    headers = {"X-API-Key": "test-key"}
    plant = client.post("/api/cmd?compact=1", headers=headers,
                        json={"session_id": session_id, "command": "plant daisy 1"}).get_json()
    assert plant["ok"] is True
    assert "盆1" in plant["message"] and "water 1" in plant["message"]
    assert plant["state"]["pots_summary"]["growing_pots"] == 1
    assert plant["state"]["inventory_counts"]["seed_total"] == 2
    failed = client.post("/api/cmd?compact=1", headers=headers,
                         json={"session_id": session_id, "command": "harvest 1"}).get_json()
    assert failed["ok"] is False
    assert "没浇水" in failed["message"]
    assert failed["session_id"] == session_id
    state = failed["state"]
    assert {"money", "cat_summary", "pots_summary", "inventory_counts", "garden_events",
            "latest_event", "bouquet_inventory"} <= state.keys()
    assert "owned_items" in state["cottage"]
    assert {"established", "is_open", "slots", "eligibility_progress", "business_start_minute",
            "pending_business_start_minute", "pending_business_effective_at"} <= state["flower_shop"].keys()
    assert "purchasable_items" not in state["cottage"]
    assert "pricing_profiles" not in state["flower_shop"]


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


def test_public_help_matches_current_pest_collectible_and_weather_rules(api):
    _, client = api
    info = client.get("/api/info").get_json()
    help_text = client.get("/api/help", headers={"X-API-Key": "test-key"}).get_json()["message"]
    info_text = "\n".join(info["features"])
    pest_rule = "种植时确定虫害，达到触发点后暂停生长，治疗后继续"
    assert pest_rule in info_text
    assert pest_rule in help_text
    assert "害虫：每5分钟最多检查一次" not in help_text
    assert "分钟内不治疗会枯萎" not in help_text
    assert "猫咪收集品：每5分钟" not in help_text
    assert "首次实际吃喝后开启" in help_text
    assert "完整来访结束或外出回家时可能带回" in help_text
    assert "离线期间不补算多轮天气" not in help_text
    assert "离线期间的天气事件按时间顺序补算" in help_text


def test_collectible_catalog_conditions_match_current_unlock_behavior(api):
    module, client = api
    catalog = client.get("/api/catalog").get_json()["collectibles"]
    session_id, headers = create_human_garden(client)
    web_state = client.get(f"/web/status?session_id={session_id}", headers=headers).get_json()["state"]
    web_catalog = {item["id"]: item for item in web_state["collectible_catalog"]}
    assert len(catalog) == 16

    for item in catalog:
        web_item = web_catalog[item["id"]]
        assert web_item["unlock_affection"] == item["unlock_affection"]
        assert web_item["unlock_hint"] == item["unlock_hint"]
        state = ge.get_default_state()
        if item["rarity"] == "common":
            assert item["unlock_affection"] is None
            assert "第一次实际吃饭或喝水后" in item["unlock_hint"]
            state["cat_max_affection"] = 100
            assert not module.is_collectible_unlocked(state, item)
            state["cat_collectibles_unlocked"] = True
            assert module.is_collectible_unlocked(state, item)
        else:
            threshold = item["unlock_affection"]
            assert threshold == 30
            assert f"历史最高亲密度{threshold}" in item["unlock_hint"]
            state["cat_max_affection"] = threshold - 1
            assert not module.is_collectible_unlocked(state, item)
            state["cat_max_affection"] = threshold
            assert module.is_collectible_unlocked(state, item)


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


def test_api_info_directs_ai_to_existing_human_created_garden(api):
    _, client = api
    payload = client.get("/api/info").get_json()
    public_text = json.dumps(payload, ensure_ascii=False)
    assert "/api/register" not in public_text
    assert "人类在网页端" in public_text
    assert "有效 session_id" in public_text
    assert "AI/API 端不能注册或创建新存档" in public_text
    assert any("/api/cmd" in endpoint for endpoint in payload["endpoints"])
    assert client.post("/api/register", headers={"X-API-Key": "test-key"}).status_code == 403


@pytest.mark.parametrize(("basic_food", "premium_food"), [(13, 0), (0, 9), (5, 4), (0, 0)])
def test_ai_inventory_counts_expose_food_types_and_preserve_legacy_alias(api, basic_food, premium_food):
    module, client = api
    state = ge.get_default_state()
    state["cat_state"]["next_visit_at"] = int(ge.time.time()) + 3600
    state["inventory"] = {
        "seeds": {"daisy": 2, "rose": 3},
        "flowers": {"rose": 4},
        "items": {"basic_food": basic_food, "premium_food": premium_food, "water": 7},
    }
    original_inventory = json.loads(json.dumps(state["inventory"]))
    original_state = json.loads(json.dumps(state))
    counts = module._build_inventory_counts_for_ai(state)
    assert counts["basic_food_servings"] == basic_food
    assert counts["premium_food_servings"] == premium_food
    assert counts["cat_food_servings"] == basic_food
    assert counts["cat_food_servings"] == counts["basic_food_servings"]
    assert state["inventory"] == original_inventory
    assert state == original_state

    for route in ("/api/status", "/api/cmd", "/api/cmd?compact=1"):
        module.db_save_state("food-counts", state)
        if route == "/api/status":
            response = client.get(f"{route}?session_id=food-counts", headers={"X-API-Key": "test-key"})
        else:
            response = client.post(route, headers={"X-API-Key": "test-key"},
                                   json={"session_id": "food-counts", "command": "help"})
        assert response.status_code == 200
        counts = response.get_json()["state"]["inventory_counts"]
        assert counts["seed_types"] == 2
        assert counts["seed_total"] == 5
        assert counts["flower_types"] == 1
        assert counts["flower_total"] == 4
        assert counts["basic_food_servings"] == basic_food
        assert counts["premium_food_servings"] == premium_food
        assert counts["cat_food_servings"] == basic_food
        assert counts["water_servings"] == 7


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

    response = client.get(
        f"/api/status?session_id={session_id}",
        headers={"X-API-Key": "test-key"},
    )
    payload = response.get_json()
    pot_line = next(
        line for line in payload["message"].splitlines()
        if line.startswith("  盆1:")
    )
    assert "有虫害" in pot_line
    assert "生长暂停" in pot_line
    assert "需先处理虫害" in pot_line
    assert "还需约" not in pot_line
    assert payload["state"]["garden_events"]["has_pests"] is True
    assert payload["state"]["garden_events"]["pest_pots"] == [1]


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
    assert web_state["recent_events"][-1] == "💐 送出了一束「初见」，还附了一张小卡片。"
    gift_events = [
        event["text"]
        for event in module.db_load_state(session_id)["events"]
        if "送出了一束「初见」" in event.get("text", "")
    ]
    assert gift_events == ["💐 送出了一束「初见」，还附了一张小卡片。"]
    assert all("返回面测试花园" not in event for event in gift_events)

    catalog = client.get("/api/catalog").get_json()
    assert len(catalog["bouquets"]) == 12


def test_bouquet_options_compact_projection_preserves_dynamic_facts(api):
    module, client = api
    session_id, _human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["encyclopedia"] = list(ge.FLOWERS)
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    original_state = json.loads(json.dumps(state))
    original_recipes = json.loads(json.dumps(ge.BOUQUETS))
    expected_options = ge.get_bouquet_options(state)
    expected_ids = [option["bouquet_id"] for option in expected_options]
    assert len(expected_options) == len(ge.BOUQUETS)
    assert state == original_state
    module.db_save_state(session_id, state)
    headers = {"X-API-Key": "test-key"}

    status_response = client.get("/api/status", headers=headers,
                                 query_string={"session_id": session_id})
    default_response = client.post("/api/cmd", headers=headers,
                                   json={"session_id": session_id, "command": "status"})
    compact_response = client.post("/api/cmd?compact=1", headers=headers,
                                   json={"session_id": session_id, "command": "status"})
    assert (
        status_response.status_code == default_response.status_code == compact_response.status_code == 200
    )

    full_fields = {"bouquet_id", "name", "components", "can_make", "missing"}
    for response in (status_response, default_response):
        options = response.get_json()["state"]["bouquet_options"]
        assert options == expected_options
        assert [option["bouquet_id"] for option in options] == expected_ids
        assert all(set(option) == full_fields for option in options)

    compact_options = compact_response.get_json()["state"]["bouquet_options"]
    assert compact_options == [
        {
            "bouquet_id": option["bouquet_id"],
            "can_make": option["can_make"],
            "missing": option["missing"],
        }
        for option in expected_options
    ]
    assert all(set(option) == {"bouquet_id", "can_make", "missing"} for option in compact_options)
    assert [option["bouquet_id"] for option in compact_options] == expected_ids
    by_id = {option["bouquet_id"]: option for option in compact_options}
    assert by_id["first_meeting"]["can_make"] is True
    assert by_id["first_meeting"]["missing"] == {}
    assert by_id["morning_light"]["can_make"] is False
    assert by_id["morning_light"]["missing"] == {"sunflower": 1, "carnation": 1, "daisy": 1}

    catalog = client.get("/api/catalog").get_json()["bouquets"]
    assert set(catalog) == set(ge.BOUQUETS)
    for bouquet_id, recipe in ge.BOUQUETS.items():
        assert catalog[bouquet_id]["name"] == recipe["name"]
        assert catalog[bouquet_id]["components"] == recipe["components"]
    saved = module.db_load_state(session_id)
    assert saved["inventory"]["flowers"] == original_state["inventory"]["flowers"]
    assert saved["encyclopedia"] == original_state["encyclopedia"]
    assert ge.BOUQUETS == original_recipes


@pytest.mark.parametrize("cmd_url", ["/api/cmd", "/api/cmd?compact=1"])
def test_flower_shop_and_bouquet_inventory_have_public_summary_only(api, cmd_url):
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
        cmd_url, headers=ai_headers,
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
    assert active_shop["shop_buff_collectible_id"] is None
    assert "shop_buff_windows" not in active_shop
    assert "buff_roll" not in active_shop

    saved = module.db_load_state(session_id)
    saved["flower_shop"]["shop_buff_collectible_id"] = ge.CAT_COLLECTIBLES[0]["id"]
    module.db_save_state(session_id, saved)
    assert module.db_load_state(session_id)["flower_shop"]["shop_buff_collectible_id"] == ge.CAT_COLLECTIBLES[0]["id"]
    responses = [
        client.get(f"/api/status?session_id={session_id}", headers=ai_headers),
        client.get(f"/web/status?session_id={session_id}", headers=human_headers),
        client.post(cmd_url, headers=ai_headers, json={"session_id": session_id, "command": "status"}),
    ]
    for response in responses:
        assert response.get_json()["state"]["flower_shop"]["shop_buff_collectible_id"] == ge.CAT_COLLECTIBLES[0]["id"]


@pytest.mark.parametrize("source_id", ["missing", "invalid"])
def test_old_or_invalid_shop_buff_source_loads_as_generic(api, source_id):
    module, client = api
    session_id, headers = create_human_garden(client)
    now = int(ge.time.time())
    state = module.db_load_state(session_id)
    state["flower_shop"].update(established_at=now - 100, shelf_capacity=3,
                                shop_buff_until=now + 3600, slots=[None] * 3)
    if source_id == "missing":
        state["flower_shop"].pop("shop_buff_collectible_id", None)
    else:
        state["flower_shop"]["shop_buff_collectible_id"] = "invalid"
    write_raw_state(module, session_id, state)
    shop = client.get(f"/web/status?session_id={session_id}", headers=headers).get_json()["state"]["flower_shop"]
    assert shop["shop_buff_active"] is True
    assert shop["shop_buff_collectible_id"] is None
    assert module.db_load_state(session_id)["flower_shop"]["shop_buff_collectible_id"] is None


@pytest.mark.parametrize("cmd_url", ["/api/cmd", "/api/cmd?compact=1"])
def test_flower_shop_listing_summary_exposes_price_but_hides_random_facts(api, monkeypatch, cmd_url):
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
        cmd_url,
        headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "list_bouquet instance_id=api-listing slot=1"},
    )
    assert response.status_code == 200
    public_state = response.get_json()["state"]
    public_slot = public_state["flower_shop"]["slots"][0]
    assert public_slot["empty"] is False
    assert public_slot["name"] == "初见"
    assert public_slot["current_price"] == 55
    assert public_slot["price_stage"]
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
        if "送出了一束「初见」" in event.get("text", "")
    ]
    assert first_gift_events == ["💐 送出了一束「初见」。"]
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
        if "送出了一束「初见」" in event.get("text", "")
    ]
    assert all_gift_events == [
        "💐 送出了一束「初见」。",
        "💐 送出了一束「初见」。",
    ]
    assert all("返回面测试花园" not in event for event in all_gift_events)
    unread_again = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert unread_again["has_unread_bouquet_gifts"] is True
    assert unread_again["unread_bouquet_gift_count"] == 1
