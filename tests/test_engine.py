import time
from datetime import datetime
from unittest.mock import patch

from game_engine import (
    BOUQUETS,
    DISPLAY_TIMEZONE,
    FLOWER_UNLOCK_REQUIREMENTS,
    FLOWERS,
    VASE_LIFESPAN_SECONDS,
    WEATHER,
    get_default_state,
    get_bouquet_options,
    get_bouquet_inventory_public,
    get_flower_shop_public_summary,
    get_vase_flower_status,
    is_bouquet_discovered,
    is_flower_shop_eligible,
    is_flower_unlocked,
    normalize_state,
    process_command,
)


def fresh_state():
    state = get_default_state()
    state["inventory"]["items"]["basic_food"] = 3
    return state


def test_negative_or_zero_quantities_are_rejected():
    state = fresh_state()
    money = state["money"]
    assert "数量必须是正整数" in process_command(state, "buy daisy -1")
    assert "数量必须是正整数" in process_command(state, "buy daisy 0")
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


def test_make_bouquet_is_atomic_and_records_each_gift():
    state = fresh_state()
    state.pop("bouquet_gifts")
    normalize_state(state)
    assert state["bouquet_gifts"] == []

    state["encyclopedia"] = ["tulip", "baby_breath"]
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    listing = process_command(state, "make_bouquet")
    assert "first_meeting" in listing
    assert "可以制作" in listing
    assert "first_meeting" in listing and "可以制作" in listing

    before = dict(state["inventory"]["flowers"])
    failed = process_command(state, "make_bouquet bouquet_id=morning_light")
    assert "还没有发现" in failed
    assert state["inventory"]["flowers"] == before
    assert state["bouquet_gifts"] == []

    result = process_command(
        state,
        "make_bouquet bouquet_id=first_meeting message=给你的春天",
    )
    assert "初见" in result
    assert state["inventory"]["flowers"] == {}
    assert len(state["bouquet_gifts"]) == 1
    assert state["bouquet_gifts"][0] == {
        "bouquet_id": "first_meeting",
        "components": dict(BOUQUETS["first_meeting"]["components"]),
        "sent_at": state["bouquet_gifts"][0]["sent_at"],
        "message": "给你的春天",
    }

    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    process_command(state, "make_bouquet bouquet_id=first_meeting")
    assert len(state["bouquet_gifts"]) == 2
    assert all(gift["bouquet_id"] == "first_meeting" for gift in state["bouquet_gifts"])


def test_craft_bouquet_creates_instance_and_gift_consumes_only_that_instance():
    state = fresh_state()
    state["encyclopedia"] = ["tulip", "baby_breath"]
    state["inventory"]["flowers"] = {"tulip": 4, "baby_breath": 2}

    assert "已制作初见" in process_command(state, "craft_bouquet bouquet_id=first_meeting")
    assert len(state["bouquet_inventory"]) == 1
    instance = state["bouquet_inventory"][0]
    assert instance["components"] == {"tulip": 2, "baby_breath": 1}
    assert state["bouquet_gifts"] == []
    assert state["inventory"]["flowers"] == {"tulip": 2, "baby_breath": 1}

    assert "送给人类" in process_command(state, f"gift_bouquet instance_id={instance['instance_id']}")
    assert state["bouquet_inventory"] == []
    assert len(state["bouquet_gifts"]) == 1
    assert state["bouquet_gifts"][0]["components"] == instance["components"]
    assert get_bouquet_inventory_public(state) == []


def test_bouquet_inventory_normalization_and_legacy_gifts_keep_component_snapshots():
    state = fresh_state()
    state["bouquet_gifts"] = [{"bouquet_id": "legacy", "components": {"removed_flower": 2}, "sent_at": 1, "message": None}]
    state["bouquet_inventory"] = [
        {"instance_id": "one", "bouquet_id": "first_meeting", "components": {"tulip": "2"}},
        {"instance_id": "one", "bouquet_id": "first_meeting", "components": {"tulip": 2}},
        {"instance_id": "bad", "bouquet_id": "first_meeting", "components": {}},
    ]
    normalize_state(state)
    assert state["bouquet_gifts"][0]["components"] == {"removed_flower": 2}
    assert state["bouquet_inventory"] == [
        {"instance_id": "one", "bouquet_id": "first_meeting", "components": {"tulip": 2}}
    ]


