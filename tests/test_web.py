from pathlib import Path
from html.parser import HTMLParser
import importlib
import os
import subprocess


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


def test_new_state_initial_resources_include_five_cat_food_servings(tmp_path):
    game_api = load_app(tmp_path)

    state = game_api._new_state()

    assert state["inventory"]["items"]["basic_food"] == 5
    assert state["money"] == 50
    assert state["max_pots"] == 3
    assert state["inventory"]["seeds"]["daisy"] == 3


def test_v520_announcement_renders_and_is_seen_once_after_old_announcement():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('static/app.js','utf8');
const key=source.match(/const UPDATE_ANNOUNCEMENT_SEEN_KEY = "([^"]+)";/)[1];
assert.strictEqual(key,'garden_cat_update_seen_v5_2_0');
const storage=new Map([['garden_cat_update_seen_v5_0','1']]);
function createPage(){
  function element(){return {textContent:'',children:[],listeners:{},
    classList:{add(){},remove(){},contains(){return false;}},
    append(...children){this.children.push(...children);},
    addEventListener(event,callback){this.listeners[event]=callback;}};}
  const nodes={};
  const context={
    $:selector=>nodes[selector]||(nodes[selector]=element()),
    document:{createElement:element},
    localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,v)},
    currentState:{},hasTriedAutoUpdateAnnouncement:false,
    resetModalPresentation(){},closeModal(){}
  };
  vm.createContext(context);
  vm.runInContext(`const UPDATE_ANNOUNCEMENT_SEEN_KEY=${JSON.stringify(key)};`+
    source.slice(source.indexOf('function hasSeenUpdateAnnouncement()'),
                 source.indexOf('function showNewGameModal()')),context);
  return {context,nodes};
}
function text(node){return [node.textContent,...node.children.map(text)].join('\n');}
const first=createPage();
first.context.maybeAutoShowUpdateAnnouncement();
assert.strictEqual(first.nodes['#modalTitle'].textContent,'🌷 v5.2.0 大型更新：花店开张，小屋亮灯');
const body=first.nodes['#modalBody'],content=text(body);
for(const feature of ['三个可以生活的地方','17 种花','12 款正式花束','3×3 售卖货架',
  '额外好生意','共同小屋','藏品与信件','花园手记'])
  assert(content.includes(feature),feature);
assert(content.includes('都有固定的位置，不需要自行摆放'));
assert(content.includes('花卉奖励装饰则会随游戏进程解锁'));
assert(!content.includes('布置出喜欢的模样'));
const childCount=body.children.length;
first.context.maybeAutoShowUpdateAnnouncement();
assert.strictEqual(body.children.length,childCount);
const confirm=body.children.at(-1).children[0];
confirm.listeners.click();
assert.strictEqual(storage.get(key),'1');
assert.strictEqual(storage.get('garden_cat_update_seen_v5_0'),'1');
const reloaded=createPage();
reloaded.context.maybeAutoShowUpdateAnnouncement();
assert.strictEqual(reloaded.nodes['#modalTitle'],undefined);
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


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
    assert '[["bouquets", "花束"], ["cards", "赠礼"]]' in js
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


def test_historical_bouquets_render_only_from_gift_history_and_open_details():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
const nodes={};
function element(tag){const node={tag,className:'',textContent:'',children:[],listeners:{},classList:{add(){},remove(){}},
 append(...items){this.children.push(...items)},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(){}};
 Object.defineProperty(node,'innerHTML',{get(){return this._html||''},set(value){this._html=value;this.children=[]}});return node}
