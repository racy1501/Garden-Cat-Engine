"""统一手记的地点、保留上限和接口边界。"""

import game_engine as ge

from test_api_response_shape import api, cat_clock, create_human_garden


def test_history_keeps_latest_50_by_time_and_preserves_legacy():
    state = ge.get_default_state()
    state["events"] = [{"time": 1, "text": "旧事件"}]
    for timestamp in range(2, 52):
        ge.add_event(state, str(timestamp), now=timestamp, source="ai", area="garden")
    assert len(state["events"]) == 50
    assert [e["time"] for e in state["events"]] == list(range(2, 52))
    ge.add_event(state, "离线旧事件", now=1, area="flower_shop")
    assert all(e["text"] != "离线旧事件" for e in state["events"])
    assert state["events"][-1]["source"] == "ai"
    assert state["events"][-1]["area"] == "garden"

    state["events"] += [{"time": 100, "text": "未知地点", "area": ["invalid"]},
                        {"time": 101, "text": "旧格式"}]
    ge.normalize_state(state)
    assert len(state["events"]) == 50
    assert "area" not in state["events"][-2]
    assert "area" not in state["events"][-1]
    ge.add_event(state, "未知分类", now=102, source="human", area="invalid")
    assert state["events"][-1]["source"] == "human"
    assert "area" not in state["events"][-1]


def test_shop_and_cottage_events_preserve_real_actor(cat_clock, monkeypatch):
    now = cat_clock[0]
    state = ge.get_default_state()
    state["money"] = 10000
    state["flower_shop"] = {**ge._default_flower_shop_state(), "established_at": now - 1,
                            "shelf_capacity": 3, "slots": [None] * 3}
    assert ge.execute_command(state, "buy_flower_shop_freshener", event_source="human").ok
    assert ge.execute_command(state, "set_flower_shop_hours 22:00", event_source="ai").ok
    assert ge.execute_command(state, "buy_cottage_furniture floor_lamp", event_source="human").ok
    events = state["events"]
    assert any(e.get("area") == "flower_shop" and e["source"] == "human" and "保鲜设备" in e["text"] for e in events)
    assert any(e.get("area") == "flower_shop" and e["source"] == "ai" and "22:00–次日 08:00" in e["text"] for e in events)
    assert any(e.get("area") == "cottage" and e["source"] == "human" and "落地灯" in e["text"] for e in events)

    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    state["encyclopedia"] = ["tulip", "baby_breath"]
    assert ge.execute_command(state, "craft_bouquet bouquet_id=first_meeting", event_source="ai").ok
    instance_id = state["bouquet_inventory"][0]["instance_id"]
    assert ge.execute_command(state, f"gift_bouquet instance_id={instance_id}", event_source="ai").ok
    gift_events = [e for e in state["events"] if "送出了一束" in e["text"]]
    assert len(gift_events) == len(state["bouquet_gifts"]) == 1
    assert gift_events[0]["area"] == "flower_shop" and gift_events[0]["source"] == "ai"
    assert any(e.get("area") == "flower_shop" and e["source"] == "ai" and "制作了一束" in e["text"] for e in state["events"])


def test_cottage_reward_recorded_on_harvest_but_not_old_save_sync(cat_clock):
    now = cat_clock[0]
    state = ge.get_default_state()
    state["pots"][0] = {"flower_id": "baby_breath", "planted_time": now - 2000,
                        "watered": True, "growth_progress": ge.FLOWERS["baby_breath"]["grow_time"],
                        "last_growth_update": now}
    assert ge.execute_command(state, "harvest 1", event_source="human").ok
    assert any(e.get("area") == "garden" and e["source"] == "human" and "收获" in e["text"] for e in state["events"])
    rewards = [e for e in state["events"] if e.get("area") == "cottage" and "纪念物" in e["text"]]
    assert len(rewards) == 1 and "白黄小花花器" in rewards[0]["text"]
    ge.sync_cottage_rewards(state, now, record_events=True)
    assert len([e for e in state["events"] if e.get("area") == "cottage"]) == 1
    old = ge.get_default_state()
    old["encyclopedia"] = ["baby_breath", "lisianthus"]
    assert len(ge.sync_cottage_rewards(old, now)) == 2
    assert old["events"] == []


def test_api_does_not_return_history_but_web_returns_50(api, cat_clock):
    module, client = api
    sid, web_headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    ai_headers = {"X-API-Key": "test-key"}
    body = {"session_id": sid, "command": "status"}

    def lengths():
        responses = [client.get(f"/api/status?session_id={sid}", headers=ai_headers),
                     client.post("/api/cmd", headers=ai_headers, json=body),
                     client.post("/api/cmd?compact=1", headers=ai_headers, json=body)]
        for response in responses:
            assert response.status_code == 200
            result = response.get_json()["state"]
            assert not {"events", "recent_events", "recent_event_records", "new_events"} & result.keys()
        return [len(response.get_data(as_text=True)) for response in responses]

    state["events"] = []
    module.db_save_state(sid, state)
    empty = lengths()
    state["events"] = [{"time": cat_clock[0] - i, "text": f"历史{i}", "area": "garden"} for i in range(50)]
    module.db_save_state(sid, state)
    filled = lengths()
    assert filled == empty
    web = client.get(f"/web/status?session_id={sid}", headers=web_headers).get_json()["state"]
    assert len(web["recent_events"]) == len(web["recent_event_records"]) == 50
    assert all(record["area"] == "garden" for record in web["recent_event_records"])
    assert web["recent_event_records"] == sorted(web["recent_event_records"], key=lambda e: e["time"])
    print(f"API response characters without/with 50 history: {empty} / {filled}")
