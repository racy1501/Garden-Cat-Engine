"""Bounded AI module projections. Call only with an already settled state."""
from copy import deepcopy

import game_engine as ge


VIEW_DETAILS = {
    "garden": {"vase"}, "cat": set(),
    "inventory": {"seeds", "flowers", "items", "bouquets"},
    "collectibles": {"rules"}, "encyclopedia": set(),
    "flower_shop": {"eligibility", "hours", "shelves", "equipment", "rules"},
    "cottage": {"cat_area"}, "bouquets": {"inventory"},
    "letters": set(), "journal": set(), "shop": {"seeds", "items", "furniture"},
}
ITEM_SECTIONS = {"garden", "collectibles", "encyclopedia", "cottage", "bouquets", "letters", "shop"}
JOURNAL_PAGE_SIZE = 10


def validate_view(section, detail=None, item_id=None, page=None):
    if section not in VIEW_DETAILS:
        raise ValueError("未知 section。可选：" + ", ".join(VIEW_DETAILS))
    if detail is not None and detail not in VIEW_DETAILS[section]:
        raise ValueError("此 section 不支持该 detail。")
    if item_id is not None and (not item_id or section not in ITEM_SECTIONS or detail is not None):
        raise ValueError("item_id 仅用于本模块具体对象，不能与 detail 同时提供。")
    if page is not None and (section != "journal" or type(page) is not int or page < 1):
        raise ValueError("page 仅供 journal 使用，且必须是正整数。")


def _pick(value, *keys):
    return {key: deepcopy(value[key]) for key in keys if key in value}


def _entry(**params):
    return params


def _navigation(result, views):
    result["available_views"] = views
    if views:
        result["next_tool"] = "garden_view"


def _item(items, item_id):
    found = next((item for item in items if str(item["id"]) == item_id), None)
    if found is None:
        raise LookupError("该内容不存在或当前不可查看。")
    return found


def _care(state):
    care = state.get("cat_care", {})
    return {key: _pick(care.get(key, {}), "facility_id", "capacity", "remaining_portions", "food_type")
            for key in ("bed", "food_bowl", "water_bowl")}


def _goods(state):
    seeds = [{"id": fid, **_pick(flower, "name", "seed_price", "grow_time", "sell_price")}
             for fid, flower in ge.FLOWERS.items() if ge.is_flower_unlocked(state, fid)]
    items = [{"id": iid, **_pick(ge.ITEMS[iid], "name", "price")}
             for iid in ge.SHOP_CAT_ITEM_IDS]
    furniture = [{"id": iid, **_pick(item, "name", "price", "description")}
                 for iid, item in ge.COTTAGE_ITEM_CATALOG.items()
                 if "price" in item and not item.get("reward_only") and not item.get("legacy_only")
                 and iid not in state.get("cottage", {}).get("items", {})]
    return {"seeds": seeds, "items": items, "furniture": furniture}


def build_garden_pots(state):
    """Project settled pot facts shared by status and garden module views."""
    pots = []
    weather = ge.WEATHER.get(state.get("weather", "sunny"), ge.WEATHER["sunny"])
    for index, pot in enumerate(state.get("pots", [])):
        status = ge.get_pot_ai_status(state, index, pot)
        flower_id = pot.get("flower_id") if pot else None
        flower = ge.FLOWERS.get(flower_id)
        grow_time = float(flower["grow_time"]) if flower else 0.0
        growth = min(grow_time, max(0.0, float(pot.get("growth_progress", 0.0)))) if grow_time else 0.0
        speed = ge.get_actual_grow_speed(pot, weather) if pot else 0.0
        paused = status in ("needs_water", "pest_blocked") or (status == "growing" and speed <= 0)
        remaining = 0 if status == "ready" else None
        if status == "growing" and speed > 0 and grow_time:
            remaining = max(0, int((grow_time - growth) / speed))
        pots.append({
            "slot": index + 1, "flower_id": flower_id, "status": status,
            "progress": growth / grow_time if grow_time else 0.0,
            "remaining_seconds": remaining,
            "watered": bool(pot.get("watered", True)) if pot else False,
            "has_pests": status == "pest_blocked", "paused": paused,
        })
    return pots