function get(selector){return nodes[selector]||(nodes[selector]=element('root'))}
const formalIds=['first_meeting','morning_light','sunny_field','heart_note','evening_breeze','soft_cloud','blue_letter','cherry_branch','spring_banquet','spring_mountain','moonlit_book','higan_poem'];
const bouquetCatalog=Object.fromEntries(formalIds.map((id)=>[id,{name:id,components:{daisy:1}}]));
const options=formalIds.map((bouquet_id)=>({bouquet_id,name:bouquetCatalog[bouquet_id].name,components:{daisy:1},can_make:true}));
const gifts=[
 {bouquet_id:'warm_sun',components:{sunflower:1,rose:2,lily:1},sent_at:300,message:'\u6696\u6696\u7684\u9633\u5149\u9001\u7ed9\u4f60'},
 {bouquet_id:'warm_sun',components:{sunflower:2,rose:1},sent_at:200,message:null},
 {bouquet_id:'purple_mist',components:{daisy:2,lavender:1,lily:1},sent_at:100,message:'\u7d2b\u8272\u7684\u82b1'},
 {bouquet_id:'little_garden',components:{daisy:2,rose:2},sent_at:50,message:'\u4e00\u5ea7\u5c0f\u82b1\u56ed'}
];
const madeCommands=[];
const ctx={catalog:{bouquets:bouquetCatalog,flowers:{sunflower:{name:'\u5411\u65e5\u8475'},rose:{name:'\u73ab\u7470'},lily:{name:'\u767e\u5408'},daisy:{name:'\u96cf\u83ca'},lavender:{name:'\u85b0\u8863\u8349'}}},
 currentState:{bouquet_gifts:gifts,bouquet_options:options,bouquet_inventory:[],flower_shop:{},money:0},bouquetVisitNewGiftIndexes:new Set(),bouquetWorkshopTab:'craft',
 document:{createElement:element},$:get,formatBouquetTimestamp:(stamp)=>`time-${stamp}`,formatDuration:()=>'',
 renderBouquetWorkshop(){},resetModalPresentation(){},closeModal(){},makeButton(label,command){madeCommands.push(command);const b=element('button');b.textContent=label;return b;}};
vm.createContext(ctx);
const ranges=[['function getBouquetImageUrl(', 'function renderBouquetArtwork('],
 ['function renderBouquetArtwork(', 'function renderBouquetTabs('],
 ['function renderBouquetTabs(', 'function getLatestBouquetCard('],
 ['function getLatestBouquetCard(', 'function flowerComponentText('],
 ['function flowerComponentText(', 'function formatShopStartMinute('],
 ['function renderBouquetWorkshop(', 'function captureUnreadBouquetGiftIndexes('],
 ['function showBouquetDetails(', 'function renderBouquetPage('],
 ['function renderBouquetEncyclopedia(', 'function renderBouquetPage('],
 ['function renderBouquetPage(', 'async function markBouquetGiftsRead(']];
for(const [start,end] of ranges){const a=source.indexOf(start),b=source.indexOf(end,a);vm.runInContext(source.slice(a,b),ctx)}
function cards(){return get('#bouquetPageContent').children.find((x)=>x.className==='bouquet-shelf-grid').children}
ctx.renderBouquetPage();
if(get('#bouquetPageContent').children.some((x)=>x.className==='bouquet-shelf-grid'))throw Error('encyclopedia remains under inventory');
ctx.renderBouquetEncyclopedia(get('#bouquetPageContent'));
let grid=cards();
for(const [id,name] of [['warm_sun','\u6696\u9633'],['purple_mist','\u7d2b\u96fe'],['little_garden','\u5c0f\u82b1\u56ed']]){
 const card=grid.find((item)=>item.children.some((child)=>child.textContent===name));
 if(!card||!card.className.includes('historical'))throw Error(`missing historical card ${id}`);
 const image=card.children[1].children[0];if(image.src!==`/static/assets/v5/bouquets/${id}.png`)throw Error(`wrong image ${id}`);
 card.listeners.click();
 const body=get('#modalBody');const text=JSON.stringify(body.children.map((node)=>({text:node.textContent,children:node.children?.map((child)=>child.textContent)})));
 if(!text.includes(name)||!text.includes('\u7d2f\u8ba1\u6536\u5230 \u00d7')||!text.includes('\u5411\u65e5\u8475')&&!text.includes('\u85b0\u8863\u8349')&&!text.includes('\u96cf\u83ca'))throw Error(`details incomplete ${id}`);
 if(id==='warm_sun'&&(!text.includes('\u6696\u6696\u7684\u9633\u5149\u9001\u7ed9\u4f60')||!text.includes('time-300')||!text.includes('time-200')))throw Error('warm sun history missing card/time');
 if(id==='purple_mist'&&!text.includes('\u7d2b\u8272\u7684\u82b1'))throw Error('purple mist message missing');
 if(id==='little_garden'&&!text.includes('\u4e00\u5ea7\u5c0f\u82b1\u56ed'))throw Error('little garden message missing');
}
if(grid.filter((card)=>card.className.includes('historical')).length!==3)throw Error('historical count incorrect');
if(madeCommands.some((command)=>/warm_sun|purple_mist|little_garden/.test(command)))throw Error('historical bouquet entered make commands');
ctx.currentState.bouquet_gifts=[];get('#bouquetPageContent').innerHTML='';ctx.renderBouquetEncyclopedia(get('#bouquetPageContent'));grid=cards();
if(grid.some((card)=>card.className.includes('historical')))throw Error('history shown without matching gifts');
if(grid.length!==12)throw Error(`formal catalog changed: ${grid.length}`);
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_new_flower_assets_higan_artwork_and_vase_missing_image_fallbacks():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
const ctx={CUSTOM_ASSETS:{},encodeURIComponent,document:{createElement(tag){return element(tag)}},
 FLOWER_EMOJI:{rose:'\u{1F339}'},formatDuration:()=>'',catalog:{vase_capacity:2},
 currentState:{inventory:{flowers:{}},vase:{capacity:2,flowers:[
  {position:1,flower:'future_flower',flower_name:'\u672a\u77e5\u82b1',freshness_label:'\u65b0\u9c9c',remaining_seconds:0},
  {position:2,flower:'rose',flower_name:'\u73ab\u7470',freshness_label:'\u65b0\u9c9c',remaining_seconds:0}
 ]}},makeButton(){return element('button')}};
