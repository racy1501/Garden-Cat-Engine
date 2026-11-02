from copy import deepcopy

import game_engine as ge
import pytest

from test_api_response_shape import api, cat_clock, create_human_garden


def test_premium_water_bowl_catalog_capacity_and_thirst(api, cat_clock):
    module, client = api
    catalog = client.get("/api/catalog").get_json()
    assert catalog["items"]["water_bowl"]["effect"] == {}

    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    ge.apply_move_with_cat_reset(state, "栗子", now=cat_clock[0])
    state["money"] = 50
    state["cat_stats"]["thirst"] = 80
    state["cat_state"]["stats"] = dict(state["cat_stats"])
    state["cat_care"]["water_bowl"]["remaining_portions"] = 0
    module.db_save_state(session_id, state)
    basic = deepcopy(state)
    assert basic["cat_care"]["water_bowl"]["capacity"] == 3

    bought = client.post("/web/cmd", headers=human_headers,
                         json={"session_id": session_id, "command": "buy water_bowl"})
    assert bought.get_json()["ok"] is True
    premium = module.db_load_state(session_id)
    assert premium["cat_care"]["water_bowl"]["capacity"] == 5
    assert premium["cat_care"]["water_bowl"]["remaining_portions"] == 0

    for current in (basic, premium):
        ge.update_cat_stats(current, cat_clock[0] + 3600, ge.WEATHER["cloudy"])
        assert current["cat_stats"]["thirst"] == pytest.approx(75)
