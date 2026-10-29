import copy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import game_engine as ge  # noqa: E402


def assert_invalid_quantity_is_a_business_error(command):
    state = ge.get_default_state()
    state["money"] = 50
    before_money = state["money"]
    before_inventory = copy.deepcopy(state["inventory"])

    result = ge.process_command(state, command)

    assert "数量必须是正整数" in result
    assert state["money"] == before_money
    assert state["inventory"] == before_inventory


def test_buy_rejects_invalid_seed_quantities_without_throwing():
    for quantity in ("0", "-1", "x"):
        assert_invalid_quantity_is_a_business_error(f"buy daisy {quantity}")


def test_buy_rejects_invalid_item_quantities_without_throwing():
    for quantity in ("0", "-1", "x"):
        assert_invalid_quantity_is_a_business_error(f"buy basic_food {quantity}")


def test_buy_accepts_internal_item_id_and_rejects_display_name():
    state = ge.get_default_state()
    state["money"] = 50

    success = ge.process_command(state, "buy basic_food 1")
    assert "买了1个普通猫粮" in success
    assert state["money"] == 40

    state = ge.get_default_state()
    state["money"] = 50
    rejected = ge.process_command(state, "buy 普通猫粮 1")
    assert "商店没有这个东西" in rejected


def test_basic_cat_food_package_contains_five_servings():
    assert ge.CAT_ITEM_PACKAGE_SIZES["basic_food"] == 5


def test_help_and_shop_expose_executable_item_id():
    help_text = ge.process_command(ge.get_default_state(), "help")
    shop_text = ge.process_command(ge.get_default_state(), "shop")

    assert "buy <商品ID>" in help_text
    assert "basic_food" in help_text
    assert "普通猫粮（basic_food）" in shop_text


def test_help_describes_current_cat_decay_without_weather_mood_effects():
    text = ge.process_command(ge.get_default_state(), "help")
    weather_section = text.split("🌤️ 天气系统", 1)[1].split("💧 浇水系统", 1)[0]
    cat_section = text.split("🐱 猫咪系统", 1)[1].split("🌸 花卉解锁", 1)[0]
    assert "天气不直接改变猫咪心情数值" in weather_section
    assert "猫心情净" not in weather_section
    assert "visitor / stayed_waiting_name 不发生被动衰减" in cat_section
    assert f"adopted 每小时被动衰减{ge.AFFECTION_NATURAL_DECAY:g}，最低到30" in cat_section
    assert "已低于30的旧状态不会自动抬高" in cat_section
    assert f"基础衰减-{ge.MOOD_BASE_DECAY:g}/小时" in cat_section
    assert f"最多结算前{ge.MOOD_OFFLINE_CAP_REAL_HOURS:g}小时" in cat_section
    assert "自然衰减-0.5" not in cat_section
    assert "额外-2.0" not in cat_section
    assert "各项最低停在20" not in cat_section


def test_help_flower_unlocks_follow_official_configuration(monkeypatch):
    text = ge.process_command(ge.get_default_state(), "help")
    section = text.split("🌸 花卉解锁：", 1)[1].split("🎉 特殊事件", 1)[0]
    for flower_id, flower in ge.FLOWERS.items():
        assert f"- {flower['name']}：{ge.get_unlock_message(flower_id)}" in section
    monkeypatch.setitem(ge.FLOWER_UNLOCK_REQUIREMENTS, "red_spider_lily",
                        {"encyclopedia": 99, "harvests": 999})
    updated = ge.process_command(ge.get_default_state(), "help")
    assert "彼岸花：图鉴收录99种，累计收获999朵后解锁" in updated