function element(tag){const node={tag,className:'',textContent:'',children:[],style:{},dataset:{},listeners:{},append(...items){this.children.push(...items)},
 addEventListener(name,fn){this.listeners[name]=fn},replaceChildren(...items){this.children=items},setAttribute(){}};
 Object.defineProperty(node,'innerHTML',{get(){return this._html||''},set(value){this._html=value;this.children=[]}});return node}
const nodes={};ctx.$=(selector)=>nodes[selector]||(nodes[selector]=element('root'));
vm.createContext(ctx);
const assignStart=source.indexOf('Object.assign(CUSTOM_ASSETS, {');
const assignEnd=source.indexOf('\n});',assignStart)+4;
vm.runInContext(source.slice(assignStart,assignEnd),ctx);
const flowers=['baby_breath','carnation','lisianthus','camellia','red_spider_lily'];
for(const id of flowers)if(ctx.CUSTOM_ASSETS[id]!==`static/assets/v5/flowers/${id}.png`)throw Error(`flower asset missing: ${id}`);
for(const id of flowers)if(ctx.CUSTOM_ASSETS[`${id}_seed`]!==`static/assets/v5/seeds/${id}_seed.png`)throw Error(`seed asset missing: ${id}`);
let start=source.indexOf('function getBouquetImageUrl('),end=source.indexOf('\n}',start)+2;
vm.runInContext(source.slice(start,end),ctx);
if(ctx.getBouquetImageUrl('higan_poem')!=='/static/assets/v5/bouquets/other_shore_poem.png')throw Error('higan artwork path mismatch');
if(ctx.getBouquetImageUrl('first_meeting')!=='/static/assets/v5/bouquets/first_meeting.png')throw Error('standard bouquet path changed');
start=source.indexOf('function showVaseFlowerFallback(');end=source.indexOf('\n}',start)+2;
vm.runInContext(source.slice(start,end),ctx);
start=source.indexOf('function renderVase(');end=source.indexOf('\n}',start)+2;
vm.runInContext(source.slice(start,end),ctx);
ctx.renderVase();
const slots=ctx.$('#vaseGrid').children;
const missingStage=slots[0].children[0];
if(missingStage.children.length!==1||missingStage.children[0].textContent!=='\u{1F338}')throw Error('missing asset fallback absent');
const failedStage=slots[1].children[0],image=failedStage.children[0];
image.onerror();
if(failedStage.children.length!==1||failedStage.children[0].textContent!=='\u{1F339}')throw Error('image error fallback absent');
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_unlocked_bouquet_card_opens_existing_detail_modal():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    page_start = js.index("function renderBouquetEncyclopedia")
    page_end = js.index("function renderBouquetPage", page_start)
    page_js = js[page_start:page_end]
    detail_start = js.index("function showBouquetDetails")
    detail_end = js.index("function renderBouquetPage", detail_start)
    detail_js = js[detail_start:detail_end]

    assert 'card.addEventListener("click", () => showBouquetDetails(bouquetId, true))' in page_js
    assert "else card.disabled = true;" in page_js
    assert '$("#modal").classList.remove("hidden");' in detail_js
    assert detail_js.index("body.append(history);") < detail_js.index(
        '$("#modal").classList.remove("hidden");'
    )
    assert '$("#modalClose").addEventListener("click", closeModal);' in js


def test_garden_notice_does_not_promote_old_history_to_notification():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert "function extractGardenNotice(message)" in js
    notice = js.split("function renderGardenNotice()", 1)[1].split("function ensureOfflineSummaryBar()", 1)[0]
    assert "recent_events" not in notice
    assert "let notice = latestNotice;" in notice


