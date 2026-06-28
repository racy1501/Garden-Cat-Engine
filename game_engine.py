"""
花园与猫咪 v4.8.10 - API与网页兼容游戏引擎
支持独立存档 API、可视化网页与本地单文件运行

v4.8.10 更新：
- 天气生长倍率重平衡：晴天1.1 / 雨天1.2 / 多云1.0
- 网页状态摘要新增游戏时间、天气倍率、花盆当前倍率与摸猫冷却

v4.8.3 更新：
- 猫咪支持自定义名字：adopt <名字>，不填则默认“小猫”
- 新增 rename_cat <名字>，收养后可随时改名
- 猫名最长12个字符，AI接口与可视化网页共用同一套规则
- 网页收藏页可展开阅读已收到的猫咪信件

v4.8.2 更新：
- 新增人类玩家可视化网页，游戏数值与玩法规则保持不变
- 人类网页与 AI 接口并存，不同花园默认使用独立存档
- 网页花园使用专属钥匙鉴权，不在前端暴露全局 API Key

v4.8.1 更新：
- 花瓶鲜花保鲜时间由现实24小时调整为现实12小时
- 新增 remove_vase <位置>：可移除花瓶中任意状态的花
- 新鲜、微蔫、即将枯萎或已枯萎的花都可主动移除
- 从花瓶移除后不返还花朵，也不返还金币
- 移除 clear_vase 命令，统一使用 remove_vase 管理花瓶位置
- 兼容 v4.8.0 及更早存档

v4.8.0 更新：
- 新增花瓶系统：最多插入3朵已收获鲜花，插花后不可出售
- 花瓶鲜花按现实时间保鲜24小时，依次显示新鲜、微微蔫、即将枯萎和已枯萎
- 当时新增 arrange、vase、clear_vase 命令，用于插花、查看花瓶和清理枯花
- 虫害致死后不再自动清空花盆，改为保留枯萎花朵等待清理
- 新增 clear <盆号>：清理枯萎花，50%概率获得种子价格一半的金币（奇数向下取整）
- 枯萎花盆无法种植、浇水、治疗或收获，必须先手动清理
- 修复旧存档补齐花盆列表时可能多追加一个空花盆的问题
- 兼容 v4.7.0 及更早存档

v4.7.0 更新：
- 新增花卉分层解锁：普通花开局开放，图鉴2/5/7种时解锁更高稀有度花卉
- 商店会显示未解锁花卉及解锁条件，购买和种植均会校验解锁状态
- 达到新图鉴阶段时会提示新花卉已解锁
- 重复获得永久图鉴奖励时，按该物品商店原价全额折算金币
- 害虫死亡倒计时延长为10分钟现实时间
- 猫咪饱食、口渴、心情、亲密度的被动衰减最低停在20，减少长期离线压力
- 明确天气采用惰性结算：到期后在下一次游戏指令时变化一次，离线期间不补算多轮天气
- 兼容 v4.6.8 及更早存档

v4.6.8 更新：
- 害虫改为每5分钟最多检查一次，不再因高频互动增加判定次数
- 已经成熟的花不再触发新的虫害
- 离线期间不会补算多轮新虫害，回来后仅在冷却到期时检查一次
- 兼容旧版 last_pest_check_time 的游戏小时记录
- 兼容 v4.6.7 及更早存档

v4.6.7 更新：
- 花朵改为累计有效生长进度，未浇水时间不再被补算
- 天气速度只影响对应时间段，切换天气后进度不会倒退或追溯变化
- 修复 pest_treatment 的整数键被 JSON 转成字符串后保护失效的问题
- 修复负数/零数量购买造成刷钱、无限种植的问题
- 为蝴蝶、收集品和信件增加真正的检查冷却，无法靠刷命令反复抽取
- 天气变化前先结算猫咪状态，避免新天气追溯影响全部离线时间
- 补全花盆编号、数量、空命令和错误参数校验，避免越界或格式崩溃
- feed/play 仅接受有效选项，不再把任意文字当成高级猫粮或逗猫棒
- 永久物品只购买一份，避免多付钱只得到一个
- 月光花奖励在尚未收养猫咪时会保存，收养后自动生效
- 状态页按猫窝实际效果显示心情变化，并移除重复摘要
- 兼容 v4.6.6 及更早存档
"""
import json
import time
import os
import random
from datetime import datetime

# 游戏数据
FLOWERS = {
    "daisy": {"name": "雏菊", "rarity": "common", "seed_price": 3, "sell_price": 10, "grow_time": 180},
    "tulip": {"name": "郁金香", "rarity": "common", "seed_price": 4, "sell_price": 15, "grow_time": 240},
    "sunflower": {"name": "向日葵", "rarity": "common", "seed_price": 5, "sell_price": 20, "grow_time": 300},
    "rose": {"name": "玫瑰", "rarity": "common", "seed_price": 6, "sell_price": 28, "grow_time": 360},
    "lavender": {"name": "薰衣草", "rarity": "uncommon", "seed_price": 10, "sell_price": 40, "grow_time": 480},
    "lily": {"name": "百合", "rarity": "uncommon", "seed_price": 12, "sell_price": 55, "grow_time": 540},
    "cherry": {"name": "樱花", "rarity": "rare", "seed_price": 20, "sell_price": 80, "grow_time": 600},
    "moonflower": {"name": "月光花", "rarity": "legendary", "seed_price": 50, "sell_price": 130, "grow_time": 720},
}


# 图鉴数量达到要求后开放购买和种植；已收录过的花始终保持解锁，兼容旧存档。
FLOWER_UNLOCK_REQUIREMENTS = {
    "daisy": 0,
    "tulip": 0,
    "sunflower": 0,
    "rose": 0,
    "lavender": 2,
    "lily": 2,
    "cherry": 5,
    "moonflower": 7,
}

ENCYCLOPEDIA_REWARDS = {
    "daisy": {"seeds": {"daisy": 3}},
    "tulip": {"items": {"basic_food": 2}},
    "sunflower": {"permanent": "water_bowl"},
    "rose": {"items": {"premium_food": 5}},
    "lavender": {"items": {"ball": 1}},
    "lily": {"permanent": "cat_bed"},
    "cherry": {"items": {"feather_wand": 1}},
    "moonflower": {"cat_mood": 30},
}

ITEMS = {
    "basic_food": {"name": "普通猫粮", "price": 5, "type": "consumable", "effect": {"hunger": 30}},
    "premium_food": {"name": "高级猫粮", "price": 15, "type": "consumable", "effect": {"hunger": 60, "mood": 10}},
    "water_bowl": {"name": "水碗", "price": 10, "type": "permanent", "effect": {"thirst_decay": -0.5}},
    "cat_bed": {"name": "猫窝", "price": 30, "type": "permanent", "effect": {"mood_decay": -0.3}},
    "ball": {"name": "毛线球", "price": 8, "type": "toy", "effect": {"mood": 15, "affection": 5}},
    "feather_wand": {"name": "逗猫棒", "price": 12, "type": "toy", "effect": {"mood": 20, "affection": 8}},
}

# v4.6.6: 天气系统 - 浇水开关版
# 雨天生长最快并自动浇水；晴天小幅加速且需手动浇水；多云为标准速度
WEATHER = {
    "sunny": {"name": "晴天", "emoji": "☀️", "grow_speed": 1.1, "cat_mood_change": 1.5},
    "rainy": {"name": "下雨", "emoji": "🌧️", "grow_speed": 1.2, "cat_mood_change": -1.5, "auto_water": True},
    "cloudy": {"name": "多云", "emoji": "☁️", "grow_speed": 1.0, "cat_mood_change": 0},
}

WEATHER_CHANGE_MIN = 300
WEATHER_CHANGE_MAX = 600

# v4.6.5: 心情基础衰减（/真实小时）
MOOD_BASE_DECAY = 0.5

# v4.6.5: 亲密度衰减（/真实小时）
AFFECTION_NATURAL_DECAY = 0.5
AFFECTION_STATUS_DECAY = 2.0

# v4.6.5: 抚摸冷却（真实分钟）
PET_COOLDOWN_REAL_MINUTES = 10

# v4.6: 游戏时间转换
GAME_HOURS_PER_REAL_HOUR = 96

# v4.7: 害虫死亡时间（真实分钟）
PEST_DEATH_REAL_MINUTES = 10

# 猫咪收集品
CAT_COLLECTIBLES = [
    {"id": "shell", "name": "贝壳", "emoji": "🐚"},
    {"id": "maple_leaf", "name": "枫叶", "emoji": "🍁"},
    {"id": "pine_needle", "name": "松针", "emoji": "🌲"},
    {"id": "clover", "name": "四叶草", "emoji": "🍀"},
    {"id": "wildflower", "name": "野花", "emoji": "🌺"},
]

