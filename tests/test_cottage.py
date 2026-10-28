import game_engine as ge
import json
import subprocess
from pathlib import Path

from test_api_response_shape import api, cat_clock, create_human_garden


def test_normalize_adds_cottage_and_keeps_only_legal_item_record_fields():
    state = ge.get_default_state()
    state.pop("cottage")
    normalized = ge.normalize_state(state)
    assert normalized["cottage"] == {"items": {}}

    normalized["cottage"] = {
        "items": {"rug": {"acquired_at": "12", "source": "invalid", "price": 900}}
    }
    ge.normalize_state(normalized)
    assert normalized["cottage"]["items"] == {
        "rug": {"acquired_at": 12, "source": "system"}
    }


def test_normalize_upgrades_legacy_reward_ids_and_keeps_earliest_record_idempotently():
    state = ge.get_default_state()
    state["cottage"] = {
        "items": {
            "small_photo_frame": {"acquired_at": 12, "source": "human"},
            "potted_plant": {"acquired_at": 20, "source": "system"},
            "small_wall_art": {"acquired_at": 30, "source": "ai"},
            "small_vase": {"acquired_at": 40, "source": "system"},
            "eternal_flower": {"acquired_at": 50, "source": "human"},
        }
    }
    ge.normalize_state(state)
    assert state["cottage"]["items"] == {
        "potted_plant": {"acquired_at": 12, "source": "human"},
        "wall_art": {"acquired_at": 30, "source": "ai"},
        "hanging_plant": {"acquired_at": 40, "source": "system"},
        "beanbag_reward": {"acquired_at": 50, "source": "human"},
    }
    normalized_once = dict(state["cottage"]["items"])
    ge.normalize_state(state)
    assert state["cottage"]["items"] == normalized_once
    state["encyclopedia"] = ["baby_breath", "lisianthus", "camellia", "moonflower", "red_spider_lily"]
    assert ge.sync_cottage_rewards(state, now=100) == []


def test_cottage_purchase_uses_shared_money_once_and_records_source():
    state = ge.get_default_state()
    state["money"] = 5000
    purchasable = [item for item in ge.COTTAGE_ITEM_CATALOG.values() if "price" in item]
    assert len(purchasable) == 9
    assert sum(item["price"] for item in purchasable) == 17_300
    assert {item["id"]: item["price"] for item in purchasable} == {
        "ottoman": 600,
        "coffee_table": 900,
        "floor_lamp": 1200,
        "bookshelf": 1500,
        "flower_stand": 1800,
        "wardrobe": 2200,
        "sofa": 2600,
        "dining_set": 3000,
        "bed": 3500,
    }

    assert "添置了绿色格纹小脚凳" in ge.process_command(state, "buy_cottage_furniture ottoman", event_source="human")
    assert state["money"] == 4400
    assert state["cottage"]["items"]["ottoman"]["source"] == "human"
    assert "已经拥有" in ge.process_command(state, "buy_cottage_furniture ottoman", event_source="ai")
    assert state["money"] == 4400

    for item_id in ("rug", "curtains", "storage_sideboard"):
        assert "停售" in ge.process_command(state, f"buy_cottage_furniture {item_id}", event_source="ai")
    assert "纪念奖励" in ge.process_command(state, "buy_cottage_furniture potted_plant", event_source="human")


def test_legacy_cottage_items_remain_in_old_save_but_not_active_collection():
    state = ge.get_default_state()
    state["cottage"]["items"] = {
        "rug": {"acquired_at": 10, "source": "human"},
        "curtains": {"acquired_at": 20, "source": "ai"},
        "storage_sideboard": {"acquired_at": 30, "source": "human"},
        "bed": {"acquired_at": 40, "source": "human"},
    }
    ge.normalize_state(state)
    assert set(state["cottage"]["items"]) == {"rug", "curtains", "storage_sideboard", "bed"}
    summary = ge.get_cottage_public_summary(state)
    assert summary["total_owned"] == 1
    assert [item["id"] for item in summary["owned_items"]] == ["bed"]
    assert {item["id"] for item in summary["purchasable_items"]} == {
        "ottoman", "coffee_table", "floor_lamp", "bookshelf", "flower_stand",
        "wardrobe", "sofa", "dining_set", "bed",
    }


def test_cottage_rewards_are_idempotent_and_preserve_existing_record():
    state = ge.get_default_state()
    state["encyclopedia"] = ["baby_breath", "lisianthus", "camellia", "moonflower"]
    assert ge.sync_cottage_rewards(state, now=100) == [
        "potted_plant", "wall_art", "hanging_plant"
    ]
    assert "beanbag_reward" not in state["cottage"]["items"]
    assert ge.sync_cottage_rewards(state, now=200) == []
    assert state["cottage"]["items"]["potted_plant"] == {
        "acquired_at": 100,
        "source": "system",
    }

    state["encyclopedia"].append("red_spider_lily")
    assert ge.sync_cottage_rewards(state, now=300) == ["beanbag_reward"]
    assert ge.sync_cottage_rewards(state, now=400) == []


def test_first_harvest_immediately_syncs_cottage_reward():
    now = 1_700_000_000
    state = ge.get_default_state()
    state["pots"][0] = {
        "flower_id": "baby_breath",
        "planted_time": now - 2000,
        "watered": True,
        "growth_progress": ge.FLOWERS["baby_breath"]["grow_time"],
        "last_growth_update": now,
    }
    ge._harvest_one_pot(state, 0, now, ge.WEATHER["cloudy"])
    assert state["cottage"]["items"]["potted_plant"] == {
        "acquired_at": now,
        "source": "system",
    }


