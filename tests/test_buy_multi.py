"""多商品单次购买：一次校验、一次扣款、逐项入库、只记一条购买记录。"""
import copy
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import game_engine as ge  # noqa: E402
from test_api_response_shape import api, cat_clock, create_human_garden  # noqa: E402


def _state(money=200):
    state = ge.get_default_state()
    state["money"] = money
    state["events"] = []
    # 把猫咪来访推到未来，避免每次命令前的例行生命周期结算写入事件，
    # 这样"状态完全不变"只反映购买行为本身。
    state["cat_state"]["next_visit_at"] = int(ge.time.time()) + 3600
    return state


def _purchase_snapshot(state):
    """购买会触及的全部事实，用于断言整笔失败后状态完全不变。"""
    return {
        "money": state["money"],
        "inventory": copy.deepcopy(state["inventory"]),
        "permanent_items": list(state["permanent_items"]),
        "cat_care": copy.deepcopy(state["cat_care"]),
        "events": copy.deepcopy(state["events"]),
    }


def _purchase_events(state):
    return [event for event in state["events"] if event["text"].startswith("购买")]


def test_buy_multi_buys_two_different_items_in_one_call():
    state = _state()
    result = ge.process_command(state, "buy_multi daisy=2 basic_food=3")

    assert "✅ 购买完成" in result
    assert "共花费36块" in result
    assert state["money"] == 200 - 2 * ge.FLOWERS["daisy"]["seed_price"] - 3 * ge.ITEMS["basic_food"]["price"]
    assert state["inventory"]["seeds"]["daisy"] == 2
    assert state["inventory"]["items"]["basic_food"] == 3 * ge.CAT_ITEM_PACKAGE_SIZES["basic_food"]


def test_buy_multi_mixes_seeds_and_cat_supplies():
    state = _state()
    result = ge.process_command(state, "buy_multi daisy=2 cat_treat=1")

    assert "✅ 购买完成" in result
    assert state["inventory"]["seeds"]["daisy"] == 2
    assert state["inventory"]["items"]["cat_treat"] == ge.CAT_ITEM_PACKAGE_SIZES["cat_treat"]
    assert state["money"] == 200 - 2 * ge.FLOWERS["daisy"]["seed_price"] - ge.ITEMS["cat_treat"]["price"]


def test_buy_multi_reports_each_item_quantity_and_total_cost():
    state = _state()
    result = ge.process_command(state, "buy_multi daisy=2 basic_food=3")

    assert f"{ge.FLOWERS['daisy']['name']}种子×2" in result
    assert f"{ge.ITEMS['basic_food']['name']}×3" in result
    assert "共花费36块" in result


def test_buy_multi_writes_exactly_one_purchase_event():
    state = _state()
    ge.process_command(state, "buy_multi daisy=2 basic_food=3")

    events = _purchase_events(state)
    assert len(events) == 1
    assert events[0]["text"] == (
        f"购买了{ge.FLOWERS['daisy']['name']}种子×2颗、"
        f"{ge.ITEMS['basic_food']['name']}×3包（共15份），共花费36块"
    )


def test_buy_multi_fails_entirely_when_balance_is_insufficient():
    state = _state(money=10)
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=2 basic_food=3")

    assert "❌ 购买失败" in result
    assert "钱不够" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_fails_entirely_when_one_item_does_not_exist():
    state = _state()
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=2 missing_item=1")

    assert "❌ 购买失败（missing_item）" in result
    assert "商店没有这个东西" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_fails_entirely_when_one_flower_is_locked():
    state = _state()
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=1 red_spider_lily=1")

    assert "❌ 购买失败（red_spider_lily）" in result
    assert "尚未解锁" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_fails_entirely_when_permanent_item_quantity_is_above_one():
    state = _state()
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=1 cat_bed=2")

    assert "❌ 购买失败（cat_bed）" in result
    assert "永久物品每次只能购买1个" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_fails_entirely_when_permanent_item_is_already_owned():
    state = _state()
    assert "✅" in ge.process_command(state, "buy cat_bed 1")
    state["events"] = []
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=1 cat_bed=1")

    assert "❌ 购买失败（cat_bed）" in result
    assert "已经有高级猫窝了" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_rejects_duplicate_item_ids():
    state = _state()
    before = _purchase_snapshot(state)

    result = ge.process_command(state, "buy_multi daisy=1 daisy=2")

    assert "❌ 购买失败（daisy）" in result
    assert "不能重复" in result
    assert _purchase_snapshot(state) == before