def test_direct_flower_sale_earned_migrates_once_and_only_grows_on_sell():
    state = fresh_state()
    state["total_earned"] = 123
    state.pop("direct_flower_sale_earned")
    normalize_state(state)
    assert state["direct_flower_sale_earned"] == 123
    state["inventory"]["flowers"] = {"daisy": 2}
    process_command(state, "sell daisy 2")
    assert state["direct_flower_sale_earned"] == 131
    process_command(state, "buy daisy 1")
    assert state["direct_flower_sale_earned"] == 131


def test_flower_shop_requires_monotonic_facts_and_establishes_once():
    state = fresh_state()
    state["money"] = 4000
    assert not is_flower_shop_eligible(state)
    assert "还不满足" in process_command(state, "establish_flower_shop")
    state["encyclopedia"] = list(FLOWERS)[:10]
    state["flower_harvest_counts"] = {"daisy": 42}
    state["direct_flower_sale_earned"] = 3000
    assert is_flower_shop_eligible(state)
    assert "建好了" in process_command(state, "establish_flower_shop")
    assert state["money"] == 500
    assert state["flower_shop"]["slots"] == [None, None, None]
    assert "不会重复扣款" in process_command(state, "establish_flower_shop")
    assert state["money"] == 500


def test_flower_shop_fixed_hours_cross_midnight_and_pending_change():
    state = fresh_state()
    state["money"] = 4000
    state["encyclopedia"] = list(FLOWERS)[:10]
    state["flower_harvest_counts"] = {"daisy": 42}
    state["direct_flower_sale_earned"] = 3000
    process_command(state, "establish_flower_shop")
    assert "已设置" in process_command(state, "set_flower_shop_hours 22:00")
    assert "正式开业" in process_command(state, "launch_flower_shop")
    overnight = int(datetime(2026, 10, 9, 23, 30, tzinfo=DISPLAY_TIMEZONE).timestamp())
    summary = get_flower_shop_public_summary(state, overnight)
    assert summary["business_duration_minutes"] == 600
    assert summary["is_open"] is True
    assert summary["capacity"] == 3
    closed = int(datetime(2026, 10, 10, 12, 0, tzinfo=DISPLAY_TIMEZONE).timestamp())
    with patch("game_engine.time.time", return_value=closed):
        assert "下一次营业周期生效" in process_command(state, "set_flower_shop_hours 09:00")
    assert state["flower_shop"]["business_start_minute"] == 22 * 60
    assert state["flower_shop"]["pending_business_start_minute"] == 9 * 60


def test_bouquet_recipes_and_discovery_are_derived_from_encyclopedia():
    expected = {
        "first_meeting": {"tulip": 2, "baby_breath": 1},
        "morning_light": {"sunflower": 1, "carnation": 1, "daisy": 1},
        "sunny_field": {"pansy": 1, "daisy": 1, "baby_breath": 1},
        "heart_note": {"rose": 1, "carnation": 1, "tulip": 1},
        "evening_breeze": {"lisianthus": 1, "lavender": 2},
        "soft_cloud": {"hydrangea": 1, "lily": 1, "baby_breath": 1},
        "blue_letter": {"iris": 1, "lisianthus": 1, "rose": 1},
        "cherry_branch": {"cherry_blossom": 1, "lisianthus": 1, "baby_breath": 1},
        "spring_banquet": {"peony": 1, "rose": 1, "lily": 1},
        "spring_mountain": {"camellia": 1, "hydrangea": 1, "tulip": 1},
        "moonlit_book": {"moonflower": 1, "lily": 1, "lavender": 1},
        "higan_poem": {"red_spider_lily": 1, "peony": 1, "iris": 1},
    }
    assert {bouquet_id: bouquet["components"] for bouquet_id, bouquet in BOUQUETS.items()} == expected
    assert all(sum(components.values()) == 3 for components in expected.values())
    assert set().union(*[set(components) for components in expected.values()]) == set(FLOWERS)

    state = fresh_state()
    state["encyclopedia"] = ["tulip"]
    state["inventory"]["flowers"] = {"tulip": 2}
    assert not is_bouquet_discovered(state, "first_meeting")
    assert get_bouquet_options(state) == []
    before = dict(state["inventory"]["flowers"])
    assert "还没有发现" in process_command(state, "make_bouquet first_meeting")
    assert state["inventory"]["flowers"] == before

    state["encyclopedia"].append("baby_breath")
    options = get_bouquet_options(state)
    assert options == [{"bouquet_id": "first_meeting", "name": "初见", "components": {"tulip": 2, "baby_breath": 1}, "can_make": False, "missing": {"baby_breath": 1}}]
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1}
    assert get_bouquet_options(state)[0]["can_make"] is True