def test_first_collectible_notice_renders_for_status_and_auxiliary_requests():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
const nodes={};
const context={
  $:selector=>nodes[selector]||(nodes[selector]={textContent:''}),
  document:{visibilityState:'visible'},
  currentState:{}, latestLocationNotices:{garden:'',flower_shop:'',cottage:''}, gardenNeedsResume:true,
  updateLiveCountdowns(){}, maybeAutoShowUpdateAnnouncement(){},
  renderBouquetMainButton(){}, renderNotesButton(){},
  fetch:async()=>({ok:true,json:async()=>context.responseData})
};
vm.createContext(context);
for(const [start,end] of [
  ['async function requestJson(', '\nfunction authHeaders('],
  ['function updateFromResponse(', '\nfunction renderNotesButton('],
  ['function extractGardenNotice(', '\nfunction ensureOfflineSummaryBar(']
]) vm.runInContext(source.slice(source.indexOf(start),source.indexOf(end,source.indexOf(start))),context);
context.renderAll=()=>context.renderGardenNotice();
const notice='🎁 发现新藏品：圆润的小石子';
(async()=>{
  context.updateFromResponse({message:notice,state:{new_events:[{text:notice}],offline_summary:{},garden_events:{}}},true);
  if(context.$('#gardenNoticeText').textContent.includes(notice))throw Error('unclassified notice guessed');
  context.responseData={ok:true,message:notice,notes:[]};
  await context.requestJson('/web/notes?session_id=test');
  if(context.$('#messageBox').textContent!==notice||context.$('#gardenNoticeText').textContent.includes(notice))throw Error('notes notice misclassified');
  context.responseData={ok:true,message:notice,state:{}};
  await context.requestJson('/web/bouquets/read');
  if(context.$('#messageBox').textContent!==notice)throw Error('bouquet-read notice missing');
  console.log('ok');
})().catch(error=>{console.error(error);process.exitCode=1});
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_flower_shop_tabs_and_nine_shelves_follow_public_state():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
function element(tag){const n={tag,className:'',textContent:'',children:[],listeners:{},style:{},
 append(...items){this.children.push(...items)},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(){}};
 Object.defineProperty(n,'innerHTML',{set(){this.children=[]}});return n}
const nodes={};const commands=[];const executed=[];
const formalIds=['first_meeting','morning_light','sunny_field','heart_note','evening_breeze','soft_cloud','blue_letter','cherry_branch','spring_banquet','spring_mountain','moonlit_book','higan_poem'];
const pricing_profiles={normal:[{until_seconds:14400,multiplier:1.15},{until_seconds:86400,multiplier:0.65}],freshener:[{until_seconds:21600,multiplier:1.15},{until_seconds:86400,multiplier:0.65}]};
const ctx={document:{createElement:element},$:(s)=>nodes[s]||(nodes[s]=element('root')),
catalog:{flowers:{daisy:{name:'雏菊'}},bouquets:Object.fromEntries(formalIds.map(id=>[id,{name:id,components:{daisy:1},base_price:30}]))},bouquetVisitNewGiftIndexes:new Set(),bouquetWorkshopTab:'shelf',
 CUSTOM_ASSETS:{pebble:'pebble-image',gray_feather:'feather-image',maple_leaf:'leaf-image'},elapsed:0,getSnapshotElapsedSeconds(){return ctx.elapsed},
 runCommand(command){executed.push(command)},
 formatDuration:()=> '2小时',makeButton(label,command,cls,disabled){const b=element('button');b.textContent=label;b.command=command;b.disabled=disabled;commands.push(b);return b},
 currentState:{money:10000,bouquet_gifts:[],bouquet_options:[{bouquet_id:'first_meeting',name:'初见',components:{daisy:1},can_make:true}],
 bouquet_inventory:[{id:'one',bouquet_id:'first_meeting',name:'初见',components:{daisy:1}}],flower_shop:{eligible:true,established:true,launched:true,is_open:true,empty_slots:2,shelf_capacity:3,freshener_cost:1800,pricing_profiles,bouquet_lifetime_seconds:86400,eligibility_progress:{encyclopedia:17,harvests:340,direct_flower_sale_earned:3000},
 slots:[{slot:1,empty:false,bouquet_id:'higan_poem',name:'彼岸诗',base_price:100,current_price:123,price_stage:'新鲜',expires_in_seconds:100,is_open:true},{slot:2,empty:true},{slot:3,empty:true}]}}};
