"""72小时保护后只恢复剩余等待，不重演被跳过的猫咪活动。"""
import copy
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import game_engine as ge

START = 1_790_985_600
CAP = START + 72 * 3600
PLANS = ("next_visit_at", "current_visit_leave_at", "stay_deadline_at",
         "next_outing_at", "outing_return_at")


@pytest.fixture
def environment(tmp_path, monkeypatch):
    clock = [START]
    monkeypatch.setattr(ge.time, "time", lambda: clock[0])
    monkeypatch.setattr(ge.random, "randint", lambda low, high: (low + high) // 2)
    monkeypatch.setattr(ge.random, "random", lambda: 1.0)
    monkeypatch.setattr(ge.random, "choice", lambda options: options[0])
    monkeypatch.setattr(ge, "SAVE_FILE", str(tmp_path / "garden.json"))
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "garden.db"))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GARDEN_API_KEY", "test-key")
    # 避免其他测试留下指向不同数据库的已导入模块。
    monkeypatch.delitem(sys.modules, "game_api", raising=False)
    api = importlib.import_module("game_api")
    assert not api.USE_POSTGRES and Path(api.SQLITE_PATH).parent == tmp_path
    api.ensure_schema()
    return clock, api


def make_cat(kind):
    state = ge.get_default_state()
    if kind in ("home", "away", "waiting"):
        state["cat"] = {"name": "栗子"}
        state["cat_stats"] = ge._default_v5_cat_stats()
        state["cat_state"].update(phase=ge.CAT_PHASE_WAITING_NAME, location="garden")
        if kind != "waiting":
            ge.process_command(state, "adopt 栗子")
        if kind == "away":
            # 初始计划仅剩20分钟；第72小时终点正在外出。
            state["cat_state"]["next_outing_at"] = START + 1200
    else:
        state["cat_state"].update(
            next_visit_at=START + (71 * 3600 + 3000 if kind == "visitor_garden" else 73 * 3600),
            first_visit_at=0, stay_deadline_at=0,
        )
    state["inventory"]["seeds"].update(daisy=1, tulip=1, rose=1)
    for flower, pot in (("daisy", 1), ("tulip", 2), ("rose", 3)):
        ge.process_command(state, f"plant {flower} {pot}")
    ge.process_command(state, "water 1")
    ge.process_command(state, "water 2")
    state["pots"][1]["pest_trigger_progress"] = ge.FLOWERS["tulip"]["grow_time"] * .6
    state["cat_care"]["food_bowl"]["remaining_portions"] = 3
    state["cat_care"]["water_bowl"]["remaining_portions"] = 3
    return state


def cat_effects(state):
    return copy.deepcopy({key: state[key] for key in
                          ("cat_state", "cat_stats", "cat_care", "events",
                           "collectibles", "letters_received")})


