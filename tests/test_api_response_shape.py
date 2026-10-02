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
def test_api_latest_event_only_reports_request_events(api, cat_clock, endpoint):
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
    assert query()["state"]["latest_event"] == "栗子回家了。"
    for delta in (0, 60, 180):
        cat_clock[0] = start + 21600 + delta
        result = query()
        assert result["state"]["latest_event"] == ""
        assert "出门" not in result["message"] and "回家" not in result["message"]
    loaded = module.db_load_state("cat-events")
    assert loaded["cat_state"]["next_outing_at"] == start + 25200
    assert loaded["events"][-1] == {"time": start + 19800, "text": "栗子回家了。"}
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


def test_ai_bouquet_command_and_web_collection_state(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["inventory"]["flowers"] = {"tulip": 2, "rose": 2}
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
    assert len(created.get_json()["state"]["bouquet_options"]) == 8

    web_state = client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["state"]
    assert len(web_state["bouquet_gifts"]) == 1
    assert web_state["bouquet_gifts"][0]["message"] == "给你的春天"
    assert web_state["bouquet_gifts"][0]["components"] == {"tulip": 2, "rose": 2}
    assert web_state["recent_events"][-1] == "💐 小机送给你一束「初见」，还附了一张小卡片。"
    gift_events = [
        event["text"]
        for event in module.db_load_state(session_id)["events"]
        if "送给你一束「初见」" in event.get("text", "")
    ]
    assert gift_events == ["💐 小机送给你一束「初见」，还附了一张小卡片。"]
    assert all("返回面测试花园" not in event for event in gift_events)

    catalog = client.get("/api/catalog").get_json()
    assert len(catalog["bouquets"]) == 8


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
    state["inventory"]["flowers"] = {"tulip": 2, "rose": 2}
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
    state["inventory"]["flowers"] = {"tulip": 2, "rose": 2}
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
