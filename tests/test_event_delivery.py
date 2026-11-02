"""事件仍使用原日志：恢复读取历史，操作/在线请求读取新消息。"""
import json
import subprocess
from pathlib import Path

import pytest

from test_api_response_shape import api, cat_clock, adopted_cat_state, create_human_garden
import game_engine as ge


@pytest.mark.parametrize("mode", ["api", "web"])
@pytest.mark.parametrize("hours", [6, 80])
def test_first_restore_keeps_history_without_live_messages(api, cat_clock, mode, hours):
    module, client = api
    sid, web_headers = create_human_garden(client)
    state = adopted_cat_state()
    token_hash = module.db_load_state(sid)[module.WEB_TOKEN_FIELD]
    state[module.WEB_TOKEN_FIELD] = token_hash
    module.db_save_state(sid, state)
    start = cat_clock[0]
    cat_clock[0] += hours * 3600
    headers = web_headers if mode == "web" else {"X-API-Key": "test-key", "X-Garden-Live": "1"}
    response = client.get(f"/{mode}/status?session_id={sid}", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    if mode == "web":
        assert "栗子出门" not in payload["message"] and "栗子回家" not in payload["message"]
    else:
        assert "栗子回家" in payload["message"]
        if hours > 72:
            assert "72小时" in payload["message"]
    saved = module.db_load_state(sid)
    assert saved["cat_state"]["location"] == "home"
    assert all(event["time"] <= start + min(hours, 72) * 3600 for event in saved["events"])
    if mode == "api":
        assert payload["state"]["latest_event"] == ""
    else:
        assert payload["state"]["new_events"] == []
        records = payload["state"]["recent_event_records"]
        assert records == sorted(
            [module._event_record_for_client(event) for event in saved["events"]],
            key=lambda event: event["time"],
        )
        assert 0 < len(records) <= 50
        assert payload["state"]["recent_events"] == [event["text"] for event in saved["events"]]
    repeated = client.get(f"/{mode}/status?session_id={sid}", headers=headers).get_json()["state"]
    assert repeated.get("latest_event", "") == ""
    assert repeated.get("new_events", []) == []


def test_online_poll_delivers_once_and_resume_suppresses_history(api, cat_clock):
    module, client = api
    sid, headers = create_human_garden(client)
    state = adopted_cat_state()
    state[module.WEB_TOKEN_FIELD] = module.db_load_state(sid)[module.WEB_TOKEN_FIELD]
    module.db_save_state(sid, state)
    url = f"/web/status?session_id={sid}"
    assert client.get(url, headers=headers).get_json()["state"]["new_events"] == []
    cat_clock[0] = state["cat_state"]["next_outing_at"]
    live = {**headers, "X-Garden-Live": "1"}
    payload = client.get(url, headers=live).get_json()["state"]
    assert payload["new_events"] == [{
        "time": cat_clock[0],
        "text": "栗子出门溜达了一会儿。",
        "source": "system",
        "source_label": "系统",
    }]
    assert client.get(url, headers=live).get_json()["state"]["new_events"] == []
    cat_clock[0] += 6 * 3600
    resumed = client.get(url, headers=headers).get_json()["state"]
    assert resumed["new_events"] == []
    assert resumed["recent_event_records"]


def test_ai_operation_keeps_catchup_hint_separate_from_request_events(api, cat_clock):
    module, client = api
    state = adopted_cat_state()
    state["inventory"]["flowers"]["rose"] = 1
    module.db_save_state("operation", state)
    cat_clock[0] += 6 * 3600
    payload = client.post("/api/cmd", headers={"X-API-Key": "test-key"},
                          json={"session_id": "operation", "command": "arrange rose"}).get_json()
    assert payload["state"]["latest_event"] == "把玫瑰插进花瓶"
    assert "栗子回家" in payload["message"]
    assert [event["text"] for event in payload["state"]["recent_events"]] == ["把玫瑰插进花瓶"]
    assert module._ai_summary(module.db_load_state("operation"))["latest_event"] == ""


def test_standalone_ai_summary_does_not_announce_offline_events(api, cat_clock):
    module, _ = api
    state = adopted_cat_state()
    cat_clock[0] += 6 * 3600
    assert module._ai_summary(state)["latest_event"] == ""
    assert state["events"][-1]["text"] == "栗子回家了。"


def test_web_operation_still_delivers_its_own_event_on_restore(api, cat_clock):
    module, client = api
    sid, headers = create_human_garden(client)
    state = adopted_cat_state()
    state[module.WEB_TOKEN_FIELD] = module.db_load_state(sid)[module.WEB_TOKEN_FIELD]
    state["inventory"]["flowers"]["rose"] = 1
    module.db_save_state(sid, state)
    cat_clock[0] += 6 * 3600
    payload = client.post("/web/cmd", headers=headers,
                          json={"session_id": sid, "command": "arrange rose"}).get_json()["state"]
    assert payload["new_events"] == [{
        "time": cat_clock[0],
        "text": "把玫瑰插进花瓶",
        "source": "human",
        "source_label": "人类",
        "area": "garden",
    }]


def test_ai_summary_cross_second_catchup_does_not_replace_operation(api, cat_clock):
    module, _ = api
    state = adopted_cat_state()
    state["cat_state"]["next_outing_at"] = cat_clock[0] + 1
    state["inventory"]["flowers"]["rose"] = 1
    before = list(state["events"])
    ge.process_command(state, "arrange rose")
    cat_clock[0] += 2
    assert module._ai_summary(state, events_before=before)["latest_event"] == "把玫瑰插进花瓶"
    assert state["events"][-1]["text"] == "栗子出门溜达了一会儿。"


def test_frontend_quiet_notifications_and_timestamped_log():
    root = Path(__file__).resolve().parents[1]
    # 执行现有前端函数；最小DOM替身，不连接浏览器或API。
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8');
const nodes={};const get=(id)=>nodes[id]||(nodes[id]={textContent:'',innerHTML:'',children:[],append(v){this.children.push(v)}});
 const ctx={currentState:null,seenEventBoundary:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},gardenNeedsResume:true,stateSnapshotAtMs:0,liveRefreshQueued:false,
 Date,document:{visibilityState:'visible',createElement(){return {textContent:'',className:''}}},
 renderBouquetMainButton(){},renderNotesButton(){},renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
ctx['$']=get;vm.createContext(ctx);
const functions=[['function formatEventSource(', 'function renderNotesButton('],
  ['function extractGardenNotice(', 'function ensureOfflineSummaryBar('],
 ['function renderEvents(', 'function showLetterModal(']];
for(const [start,end] of functions)vm.runInContext(source.slice(source.indexOf(start),source.indexOf(end)),ctx);
const old={time:100,text:'🎁 历史藏品'};
ctx.updateFromResponse({state:{new_events:[],recent_events:[old.text],recent_event_records:[old],offline_summary:{offline_seconds:3600}},message:'历史恢复'},true);
ctx.renderGardenNotice();if(get('#gardenNoticeText').textContent.includes(old.text))throw Error('history promoted');
 const fresh={time:200,text:'栗子回家了。',area:'garden'};
ctx.updateFromResponse({state:{new_events:[fresh],recent_event_records:[old,fresh]},message:'状态'},true);
ctx.renderGardenNotice();if(!get('#messageBox').textContent.includes(fresh.text))throw Error('quiet dropped event');
if(!get('#gardenNoticeText').textContent.includes(fresh.text))throw Error('live notice missing');
ctx.updateFromResponse({state:{new_events:[],recent_event_records:[old,fresh]}},true);
 ctx.renderGardenNotice();if(!get('#gardenNoticeText').textContent.includes(fresh.text))throw Error('area notice was lost');
const sameTime={time:200,text:'同秒较新的记录'};
ctx.currentState.recent_event_records.push(sameTime);
ctx.renderEvents();const rows=get('#eventsList').children;
if(rows.length!==3||!rows[0].textContent.endsWith(sameTime.text)||rows[0].textContent===sameTime.text)throw Error('log ordering/time');
console.log(JSON.stringify({notice:get('#gardenNoticeText').textContent,rows:rows.map(x=>x.textContent)}));
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert len(json.loads(result.stdout)["rows"]) == 3


def test_frontend_diary_prefers_name_and_keeps_legacy_labels():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');const src=fs.readFileSync('static/app.js','utf8');
const root={children:[],set innerHTML(v){this.children=[]},append(v){this.children.push(v)}};
const ctx={currentState:{recent_event_records:[
 {time:1,text:'种花',source:'human',source_label:'人类',source_name:'阿屿'},
 {time:2,text:'摸猫',source:'ai',source_label:'AI',source_name:'砚川'},
 {time:3,text:'旧人类',source:'human',source_label:'人类'},
 {time:4,text:'旧AI',source:'ai',source_label:'AI'},
 {time:5,text:'系统事件',source:'system',source_label:'系统'},
 {time:6,text:'空名字',source:'ai',source_label:'AI',source_name:'  '}
]},Date,document:{createElement(){return {textContent:'',className:''}}},$:()=>root};
vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('function formatEventSource('),src.indexOf('function updateFromResponse(')),ctx);vm.runInContext(src.slice(src.indexOf('function renderEvents('),src.indexOf('function showLetterModal(')),ctx);ctx.renderEvents();
for(const [label,content] of [['阿屿','种花'],['砚川','摸猫'],['人类','旧人类'],['AI','旧AI'],['系统','系统事件'],['AI','空名字']])
 if(!root.children.some(row=>row.textContent.includes(label+' ·')&&row.textContent.includes(content)))throw Error(label+' '+content);
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


