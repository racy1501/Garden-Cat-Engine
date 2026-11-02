"""Batch v1: shared state, one settlement/save, and partial-failure boundaries."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

import game_engine as ge
from test_api_response_shape import api, cat_clock, create_human_garden


def post_batch(client, sid, commands, compact=False):
    return client.post('/api/cmd/batch' + ('?compact=1' if compact else ''),
                       headers={'X-API-Key': 'test-key'},
                       json={'session_id': sid, 'commands': commands})


def test_batch_order_business_failure_and_one_final_state(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    commands = ['buy rose 1', 'plant rose 2', 'harvest 2', 'water all']
    payload = post_batch(client, sid, commands, compact=True).get_json()
    assert payload['ok'] is True
    assert [r['command'] for r in payload['results']] == commands
    assert [r['ok'] for r in payload['results']] == [True, True, False, True]
    assert all(set(r) == {'command', 'ok', 'message'} for r in payload['results'])
    assert payload['state']['pots'][1]['watered'] is True
    assert payload['state']['pots'][1]['flower_id'] == 'rose'
    assert 'water_servings' not in payload['state']['inventory_counts']
    assert '📊' not in ''.join(r['message'] for r in payload['results'])
    assert module.db_load_state(sid)['pots'][1]['watered'] is True


def test_batch_exception_preserves_completed_actions_not_partial_mutation(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    execute = module.execute_command
    attempted = []

    def fail_mid_action(state, command, **kwargs):
        attempted.append(command)
        if command == 'plant rose 2':
            state['money'] = -999
            state['pots'][0] = {'broken': True}
            ge.add_event(state, '半执行事件', area='cottage')
            kwargs['letter_context']['messages'].append('半执行信件')
            raise RuntimeError('injected')
        return execute(state, command, **kwargs)

    monkeypatch.setattr(module, 'execute_command', fail_mid_action)
    payload = post_batch(client, sid, ['buy rose 1', 'plant rose 2', 'water all']).get_json()
    assert payload['ok'] is False
    assert attempted == ['buy rose 1', 'plant rose 2']
    saved = module.db_load_state(sid)
    assert saved['inventory']['seeds']['rose'] == 1
    assert saved['money'] == payload['state']['money'] >= 0
    assert all(p is None for p in saved['pots'])
    assert not any(e['text'] == '半执行事件' for e in saved['events'])
    assert '半执行信件' not in payload['message']
    assert len([e for e in payload['state']['recent_events'] if e.get('source') == 'ai']) == 1
    assert not any(e['text'] == '半执行事件' for e in payload['state']['recent_events'])


def test_batch_settles_once_saves_once_and_summary_matches_disk(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    cat_clock[0] += 3600
    batch_time = cat_clock[0]
    load = Mock(wraps=module.db_load_state)
    settle = Mock(wraps=module.apply_offline_progress)
    prepare = Mock(wraps=module.prepare_command_state)
    save = Mock(wraps=module.db_save_state)
    execute = module.execute_command

    def advance_clock(state, command, **kwargs):
        cat_clock[0] += 5
        return execute(state, command, **kwargs)

    monkeypatch.setattr(module, 'db_load_state', load)
    monkeypatch.setattr(module, 'apply_offline_progress', settle)
    monkeypatch.setattr(module, 'prepare_command_state', prepare)
    monkeypatch.setattr(module, 'db_save_state', save)
    monkeypatch.setattr(module, 'execute_command', advance_clock)
    payload = post_batch(client, sid, ['plant daisy 1', 'water 1']).get_json()
    assert payload['ok'] is True
    assert load.call_count == settle.call_count == prepare.call_count == save.call_count == 1
    with module._get_conn() as conn:
        row = conn.execute('SELECT state FROM garden_saves WHERE session_id = ?', (sid,)).fetchone()
    stored = module._decode_state(row['state'])
    assert stored['last_update'] == stored['last_active_at'] == batch_time
    assert stored['pots'][0]['growth_progress'] == 0
    with module.app.test_request_context():
        projected = module._ai_summary(deepcopy(stored), events_before=[], settled_at=batch_time)
    assert {k: v for k, v in payload['state'].items() if k not in ('recent_events', 'latest_event')} == {
        k: v for k, v in projected.items() if k not in ('recent_events', 'latest_event')}


def test_batch_keeps_rewards_unlocks_and_request_events(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['pots'][0] = {'flower_id': 'daisy', 'growth_progress': ge.FLOWERS['daisy']['grow_time'],
                        'watered': True, 'last_growth_update': cat_clock[0], 'pest_resolved': True}
    module.db_save_state(sid, state)
    weather = ge.get_weather_info

    def rewarded_weather(state, now):
        data, messages = weather(state, now)
        state['money'] += 7
        ge.add_event(state, '随机奖励7块', now=now, area='garden')
        return data, messages + ['随机奖励7块']

    monkeypatch.setattr(ge, 'get_weather_info', rewarded_weather)
    payload = post_batch(client, sid, ['harvest 1', 'plant daisy 1']).get_json()
    assert payload['ok'] is True
    assert '解锁奖励' in payload['results'][0]['message']
    assert '随机奖励7块' in payload['message']
    assert any(e['text'] == '随机奖励7块' for e in payload['state']['recent_events'])
    assert module.db_load_state(sid)['encyclopedia'] == ['daisy']


@pytest.mark.parametrize('commands', [None, [], 'water all', [1], [''], ['buy rose 1'] * 51])
def test_batch_rejects_invalid_envelope_before_loading(api, monkeypatch, commands):
    module, client = api
    load = Mock()
    monkeypatch.setattr(module, 'db_load_state', load)
    assert post_batch(client, 'unused', commands).status_code == 400
    load.assert_not_called()


def test_batch_excludes_notes_and_queries_without_external_writes(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    notes = Mock(side_effect=AssertionError('notes must not run'))
    monkeypatch.setattr(module, '_handle_note_command', notes)
    payload = post_batch(client, sid, ['note hello', 'help', 'status', 'buy rose 1']).get_json()
    assert payload['ok'] is True
    assert [r['ok'] for r in payload['results']] == [False, False, False, True]
    notes.assert_not_called()


def test_batch_save_failure_is_not_reported_as_success(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    monkeypatch.setattr(module, 'db_save_state', Mock(side_effect=OSError('disk failed')))
    response = post_batch(client, sid, ['buy rose 1'])
    assert response.status_code == 500
    assert response.get_json()['ok'] is False
    assert 'state' not in response.get_json()
