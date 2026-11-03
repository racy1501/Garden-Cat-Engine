"""Module browsing uses the settled world without exposing hidden definitions."""
from copy import deepcopy
from unittest.mock import Mock

import pytest

import game_engine as ge
from game_views import build_garden_pots, build_overview, build_view, validate_view, VIEW_DETAILS
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
    assert set(payload) <= {'ok', 'section', 'summary', 'items', 'item', 'available_views', 'next_tool',
                            'care', 'available_interactions', 'flowers', 'seeds'}
    assert (payload.get('next_tool') == 'garden_view') is bool(payload['available_views'])
    assert not {'state', 'shared_activity', 'recent_events', 'flower_shop', 'cottage', 'pots'} & payload.keys()
    for link in payload['available_views']:
        assert view(client, sid, **link).status_code == 200
    for detail in VIEW_DETAILS[section]:
        assert view(client, sid, section, detail=detail).status_code == 200


def test_navigation_links_are_complete_and_followable_at_every_level(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['collectibles'] = {ge.CAT_COLLECTIBLES[0]['id']: 1}
    state['encyclopedia'] = list(ge.BOUQUETS['first_meeting']['components'])
    state['letters_received'] = [0]
    furniture = next(i for i, row in ge.COTTAGE_ITEM_CATALOG.items() if not row.get('legacy_only'))
    state['cottage']['items'] = {furniture: {'source': 'human', 'acquired_at': cat_clock[0]}}
    state['events'] = []
    for index in range(12):
        ge.add_event(state, f'动态{index}', now=cat_clock[0] - 20 + index, area='garden')
    module.db_save_state(sid, state)

    overview = client.get('/api/status', headers={'X-API-Key': 'test-key'},
                          query_string={'session_id': sid}).get_json()['state']
    assert overview['next_tool'] == 'garden_view'
    pending = list(overview['available_views'])
    visited = set()
    sections, terminal_sections = set(), set()
    while pending:
        link = pending.pop()
        assert 'section' in link and set(link) <= {'section', 'detail', 'item_id', 'page'}
        key = tuple(sorted(link.items()))
        if key in visited:
            continue
        visited.add(key)
        response = view(client, sid, **link)
        assert response.status_code == 200
        payload = response.get_json()
        sections.add(link['section'])
        links = payload['available_views']
        if links:
            assert payload['next_tool'] == 'garden_view'
            pending.extend(links)
        else:
            assert 'next_tool' not in payload
            terminal_sections.add(link['section'])
    assert sections == set(VIEW_DETAILS)
    assert terminal_sections == set(VIEW_DETAILS) - {'journal'}


def test_garden_view_lists_flower_and_reliable_care_status_without_changing_status(cat_clock):
    now = cat_clock[0]
    grow_time = ge.FLOWERS['daisy']['grow_time']
    pot = {'flower_id': 'daisy', 'growth_progress': 0, 'watered': True, 'last_growth_update': now}
    state = ge.get_default_state()
    state['max_pots'] = 7
    state['pots'] = [None, dict(pot), {**pot, 'growth_progress': grow_time},
                     {**pot, 'pest_active': True, 'watered': False}, {**pot, 'watered': False},
                     {**pot, 'withered': True}, {**pot, 'pest_active': True}]
    state['vase'] = [{'flower_id': 'daisy', 'arranged_time': now}]

    garden = build_view(state, 'garden', now)
    pots = garden['items']
    assert len(pots) == 7
    assert [(row['slot'], row.get('flower_id'), row['status']) for row in pots] == [
        (1, None, 'empty'), (2, 'daisy', 'growing'),
        (3, 'daisy', 'ready'), (4, 'daisy', 'pest_blocked'),
        (5, 'daisy', 'needs_water'), (6, 'daisy', 'withered'),
        (7, 'daisy', 'pest_blocked'),
    ]
    growing_seconds = int(grow_time / ge.WEATHER[state['weather']]['grow_speed'])
    assert pots[1]['remaining_seconds'] == growing_seconds
    assert pots[2]['status'] == 'ready'
    assert 'remaining_seconds' not in pots[2]
    assert pots[3]['watered'] is False and pots[6]['watered'] is True
    assert 'remaining_seconds' not in pots[0] and set(pots[0]) == {'slot', 'status'}
    assert 'remaining_seconds' not in pots[4] and 'remaining_seconds' not in pots[5]
    assert all(not {'id', 'flower_name', 'progress', 'paused', 'has_pests'} & row.keys() for row in pots)
    assert garden['available_views'] == [{'section': 'garden', 'detail': 'vase'}]
    assert garden['next_tool'] == 'garden_view'
    assert build_view(state, 'garden', now, detail='vase')['items'][0]['flower_id'] == 'daisy'
    assert set(build_view(state, 'garden', now, item_id='2')['item']) == {
        'id', 'slot', 'status', 'flower_id', 'growth_progress', 'watered',
    }

    assert set(build_garden_pots(state)[0]) == {
        'slot', 'flower_id', 'status', 'progress', 'remaining_seconds',
        'watered', 'has_pests', 'paused',
    }

    status_garden = build_overview(state, now, cat_summary=None)['garden']
    assert status_garden == {'total_pots': 7, 'empty_pots': [1], 'needs_water_pots': [5],
                             'growing_count': 1, 'pest_pots': [4, 7], 'ready_pots': [3],
                             'withered_pots': [6]}


def test_inventory_and_bouquet_level_two_include_decision_inputs(cat_clock):
    now = cat_clock[0]
    state = ge.get_default_state()
    state['inventory']['flowers'] = {'daisy': 3, 'rose': 0}
    inventory = build_view(state, 'inventory', now)
    assert inventory['flowers'] == [{'flower_id': 'daisy', 'count': 3}]
    assert 'flowers' not in inventory['summary']
    assert {'section': 'inventory', 'detail': 'flowers'} in inventory['available_views']
    assert build_view(state, 'inventory', now, detail='flowers')['items'] == [
        {'id': 'daisy', 'quantity': 3},
    ]

    state['encyclopedia'] = list(ge.FLOWERS)
    bouquet_ids = list(ge.BOUQUETS)
    makeable_id = bouquet_ids[0]
    state['inventory']['flowers'] = dict(ge.BOUQUETS[makeable_id]['components'])
    bouquets = build_view(state, 'bouquets', now)
    rows = {row['id']: row for row in bouquets['items']}
    assert rows[makeable_id]['can_make'] is True
    assert 'missing' not in rows[makeable_id]

    blocked_id = next(bid for bid in bouquet_ids if bid != makeable_id)
    expected_missing = ge.get_bouquet_options(state)
    expected_missing = next(row['missing'] for row in expected_missing if row['bouquet_id'] == blocked_id)
    assert expected_missing
    assert len(expected_missing) >= 2
    assert rows[blocked_id]['can_make'] is False
    assert rows[blocked_id]['missing'] == [
        {'flower_id': flower_id, 'count': count}
        for flower_id, count in expected_missing.items()
    ]
    assert {'section': 'bouquets', 'item_id': blocked_id} in bouquets['available_views']
    assert build_view(state, 'bouquets', now, item_id=blocked_id)['item']['components'] == \
        ge.BOUQUETS[blocked_id]['components']
    assert build_view(state, 'bouquets', now, detail='inventory')['items'] == \
        ge.get_bouquet_inventory_public(state)


def test_cat_shop_pack_and_inventory_units_follow_formal_configuration(api, cat_clock, monkeypatch):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['inventory']['items'] = {'basic_food': 5, 'premium_food': 3, 'cat_treat': 2, 'ball': 4}
    module.db_save_state(sid, state)
    shop = {row['id']: row for row in view(client, sid, 'shop', detail='items').get_json()['items']}
    for iid, portions in [('basic_food', 5), ('premium_food', 5), ('cat_treat', 2)]:
        assert shop[iid]['price_per_pack'] == ge.ITEMS[iid]['price']
        assert shop[iid]['portions_per_pack'] == portions
        assert 'price' not in shop[iid]
    assert shop['ball']['price'] == ge.ITEMS['ball']['price']
    assert 'portions_per_pack' not in shop['ball']
    inventory = {row['id']: row for row in view(client, sid, 'inventory', detail='items').get_json()['items']}
    assert inventory['basic_food']['portions'] == 5
    assert inventory['premium_food']['portions'] == 3
    assert inventory['cat_treat']['portions'] == 2
    assert inventory['ball'] == {'id': 'ball', 'quantity': 4}
    overview = client.get('/api/status', headers={'X-API-Key': 'test-key'},
                          query_string={'session_id': sid}).get_json()['state']['inventory']
    assert overview['items'] == state['inventory']['items']
    assert overview['item_units'] == {'basic_food': 'portion', 'premium_food': 'portion',
                                      'cat_treat': 'portion', 'ball': 'item'}
    monkeypatch.setitem(ge.CAT_ITEM_PACKAGE_SIZES, 'basic_food', 7)
    assert build_view(state, 'shop', cat_clock[0], detail='items')['items'][0]['portions_per_pack'] == 7


def test_buy_packaged_cat_items_through_agent_api(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['money'] = 100
    state['inventory']['items'] = {}
    module.db_save_state(sid, state)
    for iid, portions in [('basic_food', 5), ('cat_treat', 2)]:
        price = ge.ITEMS[iid]['price']
        response = client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                               json={'session_id': sid, 'command': f'buy {iid} 1'}).get_json()
        assert response['ok']
        assert f'1包{ge.ITEMS[iid]["name"]}，共{portions}份，花费{price}块' in response['message']
        assert response['state']['inventory']['items'][iid] == portions
        assert response['state']['inventory']['item_units'][iid] == 'portion'
        assert any(f'1包{ge.ITEMS[iid]["name"]}，共{portions}份' in event['text']
                   for event in response['state']['recent_events'])
    assert module.db_load_state(sid)['money'] == 100 - ge.ITEMS['basic_food']['price'] - ge.ITEMS['cat_treat']['price']


def test_redundant_shop_cottage_and_collectibles_navigation_is_not_exposed(cat_clock):
    now = cat_clock[0]
    state = ge.get_default_state()

    state['encyclopedia'] = ['daisy']
    shop = build_view(state, 'shop', now)
    seed_detail = build_view(state, 'shop', now, detail='seeds')
    assert seed_detail['items']
    assert not any('item_id' in link for link in seed_detail['available_views'])
    first_seed = seed_detail['items'][0]['id']
    assert build_view(state, 'shop', now, item_id=first_seed)['item']['id'] == first_seed
    assert all('item_id' not in link for link in shop['available_views'])

    furniture_id = next(iid for iid, row in ge.COTTAGE_ITEM_CATALOG.items()
                        if not row.get('legacy_only') and 'price' in row and not row.get('reward_only'))
    state['cottage']['items'][furniture_id] = {'source': 'human', 'acquired_at': now}
    cottage = build_view(state, 'cottage', now)
    assert any(row['id'] == furniture_id for row in cottage['items'])
    assert {'section': 'cottage', 'detail': 'cat_area'} in cottage['available_views']
    assert not any(link.get('detail') == 'furniture' for link in cottage['available_views'])
    with pytest.raises(ValueError):
        validate_view('cottage', detail='furniture')
    assert build_view(state, 'cottage', now, item_id=furniture_id)['item']['source'] == 'human'
    assert build_view(state, 'cottage', now, detail='cat_area')['summary']

    collectible_id = ge.CAT_COLLECTIBLES[0]['id']
    state['collectibles'][collectible_id] = 1
    collectibles = build_view(state, 'collectibles', now)
    assert [row['id'] for row in collectibles['items']] == [collectible_id]
    assert {'section': 'collectibles', 'detail': 'rules'} in collectibles['available_views']
    assert not any(link.get('detail') == 'owned' for link in collectibles['available_views'])
    with pytest.raises(ValueError):
        validate_view('collectibles', detail='owned')
    assert build_view(state, 'collectibles', now, item_id=collectible_id)['item']['id'] == collectible_id
    assert 'rule' in build_view(state, 'collectibles', now, detail='rules')['summary']


def test_shop_level_two_surfaces_only_unlocked_seed_economics(cat_clock):
    now = cat_clock[0]
    state = ge.get_default_state()
    state['encyclopedia'] = ['daisy']

    shop = build_view(state, 'shop', now)
    expected = [
        {'id': flower_id, 'seed_price_per_seed': flower['seed_price'],
         'grow_time': flower['grow_time'], 'sell_price_per_flower': flower['sell_price']}
        for flower_id, flower in ge.FLOWERS.items() if ge.is_flower_unlocked(state, flower_id)
    ]
    assert shop['seeds'] == expected
    assert all(set(seed) == {'id', 'seed_price_per_seed', 'grow_time', 'sell_price_per_flower'} for seed in shop['seeds'])
    assert 'red_spider_lily' not in {seed['id'] for seed in shop['seeds']}
    assert 'seeds' not in shop['summary']
    assert not any(link.get('detail') == 'seeds' for link in shop['available_views'])

    # Category details keep their existing full records and direct item lookup remains callable.
    seed_detail = build_view(state, 'shop', now, detail='seeds')
    assert seed_detail['items'] == [
        {'id': flower_id, 'name': flower['name'], 'seed_price_per_seed': flower['seed_price'],
         'grow_time': flower['grow_time'], 'sell_price_per_flower': flower['sell_price']}
        for flower_id, flower in ge.FLOWERS.items() if ge.is_flower_unlocked(state, flower_id)
    ]
    assert seed_detail['items'][0]['name']
    for row in seed_detail['items']:
        assert build_view(state, 'shop', now, item_id=row['id'])['item'] == row
        assert not {'seed_price', 'sell_price'} & row.keys()
    assert build_view(state, 'shop', now, detail='items')['items']
    furniture_detail = build_view(state, 'shop', now, detail='furniture')
    assert furniture_detail['items']
    first_item = furniture_detail['items'][0]['id']
    assert build_view(state, 'shop', now, item_id=first_item)['item']['id'] == first_item


def test_public_catalog_keeps_seed_price_contract(api):
    _, client = api
    flower = client.get('/api/catalog').get_json()['flowers']['daisy']
    assert flower['seed_price'] == ge.FLOWERS['daisy']['seed_price']
    assert flower['sell_price'] == ge.FLOWERS['daisy']['sell_price']
    assert not {'seed_price_per_pack', 'sell_price_per_flower'} & flower.keys()


def test_encyclopedia_detail_keeps_discovery_data_without_economics(cat_clock):
    now = cat_clock[0]
    state = ge.get_default_state()
    state['encyclopedia'] = ['daisy']
    state['flower_harvest_counts'] = {'daisy': 4}

    detail = build_view(state, 'encyclopedia', now, item_id='daisy')['item']
    assert detail == {'id': 'daisy', 'name': ge.FLOWERS['daisy']['name'],
                      'rarity': ge.FLOWERS['daisy']['rarity'], 'harvests': 4}
    assert not {'grow_time', 'sell_price', 'seed_price'} & detail.keys()

    shop = build_view(state, 'shop', now)
    daisy = next(row for row in shop['seeds'] if row['id'] == 'daisy')
    assert daisy == {'id': 'daisy', 'seed_price_per_seed': ge.FLOWERS['daisy']['seed_price'],
                     'grow_time': ge.FLOWERS['daisy']['grow_time'],
                     'sell_price_per_flower': ge.FLOWERS['daisy']['sell_price']}


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
        assert not any(link.get('item_id') == secret for link in payload['available_views'])
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
    assert {link['item_id'] for link in known['available_views'] if 'item_id' in link} == visible_ids
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
    assert all(row.get('quantity', row.get('portions', 0)) > 0
               for row in view(client, sid, 'inventory', detail='items').get_json()['items'])
    shop = view(client, sid, 'shop', detail='seeds').get_json()['items']
    assert {row['id'] for row in shop} == {fid for fid in ge.FLOWERS if ge.is_flower_unlocked(state, fid)}
    assert view(client, sid, 'shop', item_id='red_spider_lily').status_code == 404
    assert 'furniture' not in view(client, sid, 'shop', detail='seeds').get_json()


def test_flower_shop_eligibility_shows_formal_targets_and_remaining(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['encyclopedia'] = list(ge.FLOWERS)[:5]
    state['flower_harvest_counts'] = {'daisy': 14}
    state['direct_flower_sale_earned'] = 4
    module.db_save_state(sid, state)

    eligibility = view(client, sid, 'flower_shop', detail='eligibility').get_json()
    summary = eligibility['summary']
    formal = ge.get_flower_shop_eligibility_summary(module.db_load_state(sid))
    assert summary == formal
    assert summary['eligible'] is False
    assert summary['requirements'] == {
        'encyclopedia': {'current': 5, 'required': ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['encyclopedia'], 'remaining': 5},
        'harvests': {'current': 14, 'required': ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['harvests'], 'remaining': 28},
        'direct_flower_sale_earned': {
            'current': 4, 'required': ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['direct_flower_sale_earned'],
            'remaining': 2996,
        },
    }
    assert summary['eligible'] is ge.is_flower_shop_eligible(module.db_load_state(sid))

    state = module.db_load_state(sid)
    state['encyclopedia'] = list(ge.FLOWERS)[:ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['encyclopedia']]
    state['flower_harvest_counts'] = {'daisy': ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['harvests']}
    state['direct_flower_sale_earned'] = ge.FLOWER_SHOP_ELIGIBILITY_REQUIREMENTS['direct_flower_sale_earned']
    module.db_save_state(sid, state)
    completed = view(client, sid, 'flower_shop', detail='eligibility').get_json()['summary']
    assert completed['eligible'] is True
    assert all(row['remaining'] == 0 and row['current'] >= row['required']
               for row in completed['requirements'].values())

    rules = view(client, sid, 'flower_shop', detail='rules').get_json()
    assert set(rules['summary']) == {'pricing_profiles', 'bouquet_lifetime_seconds'}
    assert 'requirements' not in rules['summary'] and 'eligibility' not in rules['summary']


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


@pytest.mark.parametrize('command,section,detail', [
    ('shop', 'shop', None), ('vase', 'garden', 'vase'), ('collectibles', 'collectibles', None),
    ('encyclopedia', 'encyclopedia', None), ('letters', 'letters', None), ('make_bouquet', 'bouquets', None),
])
@pytest.mark.parametrize('compact', [False, True])
def test_legacy_query_is_the_same_view_without_cross_module_state(api, cat_clock, monkeypatch, command, section, detail, compact):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['cat_state']['next_visit_at'] = cat_clock[0] + 10000
    state['events'] = []
    module.db_save_state(sid, state)
    expected = view(client, sid, section, **({'detail': detail} if detail else {})).get_json()
    settle = Mock(wraps=module.apply_offline_progress)
    save = Mock(wraps=module.db_save_state)
    monkeypatch.setattr(module, 'apply_offline_progress', settle)
    monkeypatch.setattr(module, 'db_save_state', save)
    response = client.post('/api/cmd' + ('?compact=1' if compact else ''), headers={'X-API-Key': 'test-key'},
                           json={'session_id': sid, 'command': command})
    assert response.status_code == 200
    result = response.get_json()
    assert result == expected
    assert 'state' not in result and 'recent_events' not in result and 'shared_activity' not in result
    assert settle.call_count == save.call_count == 1


def test_legacy_queries_never_expose_undiscovered_items(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    state = module.db_load_state(sid)
    state['collectibles'] = {}
    state['encyclopedia'] = []
    state['letters_received'] = []
    module.db_save_state(sid, state)
    for command in ('collectibles', 'encyclopedia', 'letters', 'make_bouquet'):
        payload = client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                              json={'session_id': sid, 'command': command}).get_json()
        assert payload['items'] == []
        assert not any('item_id' in link for link in payload['available_views'])
    hidden_id = ge.CAT_COLLECTIBLES[0]['id']
    assert view(client, sid, 'collectibles', item_id=hidden_id).status_code == 404


def test_make_bouquet_with_recipe_stays_a_real_action(api, cat_clock):
    module, client = api
    sid, _ = create_human_garden(client)
    bouquet_id, bouquet = next(iter(ge.BOUQUETS.items()))
    state = module.db_load_state(sid)
    state['encyclopedia'] = list(bouquet['components'])
    state['inventory']['flowers'] = dict(bouquet['components'])
    module.db_save_state(sid, state)
    response = client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                           json={'session_id': sid, 'command': f'make_bouquet bouquet_id={bouquet_id}'})
    assert response.get_json()['ok'] is True
    assert 'state' in response.get_json()
    assert module.db_load_state(sid)['bouquet_gifts'][-1]['bouquet_id'] == bouquet_id


def test_ai_help_guides_layered_access(api, cat_clock):
    _, client = api
    sid, _ = create_human_garden(client)
    headers = {'X-API-Key': 'test-key'}
    for response in (client.get('/api/help', headers=headers),
                     client.post('/api/cmd', headers=headers, json={'session_id': sid, 'command': 'help'})):
        text = response.get_json()['message']
        assert all(name in text for name in ('garden_status', 'garden_view', 'garden_command', 'garden_batch'))
        assert '将其参数用于下一次 garden_view' in text
        assert 'collectibles - 查看' not in text and 'vase - 查看' not in text
        assert 'make_bouquet bouquet_id=' in text


def test_reference_help_excludes_sample_settlement_and_summary(api, monkeypatch):
    _, client = api
    monkeypatch.setattr(ge, 'prepare_command_state',
                        lambda state, now, *, letter_context: (ge.WEATHER['sunny'], ['猫咪来了，正在花园里停留。']))
    result = client.get('/api/help', headers={'X-API-Key': 'test-key'}).get_json()
    assert result['ok'] is True
    assert '命令帮助' in result['message'] and 'garden_view' in result['message']
    assert '猫咪来了，正在花园里停留。' not in result['message']
    assert '📊' not in result['message']
    assert '每颗可种一盆' in result['message']


def test_buff_event_metadata_reaches_web_records_and_journal(api, cat_clock):
    module, _ = api
    state = ge.get_default_state()
    ge.add_event(state, '好运', now=cat_clock[0], area='flower_shop',
                 event_type='flower_shop_cat_buff', buff_type='popular', collectible_id='pebble')
    record = module._event_record_for_client(state['events'][-1])
    assert (record['event_type'], record['buff_type'], record['collectible_id']) == ('flower_shop_cat_buff', 'popular', 'pebble')
    web_record = module._summary(state)['recent_event_records'][-1]
    assert (web_record['event_type'], web_record['buff_type'], web_record['collectible_id']) == ('flower_shop_cat_buff', 'popular', 'pebble')
    journal = build_view(state, 'journal', cat_clock[0])
    assert journal['items'][0]['buff_type'] == 'popular'
    assert journal['items'][0]['collectible_id'] == 'pebble'


@pytest.mark.parametrize('command', ['shop extra', 'vase 1', 'collectibles hidden', 'encyclopedia daisy',
                                     'letters 1', 'make_bouquet message=hello', 'make_bouquet bouquet_id='])
def test_invalid_legacy_query_arguments_do_not_return_world_state(api, command):
    _, client = api
    sid, _ = create_human_garden(client)
    response = client.post('/api/cmd', headers={'X-API-Key': 'test-key'},
                           json={'session_id': sid, 'command': command})
    assert response.status_code == 400
    assert 'state' not in response.get_json()
