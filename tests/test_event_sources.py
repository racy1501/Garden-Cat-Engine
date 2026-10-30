"""操作事件来源：入口负责传入来源，自动结算始终保持系统来源。"""

import game_engine as ge
import pytest
from urllib.parse import quote

from test_api_response_shape import api, adopted_cat_state, cat_clock, create_human_garden


def test_web_and_ai_sale_events_keep_their_own_sources(api, cat_clock):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["inventory"]["flowers"] = {"rose": 1}
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    module.db_save_state(session_id, state)

    web_payload = client.post(
        "/web/cmd",
        headers=human_headers,
        json={"session_id": session_id, "command": "sell rose"},
    ).get_json()
    assert web_payload["ok"] is True
    assert web_payload["state"]["new_events"][-1] == {
        "time": cat_clock[0],
        "text": "卖了1朵玫瑰，赚了14块",
        "source": "human",
        "source_label": "人类",
        "area": "garden",
    }

    ai_state = ge.get_default_state()
    ai_state["inventory"]["flowers"] = {"rose": 1}
    module.db_save_state("ai-sale-source", ai_state)
    ai_payload = client.post(
        "/api/cmd",
        headers={"X-API-Key": "test-key"},
        json={"session_id": "ai-sale-source", "command": "sell rose"},
    ).get_json()
    assert ai_payload["ok"] is True
    assert ai_payload["state"]["latest_event"] == "卖了1朵玫瑰，赚了14块"
    assert module.db_load_state("ai-sale-source")["events"][-1]["source"] == "ai"

    all_sale_state = ge.get_default_state()
    all_sale_state["inventory"]["flowers"] = {"daisy": 1, "rose": 1}
    assert "卖掉所有花" in ge.process_command(all_sale_state, "sell all", event_source="human")
    assert all_sale_state["events"][-1]["source"] == "human"


def test_automatic_event_is_system_even_during_human_status_request(api, cat_clock):
    module, client = api
    session_id, headers = create_human_garden(client)
    state = adopted_cat_state()
    state[module.WEB_TOKEN_FIELD] = module.db_load_state(session_id)[module.WEB_TOKEN_FIELD]
    state["events"] = []
    state["cat_state"]["next_outing_at"] = cat_clock[0]
    module.db_save_state(session_id, state)

    payload = client.get(
        f"/web/status?session_id={session_id}", headers={**headers, "X-Garden-Live": "1"}
    ).get_json()
    event = payload["state"]["new_events"][-1]
    assert event["text"] == "栗子出门溜达了一会儿。"
    assert event["source"] == "system"
    assert event["source_label"] == "系统"


def test_failed_sale_creates_no_event_and_legacy_event_stays_readable(api, cat_clock):
    module, client = api
    session_id, headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["events"] = [{"time": cat_clock[0] - 1, "text": "旧存档事件"}]
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    module.db_save_state(session_id, state)

    payload = client.post(
        "/web/cmd",
        headers=headers,
        json={"session_id": session_id, "command": "sell rose"},
    ).get_json()
    assert "没有这种花" in payload["message"]
    assert payload["state"]["new_events"] == []
    assert payload["state"]["recent_event_records"] == [
        {"time": cat_clock[0] - 1, "text": "旧存档事件"}
    ]


@pytest.mark.parametrize("source", ["human", "ai"])
def test_plant_and_pet_events_keep_actor_and_cat_name(cat_clock, source):
    state = adopted_cat_state()
    state["events"] = []
    state["cat_last_pet_real_time"] = 0
    state["inventory"]["seeds"]["daisy"] = 1
    assert ge.execute_command(state, "plant daisy 1", event_source=source).ok
    assert ge.execute_command(state, "pet", event_source=source).ok
    assert [(e["text"], e["source"]) for e in state["events"]] == [
        ("在盆1种下了雏菊", source), ("摸了摸栗子", source),
    ]
    before = list(state["events"])
    assert not ge.execute_command(state, "pet", event_source=source).ok
    assert state["events"] == before


@pytest.mark.parametrize("command,expected", [
    ("feed basic", "给粮碗补充了"),
    ("refill_food basic", "给粮碗补充了"),
    ("give_water", "给水碗补满了水"),
    ("refill_water", "给水碗补满了水"),
    ("give_treat", "给栗子吃了零食"),
    ("play ball", "和栗子玩了一会儿"),
    ("switch_food premium", "将猫粮切换为"),
])
def test_cat_care_records_one_successful_action(cat_clock, monkeypatch, command, expected):
    state = adopted_cat_state()
    state["events"] = []
    state["inventory"]["items"].update(basic_food=5, premium_food=5, cat_treat=2, ball=2)
    state["cat_care"]["food_bowl"]["remaining_portions"] = 0
    state["cat_care"]["water_bowl"]["remaining_portions"] = 0
    monkeypatch.setattr(ge, "_roll_interaction_acceptance", lambda *args: True)
    result = ge.execute_command(state, command, event_source="ai")
    assert result.ok
    matches = [event for event in state["events"] if expected in event["text"]]
    assert len(matches) == 1 and matches[0]["source"] == "ai"


