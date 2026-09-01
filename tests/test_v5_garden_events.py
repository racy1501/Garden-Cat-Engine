import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import game_engine as ge  # noqa: E402


NOW = 1_700_000_000


def make_state(now=NOW):
    state = ge.normalize_state(ge.get_default_state(), now=now)
    state["weather_change_time"] = now + 10_000
    state["next_butterfly_at"] = now + 10_000
    state["last_active_at"] = now
    return state


def test_offline_butterfly_gold_reward_adds_money(monkeypatch):
    state = make_state()
    state["next_butterfly_at"] = NOW + 1800
    monkeypatch.setattr(ge.random, "randint", lambda start, end: 4)
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)

    ge.apply_offline_progress(state, NOW + 1800)

    assert state["money"] == 54
    assert state["last_butterfly_reward"] == {"type": "money", "amount": 4}


def test_offline_rainbow_money_reward_adds_money(monkeypatch):
    state = make_state()
    state["weather"] = "rainy"
    state["weather_change_time"] = NOW + 1800

    def fake_choice(options):
        if options == list(ge.WEATHER.keys()):
            return "sunny"
        if isinstance(options, list) and options and isinstance(options[0], dict):
            return options[0]
        return options[0]

    monkeypatch.setattr(ge.random, "choice", fake_choice)
    monkeypatch.setattr(
        ge.random,
        "randint",
        lambda start, end: 9 if (start, end) == (8, 12) else 3600,
    )
    monkeypatch.setattr(ge.random, "random", lambda: 0.0)

    ge.apply_offline_progress(state, NOW + 1800)

    assert state["money"] == 59
    assert state["last_rainbow_reward"] == {"type": "money", "amount": 9}


def test_offline_progress_stays_capped_at_seventy_two_hours():
    state = make_state()
    now = NOW + ge.OFFLINE_PROGRESS_MAX_SECONDS + 3600

    ge.apply_offline_progress(state, now)

    assert state["offline_summary"]["settled_seconds"] == ge.OFFLINE_PROGRESS_MAX_SECONDS
    assert state["offline_summary"]["skipped_seconds"] == 3600
    assert state["is_frozen"] is True


def test_final_source_defines_each_garden_event_entry_once():
    source = (PROJECT_ROOT / "game_engine.py").read_text(encoding="utf-8")
    names = [node.name for node in ast.walk(ast.parse(source)) if isinstance(node, ast.FunctionDef)]

    for name in ("get_weather_info", "_advance_offline_weather", "apply_offline_progress"):
        assert names.count(name) == 1