@pytest.mark.parametrize("hours", [71, 72, 73, 80])
@pytest.mark.parametrize("kind", ["home", "away", "visitor_garden", "visitor_away", "waiting"])
@pytest.mark.parametrize("storage", ["json", "sqlite"])
def test_cap_preserves_state_remaining_plans_and_reload(environment, hours, kind, storage):
    clock, api = environment
    state = make_cat(kind)
    reference = copy.deepcopy(state)
    endpoint = START + min(hours, 72) * 3600
    clock[0] = endpoint
    ge.apply_offline_progress(reference)
    clock[0] = START
    if storage == "json":
        ge.save_game(state)
        def load():
            return ge.load_game()
        def save(s):
            ge.save_game(s)
    else:
        api.db_save_state("audit", state)
        def load():
            return api.db_load_state("audit")
        def save(s):
            api.db_save_state("audit", s)
    clock[0] = START + hours * 3600
    state = load()
    skipped = max(0, hours - 72) * 3600
    expected_cat = copy.deepcopy(reference["cat_state"])
    for field in PLANS:
        if expected_cat[field] > endpoint:
            expected_cat[field] += skipped
    expected_cat["last_lifecycle_settled_at"] = clock[0]
    assert state["cat_state"] == expected_cat
    assert state["cat_stats"] == reference["cat_stats"]
    assert [event for event in state["events"] if not event["text"].startswith("盆")] == [
        event for event in reference["events"] if not event["text"].startswith("盆")
    ]  # 猫咪历史时间不移动；普通虫害日志仍保持原有行为。
    assert state["offline_summary"]["skipped_seconds"] == skipped
    for pot, old in zip(state["pots"], reference["pots"]):
        assert pot["growth_progress"] == old["growth_progress"]
        assert pot["pest_active"] == old["pest_active"]
        assert pot["last_growth_update"] == clock[0]
    baseline = cat_effects(state)
    timeline = (state["weather"], state["weather_change_time"], state["next_butterfly_at"])
    # 先保存冻结结果，再重载；重载也不得重复平移计划。
    save(state)
    state = load()
    assert cat_effects(state) == baseline
    for command in ("status", "status", "buy daisy 1", "status"):
        ge.process_command(state, command)
        assert cat_effects(state) == baseline
        assert (state["weather"], state["weather_change_time"], state["next_butterfly_at"]) == timeline
    save(state)
    state = load()
    assert cat_effects(state) == baseline
    cs = state["cat_state"]
    field = ("next_outing_at" if cs["location"] == "home" else "outing_return_at") if cs["phase"] == "adopted" else (
        "current_visit_leave_at" if cs["location"] == "garden" else "next_visit_at") if cs["phase"] == "visitor" else None
    if field:
        due = cs[field]
        clock[0] = due - 1
        ge.apply_offline_progress(state)
        assert state["events"] == baseline["events"]
        assert state["cat_state"]["location"] == baseline["cat_state"]["location"]
        clock[0] = due
        ge.apply_offline_progress(state)
        assert state["cat_state"]["location"] != baseline["cat_state"]["location"]
        assert state["cat_state"]["location_changed_at"] == due
    else:
        clock[0] += 120
        ge.apply_offline_progress(state)
        assert state["cat_state"]["phase"] == "stayed_waiting_name"
        assert state["events"] == baseline["events"]


@pytest.mark.parametrize("route", ["api", "web"])
def test_eighty_hour_status_routes_do_not_replay(environment, route):
    clock, api = environment
    client = api.app.test_client()
    reg = client.post("/web/register", json={"name": "audit"}).get_json()
    sid = reg["session_id"]
    state = make_cat("home")
    state["_web_token_hash"] = api._hash_web_token(reg["garden_token"])
    api.db_save_state(sid, state)
    clock[0] = START + 80 * 3600
    headers = {"X-API-Key": "test-key"} if route == "api" else {"X-Garden-Token": reg["garden_token"]}
    for _ in range(3):
        response = client.get(f"/{route}/status?session_id={sid}", headers=headers)
        assert response.status_code == 200
        assert "栗子出门" not in response.get_json()["message"]
        assert "栗子回家" not in response.get_json()["message"]
        loaded = api.db_load_state(sid)
        assert loaded["cat_state"]["location"] == "home"
        assert loaded["cat_state"]["next_outing_at"] == START + 81 * 3600
        assert all(event["time"] <= CAP for event in loaded["events"])


def test_no_new_random_plan_when_skipping_time(environment, monkeypatch):
    clock, api = environment
    state = make_cat("home")
    clock[0] = CAP
    ge.apply_offline_progress(state)
    # 仅模拟额外8小时被跳过；已有计划、天气和蝴蝶都尚未到期。
    state["last_active_at"] = START
    state["weather_change_time"] = START + 90 * 3600
    state["next_butterfly_at"] = START + 90 * 3600
    clock[0] = START + 80 * 3600
    baseline = cat_effects(state)
    # 改变后续随机结果；现有计划仍须保持剩余1小时，不能重排。
    monkeypatch.setattr(ge.random, "randint", lambda low, high: low)
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)
    ge.apply_offline_progress(state)
    assert state["cat_state"]["next_outing_at"] == START + 81 * 3600
    assert state["cat_care"] == baseline["cat_care"]
    assert state["collectibles"] == baseline["collectibles"]
    assert state["events"] == baseline["events"]


def test_flower_growth_after_resume_counts_only_new_time(environment):
    clock, api = environment
    state = make_cat("home")
    clock[0] = START + 80 * 3600
    ge.apply_offline_progress(state)
    ge.process_command(state, "water 3")
    assert state["pots"][2]["growth_progress"] == 0
    clock[0] += 10
    ge.apply_offline_progress(state)
    assert state["pots"][2]["growth_progress"] == pytest.approx(11)
    assert state["cat_state"]["next_outing_at"] == START + 81 * 3600