def test_buy_multi_rejects_invalid_quantity_and_malformed_arguments():
    state = _state()
    before = _purchase_snapshot(state)

    assert "数量必须是正整数" in ge.process_command(state, "buy_multi daisy=0")
    assert "数量必须是正整数" in ge.process_command(state, "buy_multi daisy=x")
    assert "商品ID=数量" in ge.process_command(state, "buy_multi daisy")
    assert "❌ 用法：buy_multi" in ge.process_command(state, "buy_multi")
    assert _purchase_snapshot(state) == before


def test_buy_multi_applies_permanent_facility_purchase_once():
    state = _state()

    result = ge.process_command(state, "buy_multi cat_bed=1 daisy=1")

    assert "✅ 购买完成" in result
    assert state["permanent_items"] == ["cat_bed"]
    assert state["cat_care"]["bed"]["facility_id"] == ge.PREMIUM_CAT_BED_ID
    assert state["inventory"]["seeds"]["daisy"] == 1
    assert len(_purchase_events(state)) == 1


def test_single_buy_keeps_its_original_messages_and_event():
    state = _state()

    seed_result = ge.process_command(state, "buy daisy 2")
    assert "✅ 买了2颗雏菊种子！(-6块)" in seed_result
    assert state["events"][-1]["text"] == "买了2颗雏菊种子"
    assert state["events"][-1]["area"] == "garden"

    item_result = ge.process_command(state, "buy basic_food 1")
    assert "✅ 买了1包普通猫粮，共5份，花费10块。" in item_result
    assert state["events"][-1]["text"] == "买了1包普通猫粮，共5份"
    assert state["events"][-1]["area"] == "cottage"


def test_buy_multi_runs_through_the_api_command_route(api, cat_clock):
    module, client = api
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["money"] = 200
    module.db_save_state(session_id, state)
    before = module.db_load_state(session_id)

    response = client.post(
        "/api/cmd",
        headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "buy_multi daisy=2 basic_food=3"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert "✅ 购买完成" in payload["message"]
    assert "共花费36块" in payload["message"]

    saved = module.db_load_state(session_id)
    assert saved["inventory"]["seeds"]["daisy"] == before["inventory"]["seeds"]["daisy"] + 2
    assert saved["inventory"]["items"]["basic_food"] == (
        before["inventory"]["items"]["basic_food"] + 3 * ge.CAT_ITEM_PACKAGE_SIZES["basic_food"]
    )
    assert saved["money"] == 200 - 2 * ge.FLOWERS["daisy"]["seed_price"] - 3 * ge.ITEMS["basic_food"]["price"]
    purchases = [e for e in saved["events"] if e["text"].startswith("购买")]
    assert len(purchases) == 1


def test_buy_multi_failure_through_the_api_command_route_leaves_state_unchanged(api, cat_clock):
    module, client = api
    session_id, _ = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["money"] = 200
    module.db_save_state(session_id, state)
    before = module.db_load_state(session_id)

    response = client.post(
        "/api/cmd",
        headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "buy_multi daisy=2 missing_item=1"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is False
    assert "❌ 购买失败（missing_item）" in payload["message"]

    saved = module.db_load_state(session_id)
    assert saved["inventory"]["seeds"]["daisy"] == before["inventory"]["seeds"]["daisy"]
    assert saved["inventory"]["items"]["basic_food"] == before["inventory"]["items"]["basic_food"]
    assert saved["money"] == before["money"]
    assert not [e for e in saved["events"] if e["text"].startswith("购买")]


def test_single_buy_keeps_its_original_failure_messages():
    state = _state(money=0)

    assert "❌ 商店没有这个东西" in ge.process_command(state, "buy missing_item")
    assert "❌ 钱不够！需要6块" in ge.process_command(state, "buy daisy 2")
    assert "❌ 数量必须是正整数" in ge.process_command(state, "buy daisy 0")
    assert "❌ 用法：buy <物品> [数量]" in ge.process_command(state, "buy daisy 1 2")
    assert "🔒 彼岸花尚未解锁" in ge.process_command(state, "buy red_spider_lily 1")
    assert "❌ 永久物品每次只能购买1个" in ge.process_command(state, "buy cat_bed 2")
