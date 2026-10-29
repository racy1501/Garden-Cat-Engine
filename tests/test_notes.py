import importlib
import json
import os
import re
import sys
import time
import tomllib
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


def test_release_versions_and_public_api_introduction(api):
    module, client = api
    root = Path(__file__).resolve().parents[1]
    metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert module.APP_VERSION == "v5.2.0"
    assert metadata["project"]["version"] == module.APP_VERSION.removeprefix("v")
    html = client.get("/").get_data(as_text=True)
    assert f"花园与猫咪 {module.APP_VERSION}" in html
    assert f"/static/app.js?v={module.APP_VERSION}" in html
    assert "v4.9.9" not in html
    assert "0 / 8" not in html
    assert "同一个 session_id" in html

    info = client.get("/api/info").get_json()
    public_text = json.dumps(info, ensure_ascii=False)
    assert module.APP_VERSION in info["game"]
    assert "/api/register" not in public_text
    assert "有效 session_id" in public_text
    assert "X-API-Key" in public_text
    assert "AI/API 端不能注册或创建新存档" in public_text
    assert "害虫每5分钟" not in public_text
    assert "达到触发点后暂停生长" in public_text
    for feature in ("17 种花", "12 款正式花束", "花店", "小屋", "家具商店"):
        assert feature in public_text
    state_help = next(value for key, value in info["endpoints"].items() if "/api/state" in key)
    assert "已停用" in state_help
    catalog = client.get("/api/catalog").get_json()
    assert catalog["version"] == module.APP_VERSION


def test_readme_describes_current_release_and_formal_bouquet_catalog(api):
    module, _ = api
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert readme.startswith(f"# 🌸 花园与猫咪 {module.APP_VERSION}")
    for obsolete in (
        "POST /api/register", "不存在花束中间库存", "不出售、不产生金币",
        "第一版固定花束", "每 5 分钟最多检查一次", "12种花", "12 种花",
        "网页顶部的「花束」与花园、商店同级",
    ):
        assert obsolete not in readme
    for current in (
        "有效的 `session_id`", "X-API-Key", "GET /api/catalog", "bouquet inventory",
        "craft_bouquet", "gift_bouquet", "list_bouquet", "24 小时", "共同小屋",
    ):
        assert current in readme
    release_intro = re.search(
        r"^## v5\.2\.0 发布介绍\n(.*?)(?=^## |\Z)", readme, re.MULTILINE | re.DOTALL
    ).group(1)
    cottage_intro = next(
        line for line in release_intro.splitlines() if "**共同小屋**" in line
    )
    assert "9 件" in cottage_intro and "家具" in cottage_intro and "可购买" in cottage_intro
    assert "4 件" in cottage_intro and "奖励装饰" in cottage_intro
    cat_intro = next(
        line for line in release_intro.splitlines() if "**猫咪生活与收藏**" in line
    )
    assert "正式收养" in cat_intro
    listed = re.search(r"正式 12 款花束：([^。]+)。", readme).group(1).split("、")
    expected = ["初见", "晨光", "晴野", "心笺", "晚风", "柔云", "蓝信", "樱枝", "春宴", "春山", "月下书", "彼岸诗"]
    assert listed == expected
    assert listed == [bouquet["name"] for bouquet in module.BOUQUETS.values()]
    assert "暖阳、紫雾、小花园只作为旧存档历史赠礼兼容展示" in readme
    flower_rows = re.findall(r"^\| (\S+) \| (\d+)分钟 \|$", readme, re.MULTILINE)
    assert flower_rows == [(flower["name"], str(flower["grow_time"] // 60)) for flower in module.FLOWERS.values()]


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
    assert module.APP_VERSION == "v5.2.0"
    assert f"花园与猫咪 {module.APP_VERSION}" in html

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


def test_ai_note_unread_cursor_is_durable_and_legacy_notes_are_read(api, monkeypatch):
    module, client = api
    session_id, human_headers = create_human_garden(client)
    ai_headers = {"X-API-Key": "test-key"}

    old_note, _, error = module.db_add_note(
        session_id,
        "ai",
        "升级前的旧便签",
        now=1_700_000_000,
    )
    assert error is None and old_note is not None
    with module._get_conn() as conn:
        conn.execute("DELETE FROM garden_note_reads")
        conn.commit()
    assert module.db_note_read_status(session_id)["has_unread_ai_notes"] is False

    first_ai = client.post(
        "/api/notes",
        headers=ai_headers,
        json={"session_id": session_id, "content": "AI刚写的新便签"},
    )
    assert first_ai.status_code == 200
    assert first_ai.get_json()["has_unread_ai_notes"] is True
    assert client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["notes"]["has_unread_ai_notes"] is True

    viewed = client.get(
        f"/web/notes?session_id={session_id}&page=1", headers=human_headers
    )
    assert viewed.status_code == 200
    assert viewed.get_json()["has_unread_ai_notes"] is False
    assert client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["notes"]["has_unread_ai_notes"] is False

    now = int(time.time())
    monkeypatch.setattr(
        module.time,
        "time",
        lambda: now + module.NOTE_COOLDOWN_SECONDS + 1,
    )
    second_ai = client.post(
        "/api/notes",
        headers=ai_headers,
        json={"session_id": session_id, "content": "AI再次写的新便签"},
    )
    assert second_ai.status_code == 200
    assert client.get(
        f"/web/status?session_id={session_id}", headers=human_headers
    ).get_json()["notes"]["has_unread_ai_notes"] is True

    human = client.post(
        "/web/notes",
        headers=human_headers,
        json={"session_id": session_id, "content": "人类也能继续写便签"},
    )
    assert human.status_code == 200
    assert human.get_json()["note"]["author_type"] == "human"
    assert human.get_json()["has_unread_ai_notes"] is False
