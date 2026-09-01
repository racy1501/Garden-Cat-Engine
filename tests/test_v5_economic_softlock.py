import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import game_engine as ge  # noqa: E402


NOW = 1_700_000_000


def make_state():
    state = ge.normalize_state(ge.get_default_state(), now=NOW)
    state["money"] = 1
    state["inventory"]["seeds"] = {}
    state["inventory"]["flowers"] = {}
    state["pots"] = [None] * state["max_pots"]
    state["weather_change_time"] = NOW + 10_000
    state["next_butterfly_at"] = NOW + 10_000
    return state


def run_status(state, monkeypatch):
    monkeypatch.setattr(ge.time, "time", lambda: NOW)
    return ge.process_command(state, "status")


def make_pot(*, progress=20.0, pest_active=False):
    return {
        "flower_id": "daisy",
        "watered": True,
        "withered": False,
        "growth_progress": progress,
        "last_growth_update": NOW,
        "pest_trigger_progress": progress if pest_active else None,
        "pest_triggered": pest_active,
        "pest_active": pest_active,
        "pest_resolved": False,
    }


def test_empty_garden_with_insufficient_money_gets_one_daisy_seed(monkeypatch):
    state = make_state()

    run_status(state, monkeypatch)

    assert state["inventory"]["seeds"] == {"daisy": 1}


def test_existing_seed_or_flower_does_not_trigger_safety_net(monkeypatch):
    for inventory_key in ("seeds", "flowers"):
        state = make_state()
        state["inventory"][inventory_key] = {"tulip": 1}

        run_status(state, monkeypatch)

        assert state["inventory"]["seeds"] == ({"tulip": 1} if inventory_key == "seeds" else {})


def test_normal_or_mature_flower_keeps_recovery_path(monkeypatch):
    for progress in (20.0, float(ge.FLOWERS["daisy"]["grow_time"])):
        state = make_state()
        state["pots"][0] = make_pot(progress=progress)

        run_status(state, monkeypatch)

        assert state["inventory"]["seeds"] == {}


def test_pest_flower_only_blocks_safety_net_when_treatment_is_affordable(monkeypatch):
    state = make_state()
    state["money"] = ge.PEST_TREATMENT_COST
    state["pots"][0] = make_pot(pest_active=True)

    run_status(state, monkeypatch)

    assert state["inventory"]["seeds"] == {}

    state = make_state()
    state["pots"][0] = make_pot(pest_active=True)

    run_status(state, monkeypatch)

    assert state["inventory"]["seeds"] == {"daisy": 1}


def test_repeated_status_does_not_grant_the_safety_net_seed_twice(monkeypatch):
    state = make_state()

    run_status(state, monkeypatch)
    run_status(state, monkeypatch)

    assert state["inventory"]["seeds"] == {"daisy": 1}


def test_offline_safety_net_then_command_still_has_only_one_daisy_seed(monkeypatch):
    state = make_state()
    state["last_active_at"] = NOW - 60

    ge.apply_offline_progress(state, NOW)
    run_status(state, monkeypatch)

    assert state["inventory"]["seeds"] == {"daisy": 1}