def test_api_and_web_share_cottage_summary_and_old_save_sync(api, cat_clock):
    module, client = api
    session_id, web_headers = create_human_garden(client)
    state = module.db_load_state(session_id)
    state["money"] = 1000
    state["encyclopedia"] = ["baby_breath"]
    state.pop("cottage")
    module.db_save_state(session_id, state)

    web_payload = client.get(f"/web/status?session_id={session_id}", headers=web_headers).get_json()
    cottage = web_payload["state"]["cottage"]
    assert cottage["owned_items"][0]["id"] == "potted_plant"
    assert "cottage" not in web_payload["state"]["inventory"]
    assert all(item["id"] != "potted_plant" for item in cottage["purchasable_items"])

    bought = client.post(
        "/web/cmd", headers=web_headers,
        json={"session_id": session_id, "command": "buy_cottage_furniture ottoman"},
    ).get_json()
    assert bought["state"]["cottage"]["owned_items"][-1]["source"] == "human"

    ai_payload = client.post(
        "/api/cmd", headers={"X-API-Key": "test-key"},
        json={"session_id": session_id, "command": "status"},
    ).get_json()
    assert {item["id"] for item in ai_payload["state"]["cottage"]["owned_items"]} == {
        "potted_plant", "ottoman"
    }
    assert ai_payload["state"]["cottage"]["cat_area"]["bed"]["facility_id"] == "basic_cat_bed"


def test_cottage_frontend_renders_the_v1_b_scene_from_catalog_asset_keys():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert 'data-main-pane="cottage"' in html
    assert 'id="cottageContent"' in html
    assert "function renderCottage()" in js
    assert '"/static/assets/v5/cottage/base.png"' in js
    assert "item.asset_key && !item.legacy_only" in js
    assert "locked/${item.asset_key}.svg" in js
    assert "if (ownedIds.has(item.id)) continue;" in js
    assert "cottage-scene" in js
    assert "THE FLOWER SHOP" in html


def test_cottage_shop_uses_public_catalog_and_keeps_tab_after_purchase():
    root = Path(__file__).resolve().parents[1]
    state = ge.get_default_state()
    state["money"] = 5000
    before = ge.get_cottage_public_summary(state)
    ge.process_command(state, "buy_cottage_furniture bookshelf", event_source="human")
    after = ge.get_cottage_public_summary(state)
    data = {"before": before, "after": after, "catalog": list(ge.COTTAGE_ITEM_CATALOG.values())}
    script = r"""
const fs=require('fs'),vm=require('vm');
const data=JSON.parse(process.argv[1]);
const source=fs.readFileSync('static/app.js','utf8');
function element(tag){const n={tag,children:[],listeners:{},className:'',textContent:'',hidden:false,
 append(...items){this.children.push(...items)},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(){}};
 Object.defineProperty(n,'innerHTML',{set(){this.children=[]}});return n}
const nodes={'#cottageContent':element('root'),'.cottage-panel > .cat-panel':element('article')};
let command='';
const ctx={document:{createElement:element},$:s=>nodes[s],catalog:{cottage_items:data.catalog},
 currentState:{cottage:data.before},cottageTab:'cottage',
 makeButton(label,cmd,cls,disabled){const b=element('button');b.textContent=label;b.disabled=disabled;
 if(!disabled)b.listeners.click=()=>{command=cmd;ctx.currentState.cottage=data.after;ctx.renderCottage()};return b}};
vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('const COTTAGE_CATEGORY_FALLBACK'),source.indexOf('function seedOptions(')),ctx);
const root=nodes['#cottageContent'],cat=nodes['.cottage-panel > .cat-panel'];
const walk=n=>[n,...n.children.flatMap(walk)];
const find=cls=>walk(root).find(n=>n.className===cls);
if(!source.includes('let cottageTab = "cottage";'))throw Error('default cottage tab');
ctx.renderCottage();
let tabs=root.children[0];
if(tabs.children.map(b=>b.textContent).join('/')!=='小屋/家具商店'||cat.hidden||!find('cottage-scene'))throw Error('default cottage view');
if(!walk(root).some(n=>n.src==='/static/assets/v5/cottage/locked/low_bookshelf.png'))throw Error('unowned overlay');
tabs.children[1].listeners.click();
if(!cat.hidden||find('cottage-scene'))throw Error('shop must hide cottage and cat');
let cards=find('cat-collection-grid cottage-shop-grid').children;
if(cards.length!==9)throw Error('purchase catalog');
const card=id=>cards.find(c=>walk(c).some(n=>n.alt===data.before.purchasable_items.find(i=>i.id===id).name));
if(!walk(card('bookshelf')).some(n=>n.src?.endsWith('/low_bookshelf.png'))||!walk(card('flower_stand')).some(n=>n.src?.endsWith('/plant_ladder.png')))throw Error('asset key');
if(cards.some(c=>walk(c).some(n=>['potted_plant','wall_art','hanging_plant','beanbag_reward','rug'].some(id=>n.src?.endsWith('/'+id+'.png')))))throw Error('non-purchasable item');
walk(card('bookshelf')).find(n=>n.textContent==='购买').listeners.click();
if(command!=='buy_cottage_furniture bookshelf'||ctx.cottageTab!=='shop'||!cat.hidden)throw Error('purchase or retained tab');
cards=find('cat-collection-grid cottage-shop-grid').children;
if(!walk(card('bookshelf')).some(n=>n.textContent==='已拥有'&&n.disabled))throw Error('owned purchase button');
root.children[0].children[0].listeners.click();
if(cat.hidden||!find('cottage-scene')||walk(root).some(n=>n.src==='/static/assets/v5/cottage/locked/low_bookshelf.png'))throw Error('owned scene');
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script, json.dumps(data, ensure_ascii=False)], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"

