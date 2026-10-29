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
    assert "栗子出门" not in payload["message"] and "栗子回家" not in payload["message"]
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


def test_ai_operation_reports_new_event_but_not_catchup(api, cat_clock):
    module, client = api
    state = adopted_cat_state()
    state["inventory"]["flowers"]["rose"] = 1
    module.db_save_state("operation", state)
    cat_clock[0] += 6 * 3600
    payload = client.post("/api/cmd", headers={"X-API-Key": "test-key"},
                          json={"session_id": "operation", "command": "arrange rose"}).get_json()
    assert payload["state"]["latest_event"] == "把玫瑰插进花瓶"
    assert "栗子出门" not in payload["message"] and "栗子回家" not in payload["message"]
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
 const ctx={currentState:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},gardenNeedsResume:true,stateSnapshotAtMs:0,liveRefreshQueued:false,
 Date,document:{visibilityState:'visible',createElement(){return {textContent:'',className:''}}},
 renderBouquetMainButton(){},renderNotesButton(){},renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
ctx['$']=get;vm.createContext(ctx);
const functions=[['function updateFromResponse(', 'function renderNotesButton('],
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
const ctx={currentState:null,latestLocationNotices:{garden:'',flower_shop:'',cottage:''},gardenNeedsResume:false,stateSnapshotAtMs:0,liveRefreshQueued:false,
 Date,document:{visibilityState:'visible',createElement(){return {textContent:'',className:''}}},
 renderBouquetMainButton(){},renderNotesButton(){},renderAll(){},updateLiveCountdowns(){},maybeAutoShowUpdateAnnouncement(){}};
ctx.$=get;vm.createContext(ctx);
for(const [start,end] of [['function updateFromResponse(','function renderNotesButton('],['function extractGardenNotice(','function ensureOfflineSummaryBar('],['function renderEvents(','function showLetterModal(']])
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


def test_frontend_requests_explicitly_distinguish_resume_and_live():
    root = Path(__file__).resolve().parents[1]
    script = r"""
const fs=require('fs'),vm=require('vm');const src=fs.readFileSync('static/app.js','utf8');
const requests=[],listeners={};
const ctx={credentials:{session_id:'test'},isBusy:false,gardenNeedsResume:true,
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
