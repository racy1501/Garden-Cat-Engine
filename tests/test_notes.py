import importlib
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "garden_test.db"))
    monkeypatch.setenv("GARDEN_API_KEY", "test-key")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    if "game_api" in sys.modules:
        del sys.modules["game_api"]
    module = importlib.import_module("game_api")
    module.ensure_schema()
    return module, module.app.test_client()


def create_human_garden(client):
    response = client.post("/web/register", json={"name": "便签测试园"})
    assert response.status_code == 200
    payload = response.get_json()
    return payload["session_id"], {"X-Garden-Token": payload["garden_token"]}


def test_human_and_ai_share_timeline_with_separate_cooldowns(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    ai_headers = {"X-API-Key": "test-key"}

    human = client.post(
        "/web/notes",
        headers=human_headers,
        json={"session_id": session_id, "content": "今天的花开得很好"},
    )
    assert human.status_code == 200
    assert human.get_json()["note"]["author_type"] == "human"

    # 人类刚写完不会占用 AI 的冷却。
    ai = client.post(
        "/api/notes",
        headers=ai_headers,
        json={"session_id": session_id, "content": "我给小猫添过水啦"},
    )
    assert ai.status_code == 200
    assert ai.get_json()["note"]["author_type"] == "ai"

    timeline = client.get(
        f"/api/notes?session_id={session_id}&page=1",
        headers=ai_headers,
    ).get_json()
    assert timeline["total"] == 2
    assert [note["author_type"] for note in timeline["notes"]] == ["ai", "human"]

    second_human = client.post(
        "/web/notes",
        headers=human_headers,
        json={"session_id": session_id, "content": "第二张人类便签"},
    )
    second_ai = client.post(
        "/api/notes",
        headers=ai_headers,
        json={"session_id": session_id, "content": "第二张AI便签"},
    )
    assert second_human.status_code == 429
    assert second_ai.status_code == 429
    assert second_human.get_json()["cooldown_remaining_seconds"] > 0
    assert second_ai.get_json()["cooldown_remaining_seconds"] > 0
    assert module.NOTE_COOLDOWN_SECONDS == 2 * 60 * 60


def test_note_length_pagination_and_append_only_routes(api):
    module, client = api
    session_id, human_headers = create_human_garden(client)

    too_long = client.post(
        "/web/notes",
        headers=human_headers,
        json={
            "session_id": session_id,
            "content": "一二三四五六七八九十一二三四五六七八九十一",
        },
    )
    assert too_long.status_code == 400

    # 用不同时间写入 12 条，验证数据库长期追加与分页，不把历史塞进主存档 JSON。
    base_time = 1_700_000_000
    for index in range(12):
        note, remaining, error = module.db_add_note(
            session_id,
            "human",
            f"便签{index + 1}",
            now=base_time + index * module.NOTE_COOLDOWN_SECONDS,
        )
        assert error is None
        assert remaining == module.NOTE_COOLDOWN_SECONDS
        assert note is not None

    page_one = module.db_list_notes(session_id, "human", page=1, now=base_time + 99_999)
    page_two = module.db_list_notes(session_id, "human", page=2, now=base_time + 99_999)
    assert page_one["total"] == 12
    assert page_one["total_pages"] == 2
    assert len(page_one["notes"]) == 10
    assert len(page_two["notes"]) == 2
    assert page_one["notes"][0]["content"] == "便签12"
    assert page_two["notes"][-1]["content"] == "便签1"

    # 没有便签修改、删除路由。
    assert client.patch("/web/notes", headers=human_headers).status_code == 405
    assert client.delete("/web/notes", headers=human_headers).status_code == 405


def test_ui_command_help_and_pet_cooldown_regression(api):
    module, client = api
    session_id, _ = create_human_garden(client)
    ai_headers = {"X-API-Key": "test-key"}

    home = client.get("/")
    html = home.get_data(as_text=True)
    assert home.status_code == 200
    assert 'id="notesBtn"' in html
    assert "v4.9.8" in html

    write = client.post(
        "/api/cmd",
        headers=ai_headers,
        json={"session_id": session_id, "command": "note 今晚也要记得休息"},
    )
    assert write.status_code == 200
    assert "已贴好" in write.get_json()["message"]

    read = client.post(
        "/api/cmd",
        headers=ai_headers,
        json={"session_id": session_id, "command": "notes"},
    )
    assert read.status_code == 200
    assert "今晚也要记得休息" in read.get_json()["message"]

    help_response = client.get("/api/help", headers=ai_headers)
    assert "notes" in help_response.get_json()["message"]
    assert "note &lt;内容&gt;" not in help_response.get_json()["message"]

    # 本次功能不能碰坏摸猫的现实 10 分钟冷却。
    assert module.PET_COOLDOWN_REAL_MINUTES == 10