def test_notice_sources_and_temporary_garden_appearances():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm'),src=fs.readFileSync('static/app.js','utf8');
const nodes={},get=id=>nodes[id]||(nodes[id]={textContent:''}),toasts=[];
const ctx={currentState:null,seenEventBoundary:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},
 gardenNeedsResume:false,stateSnapshotAtMs:0,liveRefreshQueued:false,Date,$:get,
 document:{visibilityState:'visible'},showToast(text){toasts.push(text)},renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('function formatEventSource('),src.indexOf('function renderNotesButton(')),ctx);
function update(records, events, garden_events={}){ctx.updateFromResponse({state:{recent_event_records:records,new_events:events,garden_events}},true,true)}
update([],[]);if(toasts.length)throw Error('untriggered event');
const ai={time:1,area:'garden',text:'浇水',source:'ai',source_label:'AI'};
update([ai],[]);if(ctx.latestLocationNotices.garden!=='AI · 浇水')throw Error('AI source');
const human={time:2,area:'cottage',text:'买家具',source:'human',source_label:'人类'};
update([ai,human],[human]);if(ctx.latestLocationNotices.cottage!=='人类 · 买家具')throw Error('human source');
const named={time:3,area:'garden',text:'种花',source:'ai',source_name:'砚川',source_label:'AI'};
update([ai,human,named],[]);if(ctx.latestLocationNotices.garden!=='砚川 · 种花')throw Error('named source');
update([ai,human,named],[],{butterfly_active:true,butterfly_until:400,butterfly_reward:''});
if(toasts.length!==1||!toasts[0].includes('蝴蝶'))throw Error('ordinary butterfly absent');
update([ai,human,named],[],{butterfly_active:true,butterfly_until:400,butterfly_reward:''});
if(toasts.length!==1)throw Error('appearance repeated');
update([ai,human,named],[],{butterfly_active:true,butterfly_until:500,butterfly_reward:'获得4金币'});
if(!toasts[1].includes('蝴蝶')||!toasts[1].includes('4金币'))throw Error('butterfly reward absent');
update([ai,human,named],[],{butterfly_active:false,butterfly_until:500,rainbow_active:true,rainbow_until:600,rainbow_reward:'获得9金币'});
if(!toasts[2].includes('彩虹')||!toasts[2].includes('9金币'))throw Error('rainbow absent');
update([ai,human,named],[],{butterfly_active:false,butterfly_until:500,rainbow_active:false,rainbow_until:600});
if(toasts.length!==3)throw Error('false appearance');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('reward', [False, True])
def test_web_status_exposes_real_butterfly_without_plain_diary_event(api, cat_clock, monkeypatch, reward):
    module, client = api
    sid, headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state['weather_change_time'] = cat_clock[0] + 10000
    state['last_butterfly_at'] = cat_clock[0]
    state['last_butterfly_check'] = cat_clock[0]
    state['next_butterfly_at'] = cat_clock[0] + 10
    module.db_save_state(sid, state)
    before = client.get(f'/web/status?session_id={sid}', headers=headers).get_json()['state']
    assert not before['garden_events']['butterfly_active']
    monkeypatch.setattr(ge.random, 'random', lambda: 0.0 if reward else 1.0)
    cat_clock[0] += 10
    after = client.get(f'/web/status?session_id={sid}', headers=headers).get_json()['state']
    assert after['garden_events']['butterfly_active']
    assert after['garden_events']['butterfly_until'] > before['garden_events']['butterfly_until']
    butterfly_records = [e['text'] for e in after['recent_event_records'] if '蝴蝶' in e['text']]
    assert bool(butterfly_records) is reward
    if reward:
        assert '金币' in butterfly_records[-1]
        assert after['garden_events']['butterfly_reward']


