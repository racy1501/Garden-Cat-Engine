"""The AI sees a bounded projection of the same shared garden events."""
from urllib.parse import quote

import game_engine as ge
from copy import deepcopy
from test_api_response_shape import api, cat_clock, create_human_garden


def test_shared_activity_tracks_web_actions_across_locations(api, cat_clock):
    module, client = api
    sid, web_headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state['money'] = 10000
    state['cat_state']['next_visit_at'] = cat_clock[0] + 3600
    state['flower_shop'] = {**ge._default_flower_shop_state(), 'established_at': cat_clock[0] - 1,
                            'shelf_capacity': 3, 'slots': [None] * 3}
    state['events'] = []
    module.db_save_state(sid, state)
    web_headers['X-Garden-Human-Name'] = quote('阿屿')
    ai_headers = {'X-API-Key': 'test-key'}
    for command, area, text in [
        ('plant daisy 1', 'garden', '种下了雏菊'),
        ('buy_flower_shop_freshener', 'flower_shop', '保鲜设备'),
        ('buy_cottage_furniture floor_lamp', 'cottage', '落地灯'),
    ]:
        response = client.post('/web/cmd', headers=web_headers, json={'session_id': sid, 'command': command})
        assert response.get_json()['ok'] is True
        summary = client.get('/api/status', headers=ai_headers, query_string={'session_id': sid}).get_json()['state']
        event = next(event for event in summary['shared_activity'] if text in event['text'])
        assert event['area'] == area
        assert (event['source'], event['source_name'], event['source_label']) == ('human', '阿屿', '人类')
        assert summary['recent_events'] == [] and summary['latest_event'] == ''


def test_shared_activity_includes_real_sources_and_is_limited_in_compact_and_batch(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['events'] = []
    state['cat_state']['next_visit_at'] = cat_clock[0] + 3600
    for index in range(6):
        ge.add_event(state, f'旧事件{index}', now=cat_clock[0] - 10 + index, source='system', area='cottage')
    module.db_save_state(sid, state)
    headers = {'X-API-Key': 'test-key', 'X-Garden-Owner-Name': quote('砚川')}
    command = client.post('/api/cmd?compact=1', headers=headers,
                          json={'session_id': sid, 'command': 'plant daisy 1'}).get_json()['state']
    assert command['recent_events'][-1]['source'] == 'ai'
    assert command['latest_event'] == command['recent_events'][-1]['text']
    assert command['shared_activity'][-1]['source_name'] == '砚川'
    assert len(command['shared_activity']) == 5
    assert all(set(event) <= {'source', 'source_name', 'source_label', 'area', 'text', 'time'}
               for event in command['shared_activity'])
    assert not {'events', 'recent_event_records', 'new_events'} & command.keys()

    state = module.db_load_state(sid)
    ge.add_event(state, '系统活动', now=cat_clock[0] + 1, source='system', area='flower_shop')
    module.db_save_state(sid, state)
    status = client.get('/api/status', headers=headers, query_string={'session_id': sid}).get_json()['state']
    assert len(status['shared_activity']) == 5
    assert any(e['source'] == 'ai' and e['source_name'] == '砚川' for e in status['shared_activity'])
    assert status['shared_activity'][-1] == {'source': 'system', 'source_label': '系统',
                                           'area': 'flower_shop', 'text': '系统活动', 'time': cat_clock[0] + 1}
    assert status['recent_events'] == [] and status['latest_event'] == ''
    again = client.get('/api/status', headers=headers, query_string={'session_id': sid}).get_json()['state']
    assert again['shared_activity'] == status['shared_activity']
    batch = client.post('/api/cmd/batch?compact=1', headers=headers,
                        json={'session_id': sid, 'commands': ['plant daisy 2']}).get_json()
    assert batch['ok'] is True and len(batch['state']['shared_activity']) <= 5
    assert any(e['text'] == '在盆2种下了雏菊' for e in batch['state']['shared_activity'])


def test_shared_activity_uses_saved_snapshot_before_summary_catchup(api, cat_clock, monkeypatch):
    module, _ = api
    state = ge.get_default_state()
    state['events'] = []
    ge.add_event(state, '已保存事件', now=cat_clock[0] - 1, source='human', area='garden')

    def late_catchup(state, now, **kwargs):
        ge.add_event(state, '摘要补算事件', now=now, source='system', area='garden')
        return True

    monkeypatch.setattr(module, 'apply_offline_progress', late_catchup)
    with module.app.test_request_context():
        summary = module._ai_summary(deepcopy(state))
    assert [event['text'] for event in summary['shared_activity']] == ['已保存事件']
    assert summary['recent_events'] == [] and summary['latest_event'] == ''