def test_bouquet_duplicate_component_shortage_and_deduction():
    state = fresh_state()
    state["encyclopedia"] = ["tulip", "baby_breath", "lisianthus", "lavender"]
    state["inventory"]["flowers"] = {"tulip": 1, "baby_breath": 1, "lisianthus": 1, "lavender": 1}
    options = {option["bouquet_id"]: option for option in get_bouquet_options(state)}
    assert options["first_meeting"]["missing"] == {"tulip": 1}
    assert options["evening_breeze"]["missing"] == {"lavender": 1}
    state["inventory"]["flowers"] = {"tulip": 2, "baby_breath": 1, "lisianthus": 1, "lavender": 2}
    assert "初见" in process_command(state, "make_bouquet first_meeting")
    assert state["inventory"]["flowers"] == {"lisianthus": 1, "lavender": 2}
    assert "晚风" in process_command(state, "make_bouquet evening_breeze")
    assert state["inventory"]["flowers"] == {}


def test_seventeen_flower_configuration_matches_the_first_development_batch():
    expected = {
        "daisy": ("雏菊", "common", 180, 3, 4),
        "tulip": ("郁金香", "common", 300, 4, 6),
        "pansy": ("三色堇", "common", 420, 5, 8),
        "sunflower": ("向日葵", "common", 600, 6, 10),
        "rose": ("玫瑰", "common", 900, 8, 14),
        "baby_breath": ("满天星", "common", 1200, 10, 18),
        "carnation": ("康乃馨", "common", 1500, 12, 22),
        "lavender": ("薰衣草", "uncommon", 2100, 16, 30),
        "hydrangea": ("绣球花", "uncommon", 2700, 20, 38),
        "lily": ("百合", "uncommon", 3600, 26, 50),
        "iris": ("鸢尾花", "uncommon", 5400, 28, 64),
        "lisianthus": ("洋桔梗", "uncommon", 7200, 36, 84),
        "cherry_blossom": ("樱花", "rare", 9000, 46, 106),
        "peony": ("牡丹", "rare", 10800, 58, 130),
        "camellia": ("山茶花", "rare", 12600, 72, 156),
        "moonflower": ("月光花", "legendary", 16200, 90, 198),
        "red_spider_lily": ("彼岸花", "legendary", 21600, 120, 264),
    }

    assert len(FLOWERS) == 17
    assert {
        flower_id: (
            flower["name"],
            flower["rarity"],
            flower["grow_time"],
            flower["seed_price"],
            flower["sell_price"],
        )
        for flower_id, flower in FLOWERS.items()
    } == expected
    assert {
        rarity: sum(flower["rarity"] == rarity for flower in FLOWERS.values())
        for rarity in ("common", "uncommon", "rare", "legendary")
    } == {"common": 7, "uncommon": 5, "rare": 3, "legendary": 2}


def test_unlock_tiers_share_the_dynamic_encyclopedia_and_harvest_facts():
    state = fresh_state()
    flower_ids = list(FLOWERS)
    tiers = [
        (0, 0, 5),
        (4, 8, 7),
        (7, 24, 10),
        (10, 42, 12),
        (12, 62, 14),
        (14, 85, 15),
        (15, 105, 16),
        (16, 125, 17),
    ]

    locked_result = process_command(state, "buy baby_breath 1")
    assert "满天星尚未解锁" in locked_result
    for encyclopedia_count, harvest_count, unlocked_count in tiers:
        state["encyclopedia"] = flower_ids[:encyclopedia_count]
        state["flower_harvest_counts"] = {"daisy": harvest_count}
        unlocked = [flower_id for flower_id in flower_ids if is_flower_unlocked(state, flower_id)]
        assert unlocked == flower_ids[:unlocked_count]

    state["encyclopedia"] = flower_ids[:4]
    state["flower_harvest_counts"] = {"daisy": 7}
    assert "满天星尚未解锁" in process_command(state, "buy baby_breath 1")
    state["flower_harvest_counts"] = {"daisy": 8}
    process_command(state, "buy baby_breath 1")
    assert state["inventory"]["seeds"]["baby_breath"] == 1

    state["encyclopedia"] = ["moonflower"]
    state["flower_harvest_counts"] = {}
    assert is_flower_unlocked(state, "moonflower")

    assert FLOWER_UNLOCK_REQUIREMENTS["red_spider_lily"] == {"encyclopedia": 16, "harvests": 125}


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