def test_web_status_exposes_real_rainbow_and_its_reward(api, cat_clock, monkeypatch):
    module, client = api
    sid, headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state['weather'] = 'rainy'
    state['weather_change_time'] = cat_clock[0] + 10
    state['last_butterfly_at'] = cat_clock[0]
    state['last_butterfly_check'] = cat_clock[0]
    state['next_butterfly_at'] = cat_clock[0] + 10000
    module.db_save_state(sid, state)
    before = client.get(f'/web/status?session_id={sid}', headers=headers).get_json()['state']
    assert not before['garden_events']['rainbow_active']

    def choose(options):
        if options == list(ge.WEATHER.keys()):
            return 'sunny'
        return options[0]

    monkeypatch.setattr(ge.random, 'choice', choose)
    monkeypatch.setattr(ge.random, 'random', lambda: 0.0)
    cat_clock[0] += 10
    after = client.get(f'/web/status?session_id={sid}', headers=headers).get_json()['state']
    assert after['garden_events']['rainbow_active']
    assert after['garden_events']['rainbow_reward']
    assert any('彩虹出现' in e['text'] for e in after['recent_event_records'])


@pytest.mark.parametrize("command,area", [
    ("water 1", "garden"),
    ("buy_flower_shop_freshener", "flower_shop"),
    ("buy_cottage_furniture floor_lamp", "cottage"),
    ("status", None),
    ("pet", None),
])
def test_web_command_notice_area_and_action_message(api, cat_clock, monkeypatch, command, area):
    module, client = api
    sid, headers = create_human_garden(client)
    monkeypatch.setattr(ge, "get_weather_info", lambda state, now: (ge.WEATHER["sunny"], ["花店自动成交"]))
    response = client.post("/web/cmd", headers=headers, json={"session_id": sid, "command": command})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["notice_area"] == area
    assert "花店自动成交" in payload["message"]
    if area:
        assert "花店自动成交" not in payload["notice_message"]
        assert "📊" not in payload["notice_message"]
    else:
        assert payload["notice_message"] is None