# 猫咪信件（按亲密度顺序）
CAT_LETTERS = [
    {"min_affection": 0, "text": "喵。（这张纸条上只有一个爪印）"},
    {"min_affection": 20, "text": "...喵。（纸条上有歪歪扭扭的字：你...还行）"},
    {"min_affection": 40, "text": "今天的花开得不错。——猫"},
    {"min_affection": 60, "text": "谢谢你每天来看我。——猫"},
    {"min_affection": 80, "text": "你是我最重要的人。永远。——猫"},
]

POT_UNLOCK_COSTS = {4: 20, 5: 35, 6: 50}
MAX_POTS = 6
PEST_TREATMENT_COST = 3

CAT_ADOPT_COST = 100
CAT_NAME_MAX_LENGTH = 12
SAVE_FILE = "garden_cat_save.json"

BUTTERFLY_CHECK_INTERVAL = 300
COLLECTIBLE_CHECK_INTERVAL = 300
LETTER_CHECK_INTERVAL = 300
PEST_CHECK_INTERVAL = 300
TREATMENT_PROTECTION_SECONDS = 365 * 24 * 3600
CAT_PASSIVE_STAT_FLOOR = 20.0

VASE_CAPACITY = 3
VASE_LIFESPAN_REAL_HOURS = 12
VASE_LIFESPAN_SECONDS = VASE_LIFESPAN_REAL_HOURS * 3600
WITHERED_CLEAR_REWARD_CHANCE = 0.50


def get_next_pot_cost(state):
    """返回解锁下一个花盆所需金币；达到上限时返回 None。"""
    next_pot_number = int(state.get("max_pots", 3)) + 1
    return POT_UNLOCK_COSTS.get(next_pot_number)


def normalize_cat_name(raw_name, default="小猫"):
    """整理并校验猫咪名字；返回 None 表示名字不合法。"""
    if raw_name is None:
        return default
    name = " ".join(str(raw_name).strip().split())
    if not name:
        return default
    if len(name) > CAT_NAME_MAX_LENGTH:
        return None
    if any(ord(char) < 32 for char in name):
        return None
    return name


def get_default_state():
    now = int(time.time())
    return {
        "money": 50,
        "pots": [None, None, None],
        "max_pots": 3,
        "inventory": {
            "seeds": {},
            "flowers": {},
            "items": {},
        },
        "cat": None,
        "cat_stats": None,
        "permanent_items": [],
        "last_update": now,
        "cat_last_pet": 0,
        "encyclopedia": [],
        "total_earned": 0,
        "weather": "sunny",
        "weather_change_time": now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX),
        "events": [],
        "pest_treatment": {},
        "collectibles": {},
        "letters_received": [],
        "last_letter_check": now,
        "last_collectible_check": now,
        "last_butterfly_check": now,
        "game_start_time": now,
        "cat_last_pet_real_time": 0,
        "last_pest_check_time": now,
        "pending_cat_mood_bonus": 0,
        "vase": [],
    }


def get_game_hours(state, now=None):
    if now is None:
        now = int(time.time())
    elapsed_real_seconds = max(0, now - state.get("game_start_time", now))
    elapsed_real_hours = elapsed_real_seconds / 3600
    return elapsed_real_hours * GAME_HOURS_PER_REAL_HOUR


def _positive_inventory(raw):
    cleaned = {}
    if not isinstance(raw, dict):
        return cleaned
    for key, value in raw.items():
        try:
            quantity = int(value)
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            cleaned[str(key)] = quantity
    return cleaned


