from pathlib import Path
from html.parser import HTMLParser
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


def test_three_locations_keep_the_original_garden_function_strip():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    class Elements(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []
            self.nodes = []

        def handle_starttag(self, tag, attrs):
            node = {"tag": tag, "attrs": dict(attrs), "parent": self.stack[-1] if self.stack else None}
            self.nodes.append(node)
            if tag not in {"area", "base", "br", "hr", "img", "input", "link", "meta", "source"}:
                self.stack.append(node)

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1]["tag"] == tag:
                self.stack.pop()

    elements = Elements()
    elements.feed(html)

    def by_class(name):
        matches = [node for node in elements.nodes if name in node["attrs"].get("class", "").split()]
        assert len(matches) == 1
        return matches[0]

    def by_id(name):
        matches = [node for node in elements.nodes if node["attrs"].get("id") == name]
        assert len(matches) == 1
        return matches[0]

    top = by_class("location-switch-strip")
    garden = by_class("garden-location-panel")
    strip = by_class("main-switch-strip")
    garden_pane = by_class("garden-panel")
    store_pane = by_class("store-panel")
    bouquet = by_class("bouquet-panel")
    cottage = by_class("cottage-panel")
    assert garden["parent"] is bouquet["parent"] is cottage["parent"]
    assert strip["parent"] is garden
    assert garden_pane["parent"] is store_pane["parent"] is garden
    assert by_class("vase-panel")["parent"] is garden_pane
    assert by_class("cat-panel")["parent"] is cottage
    assert [node["attrs"].get("data-main-pane") for node in elements.nodes if node["parent"] is by_class("location-tabs") and node["tag"] == "button"] == ["garden", "bouquet", "cottage"]
    garden_tabs = [node for node in elements.nodes if node["parent"] is strip and "sticky-title-tabs" in node["attrs"].get("class", "").split()]
    assert len(garden_tabs) == 1
    assert [node["attrs"].get("data-garden-tab") for node in elements.nodes if node["parent"] is garden_tabs[0] and node["tag"] == "button"] == ["garden", "store"]
    assert all(by_id(name)["parent"] is by_class("main-strip-actions") for name in ("backpackBtn", "harvestAllBtn", "notesBtn"))
    assert 'id="gardenTitle"' in html
    assert html.index("</header>") < html.index('class="location-switch-strip"') < html.index('class="dashboard-grid"')
    assert html.count('data-main-pane="garden"') == 1
    assert html.count('data-main-pane="bouquet"') == 1
    assert html.count('data-main-pane="cottage"') == 1
    assert 'data-main-pane="store"' not in html
    assert 'class="main-switch-strip"' in html
    assert 'class="main-strip-actions"' in html
    assert 'class="garden-inner-tabs"' not in html
    strip_start = html.index('class="main-switch-strip"')
    location_start = html.index('class="garden-location-panel main-switch-pane active"')
    garden_start = html.index('class="panel garden-panel garden-switch-pane active"')
    store_start = html.index('class="panel store-panel garden-switch-pane"')
    location_end = html.index("</section>", store_start)
    bouquet_start = html.index('class="panel bouquet-panel main-switch-pane"')
    assert location_start < strip_start < garden_start < store_start < location_end < bouquet_start
    assert 'data-location-pane="garden"' in html
    assert 'data-garden-pane="garden"' in html
    assert 'data-garden-pane="store"' in html
    assert ".main-switch-strip { display:flex;" in css
    assert ".main-strip-actions {" in css
    assert ".main-switch-pane, .garden-switch-pane { display:none; }" in css
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in css
    assert "'.garden-location-panel .main-switch-strip .sticky-tab'" in js
    assert "'.location-switch-strip .sticky-tab'" in js
    assert "'.garden-location-panel .garden-switch-pane'" in js
    assert "'.main-column > .main-switch-pane'" in js
    assert "pane.dataset.gardenPane===button.dataset.gardenTab" in js
    assert "pane.dataset.locationPane===button.dataset.mainPane" in js
    assert "document.querySelectorAll('.sticky-tab')" not in js
    assert "document.querySelectorAll('.main-switch-pane')" not in js
    assert "THE FLOWER SHOP" in html
    assert "THE BOUQUET" not in html
    assert 'id="bouquetPageContent"' in html
    assert 'id="bouquetCollectionBtn"' not in html
    assert "renderBouquetCollectionModal" not in js
    assert "renderBouquetPage" in js
    assert "bouquet_gifts" in js