def test_location_notice_delivery_and_combined_diary():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync('static/app.js','utf8'),css=fs.readFileSync('static/style.css','utf8');
const nodes={};const get=id=>nodes[id]||(nodes[id]={textContent:'',hidden:false,children:[],set innerHTML(v){this.children=[]},append(v){this.children.push(v)}});
const ctx={currentState:null,seenEventBoundary:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},gardenNeedsResume:false,stateSnapshotAtMs:0,liveRefreshQueued:false,
 Date,document:{visibilityState:'visible',createElement(){return {textContent:'',className:''}}},
 renderBouquetMainButton(){},renderNotesButton(){},renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
ctx.$=get;vm.createContext(ctx);
for(const [start,end] of [['function formatEventSource(','function renderNotesButton('],['function extractGardenNotice(','function ensureOfflineSummaryBar('],['function renderEvents(','function showLetterModal(']])
 vm.runInContext(source.slice(source.indexOf(start),source.indexOf(end)),ctx);
function update(area,msg,events=[]){ctx.updateFromResponse({notice_area:area,notice_message:msg,message:msg,state:{new_events:events,garden_events:{}}});ctx.renderGardenNotice();ctx.renderLocationNotices()}
ctx.renderLocationNotices();
if(!get('#flowerShopNoticeText').textContent||!get('#cottageNoticeText').textContent||get('#flowerShopNotice').hidden||get('#cottageNotice').hidden)throw Error('empty notices must remain visible');
update('garden','浇水');update('flower_shop','上架');update('cottage','买家具');
if(!get('#gardenNoticeText').textContent.includes('浇水')||get('#gardenNoticeText').textContent.includes('买家具'))throw Error('garden leaked');
if(get('#flowerShopNoticeText').textContent!=='上架'||get('#cottageNoticeText').textContent!=='买家具')throw Error('area messages');
update('cottage','消息不优先',[{area:'garden',text:'花园新事件'},{area:'flower_shop',text:'花店成交'},{area:'cottage',text:'小屋奖励'},{text:'无地点'}]);
if(ctx.latestLocationNotices.garden!=='花园新事件'||ctx.latestLocationNotices.flower_shop!=='花店成交'||ctx.latestLocationNotices.cottage!=='小屋奖励')throw Error('event routing');
update(null,'无地点消息',[{text:'没有归属'}]);
if(ctx.latestLocationNotices.cottage!=='小屋奖励'||ctx.latestLocationNotices.garden!=='花园新事件')throw Error('unclassified routed');
ctx.currentState.recent_event_records=Array.from({length:51},(_,i)=>({time:i+1,text:`事件${i+1}`,area:i%3===0?'garden':i%3===1?'flower_shop':'cottage'}));
ctx.currentState.recent_event_records[50]={time:51,text:'旧记录'};
ctx.renderEvents();const rows=get('#eventsList').children;
if(rows.length!==50||!rows[0].textContent.endsWith('旧记录')||rows[0].textContent.includes('[花园]'))throw Error('history order or legacy');
for(const label of ['[花园]','[花店]','[小屋]'])if(!rows.some(x=>x.textContent.includes(label)))throw Error('missing area '+label);
if(!/\.events-list\s*\{[^}]*height:\s*280px;[^}]*overflow-y:\s*auto/s.test(css))throw Error('diary scrolling');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


