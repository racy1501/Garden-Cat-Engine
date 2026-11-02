from copy import deepcopy

import game_engine as ge
import pytest

from test_api_response_shape import api, cat_clock, create_human_garden


def test_human_crafts_but_only_agent_can_gift(api, cat_clock):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["encyclopedia"] = ["tulip", "baby_breath"]
    state["inventory"]["flowers"] = {"tulip": 4, "baby_breath": 2}
    state["bouquet_gifts"] = [{"bouquet_id": "first_meeting", "components": {"tulip": 2, "rose": 2},
                                "sent_at": 1, "message": "旧卡片"}]
    state["cat_state"]["next_visit_at"] = cat_clock[0] + 3600
    module.db_save_state(session_id, state)

    def human(command):
        response = client.post("/web/cmd", headers=human_headers,
                               json={"session_id": session_id, "command": command})
        assert response.status_code == 200
        return response.get_json()

    help_text = human("help")["message"]
    assert "make_bouquet - 查看花束配方" in help_text
    assert "花束赠礼由 AI 送给人类" in help_text
    assert "gift_bouquet instance_id=" not in help_text
    assert human("make_bouquet")["ok"] is True  # 无参数仍可查看配方。
    assert human("craft_bouquet bouquet_id=first_meeting")["ok"] is True
    before = module.db_load_state(session_id)
    instance_id = before["bouquet_inventory"][0]["instance_id"]
    for command in (f"GiFt_BoUqUeT instance_id={instance_id} message=自赠",
                    "MAKE_BOUQUET bouquet_id=first_meeting message=自赠",
                    "make_bouquet first_meeting"):
        assert human(command)["ok"] is False
        after = module.db_load_state(session_id)
        assert after["bouquet_gifts"] == before["bouquet_gifts"]
        assert after["bouquet_inventory"] == before["bouquet_inventory"]
        assert after["inventory"]["flowers"] == before["inventory"]["flowers"]
        assert after["events"] == before["events"]

    ai_headers = {"X-API-Key": "test-key"}
    for command in (f"gift_bouquet instance_id={instance_id} message=第一张卡片",
                    "make_bouquet bouquet_id=first_meeting message=第二张卡片"):
        response = client.post("/api/cmd", headers=ai_headers,
                               json={"session_id": session_id, "command": command})
        assert response.status_code == 200
        assert response.get_json()["ok"] is True

    web_state = client.get(f"/web/status?session_id={session_id}", headers=human_headers).get_json()["state"]
    assert [gift["message"] for gift in web_state["bouquet_gifts"]] == ["旧卡片", "第一张卡片", "第二张卡片"]
    assert len([event for event in module.db_load_state(session_id)["events"]
                if "送出了一束" in event["text"]]) == 2


@pytest.mark.parametrize("command", ["make_bouquet first_meeting", "gift_bouquet instance_id=one"])
def test_human_source_is_rejected_at_command_boundary(command):
    state = ge.get_default_state()
    before = deepcopy(state)
    result = ge.execute_command(state, command, event_source="human")
    assert result.ok is False
    assert state == before
