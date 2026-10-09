import game_engine as ge
from pathlib import Path

from test_api_response_shape import api, cat_clock, create_human_garden


def test_normalize_adds_cottage_and_keeps_only_legal_item_record_fields():
    state = ge.get_default_state()
    state.pop("cottage")
    normalized = ge.normalize_state(state)
    assert normalized["cottage"] == {"items": {}}

    normalized["cottage"] = {
        "items": {"rug": {"acquired_at": "12", "source": "invalid", "price": 900}}
    }
    ge.normalize_state(normalized)
    assert normalized["cottage"]["items"] == {
        "rug": {"acquired_at": 12, "source": "system"}
    }


def test_cottage_purchase_uses_shared_money_once_and_records_source():
    state = ge.get_default_state()
    state["money"] = 5000
    purchasable = [item for item in ge.COTTAGE_ITEM_CATALOG.values() if "price" in item]
    assert len(purchasable) == 11
    assert sum(item["price"] for item in purchasable) == 21_500

    assert "添置了地毯" in ge.process_command(state, "buy_cottage_furniture rug", event_source="human")
    assert state["money"] == 4100
    assert state["cottage"]["items"]["rug"]["source"] == "human"
    assert "已经拥有" in ge.process_command(state, "buy_cottage_furniture rug", event_source="ai")
    assert state["money"] == 4100

    assert "添置了窗帘" in ge.process_command(state, "buy_cottage_furniture curtains", event_source="ai")
    assert state["cottage"]["items"]["curtains"]["source"] == "ai"
    assert "纪念奖励" in ge.process_command(state, "buy_cottage_furniture small_photo_frame", event_source="human")


def test_cottage_rewards_are_idempotent_and_preserve_existing_record():
    state = ge.get_default_state()
    state["encyclopedia"] = ["baby_breath", "lisianthus", "camellia", "moonflower"]
    assert ge.sync_cottage_rewards(state, now=100) == [
        "small_photo_frame", "small_wall_art", "small_vase"
    ]
    assert "eternal_flower" not in state["cottage"]["items"]
    assert ge.sync_cottage_rewards(state, now=200) == []
    assert state["cottage"]["items"]["small_photo_frame"] == {
        "acquired_at": 100,
        "source": "system",
    }

    state["encyclopedia"].append("red_spider_lily")
    assert ge.sync_cottage_rewards(state, now=300) == ["eternal_flower"]
    assert ge.sync_cottage_rewards(state, now=400) == []


def test_first_harvest_immediately_syncs_cottage_reward():
    now = 1_700_000_000
    state = ge.get_default_state()
    state["pots"][0] = {
        "flower_id": "baby_breath",
        "planted_time": now - 2000,
        "watered": True,
        "growth_progress": ge.FLOWERS["baby_breath"]["grow_time"],
        "last_growth_update": now,
    }
    ge._harvest_one_pot(state, 0, now, ge.WEATHER["cloudy"])
    assert state["cottage"]["items"]["small_photo_frame"] == {
        "acquired_at": now,
        "source": "system",
    }


def test_api_and_web_share_cottage_summary_and_old_save_sync(api, cat_clock):
    module, client = api
    session_id, web_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["money"] = 1000
    state["encyclopedia"] = ["baby_breath"]
    state.pop("cottage")
    module.db_save_state(session_id, state)

    web_payload = client.get(f"/web/status?session_id={session_id}", headers=web_headers).get_json()
    cottage = web_payload["state"]["cottage"]
    assert cottage["owned_items"][0]["id"] == "small_photo_frame"
    assert "cottage" not in web_payload["state"]["inventory"]
    assert all(item["id"] != "small_photo_frame" for item in cottage["purchasable_items"])

    bought = client.post(
        "/web/cmd", headers=web_headers,
        json={"session_id": session_id, "command": "buy_cottage_furniture rug"},
    ).get_json()
    assert bought["state"]["cottage"]["owned_items"][-1]["source"] == "human"

    ai_payload = client.post(
        "/api/cmd", headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "status"},
    ).get_json()
    assert {item["id"] for item in ai_payload["state"]["cottage"]["owned_items"]} == {
        "small_photo_frame", "rug"
    }
    assert ai_payload["state"]["cottage"]["cat_area"]["bed"]["facility_id"] == "basic_cat_bed"


def test_cottage_frontend_is_a_functional_entry_with_no_asset_image_dependency():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert 'data-main-pane="cottage"' in html
    assert 'id="cottageContent"' in html
    assert "function renderCottage()" in js
    assert "COTTAGE_CATEGORY_FALLBACK" in js
    assert "buy_cottage_furniture ${item.id}" in js

