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


def test_help_and_shop_expose_executable_item_id():
    help_text = ge.process_command(ge.get_default_state(), "help")
    shop_text = ge.process_command(ge.get_default_state(), "shop")

    assert "buy <商品ID>" in help_text
    assert "basic_food" in help_text
    assert "普通猫粮（basic_food）" in shop_text
