import time
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from game_engine import (
    FLOWERS,
    MOOD_OFFLINE_CAP_REAL_HOURS,
    WEATHER,
    _harvest_one_pot,
    get_default_state,
    normalize_state,
    update_cat_stats,
)


def make_cat_state(now: int):
    state = get_default_state()
    state["cat"] = {"name": "半夏"}
    state["cat_stats"] = {
        "hunger": 100.0,
        "thirst": 100.0,
        "mood": 50.0,
        "affection": 100.0,
    }
    state["last_update"] = now - 10 * 3600
    return state


def test_offline_mood_is_capped_at_two_hours_but_other_stats_keep_full_elapsed_time():
    now = int(time.time())
    state = make_cat_state(now)

    update_cat_stats(state, now, WEATHER["sunny"])

    assert MOOD_OFFLINE_CAP_REAL_HOURS == 2.0
    # 晴天净 +1/小时，离线10小时也只结算前2小时。
    assert state["cat_stats"]["mood"] == pytest.approx(52.0)
    # 饱食、口渴仍按完整10小时结算。
    assert state["cat_stats"]["hunger"] == pytest.approx(50.0)
    assert state["cat_stats"]["thirst"] == pytest.approx(40.0)
    assert state["last_update"] == now


def test_old_save_harvest_counts_start_from_current_flower_inventory():
    old_state = get_default_state()
    old_state.pop("flower_harvest_counts")
    old_state["inventory"]["flowers"] = {"daisy": 2, "lily": 1}

    normalized = normalize_state(old_state)

    assert normalized["flower_harvest_counts"] == {"daisy": 2, "lily": 1}


def test_each_successful_harvest_increments_flower_count():
    now = int(time.time())
    state = get_default_state()
    state["encyclopedia"] = ["daisy"]
    state["flower_harvest_counts"] = {"daisy": 4}
    state["pots"][0] = {
        "flower_id": "daisy",
        "planted_time": now - 1000,
        "watered": True,
        "withered": False,
        "growth_progress": FLOWERS["daisy"]["grow_time"],
        "last_growth_update": now,
    }

    result = _harvest_one_pot(state, 0, now, WEATHER["cloudy"])

    assert result.startswith("🌸 收获了雏菊")
    assert state["inventory"]["flowers"]["daisy"] == 1
    assert state["flower_harvest_counts"]["daisy"] == 5


def test_web_files_contain_all_requested_v499_controls():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="backpackBtn"' in html
    assert 'id="catBackpackBtn"' in html
    assert 'data-role="pet-button"' in js
    assert 'makeBackpackActionButton("一键售出", "sell all"' in js
    assert 'makeBackpackActionButton("卖全部"' in js
    assert '累计收获 ${Number(harvestCounts[id] || 0)}朵' in js
    assert 'const rarityRank = { common: 0, uncommon: 1, rare: 2, legendary: 3 }' in js
    assert '.shop-square-card {' in css and 'height: 236px;' in css
