"""Actions report their outcome and one bounded, already-settled decision state."""
from copy import deepcopy

import pytest
import game_engine as ge
from test_api_response_shape import api, cat_clock, create_human_garden, adopted_cat_state
from test_batch import post_batch


def command(client, sid, text):
    return client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                       json={'session_id': sid, 'command': text}).get_json()


def assert_decision_state(state):
    assert {'money', 'garden', 'cat', 'inventory', 'encyclopedia', 'collectibles',
            'letters_received', 'available_views', 'recent_events', 'latest_event'} <= state.keys()
    assert not {'pots', 'pots_summary', 'inventory_counts', 'bouquet_options', 'bouquet_inventory',
                'shared_activity', 'offline_summary', 'garden_events'} & state.keys()
    assert 'slots' not in state['flower_shop']
    assert 'owned_items' not in state['cottage']


def test_single_success_and_failure_keep_outcome_and_decision_state(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    planted = command(client, sid, 'plant daisy 1')
    assert planted['ok'] is True and planted['command'] == 'plant daisy 1'
    assert 'water 1' in planted['message']
    assert '📊' not in planted['message']
    assert_decision_state(planted['state'])
    assert planted['state']['garden']['needs_water_pots'] == [1]
    assert planted['state']['inventory']['seed_total'] == 2
    failed = command(client, sid, 'harvest 1')
    assert failed['ok'] is False and '没浇水' in failed['message']
    assert_decision_state(failed['state'])
    assert failed['state']['recent_events'] == [] and failed['state']['latest_event'] == ''
    assert failed['state']['money'] == module.db_load_state(sid)['money']


@pytest.mark.parametrize('batch', [False, True])
def test_crafted_instance_ids_allow_immediate_gift(api, cat_clock, batch):
    module, client = api
    sid, headers = create_human_garden(client)
    state = module.db_load_state(sid)
    state['encyclopedia'] = ['tulip', 'baby_breath']
    state['inventory']['flowers'] = {'tulip': 4, 'baby_breath': 2}
    module.db_save_state(sid, state)
    craft = 'craft_bouquet bouquet_id=first_meeting'
    if batch:
        payload = post_batch(client, sid, [craft, 'harvest 1', craft]).get_json()
        assert [row['ok'] for row in payload['results']] == [True, False, True]
        created = [row['created_bouquets'][0] for row in (payload['results'][0], payload['results'][2])]
        assert len({row['instance_id'] for row in created}) == 2
    else:
        payload = command(client, sid, craft)
        created = payload['created_bouquets']
    assert_decision_state(payload['state'])
    for item in created:
        assert set(item) == {'instance_id', 'bouquet_id'} and item['bouquet_id'] == 'first_meeting'
        gifted = command(client, sid, f"gift_bouquet instance_id={item['instance_id']} message=春天快乐")
        assert gifted['ok'] is True and '送' in gifted['message']
        assert 'created_bouquets' not in gifted
    saved = module.db_load_state(sid)
    assert saved['bouquet_inventory'] == []
    web = client.get(f'/web/status?session_id={sid}', headers=headers).get_json()['state']
    assert len(web['bouquet_gifts']) == len(created)
    assert all(gift['message'] == '春天快乐' for gift in web['bouquet_gifts'])


@pytest.mark.parametrize('batch', [False, True])
def test_harvest_rewards_unlock_and_new_record_survive(api, cat_clock, batch):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['pots'][0] = {'flower_id': 'daisy', 'growth_progress': ge.FLOWERS['daisy']['grow_time'],
                        'watered': True, 'last_growth_update': cat_clock[0], 'pest_resolved': True}
    module.db_save_state(sid, state)
    payload = post_batch(client, sid, ['harvest 1']).get_json() if batch else command(client, sid, 'harvest 1')
    message = payload['results'][0]['message'] if batch else payload['message']
    assert '解锁奖励' in message and '雏菊' in message
    assert payload['state']['encyclopedia']['recorded'] == 1
    assert payload['state']['inventory']['flower_total'] == 1
    assert payload['state']['garden']['empty_pots'] == [1, 2, 3]
    assert any('收获' in event['text'] for event in payload['state']['recent_events'])
    assert payload['state']['money'] == module.db_load_state(sid)['money']


@pytest.mark.parametrize('batch', [False, True])
def test_new_letter_results_survive(api, cat_clock, monkeypatch, batch):
    module, client = api
    state = adopted_cat_state()
    state['cat_max_affection'] = 100
    state['letter_affection_progress'] = 4
    module.db_save_state('action-letter', state)
    monkeypatch.setattr(ge.random, 'random', lambda: 0.0)
    payload = post_batch(client, 'action-letter', ['pet']).get_json() if batch else command(client, 'action-letter', 'pet')
    messages = payload['message'] + '\n' + '\n'.join(row['message'] for row in payload.get('results', []))
    assert ge.CAT_LETTERS[0]['title'] in messages
    assert payload['state']['letters_received'] == 1
    assert_decision_state(payload['state'])


@pytest.mark.parametrize('batch', [False, True])
def test_settled_cat_return_is_readable_without_replaying_history(api, cat_clock, batch):
    module, client = api
    state = adopted_cat_state()
    state['cat_state'].update(location=ge.CAT_LOCATION_AWAY, outing_return_at=cat_clock[0] + 60,
                              next_outing_at=0, last_lifecycle_settled_at=cat_clock[0])
    module.db_save_state('action-return', state)
    cat_clock[0] += 60
    payload = post_batch(client, 'action-return', ['harvest 1']).get_json() if batch else command(client, 'action-return', 'harvest 1')
    assert '回家' in payload['message']
    assert payload['state']['cat']['is_present'] is True
    assert payload['state']['recent_events'] == [] and payload['state']['latest_event'] == ''
    again = command(client, 'action-return', 'harvest 1')
    assert '回家' not in again['message']


@pytest.mark.parametrize('batch', [False, True])
def test_settled_rainbow_reward_is_readable_without_full_event_module(api, cat_clock, monkeypatch, batch):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['weather'] = 'rainy'
    state['weather_change_time'] = cat_clock[0] + 10
    state['next_butterfly_at'] = cat_clock[0] + 10000
    module.db_save_state(sid, state)

    def choose(options):
        return 'sunny' if options == list(ge.WEATHER.keys()) else options[0]

    monkeypatch.setattr(ge.random, 'choice', choose)
    monkeypatch.setattr(ge.random, 'random', lambda: 0.0)
    cat_clock[0] += 10
    payload = post_batch(client, sid, ['harvest 1']).get_json() if batch else command(client, sid, 'harvest 1')
    assert '彩虹出现' in payload['message'] and '+10金币' in payload['message']
    assert_decision_state(payload['state'])
    assert payload['state']['money'] == module.db_load_state(sid)['money']
    assert '彩虹' not in command(client, sid, 'harvest 1')['message']


def test_action_projection_reads_saved_state_without_extra_settlement(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    project = module.build_overview

    def inspect(state, now, **kwargs):
        before = deepcopy(state)
        with module._get_conn() as conn:
            row = conn.execute('SELECT state FROM garden_saves WHERE session_id = ?', (sid,)).fetchone()
        assert module._decode_state(row['state']) == before
        result = project(state, now, **kwargs)
        assert state == before
        return result

    monkeypatch.setattr(module, 'build_overview', inspect)
    assert command(client, sid, 'plant daisy 1')['ok'] is True
