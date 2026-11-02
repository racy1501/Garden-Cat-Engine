"""Module browsing uses the settled world without exposing hidden definitions."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

import game_engine as ge
from game_views import build_view, VIEW_DETAILS
from test_api_response_shape import api, cat_clock, create_human_garden, adopted_cat_state


def view(client, sid, section, **params):
    return client.get('/api/view', headers={'X-API-Key': 'test-key'},
                      query_string={'session_id': sid, 'section': section, **params})


@pytest.mark.parametrize('section', VIEW_DETAILS)
def test_sections_are_bounded_and_their_links_work(api, cat_clock, section):
    _, client = api
    sid, _ = create_human_garden(client)
    response = view(client, sid, section)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload['section'] == section and payload['ok'] is True
    assert set(payload) <= {'ok', 'section', 'summary', 'items', 'item', 'available_views',
                            'care', 'available_interactions'}
    assert not {'state', 'shared_activity', 'recent_events', 'flower_shop', 'cottage', 'pots'} & payload.keys()
    for link in payload['available_views']:
        assert view(client, sid, **link).status_code == 200
    for detail in VIEW_DETAILS[section]:
        assert view(client, sid, section, detail=detail).status_code == 200


def test_owned_and_discovered_details_and_guessed_ids(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    owned = ge.CAT_COLLECTIBLES[0]
    hidden = ge.CAT_COLLECTIBLES[-1]
    state['collectibles'] = {owned['id']: 2}
    state['encyclopedia'] = ['daisy']
    state['letters_received'] = [0]
    furniture = next(i for i, row in ge.COTTAGE_ITEM_CATALOG.items() if not row.get('legacy_only'))
    state['cottage']['items'] = {furniture: {'source': 'human', 'acquired_at': cat_clock[0]}}
    module.db_save_state(sid, state)
    for section, visible, secret in [
        ('collectibles', owned['id'], hidden['id']),
        ('encyclopedia', 'daisy', 'red_spider_lily'),
        ('letters', '1', '12'),
        ('cottage', furniture, 'not_owned'),
    ]:
        payload = view(client, sid, section).get_json()
        assert len(payload['items']) == 1
        assert 'text' not in payload['items'][0] and 'description' not in payload['items'][0]
        assert view(client, sid, section, item_id=visible).status_code == 200
        denied = view(client, sid, section, item_id=secret)
        assert denied.status_code == 404
        assert secret not in denied.get_data(as_text=True)
    assert '未知' not in view(client, sid, 'collectibles').get_data(as_text=True)
    assert view(client, sid, 'letters', item_id='1').get_json()['item']['text'] == ge.CAT_LETTERS[0]['text']

    state = module.db_load_state(sid)
    state['encyclopedia'] = list(ge.BOUQUETS[next(iter(ge.BOUQUETS))]['components'])
    module.db_save_state(sid, state)
    known = view(client, sid, 'bouquets').get_json()
    visible_ids = {row['id'] for row in known['items']}
    assert visible_ids
    for bid in ge.BOUQUETS:
        response = view(client, sid, 'bouquets', item_id=bid)
        assert response.status_code == (200 if bid in visible_ids else 404)
        if bid in visible_ids:
            assert response.get_json()['item']['components'] == ge.BOUQUETS[bid]['components']
    assert all('components' not in row for row in known['items'])


def test_inventory_positive_only_and_shop_respects_unlocks(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['inventory']['seeds'] = {'daisy': 3, 'rose': 0}
    state['inventory']['flowers'] = {'daisy': 0}
    state['inventory']['items']['ball'] = 0
    module.db_save_state(sid, state)
    assert view(client, sid, 'inventory', detail='seeds').get_json()['items'] == [{'id': 'daisy', 'quantity': 3}]
    assert view(client, sid, 'inventory', detail='flowers').get_json()['items'] == []
    assert all(row['quantity'] > 0 for row in view(client, sid, 'inventory', detail='items').get_json()['items'])
    shop = view(client, sid, 'shop', detail='seeds').get_json()['items']
    assert {row['id'] for row in shop} == {fid for fid in ge.FLOWERS if ge.is_flower_unlocked(state, fid)}
    assert view(client, sid, 'shop', item_id='red_spider_lily').status_code == 404
    assert 'furniture' not in view(client, sid, 'shop', detail='seeds').get_json()


def test_journal_retention_pages_and_source_metadata(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['cat_state']['next_visit_at'] = cat_clock[0] + 10000
    state['events'] = []
    for i in range(55):
        ge.add_event(state, f'event{i}', now=cat_clock[0] - 55 + i, source='human', source_name='阿屿', area='garden')
    module.db_save_state(sid, state)
    before = deepcopy(module.db_load_state(sid))
    pages = [view(client, sid, 'journal', page=p).get_json() for p in range(1, 7)]
    assert pages[0]['summary']['retention_limit'] == pages[0]['summary']['retained'] == 50
    assert pages[0]['items'][0]['text'] == 'event54'
    assert pages[4]['items'][-1]['text'] == 'event5'
    assert pages[5]['items'] == []
    assert sum(len(page['items']) for page in pages) == 50
    assert pages[0]['items'][0]['source_label'] == '人类'
    assert pages[0]['items'][0]['source_name'] == '阿屿'
    saved = module.db_load_state(sid)
    assert saved['events'] == before['events'] and set(saved) == set(before)


def test_projection_cannot_advance_clock_roll_random_or_mutate_state(cat_clock, monkeypatch):
    state = adopted_cat_state()
    state['encyclopedia'] = list(ge.FLOWERS)
    state['letters_received'] = [0]
    state['collectibles'] = {ge.CAT_COLLECTIBLES[0]['id']: 1}
    ge.normalize_state(state, cat_clock[0])
    before = deepcopy(state)

    def forbidden(*args, **kwargs):
        raise AssertionError('projection advanced or rolled')

    monkeypatch.setattr(ge.time, 'time', forbidden)
    for key in ('random', 'randint', 'choice'):
        monkeypatch.setattr(ge.random, key, forbidden)
    for section in VIEW_DETAILS:
        payload = build_view(state, section, cat_clock[0])
        for link in payload['available_views']:
            build_view(state, now=cat_clock[0], **link)
        for detail in VIEW_DETAILS[section]:
            build_view(state, section, cat_clock[0], detail=detail)
    assert state == before


@pytest.mark.parametrize('section,params', [('garden', {}), ('flower_shop', {'detail': 'shelves'}),
                                          ('journal', {'page': 2})])
def test_view_settles_and_saves_once_before_read_only_projection(api, cat_clock, monkeypatch, section, params):
    module, client = api
    sid, _ = create_human_garden(client)
    client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                json={'session_id': sid, 'command': 'plant daisy 1'})
    cat_clock[0] += 3600
    settle = Mock(wraps=module.apply_offline_progress)
    save = Mock(wraps=module.db_save_state)
    monkeypatch.setattr(module, 'apply_offline_progress', settle)
    monkeypatch.setattr(module, 'db_save_state', save)
    project = module.build_view

    def inspect_projection(state, section, now, **kwargs):
        snapshot = deepcopy(state)
        assert save.call_count == 1
        result = project(state, section, now, **kwargs)
        assert state == snapshot
        with module._get_conn() as conn:
            row = conn.execute('SELECT state FROM garden_saves WHERE session_id = ?', (sid,)).fetchone()
        assert module._decode_state(row['state']) == state
        return result

    monkeypatch.setattr(module, 'build_view', inspect_projection)
    assert view(client, sid, section, **params).status_code == 200
    assert settle.call_count == save.call_count == 1


@pytest.mark.parametrize('params', [{'section': 'unknown'}, {'section': 'cat', 'detail': 'shelves'},
                                    {'section': 'journal', 'page': '0'}, {'section': 'journal', 'page': 'a'},
                                    {'section': 'cat', 'page': '1'}, {'section': 'cat', 'item_id': 'x'},
                                    {'section': 'collectibles', 'detail': 'owned', 'item_id': 'x'}])
def test_invalid_selectors_do_not_settle(api, monkeypatch, params):
    module, client = api
    load = Mock(side_effect=AssertionError('invalid query loaded state'))
    monkeypatch.setattr(module, 'db_load_state', load)
    assert view(client, 'unused', **params).status_code == 400
    load.assert_not_called()


def test_view_requires_auth_and_an_existing_session(api):
    _, client = api
    assert client.get('/api/view?section=garden&session_id=unused').status_code == 401
    assert view(client, '', 'garden').status_code == 400
    assert view(client, 'missing', 'garden').status_code == 404


def test_cat_interactions_and_garden_action_status(cat_clock):
    state = adopted_cat_state()
    state['cat_last_pet_real_time'] = cat_clock[0]
    state['inventory']['items']['ball'] = 1
    cat = build_view(state, 'cat', cat_clock[0])
    assert cat['summary']['pet_cooldown_seconds'] == ge.PET_COOLDOWN_REAL_MINUTES * 60
    assert 'pet' not in cat['available_interactions'] and 'play ball' in cat['available_interactions']
    state['cat_state']['location'] = ge.CAT_LOCATION_AWAY
    cat = build_view(state, 'cat', cat_clock[0])
    assert 'play ball' not in cat['available_interactions']
    state['pots'][0] = {'flower_id': 'daisy', 'growth_progress': ge.FLOWERS['daisy']['grow_time'], 'watered': True}
    assert build_view(state, 'garden', cat_clock[0])['items'][0]['status'] == 'ready'
    state['pots'][0]['pest_active'] = True
    assert build_view(state, 'garden', cat_clock[0])['items'][0]['status'] == 'pest_blocked'