def test_treat_and_batch_water_record_once_and_failures_do_not(cat_clock):
    state = ge.get_default_state()
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    state["weather"] = "sunny"
    state["inventory"]["seeds"]["daisy"] = 2
    assert ge.execute_command(state, "plant daisy 1", event_source="human").ok
    assert ge.execute_command(state, "plant daisy 2", event_source="human").ok
    state["events"] = []
    assert ge.execute_command(state, "water all", event_source="human").ok
    assert [(e["text"], e["source"]) for e in state["events"]] == [("给2盆花浇了水", "human")]
    state["pots"][0]["pest_active"] = True
    assert ge.execute_command(state, "treat 1", event_source="ai").ok
    assert state["events"][-1]["text"] == "处理了盆1的虫害"
    assert state["events"][-1]["source"] == "ai"
    before = list(state["events"])
    assert not ge.execute_command(state, "treat 1", event_source="ai").ok
    assert not ge.execute_command(state, "plant daisy 1", event_source="human").ok
    assert state["events"] == before


def test_web_history_shows_human_and_ai_plant_sources(api, cat_clock):
    module, client = api
    sid, headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    module.db_save_state(sid, state)
    assert client.post("/web/cmd", headers=headers, json={"session_id": sid, "command": "plant daisy 1"}).get_json()["ok"]
    assert client.post("/api/cmd", headers={"X-API-Key": "test-key"}, json={"session_id": sid, "command": "plant daisy 2"}).get_json()["ok"]
    events = client.get(f"/web/status?session_id={sid}", headers=headers).get_json()["state"]["recent_event_records"]
    assert [(e["source"], e["source_label"]) for e in events if "种下了雏菊" in e["text"]] == [("human", "人类"), ("ai", "AI")]


def test_command_names_are_decoded_and_saved_as_event_snapshots(api, cat_clock):
    module, client = api
    sid, headers = create_human_garden(client)
    state = adopted_cat_state()
    state[module.WEB_TOKEN_FIELD] = module.db_load_state(sid)[module.WEB_TOKEN_FIELD]
    state["inventory"]["seeds"]["daisy"] = 2
    state["cat_last_pet_real_time"] = 0
    state["events"] = [{"time": cat_clock[0] - 1, "text": "旧事件", "source": "ai"}]
    module.db_save_state(sid, state)
    human_headers = {**headers, "X-Garden-Human-Name": quote("阿屿"), "X-Garden-Owner-Name": quote("错误名字")}
    human = client.post("/web/cmd", headers=human_headers, json={"session_id": sid, "command": "plant daisy 1"}).get_json()
    assert human["ok"]
    ai_headers = {"X-API-Key": "test-key", "X-Garden-Owner-Name": quote("砚川"), "X-Garden-Human-Name": quote("错误名字")}
    ai = client.post("/api/cmd?compact=1", headers=ai_headers, json={"session_id": sid, "command": "pet"}).get_json()
    assert ai["ok"]
    assert client.post("/api/cmd", headers=ai_headers, json={"session_id": sid, "command": "pet"}).get_json()["ok"] is False
    # 后续不同请求头不能改写已经写入的用户名。
    web = client.get(f"/web/status?session_id={sid}", headers={**headers, "X-Garden-Human-Name": quote("新名字")}).get_json()["state"]
    records = web["recent_event_records"]
    assert [(e["source"], e.get("source_name")) for e in records] == [("ai", None), ("human", "阿屿"), ("ai", "砚川")]
    assert records[0]["source_label"] == "AI"
    assert [e["text"] for e in records[1:]] == ["在盆1种下了雏菊", "摸了摸栗子"]
    saved = module.db_load_state(sid)["events"]
    assert [e.get("source_name") for e in saved] == [None, "阿屿", "砚川"]


@pytest.mark.parametrize("source,name", [("human", ""), ("ai", "  "), ("system", "不应保存")])
def test_empty_name_and_system_events_keep_fallback(source, name):
    state = ge.get_default_state()
    ge.add_event(state, "事件", source=source, source_name=name)
    assert "source_name" not in state["events"][-1]


def test_names_flow_through_existing_harvest_and_food_events(cat_clock):
    state = adopted_cat_state()
    state["events"] = []
    state["inventory"]["items"]["basic_food"] = 5
    state["cat_care"]["food_bowl"]["remaining_portions"] = 0
    state["pots"][0] = {"flower_id": "daisy", "watered": True,
                        "planted_time": cat_clock[0] - 1000,
                        "growth_progress": ge.FLOWERS["daisy"]["grow_time"],
                        "last_growth_update": cat_clock[0]}
    assert ge.execute_command(state, "harvest 1", event_source="human", source_name="阿屿").ok
    assert ge.execute_command(state, "feed basic", event_source="ai", source_name="砚川").ok
    assert next(e for e in state["events"] if "收获了" in e["text"])["source_name"] == "阿屿"
    assert next(e for e in state["events"] if "给粮碗补充" in e["text"])["source_name"] == "砚川"


def test_named_events_respect_history_limit():
    state = ge.get_default_state()
    for timestamp in range(51):
        ge.add_event(state, str(timestamp), now=timestamp, source="ai", source_name="砚川")
    assert len(state["events"]) == 50
    assert state["events"][0]["text"] == "1"
    assert all(e["source_name"] == "砚川" for e in state["events"])