def test_location_notices_replace_fallbacks_with_latest_event():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm'),src=fs.readFileSync('static/app.js','utf8');
const nodes={},get=id=>nodes[id]||(nodes[id]={textContent:'',children:[],set innerHTML(v){this.children=[]},append(v){this.children.push(v)}});
const ctx={currentState:null,seenEventBoundary:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},
 gardenNeedsResume:true,stateSnapshotAtMs:0,liveRefreshQueued:false,Date,$:get,
 document:{visibilityState:'visible',createElement(){return {textContent:'',className:''}}},
 renderAll(){ctx.renderGardenNotice();ctx.renderLocationNotices()},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
vm.createContext(ctx);
for(const [a,b] of [['function formatEventSource(','function renderNotesButton('],
 ['function extractGardenNotice(','function ensureOfflineSummaryBar('],['function renderEvents(','function showLetterModal(']])
 vm.runInContext(src.slice(src.indexOf(a),src.indexOf(b)),ctx);
const old={time:1,area:'garden',text:'历史事件'},records=[old];
function refresh(offline=0){ctx.updateFromResponse({state:{recent_event_records:[...records],new_events:[],offline_summary:{offline_seconds:offline},garden_events:{has_pests:true}}},true,true)}
refresh();
if(get('#gardenNoticeText').textContent!=='花园很安静，风从花叶间穿过去。'||!get('#flowerShopNoticeText').textContent.includes('花店很安静')||!get('#cottageNoticeText').textContent.includes('小屋很安静'))throw Error('initial fallbacks');
refresh(3600);
if(get('#gardenNoticeText').textContent!=='你离开了一会儿，花园仍在安静生长。')throw Error('offline fallback');
records.push({time:2,area:'garden',text:'猫咪离开了花园。'});refresh(3600);
if(get('#gardenNoticeText').textContent!=='猫咪离开了花园。')throw Error('garden fallback not replaced');
records.push({time:3,area:'flower_shop',text:'花店成交'}, {time:4,area:'cottage',text:'小屋奖励'});refresh(3600);
if(get('#flowerShopNoticeText').textContent!=='花店成交'||get('#cottageNoticeText').textContent!=='小屋奖励')throw Error('location fallback not replaced');
records.push({time:5,area:'garden',text:'猫咪回来了。'});refresh(3600);
if(get('#gardenNoticeText').textContent!=='猫咪回来了。')throw Error('newer event not displayed');
ctx.renderEvents();const rows=get('#eventsList').children;
if(rows.length!==records.length||!rows.some(row=>row.textContent.endsWith('历史事件')))throw Error('diary history changed');
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


