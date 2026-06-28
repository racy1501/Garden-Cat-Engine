import time
from unittest.mock import patch

from game_engine import (
    FLOWERS,
    VASE_LIFESPAN_SECONDS,
    WEATHER,
    get_default_state,
    get_vase_flower_status,
    process_command,
)


def fresh_state():
    state = get_default_state()
    state["inventory"]["items"]["basic_food"] = 3
    return state


def test_negative_or_zero_quantities_are_rejected():
    state = fresh_state()
    money = state["money"]
    assert process_command(state, "buy daisy -1").startswith("❌")
    assert process_command(state, "buy daisy 0").startswith("❌")
    assert state["money"] == money


def test_unwatered_time_does_not_count_as_growth():
    state = fresh_state()
    state["inventory"]["seeds"]["daisy"] = 1
    process_command(state, "plant daisy 1")
    state["pots"][0]["last_growth_update"] -= 600
    process_command(state, "status")
    assert state["pots"][0]["growth_progress"] == 0


def test_withered_flower_stays_until_cleared():
    state = fresh_state()
    now = int(time.time())
    state["pots"][0] = {
        "flower_id": "daisy",
        "planted_time": now - 100,
        "watered": True,
        "growth_progress": 20.0,
        "last_growth_update": now,
        "pest_time": now - 1,
    }
    process_command(state, "status")
    assert state["pots"][0] is not None
    assert state["pots"][0]["withered"] is True

    with patch("game_engine.random.random", return_value=0.1):
        result = process_command(state, "clear 1")
    assert state["pots"][0] is None
    assert state["money"] == 51  # 雏菊种子3块，半价向下取整为1块
    assert "1块" in result


def test_vase_uses_twelve_real_hours_and_remove_returns_nothing():
    state = fresh_state()
    state["inventory"]["flowers"]["rose"] = 1
    before_money = state["money"]
    process_command(state, "arrange rose")
    assert state["inventory"]["flowers"].get("rose", 0) == 0
    assert len(state["vase"]) == 1

    state["vase"][0]["arranged_time"] = int(time.time()) - VASE_LIFESPAN_SECONDS - 1
    label, _, remaining = get_vase_flower_status(state["vase"][0], int(time.time()))
    assert "枯萎" in label
    assert remaining == 0

    process_command(state, "remove_vase 1")
    assert state["vase"] == []
    assert state["money"] == before_money
    assert state["inventory"]["flowers"].get("rose", 0) == 0


def test_unlock_tiers():
    state = fresh_state()
    assert process_command(state, "buy lavender 1").startswith("🔒")
    state["encyclopedia"] = ["daisy", "tulip"]
    assert process_command(state, "buy lavender 1").startswith("✅")
    assert process_command(state, "buy cherry 1").startswith("🔒")


def test_duplicate_permanent_reward_refunds_full_store_price():
    state = fresh_state()
    now = int(time.time())
    state["permanent_items"].append("water_bowl")
    state["pots"][0] = {
        "flower_id": "sunflower",
        "planted_time": now - 1000,
        "watered": True,
        "growth_progress": FLOWERS["sunflower"]["grow_time"],
        "last_growth_update": now,
    }
    before = state["money"]
    result = process_command(state, "harvest 1")
    assert state["money"] == before + 10
    assert "折算10块" in result


def test_cat_passive_stats_stop_at_twenty():
    state = fresh_state()
    state["cat"] = {"name": "栗子"}
    state["cat_stats"] = {"hunger": 80.0, "thirst": 80.0, "mood": 80.0, "affection": 80.0}
    state["last_update"] = int(time.time()) - 1000 * 3600
    state["weather"] = "rainy"
    process_command(state, "status")
    for value in state["cat_stats"].values():
        assert value >= 20


def test_mature_flower_does_not_get_new_pests():
    state = fresh_state()
    now = int(time.time())
    state["pots"][0] = {
        "flower_id": "daisy",
        "planted_time": now - 1000,
        "watered": True,
        "growth_progress": FLOWERS["daisy"]["grow_time"],
        "last_growth_update": now,
    }
    state["last_pest_check_time"] = now - 301
    with patch("game_engine.random.random", return_value=0.0):
        process_command(state, "status")
    assert "pest_time" not in state["pots"][0]


def test_cat_can_be_named_when_adopted_and_renamed():
    state = fresh_state()
    state["money"] = 200
    result = process_command(state, "adopt 栗子")
    assert "栗子" in result
    assert state["cat"]["name"] == "栗子"

    result = process_command(state, "rename_cat 橘子")
    assert "橘子" in result
    assert state["cat"]["name"] == "橘子"


def test_cat_name_defaults_and_length_limit():
    state = fresh_state()
    state["money"] = 200
    process_command(state, "adopt")
    assert state["cat"]["name"] == "小猫"

    result = process_command(state, "rename_cat 这是一个超过十二个字符的猫咪名字")
    assert result.startswith("❌")
    assert state["cat"]["name"] == "小猫"


def test_weather_growth_speed_rebalance():
    assert WEATHER["sunny"]["grow_speed"] == 1.1
    assert WEATHER["rainy"]["grow_speed"] == 1.2
    assert WEATHER["rainy"]["auto_water"] is True
    assert WEATHER["cloudy"]["grow_speed"] == 1.0


def test_pot_unlock_costs_increase_by_slot():
    state = fresh_state()
    state["money"] = 200

    result = process_command(state, "buy_pot")
    assert state["max_pots"] == 4
    assert state["money"] == 180
    assert "20块" in result

    result = process_command(state, "buy_pot")
    assert state["max_pots"] == 5
    assert state["money"] == 145
    assert "35块" in result

    result = process_command(state, "buy_pot")
    assert state["max_pots"] == 6
    assert state["money"] == 95
    assert "50块" in result


def test_pot_unlock_rejects_when_next_price_is_unaffordable():
    state = fresh_state()
    state["money"] = 19
    result = process_command(state, "buy_pot")
    assert result.startswith("❌")
    assert state["max_pots"] == 3


def test_harvest_all_collects_every_ready_flower():
    state = fresh_state()
    now = int(time.time())
    state["pots"] = [
        {
            "flower_id": "daisy",
            "planted_time": now - 1000,
            "watered": True,
            "growth_progress": FLOWERS["daisy"]["grow_time"],
            "last_growth_update": now,
        },
        {
            "flower_id": "tulip",
            "planted_time": now - 1000,
            "watered": True,
            "growth_progress": FLOWERS["tulip"]["grow_time"],
            "last_growth_update": now,
        },
        None,
    ]
    result = process_command(state, "harvest all")
    assert "共收获2朵花" in result
    assert state["pots"][0] is None
    assert state["pots"][1] is None
    assert state["inventory"]["flowers"]["daisy"] == 1
    assert state["inventory"]["flowers"]["tulip"] == 1


def test_harvest_all_skips_unready_and_pested_flowers():
    state = fresh_state()
    now = int(time.time())
    state["pots"] = [
        {
            "flower_id": "daisy",
            "planted_time": now,
            "watered": True,
            "growth_progress": 10,
            "last_growth_update": now,
        },
        {
            "flower_id": "tulip",
            "planted_time": now - 1000,
            "watered": True,
            "growth_progress": FLOWERS["tulip"]["grow_time"],
            "last_growth_update": now,
            "pest_time": now + 300,
        },
        None,
    ]
    result = process_command(state, "harvest all")
    assert result.startswith("❌")
    assert state["pots"][0] is not None
    assert state["pots"][1] is not None