def normalize_state(data, now=None):
    """补齐旧存档字段，并修复 JSON 字典键类型。"""
    if now is None:
        now = int(time.time())
    if not isinstance(data, dict):
        return get_default_state()

    defaults = get_default_state()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value

    try:
        data["money"] = max(0, int(data.get("money", 0)))
    except (TypeError, ValueError):
        data["money"] = 0

    try:
        data["max_pots"] = int(data.get("max_pots", 3))
    except (TypeError, ValueError):
        data["max_pots"] = 3
    data["max_pots"] = min(MAX_POTS, max(3, data["max_pots"]))

    if not isinstance(data.get("pots"), list):
        data["pots"] = []
    data["pots"] = data["pots"][:data["max_pots"]]
    while len(data["pots"]) < data["max_pots"]:
        data["pots"].append(None)

    inventory = data.get("inventory")
    if not isinstance(inventory, dict):
        inventory = {}
    data["inventory"] = {
        "seeds": _positive_inventory(inventory.get("seeds", {})),
        "flowers": _positive_inventory(inventory.get("flowers", {})),
        "items": _positive_inventory(inventory.get("items", {})),
    }

    if data.get("weather") not in WEATHER:
        data["weather"] = "sunny"
    weather_data = WEATHER[data["weather"]]

    try:
        data["weather_change_time"] = int(data.get("weather_change_time", now))
    except (TypeError, ValueError):
        data["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)

    try:
        data["game_start_time"] = int(data.get("game_start_time", now))
    except (TypeError, ValueError):
        data["game_start_time"] = now
    try:
        data["last_update"] = int(data.get("last_update", now))
    except (TypeError, ValueError):
        data["last_update"] = now

    for field in (
        "cat_last_pet_real_time",
        "last_letter_check",
        "last_collectible_check",
        "last_butterfly_check",
        "last_pest_check_time",
        "pending_cat_mood_bonus",
        "total_earned",
    ):
        try:
            data[field] = int(data.get(field, defaults[field]))
        except (TypeError, ValueError):
            data[field] = defaults[field]

    # 旧版检查时间为0时，从本次加载开始计时，避免连续刷命令抽事件。
    for field in ("last_letter_check", "last_collectible_check", "last_butterfly_check"):
        if data[field] <= 0:
            data[field] = now

    # v4.6.7 及更早版本把害虫检查时间保存为“游戏小时”整数。
    # 这类数值远小于 Unix 时间戳，迁移时从当前时刻重新开始5分钟冷却。
    if data["last_pest_check_time"] < 1_000_000_000:
        data["last_pest_check_time"] = now

    if not isinstance(data.get("events"), list):
        data["events"] = []
    data["events"] = data["events"][-5:]

    if not isinstance(data.get("permanent_items"), list):
        data["permanent_items"] = []
    data["permanent_items"] = [item for item in data["permanent_items"] if item in ITEMS]

    if not isinstance(data.get("encyclopedia"), list):
        data["encyclopedia"] = []
    data["encyclopedia"] = list(dict.fromkeys(fid for fid in data["encyclopedia"] if fid in FLOWERS))

    if not isinstance(data.get("collectibles"), dict):
        data["collectibles"] = {}
    data["collectibles"] = _positive_inventory(data["collectibles"])

    if not isinstance(data.get("letters_received"), list):
        data["letters_received"] = []
    valid_letters = []
    for idx in data["letters_received"]:
        try:
            idx = int(idx)
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(CAT_LETTERS) and idx not in valid_letters:
            valid_letters.append(idx)
    data["letters_received"] = sorted(valid_letters)

    # JSON 会把整数键写成字符串；加载时恢复为整数。
    treatments = {}
    raw_treatments = data.get("pest_treatment", {})
    if isinstance(raw_treatments, dict):
        for key, value in raw_treatments.items():
            try:
                pot_idx = int(key)
                expiry = int(value)
            except (TypeError, ValueError):
                continue
            if 0 <= pot_idx < data["max_pots"]:
                treatments[pot_idx] = expiry
    data["pest_treatment"] = treatments

    # v4.8.0：兼容旧存档并清理无效花瓶数据。
    vase_entries = []
    raw_vase = data.get("vase", [])
    if isinstance(raw_vase, list):
        for entry in raw_vase:
            if not isinstance(entry, dict):
                continue
            flower_id = entry.get("flower_id")
            if flower_id not in FLOWERS:
                continue
            try:
                arranged_time = int(entry.get("arranged_time", now))
            except (TypeError, ValueError):
                arranged_time = now
            vase_entries.append({
                "flower_id": flower_id,
                "arranged_time": min(now, arranged_time),
            })
            if len(vase_entries) >= VASE_CAPACITY:
                break
    data["vase"] = vase_entries

    for i, pot in enumerate(data["pots"]):
        if not isinstance(pot, dict) or pot.get("flower_id") not in FLOWERS:
            data["pots"][i] = None
            data["pest_treatment"].pop(i, None)
            continue

        flower_id = pot["flower_id"]
        try:
            planted_time = int(pot.get("planted_time", now))
        except (TypeError, ValueError):
            planted_time = now
        pot["planted_time"] = planted_time
        pot["watered"] = bool(pot.get("watered", True))
        pot["withered"] = bool(pot.get("withered", False))
        if pot["withered"]:
            try:
                pot["withered_time"] = int(pot.get("withered_time", now))
            except (TypeError, ValueError):
                pot["withered_time"] = now
            pot.pop("pest_time", None)
            data["pest_treatment"].pop(i, None)

        if "growth_progress" not in pot:
            # 兼容旧存档：按旧版当前显示方式估算一次已有进度。
            elapsed = max(0, now - planted_time)
            speed = weather_data["grow_speed"] if pot["watered"] else 0
            pot["growth_progress"] = min(FLOWERS[flower_id]["grow_time"], elapsed * speed)
            pot["last_growth_update"] = now
        else:
            try:
                pot["growth_progress"] = float(pot["growth_progress"])
            except (TypeError, ValueError):
                pot["growth_progress"] = 0.0
            pot["growth_progress"] = min(
                FLOWERS[flower_id]["grow_time"],
                max(0.0, pot["growth_progress"]),
            )
            try:
                pot["last_growth_update"] = int(pot.get("last_growth_update", now))
            except (TypeError, ValueError):
                pot["last_growth_update"] = now

        if "pest_time" in pot:
            try:
                pot["pest_time"] = int(pot["pest_time"])
            except (TypeError, ValueError):
                pot.pop("pest_time", None)

    if data.get("cat") is None:
        data["cat"] = None
        data["cat_stats"] = None
    else:
        if not isinstance(data.get("cat"), dict):
            data["cat"] = {"name": "小猫"}
        normalized_name = normalize_cat_name(data["cat"].get("name"), default="小猫")
        data["cat"]["name"] = normalized_name or "小猫"
        stats = data.get("cat_stats")
        if not isinstance(stats, dict):
            stats = {"hunger": 70, "thirst": 70, "mood": 60, "affection": 10}
        for stat, default_value in (("hunger", 70), ("thirst", 70), ("mood", 60), ("affection", 10)):
            try:
                stats[stat] = float(stats.get(stat, default_value))
            except (TypeError, ValueError):
                stats[stat] = float(default_value)
            stats[stat] = min(100.0, max(0.0, stats[stat]))
        data["cat_stats"] = stats

    return data


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return normalize_state(json.load(f))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        backup_file = SAVE_FILE + ".backup"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_data = normalize_state(json.load(f))
                os.replace(backup_file, SAVE_FILE)
                return backup_data
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return None


def save_game(state):
    state["last_update"] = int(time.time())
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                old_data = f.read()
            with open(SAVE_FILE + ".backup", "w", encoding="utf-8") as f:
                f.write(old_data)
        except OSError:
            pass

    temp_file = SAVE_FILE + ".temp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, SAVE_FILE)
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(SAVE_FILE + ".backup"):
            os.replace(SAVE_FILE + ".backup", SAVE_FILE)
        raise Exception(f"存档保存失败，已从备份恢复：{str(e)}") from e


def new_game():
    state = get_default_state()
    state["inventory"]["items"]["basic_food"] = 3
    save_game(state)
    return (
        "🌱 新游戏开始！你有50块钱，3盆花，3包普通猫粮。\n"
        "先种花赚钱，攒够100块就能收养小猫啦！\n\n"
        "🌤️ 当前天气：晴天 ☀️（花生长×1.1，需手动浇水）"
    )


def format_time(seconds):
    seconds = max(0, int(round(seconds)))
    if seconds < 60:
        return f"{seconds}秒"
    if seconds < 3600:
        return f"{seconds // 60}分{seconds % 60}秒"
    return f"{seconds // 3600}小时{(seconds % 3600) // 60}分"


def parse_positive_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def get_pot_index(value, state):
    number = parse_positive_int(value)
    if number is None or number > state["max_pots"]:
        return None
    return number - 1


def get_flower_unlock_requirement(flower_id):
    return int(FLOWER_UNLOCK_REQUIREMENTS.get(flower_id, 0))


def is_flower_unlocked(state, flower_id):
    if flower_id not in FLOWERS:
        return False
    if flower_id in state.get("encyclopedia", []):
        return True
    return len(state.get("encyclopedia", [])) >= get_flower_unlock_requirement(flower_id)


def get_unlock_message(flower_id):
    return f"图鉴达到{get_flower_unlock_requirement(flower_id)}种后解锁"


def get_stage_unlocks(before_count, after_count, encyclopedia_before):
    newly_unlocked = []
    known_before = set(encyclopedia_before)
    for flower_id, requirement in FLOWER_UNLOCK_REQUIREMENTS.items():
        if requirement <= 0 or flower_id in known_before:
            continue
        if before_count < requirement <= after_count:
            newly_unlocked.append(FLOWERS[flower_id]["name"])
    return newly_unlocked


def is_pot_withered(pot):
    return isinstance(pot, dict) and bool(pot.get("withered", False))


def get_vase_flower_status(entry, now):
    arranged_time = int(entry.get("arranged_time", now))
    elapsed = max(0, now - arranged_time)
    remaining = max(0, VASE_LIFESPAN_SECONDS - elapsed)
    ratio = elapsed / VASE_LIFESPAN_SECONDS if VASE_LIFESPAN_SECONDS > 0 else 1.0

    if elapsed >= VASE_LIFESPAN_SECONDS:
        return "🥀 已枯萎", 100, 0
    if ratio < 0.50:
        label = "🌸 新鲜"
    elif ratio < 0.83:
        label = "🌷 微微蔫"
    else:
        label = "🍂 即将枯萎"
    wither_pct = min(99, int(ratio * 100))
    return label, wither_pct, remaining


def get_vase_status(state, now=None):
    if now is None:
        now = int(time.time())
    vase = state.get("vase", [])
    lines = [f"💐 花瓶（{len(vase)}/{VASE_CAPACITY}）"]
    if not vase:
        lines.append("  空，等待一束喜欢的花")
        return "\n".join(lines)

    for idx, entry in enumerate(vase, start=1):
        flower_id = entry["flower_id"]
        label, wither_pct, remaining = get_vase_flower_status(entry, now)
        if remaining > 0:
            lines.append(
                f"  {idx}. {FLOWERS[flower_id]['name']} - {label} "
                f"（枯萎度{wither_pct}%，约{format_time(remaining)}后枯萎）"
            )
        else:
            lines.append(f"  {idx}. {FLOWERS[flower_id]['name']} - {label}（可移除）")
    return "\n".join(lines)


def get_actual_grow_speed(pot, weather_data):
    if is_pot_withered(pot) or not pot.get("watered", True):
        return 0.0
    return weather_data["grow_speed"]


def update_flower_growth(state, now, weather_data):
    """只累计实际处于浇水状态下的有效生长进度。"""
    for pot in state["pots"]:
        if pot is None or is_pot_withered(pot):
            continue
        flower_id = pot["flower_id"]
        grow_time = FLOWERS[flower_id]["grow_time"]
        try:
            last_update = int(pot.get("last_growth_update", now))
        except (TypeError, ValueError):
            last_update = now
        elapsed = max(0, now - last_update)
        progress = float(pot.get("growth_progress", 0.0))
        if pot.get("watered", True) and progress < grow_time:
            progress += elapsed * weather_data["grow_speed"]
        pot["growth_progress"] = min(float(grow_time), max(0.0, progress))
        pot["last_growth_update"] = now


def _auto_water_pots(state, now):
    count = 0
    for pot in state["pots"]:
        if pot is not None and not is_pot_withered(pot) and not pot.get("watered", True):
            pot["watered"] = True
            pot["last_growth_update"] = now
            count += 1
    return count


def get_weather_info(state, now):
    weather_id = state["weather"]
    weather_data = WEATHER[weather_id]
    messages = []

    if now >= state["weather_change_time"]:
        old_weather = weather_id
        weathers = ["sunny", "rainy", "cloudy"]
        weathers.remove(old_weather)
        new_weather = random.choice(weathers)

        state["weather"] = new_weather
        state["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)
        new_weather_data = WEATHER[new_weather]
        messages.append(
            f"\n🌤️ 天气变化：{weather_data['emoji']}{weather_data['name']} → "
            f"{new_weather_data['emoji']}{new_weather_data['name']}"
        )

        if new_weather == "rainy":
            auto_watered = _auto_water_pots(state, now)
            if auto_watered > 0:
                messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花，它们开始生长了！")

        if old_weather == "rainy" and new_weather == "sunny" and random.random() < 0.15:
            reward = random.choice([
                {"type": "money", "amount": random.randint(8, 12)},
                {"type": "seeds", "flower": random.choice(["daisy", "tulip"]), "qty": 2},
            ])
            if reward["type"] == "money":
                state["money"] += reward["amount"]
                messages.append(f"🌈 彩虹出现！获得{reward['amount']}块奖励！")
            else:
                flower_id = reward["flower"]
                state["inventory"]["seeds"][flower_id] = (
                    state["inventory"]["seeds"].get(flower_id, 0) + reward["qty"]
                )
                messages.append(f"🌈 彩虹出现！获得{FLOWERS[flower_id]['name']}种子x{reward['qty']}！")
            add_event(state, "彩虹出现")

        weather_data = new_weather_data

    # 兼容旧存档：只要当前正在下雨，就确保所有花已被雨水滋润。
    if weather_data.get("auto_water"):
        auto_watered = _auto_water_pots(state, now)
        if auto_watered > 0:
            messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花，它们开始生长了！")

    if now - state.get("last_butterfly_check", now) >= BUTTERFLY_CHECK_INTERVAL:
        state["last_butterfly_check"] = now
        if random.random() < 0.15:
            messages.append("🦋 一只蝴蝶飞过花园...")
            if random.random() < 0.30:
                gold = random.randint(3, 5)
                state["money"] += gold
                messages.append(f"   💰 蝴蝶掉落了{gold}块金币！")
                add_event(state, f"🦋 蝴蝶掉落了{gold}块金币")
            else:
                add_event(state, "🦋 一只蝴蝶飞过花园")

    if state["cat"] is not None:
        if now - state.get("last_collectible_check", now) >= COLLECTIBLE_CHECK_INTERVAL:
            state["last_collectible_check"] = now
            if random.random() < 0.05:
                collectible = random.choice(CAT_COLLECTIBLES)
                collectible_id = collectible["id"]
                state["collectibles"][collectible_id] = state["collectibles"].get(collectible_id, 0) + 1
                messages.append(f"🎁 小猫带回来了{collectible['emoji']}{collectible['name']}！")
                add_event(state, f"🎁 猫咪带回了{collectible['emoji']}{collectible['name']}")

        if now - state.get("last_letter_check", now) >= LETTER_CHECK_INTERVAL:
            state["last_letter_check"] = now
            if random.random() < 0.10 and len(state["letters_received"]) < len(CAT_LETTERS):
                next_letter_idx = len(state["letters_received"])
                letter = CAT_LETTERS[next_letter_idx]
                current_affection = state["cat_stats"]["affection"]
                if current_affection >= letter["min_affection"]:
                    state["letters_received"].append(next_letter_idx)
                    messages.append("\n✉️ 收到猫咪的一封信！")
                    messages.append(f"   「{letter['text']}」")
                    messages.append(f"   （已收集{len(state['letters_received'])}/5封）")
                    add_event(state, f"✉️ 收到猫咪第{next_letter_idx + 1}封信")

    return weather_data, messages


def add_event(state, event_text):
    state["events"].append({
        "time": int(time.time()),
        "text": event_text,
    })
    if len(state["events"]) > 5:
        state["events"].pop(0)


def check_pests(state, now):
    messages = []

    # 已经存在的虫害死亡倒计时始终按现实时间结算，
    # 不受“每5分钟最多检查一次”的新虫害冷却限制。
    for i, pot in enumerate(state["pots"]):
        if pot is None or "pest_time" not in pot:
            continue
        if now < pot["pest_time"]:
            continue
        if i in state["pest_treatment"] and now < state["pest_treatment"][i]:
            pot.pop("pest_time", None)
            continue
        flower_name = FLOWERS[pot["flower_id"]]["name"]
        pot.pop("pest_time", None)
        pot["withered"] = True
        pot["withered_time"] = now
        pot["watered"] = False
        state["pest_treatment"].pop(i, None)
        messages.append(f"\n💀 盆{i + 1}的{flower_name}被害虫害死，已经枯萎了！")
        messages.append(f"   使用 'clear {i + 1}' 清理花盆")
        add_event(state, f"{flower_name}枯萎（盆{i + 1}）")

    # 新虫害每5分钟最多判定一次。离线再久也只在回来时检查一轮，
    # 不补算错过的次数，避免“越频繁互动越容易长虫”。
    last_pest_check = int(state.get("last_pest_check_time", now))
    if now - last_pest_check < PEST_CHECK_INTERVAL:
        return messages

    state["last_pest_check_time"] = now
    for i, pot in enumerate(state["pots"]):
        if pot is None or is_pot_withered(pot) or "pest_time" in pot:
            continue
        if i in state["pest_treatment"] and now < state["pest_treatment"][i]:
            continue

        flower_id = pot["flower_id"]
        grow_time = FLOWERS[flower_id]["grow_time"]
        growth_progress = float(pot.get("growth_progress", 0.0))

        # 已成熟的花只等待收获，不再发生新的虫害。
        if growth_progress >= grow_time:
            continue

        if random.random() < 0.05:
            pest_death_seconds = PEST_DEATH_REAL_MINUTES * 60
            pot["pest_time"] = now + pest_death_seconds
            messages.append(f"\n🐛 警告：盆{i + 1}的{FLOWERS[flower_id]['name']}长虫子了！")
            messages.append(f"   使用 'treat {i + 1}' 治疗（花费{PEST_TREATMENT_COST}块）")
            messages.append(f"   不治疗的话，花会在{format_time(pest_death_seconds)}后枯萎！")
            add_event(state, f"盆{i + 1}出现害虫")

    return messages


def get_game_time_info(state):
    now = int(time.time())
    elapsed_real_seconds = max(0, now - state.get("game_start_time", now))
    elapsed_real_minutes = elapsed_real_seconds / 60
    game_minutes_total = int(elapsed_real_minutes * 96)
    game_days = game_minutes_total // (24 * 60) + 1
    game_hour = (game_minutes_total // 60) % 24
    game_minute = game_minutes_total % 60
    return game_days, game_hour, game_minute


def get_time_of_day(state):
    game_days, game_hour, _ = get_game_time_info(state)
    if 5 <= game_hour < 7:
        return f"🌅 晨光微亮，花园笼罩在淡金色的光晕中（第{game_days}天）"
    if 7 <= game_hour < 9:
        return f"🌅 日出时分，露珠在花叶上闪闪发光（第{game_days}天）"
    if 17 <= game_hour < 19:
        return f"🌇 夕阳西下，花盆的影子渐渐拉长（第{game_days}天）"
    if 19 <= game_hour < 21:
        return f"🌆 暮色四合，花园笼罩在温柔的橘色余晖中（第{game_days}天）"
    return f"（第{game_days}天）"


def get_status(state, weather_data):
    now = int(time.time())
    elapsed = max(0, now - state["last_update"])
    game_days, game_hour, game_minute = get_game_time_info(state)
    time_of_day_msg = get_time_of_day(state)

    lines = [f"💰 金钱：{state['money']}", f"⏰ 上次更新：{format_time(elapsed)}前"]
    lines.append(f"🌤️ 天气：{weather_data['emoji']} {weather_data['name']}")
    lines.append(f"🕐 游戏时间：第{game_days}天 {game_hour:02d}:{game_minute:02d}")
    lines.append(time_of_day_msg)

    base_speed = weather_data["grow_speed"]
    speed_pct = int(round((base_speed - 1.0) * 100))
    sign = "+" if speed_pct > 0 else ""
    lines.append(f"   花生长速度{sign}{speed_pct}%")
    if weather_data.get("auto_water"):
        lines.append("   🌧️ 雨水自动滋润所有花")

    mood_decay = MOOD_BASE_DECAY
    if "cat_bed" in state["permanent_items"]:
        mood_decay *= 0.6
    net_mood = weather_data["cat_mood_change"] - mood_decay
    mood_text = f"+{net_mood:.1f}" if net_mood > 0 else f"{net_mood:.1f}"
    lines.append(f"   猫咪心情{mood_text}/小时")

    lines.append("\n【花盆】")
    for i, pot in enumerate(state["pots"]):
        if pot is None:
            lines.append(f"  盆{i + 1}: 空")
            continue

        flower_id = pot["flower_id"]
        flower_data = FLOWERS[flower_id]
        if is_pot_withered(pot):
            lines.append(
                f"  盆{i + 1}: 🥀 {flower_data['name']}已枯萎 - 等待清理 "
                f"（使用 clear {i + 1}）"
            )
            continue
        grow_time = flower_data["grow_time"]
        progress_value = min(float(grow_time), float(pot.get("growth_progress", 0.0)))
        progress_pct = min(100, int((progress_value / grow_time) * 100))
        speed = get_actual_grow_speed(pot, weather_data)

        if progress_value >= grow_time:
            status = "🌸 可收获！"
        elif speed <= 0:
            status = f"🏜️ 未浇水，生长暂停（{progress_pct}%）"
        else:
            remaining_real_seconds = (grow_time - progress_value) / speed
            status = f"🌱 {progress_pct}% (还需约{format_time(remaining_real_seconds)})"

        pest_warning = ""
        if "pest_time" in pot and now < pot["pest_time"]:
            if i not in state["pest_treatment"] or now >= state["pest_treatment"].get(i, 0):
                pest_warning = f" 🐛 {format_time(pot['pest_time'] - now)}后枯萎"

        if speed <= 0:
            water_tag = " 💧需浇水"
        elif weather_data.get("auto_water"):
            water_tag = " 🌧️雨水滋润"
        else:
            water_tag = " 💧已浇水"

        lines.append(f"  盆{i + 1}: {flower_data['name']} - {status}{pest_warning}{water_tag}")

    lines.append("\n【花瓶】")
    vase_lines = get_vase_status(state, now).splitlines()
    lines.extend("  " + line if index > 0 else line for index, line in enumerate(vase_lines))

    if state["cat"] is None:
        lines.append(f"\n【猫咪】未收养 (需要{CAT_ADOPT_COST}块)")
        if state.get("pending_cat_mood_bonus", 0) > 0:
            lines.append(f"  🎁 已保存猫咪心情奖励+{state['pending_cat_mood_bonus']}，收养后生效")
    else:
        stats = state["cat_stats"]
        cat_name = state["cat"].get("name", "小猫")
        lines.append(f"\n【猫咪】{cat_name}")
        lines.append(f"  饱食度：{get_bar(stats['hunger'])} {int(stats['hunger'])}")
        lines.append(f"  口渴度：{get_bar(stats['thirst'])} {int(stats['thirst'])}")
        lines.append(f"  心情  ：{get_bar(stats['mood'])} {int(stats['mood'])}")
        lines.append(f"  亲密度：{get_bar(stats['affection'])} {int(stats['affection'])}")
        if "water_bowl" in state["permanent_items"]:
            lines.append("  💧 有水碗")
        if "cat_bed" in state["permanent_items"]:
            lines.append("  🛏️ 有猫窝")

    lines.append("\n【背包】")
    has_any = False
    seeds = {k: v for k, v in state["inventory"]["seeds"].items() if k in FLOWERS and v > 0}
    flowers = {k: v for k, v in state["inventory"]["flowers"].items() if k in FLOWERS and v > 0}
    items = {k: v for k, v in state["inventory"]["items"].items() if k in ITEMS and v > 0}
    if seeds:
        has_any = True
        lines.append("  种子：" + ", ".join(f"{FLOWERS[k]['name']}x{v}" for k, v in seeds.items()))
    if flowers:
        has_any = True
        lines.append("  花：" + ", ".join(f"{FLOWERS[k]['name']}x{v}" for k, v in flowers.items()))
    if items:
        has_any = True
        lines.append("  物品：" + ", ".join(f"{ITEMS[k]['name']}x{v}" for k, v in items.items()))
    if not has_any:
        lines.append("  空")

    lines.append(f"\n📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/8")
    if state["cat"]:
        collectible_count = sum(state["collectibles"].values())
        letter_count = len(state["letters_received"])
        if collectible_count > 0 or letter_count > 0:
            lines.append(f"🎁 收集品{collectible_count}个 ✉️ 信件{letter_count}/5封")

    return "\n".join(lines)


def get_bar(value, max_val=100):
    value = min(float(max_val), max(0.0, float(value)))
    filled = int((value / max_val) * 10)
    empty = 10 - filled
    return "🟩" * filled + "🟥" * empty


def _hours_below_threshold(start_value, decay_per_hour, threshold, elapsed_hours):
    if elapsed_hours <= 0:
        return 0.0
    if start_value < threshold:
        return elapsed_hours
    if decay_per_hour <= 0:
        return 0.0
    crossing_time = (start_value - threshold) / decay_per_hour
    return max(0.0, elapsed_hours - crossing_time)


def update_cat_stats(state, now, weather_data):
    if state["cat"] is None:
        return

    elapsed = max(0, now - state["last_update"])
    if elapsed <= 0:
        return

    hours = elapsed / 3600
    stats = state["cat_stats"]
    start_hunger = stats["hunger"]
    start_thirst = stats["thirst"]

    hunger_decay = 5.0
    thirst_decay = 6.0
    if "water_bowl" in state["permanent_items"]:
        thirst_decay *= 0.5

    hunger_floor = min(CAT_PASSIVE_STAT_FLOOR, start_hunger)
    thirst_floor = min(CAT_PASSIVE_STAT_FLOOR, start_thirst)
    stats["hunger"] = max(hunger_floor, start_hunger - hunger_decay * hours)
    stats["thirst"] = max(thirst_floor, start_thirst - thirst_decay * hours)

    mood_decay = MOOD_BASE_DECAY
    if "cat_bed" in state["permanent_items"]:
        mood_decay *= 0.6
    mood_change = (weather_data["cat_mood_change"] - mood_decay) * hours
    mood_floor = min(CAT_PASSIVE_STAT_FLOOR, stats["mood"])
    stats["mood"] = min(100.0, max(mood_floor, stats["mood"] + mood_change))

    hunger_bad_hours = _hours_below_threshold(start_hunger, hunger_decay, 50, hours)
    thirst_bad_hours = _hours_below_threshold(start_thirst, thirst_decay, 50, hours)
    status_bad_hours = max(hunger_bad_hours, thirst_bad_hours)

    affection_loss = AFFECTION_NATURAL_DECAY * hours
    affection_loss += AFFECTION_STATUS_DECAY * status_bad_hours
    affection_floor = min(CAT_PASSIVE_STAT_FLOOR, stats["affection"])
    stats["affection"] = max(affection_floor, stats["affection"] - affection_loss)

    state["last_update"] = now


def _summary(state):
    text = (
        f"📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/8 "
        f"💐{len(state.get('vase', []))}/{VASE_CAPACITY}"
    )
    if state["cat"]:
        stats = state["cat_stats"]
        cat_name = state["cat"].get("name", "小猫")
        text += (
            f" 🐱{cat_name} 饱{int(stats['hunger'])}渴{int(stats['thirst'])}"
            f"心情{int(stats['mood'])}亲密{int(stats['affection'])}"
        )
    return text



def _harvest_one_pot(state, pot_idx, now, weather_data):
    """收获一个花盆，返回玩家可读结果。"""
    if pot_idx < 0 or pot_idx >= state["max_pots"]:
        return f"❌ 盆号必须是1-{state['max_pots']}"

    pot = state["pots"][pot_idx]
    if pot is None:
        return "❌ 这个盆是空的"
    if is_pot_withered(pot):
        return f"❌ 这盆花已经枯萎，请使用 clear {pot_idx + 1} 清理"
    if "pest_time" in pot and now < pot["pest_time"] and (
        pot_idx not in state["pest_treatment"]
        or now >= state["pest_treatment"].get(pot_idx, 0)
    ):
        return "❌ 花长虫子了！先治疗才能收获"

    flower_id = pot["flower_id"]
    flower_data = FLOWERS[flower_id]
    grow_time = flower_data["grow_time"]
    progress = float(pot.get("growth_progress", 0.0))

    if progress < grow_time:
        if not pot.get("watered", True):
            return "❌ 这盆花还没浇水，生长暂停"
        speed = weather_data["grow_speed"]
        remaining = (grow_time - progress) / speed
        return f"❌ 还没成熟，还需约{format_time(remaining)}"

    state["inventory"]["flowers"][flower_id] = (
        state["inventory"]["flowers"].get(flower_id, 0) + 1
    )
    state["pots"][pot_idx] = None
    state["pest_treatment"].pop(pot_idx, None)

    if flower_id in state["encyclopedia"]:
        return f"🌸 收获了{flower_data['name']}！"

    encyclopedia_before = list(state["encyclopedia"])
    before_count = len(encyclopedia_before)
    state["encyclopedia"].append(flower_id)
    after_count = len(state["encyclopedia"])
    result = f"🎉 收获{flower_data['name']}！图鉴+1！"
    reward = ENCYCLOPEDIA_REWARDS.get(flower_id, {})
    reward_text = []

    for seed_id, qty in reward.get("seeds", {}).items():
        state["inventory"]["seeds"][seed_id] = (
            state["inventory"]["seeds"].get(seed_id, 0) + qty
        )
        reward_text.append(f"{FLOWERS[seed_id]['name']}种子x{qty}")

    for item_id, qty in reward.get("items", {}).items():
        state["inventory"]["items"][item_id] = (
            state["inventory"]["items"].get(item_id, 0) + qty
        )
        reward_text.append(f"{ITEMS[item_id]['name']}x{qty}")

    if "permanent" in reward:
        permanent_id = reward["permanent"]
        if permanent_id not in state["permanent_items"]:
            state["permanent_items"].append(permanent_id)
            reward_text.append(f"{ITEMS[permanent_id]['name']}（永久）")
        else:
            compensation = int(ITEMS[permanent_id]["price"])
            state["money"] += compensation
            reward_text.append(
                f"{ITEMS[permanent_id]['name']}已拥有，折算{compensation}块"
            )

    if "cat_mood" in reward:
        mood_bonus = int(reward["cat_mood"])
        if state["cat"] is not None:
            state["cat_stats"]["mood"] = min(
                100, state["cat_stats"]["mood"] + mood_bonus
            )
            reward_text.append(f"猫咪心情+{mood_bonus}")
        else:
            state["pending_cat_mood_bonus"] += mood_bonus
            reward_text.append(f"猫咪心情+{mood_bonus}（收养后生效）")

    if reward_text:
        result += "\n🎁 解锁奖励：" + ", ".join(reward_text)

    newly_unlocked = get_stage_unlocks(
        before_count,
        after_count,
        encyclopedia_before,
    )
    if newly_unlocked:
        result += "\n🔓 商店新解锁：" + "、".join(newly_unlocked)

    return result



def process_command(state, command):
    """在传入的存档字典上执行命令，并原地更新状态。

    该入口供 Flask API / 数据库存档调用，不读取或写入本地 JSON 文件。
    """
    if not isinstance(state, dict):
        raise TypeError("state 必须是字典")

    if not isinstance(command, str) or not command.strip():
        return "❌ 请输入命令，输入 help 查看帮助"

    parts = command.strip().split()
    action = parts[0].lower()
    now = int(time.time())
    normalize_state(state, now)

    # 先按旧天气结算到当前时刻，再允许天气在此刻变化，避免追溯修改过去。
    previous_weather_data = WEATHER[state["weather"]]
    update_flower_growth(state, now, previous_weather_data)
    update_cat_stats(state, now, previous_weather_data)
    weather_data, weather_messages = get_weather_info(state, now)
    pest_messages = check_pests(state, now)

    result = ""
    all_event_messages = weather_messages + pest_messages

    if action == "shop":
        result = "🏪 商店\n\n【种子】\n"
        for flower_id, flower_data in FLOWERS.items():
            rarity = flower_data["rarity"]
            emoji = "⚪" if rarity == "common" else "🟢" if rarity == "uncommon" else "🔵" if rarity == "rare" else "🟣"
            if is_flower_unlocked(state, flower_id):
                result += (
                    f"  {emoji} {flower_data['name']} - {flower_data['seed_price']}块 "
                    f"({format_time(flower_data['grow_time'])}基础成熟时间, 卖{flower_data['sell_price']}块)\n"
                )
            else:
                result += f"  🔒 {flower_data['name']} - {get_unlock_message(flower_id)}\n"
        result += "\n【猫咪用品】\n"
        for item_data in ITEMS.values():
            result += f"  {item_data['name']} - {item_data['price']}块\n"

    elif action == "buy":
        if len(parts) < 2:
            result = "❌ 要买什么？"
        else:
            item_id = parts[1].lower()
            quantity = 1 if len(parts) < 3 else parse_positive_int(parts[2])
            if quantity is None:
                result = "❌ 购买数量必须是大于0的整数"
            elif len(parts) > 3:
                result = "❌ 用法：buy <物品> [数量]"
            elif item_id in FLOWERS:
                if not is_flower_unlocked(state, item_id):
                    result = f"🔒 {FLOWERS[item_id]['name']}尚未解锁，{get_unlock_message(item_id)}"
                else:
                    price = FLOWERS[item_id]["seed_price"] * quantity
                    if state["money"] < price:
                        result = f"❌ 钱不够！需要{price}块"
                    else:
                        state["money"] -= price
                        state["inventory"]["seeds"][item_id] = state["inventory"]["seeds"].get(item_id, 0) + quantity
                        result = f"✅ 买了{quantity}包{FLOWERS[item_id]['name']}种子！(-{price}块)"
            elif item_id in ITEMS:
                item_data = ITEMS[item_id]
                if item_data["type"] == "permanent":
                    if quantity != 1:
                        result = "❌ 永久物品每次只能购买1个"
                    elif item_id in state["permanent_items"]:
                        result = f"❌ 已经有{item_data['name']}了"
                    elif state["money"] < item_data["price"]:
                        result = f"❌ 钱不够！需要{item_data['price']}块"
                    else:
                        state["money"] -= item_data["price"]
                        state["permanent_items"].append(item_id)
                        result = f"✅ 买了{item_data['name']}！永久生效 (-{item_data['price']}块)"
                else:
                    price = item_data["price"] * quantity
                    if state["money"] < price:
                        result = f"❌ 钱不够！需要{price}块"
                    else:
                        state["money"] -= price
                        state["inventory"]["items"][item_id] = state["inventory"]["items"].get(item_id, 0) + quantity
                        result = f"✅ 买了{quantity}个{item_data['name']}！(-{price}块)"
            else:
                result = "❌ 商店没有这个东西"

    elif action == "plant":
        if len(parts) != 3:
            result = "❌ 用法：plant <花> <盆号>"
        else:
            flower_id = parts[1].lower()
            pot_idx = get_pot_index(parts[2], state)
            if flower_id not in FLOWERS:
                result = "❌ 没有这种花"
            elif not is_flower_unlocked(state, flower_id):
                result = f"🔒 {FLOWERS[flower_id]['name']}尚未解锁，{get_unlock_message(flower_id)}"
            elif pot_idx is None:
                result = f"❌ 盆号必须是1-{state['max_pots']}"
            elif state["pots"][pot_idx] is not None:
                if is_pot_withered(state["pots"][pot_idx]):
                    result = f"❌ 这个盆里有枯萎的花，请先使用 clear {pot_idx + 1} 清理"
                else:
                    result = "❌ 这个盆已经有花了"
            elif state["inventory"]["seeds"].get(flower_id, 0) <= 0:
                result = "❌ 没有这种种子"
            else:
                state["pest_treatment"].pop(pot_idx, None)
                is_rainy = bool(weather_data.get("auto_water"))
                state["pots"][pot_idx] = {
                    "flower_id": flower_id,
                    "planted_time": now,
                    "watered": is_rainy,
                    "growth_progress": 0.0,
                    "last_growth_update": now,
                }
                state["inventory"]["seeds"][flower_id] -= 1
                if state["inventory"]["seeds"][flower_id] <= 0:
                    del state["inventory"]["seeds"][flower_id]

                result = f"🌱 在盆{pot_idx + 1}种下了{FLOWERS[flower_id]['name']}！"
                if is_rainy:
                    actual_time = FLOWERS[flower_id]["grow_time"] / weather_data["grow_speed"]
                    result += f"\n   🌧️ 雨水自动滋润，预计约{format_time(actual_time)}成熟"
                else:
                    result += f"\n   🏜️ 未浇水，花尚未开始生长，请使用 water {pot_idx + 1}"

    elif action == "water":
        if len(parts) != 2:
            result = "❌ 用法：water <盆号> 或 water all"
        else:
            target = parts[1].lower()
            target_indices = []
            if target == "all":
                target_indices = list(range(state["max_pots"]))
            else:
                pot_idx = get_pot_index(target, state)
                if pot_idx is None:
                    result = f"❌ 盆号必须是1-{state['max_pots']}，或使用 water all"
                else:
                    target_indices = [pot_idx]

            if not result:
                watered_count = 0
                has_growing_flower = False
                has_withered_flower = False
                for i in target_indices:
                    pot = state["pots"][i]
                    if pot is None:
                        continue
                    if is_pot_withered(pot):
                        has_withered_flower = True
                        continue
                    has_growing_flower = True
                    if not pot.get("watered", True):
                        pot["watered"] = True
                        pot["last_growth_update"] = now
                        watered_count += 1

                if weather_data.get("auto_water") and has_growing_flower:
                    result = "🌧️ 正在下雨，所有生长中的花已经被雨水滋润了"
                elif watered_count > 0:
                    result = f"💧 浇水完成！{watered_count}盆花开始生长"
                elif has_withered_flower and not has_growing_flower:
                    result = "❌ 枯萎的花无法浇水，请先清理花盆"
                elif not has_growing_flower:
                    result = "❌ 指定花盆里没有可浇水的花"
                else:
                    result = "❌ 没有需要浇水的花（可能都已经浇过了）"

    elif action == "harvest":
        if len(parts) != 2:
            result = "❌ 用法：harvest <盆号> 或 harvest all"
        elif parts[1].lower() == "all":
            ready_indices = []
            for pot_idx, pot in enumerate(state["pots"][: state["max_pots"]]):
                if pot is None or is_pot_withered(pot):
                    continue
                if "pest_time" in pot and now < pot["pest_time"] and (
                    pot_idx not in state["pest_treatment"]
                    or now >= state["pest_treatment"].get(pot_idx, 0)
                ):
                    continue
                flower_id = pot["flower_id"]
                if float(pot.get("growth_progress", 0.0)) >= FLOWERS[flower_id]["grow_time"]:
                    ready_indices.append(pot_idx)

            if not ready_indices:
                result = "❌ 现在没有可以收获的成熟花朵"
            else:
                harvested_messages = [
                    _harvest_one_pot(state, pot_idx, now, weather_data)
                    for pot_idx in ready_indices
                ]
                result = (
                    f"🧺 一键收获完成，共收获{len(ready_indices)}朵花！\n\n"
                    + "\n\n".join(harvested_messages)
                )
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                result = f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                result = _harvest_one_pot(state, pot_idx, now, weather_data)

    elif action == "treat":
        if len(parts) != 2:
            result = "❌ 用法：treat <盆号>"
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                result = f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                pot = state["pots"][pot_idx]
                if pot is None:
                    result = "❌ 这个盆是空的"
                elif is_pot_withered(pot):
                    result = f"❌ 这盆花已经枯萎，无法治疗，请使用 clear {pot_idx + 1} 清理"
                elif "pest_time" not in pot:
                    result = "❌ 这盆花没有长虫"
                elif state["money"] < PEST_TREATMENT_COST:
                    result = f"❌ 治疗需要{PEST_TREATMENT_COST}块，钱不够！"
                else:
                    state["money"] -= PEST_TREATMENT_COST
                    state["pest_treatment"][pot_idx] = now + TREATMENT_PROTECTION_SECONDS
                    pot.pop("pest_time", None)
                    result = (
                        f"✅ 治疗了盆{pot_idx + 1}的花！(-{PEST_TREATMENT_COST}块)\n"
                        "   这盆花在本轮生长周期内不会再长虫。"
                    )

    elif action == "clear":
        if len(parts) != 2:
            result = "❌ 用法：clear <盆号>"
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                result = f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                pot = state["pots"][pot_idx]
                if pot is None:
                    result = "❌ 这个盆是空的"
                elif not is_pot_withered(pot):
                    result = "❌ 这盆花还活着，不能清理"
                else:
                    flower_id = pot["flower_id"]
                    flower_name = FLOWERS[flower_id]["name"]
                    state["pots"][pot_idx] = None
                    state["pest_treatment"].pop(pot_idx, None)
                    reward = max(1, FLOWERS[flower_id]["seed_price"] // 2)
                    if random.random() < WITHERED_CLEAR_REWARD_CHANCE:
                        state["money"] += reward
                        result = (
                            f"🧹 清理了盆{pot_idx + 1}枯萎的{flower_name}。"
                            f"\n🪙 翻土时找到了{reward}块金币！"
                        )
                    else:
                        result = f"🧹 清理了盆{pot_idx + 1}枯萎的{flower_name}，花盆重新空出来了。"
                    add_event(state, f"清理枯萎的{flower_name}（盆{pot_idx + 1}）")

    elif action == "arrange":
        if len(parts) != 2:
            result = "❌ 用法：arrange <花>"
        else:
            flower_id = parts[1].lower()
            vase = state.setdefault("vase", [])
            if flower_id not in FLOWERS:
                result = "❌ 没有这种花"
            elif len(vase) >= VASE_CAPACITY:
                result = f"❌ 花瓶已经插满了（最多{VASE_CAPACITY}朵）"
            elif state["inventory"]["flowers"].get(flower_id, 0) <= 0:
                result = "❌ 背包里没有这种已经收获的花"
            else:
                state["inventory"]["flowers"][flower_id] -= 1
                if state["inventory"]["flowers"][flower_id] <= 0:
                    del state["inventory"]["flowers"][flower_id]
                vase.append({"flower_id": flower_id, "arranged_time": now})
                result = (
                    f"💐 把一朵{FLOWERS[flower_id]['name']}插进了花瓶。"
                    f"\n   花瓶里的花不能再出售，可保持约{VASE_LIFESPAN_REAL_HOURS}小时。"
                )
                add_event(state, f"把{FLOWERS[flower_id]['name']}插进花瓶")

    elif action == "vase":
        if len(parts) != 1:
            result = "❌ 用法：vase"
        else:
            result = get_vase_status(state, now)

    elif action == "remove_vase":
        if len(parts) != 2:
            result = "❌ 用法：remove_vase <位置>"
        else:
            vase = state.setdefault("vase", [])
            try:
                vase_idx = int(parts[1]) - 1
            except ValueError:
                result = "❌ 花瓶位置必须是数字"
            else:
                if vase_idx < 0 or vase_idx >= len(vase):
                    if vase:
                        result = f"❌ 花瓶位置应为1-{len(vase)}"
                    else:
                        result = "❌ 花瓶现在是空的"
                else:
                    entry = vase.pop(vase_idx)
                    flower_name = FLOWERS[entry["flower_id"]]["name"]
                    result = (
                        f"🧹 从花瓶位置{vase_idx + 1}移除了{flower_name}。"
                        "\n   花朵和金币都不会返还。"
                    )
                    add_event(state, f"从花瓶移除{flower_name}")

    elif action == "sell":
        if len(parts) < 2:
            result = "❌ 要卖什么？"
        elif parts[1].lower() == "all":
            if len(parts) != 2:
                result = "❌ 用法：sell all"
            else:
                total = sum(
                    FLOWERS[flower_id]["sell_price"] * qty
                    for flower_id, qty in state["inventory"]["flowers"].items()
                    if flower_id in FLOWERS and qty > 0
                )
                if total <= 0:
                    result = "❌ 背包里没有花可卖"
                else:
                    state["money"] += total
                    state["total_earned"] += total
                    state["inventory"]["flowers"] = {}
                    result = f"💰 卖掉所有花，赚了{total}块！"
        else:
            flower_id = parts[1].lower()
            quantity = 1 if len(parts) < 3 else parse_positive_int(parts[2])
            if len(parts) > 3:
                result = "❌ 用法：sell <花> [数量]"
            elif quantity is None:
                result = "❌ 出售数量必须是大于0的整数"
            elif flower_id not in FLOWERS or state["inventory"]["flowers"].get(flower_id, 0) <= 0:
                result = "❌ 没有这种花"
            elif state["inventory"]["flowers"][flower_id] < quantity:
                result = "❌ 数量不够"
            else:
                price = FLOWERS[flower_id]["sell_price"] * quantity
                state["money"] += price
                state["total_earned"] += price
                state["inventory"]["flowers"][flower_id] -= quantity
                if state["inventory"]["flowers"][flower_id] <= 0:
                    del state["inventory"]["flowers"][flower_id]
                result = f"💰 卖了{quantity}朵{FLOWERS[flower_id]['name']}，赚了{price}块！"

    elif action == "adopt":
        requested_name = " ".join(parts[1:]) if len(parts) > 1 else "小猫"
        cat_name = normalize_cat_name(requested_name, default="小猫")
        if cat_name is None:
            result = f"❌ 猫咪名字不能超过{CAT_NAME_MAX_LENGTH}个字符"
        elif state["cat"] is not None:
            result = "❌ 已经有猫了"
        elif state["money"] < CAT_ADOPT_COST:
            result = f"❌ 钱不够！需要{CAT_ADOPT_COST}块才能收养小猫"
        else:
            state["money"] -= CAT_ADOPT_COST
            pending_bonus = max(0, int(state.get("pending_cat_mood_bonus", 0)))
            state["cat"] = {"name": cat_name}
            state["cat_stats"] = {
                "hunger": 70.0,
                "thirst": 70.0,
                "mood": min(100.0, 60.0 + pending_bonus),
                "affection": 10.0,
            }
            state["pending_cat_mood_bonus"] = 0
            state["cat_last_pet_real_time"] = now - (PET_COOLDOWN_REAL_MINUTES * 60)
            state["last_letter_check"] = now
            state["last_collectible_check"] = now
            result = f"🎉 成功收养了{cat_name}！记得喂它哦~"
            if pending_bonus > 0:
                result += f"\n🎁 已保存的图鉴奖励生效：猫咪心情+{pending_bonus}"

    elif action == "rename_cat":
        if state["cat"] is None:
            result = "❌ 还没有猫"
        elif len(parts) < 2:
            result = "❌ 用法：rename_cat <名字>"
        else:
            new_name = normalize_cat_name(" ".join(parts[1:]), default=None)
            if new_name is None:
                result = f"❌ 猫咪名字不能为空，且不能超过{CAT_NAME_MAX_LENGTH}个字符"
            else:
                old_name = state["cat"].get("name", "小猫")
                state["cat"]["name"] = new_name
                result = f"🐱 {old_name}现在叫{new_name}了！"

    elif action == "feed":
        if state["cat"] is None:
            result = "❌ 还没有猫"
        elif len(parts) != 2 or parts[1].lower() not in ("basic", "premium"):
            result = "❌ 用法：feed <basic|premium>"
        else:
            food_type = "basic_food" if parts[1].lower() == "basic" else "premium_food"
            if state["inventory"]["items"].get(food_type, 0) <= 0:
                result = "❌ 没有这种猫粮"
            else:
                state["inventory"]["items"][food_type] -= 1
                if state["inventory"]["items"][food_type] <= 0:
                    del state["inventory"]["items"][food_type]
                for stat, value in ITEMS[food_type]["effect"].items():
                    state["cat_stats"][stat] = min(100, state["cat_stats"][stat] + value)
                result = f"🍽️ 喂了{ITEMS[food_type]['name']}！"

    elif action == "give_water":
        if len(parts) != 1:
            result = "❌ 用法：give_water"
        elif state["cat"] is None:
            result = "❌ 还没有猫"
        else:
            state["cat_stats"]["thirst"] = min(100, state["cat_stats"]["thirst"] + 40)
            result = "💧 给猫喝了水！"

    elif action == "pet":
        if len(parts) != 1:
            result = "❌ 用法：pet"
        elif state["cat"] is None:
            result = "❌ 还没有猫"
        else:
            last_pet_time = state.get("cat_last_pet_real_time", 0)
            cooldown_seconds = PET_COOLDOWN_REAL_MINUTES * 60
            time_since_last_pet = now - last_pet_time
            if time_since_last_pet < cooldown_seconds:
                result = f"❌ 猫不想被摸，过{format_time(cooldown_seconds - time_since_last_pet)}再试"
            else:
                state["cat_last_pet_real_time"] = now
                state["cat_stats"]["mood"] = min(100, state["cat_stats"]["mood"] + 10)
                state["cat_stats"]["affection"] = min(100, state["cat_stats"]["affection"] + 3)
                result = "🤗 抚摸了小猫，它很开心！心情+10 亲密度+3"

    elif action == "play":
        if state["cat"] is None:
            result = "❌ 还没有猫"
        elif len(parts) != 2 or parts[1].lower() not in ("ball", "feather"):
            result = "❌ 用法：play <ball|feather>"
        else:
            toy_id = "ball" if parts[1].lower() == "ball" else "feather_wand"
            if state["inventory"]["items"].get(toy_id, 0) <= 0:
                result = "❌ 没有这个玩具"
            else:
                state["inventory"]["items"][toy_id] -= 1
                if state["inventory"]["items"][toy_id] <= 0:
                    del state["inventory"]["items"][toy_id]
                for stat, value in ITEMS[toy_id]["effect"].items():
                    state["cat_stats"][stat] = min(100, state["cat_stats"][stat] + value)
                result = f"🎾 和猫玩了{ITEMS[toy_id]['name']}！（玩具已消耗）"

    elif action == "buy_pot":
        if len(parts) != 1:
            result = "❌ 用法：buy_pot"
        elif state["max_pots"] >= MAX_POTS:
            result = f"❌ 已经有{MAX_POTS}个花盆了，无法再扩展！"
        else:
            next_pot_number = state["max_pots"] + 1
            pot_cost = get_next_pot_cost(state)
            if pot_cost is None:
                result = f"❌ 已经有{MAX_POTS}个花盆了，无法再扩展！"
            elif state["money"] < pot_cost:
                result = f"❌ 解锁第{next_pot_number}个花盆需要{pot_cost}块，钱不够！"
            else:
                state["money"] -= pot_cost
                state["pots"].append(None)
                state["max_pots"] += 1
                result = (
                    f"✅ 解锁了第{next_pot_number}个花盆！"
                    f"现在有{state['max_pots']}个花盆 (-{pot_cost}块)"
                )

    elif action == "collectibles":
        if len(parts) != 1:
            result = "❌ 用法：collectibles"
        else:
            lines = ["🎁 猫咪收集品"]
            if not state["collectibles"]:
                lines.append("  还没有收集品")
            else:
                for collectible in CAT_COLLECTIBLES:
                    count = state["collectibles"].get(collectible["id"], 0)
                    if count > 0:
                        lines.append(f"  {collectible['emoji']} {collectible['name']} x{count}")
            result = "\n".join(lines)

    elif action == "letters":
        if len(parts) != 1:
            result = "❌ 用法：letters"
        else:
            lines = ["✉️ 猫咪信件"]
            if not state["letters_received"]:
                lines.append("  还没有收到信")
            else:
                for idx in state["letters_received"]:
                    lines.append(f"  「{CAT_LETTERS[idx]['text']}」")
            lines.append(f"\n  已收集：{len(state['letters_received'])}/5封")
            result = "\n".join(lines)

    elif action == "encyclopedia":
        if len(parts) != 1:
            result = "❌ 用法：encyclopedia"
        else:
            lines = ["📚 图鉴"]
            for flower_id, flower_data in FLOWERS.items():
                if flower_id in state["encyclopedia"]:
                    lines.append(f"  ✅ {flower_data['name']} ({flower_data['rarity']})")
                else:
                    lines.append("  ❓ ???")
            lines.append(f"\n进度：{len(state['encyclopedia'])}/8")
            result = "\n".join(lines)

    elif action == "status":
        if len(parts) != 1:
            result = "❌ 用法：status"
        else:
            result = get_status(state, weather_data)

    elif action == "help":
        result = f"""💡 命令帮助：
shop - 查看商店
buy <物品> [数量] - 买东西（数量必须大于0）
plant <花> <盆号> - 种花（雨天自动浇水，否则需手动浇水才能生长）
water <盆号|all> - 给花浇水（浇一次永久有效，直到收获）
harvest <盆号|all> - 收获一盆，或一键收获全部成熟花朵
sell <花> [数量] - 卖花，或 sell all
treat <盆号> - 治疗害虫({PEST_TREATMENT_COST}块，本轮不再长虫)
clear <盆号> - 清理枯萎花（50%概率获得少量金币）
buy_pot - 解锁下一个花盆(第4盆20块 / 第5盆35块 / 第6盆50块)
arrange <花> - 把已收获鲜花插入花瓶（插入后不可出售）
vase - 查看花瓶与鲜花枯萎度
remove_vase <位置> - 移除花瓶中任意状态的花（不返还花朵或金币）
adopt [名字] - 收养猫咪并可选取名(需{CAT_ADOPT_COST}块)
rename_cat <名字> - 给已收养的猫咪改名
feed <basic|premium> - 喂猫
give_water - 给猫喝水
pet - 抚摸猫(冷却{PET_COOLDOWN_REAL_MINUTES}分钟)
play <ball|feather> - 和猫玩（消耗玩具）
encyclopedia - 查看图鉴
collectibles - 查看猫咪收集品
letters - 查看猫咪信件
status - 查看状态
help - 显示帮助

🌤️ 天气系统（真实时间）：
☀️ 晴天：花生长×1.1，需手动浇水，猫心情净+1.0/小时
🌧️ 下雨：花生长×1.2，自动浇水，猫心情净-2.0/小时
☁️ 多云：花生长×1.0，需手动浇水，猫心情净-0.5/小时
天气到期后在下一次游戏指令时变化一次；离线期间不补算多轮天气

💧 浇水系统：
- 花种下后默认不生长，需浇水才能开始生长
- 未浇水期间不会积累进度，之后浇水也不会补算
- 手动浇水一次后永久有效，直到本轮收获
- 雨天自动滋润所有花盆

🐱 猫咪系统（真实时间）：
  饱食度：-5/小时    口渴度：-6/小时
  心情：基础衰减-0.5/小时，天气影响
  亲密度：自然衰减-0.5/小时
         饱食或口渴<50时额外-2.0/小时
  被动衰减保护：各项最低停在20，不会因长期离线继续下降

🌸 花卉解锁：
- 开局：雏菊、郁金香、向日葵、玫瑰
- 图鉴2种：解锁薰衣草、百合
- 图鉴5种：解锁樱花
- 图鉴7种：解锁月光花

🎉 特殊事件：
🌈 雨后彩虹：获得金币或普通种子
🦋 蝴蝶飞过：每5分钟最多检查一次，可能掉落少量金币
🎁 猫咪收集品：每5分钟最多检查一次
✉️ 猫咪写信：每5分钟最多检查一次，按亲密度收5封信
🐛 害虫：每5分钟最多检查一次；成熟花不再长新虫，染虫后{PEST_DEATH_REAL_MINUTES}分钟内不治疗会枯萎
   枯萎花会留在花盆里，需使用 clear <盆号> 手动清理

💐 花瓶系统：
- 花瓶最多插{VASE_CAPACITY}朵已经收获的花
- 插花后不能再出售，可保持约{VASE_LIFESPAN_REAL_HOURS}小时
- vase 可查看新鲜程度与枯萎度
- 任意状态都可使用 remove_vase <位置> 移除，且不返还花朵或金币"""

    else:
        result = "❌ 未知命令，输入 help 查看帮助"

    if all_event_messages:
        result = "\n".join(all_event_messages) + "\n\n" + result

    if action != "status" or result.startswith("❌"):
        result += "\n\n" + _summary(state)

    return result


def cmd(command):
    """本地单存档兼容入口。"""
    state = load_game()
    if state is None:
        return "❌ 没有存档，请先 new_game()"
    result = process_command(state, command)
    save_game(state)
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if load_game() is None:
            print(new_game())
        print(cmd(" ".join(sys.argv[1:])))
    else:
        print(new_game())
        print("\n" + "=" * 50 + "\n")
        print(cmd("status"))