def test_bouquet_main_page_keeps_tabs_and_unread_badge():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert '[["bouquets", "花束"], ["cards", "卡片"]]' in js
    assert "markBouquetGiftsRead" in js
    assert "/web/bouquets/read" in js
    assert 'name.textContent = bouquet.name' in js
    assert "const discoveredOptions = new Map(" in js
    assert 'count.textContent = "配方未发现";' in js
    assert 'count.textContent = "已发现，尚未赠送";' in js
    assert ".bouquet-main-tab.has-unread::after" in css


def test_bouquet_new_badges_use_only_the_current_visit_snapshot():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert "let bouquetVisitNewGiftIndexes = new Set();" in js
    assert "function captureUnreadBouquetGiftIndexes()" in js
    assert "currentState?.unread_bouquet_gift_count" in js
    assert "for (let index = gifts.length - unreadGiftCount; index < gifts.length; index += 1)" in js
    assert "bouquetVisitNewGiftIndexes.add(index);" in js
    assert 'badge.textContent = "新";' in js
    assert "if (hasNewGift) card.append(createBouquetNewBadge());" in js
    assert "if (bouquetVisitNewGiftIndexes.has(index)) card.append(createBouquetNewBadge());" in js
    assert js.index("captureUnreadBouquetGiftIndexes();") < js.index("markBouquetGiftsRead();")
    assert ".bouquet-new-badge" in css


def test_bouquet_detail_uses_its_latest_nonempty_card_and_compact_modal():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert "function getLatestBouquetCard(gifts)" in js
    assert 'gifts.find((gift) => String(gift.message || "").trim())' in js
    assert "const latestCard = getLatestBouquetCard(gifts);" in js
    assert "最近的卡片" in js
    assert "累计收到 ×${gifts.length}" in js
    assert "modal-card-bouquet-detail" in js
    assert ".modal-card-bouquet-detail" in css
    assert ".bouquet-detail-card" in css


def test_unlocked_bouquet_card_opens_existing_detail_modal():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    page_start = js.index("function renderBouquetPage")
    page_end = js.index("function resetModalPresentation", page_start)
    page_js = js[page_start:page_end]
    detail_start = js.index("function showBouquetDetails")
    detail_end = js.index("function renderBouquetPage", detail_start)
    detail_js = js[detail_start:detail_end]

    assert 'card.addEventListener("click", () => showBouquetDetails(bouquetId))' in page_js
    assert "else card.disabled = true;" in page_js
    assert '$("#modal").classList.remove("hidden");' in detail_js
    assert detail_js.index("body.append(history);") < detail_js.index(
        '$("#modal").classList.remove("hidden");'
    )
    assert '$("#modalClose").addEventListener("click", closeModal);' in js


def test_garden_notice_does_not_promote_old_history_to_notification():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert "function extractImportantGardenNotice(message)" in js
    notice = js.split("function renderGardenNotice()", 1)[1].split("function ensureOfflineSummaryBar()", 1)[0]
    assert "recent_events" not in notice
    assert "let notice = latestNotice;" in notice