def build_overview(state, now, *, cat_summary):
    """Level-one decision data from the same settled state as module views."""
    garden = {"total_pots": len(state["pots"]), "ready_pots": [], "needs_water_pots": [],
              "pest_pots": [], "empty_pots": [], "withered_pots": [], "growing_count": 0}
    groups = {"ready": "ready_pots", "needs_water": "needs_water_pots", "pest_blocked": "pest_pots",
              "empty": "empty_pots", "withered": "withered_pots"}
    for index, pot in enumerate(state["pots"]):
        status = ge.get_pot_ai_status(state, index, pot)
        if status in groups:
            garden[groups[status]].append(index + 1)
        elif status == "growing":
            garden["growing_count"] += 1
    inventory = state["inventory"]
    seeds = {fid: count for fid, count in inventory["seeds"].items() if count > 0}
    shop = ge.get_flower_shop_public_summary(state, now)
    cottage = ge.get_cottage_public_summary(state)
    result = {
        "garden_name": state.get("garden_name", ""), "money": state["money"], "server_now": now,
        "weather": state["weather"], "weather_name": ge.WEATHER[state["weather"]]["name"],
        "garden": garden,
        "inventory": {"seeds": seeds, "seed_total": sum(seeds.values()),
                      "flower_total": sum(count for count in inventory["flowers"].values() if count > 0),
                      "items": {iid: count for iid, count in inventory["items"].items() if count > 0}},
        "encyclopedia": {"recorded": len(state["encyclopedia"]), "capacity": len(ge.FLOWERS)},
        "collectibles": {"owned": ge.get_collectible_unique_count(state), "capacity": len(ge.CAT_COLLECTIBLES)},
        "letters_received": len(state["letters_received"]),
        "flower_shop": _pick(shop, "established", "launched", "is_open", "shelf_capacity", "occupied_slots", "empty_slots"),
        "cottage": {"owned_count": cottage["total_owned"],
                    "food_remaining": state["cat_care"]["food_bowl"]["remaining_portions"],
                    "water_remaining": state["cat_care"]["water_bowl"]["remaining_portions"]},
    }
    _navigation(result, [{"section": section} for section in VIEW_DETAILS])
    if cat_summary:
        result["cat"] = _pick(cat_summary, "name", "stage", "location", "is_present", "hunger", "thirst", "mood", "affection", "max_affection")
    return result