vm.createContext(ctx);
const start=source.indexOf('function getBouquetImageUrl('),end=source.indexOf('async function markBouquetGiftsRead(',start);
vm.runInContext(source.slice(start,end),ctx);
const body=ctx.$('#bouquetPageContent');
const walk=(node)=>[node,...node.children.flatMap(walk)];
const find=(cls)=>walk(body).find(n=>n.className===cls);
ctx.renderBouquetPage();
if(!find('flower-shop-buff')||!walk(find('flower-shop-buff')).some(n=>n.src==='/static/assets/v5/flower_shop/cat_buff_tray.png')||!walk(find('flower-shop-buff')).some(n=>n.textContent==='外出回来时，它偶尔会给花店带点什么。'))throw Error('empty tray missing');
if(!walk(find('flower-shop-buff')).some(n=>n.textContent==='猫咪的小惊喜'))throw Error('surprise title');
ctx.currentState.cat={name:'栗子'};ctx.renderBouquetPage();
if(!walk(find('flower-shop-buff')).some(n=>n.textContent==='外出回来时，它偶尔会给花店带点什么。'))throw Error('idle hint should stay lightweight');
ctx.currentState.cat=null;ctx.renderBouquetPage();
const pageTabs=find('bouquet-collection-tabs bouquet-page-tabs');
if(!pageTabs||pageTabs.children.map(b=>b.textContent).join('/')!=='花束/赠礼')throw Error('shop-level tabs');
let tabs=find('bouquet-collection-tabs bouquet-workshop-tabs');
if(tabs.children.map(b=>b.textContent).join('/')!=='货架/制作'||!tabs.children[0].className.includes('active'))throw Error('default tabs');
if(walk(body).some(n=>n.textContent.includes('解锁条件')))throw Error('eligibility persists after unlock');
if(walk(body).filter(n=>n.tag==='h3').map(n=>n.textContent).join('/')!=='售卖货架')throw Error('shelf title hierarchy');
let shelves=find('flower-shop-shelves');
const display=find('flower-shop-display');
if(!display||display.children[0]!==shelves||display.children[1].className!=='flower-shop-buff')throw Error('shelf should precede the surprise corner in narrow-screen flow');
if(shelves.children.length!==9||shelves.children.filter(n=>n.className==='locked').length!==6)throw Error('capacity');
if(!walk(shelves.children[1]).some(n=>n.textContent==='暂无上架')||walk(shelves.children[1]).some(n=>n.tag==='img'))throw Error('empty slot');
const first=walk(shelves.children[0]);
if(!first.some(n=>n.src==='/static/assets/v5/bouquets/other_shore_poem.png')||!first.some(n=>n.textContent==='彼岸诗 ×1')||!first.some(n=>n.textContent.includes('基础价 100 → 当前售价 123')))throw Error('listed slot price relationship');
if(!walk(body).some(n=>n.textContent==='保鲜设备：未安装')||!walk(body).some(n=>n.textContent.includes('相对基础售价：0–4小时 ×1.15'))||!walk(body).some(n=>n.textContent.includes('上架满24小时后报废')))throw Error('ordinary shelf pricing explanation');
ctx.currentState.collectible_catalog=[{id:'pebble',name:'小石子',display_name:'小石子'},{id:'gray_feather',name:'羽毛'},{id:'maple_leaf',name:'枫叶'}];
Object.assign(ctx.currentState.flower_shop,{shop_buff_active:true,shop_buff_collectible_id:'pebble',shop_buff_effect:'成交金额 +10%',shop_buff_remaining_seconds:7200});
ctx.renderBouquetPage();
let buff=find('flower-shop-buff');
if(!buff||!walk(buff).some(n=>n.src===ctx.CUSTOM_ASSETS.pebble&&n.alt==='小石子')||!walk(buff).some(n=>n.textContent==='小石子')||!walk(buff).some(n=>n.textContent==='猫咪把它放在了花店柜台上。')||!walk(buff).some(n=>n.textContent==='成交金额 +10%｜剩余 2小时'))throw Error('real buff collectible missing');
ctx.currentState.cat={name:'麻薯'};ctx.renderBouquetPage();buff=find('flower-shop-buff');if(!walk(buff).some(n=>n.textContent==='麻薯把它放在了花店柜台上。'))throw Error('named cat should appear in the active buff note');ctx.currentState.cat=null;
for(const id of ['gray_feather','maple_leaf']){ctx.currentState.flower_shop.shop_buff_collectible_id=id;ctx.renderBouquetPage();buff=find('flower-shop-buff');if(!walk(buff).some(n=>n.className==='flower-shop-buff-image'&&n.src===ctx.CUSTOM_ASSETS[id]))throw Error('collectible overlay '+id)}
ctx.currentState.flower_shop.shop_buff_collectible_id=null;ctx.renderBouquetPage();buff=find('flower-shop-buff');
if(!buff||!walk(buff).some(n=>n.textContent==='🐾 猫咪好运')||walk(buff).some(n=>n.className==='flower-shop-buff-image'))throw Error('legacy buff fallback');
ctx.currentState.flower_shop.shop_buff_collectible_id='pebble';ctx.elapsed=7200;ctx.renderBouquetPage();
buff=find('flower-shop-buff');if(!buff||walk(buff).some(n=>n.className==='flower-shop-buff-image')||!walk(buff).some(n=>n.textContent==='外出回来时，它偶尔会给花店带点什么。'&&!n.hidden))throw Error('expired buff must leave empty tray');
ctx.elapsed=0;ctx.currentState.flower_shop.shop_buff_active=false;ctx.renderBouquetPage();
if(!commands.some(b=>b.command==='buy_flower_shop_freshener'&&b.textContent==='安装 · 1800'))throw Error('freshener purchase entry missing');
const freshenerButtonsBefore=commands.filter(b=>b.command==='buy_flower_shop_freshener').length;
ctx.currentState.flower_shop.has_freshener=true;ctx.currentState.flower_shop.freshener_cost=null;ctx.renderBouquetPage();
let ruleNodes=walk(body);
if(!ruleNodes.some(n=>n.textContent==='保鲜设备：已启用')||!ruleNodes.some(n=>n.textContent.includes('相对基础售价：0–6小时 ×1.15'))||!ruleNodes.some(n=>n.textContent==='延后花束折价节点；24小时报废时间不变。仅对安装后新上架的花束生效。'))throw Error('freshener pricing explanation');
if(walk(body).some(n=>n.textContent.includes('售价阶段暂不可用')))throw Error('pricing stages unexpectedly unavailable');
if(!ruleNodes.some(n=>n.textContent.includes('24小时报废时间不变')))throw Error('freshener lifetime explanation');
if(commands.filter(b=>b.command==='buy_flower_shop_freshener').length!==freshenerButtonsBefore)throw Error('installed freshener still offers purchase');
ctx.currentState.flower_shop.pricing_profiles.freshener=[{until_seconds:7200,multiplier:1.23},{until_seconds:108000,multiplier:0.77}];ctx.currentState.flower_shop.bouquet_lifetime_seconds=108000;ctx.renderBouquetPage();
ruleNodes=walk(body);
if(!ruleNodes.some(n=>n.textContent.includes('0–2小时 ×1.23｜2–30小时 ×0.77'))||!ruleNodes.some(n=>n.textContent.includes('上架满30小时后报废'))||!ruleNodes.some(n=>n.textContent.includes('30小时报废时间不变')))throw Error('rules not derived from public data');
ctx.currentState.flower_shop.has_freshener=false;ctx.currentState.flower_shop.freshener_cost=1800;
tabs.children[1].listeners.click();
if(!commands.some(b=>b.command==='craft_bouquet bouquet_id=first_meeting'))throw Error('craft missing');
if(walk(body).filter(n=>n.tag==='h3').map(n=>n.textContent).join('/')!=='制作花束')throw Error('craft title hierarchy');
const craftGrid=find('cat-collection-grid bouquet-craft-grid');
if(!craftGrid||craftGrid.children.length!==12)throw Error('formal craft cards missing');
const firstCard=walk(craftGrid.children[0]);
if(!firstCard.some(n=>n.src==='/static/assets/v5/bouquets/first_meeting.png')||!firstCard.some(n=>n.textContent==='库存 ×1')||!firstCard.some(n=>n.textContent.includes('配方：'))||!firstCard.some(n=>n.textContent==='基础售价：30 块'))throw Error('craft card incomplete');
if(!walk(craftGrid.children[1]).some(n=>n.textContent==='上架'&&n.disabled))throw Error('empty stock can list');
if(!walk(craftGrid.children[1]).some(n=>n.textContent==='制作'&&n.disabled))throw Error('undiscovered recipe can be crafted');
const list=commands.find(b=>b.command==='list_bouquet instance_id=one');
if(!list||list.disabled||commands.some(b=>b.command==='gift_bouquet instance_id=one'))throw Error('craft actions');
ctx.currentState.bouquet_inventory.push({id:'two',bouquet_id:'first_meeting',name:'初见',components:{daisy:2}});ctx.renderBouquetPage();
const multi=walk(find('cat-collection-grid bouquet-craft-grid').children[0]);
const selection=multi.find(n=>n.tag==='select');selection.value='two';
multi.find(n=>n.textContent==='上架').listeners.click();
if(executed.at(-1)!=='list_bouquet instance_id=two'||!multi.some(n=>n.textContent==='库存 ×2'))throw Error('instance selection or count');
ctx.currentState.bouquet_inventory.pop();
ctx.currentState.flower_shop.empty_slots=0;ctx.renderBouquetPage();
if(!commands.filter(b=>b.command==='list_bouquet instance_id=one').at(-1).disabled)throw Error('full shelf');
ctx.renderBouquetPage('cards');
if(find('bouquet-collection-tabs bouquet-workshop-tabs'))throw Error('cards changed');
if(!commands.some(b=>b.command==='gift_bouquet instance_id=one'))throw Error('card gifting entry missing');
if(!walk(body).some(n=>n.className==='bouquet-card-list')&&!walk(body).some(n=>n.className==='bouquet-empty'))throw Error('existing cards content missing');
ctx.currentState.flower_shop={eligible:false,established:false,shelf_capacity:0,slots:[],eligibility_progress:{encyclopedia:8,harvests:20,direct_flower_sale_earned:1000}};ctx.bouquetWorkshopTab='shelf';ctx.renderBouquetPage();
shelves=find('flower-shop-shelves');if(shelves.children.length!==9||shelves.children.some(n=>n.className!=='locked'))throw Error('unbuilt shop');
if(!walk(body).some(n=>n.textContent==='解锁条件：图鉴 8/10｜收获 20/42｜直接卖花 1000/3000'))throw Error('eligibility missing before unlock');
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_existing_encyclopedia_modal_switches_between_flowers_and_bouquets():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
function element(tag){const n={tag,className:'',textContent:'',children:[],listeners:{},attrs:{},
 classList:{add(){},remove(){}},append(...items){this.children.push(...items)},addEventListener(name,fn){this.listeners[name]=fn},setAttribute(k,v){this.attrs[k]=v}};
 Object.defineProperty(n,'innerHTML',{set(){this.children=[]}});return n}
