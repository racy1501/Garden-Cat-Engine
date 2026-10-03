"""操作事件来源：入口负责传入来源，自动结算始终保持系统来源。"""

import game_engine as ge

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
        "text": "卖了1朵玫瑰，赚了11块",
        "source": "human",
        "source_label": "人类",
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
    assert ai_payload["state"]["latest_event"] == "卖了1朵玫瑰，赚了11块"
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