def build_view(state, section, now, *, detail=None, item_id=None, page=None):
    """No normalization, settlement, random decisions, writes, or clock reads here."""
    validate_view(section, detail, item_id, page)
    result = {"ok": True, "section": section}
    views = []

    if section == "garden":
        if item_id is not None:
            pots = [{"id": str(index + 1), "slot": index + 1,
                     "status": ge.get_pot_ai_status(state, index, pot)}
                    for index, pot in enumerate(state["pots"])]
            row = _item(pots, item_id)
            pot = state["pots"][row["slot"] - 1]
            result["item"] = {**row, **(_pick(pot, "flower_id", "growth_progress", "watered") if pot else {})}
        elif detail == "vase":
            result["items"] = []
            for i, entry in enumerate(state.get("vase", [])):
                status, _, remaining = ge.get_vase_flower_status(entry, now)
                result["items"].append({"slot": i + 1, "flower_id": entry["flower_id"],
                                        "status": status, "remaining_seconds": remaining})
        else:
            projected_pots = build_garden_pots(state)
            items = []
            for row in projected_pots:
                item = {"slot": row["slot"], "status": row["status"]}
                if row["flower_id"] is not None:
                    item["flower_id"] = row["flower_id"]
                if row["status"] == "growing" and row["remaining_seconds"] is not None:
                    item["remaining_seconds"] = row["remaining_seconds"]
                if row["status"] == "pest_blocked":
                    item["watered"] = row["watered"]
                items.append(item)
            result.update(items=items, summary={"vase_count": len(state.get("vase", [])),
                                              "vase_capacity": ge.VASE_CAPACITY})
            views = [_entry(detail="vase")]

    elif section == "cat":
        cat = state.get("cat_state", {})
        present = ge._is_cat_present_for_interaction(state)
        cooldown = max(0, int(state.get("cat_last_pet_real_time", 0)) + ge.PET_COOLDOWN_REAL_MINUTES * 60 - now)
        stock = state["inventory"]["items"]
        care = _care(state)
        interactions = []
        if present:
            if not cooldown:
                interactions.append("pet")
            for command, iid in (("play ball", "ball"), ("play feather", "feather_wand"),
                                 ("give_treat", ge.CAT_TREAT_ITEM_ID)):
                if stock.get(iid, 0) > 0:
                    interactions.append(command)
        if state.get("cat") is not None:
            if care["water_bowl"].get("remaining_portions", 0) < care["water_bowl"].get("capacity", 0):
                interactions.append("give_water")
            if care["food_bowl"].get("remaining_portions", 0) < care["food_bowl"].get("capacity", 0):
                interactions.extend(f"feed {kind}" for kind, iid in ge.CAT_CARE_FOOD_TYPES.items() if stock.get(iid, 0) > 0)
        if cat.get("phase") == ge.CAT_PHASE_WAITING_NAME:
            interactions.append("adopt")
        result.update(summary={"name": ge.get_current_cat_name(state), "stage": cat.get("phase"),
                               "location": cat.get("location"), "is_present": present,
                               "stats": _pick(cat.get("stats", {}), "hunger", "thirst", "mood", "affection"),
                               "pet_cooldown_seconds": cooldown},
                      care=care, available_interactions=interactions)

    elif section == "inventory":
        categories = {key: [{"id": iid, "quantity": qty} for iid, qty in state["inventory"].get(key, {}).items() if qty > 0]
                      for key in ("seeds", "flowers", "items")}
        categories["bouquets"] = ge.get_bouquet_inventory_public(state)
        if detail:
            result["items"] = categories[detail]
        else:
            result["summary"] = {key: {"types": len(rows), "quantity": sum(row.get("quantity", 1) for row in rows)}
                                 for key, rows in categories.items() if key != "flowers"}
            result["flowers"] = [
                {"flower_id": flower_id, "count": count}
                for flower_id, count in state["inventory"].get("flowers", {}).items()
                if count > 0
            ]
            views = [_entry(detail=key) for key in categories]

    elif section == "collectibles":
        owned = [{"id": item["id"], "name": item["name"], "quantity": state["collectibles"][item["id"]]}
                 for item in ge.CAT_COLLECTIBLES if state["collectibles"].get(item["id"], 0) > 0]
        if item_id is not None:
            row = _item(owned, item_id)
            definition = next(item for item in ge.CAT_COLLECTIBLES if item["id"] == item_id)
            result["item"] = {**row, **_pick(definition, "description", "rarity"),
                              "first_found_at": state.get("collectible_first_found", {}).get(item_id, 0)}
        elif detail == "rules":
            result["summary"] = {"unlocked": ge.are_cat_collectibles_unlocked(state),
                                 "rule": "首次实际吃喝后开启；完整来访结束或外出回家时可能带回，允许重复。"}
        else:
            result.update(summary={"owned": len(owned), "capacity": len(ge.CAT_COLLECTIBLES)}, items=owned)
            views = [_entry(item_id=row["id"]) for row in owned] + [_entry(detail="rules")]

    elif section == "encyclopedia":
        known = [{"id": fid, "name": ge.FLOWERS[fid]["name"]}
                 for fid in state["encyclopedia"] if fid in ge.FLOWERS]
        if item_id is not None:
            result["item"] = {**_item(known, item_id),
                              **_pick(ge.FLOWERS[item_id], "rarity"),
                              "harvests": state.get("flower_harvest_counts", {}).get(item_id, 0)}
        else:
            result.update(summary={"recorded": len(known), "capacity": len(ge.FLOWERS)}, items=known)
            views = [_entry(item_id=row["id"]) for row in known]

    elif section == "flower_shop":
        shop = ge.get_flower_shop_public_summary(state, now)
        fields = {
            None: ("established", "launched", "is_open", "shelf_capacity", "occupied_slots", "empty_slots"),
            "eligibility": (),
            "hours": ("business_start_minute", "business_duration_minutes", "pending_business_start_minute",
                      "pending_business_effective_at", "is_open", "next_business_cycle_at"),
            "shelves": ("shelf_capacity", "slots", "can_upgrade_shelf", "next_shelf_capacity", "next_shelf_upgrade_cost"),
            "equipment": ("has_freshener", "freshener_cost", "shop_buff_active", "shop_buff_remaining_seconds", "shop_buff_effect"),
            "rules": ("pricing_profiles", "bouquet_lifetime_seconds"),
        }
        if detail == "eligibility":
            eligibility = ge.get_flower_shop_eligibility_summary(state)
            result["summary"] = {
                "eligible": eligibility["eligible"],
                "requirements": eligibility["requirements"],
            }
        else:
            result["summary"] = _pick(shop, *fields[detail])
        if detail is None:
            views = [_entry(detail=key) for key in fields if key is not None]

    elif section == "cottage":
        owned = [{"id": iid, "name": ge.COTTAGE_ITEM_CATALOG[iid]["name"]}
                 for iid in state.get("cottage", {}).get("items", {})
                 if iid in ge.COTTAGE_ITEM_CATALOG and not ge.COTTAGE_ITEM_CATALOG[iid].get("legacy_only")]
        if item_id is not None:
            row = _item(owned, item_id)
            result["item"] = {**row, **_pick(ge.COTTAGE_ITEM_CATALOG[item_id], "description", "category"),
                              **_pick(state["cottage"]["items"][item_id], "source", "acquired_at")}
        elif detail == "cat_area":
            result["summary"] = _care(state)
        else:
            result.update(summary={"owned": len(owned)}, items=owned)
            if detail is None:
                result["summary"]["cat_area"] = {key: _pick(value, "remaining_portions", "capacity")
                                                      for key, value in _care(state).items() if key != "bed"}
            views = [_entry(item_id=row["id"]) for row in owned]
            if detail is None:
                views += [_entry(detail="cat_area")]

    elif section == "bouquets":
        options = ge.get_bouquet_options(state)
        recipes = [{"id": row["bouquet_id"], **_pick(row, "name", "can_make")}
                   for row in options]
        for recipe, option in zip(recipes, options):
            if not option["can_make"]:
                recipe["missing"] = [
                    {"flower_id": flower_id, "count": count}
                    for flower_id, count in option["missing"].items()
                ]
        if item_id is not None:
            row = _item(recipes, item_id)
            option = next(row for row in options if row["bouquet_id"] == item_id)
            result["item"] = {**row, **_pick(option, "components", "missing")}
        elif detail == "inventory":
            result["items"] = ge.get_bouquet_inventory_public(state)
        else:
            result.update(summary={"discovered": len(recipes), "inventory_count": len(state.get("bouquet_inventory", []))}, items=recipes)
            views = [_entry(item_id=row["id"]) for row in recipes] + [_entry(detail="inventory")]

    elif section == "letters":
        received = [{"id": str(index + 1), "number": index + 1, "title": ge.CAT_LETTERS[index]["title"]}
                    for index in state.get("letters_received", [])]
        if item_id is not None:
            row = _item(received, item_id)
            result["item"] = {**row, "text": ge.CAT_LETTERS[row["number"] - 1]["text"]}
        else:
            result.update(summary={"received": len(received), "capacity": len(ge.CAT_LETTERS)}, items=received)
            views = [_entry(item_id=row["id"]) for row in received]

    elif section == "journal":
        records = state.get("events", [])[-ge.EVENT_HISTORY_LIMIT:]
        page = page or 1
        pages = max(1, (len(records) + JOURNAL_PAGE_SIZE - 1) // JOURNAL_PAGE_SIZE)
        result["summary"] = {"retention_limit": ge.EVENT_HISTORY_LIMIT, "retained": len(records),
                             "page": page, "page_size": JOURNAL_PAGE_SIZE, "total_pages": pages,
                             "order": "newest_first"}
        result["items"] = []
        for event in list(reversed(records))[(page - 1) * JOURNAL_PAGE_SIZE:page * JOURNAL_PAGE_SIZE]:
            row = _pick(event, "source", "source_name", "area", "text", "time")
            if event.get("source"):
                row["source_label"] = ge.get_event_source_label(event["source"])
            result["items"].append(row)
        views = [_entry(page=p) for p in (page - 1, page + 1) if 1 <= p <= pages]

    elif section == "shop":
        goods = _goods(state)
        if item_id is not None:
            result["item"] = _item([row for rows in goods.values() for row in rows], item_id)
        elif detail:
            result["items"] = goods[detail]
        else:
            result["summary"] = {key: len(rows) for key, rows in goods.items() if key != "seeds"}
            result["seeds"] = [
                {"id": row["id"], **_pick(row, "seed_price", "grow_time", "sell_price")}
                for row in goods["seeds"]
            ]
            views = [_entry(detail=key) for key in goods if key != "seeds"]

    _navigation(result, [{"section": section, **view} for view in views])
    return result