def test_bouquet_artwork_uses_id_derived_assets_and_fallback():
    root = Path(__file__).resolve().parents[1]
    asset_dir = root / "static" / "assets" / "v5" / "bouquets"
    bouquet_ids = [
        "first_meeting",
        "soft_cloud",
        "blue_letter",
        "spring_banquet",
        "cherry_branch",
    ]
    assert all((asset_dir / f"{bouquet_id}.png").is_file() for bouquet_id in bouquet_ids)
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert "/static/assets/v5/bouquets/" in js
    assert "getBouquetImageUrl" in js
    assert "const renderFallback = () =>" in js
    assert "bouquet-artwork-fallback" in js


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
    assert len(catalog.json["flowers"]) == 17
    assert catalog.json["flowers"]["moonflower"]["unlock_requirement"] == {
        "encyclopedia": 15,
        "harvests": 105,
    }
    assert catalog.json["flowers"]["red_spider_lily"]["unlock_requirement"] == {
        "encyclopedia": 16,
        "harvests": 125,
    }
    assert client.post("/api/register", json={}).status_code == 401


def test_web_unlocked_flowers_uses_the_engine_unlock_result(tmp_path):
    game_api = load_app(tmp_path)
    client = game_api.app.test_client()
    created = client.post("/web/register", json={})
    sid = created.json["session_id"]
    token = created.json["garden_token"]
    state = game_api.db_load_state(sid)
    state["encyclopedia"] = [
        "daisy",
        "tulip",
        "pansy",
        "sunflower",
        "rose",
        "baby_breath",
        "carnation",
    ]
    state["flower_harvest_counts"] = {"daisy": 24}
    game_api.db_save_state(sid, state)

    response = client.get(
        f"/web/status?session_id={sid}",
        headers={"X-Garden-Token": token},
    )

    assert response.status_code == 200
    assert response.json["state"]["unlocked_flowers"] == [
        "daisy",
        "tulip",
        "pansy",
        "sunflower",
        "rose",
        "baby_breath",
        "carnation",
        "lavender",
        "hydrangea",
        "lily",
    ]


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


def test_v489_cat_and_vase_belong_to_their_location_panes():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    garden_start = html.index('class="panel garden-panel garden-switch-pane active"')
    bouquet_start = html.index('class="panel bouquet-panel main-switch-pane"')
    cottage_start = html.index('class="panel cottage-panel main-switch-pane"')
    side_column_start = html.index('<aside class="side-column">')
    vase_start = html.index('class="panel vase-panel"')
    cat_start = html.index('class="panel cat-panel"')
    assert '购买后进入背包，可在上方空花盆种植' in html
    assert garden_start < vase_start < bouquet_start
    assert cottage_start < cat_start < side_column_start
    assert 'class="panel vase-panel"' not in html[bouquet_start:cottage_start]
    assert 'class="panel cat-panel"' not in html[bouquet_start:cottage_start]
    assert "猫咪生活区" in html
    assert 'data-cat-pane="cat" type="button">猫窝</button>' in html
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


def test_flower_shop_3a_uses_bouquet_page_without_a_separate_shop_screen():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert "renderBouquetWorkshop" in js
    assert "craft_bouquet bouquet_id=" in js
    assert "gift_bouquet instance_id=" in js
    assert "set_flower_shop_hours" in js
    assert "launch_flower_shop" in js
    assert ".flower-shop-panel" in css
    assert "flower-shop-panel" not in html


def test_flower_shop_3b_frontend_lists_bouquets_without_exposing_sale_odds():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert "list_bouquet instance_id=" in js
    assert "slot.current_price" in js
    assert "slot.expires_in_seconds" in js
    assert "闭店中 · 继续老化" in js
    assert "sale_business_seconds_remaining" not in js
    assert "will_sell" not in js
    assert "82%" not in js
    assert ".flower-shop-shelves article" in css
    assert "upgrade_flower_shop_shelf" in js
    assert "buy_flower_shop_freshener" in js
    assert "shop.slots || []" in js
    assert "不延长24小时报废时间" in js
    assert ".flower-shop-facilities" in css
    assert "shop.shop_buff_active" in js
    assert "猫咪好运" in js
    assert "成交金额 +10%" in js
    assert "12%" not in js
    assert ".flower-shop-buff" in css