const nodes={};const $=(s)=>nodes[s]||(nodes[s]=element('root'));
const flowers=Object.fromEntries(Array.from({length:17},(_,i)=>[`flower_${i}`,{name:`花${i}`,rarity_name:'普通'}]));
const bouquets=Object.fromEntries(['first_meeting','morning_light','sunny_field','heart_note','evening_breeze','soft_cloud','blue_letter','cherry_branch','spring_banquet','spring_mountain','moonlit_book','higan_poem'].map((id)=>[id,{name:id,components:{flower_0:1}}]));
const ctx={document:{createElement:element},$,encodeURIComponent,catalog:{flowers,bouquets},currentState:{encyclopedia:Object.keys(flowers),encyclopedia_count:17,flower_harvest_counts:{},bouquet_options:[{bouquet_id:'first_meeting',components:{flower_0:1},can_make:true}],bouquet_gifts:[]},
 bouquetVisitNewGiftIndexes:new Set(),getSortedCatalogFlowers:(items)=>Object.entries(items).map(([id,flower])=>({id,flower})),
 setFlowerIcon(el,id){el.textContent=id},setAssetIcon(el){el.textContent='?';return true},flowerComponentText:()=>'',
 createBouquetNewBadge:()=>element('badge'),showBouquetDetails(){},resetModalPresentation(){}};