def test_status_refresh_delivers_only_unseen_location_events():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm'),src=fs.readFileSync('static/app.js','utf8');
const nodes={},get=id=>nodes[id]||(nodes[id]={textContent:''}),listeners={};
const ctx={credentials:{session_id:'test'},isBusy:false,currentState:null,seenEventBoundary:null,
 latestLocationNotices:{garden:'',flower_shop:'',cottage:''},gardenNeedsResume:true,stateSnapshotAtMs:0,liveRefreshQueued:false,
 document:{visibilityState:'visible',addEventListener(n,f){listeners[n]=f}},window:{addEventListener(n,f){listeners[n]=f}},
 $:get,authHeaders(){return {}},setBusy(v){ctx.isBusy=v},showToast(){},
 renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){},
 async requestJson(){return {state:{recent_event_records:ctx.records,new_events:[]}}}};
vm.createContext(ctx);
for(const [a,b] of [['async function refreshGarden(','async function runCommand('],['function formatEventSource(','function renderNotesButton('],
 ['window.addEventListener("focus"','setInterval(updateLiveCountdowns']])
 vm.runInContext(src.slice(src.indexOf(a),src.indexOf(b)),ctx);
const old={time:100,area:'garden',text:'旧花'},garden={time:100,area:'garden',text:'新花'},cottage={time:101,area:'cottage',text:'新家具'};
(async()=>{
 ctx.records=[old];await ctx.refreshGarden({quiet:true});
 if(ctx.latestLocationNotices.garden)throw Error('initial history promoted');
 ctx.records=[old,garden];listeners.focus();await new Promise(resolve=>setImmediate(resolve));
 if(ctx.latestLocationNotices.garden!=='新花')throw Error('focus missed same-second garden event');
 ctx.records=[old,garden,cottage];ctx.document.visibilityState='visible';listeners.visibilitychange();await new Promise(resolve=>setImmediate(resolve));
 if(ctx.latestLocationNotices.cottage!=='新家具'||ctx.latestLocationNotices.garden!=='新花'||ctx.latestLocationNotices.flower_shop)throw Error('area routing');
 ctx.updateFromResponse({notice_area:'garden',notice_message:'网页浇水',message:'网页浇水',state:{recent_event_records:ctx.records,new_events:[]}});
 if(ctx.latestLocationNotices.garden!=='网页浇水')throw Error('command notice missing');
 await ctx.refreshGarden({quiet:true});
 if(ctx.latestLocationNotices.garden!=='网页浇水'||ctx.latestLocationNotices.cottage!=='新家具')throw Error('event repeated');
})().catch(e=>{console.error(e);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr


def test_frontend_requests_explicitly_distinguish_resume_and_live():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');const src=fs.readFileSync('static/app.js','utf8');
const requests=[],listeners={};
const ctx={credentials:{session_id:'test'},isBusy:false,gardenNeedsResume:true,seenEventBoundary:null,
 STORAGE_KEY:'test',localStorage:{setItem(){}},
 authHeaders(){return {}},setBusy(value){ctx.isBusy=value},showToast(){},
 document:{visibilityState:'visible',addEventListener(name,fn){listeners[name]=fn}},
 window:{addEventListener(name,fn){listeners[name]=fn}},
 async requestJson(url,options){requests.push(options.headers['X-Garden-Live']);return {state:{}}},
 updateFromResponse(){ctx.gardenNeedsResume=ctx.document.visibilityState!=='visible'}};
vm.createContext(ctx);
vm.runInContext(src.slice(src.indexOf('function saveCredentials('),src.indexOf('function loadCredentials(')),ctx);
vm.runInContext(src.slice(src.indexOf('async function refreshGarden('),src.indexOf('async function runCommand(')),ctx);
vm.runInContext(src.slice(src.indexOf('window.addEventListener("focus"'),src.indexOf('setInterval(updateLiveCountdowns')),ctx);
(async()=>{await ctx.refreshGarden({quiet:true});await ctx.refreshGarden({quiet:true});
 ctx.document.visibilityState='hidden';listeners.visibilitychange();
 ctx.document.visibilityState='visible';await ctx.refreshGarden({quiet:true});
 ctx.saveCredentials({session_id:'another'});await ctx.refreshGarden({quiet:true});
 if(JSON.stringify(requests)!=='["0","1","0","0"]')throw Error('resume/live intent');
 console.log(JSON.stringify(requests));})().catch(error=>{console.error(error);process.exit(1)});
"""
    result = subprocess.run(["node", "-e", script], cwd=root, encoding="utf-8", capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ["0", "1", "0", "0"]
