"""Level-one status is actionable, bounded, and distinct from action responses."""
from copy import deepcopy
import json
from unittest.mock import Mock

import pytest
import game_engine as ge
from game_views import VIEW_DETAILS, build_overview
from test_api_response_shape import api, cat_clock, create_human_garden, adopted_cat_state


def status(client, sid):
    return client.get('/api/status', headers={'X-API-Key': 'test-key'}, query_string={'session_id': sid}).get_json()


def test_overview_slots_can_be_used_directly_for_actions(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    pot = {'flower_id': 'daisy', 'growth_progress': 0, 'watered': True, 'last_growth_update': cat_clock[0]}
    state['max_pots'] = 6
    state['pots'] = [None, {**pot, 'watered': False}, dict(pot), {**pot, 'pest_active': True},
                     {**pot, 'growth_progress': ge.FLOWERS['daisy']['grow_time']}, {**pot, 'withered': True}]
    module.db_save_state(sid, state)
    payload = status(client, sid)
    summary = payload['state']
    assert summary['garden'] == {'total_pots': 6, 'empty_pots': [1], 'needs_water_pots': [2], 'growing_count': 1,
                                 'pest_pots': [4], 'ready_pots': [5], 'withered_pots': [6]}
    assert not {'pots', 'pots_summary', 'inventory_counts', 'bouquet_options', 'bouquet_inventory',
                'offline_summary', 'game_hour', 'local_date', 'timezone'} & summary.keys()
    assert {v['section'] for v in summary['available_views']} == set(VIEW_DETAILS)
    assert set(summary['flower_shop']) == {'established', 'launched', 'is_open', 'shelf_capacity', 'occupied_slots', 'empty_slots'}
    assert set(summary['cottage']) == {'owned_count', 'food_remaining', 'water_remaining'}
    assert len(payload['message']) < 100
    for command in ('harvest 5', 'water 2', 'treat 4', 'plant daisy 1'):
        assert client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                           json={'session_id': sid, 'command': command}).get_json()['ok'] is True


@pytest.mark.parametrize('location,present', [(ge.CAT_LOCATION_HOME, True), (ge.CAT_LOCATION_AWAY, False)])
def test_cat_overview_and_positive_inventory(api, cat_clock, location, present):
    module, client = api
    state = adopted_cat_state()
    state['cat_state'].update(location=location, next_outing_at=cat_clock[0] + 10000,
                              outing_return_at=cat_clock[0] + 10000)
    state['inventory']['seeds'] = {'daisy': 3, 'rose': 0}
    state['inventory']['flowers'] = {'daisy': 2}
    state['inventory']['items'] = {'basic_food': 3, 'premium_food': 0, 'cat_treat': 2}
    module.db_save_state('overview-cat', state)
    summary = status(client, 'overview-cat')['state']
    assert summary['cat']['is_present'] is present
    assert summary['cat']['location'] == location
    assert set(summary['cat']) == {'name', 'stage', 'location', 'is_present', 'hunger', 'thirst', 'mood', 'affection', 'max_affection'}
    assert summary['inventory'] == {'seeds': {'daisy': 3}, 'seed_total': 3, 'flower_total': 2,
                                    'items': {'basic_food': 3, 'cat_treat': 2}}


def test_status_request_events_and_reward_hints_are_preserved(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    prepare = module.prepare_command_state

    def reward(state, now, **kwargs):
        weather, messages = prepare(state, now, **kwargs)
        state['money'] += 7
        ge.add_event(state, '随机奖励7金币', now=now, area='garden')
        return weather, messages

    monkeypatch.setattr(module, 'prepare_command_state', reward)
    payload = status(client, sid)
    assert '随机奖励7金币' in payload['message']
    assert payload['state']['recent_events'][-1]['text'] == payload['state']['latest_event'] == '随机奖励7金币'
    monkeypatch.setattr(module, 'prepare_command_state', prepare)
    again = status(client, sid)
    assert again['state']['recent_events'] == [] and again['state']['latest_event'] == ''
    assert any(e['text'] == '随机奖励7金币' for e in again['state']['shared_activity'])
    assert '随机奖励7金币' not in again['message']


def test_new_letter_is_not_lost_or_expanded(api, cat_clock, monkeypatch):
    module, client = api
    state = adopted_cat_state()
    state['cat_max_affection'] = 100
    state['letter_affection_progress'] = 4
    module.db_save_state('overview-letter', state)
    monkeypatch.setattr(ge.random, 'random', lambda: 0.0)
    payload = status(client, 'overview-letter')
    assert payload['state']['letters_received'] == 1
    assert ge.CAT_LETTERS[0]['title'] in payload['message']
    assert ge.CAT_LETTERS[0]['text'] not in payload['message']


def test_overview_projection_is_read_only(api, cat_clock, monkeypatch):
    module, _ = api
    state = adopted_cat_state()
    before = deepcopy(state)
    cat = module._build_cat_summary_for_ai(state)

    def forbidden(*args, **kwargs):
        raise AssertionError('projection reads clock or random')

    monkeypatch.setattr(ge.time, 'time', forbidden)
    monkeypatch.setattr(ge.random, 'random', forbidden)
    monkeypatch.setattr(ge.random, 'randint', forbidden)
    build_overview(state, cat_clock[0], cat_summary=cat)
    assert state == before


def test_status_size_reduction_on_the_same_test_save(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['encyclopedia'] = list(ge.FLOWERS)
    state['inventory']['flowers'] = {fid: 3 for fid in ge.FLOWERS}
    module.db_save_state(sid, state)
    old_state = deepcopy(state)
    with module.app.test_request_context():
        old = {'ok': True, 'session_id': sid, 'message': ge.process_command(old_state, 'status'),
               'state': module._ai_summary(old_state)}
    new = status(client, sid)
    old_json = json.dumps(old, ensure_ascii=False, separators=(',', ':'))
    new_json = json.dumps(new, ensure_ascii=False, separators=(',', ':'))
    print(f'OVERVIEW_SIZE chars {len(old_json)} -> {len(new_json)}; UTF8 bytes {len(old_json.encode())} -> {len(new_json.encode())}')
    assert len(new_json) < len(old_json) * 0.6


def test_status_settles_once_and_projects_the_saved_snapshot(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    cat_clock[0] += 3600
    settle = Mock(wraps=module.apply_offline_progress)
    save = Mock(wraps=module.db_save_state)
    project = module.build_overview
    monkeypatch.setattr(module, 'apply_offline_progress', settle)
    monkeypatch.setattr(module, 'db_save_state', save)

    def inspect(state, now, **kwargs):
        snapshot = deepcopy(state)
        with module._get_conn() as conn:
            row = conn.execute('SELECT state FROM garden_saves WHERE session_id = ?', (sid,)).fetchone()
        assert module._decode_state(row['state']) == snapshot
        result = project(state, now, **kwargs)
        assert state == snapshot
        return result

    monkeypatch.setattr(module, 'build_overview', inspect)
    assert status(client, sid)['state']['server_now'] == cat_clock[0]
    assert settle.call_count == save.call_count == 1