vm.createContext(ctx);
for(const [start,end] of [['function getBouquetImageUrl(','function renderBouquetArtwork('],['function renderBouquetArtwork(','function renderBouquetTabs('],['function renderBouquetEncyclopedia(','function renderBouquetPage('],['function showEncyclopediaModal(','function renderEvents(']]){
 const a=source.indexOf(start),b=source.indexOf(end,a);vm.runInContext(source.slice(a,b),ctx);
}
ctx.showEncyclopediaModal();
let body=$('#modalBody'),tabs=body.children[0];
if($('#modalTitle').textContent!=='图鉴')throw Error('generic encyclopedia title');
if(tabs.children.map(x=>x.textContent).join('/')!=='花卉 17/17/花束 1/12'||!tabs.children[0].className.includes('active'))throw Error('discovery progress tabs');
if(body.children[1].className!=='encyclopedia-grid'||body.children[1].children.length!==17)throw Error('flower encyclopedia changed');
tabs.children[1].listeners.click();body=$('#modalBody');
if(!body.children[0].children[1].className.includes('active'))throw Error('bouquet tab not active');
const grid=body.children.find(x=>x.className==='bouquet-shelf-grid');
if(!grid||grid.children.length!==12)throw Error('formal bouquet grid missing');
const path=grid.children[0].children.find(x=>x.className==='bouquet-card-artwork').children[0].src;
if(path!=='/static/assets/v5/bouquets/first_meeting.png')throw Error('formal artwork path changed');
console.log('ok');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


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
    assert catalog.json["bouquets"]["first_meeting"]["base_price"] == game_api.get_flower_shop_base_price(
        catalog.json["bouquets"]["first_meeting"]["components"]
    )
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
    state["cat_state"].update(phase="stayed_waiting_name", location="garden")
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


