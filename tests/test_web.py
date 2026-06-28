from pathlib import Path
import importlib
import os


def load_app(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "garden_web.db")
    os.environ["GARDEN_API_KEY"] = "test-key"
    import game_api
    return importlib.reload(game_api)


def test_home_serves_visual_frontend(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")
    assert "花园与猫咪" in response.get_data(as_text=True)
    assert "/static/app.js" in response.get_data(as_text=True)


def test_web_garden_uses_private_per_garden_token(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()

    created = client.post("/web/register", json={"name": "人类花园"})
    assert created.status_code == 200
    sid = created.json["session_id"]
    token = created.json["garden_token"]
    assert sid.startswith("web_")
    assert token

    status = client.get(
        f"/web/status?session_id={sid}",
        headers={"X-Garden-Token": token},
    )
    assert status.status_code == 200
    assert status.json["state"]["garden_name"] == "人类花园"

    denied = client.get(
        f"/web/status?session_id={sid}",
        headers={"X-Garden-Token": "wrong-token"},
    )
    assert denied.status_code == 401


def test_web_command_does_not_need_global_api_key(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    created = client.post("/web/register", json={})
    sid = created.json["session_id"]
    token = created.json["garden_token"]

    result = client.post(
        "/web/cmd",
        headers={"X-Garden-Token": token},
        json={"session_id": sid, "command": "buy daisy 1"},
    )
    assert result.status_code == 200
    assert result.json["state"]["money"] == 47


def test_catalog_is_public_and_ai_api_stays_protected(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    catalog = client.get("/api/catalog")
    assert catalog.status_code == 200
    assert catalog.json["flowers"]["moonflower"]["unlock_requirement"] == 7
    assert client.post("/api/register", json={}).status_code == 401


def test_web_summary_includes_cat_name_and_readable_letters(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    created = client.post("/web/register", json={})
    sid = created.json["session_id"]
    token = created.json["garden_token"]

    state = game_api.db_load_state(sid)
    state["money"] = 200
    state["letters_received"] = [0, 1]
    game_api.db_save_state(sid, state)

    adopted = client.post(
        "/web/cmd",
        headers={"X-Garden-Token": token},
        json={"session_id": sid, "command": "adopt 栗子"},
    )
    assert adopted.status_code == 200
    assert adopted.json["state"]["cat"]["name"] == "栗子"
    assert len(adopted.json["state"]["letters"]) == 2
    assert "爪印" in adopted.json["state"]["letters"][0]["text"]


def test_web_summary_includes_time_speed_and_pet_cooldown(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    created = client.post("/web/register", json={})
    sid = created.json["session_id"]
    token = created.json["garden_token"]

    state = game_api.db_load_state(sid)
    state["money"] = 200
    game_api.db_save_state(sid, state)
    adopted = client.post(
        "/web/cmd",
        headers={"X-Garden-Token": token},
        json={"session_id": sid, "command": "adopt 栗子"},
    )
    summary = adopted.json["state"]
    assert summary["weather_grow_speed"] in (1.0, 1.1, 1.2)
    assert summary["game_day"] >= 1
    assert summary["daypart"] in {"清晨", "上午", "中午", "下午", "傍晚", "夜晚"}
    assert summary["cat"]["pet_cooldown_remaining_seconds"] == 0


def test_v485_ui_assets_and_labels():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert "👝" in html
    assert "· ×1.1" not in html
    assert "/static/orange_cat.png" in js
    assert "/static/lavender.svg" in js
    assert ".mini-btn:disabled" in css
    assert (root / "static" / "orange_cat.png").exists()
    assert (root / "static" / "lavender.svg").exists()


def test_v486_fixed_six_pot_layout_and_prices(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    catalog = client.get("/api/catalog").json
    assert catalog["max_pots"] == 6
    assert catalog["pot_unlock_costs"] == {"4": 20, "5": 35, "6": 50}

    created = client.post("/web/register", json={})
    state = created.json["state"]
    assert state["max_pots"] == 3
    assert state["pot_capacity"] == 6
    assert state["next_pot_cost"] == 20

    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    assert "for (let slot = 1; slot <= capacity; slot += 1)" in js
    assert "locked-pot" in js
    assert "potCountMeta" in html
    assert "buyPotBtn" not in html


def test_v487_main_action_area_and_harvest_all(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="gardenNotice"' in html
    assert 'id="seedShopGrid"' in html
    assert 'id="harvestAllBtn"' in html
    assert 'data-store-tab="seeds"' in html
    assert 'data-store-tab="cat-items"' in html
    assert 'id="suppliesTab"' not in html
    assert 'runCommand("harvest all"' in js
    assert "renderSeedShop()" in js
    assert "renderGardenNotice()" in js
    assert "pointer-events: none" not in css.split(".loading", 1)[1].split("}", 1)[0]


def test_v488_mobile_compact_layout():
    root = Path(__file__).resolve().parents[1]
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert "grid-template-columns: 1.35fr repeat(3, minmax(0, 1fr));" in css
    assert ".pots-grid {" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in css
    assert ".vase-grid {" in css
    assert ".command-panel {" in css
    assert "display: none;" in css


def test_v489_mobile_three_columns_and_cat_before_vase():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert '购买后进入背包，可在上方空花盆种植' in html
    assert html.index('class="panel cat-panel"') < html.index('class="panel vase-panel"')
    assert 'grid-template-columns: repeat(3, minmax(0, 1fr));' in css
    assert '.utility-card' in css


def test_v4810_compact_store_and_item_effects():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="catShopGrid"' in html
    assert 'data-store-tab="seeds"' in html
    assert 'data-store-tab="cat-items"' in html
    assert 'id="suppliesTab"' not in html
    assert "renderCatShop()" in js
    assert "口渴下降速度减半" in js
    assert "心情自然下降降低40%" in js
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in css
    assert ".shop-square-card" in css
    assert ".vase-grid.real-vase" in css


def test_v4811_live_timers_encyclopedia_shortcut_and_lily_asset():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="encyclopediaCard"' in html
    assert 'lily: "/static/lily.svg"' in js
    assert 'lily: "🪷"' not in js
    assert (root / "static" / "lily.svg").exists()
    assert "GAME_MINUTES_PER_REAL_SECOND" in js
    assert "updateLiveGameTime()" in js
    assert "updateLiveCountdowns()" in js
    assert "dataset.livePotStatus" in js
    assert "dataset.liveVaseInfo" in js
    assert "setInterval(updateLiveCountdowns, 1_000)" in js
    assert "openCollectionShortcut" in js
    assert "waitForNextPaint" in js
    assert ".pending-action" in css
    assert ".metric-link" in css