def test_adopted_cat_hint_matches_home_or_away_location():
    root = Path(__file__).resolve().parents[1]
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    active_renderer = js.rsplit("function renderCatHouseV5() {", 1)[1]
    hint_logic = active_renderer.split("portrait.append(hint);", 1)[0].rsplit("const hint = document.createElement(\"p\");", 1)[1]

    assert '`位置 · ${CAT_LOCATION_LABELS[location] || "未知"}`' in active_renderer
    assert 'else if (isAdopted && location === "home")' in hint_logic
    assert 'hint.textContent = "猫咪已经在家安顿下来，可以慢慢照料它。";' in hint_logic
    assert 'else if (isAdopted && location === "away")' in hint_logic
    assert 'hint.textContent = "猫咪现在正在外出，回来后可以继续照料。";' in hint_logic
    assert 'if (isAdopted) {' not in hint_logic


def test_v485_ui_assets_and_labels():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")
    assert 'id="backpackBtn"' in html
    assert "· ×1.1" not in html
    assert '"cat": "data:image/png;base64,' in js
    assert 'lavender: "static/assets/v5/flowers/lavender.png"' in js
    assert ".mini-btn:disabled" in css
    assert (root / "static" / "assets" / "v5" / "flowers" / "lavender.png").exists()


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
    assert "只增加容量，不改变喝水效果" in js
    assert "降低心情自然下降速度" in js
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in css
    assert ".shop-square-card" in css
    assert ".vase-grid.real-vase" in css


def test_v4811_live_timers_encyclopedia_shortcut_and_lily_asset():
    root = Path(__file__).resolve().parents[1]
    html = (root / "templates" / "index.html").read_text(encoding="utf-8")
    js = (root / "static" / "app.js").read_text(encoding="utf-8")
    css = (root / "static" / "style.css").read_text(encoding="utf-8")

    assert 'id="encyclopediaCard"' in html
    assert 'lily: "static/assets/v5/flowers/lily.png"' in js
    assert 'lily: "🌺"' in js
    assert (root / "static" / "assets" / "v5" / "flowers" / "lily.png").exists()
    assert "REAL_SECONDS_PER_DAY" in js
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
    assert ".flower-shop-facilities" in css
    assert "shop.shop_buff_active" in js
    assert "猫咪好运" in js
    assert "shop.shop_buff_effect" in js
    assert "12%" not in js
    assert ".flower-shop-buff" in css


def test_shop_buff_live_countdown_hides_at_expiry():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
const box={hidden:false}, item={hidden:false}, empty={hidden:true}, text={textContent:''};
const ctx={elapsed:1,currentState:{pots:[],vase:{flowers:[]},flower_shop:{shop_buff_active:true,shop_buff_remaining_seconds:2,shop_buff_effect:'成交金额 +10%'}},
 document:{visibilityState:'visible',querySelector:s=>s==='[data-live-shop-buff]'?box:s==='[data-live-shop-buff-text]'?text:s==='[data-live-shop-buff-item]'?item:s==='[data-live-shop-buff-empty]'?empty:null},
 getSnapshotElapsedSeconds(){return ctx.elapsed},updateLiveGameTime(){},formatDuration:seconds=>`${seconds}秒`,queueLiveRefresh(){}};
vm.createContext(ctx);
const start=source.indexOf('function updateLiveCountdowns('),end=source.indexOf('\nfunction showToast(',start);
vm.runInContext(source.slice(start,end),ctx);
ctx.updateLiveCountdowns();
if(box.hidden||text.textContent!=='成交金额 +10%｜剩余 1秒')throw Error('live countdown');
ctx.elapsed=2;ctx.updateLiveCountdowns();
if(!box.hidden||!item.hidden||empty.hidden)throw Error('expired collectible remains visible or empty tray hint missing');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
