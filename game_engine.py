"""
花园与猫咪 - API与网页兼容游戏引擎
支持独立存档 API、可视化网页与本地单文件运行

v4.9.9 更新：
- 心情离线结算最多计算前2个现实小时，超出部分冻结；饱食、口渴、亲密度维持原规则
- 新增每种花的累计收获计数；旧存档以升级时背包中的鲜花数量作为最低起点
- 网页图鉴按普通、稀有、珍贵顺序展示，并显示已发现花卉的累计收获数量
- 网页顶部与猫屋标题旁新增背包入口，摸摸按钮移到猫咪名字旁
- 背包鲜花区新增一键售出与单种卖全部，商店两页卡片尺寸统一
- 保留共享便签与摸猫现实10分钟冷却，兼容 v4.9.8c 及更早存档

v4.9.1 更新：
- 猫咪收集品改为“历史最高亲密度永久解锁，当前状态只影响概率”
- 收藏阶段解锁后不会因亲密度自然衰减而重新锁定
- 夜晚与高心情不再作为硬门槛，仅提高珍贵物品出现概率
- 收集品允许完全随机重复，不再优先补齐尚未获得的物品
- 新增收藏首次获得时间与稳定解锁提示，供后续收藏室界面使用
- 兼容 v4.9.0 及更早存档

v4.9.0 更新：
- 猫咪收集品由5件扩充为16件，新增稀有度、描述与解锁条件
- 猫咪信件由5封扩充为12封，统一为更有猫咪感的短句风格
- 收集品与信件查看命令新增动态完成度和更完整内容
- 兼容旧版收集品与信件存档

v4.8.11 更新：
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
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# 事件来源是稳定的机器可读标识；展示名由调用方按需转换，未来可独立扩展昵称。
EVENT_HISTORY_LIMIT = 50
EVENT_AREAS = ("garden", "flower_shop", "cottage")

EVENT_SOURCE_LABELS = {
    "human": "人类",
    "ai": "AI",
    "system": "系统",
}


def normalize_event_source(source):
    source_id = str(source or "system").strip().lower()
    return source_id if source_id in EVENT_SOURCE_LABELS else "system"


def get_event_source_label(source):
    return EVENT_SOURCE_LABELS[normalize_event_source(source)]


# 游戏数据
FLOWERS = {
    "daisy": {"name": "雏菊", "rarity": "common", "seed_price": 3, "sell_price": 4, "grow_time": 180},
    "tulip": {"name": "郁金香", "rarity": "common", "seed_price": 4, "sell_price": 6, "grow_time": 300},
    "pansy": {"name": "三色堇", "rarity": "common", "seed_price": 5, "sell_price": 8, "grow_time": 420},
    "sunflower": {"name": "向日葵", "rarity": "common", "seed_price": 6, "sell_price": 10, "grow_time": 600},
    "rose": {"name": "玫瑰", "rarity": "common", "seed_price": 8, "sell_price": 14, "grow_time": 900},
    "baby_breath": {"name": "满天星", "rarity": "common", "seed_price": 10, "sell_price": 18, "grow_time": 1200},
    "carnation": {"name": "康乃馨", "rarity": "common", "seed_price": 12, "sell_price": 22, "grow_time": 1500},
    "lavender": {"name": "薰衣草", "rarity": "uncommon", "seed_price": 16, "sell_price": 30, "grow_time": 1800},
    "hydrangea": {"name": "绣球花", "rarity": "uncommon", "seed_price": 20, "sell_price": 38, "grow_time": 2400},
    "lily": {"name": "百合", "rarity": "uncommon", "seed_price": 26, "sell_price": 50, "grow_time": 3000},
    "iris": {"name": "鸢尾花", "rarity": "uncommon", "seed_price": 28, "sell_price": 64, "grow_time": 3600},
    "lisianthus": {"name": "洋桔梗", "rarity": "uncommon", "seed_price": 36, "sell_price": 84, "grow_time": 4500},
    "cherry_blossom": {"name": "樱花", "rarity": "rare", "seed_price": 46, "sell_price": 106, "grow_time": 5400},
    "peony": {"name": "牡丹", "rarity": "rare", "seed_price": 58, "sell_price": 130, "grow_time": 6300},
    "camellia": {"name": "山茶花", "rarity": "rare", "seed_price": 72, "sell_price": 156, "grow_time": 7200},
    "moonflower": {"name": "月光花", "rarity": "legendary", "seed_price": 90, "sell_price": 198, "grow_time": 8400},
    "red_spider_lily": {"name": "彼岸花", "rarity": "legendary", "seed_price": 120, "sell_price": 264, "grow_time": 9900},
}

BOUQUETS = {
    "first_meeting": {"name": "初见", "components": {"tulip": 2, "baby_breath": 1}},
    "morning_light": {"name": "晨光", "components": {"sunflower": 1, "carnation": 1, "daisy": 1}},
    "sunny_field": {"name": "晴野", "components": {"pansy": 1, "daisy": 1, "baby_breath": 1}},
    "heart_note": {"name": "心笺", "components": {"rose": 1, "carnation": 1, "tulip": 1}},
    "evening_breeze": {"name": "晚风", "components": {"lisianthus": 1, "lavender": 2}},
    "soft_cloud": {"name": "柔云", "components": {"hydrangea": 1, "lily": 1, "baby_breath": 1}},
    "blue_letter": {"name": "蓝信", "components": {"iris": 1, "lisianthus": 1, "rose": 1}},
    "cherry_branch": {"name": "樱枝", "components": {"cherry_blossom": 1, "lisianthus": 1, "baby_breath": 1}},
    "spring_banquet": {"name": "春宴", "components": {"peony": 1, "rose": 1, "lily": 1}},
    "spring_mountain": {"name": "春山", "components": {"camellia": 1, "hydrangea": 1, "tulip": 1}},
    "moonlit_book": {"name": "月下书", "components": {"moonflower": 1, "lily": 1, "lavender": 1}},
    "higan_poem": {"name": "彼岸诗", "components": {"red_spider_lily": 1, "peony": 1, "iris": 1}},
}


# 图鉴数量和累计收获数达到要求后开放购买和种植；已收录过的花始终保持解锁，兼容旧存档。
FLOWER_UNLOCK_REQUIREMENTS = {
    "daisy": {"encyclopedia": 0, "harvests": 0},
    "tulip": {"encyclopedia": 0, "harvests": 0},
    "pansy": {"encyclopedia": 0, "harvests": 0},
    "sunflower": {"encyclopedia": 0, "harvests": 0},
    "rose": {"encyclopedia": 0, "harvests": 0},
    "baby_breath": {"encyclopedia": 4, "harvests": 8},
    "carnation": {"encyclopedia": 4, "harvests": 8},
    "lavender": {"encyclopedia": 7, "harvests": 24},
    "hydrangea": {"encyclopedia": 7, "harvests": 24},
    "lily": {"encyclopedia": 7, "harvests": 24},
    "iris": {"encyclopedia": 10, "harvests": 42},
    "lisianthus": {"encyclopedia": 10, "harvests": 42},
    "cherry_blossom": {"encyclopedia": 12, "harvests": 62},
    "peony": {"encyclopedia": 12, "harvests": 62},
    "camellia": {"encyclopedia": 14, "harvests": 85},
    "moonflower": {"encyclopedia": 15, "harvests": 105},
    "red_spider_lily": {"encyclopedia": 16, "harvests": 125},
}

ENCYCLOPEDIA_REWARDS = {
    "daisy": {"seeds": {"daisy": 2}},
    "tulip": {"money": 3},
    "pansy": {"items": {"basic_food": 5}},
    "sunflower": {"money": 5},
    "rose": {"seeds": {"rose": 1}},
    "carnation": {"seeds": {"carnation": 1}},
    "lavender": {"items": {"cat_treat": 2}},
    "hydrangea": {"money": 6},
    "lily": {"items": {"premium_food": 5}},
    "iris": {"seeds": {"iris": 1}},
    "cherry_blossom": {"items": {"ball": 1}},
    "peony": {"money": 10},
    "moonflower": {"items": {"feather_wand": 1}},
    "red_spider_lily": {"seeds": {"red_spider_lily": 1}},
}

GARDEN_EVENT_COLLECTIBLES = [
    {
        "id": "rainbow_shard",
        "name": "雨后彩虹碎片",
        "emoji": "🌈",
        "source": "rainbow",
        "description": "彩虹出现并送来奖励后，留下一小枚短暂发亮的纪念。",
    },
    {
        "id": "butterfly_glimmer",
        "name": "蝶影碎光",
        "emoji": "🦋",
        "source": "butterfly",
        "description": "蝴蝶带来金币时，花丛里会留下轻飘飘的碎光。",
    },
]


def _build_garden_flower_collectibles():
    return [
        {
            "id": f"flower_{flower_id}",
            "name": f"{flower['name']}压花",
            "emoji": "🌸",
            "source": "flower",
            "flower_id": flower_id,
            "description": f"第一次收获{flower['name']}后留下的花园藏品。",
        }
        for flower_id, flower in FLOWERS.items()
    ]


GARDEN_COLLECTIBLES = GARDEN_EVENT_COLLECTIBLES + _build_garden_flower_collectibles()
GARDEN_COLLECTIBLE_IDS = {item["id"] for item in GARDEN_COLLECTIBLES}
GARDEN_COLLECTIBLE_BY_ID = {item["id"]: item for item in GARDEN_COLLECTIBLES}

ITEMS = {
    "basic_food": {"name": "普通猫粮", "price": 10, "type": "consumable", "effect": {"hunger": 20}},
    "premium_food": {"name": "高级猫粮", "price": 20, "type": "consumable", "effect": {"hunger": 25, "mood": 1}},
    "cat_treat": {"name": "猫零食", "price": 14, "type": "consumable", "effect": {"hunger": 5, "mood": 8}},
    "water_bowl": {"name": "高级水碗", "price": 10, "type": "permanent", "effect": {"thirst_decay": -0.5}},
    "cat_bed": {"name": "高级猫窝", "price": 30, "type": "permanent", "effect": {"mood_decay": -0.3}},
    "premium_food_bowl": {"name": "高级粮碗", "price": 18, "type": "permanent", "effect": {}},
    "ball": {"name": "毛线球", "price": 8, "type": "toy", "effect": {"mood": 12}},
    "feather_wand": {"name": "逗猫棒", "price": 12, "type": "toy", "effect": {"mood": 20}},
}

# 共同小屋只把“是否拥有、何时获得、由谁获得”写入存档；展示位置和素材始终由
# catalog 决定。当前 slot_key 只是稳定语义标识，不代表视觉坐标或层级。
COTTAGE_ITEM_CATALOG = {
    # v1-A 已售出的三项保留 catalog 身份，供旧存档识别；它们不再参与 v1-B 收藏或购买。
    "rug": {"id": "rug", "name": "地毯", "category": "legacy", "legacy_only": True, "slot_key": "rug", "asset_key": "", "description": "v1-A 的固定场景记录。"},
    "curtains": {"id": "curtains", "name": "窗帘", "category": "legacy", "legacy_only": True, "slot_key": "curtains", "asset_key": "", "description": "v1-A 的固定场景记录。"},
    "storage_sideboard": {"id": "storage_sideboard", "name": "储物边柜", "category": "legacy", "legacy_only": True, "slot_key": "storage_sideboard", "asset_key": "", "description": "v1-A 的停售家具记录。"},
    "ottoman": {"id": "ottoman", "name": "绿色格纹小脚凳", "category": "furniture", "price": 600, "slot_key": "ottoman", "asset_key": "ottoman", "description": "一件轻巧的绿色格纹小脚凳。"},
    "coffee_table": {"id": "coffee_table", "name": "茶几", "category": "furniture", "price": 900, "slot_key": "coffee_table", "asset_key": "coffee_table", "description": "适合放下茶杯与小花束的茶几。"},
    "floor_lamp": {"id": "floor_lamp", "name": "落地灯", "category": "furniture", "price": 1200, "slot_key": "floor_lamp", "asset_key": "floor_lamp", "description": "在傍晚亮起的落地灯。"},
    "flower_stand": {"id": "flower_stand", "name": "花梯架", "category": "furniture", "price": 1800, "slot_key": "flower_stand", "asset_key": "plant_ladder", "description": "留给花盆与垂落枝叶的梯子式花架。"},
    "wardrobe": {"id": "wardrobe", "name": "衣柜", "category": "furniture", "price": 2200, "slot_key": "wardrobe", "asset_key": "wardrobe", "description": "安静立在角落的衣柜。"},
    "bookshelf": {"id": "bookshelf", "name": "矮书柜", "category": "furniture", "price": 1500, "slot_key": "bookshelf", "asset_key": "low_bookshelf", "description": "可以慢慢填满的低矮书柜。"},
    "sofa": {"id": "sofa", "name": "沙发", "category": "furniture", "price": 2600, "slot_key": "sofa", "asset_key": "sofa", "description": "一起休息的沙发。"},
    "dining_set": {"id": "dining_set", "name": "餐桌椅", "category": "furniture", "price": 3000, "slot_key": "dining_set", "asset_key": "dining_set", "description": "留给日常用餐的餐桌椅。"},
    "bed": {"id": "bed", "name": "床", "category": "furniture", "price": 3500, "slot_key": "bed", "asset_key": "bed", "description": "让小屋真正安顿下来的床。"},
    "potted_plant": {"id": "potted_plant", "name": "白黄小花花器", "category": "decoration", "reward_only": True, "slot_key": "potted_plant", "asset_key": "potted_plant", "description": "满天星首次收获留下的小屋纪念。"},
    "wall_art": {"id": "wall_art", "name": "小挂画", "category": "decoration", "reward_only": True, "slot_key": "wall_art", "asset_key": "wall_art", "description": "洋桔梗首次收获留下的小屋纪念。"},
    "hanging_plant": {"id": "hanging_plant", "name": "墙上小搁板藤蔓盆栽", "category": "decoration", "reward_only": True, "slot_key": "hanging_plant", "asset_key": "hanging_plant", "description": "山茶花首次收获留下的小屋纪念。"},
    "beanbag_reward": {"id": "beanbag_reward", "name": "豆袋懒人沙发", "category": "decoration", "reward_only": True, "slot_key": "beanbag_reward", "asset_key": "beanbag_reward", "description": "两种传说花相遇后留下的纪念。"},
}

COTTAGE_REWARD_REQUIREMENTS = {
    "potted_plant": {"flowers": {"baby_breath"}},
    "wall_art": {"flowers": {"lisianthus"}},
    "hanging_plant": {"flowers": {"camellia"}},
    "beanbag_reward": {"flowers": {"moonflower", "red_spider_lily"}},
}


def get_cottage_reward_requirement_text(item_id):
    """从正式解锁条件生成小屋奖励的展示文案。"""
    requirement = COTTAGE_REWARD_REQUIREMENTS.get(item_id, {})
    flower_ids = requirement.get("flowers", set())
    flower_names = [
        FLOWERS[flower_id]["name"]
        for flower_id in FLOWERS
        if flower_id in flower_ids
    ]
    if not flower_names:
        return ""
    if len(flower_names) == 1:
        return f"首次收获{flower_names[0]}"
    return f"收录{' + '.join(flower_names)}"


COTTAGE_REWARD_ID_ALIASES = {
    "small_photo_frame": "potted_plant",
    "small_wall_art": "wall_art",
    "small_vase": "hanging_plant",
    "eternal_flower": "beanbag_reward",
}

# v4.6.6: 天气系统 - 浇水开关版
# 雨天生长最快并自动浇水；晴天小幅加速且需手动浇水；多云为标准速度
WEATHER = {
    "sunny": {"name": "晴天", "emoji": "☀️", "grow_speed": 1.1, "cat_mood_change": 1.5},
    "rainy": {"name": "下雨", "emoji": "🌧️", "grow_speed": 1.2, "cat_mood_change": -1.5, "auto_water": True},
    "cloudy": {"name": "多云", "emoji": "☁️", "grow_speed": 1.0, "cat_mood_change": 0},
}

WEATHER_CHANGE_MIN = 3600
WEATHER_CHANGE_MAX = 7200

# v4.6.5: 心情基础衰减（/真实小时）
MOOD_BASE_DECAY = 0.5

# v4.9.9: 单次离线心情结算最多覆盖前2个现实小时
MOOD_OFFLINE_CAP_REAL_HOURS = 2.0
OFFLINE_PROGRESS_MAX_SECONDS = 72 * 3600
OFFLINE_CAT_AUTO_FEED_TRIGGER = 45.0
OFFLINE_CAT_AUTO_WATER_TRIGGER = 45.0
OFFLINE_CAT_AUTO_REFILL_TARGET = 72.0

# v4.6.5: 亲密度衰减（/真实小时）
AFFECTION_NATURAL_DECAY = 0.1
AFFECTION_STATUS_DECAY = 2.0

# v4.6.5: 抚摸冷却（真实分钟）
PET_COOLDOWN_REAL_MINUTES = 10

CAT_PHASE_VISITOR = "visitor"
CAT_PHASE_WAITING_NAME = "stayed_waiting_name"
CAT_PHASE_ADOPTED = "adopted"
VALID_CAT_PHASES = {CAT_PHASE_VISITOR, CAT_PHASE_WAITING_NAME, CAT_PHASE_ADOPTED}

CAT_LOCATION_GARDEN = "garden"
CAT_LOCATION_HOME = "home"
CAT_LOCATION_AWAY = "away"
VALID_CAT_LOCATIONS = {CAT_LOCATION_GARDEN, CAT_LOCATION_HOME, CAT_LOCATION_AWAY}

CAT_VISIT_INTERVAL_MIN_SECONDS = 60 * 60
CAT_VISIT_INTERVAL_MAX_SECONDS = 2 * 60 * 60
CAT_VISIT_DURATION_MIN_SECONDS = 20 * 60
CAT_VISIT_DURATION_MAX_SECONDS = 40 * 60
CAT_STAY_DECISION_GRACE_SECONDS = 48 * 60 * 60
CAT_HOME_STAY_MIN_SECONDS = 60 * 60
CAT_HOME_STAY_MAX_SECONDS = 2 * 60 * 60
CAT_OUTING_DURATION_MIN_SECONDS = 10 * 60
CAT_OUTING_DURATION_MAX_SECONDS = 30 * 60

DEFAULT_CAT_FOOD_TYPE = "basic_food"
DEFAULT_BASIC_CAT_BED_ID = "basic_cat_bed"
DEFAULT_BASIC_FOOD_BOWL_ID = "basic_food_bowl"
DEFAULT_BASIC_WATER_BOWL_ID = "basic_water_bowl"
PREMIUM_CAT_BED_ID = "cat_bed"
PREMIUM_FOOD_BOWL_ID = "premium_food_bowl"
PREMIUM_WATER_BOWL_ID = "water_bowl"
DEFAULT_FOOD_BOWL_CAPACITY = 3
DEFAULT_WATER_BOWL_CAPACITY = 3
PREMIUM_FOOD_BOWL_CAPACITY = 5
PREMIUM_WATER_BOWL_CAPACITY = 5
CAT_ITEM_PACKAGE_SIZES = {
    "basic_food": 5,
    "premium_food": 5,
    "cat_treat": 2,
}
CAT_INTERACTION_ACCEPTANCE = {
    "pet": {"visitor": 1.0, "adopted": 1.0},
    "give_treat": {"visitor": 0.60, "adopted": 0.70},
    "ball": {"visitor": 0.45, "adopted": 0.55},
    "feather_wand": {"visitor": 0.60, "adopted": 0.70},
}
CAT_CARE_FOOD_TYPES = {
    "basic": "basic_food",
    "premium": "premium_food",
}
CAT_TREAT_ITEM_ID = "cat_treat"
SHOP_CAT_ITEM_IDS = (
    "basic_food",
    "premium_food",
    "cat_treat",
    "ball",
    "feather_wand",
    PREMIUM_CAT_BED_ID,
    PREMIUM_WATER_BOWL_ID,
    PREMIUM_FOOD_BOWL_ID,
)

# v5.0: 显示层时间与现实时间 1:1 绑定
REAL_SECONDS_PER_DAY = 24 * 60 * 60
DISPLAY_TIMEZONE = timezone(timedelta(hours=8), name="Asia/Shanghai")
DISPLAY_TIMEZONE_NAME = "Asia/Shanghai"

# 花店 3A：只保存开店与营业安排，不在本批次处理上架或销售。
FLOWER_SHOP_ESTABLISH_COST = 3500
FLOWER_SHOP_SHELF_CAPACITY = 3
FLOWER_SHOP_SHELF_CAPACITIES = (3, 6, 9)
FLOWER_SHOP_SHELF_UPGRADE_COSTS = {3: 1500, 6: 2500}
FLOWER_SHOP_FRESHENER_COST = 1800
FLOWER_SHOP_CAT_BUFF_CHANCE = 0.12
FLOWER_SHOP_CAT_BUFF_DURATION_SECONDS = 4 * 60 * 60
FLOWER_SHOP_CAT_BUFF_MULTIPLIER = 1.10
FLOWER_SHOP_BUSINESS_DURATION_MINUTES = 10 * 60
FLOWER_SHOP_SALE_CHANCE = 0.82
FLOWER_SHOP_SALE_WAIT_MAX_SECONDS = 10 * 60 * 60
FLOWER_SHOP_SALE_WAIT_MODE_SECONDS = 3 * 60 * 60
FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS = 24 * 60 * 60
FLOWER_SHOP_BASE_PRICE_MULTIPLIER = 1.60
FLOWER_SHOP_BASE_PRICING_PROFILE = (
    (4 * 60 * 60, 1.15, "新鲜加价"),
    (10 * 60 * 60, 1.00, "标准售价"),
    (18 * 60 * 60, 0.85, "轻微折价"),
    (24 * 60 * 60, 0.65, "临期折价"),
)
FLOWER_SHOP_FRESHENER_PRICING_PROFILE = (
    (6 * 60 * 60, 1.15, "新鲜加价"),
    (12 * 60 * 60, 1.00, "标准售价"),
    (20 * 60 * 60, 0.85, "轻微折价"),
    (24 * 60 * 60, 0.65, "临期折价"),
)

# v4.7: 害虫死亡时间（真实分钟）
PEST_DEATH_REAL_MINUTES = 10

# 猫咪收集品
# 解锁规则：历史最高亲密度决定永久解锁；当前心情与昼夜只改变概率。
# 旧版5件物品的内部 id 保持不变，确保已有存档继续有效。
CAT_COLLECTIBLES = [
    {
        "id": "pebble",
        "name": "圆润的小石子",
        "emoji": "🪨",
        "rarity": "common",
        "description": "被猫咪舔得很干净，不知道它为什么如此珍惜。",
    },
    {
        "id": "faded_button",
        "name": "褪色纽扣",
        "emoji": "🔘",
        "rarity": "common",
        "description": "蓝色已经快看不出来了，边缘还有浅浅的牙印。",
    },
    {
        "id": "gray_feather",
        "name": "灰白羽毛",
        "emoji": "🪶",
        "rarity": "common",
        "description": "插在猫窝边上时，会跟着风轻轻晃。",
    },
    {
        "id": "maple_leaf",
        "name": "干枯的小树叶",
        "emoji": "🍂",
        "rarity": "common",
        "description": "叶脉很完整，像一张缩小的地图。",
    },
    {
        "id": "bottle_cap",
        "name": "旧瓶盖",
        "emoji": "◉",
        "rarity": "common",
        "description": "猫咪一路踢回来的，发出了很响的声音。",
    },
    {
        "id": "glass_marble",
        "name": "玻璃珠",
        "emoji": "🔮",
        "rarity": "common",
        "description": "对着太阳看，里面藏着一点绿色的光。",
    },
    {
        "id": "red_yarn",
        "name": "红色毛线头",
        "emoji": "🧶",
        "rarity": "common",
        "description": "缠成了一个歪歪扭扭的小球。",
    },
    {
        "id": "pine_needle",
        "name": "一小束松针",
        "emoji": "🌲",
        "rarity": "common",
        "description": "沾着一点泥土，闻起来像雨后的树林。",
    },
    {
        "id": "wildflower",
        "name": "路边的小野花",
        "emoji": "🌼",
        "rarity": "common",
        "description": "花茎被压弯了一点，但猫咪把它完整带回来了。",
    },
    {
        "id": "shell",
        "name": "完整的贝壳",
        "emoji": "🐚",
        "rarity": "uncommon",
        "description": "放在耳边，似乎还能听见很远的水声。",
    },
    {
        "id": "silver_bell",
        "name": "银色铃铛",
        "emoji": "🔔",
        "rarity": "uncommon",
        "description": "已经不会响了，但猫咪还是很喜欢拨弄它。",
    },
    {
        "id": "star_wrapper",
        "name": "星形糖纸",
        "emoji": "⭐",
        "rarity": "uncommon",
        "description": "阳光照上去时，会闪出彩色的光点。",
    },
    {
        "id": "purple_ribbon",
        "name": "淡紫色丝带",
        "emoji": "🎀",
        "rarity": "uncommon",
        "description": "不知道从哪里捡来的，刚好可以系在花瓶上。",
    },
    {
        "id": "clover",
        "name": "四叶草",
        "emoji": "🍀",
        "rarity": "uncommon",
        "description": "四片叶子都完完整整，像是猫咪认真挑过。",
        "boost_hint": "猫咪心情很好时，出现概率会略微提高。",
    },
    {
        "id": "moonstone",
        "name": "月光石碎片",
        "emoji": "🌙",
        "rarity": "rare",
        "description": "夜里会泛起很淡的蓝光，像一小块凝固的月亮。",
        "boost_hint": "夜晚或猫咪心情很好时，出现概率提高。",
        "night_multiplier": 3.0,
        "mood_threshold": 80,
        "mood_multiplier": 1.5,
    },
    {
        "id": "paw_tag",
        "name": "刻着爪印的铜牌",
        "emoji": "🏷️",
        "rarity": "rare",
        "description": "背面刻着一句已经模糊的话：记得回家。",
        "boost_hint": "猫咪心情很好时，出现概率提高。",
        "mood_threshold": 85,
        "mood_multiplier": 3.0,
    },
]

CAT_COLLECTIBLE_RARITY_LABELS = {
    "common": "普通",
    "uncommon": "少见",
    "rare": "珍贵",
}

# 历史最高亲密度达到阶段后，阶段永久开启。
# 数值是抽取权重，归一化后即为大致概率。
CAT_COLLECTIBLE_VISITOR_DROP_RATE = 0.30
CAT_COLLECTIBLE_ADOPTED_DROP_RATE = 0.20
CAT_COLLECTIBLE_UNLOCK_AFFECTION = 30
CAT_COLLECTIBLE_RARITY_WEIGHTS_MID = {"common": 73.0, "uncommon": 25.0, "rare": 2.0}
CAT_COLLECTIBLE_RARITY_WEIGHTS_HIGH = {"common": 60.0, "uncommon": 30.0, "rare": 10.0}

# 猫咪信件（按亲密度顺序）
CAT_LETTERS = [
    {
        "title": "爪印",
        "min_affection": 30,
        "text": "喵。\n（纸上只有一个黑乎乎的爪印。）",
    },
    {
        "title": "饭，还行",
        "min_affection": 34,
        "text": "……喵。\n（爪印旁边歪歪扭扭地写着：饭，还行。）",
    },
    {
        "title": "花盆",
        "min_affection": 38,
        "text": "今天我没有碰倒花盆。\n你应该知道这很难。\n——猫",
    },
    {
        "title": "窗边",
        "min_affection": 42,
        "text": "窗边那块有太阳的地方，是我的。\n你可以坐旁边。\n——猫",
    },
    {
        "title": "叶子",
        "min_affection": 46,
        "text": "我给你带了一片叶子。\n不是捡的，是选的。\n——猫",
    },
    {
        "title": "三觉",
        "min_affection": 50,
        "text": "你出门以后，我睡了三觉。\n醒来的时候你还没回来。\n不合理。\n——猫",
    },
    {
        "title": "晚饭",
        "min_affection": 54,
        "text": "今天的饭晚了一点。\n我已经原谅你了。\n大概。\n——猫",
    },
    {
        "title": "床",
        "min_affection": 58,
        "text": "你的床比猫窝大。\n所以今晚我睡你的床。\n你睡哪里自己想。\n——猫",
    },
    {
        "title": "这里有猫",
        "min_affection": 62,
        "text": "外面有一只猫看了我很久。\n我告诉它，这里已经有猫了。\n——猫",
    },
    {
        "title": "很高的评价",
        "min_affection": 66,
        "text": "你摸我的时候，我没有咬你。\n这是很高的评价。\n——猫",
    },
    {
        "title": "门口",
        "min_affection": 72,
        "text": "今天我在门口等了一会儿。\n不是等你。\n只是门口正好需要一只猫。\n——猫",
    },
    {
        "title": "我的",
        "min_affection": 78,
        "text": "这里的饭是我的，花盆是我的，窗台也是我的。\n你也是。\n（下面盖了两个很用力的爪印。）",
    },
]

POT_UNLOCK_COSTS = {4: 20, 5: 35, 6: 50}
MAX_POTS = 6
PEST_TREATMENT_COST = 2

CAT_ADOPT_COST = 100
CAT_NAME_MAX_LENGTH = 12
SAVE_FILE = "garden_cat_save.json"

GARDEN_EVENT_ACTIVE_SECONDS = 300
BUTTERFLY_APPEAR_MIN_SECONDS = 30 * 60
BUTTERFLY_APPEAR_MAX_SECONDS = 2 * 60 * 60
GARDEN_EVENT_SETTLE_MAX_STEPS = 256
COLLECTIBLE_CHECK_INTERVAL = 300
PEST_CHECK_INTERVAL = 300
TREATMENT_PROTECTION_SECONDS = 365 * 24 * 3600
PEST_TRIGGER_MIN_PERCENT = 20
PEST_TRIGGER_MAX_PERCENT = 100
CAT_PASSIVE_STAT_FLOOR = 20.0
LETTER_PROGRESS_BATCH = 4

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


def get_current_cat_name(state, default="猫咪"):
    cat = state.get("cat")
    if not isinstance(cat, dict):
        return default
    name = normalize_cat_name(cat.get("name"), default=None)
    if name is None or name == "小猫":
        return default
    cat_state = state.get("cat_state", {}) if isinstance(state.get("cat_state"), dict) else {}
    if cat_state.get("phase") == CAT_PHASE_WAITING_NAME:
        return default
    return name


def get_collectible_by_id(collectible_id):
    """按内部 id 获取猫咪收集品资料。"""
    return next(
        (item for item in CAT_COLLECTIBLES if item["id"] == collectible_id),
        None,
    )


def get_cat_max_affection(state):
    """返回猫咪历史最高亲密度；旧存档会至少继承当前亲密度。"""
    current = 0.0
    if isinstance(state.get("cat_stats"), dict):
        try:
            current = float(state["cat_stats"].get("affection", 0))
        except (TypeError, ValueError):
            current = 0.0

    try:
        recorded = float(state.get("cat_max_affection", 0))
    except (TypeError, ValueError):
        recorded = 0.0

    return min(100.0, max(0.0, current, recorded))


def update_cat_max_affection(state):
    """在亲密度上升后刷新历史最高值，并保证只增不减。"""
    if state.get("cat") is None or not isinstance(state.get("cat_stats"), dict):
        state["cat_max_affection"] = 0.0
        return 0.0

    maximum = get_cat_max_affection(state)
    state["cat_max_affection"] = maximum
    return maximum


def _get_next_letter(state):
    received = state.get("letters_received", [])
    if len(received) >= len(CAT_LETTERS):
        return None, None
    next_idx = len(received)
    return next_idx, CAT_LETTERS[next_idx]


def _build_letter_messages(state, letter):
    cat_name = get_current_cat_name(state)
    return [
        f"✉️ 收到{cat_name}的一封信！",
        f"《{letter['title']}》",
        letter["text"],
        f"当前已收集 {len(state['letters_received'])}/{len(CAT_LETTERS)}",
    ]


def _advance_cat_commitment_phase(state, now=None):
    cat_state = state.get("cat_state")
    stats = state.get("cat_stats")
    if not isinstance(cat_state, dict) or not isinstance(stats, dict):
        return False
    if now is None:
        now = int(time.time())
    if cat_state.get("phase") != CAT_PHASE_VISITOR:
        return False
    if get_cat_max_affection(state) < 30:
        return False
    return _enter_waiting_name_phase(state, now)


def _resolve_letter_progress(state, now=None, letter_context=None):
    if now is None:
        now = int(time.time())
    if letter_context is not None and int(letter_context.get("remaining_deliveries", 0)) <= 0:
        return []

    next_idx, next_letter = _get_next_letter(state)
    if next_letter is None:
        return []
    if get_cat_max_affection(state) < int(next_letter.get("min_affection", 0) or 0):
        return []

    progress = _safe_nonnegative_int(state.get("letter_affection_progress", 0), 0)
    delivered_messages = []
    while progress >= LETTER_PROGRESS_BATCH:
        progress -= LETTER_PROGRESS_BATCH
        if random.random() < 0.50:
            state["letters_received"].append(next_idx)
            state["letter_affection_progress"] = progress
            delivered_messages = _build_letter_messages(state, next_letter)
            cat_name = get_current_cat_name(state)
            add_event(state, f"✉️ 收到{cat_name}第{next_idx + 1}封信", now=now)
            if letter_context is not None:
                letter_context.setdefault("messages", []).extend(delivered_messages)
                letter_context["remaining_deliveries"] = max(
                    0,
                    int(letter_context.get("remaining_deliveries", 0)) - 1,
                )
            return delivered_messages

    state["letter_affection_progress"] = progress
    return []


def add_affection(state, amount, now=None, source=None, allow_letter_check=True, letter_context=None):
    if now is None:
        now = int(time.time())
    stats = _sync_cat_stats_views(state)
    if stats is None:
        return []

    amount_value = float(amount or 0)
    if amount_value <= 0:
        return []

    previous_max = get_cat_max_affection(state)
    _, next_letter = _get_next_letter(state)
    _set_cat_stat(state, "affection", stats.get("affection", 0.0) + amount_value)
    update_cat_max_affection(state)
    _advance_cat_commitment_phase(state, now)

    progress_gain = 0
    if next_letter is not None:
        threshold = int(next_letter.get("min_affection", 0) or 0)
        if previous_max >= threshold:
            progress_gain = int(amount_value)
        else:
            progress_gain = int(max(0.0, get_cat_max_affection(state) - threshold))
    if progress_gain > 0:
        state["letter_affection_progress"] = _safe_nonnegative_int(
            state.get("letter_affection_progress", 0),
            0,
        ) + progress_gain

    if not allow_letter_check:
        return []
    return _resolve_letter_progress(state, now=now, letter_context=letter_context)


def is_collectible_unlocked(state, item):
    """是否已永久解锁某件收集品。"""
    return get_cat_max_affection(state) >= float(item.get("unlock_affection", 10))


def get_collectible_unlock_hint(item):
    """收藏室中稳定显示的解锁条件。"""
    required = int(item.get("unlock_affection", 10))
    return f"曾达到亲密度{required}后，猫咪外出时可能带回。"


def get_collectible_boost_hint(item):
    """收藏室中显示的概率加成提示。"""
    return str(item.get("boost_hint", "")).strip()


def get_collectible_status_text(state, item):
    """未获得卡片使用的稳定状态文字，不受当前心情与昼夜起伏影响。"""
    if state.get("collectibles", {}).get(item["id"], 0) > 0:
        return "已经收集到。"
    if is_collectible_unlocked(state, item):
        return "条件已满足，猫咪外出时有机会带回。"
    return get_collectible_unlock_hint(item)


def get_collectible_rarity_weights(state, now=None):
    """按永久解锁阶段返回稀有度权重，并应用当前状态概率加成。"""
    if now is None:
        now = int(time.time())

    max_affection = get_cat_max_affection(state)
    weights = {"common": 0.0, "uncommon": 0.0, "rare": 0.0}
    for threshold, stage_weights in CAT_COLLECTIBLE_STAGE_RARITY_WEIGHTS:
        if max_affection >= threshold:
            weights = {key: float(value) for key, value in stage_weights.items()}
            break

    stats = state.get("cat_stats") or {}
    try:
        mood = float(stats.get("mood", 0))
    except (TypeError, ValueError):
        mood = 0.0

    _, game_hour, _ = get_game_time_info(state, now)
    is_night = game_hour >= 19 or game_hour < 5

    if weights["rare"] > 0:
        if is_night:
            weights["rare"] *= CAT_COLLECTIBLE_RARE_NIGHT_MULTIPLIER
        if mood >= CAT_COLLECTIBLE_RARE_HIGH_MOOD_THRESHOLD:
            weights["rare"] *= CAT_COLLECTIBLE_RARE_HIGH_MOOD_MULTIPLIER

    return weights


def get_eligible_cat_collectibles(state, now=None):
    """返回已经被历史最高亲密度永久解锁的收集品。"""
    if state.get("cat") is None or not isinstance(state.get("cat_stats"), dict):
        return []
    return [
        item
        for item in CAT_COLLECTIBLES
        if is_collectible_unlocked(state, item)
    ]


def _get_collectible_item_weight(item, mood, is_night):
    """同一稀有度内，根据当前状态调整单件物品的相对概率。"""
    weight = 1.0

    if item.get("night_multiplier") and is_night:
        weight *= float(item["night_multiplier"])

    mood_threshold = item.get("mood_threshold")
    if mood_threshold is not None and mood >= float(mood_threshold):
        weight *= float(item.get("mood_multiplier", 1.0))

    # 四叶草只有轻微的心情加成，不设置硬门槛。
    if item["id"] == "clover" and mood >= 60:
        weight *= 1.35

    return max(0.01, weight)


def choose_cat_collectible(state, now=None):
    """先抽稀有度，再在已永久解锁的同稀有度物品中完全随机抽取。

    已获得物品不会被排除，也不会给未获得物品额外权重。
    """
    if now is None:
        now = int(time.time())

    eligible = get_eligible_cat_collectibles(state, now)
    if not eligible:
        return None

    by_rarity = {}
    for item in eligible:
        by_rarity.setdefault(item["rarity"], []).append(item)

    rarity_weights = get_collectible_rarity_weights(state, now)
    rarities = [
        rarity
        for rarity, items in by_rarity.items()
        if items and rarity_weights.get(rarity, 0) > 0
    ]
    if not rarities:
        return None

    selected_rarity = random.choices(
        rarities,
        weights=[rarity_weights[rarity] for rarity in rarities],
        k=1,
    )[0]

    stats = state.get("cat_stats") or {}
    try:
        mood = float(stats.get("mood", 0))
    except (TypeError, ValueError):
        mood = 0.0
    _, game_hour, _ = get_game_time_info(state, now)
    is_night = game_hour >= 19 or game_hour < 5

    candidates = by_rarity[selected_rarity]
    item_weights = [
        _get_collectible_item_weight(item, mood, is_night)
        for item in candidates
    ]
    return random.choices(candidates, weights=item_weights, k=1)[0]


def are_cat_collectibles_unlocked(state):
    if bool(state.get("cat_collectibles_unlocked", False)):
        return True
    collectibles = state.get("collectibles", {})
    if not isinstance(collectibles, dict):
        return False
    return any(int(count or 0) > 0 for count in collectibles.values())


def unlock_cat_collectibles(state, now=None):
    if now is None:
        now = int(time.time())
    if are_cat_collectibles_unlocked(state):
        state["cat_collectibles_unlocked"] = True
        unlocked_at = _safe_nonnegative_int(state.get("cat_collectibles_unlocked_at", 0), 0)
        if unlocked_at > 0:
            state["cat_collectibles_unlocked_at"] = unlocked_at
        return False
    state["cat_collectibles_unlocked"] = True
    state["cat_collectibles_unlocked_at"] = int(now)
    return True


def get_collectible_unlock_affection(item):
    """现行藏品亲密度条件；普通藏品由首次吃喝开启。"""
    return None if item.get("rarity", "common") == "common" else CAT_COLLECTIBLE_UNLOCK_AFFECTION


def is_collectible_unlocked(state, item):
    rarity = str(item.get("rarity", "common"))
    max_affection = get_cat_max_affection(state)
    if rarity == "common":
        return are_cat_collectibles_unlocked(state)
    if rarity in ("uncommon", "rare"):
        return max_affection >= get_collectible_unlock_affection(item)
    return False


def get_collectible_unlock_hint(item):
    rarity = str(item.get("rarity", "common"))
    if rarity == "common":
        return "猫咪第一次实际吃饭或喝水后，完整来访或外出回家时可能带回。"
    return f"曾达到历史最高亲密度{get_collectible_unlock_affection(item)}后，猫咪外出回家时可能带回。"


def get_collectible_boost_hint(item):
    return ""


def get_collectible_status_text(state, item):
    if state.get("collectibles", {}).get(item["id"], 0) > 0:
        return "已经收集到。"
    if is_collectible_unlocked(state, item):
        if str(item.get("rarity", "common")) == "common":
            return "条件已满足，完整来访或外出回家时有机会带回。"
        return "条件已满足，猫咪外出回家时有机会带回。"
    return get_collectible_unlock_hint(item)


def get_collectible_rarity_weights(state, drop_context):
    if drop_context == "visitor":
        return {"common": 100.0, "uncommon": 0.0, "rare": 0.0}
    max_affection = get_cat_max_affection(state)
    if max_affection >= 66:
        return dict(CAT_COLLECTIBLE_RARITY_WEIGHTS_HIGH)
    if max_affection >= CAT_COLLECTIBLE_UNLOCK_AFFECTION:
        return dict(CAT_COLLECTIBLE_RARITY_WEIGHTS_MID)
    return {"common": 100.0, "uncommon": 0.0, "rare": 0.0}


def get_eligible_cat_collectibles(state, drop_context):
    if state.get("cat") is None or not isinstance(state.get("cat_stats"), dict):
        return []
    rarity_weights = get_collectible_rarity_weights(state, drop_context)
    return [
        item
        for item in CAT_COLLECTIBLES
        if rarity_weights.get(str(item.get("rarity", "")), 0) > 0
    ]


def _get_collectible_item_weight(state, item):
    owned = int(state.get("collectibles", {}).get(item["id"], 0) or 0)
    return 1.0 / (owned + 1)


def choose_cat_collectible(state, drop_context):
    eligible = get_eligible_cat_collectibles(state, drop_context)
    if not eligible:
        return None

    by_rarity = {}
    for item in eligible:
        by_rarity.setdefault(item["rarity"], []).append(item)

    rarity_weights = get_collectible_rarity_weights(state, drop_context)
    rarities = [
        rarity
        for rarity, items in by_rarity.items()
        if items and rarity_weights.get(rarity, 0) > 0
    ]
    if not rarities:
        return None

    selected_rarity = random.choices(
        rarities,
        weights=[rarity_weights[rarity] for rarity in rarities],
        k=1,
    )[0]
    candidates = by_rarity[selected_rarity]
    item_weights = [_get_collectible_item_weight(state, item) for item in candidates]
    return random.choices(candidates, weights=item_weights, k=1)[0]


def award_cat_collectible(state, collectible, now=None, source=None):
    if collectible is None:
        return None
    if now is None:
        now = int(time.time())
    collectible_id = collectible["id"]
    previous_count = int(state.get("collectibles", {}).get(collectible_id, 0) or 0)
    state.setdefault("collectibles", {})[collectible_id] = previous_count + 1
    if previous_count <= 0:
        state.setdefault("collectible_first_found", {})[collectible_id] = int(now)
    cat_name = get_current_cat_name(state)
    add_event(state, f"🎁 {cat_name}带回了{collectible['emoji']}{collectible['name']}", now=now)
    return f"🎁 {cat_name}带回了{collectible['emoji']}{collectible['name']}！"


def maybe_drop_cat_collectible(state, drop_context, now=None, source=None):
    if now is None:
        now = int(time.time())
    if not are_cat_collectibles_unlocked(state):
        return None
    if drop_context == "visitor":
        drop_rate = CAT_COLLECTIBLE_VISITOR_DROP_RATE
    elif drop_context == "adopted":
        drop_rate = CAT_COLLECTIBLE_ADOPTED_DROP_RATE
    else:
        return None
    if random.random() >= drop_rate:
        return None
    collectible = choose_cat_collectible(state, drop_context)
    message = award_cat_collectible(state, collectible, now=now, source=source)
    if not message:
        return None
    return collectible["id"], message


def _maybe_trigger_flower_shop_cat_buff(state, now, collectible_id, buff_windows=None):
    shop = state.get("flower_shop")
    if not isinstance(shop, dict) or not shop.get("established_at"):
        return None
    if random.random() >= FLOWER_SHOP_CAT_BUFF_CHANCE:
        return None
    start_at = int(now)
    until_at = start_at + FLOWER_SHOP_CAT_BUFF_DURATION_SECONDS
    shop["shop_buff_until"] = until_at
    shop["shop_buff_collectible_id"] = collectible_id
    if isinstance(buff_windows, list):
        buff_windows.append({"start_at": start_at, "until_at": until_at})
    message = "🐾 猫咪带回的小发现给花店添了好运，接下来4小时成交金额会提高。"
    add_event(state, message, now=start_at, area="flower_shop")
    return message


def get_collectible_unique_count(state):
    """返回已获得的不同收集品数量。"""
    valid_ids = {item["id"] for item in CAT_COLLECTIBLES}
    return sum(
        1
        for collectible_id, count in state.get("collectibles", {}).items()
        if collectible_id in valid_ids and int(count) > 0
    )


def get_garden_collectible_by_id(collectible_id):
    if collectible_id is None:
        return None
    return GARDEN_COLLECTIBLE_BY_ID.get(str(collectible_id))


def get_garden_collectible_unique_count(state):
    return sum(
        1
        for collectible_id, count in state.get("garden_collectibles", {}).items()
        if collectible_id in GARDEN_COLLECTIBLE_IDS and int(count) > 0
    )


def get_garden_flower_collectible_id(flower_id):
    return f"flower_{flower_id}"


def unlock_garden_collectible(state, collectible_id, now=None, source=None):
    collectible = get_garden_collectible_by_id(collectible_id)
    if collectible is None:
        return False, None
    if now is None:
        now = int(time.time())
    garden_collectibles = state.setdefault("garden_collectibles", {})
    if int(garden_collectibles.get(collectible["id"], 0) or 0) > 0:
        return False, collectible
    garden_collectibles[collectible["id"]] = 1
    state.setdefault("garden_collectible_first_found", {})[collectible["id"]] = int(now)
    collection_log = state.setdefault("garden_collection_log", [])
    collection_log.append(
        {
            "id": collectible["id"],
            "time": int(now),
            "source": str(source or collectible.get("source") or "garden"),
        }
    )
    if len(collection_log) > 40:
        del collection_log[:-40]
    return True, collectible


def build_garden_collectible_catalog(state):
    garden_collectibles = state.get("garden_collectibles", {})
    first_found = state.get("garden_collectible_first_found", {})
    return [
        {
            **item,
            "display_name": item["name"] if int(garden_collectibles.get(item["id"], 0) or 0) > 0 else "未发现",
            "owned": int(garden_collectibles.get(item["id"], 0) or 0) > 0,
            "count": int(garden_collectibles.get(item["id"], 0) or 0),
            "first_found_at": int(first_found.get(item["id"], 0) or 0),
        }
        for item in GARDEN_COLLECTIBLES
    ]


def _default_v5_cat_stats():
    return {"hunger": 70.0, "thirst": 70.0, "mood": 60.0, "affection": 0.0}


def _default_v5_cat_state(now: int):
    return {
        "phase": CAT_PHASE_VISITOR,
        "location": CAT_LOCATION_AWAY,
        "phase_changed_at": now,
        "location_changed_at": now,
        "first_visit_at": 0,
        "next_visit_at": now,
        "current_visit_started_at": 0,
        "current_visit_leave_at": 0,
        "stay_deadline_at": 0,
        "next_outing_at": 0,
        "outing_return_at": 0,
        "last_lifecycle_settled_at": now,
        "stats": _default_v5_cat_stats(),
    }


def _default_v5_cat_care():
    return {
        "bed": {
            "facility_id": DEFAULT_BASIC_CAT_BED_ID,
            "is_default": True,
        },
        "food_bowl": {
            "facility_id": DEFAULT_BASIC_FOOD_BOWL_ID,
            "is_default": True,
            "capacity": DEFAULT_FOOD_BOWL_CAPACITY,
            "remaining_portions": 0,
            "food_type": DEFAULT_CAT_FOOD_TYPE,
        },
        "water_bowl": {
            "facility_id": DEFAULT_BASIC_WATER_BOWL_ID,
            "is_default": True,
            "capacity": DEFAULT_WATER_BOWL_CAPACITY,
            "remaining_portions": 0,
        },
        "legacy_upgrades": {
            "cat_bed": False,
            "water_bowl": False,
            "food_bowl": False,
        },
    }


def _roll_cat_visit_interval_seconds():
    return random.randint(CAT_VISIT_INTERVAL_MIN_SECONDS, CAT_VISIT_INTERVAL_MAX_SECONDS)


def _roll_cat_visit_duration_seconds():
    return random.randint(CAT_VISIT_DURATION_MIN_SECONDS, CAT_VISIT_DURATION_MAX_SECONDS)


def _roll_cat_home_stay_seconds():
    return random.randint(CAT_HOME_STAY_MIN_SECONDS, CAT_HOME_STAY_MAX_SECONDS)


def _roll_cat_outing_duration_seconds():
    return random.randint(CAT_OUTING_DURATION_MIN_SECONDS, CAT_OUTING_DURATION_MAX_SECONDS)


def _ensure_cat_lifecycle_fields(cat_state, now):
    if not isinstance(cat_state, dict):
        cat_state = _default_v5_cat_state(now)
    for key, default_value in {
        "phase_changed_at": now,
        "location_changed_at": now,
        "first_visit_at": 0,
        "next_visit_at": now,
        "current_visit_started_at": 0,
        "current_visit_leave_at": 0,
        "stay_deadline_at": 0,
        "next_outing_at": 0,
        "outing_return_at": 0,
        "last_lifecycle_settled_at": now,
    }.items():
        cat_state[key] = _safe_nonnegative_int(cat_state.get(key, default_value), default_value)
    return cat_state


def _ensure_cat_identity(state):
    if not isinstance(state.get("cat"), dict):
        state["cat"] = {"name": "小猫"}
    else:
        normalized_name = normalize_cat_name(state["cat"].get("name"), default="小猫")
        state["cat"]["name"] = normalized_name or "小猫"


def _ensure_cat_stats_for_lifecycle(state):
    _ensure_cat_identity(state)
    stats = state.get("cat_stats")
    if not isinstance(stats, dict):
        pending_bonus = max(0, int(state.get("pending_cat_mood_bonus", 0) or 0))
        stats = _default_v5_cat_stats()
        stats["mood"] = min(100.0, stats["mood"] + pending_bonus)
        state["cat_stats"] = stats
        state["pending_cat_mood_bonus"] = 0
    for stat, default_value in _default_v5_cat_stats().items():
        try:
            state["cat_stats"][stat] = float(state["cat_stats"].get(stat, default_value))
        except (TypeError, ValueError, AttributeError):
            state["cat_stats"][stat] = float(default_value)
        state["cat_stats"][stat] = min(100.0, max(0.0, state["cat_stats"][stat]))
    update_cat_max_affection(state)
    return state["cat_stats"]


def _set_cat_phase(state, phase, now):
    cat_state = state.get("cat_state")
    if not isinstance(cat_state, dict):
        return
    if cat_state.get("phase") != phase:
        cat_state["phase"] = phase
        cat_state["phase_changed_at"] = now


def _set_cat_location(state, location, now):
    cat_state = state.get("cat_state")
    if not isinstance(cat_state, dict):
        return
    if cat_state.get("location") != location:
        cat_state["location"] = location
        cat_state["location_changed_at"] = now


def _schedule_next_visitor_visit(cat_state, base_time):
    cat_state["next_visit_at"] = base_time + _roll_cat_visit_interval_seconds()
    cat_state["current_visit_started_at"] = 0
    cat_state["current_visit_leave_at"] = 0


def _schedule_next_adopted_outing(cat_state, base_time):
    cat_state["next_outing_at"] = base_time + _roll_cat_home_stay_seconds()
    cat_state["outing_return_at"] = 0


def _enter_waiting_name_phase(state, now, *, force_location=CAT_LOCATION_GARDEN):
    cat_state = state.get("cat_state")
    if not isinstance(cat_state, dict):
        return False
    _ensure_cat_stats_for_lifecycle(state)
    changed = cat_state.get("phase") != CAT_PHASE_WAITING_NAME
    _set_cat_phase(state, CAT_PHASE_WAITING_NAME, now)
    _set_cat_location(state, force_location, now)
    cat_state["next_visit_at"] = 0
    cat_state["current_visit_started_at"] = max(
        _safe_nonnegative_int(cat_state.get("current_visit_started_at", 0), 0),
        _safe_nonnegative_int(cat_state.get("first_visit_at", now), now),
    )
    cat_state["current_visit_leave_at"] = 0
    cat_state["next_outing_at"] = 0
    cat_state["outing_return_at"] = 0
    return changed


def settle_cat_lifecycle(
    state, target_time, letter_context=None, shop_buff_windows=None, before_transition=None,
):
    if not isinstance(state, dict):
        return []

    cat_state = state.get("cat_state")
    if not isinstance(cat_state, dict):
        return []
    cat_state = _ensure_cat_lifecycle_fields(cat_state, target_time)

    try:
        target_time = int(target_time)
    except (TypeError, ValueError):
        target_time = int(time.time())

    phase = cat_state.get("phase")
    if phase not in VALID_CAT_PHASES:
        return []

    events = []
    settled_at = _safe_nonnegative_int(cat_state.get("last_lifecycle_settled_at", target_time), target_time)
    if target_time < settled_at:
        target_time = settled_at

    while True:
        phase = cat_state.get("phase")
        location = cat_state.get("location")

        if phase == CAT_PHASE_VISITOR:
            next_points = []
            next_visit_at = _safe_nonnegative_int(cat_state.get("next_visit_at", 0), 0)
            current_visit_leave_at = _safe_nonnegative_int(cat_state.get("current_visit_leave_at", 0), 0)
            if location == CAT_LOCATION_AWAY and next_visit_at > 0:
                next_points.append(next_visit_at)
            if location == CAT_LOCATION_GARDEN and current_visit_leave_at > 0:
                next_points.append(current_visit_leave_at)
            if not next_points:
                break

            next_transition_at = min(next_points)
            if next_transition_at > target_time:
                break
            if before_transition is not None:
                before_transition(next_transition_at)
                if cat_state.get("phase") != phase or cat_state.get("location") != location:
                    continue

            if location == CAT_LOCATION_AWAY and next_visit_at == next_transition_at:
                _ensure_cat_stats_for_lifecycle(state)
                stay_deadline_at = _safe_nonnegative_int(cat_state.get("stay_deadline_at", 0), 0)
                if stay_deadline_at > 0 and next_transition_at >= stay_deadline_at:
                    if _safe_nonnegative_int(cat_state.get("first_visit_at", 0), 0) <= 0:
                        cat_state["first_visit_at"] = next_transition_at
                    _enter_waiting_name_phase(state, next_transition_at)
                    cat_name = get_current_cat_name(state)
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。", now=next_transition_at, area="garden")
                    events.append(f"{cat_name}决定留下，正在等你正式取名。")
                    cat_state["last_lifecycle_settled_at"] = next_transition_at
                    continue
                _set_cat_location(state, CAT_LOCATION_GARDEN, next_transition_at)
                if _safe_nonnegative_int(cat_state.get("first_visit_at", 0), 0) <= 0:
                    cat_state["first_visit_at"] = next_transition_at
                    cat_state["stay_deadline_at"] = next_transition_at + CAT_STAY_DECISION_GRACE_SECONDS
                cat_state["current_visit_started_at"] = next_transition_at
                cat_state["current_visit_leave_at"] = next_transition_at + _roll_cat_visit_duration_seconds()
                cat_state["next_visit_at"] = 0
                _trigger_cat_bowls_for_auto_node(
                    state,
                    now=next_transition_at,
                    source="visit_arrival",
                    letter_context=letter_context,
                )
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}来了，正在花园里停留。", now=next_transition_at, area="garden")
                events.append(f"{cat_name}来了，正在花园里停留。")
                cat_state["last_lifecycle_settled_at"] = next_transition_at
                continue

            if location == CAT_LOCATION_GARDEN and current_visit_leave_at == next_transition_at:
                stay_deadline_at = _safe_nonnegative_int(cat_state.get("stay_deadline_at", 0), 0)
                max_affection = get_cat_max_affection(state)
                collectible_result = maybe_drop_cat_collectible(
                    state,
                    "visitor",
                    now=next_transition_at,
                    source="visit_complete",
                )
                if collectible_result:
                    events.append(collectible_result[1])
                if max_affection >= 30 or (stay_deadline_at > 0 and next_transition_at >= stay_deadline_at):
                    _enter_waiting_name_phase(state, next_transition_at)
                    cat_name = get_current_cat_name(state)
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。", now=next_transition_at, area="garden")
                    events.append(f"{cat_name}决定留下，正在等你正式取名。")
                    cat_state["last_lifecycle_settled_at"] = next_transition_at
                    continue

                _set_cat_location(state, CAT_LOCATION_AWAY, next_transition_at)
                cat_state["current_visit_leave_at"] = 0
                cat_state["current_visit_started_at"] = 0
                _schedule_next_visitor_visit(cat_state, next_transition_at)
                letter_messages = add_affection(
                    state,
                    1,
                    now=next_transition_at,
                    source="visit_complete",
                    letter_context=letter_context,
                )
                if cat_state.get("phase") == CAT_PHASE_WAITING_NAME:
                    cat_name = get_current_cat_name(state)
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。", now=next_transition_at, area="garden")
                    events.append(f"{cat_name}决定留下，正在等你正式取名。")
                    cat_state["last_lifecycle_settled_at"] = next_transition_at
                    continue
                if letter_context is None and letter_messages:
                    events.extend(letter_messages)
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}离开了花园，下次还会再来。", now=next_transition_at, area="garden")
                events.append(f"{cat_name}离开了花园，下次还会再来。")
                cat_state["last_lifecycle_settled_at"] = next_transition_at
                continue

        elif phase == CAT_PHASE_WAITING_NAME:
            _ensure_cat_stats_for_lifecycle(state)
            if location == CAT_LOCATION_AWAY:
                _set_cat_location(state, CAT_LOCATION_GARDEN, settled_at)
                _trigger_cat_bowls_for_auto_node(
                    state,
                    now=settled_at,
                    source="waiting_name_arrival",
                    letter_context=letter_context,
                )
            cat_state["next_visit_at"] = 0
            cat_state["current_visit_leave_at"] = 0
            cat_state["next_outing_at"] = 0
            cat_state["outing_return_at"] = 0
            break

        elif phase == CAT_PHASE_ADOPTED:
            _ensure_cat_stats_for_lifecycle(state)
            if location == CAT_LOCATION_HOME:
                next_outing_at = _safe_nonnegative_int(cat_state.get("next_outing_at", 0), 0)
                if next_outing_at <= 0:
                    _schedule_next_adopted_outing(cat_state, settled_at)
                    next_outing_at = cat_state["next_outing_at"]
                if next_outing_at > target_time:
                    break
                if before_transition is not None:
                    before_transition(next_outing_at)
                _set_cat_location(state, CAT_LOCATION_AWAY, next_outing_at)
                cat_state["outing_return_at"] = next_outing_at + _roll_cat_outing_duration_seconds()
                cat_state["next_outing_at"] = 0
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}出门溜达了一会儿。", now=next_outing_at)
                events.append(f"{cat_name}出门溜达了一会儿。")
                cat_state["last_lifecycle_settled_at"] = next_outing_at
                continue

            if location == CAT_LOCATION_AWAY:
                outing_return_at = _safe_nonnegative_int(cat_state.get("outing_return_at", 0), 0)
                if outing_return_at <= 0 or outing_return_at > target_time:
                    break
                if before_transition is not None:
                    before_transition(outing_return_at)
                _set_cat_location(state, CAT_LOCATION_HOME, outing_return_at)
                cat_state["outing_return_at"] = 0
                _schedule_next_adopted_outing(cat_state, outing_return_at)
                _trigger_cat_bowls_for_auto_node(
                    state,
                    now=outing_return_at,
                    source="outing_return",
                    letter_context=letter_context,
                )
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}回家了。", now=outing_return_at)
                events.append(f"{cat_name}回家了。")
                collectible_result = maybe_drop_cat_collectible(
                    state,
                    "adopted",
                    now=outing_return_at,
                    source="outing_return",
                )
                if collectible_result:
                    collectible_id, collectible_message = collectible_result
                    events.append(collectible_message)
                    buff_message = _maybe_trigger_flower_shop_cat_buff(
                        state,
                        outing_return_at,
                        collectible_id,
                        shop_buff_windows,
                    )
                    if buff_message:
                        events.append(buff_message)
                cat_state["last_lifecycle_settled_at"] = outing_return_at
                continue

        break

    cat_state["last_lifecycle_settled_at"] = target_time
    return events


def _default_offline_summary():
    return {
        "offline_seconds": 0,
        "settled_seconds": 0,
        "skipped_seconds": 0,
        "is_frozen": False,
        "message": "",
        "processed_at": 0,
        "auto_food_servings_used": 0,
        "auto_water_servings_used": 0,
    }


def _default_flower_shop_state():
    return {
        "established_at": None,
        "launched_at": None,
        "shelf_capacity": 0,
        "has_freshener": False,
        "shop_buff_until": 0,
        "shop_buff_collectible_id": None,
        "business_start_minute": None,
        "pending_business_start_minute": None,
        "pending_business_effective_at": None,
        "slots": [],
    }


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
        "cottage": {"items": {}},
        "last_update": now,
        "last_active_at": now,
        "cat_last_pet": 0,
        "encyclopedia": [],
        "flower_harvest_counts": {},
        "total_earned": 0,
        "direct_flower_sale_earned": 0,
        "weather": "sunny",
        "weather_change_time": now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX),
        "events": [],
        "garden_events": {},
        "rainbow_until": 0,
        "butterfly_until": 0,
        "last_rainbow_reward": None,
        "last_butterfly_reward": None,
        "next_butterfly_at": now + random.randint(BUTTERFLY_APPEAR_MIN_SECONDS, BUTTERFLY_APPEAR_MAX_SECONDS),
        "last_butterfly_at": 0,
        "pest_treatment": {},
        "collectibles": {},
        "collectible_first_found": {},
        "cat_collectibles_unlocked": False,
        "cat_collectibles_unlocked_at": 0,
        "garden_collectibles": {},
        "garden_collectible_first_found": {},
        "garden_collection_log": [],
        "bouquet_gifts": [],
        "bouquet_inventory": [],
        "human_last_read_bouquet_gift_count": 0,
        "flower_shop": _default_flower_shop_state(),
        "cat_state": _default_v5_cat_state(now),
        "cat_care": _default_v5_cat_care(),
        "cat_max_affection": 0.0,
        "letters_received": [],
        "letter_affection_progress": 0,
        "last_letter_check": now,
        "last_collectible_check": now,
        "last_butterfly_check": now,
        "game_start_time": now,
        "cat_last_pet_real_time": 0,
        "last_pest_check_time": now,
        "pending_cat_mood_bonus": 0,
        "offline_summary": _default_offline_summary(),
        "is_frozen": False,
        "garden_frozen_until": 0,
        "frozen_reason": "",
        "vase": [],
        "ai_v5_update_notice_seen": True,
    }


def apply_move_with_cat_reset(state, cat_name, now=None):
    if now is None:
        now = int(time.time())
    if not isinstance(state, dict):
        state = get_default_state()

    normalized_name = normalize_cat_name(cat_name, default="小猫") or "小猫"
    moved_stats = {"hunger": 60.0, "thirst": 60.0, "mood": 60.0, "affection": 30.0}

    state["cat"] = {"name": normalized_name}
    state["cat_stats"] = dict(moved_stats)
    state["cat_state"] = _default_v5_cat_state(now)
    state["cat_state"]["stats"] = dict(moved_stats)
    state["cat_care"] = _default_v5_cat_care()
    state["cat_max_affection"] = 30.0
    state["cat_last_pet"] = 0
    state["cat_last_pet_real_time"] = 0
    state["last_update"] = now
    state["last_active_at"] = now

    _set_cat_phase(state, CAT_PHASE_ADOPTED, now)
    _set_cat_location(state, CAT_LOCATION_HOME, now)
    state["cat_state"]["first_visit_at"] = 0
    state["cat_state"]["next_visit_at"] = 0
    state["cat_state"]["current_visit_started_at"] = 0
    state["cat_state"]["current_visit_leave_at"] = 0
    state["cat_state"]["stay_deadline_at"] = 0
    state["cat_state"]["outing_return_at"] = 0
    state["cat_state"]["last_lifecycle_settled_at"] = now
    _schedule_next_adopted_outing(state["cat_state"], now)
    _sync_cat_stats_views(state)
    return state


def _garden_event_reward_text(reward):
    if not isinstance(reward, dict):
        return ""
    reward_type = reward.get("type")
    if reward_type == "money":
        amount = _safe_nonnegative_int(reward.get("amount"), 0)
        return f"+{amount}金币" if amount > 0 else ""
    if reward_type == "seeds":
        flower_id = reward.get("flower")
        qty = _safe_nonnegative_int(reward.get("qty"), 0)
        flower = FLOWERS.get(flower_id)
        if flower is None or qty <= 0:
            return ""
        return f"{flower['name']}种子x{qty}"
    return str(reward.get("text", "") or "")


def refresh_garden_events(state, now=None):
    if now is None:
        now = int(time.time())

    weather_id = state.get("weather", "sunny")
    if weather_id not in WEATHER:
        weather_id = "sunny"

    pest_pots = []
    for idx, pot in enumerate(state.get("pots", [])):
        if not isinstance(pot, dict):
            continue
        pest_time = pot.get("pest_time")
        if pest_time is None:
            continue
        try:
            pest_time = int(pest_time)
        except (TypeError, ValueError):
            continue
        treatment_until = state.get("pest_treatment", {}).get(idx, 0)
        try:
            treatment_until = int(treatment_until)
        except (TypeError, ValueError):
            treatment_until = 0
        if pest_time > now and treatment_until <= now:
            pest_pots.append(idx + 1)

    rainbow_until = _safe_nonnegative_int(state.get("rainbow_until", 0), 0)
    butterfly_until = _safe_nonnegative_int(state.get("butterfly_until", 0), 0)

    existing = state.get("garden_events")
    if not isinstance(existing, dict):
        existing = {}

    garden_events = dict(existing)
    garden_events.update(
        {
            "weather": weather_id,
            "has_pests": bool(pest_pots),
            "pest_pots": pest_pots,
            "rainbow_active": rainbow_until > now,
            "rainbow_until": rainbow_until,
            "rainbow_reward": _garden_event_reward_text(state.get("last_rainbow_reward")),
            "butterfly_active": butterfly_until > now,
            "butterfly_until": butterfly_until,
            "butterfly_reward": _garden_event_reward_text(state.get("last_butterfly_reward")),
            "updated_at": now,
        }
    )
    state["garden_events"] = garden_events
    return garden_events


def _roll_weather_interval_seconds():
    try:
        return random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)
    except AssertionError:
        return random.randint(WEATHER_CHANGE_MIN // 12, WEATHER_CHANGE_MAX // 12) * 12


def _roll_butterfly_interval_seconds():
    return random.randint(BUTTERFLY_APPEAR_MIN_SECONDS, BUTTERFLY_APPEAR_MAX_SECONDS)


def _schedule_next_weather_change(state, base_time):
    state["weather_change_time"] = int(base_time) + _roll_weather_interval_seconds()


def _schedule_next_butterfly(state, base_time):
    state["next_butterfly_at"] = int(base_time) + _roll_butterfly_interval_seconds()


class _WeatherRollOptions(list):
    def __init__(self, current_weather):
        super().__init__(list(WEATHER.keys()))
        self._legacy_alias = [weather for weather in WEATHER if weather != current_weather]

    def __eq__(self, other):
        return list.__eq__(self, other) or other == self._legacy_alias


def _settle_rainbow_event(state, now, messages):
    if random.random() >= 0.30:
        return
    reward = random.choice(
        [
            {"type": "money", "amount": random.randint(8, 12)},
            {"type": "seeds", "flower": random.choice(["daisy", "tulip"]), "qty": 2},
        ]
    )
    state["rainbow_until"] = now + GARDEN_EVENT_ACTIVE_SECONDS
    state["last_rainbow_reward"] = dict(reward)
    if reward["type"] == "money":
        state["money"] += reward["amount"]
        messages.append(f"🌈 彩虹出现！获得{reward['amount']}金币！")
    else:
        flower_id = reward["flower"]
        state["inventory"]["seeds"][flower_id] = state["inventory"]["seeds"].get(flower_id, 0) + reward["qty"]
        messages.append(f"🌈 彩虹出现！获得{FLOWERS[flower_id]['name']}种子x{reward['qty']}！")
    add_event(state, "🌈 彩虹出现", now=now, area="garden")


def _settle_weather_event(state, now, messages, *, record_event):
    old_weather = state.get("weather", "sunny")
    if old_weather not in WEATHER:
        old_weather = "sunny"
    new_weather = random.choice(_WeatherRollOptions(old_weather))
    state["weather"] = new_weather
    _schedule_next_weather_change(state, now)
    new_weather_data = WEATHER[new_weather]
    if old_weather != new_weather:
        if record_event:
            add_event(state, f"天气变化：{WEATHER[old_weather]['name']} -> {new_weather_data['name']}", now=now, area="garden")
        messages.append(
            f"\n🌤️ 天气变化：{WEATHER[old_weather]['emoji']}{WEATHER[old_weather]['name']} -> "
            f"{new_weather_data['emoji']}{new_weather_data['name']}"
        )
    if new_weather == "rainy":
        auto_watered = _auto_water_pots(state, now)
        if auto_watered > 0:
            messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花。")
    if old_weather == "rainy" and new_weather == "sunny":
        _settle_rainbow_event(state, now, messages)
    return new_weather_data


def _settle_butterfly_event(state, now, messages, *, record_event):
    state["last_butterfly_at"] = int(now)
    state["butterfly_until"] = now + GARDEN_EVENT_ACTIVE_SECONDS
    state["last_butterfly_check"] = int(now)
    _schedule_next_butterfly(state, now)
    if random.random() >= 0.05:
        state["last_butterfly_reward"] = None
        return
    gold = random.randint(3, 5)
    state["money"] += gold
    state["last_butterfly_reward"] = {"type": "money", "amount": gold}
    messages.append(f"🦋 蝴蝶掉落了{gold}金币！")
    if record_event:
        add_event(state, f"🦋 蝴蝶掉落了{gold}金币", now=now, area="garden")


def _settle_garden_timeline(state, settle_at, *, collect_messages, advance_growth):
    messages = []
    weather_id = state.get("weather", "sunny")
    if weather_id not in WEATHER:
        weather_id = "sunny"
        state["weather"] = weather_id
    weather_data = WEATHER[weather_id]
    if (
        _safe_nonnegative_int(state.get("last_butterfly_at", 0), 0) <= 0
        and _safe_nonnegative_int(state.get("last_butterfly_check", 0), 0) <= 0
        and _safe_nonnegative_int(state.get("next_butterfly_at", 0), 0) > settle_at
    ):
        state["next_butterfly_at"] = settle_at
    steps = 0
    while steps < GARDEN_EVENT_SETTLE_MAX_STEPS:
        next_points = []
        weather_change_at = _safe_nonnegative_int(state.get("weather_change_time", 0), 0)
        next_butterfly_at = _safe_nonnegative_int(state.get("next_butterfly_at", 0), 0)
        if 0 < weather_change_at <= settle_at:
            next_points.append(("weather", weather_change_at))
        if 0 < next_butterfly_at <= settle_at:
            next_points.append(("butterfly", next_butterfly_at))
        if not next_points:
            break
        event_type, event_at = min(next_points, key=lambda item: (item[1], 0 if item[0] == "weather" else 1))
        if event_type == "weather":
            if advance_growth:
                update_flower_growth(state, event_at, weather_data)
            weather_data = _settle_weather_event(
                state,
                event_at,
                messages,
                record_event=collect_messages,
            )
        else:
            _settle_butterfly_event(
                state,
                event_at,
                messages,
                record_event=True,
            )
        steps += 1
    if steps >= GARDEN_EVENT_SETTLE_MAX_STEPS:
        if state.get("weather_change_time", 0) <= settle_at:
            _schedule_next_weather_change(state, settle_at)
        if state.get("next_butterfly_at", 0) <= settle_at:
            _schedule_next_butterfly(state, settle_at)
    return weather_data, messages


def get_game_hours(state, now=None):
    if now is None:
        now = int(time.time())
    elapsed_real_seconds = max(0, now - state.get("game_start_time", now))
    return elapsed_real_seconds / 3600


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


def _safe_nonnegative_int(value, default=0) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return int(default)
    return max(0, value)


def _is_premium_bed(bed):
    facility_id = str((bed or {}).get("facility_id", ""))
    return facility_id == PREMIUM_CAT_BED_ID


def _is_premium_water_bowl(water_bowl):
    facility_id = str((water_bowl or {}).get("facility_id", ""))
    return facility_id == PREMIUM_WATER_BOWL_ID


def _is_premium_food_bowl(food_bowl):
    facility_id = str((food_bowl or {}).get("facility_id", ""))
    return facility_id == PREMIUM_FOOD_BOWL_ID


def _apply_facility_purchase(state, item_id):
    care = state.setdefault("cat_care", _default_v5_cat_care())
    legacy = care.setdefault("legacy_upgrades", {"cat_bed": False, "water_bowl": False, "food_bowl": False})
    permanent_items = state.setdefault("permanent_items", [])
    if item_id not in permanent_items:
        permanent_items.append(item_id)

    if item_id == PREMIUM_CAT_BED_ID:
        care["bed"]["facility_id"] = PREMIUM_CAT_BED_ID
        care["bed"]["is_default"] = False
        legacy["cat_bed"] = True
    elif item_id == PREMIUM_WATER_BOWL_ID:
        current = care["water_bowl"]
        current["facility_id"] = PREMIUM_WATER_BOWL_ID
        current["is_default"] = False
        current["capacity"] = max(
            _safe_nonnegative_int(current.get("remaining_portions", 0), 0),
            PREMIUM_WATER_BOWL_CAPACITY,
        )
        legacy["water_bowl"] = True
    elif item_id == PREMIUM_FOOD_BOWL_ID:
        current = care["food_bowl"]
        current["facility_id"] = PREMIUM_FOOD_BOWL_ID
        current["is_default"] = False
        current["capacity"] = max(
            _safe_nonnegative_int(current.get("remaining_portions", 0), 0),
            PREMIUM_FOOD_BOWL_CAPACITY,
        )
        legacy["food_bowl"] = True


def _sync_owned_facilities(state):
    care = state.get("cat_care")
    if not isinstance(care, dict):
        return
    legacy = care.get("legacy_upgrades")
    if not isinstance(legacy, dict):
        legacy = {"cat_bed": False, "water_bowl": False, "food_bowl": False}
        care["legacy_upgrades"] = legacy
    permanent_items = set(state.get("permanent_items", []))

    if PREMIUM_CAT_BED_ID in permanent_items or legacy.get("cat_bed"):
        care["bed"]["facility_id"] = PREMIUM_CAT_BED_ID
        care["bed"]["is_default"] = False
        legacy["cat_bed"] = True
    if PREMIUM_WATER_BOWL_ID in permanent_items or legacy.get("water_bowl"):
        care["water_bowl"]["facility_id"] = PREMIUM_WATER_BOWL_ID
        care["water_bowl"]["is_default"] = False
        care["water_bowl"]["capacity"] = max(
            _safe_nonnegative_int(care["water_bowl"].get("remaining_portions", 0), 0),
            _safe_nonnegative_int(care["water_bowl"].get("capacity", DEFAULT_WATER_BOWL_CAPACITY), DEFAULT_WATER_BOWL_CAPACITY),
            PREMIUM_WATER_BOWL_CAPACITY,
        )
        legacy["water_bowl"] = True
    if PREMIUM_FOOD_BOWL_ID in permanent_items or legacy.get("food_bowl"):
        care["food_bowl"]["facility_id"] = PREMIUM_FOOD_BOWL_ID
        care["food_bowl"]["is_default"] = False
        care["food_bowl"]["capacity"] = max(
            _safe_nonnegative_int(care["food_bowl"].get("remaining_portions", 0), 0),
            _safe_nonnegative_int(care["food_bowl"].get("capacity", DEFAULT_FOOD_BOWL_CAPACITY), DEFAULT_FOOD_BOWL_CAPACITY),
            PREMIUM_FOOD_BOWL_CAPACITY,
        )
        legacy["food_bowl"] = True


def _owns_facility(state, item_id):
    care = state.get("cat_care", {})
    legacy = care.get("legacy_upgrades", {})
    permanent_items = set(state.get("permanent_items", []))
    if item_id == PREMIUM_CAT_BED_ID:
        return item_id in permanent_items or bool(legacy.get("cat_bed")) or _is_premium_bed(care.get("bed"))
    if item_id == PREMIUM_WATER_BOWL_ID:
        return item_id in permanent_items or bool(legacy.get("water_bowl")) or _is_premium_water_bowl(care.get("water_bowl"))
    if item_id == PREMIUM_FOOD_BOWL_ID:
        return item_id in permanent_items or bool(legacy.get("food_bowl")) or _is_premium_food_bowl(care.get("food_bowl"))
    return item_id in permanent_items


def _get_cat_facility_labels(state):
    care = state.get("cat_care", {})
    bed = care.get("bed", {})
    food_bowl = care.get("food_bowl", {})
    water_bowl = care.get("water_bowl", {})
    return {
        "bed": "高级猫窝" if _is_premium_bed(bed) else "普通猫窝",
        "food_bowl": "高级粮碗" if _is_premium_food_bowl(food_bowl) else "普通粮碗",
        "water_bowl": "高级水碗" if _is_premium_water_bowl(water_bowl) else "普通水碗",
    }


def _normalize_v5_cat_foundation(data, now, had_cat_state=False):
    has_legacy_cat = isinstance(data.get("cat"), dict)
    phase_default = CAT_PHASE_ADOPTED if has_legacy_cat else CAT_PHASE_VISITOR
    location_default = CAT_LOCATION_HOME if phase_default == CAT_PHASE_ADOPTED else CAT_LOCATION_AWAY

    raw_cat_state = data.get("cat_state")
    if not had_cat_state or not isinstance(raw_cat_state, dict):
        raw_cat_state = {}
    phase = str(raw_cat_state.get("phase", phase_default))
    if phase not in VALID_CAT_PHASES:
        phase = phase_default
    if has_legacy_cat and not had_cat_state and phase == CAT_PHASE_VISITOR:
        phase = CAT_PHASE_ADOPTED
        location_default = CAT_LOCATION_HOME
    location = str(raw_cat_state.get("location", location_default))
    if location not in VALID_CAT_LOCATIONS:
        location = location_default
    if phase == CAT_PHASE_ADOPTED and location == CAT_LOCATION_GARDEN:
        location = CAT_LOCATION_HOME
    elif phase == CAT_PHASE_ADOPTED and has_legacy_cat and not had_cat_state and location == CAT_LOCATION_AWAY:
        location = CAT_LOCATION_HOME
    elif phase == CAT_PHASE_WAITING_NAME and location == CAT_LOCATION_AWAY:
        location = CAT_LOCATION_GARDEN
    elif phase == CAT_PHASE_VISITOR and location == CAT_LOCATION_HOME:
        location = CAT_LOCATION_AWAY

    stats_defaults = _default_v5_cat_stats()
    stats_source = data.get("cat_stats") if isinstance(data.get("cat_stats"), dict) else raw_cat_state.get("stats", {})
    stats = {}
    for stat, default_value in stats_defaults.items():
        try:
            stats[stat] = float(stats_source.get(stat, default_value))
        except (TypeError, ValueError, AttributeError):
            stats[stat] = float(default_value)
        stats[stat] = min(100.0, max(0.0, stats[stat]))

    data["cat_state"] = {
        "phase": phase,
        "location": location,
        "phase_changed_at": _safe_nonnegative_int(raw_cat_state.get("phase_changed_at", now), now),
        "location_changed_at": _safe_nonnegative_int(raw_cat_state.get("location_changed_at", now), now),
        "stats": stats,
    }
    for field in (
        "first_visit_at",
        "next_visit_at",
        "current_visit_started_at",
        "current_visit_leave_at",
        "stay_deadline_at",
        "next_outing_at",
        "outing_return_at",
        "last_lifecycle_settled_at",
    ):
        if field in raw_cat_state:
            data["cat_state"][field] = raw_cat_state.get(field)
    _ensure_cat_lifecycle_fields(data["cat_state"], now)
    data["cat_state"]["phase"] = phase
    data["cat_state"]["location"] = location
    data["cat_state"]["phase_changed_at"] = _safe_nonnegative_int(raw_cat_state.get("phase_changed_at", now), now)
    data["cat_state"]["location_changed_at"] = _safe_nonnegative_int(raw_cat_state.get("location_changed_at", now), now)

    cat_state = data["cat_state"]
    if phase == CAT_PHASE_VISITOR:
        if cat_state["location"] == CAT_LOCATION_AWAY and cat_state["next_visit_at"] <= 0:
            cat_state["next_visit_at"] = now
        if cat_state["location"] == CAT_LOCATION_GARDEN and cat_state["current_visit_leave_at"] <= 0:
            cat_state["current_visit_started_at"] = max(
                _safe_nonnegative_int(cat_state.get("current_visit_started_at", 0), 0),
                now,
            )
            if cat_state["first_visit_at"] <= 0:
                cat_state["first_visit_at"] = cat_state["current_visit_started_at"]
                cat_state["stay_deadline_at"] = cat_state["first_visit_at"] + CAT_STAY_DECISION_GRACE_SECONDS
            cat_state["current_visit_leave_at"] = (
                cat_state["current_visit_started_at"] + _roll_cat_visit_duration_seconds()
            )
        if cat_state["first_visit_at"] > 0 and cat_state["stay_deadline_at"] <= 0:
            cat_state["stay_deadline_at"] = cat_state["first_visit_at"] + CAT_STAY_DECISION_GRACE_SECONDS
    elif phase == CAT_PHASE_WAITING_NAME:
        if cat_state["first_visit_at"] <= 0:
            cat_state["first_visit_at"] = now
        if cat_state["stay_deadline_at"] <= 0:
            cat_state["stay_deadline_at"] = cat_state["first_visit_at"] + CAT_STAY_DECISION_GRACE_SECONDS
        cat_state["next_visit_at"] = 0
        cat_state["current_visit_leave_at"] = 0
        cat_state["next_outing_at"] = 0
        cat_state["outing_return_at"] = 0
    else:
        cat_state["next_visit_at"] = 0
        cat_state["current_visit_started_at"] = 0
        cat_state["current_visit_leave_at"] = 0
        if cat_state["next_outing_at"] <= 0 and cat_state["location"] == CAT_LOCATION_HOME:
            cat_state["next_outing_at"] = now + _roll_cat_home_stay_seconds()
        if cat_state["location"] == CAT_LOCATION_AWAY and cat_state["outing_return_at"] <= 0:
            cat_state["outing_return_at"] = now + _roll_cat_outing_duration_seconds()

    raw_cat_care = data.get("cat_care")
    if not isinstance(raw_cat_care, dict):
        raw_cat_care = {}
    raw_food_bowl = raw_cat_care.get("food_bowl")
    if not isinstance(raw_food_bowl, dict):
        raw_food_bowl = {}
    raw_water_bowl = raw_cat_care.get("water_bowl")
    if not isinstance(raw_water_bowl, dict):
        raw_water_bowl = {}
    raw_bed = raw_cat_care.get("bed")
    if not isinstance(raw_bed, dict):
        raw_bed = {}
    raw_legacy_upgrades = raw_cat_care.get("legacy_upgrades")
    if not isinstance(raw_legacy_upgrades, dict):
        raw_legacy_upgrades = {}

    food_type = str(raw_food_bowl.get("food_type", DEFAULT_CAT_FOOD_TYPE))
    if food_type not in ("basic_food", "premium_food"):
        food_type = DEFAULT_CAT_FOOD_TYPE

    permanent_items = set(data.get("permanent_items", []))
    data["cat_care"] = {
        "bed": {
            "facility_id": str(raw_bed.get("facility_id", DEFAULT_BASIC_CAT_BED_ID)),
            "is_default": bool(raw_bed.get("is_default", True)),
        },
        "food_bowl": {
            "facility_id": str(raw_food_bowl.get("facility_id", DEFAULT_BASIC_FOOD_BOWL_ID)),
            "is_default": bool(raw_food_bowl.get("is_default", True)),
            "capacity": _safe_nonnegative_int(
                raw_food_bowl.get("capacity", DEFAULT_FOOD_BOWL_CAPACITY), DEFAULT_FOOD_BOWL_CAPACITY
            ),
            "remaining_portions": _safe_nonnegative_int(raw_food_bowl.get("remaining_portions", 0), 0),
            "food_type": food_type,
        },
        "water_bowl": {
            "facility_id": str(raw_water_bowl.get("facility_id", DEFAULT_BASIC_WATER_BOWL_ID)),
            "is_default": bool(raw_water_bowl.get("is_default", True)),
            "capacity": _safe_nonnegative_int(
                raw_water_bowl.get("capacity", DEFAULT_WATER_BOWL_CAPACITY), DEFAULT_WATER_BOWL_CAPACITY
            ),
            "remaining_portions": _safe_nonnegative_int(raw_water_bowl.get("remaining_portions", 0), 0),
        },
        "legacy_upgrades": {
            "cat_bed": bool(raw_legacy_upgrades.get("cat_bed")) or "cat_bed" in permanent_items,
            "water_bowl": bool(raw_legacy_upgrades.get("water_bowl")) or "water_bowl" in permanent_items,
            "food_bowl": bool(raw_legacy_upgrades.get("food_bowl")) or "food_bowl" in permanent_items,
        },
    }
    _sync_owned_facilities(data)


def _get_adopted_cat_message(state):
    phase = state.get("cat_state", {}).get("phase")
    if phase == CAT_PHASE_WAITING_NAME:
        return "❌ 猫咪还在等待正式取名，暂时不能使用照料命令。"
    return "❌ 只有已正式收养的猫咪才能使用这个照料命令。"


def _has_adopted_cat(state):
    return (
        isinstance(state.get("cat"), dict)
        and isinstance(state.get("cat_state"), dict)
        and state["cat_state"].get("phase") == CAT_PHASE_ADOPTED
    )


def _sync_cat_stats_views(state):
    if not isinstance(state.get("cat"), dict):
        return None

    if not isinstance(state.get("cat_state"), dict):
        state["cat_state"] = _default_v5_cat_state(int(time.time()))
    else:
        _ensure_cat_lifecycle_fields(state["cat_state"], int(time.time()))
    if not isinstance(state["cat_state"].get("stats"), dict):
        state["cat_state"]["stats"] = _default_v5_cat_stats()

    stats_source = state["cat_stats"] if isinstance(state.get("cat_stats"), dict) else state["cat_state"]["stats"]
    merged = {}
    for stat, default_value in _default_v5_cat_stats().items():
        try:
            merged[stat] = float(stats_source.get(stat, default_value))
        except (TypeError, ValueError, AttributeError):
            merged[stat] = float(default_value)
        merged[stat] = min(100.0, max(0.0, merged[stat]))

    state["cat_stats"] = dict(merged)
    state["cat_state"]["stats"] = dict(merged)
    return state["cat_stats"]


def _set_cat_stat(state, stat, value):
    stats = _sync_cat_stats_views(state)
    if stats is None:
        return
    stats[stat] = min(100.0, max(0.0, float(value)))
    state["cat_state"]["stats"][stat] = stats[stat]


def _change_cat_stat(state, stat, delta):
    stats = _sync_cat_stats_views(state)
    if stats is None:
        return
    _set_cat_stat(state, stat, stats.get(stat, 0.0) + delta)


def _apply_cat_effects(state, effects, now=None, source=None, letter_context=None):
    if not isinstance(effects, dict):
        return []
    if state.get("_interaction_accepted") is False and source in {
        "give_treat",
        "play:ball",
        "play:feather_wand",
    }:
        return []
    letter_messages = []
    for stat, value in effects.items():
        if stat == "affection":
            letter_messages.extend(
                add_affection(
                    state,
                    value,
                    now=now,
                    source=source,
                    letter_context=letter_context,
                )
            )
        else:
            _change_cat_stat(state, stat, value)
    return letter_messages


def _use_inventory_item(state, item_id, quantity=1):
    if state.get("_interaction_accepted") is False and item_id in {
        CAT_TREAT_ITEM_ID,
        "ball",
        "feather_wand",
    }:
        return False
    items = state.get("inventory", {}).get("items", {})
    if items.get(item_id, 0) < quantity:
        return False
    items[item_id] -= quantity
    if items[item_id] <= 0:
        del items[item_id]
    return True


def _add_inventory_item(state, item_id, quantity=1):
    if quantity <= 0:
        return
    items = state.setdefault("inventory", {}).setdefault("items", {})
    items[item_id] = items.get(item_id, 0) + quantity


def _get_cat_interaction_stage(state):
    phase = state.get("cat_state", {}).get("phase")
    if phase == CAT_PHASE_ADOPTED:
        return "adopted"
    return "visitor"


def _is_cat_present_for_interaction(state):
    if not isinstance(state.get("cat"), dict):
        return False
    return state.get("cat_state", {}).get("location") in (CAT_LOCATION_GARDEN, CAT_LOCATION_HOME)


def _is_cat_near_bowls(state):
    if not _is_cat_present_for_interaction(state):
        return False
    phase = state.get("cat_state", {}).get("phase")
    location = state.get("cat_state", {}).get("location")
    if phase in (CAT_PHASE_VISITOR, CAT_PHASE_WAITING_NAME):
        return location == CAT_LOCATION_GARDEN
    if phase == CAT_PHASE_ADOPTED:
        return location == CAT_LOCATION_HOME
    return False


def _get_food_roll_chance(hunger):
    hunger = float(hunger)
    if hunger <= 30:
        return 1.0
    if hunger <= 50:
        return 0.80
    if hunger <= 70:
        return 0.50
    if hunger <= 85:
        return 0.20
    return 0.0


def _get_water_roll_chance(thirst):
    thirst = float(thirst)
    if thirst <= 25:
        return 1.0
    if thirst <= 50:
        return 0.90
    if thirst <= 70:
        return 0.60
    if thirst <= 85:
        return 0.25
    return 0.0


def _consume_food_serving(state, food_type, now=None, source=None, letter_context=None):
    unlock_cat_collectibles(state, now=now)
    food_effects = ITEMS.get(food_type, ITEMS[DEFAULT_CAT_FOOD_TYPE]).get("effect", {})
    _apply_cat_effects(
        state,
        food_effects,
        now=now,
        source=source,
        letter_context=letter_context,
    )
    return add_affection(
        state,
        1,
        now=now,
        source=source,
        letter_context=letter_context,
    )


def _consume_water_serving(state, now=None, source=None, letter_context=None):
    unlock_cat_collectibles(state, now=now)
    _change_cat_stat(state, "thirst", 20)
    return add_affection(
        state,
        1,
        now=now,
        source=source,
        letter_context=letter_context,
    )


def _record_cat_care_event(state, event_text, *, source=None, now=None):
    if source in {"offline_food", "offline_water"}:
        return
    add_event(state, event_text, now=now)


def _trigger_food_bowl_roll(state, now=None, source=None, letter_context=None):
    if not _is_cat_near_bowls(state):
        return 0, []
    food_bowl = state.get("cat_care", {}).get("food_bowl", {})
    servings_eaten = 0
    letter_messages = []
    while _safe_nonnegative_int(food_bowl.get("remaining_portions", 0), 0) > 0:
        stats = _sync_cat_stats_views(state)
        if random.random() >= _get_food_roll_chance(stats.get("hunger", 0.0)):
            break
        food_bowl["remaining_portions"] = max(
            0,
            _safe_nonnegative_int(food_bowl.get("remaining_portions", 0), 0) - 1,
        )
        servings_eaten += 1
        food_type = str(food_bowl.get("food_type", DEFAULT_CAT_FOOD_TYPE))
        letter_messages.extend(
            _consume_food_serving(
                state,
                food_type,
                now=now,
                source=source,
                letter_context=letter_context,
            )
        )
    if servings_eaten > 0:
        food_type = str(food_bowl.get("food_type", DEFAULT_CAT_FOOD_TYPE))
        food_name = ITEMS.get(food_type, ITEMS[DEFAULT_CAT_FOOD_TYPE]).get("name", ITEMS[DEFAULT_CAT_FOOD_TYPE]["name"])
        cat_name = get_current_cat_name(state)
        _record_cat_care_event(state, f"{cat_name}吃了{servings_eaten}份{food_name}。", source=source, now=now)
    return servings_eaten, letter_messages


def _trigger_water_bowl_roll(state, now=None, source=None, letter_context=None):
    if not _is_cat_near_bowls(state):
        return 0, []
    water_bowl = state.get("cat_care", {}).get("water_bowl", {})
    servings_drank = 0
    letter_messages = []
    while _safe_nonnegative_int(water_bowl.get("remaining_portions", 0), 0) > 0:
        stats = _sync_cat_stats_views(state)
        if random.random() >= _get_water_roll_chance(stats.get("thirst", 0.0)):
            break
        water_bowl["remaining_portions"] = max(
            0,
            _safe_nonnegative_int(water_bowl.get("remaining_portions", 0), 0) - 1,
        )
        servings_drank += 1
        letter_messages.extend(
            _consume_water_serving(
                state,
                now=now,
                source=source,
                letter_context=letter_context,
            )
        )
    if servings_drank > 0:
        cat_name = get_current_cat_name(state)
        _record_cat_care_event(state, f"{cat_name}喝了{servings_drank}份水。", source=source, now=now)
    return servings_drank, letter_messages


CAT_AUTO_FOOD_THRESHOLDS = (85.0, 70.0, 50.0, 30.0)
CAT_AUTO_WATER_THRESHOLDS = (85.0, 70.0, 50.0, 25.0)


def _crossed_lower_stat_band(start_value, end_value, thresholds):
    try:
        start_value = float(start_value)
        end_value = float(end_value)
    except (TypeError, ValueError):
        return False
    if end_value >= start_value:
        return False
    return any(start_value > threshold >= end_value for threshold in thresholds)


def _should_auto_food_roll(start_hunger, end_hunger):
    if _crossed_lower_stat_band(start_hunger, end_hunger, CAT_AUTO_FOOD_THRESHOLDS):
        return True
    try:
        return float(start_hunger) <= CAT_PASSIVE_STAT_FLOOR and float(end_hunger) <= CAT_PASSIVE_STAT_FLOOR
    except (TypeError, ValueError):
        return False


def _should_auto_water_roll(start_thirst, end_thirst):
    if _crossed_lower_stat_band(start_thirst, end_thirst, CAT_AUTO_WATER_THRESHOLDS):
        return True
    try:
        return float(start_thirst) <= CAT_PASSIVE_STAT_FLOOR and float(end_thirst) <= CAT_PASSIVE_STAT_FLOOR
    except (TypeError, ValueError):
        return False


def _remember_auto_bowl_usage(state, food_used=0, water_used=0):
    if food_used > 0:
        state["_auto_food_servings_used"] = _safe_nonnegative_int(
            state.get("_auto_food_servings_used", 0),
            0,
        ) + int(food_used)
    if water_used > 0:
        state["_auto_water_servings_used"] = _safe_nonnegative_int(
            state.get("_auto_water_servings_used", 0),
            0,
        ) + int(water_used)


def _trigger_cat_bowls_for_auto_node(
    state,
    *,
    now=None,
    source="auto_bowl",
    letter_context=None,
    food=True,
    water=True,
):
    if not _is_cat_near_bowls(state):
        return 0, 0, []
    used_food = 0
    used_water = 0
    letter_messages = []
    if food:
        used_food, messages = _trigger_food_bowl_roll(
            state,
            now=now,
            source=f"{source}:food",
            letter_context=letter_context,
        )
        letter_messages.extend(messages)
    if water:
        used_water, messages = _trigger_water_bowl_roll(
            state,
            now=now,
            source=f"{source}:water",
            letter_context=letter_context,
        )
        letter_messages.extend(messages)
    _remember_auto_bowl_usage(state, used_food, used_water)
    return used_food, used_water, letter_messages


def _get_interaction_acceptance_rate(state, interaction_id):
    stage = _get_cat_interaction_stage(state)
    table = CAT_INTERACTION_ACCEPTANCE.get(interaction_id, {})
    return float(table.get(stage, 0.0))


def _roll_interaction_acceptance(state, interaction_id):
    return random.random() < _get_interaction_acceptance_rate(state, interaction_id)


def _refill_food_bowl(state, requested_food_type, now=None, source=None, letter_context=None):
    bowl = state["cat_care"]["food_bowl"]
    original_remaining = _safe_nonnegative_int(bowl.get("remaining_portions", 0), 0)
    refill_type = str(bowl.get("food_type", DEFAULT_CAT_FOOD_TYPE)) if original_remaining > 0 else requested_food_type
    space = max(0, bowl["capacity"] - original_remaining)
    available = state["inventory"]["items"].get(refill_type, 0)
    added = min(space, available)
    bowl["food_type"] = refill_type
    if added > 0:
        _use_inventory_item(state, refill_type, added)
        bowl["remaining_portions"] = original_remaining + added
        food_name = ITEMS.get(refill_type, ITEMS[DEFAULT_CAT_FOOD_TYPE]).get("name", ITEMS[DEFAULT_CAT_FOOD_TYPE]["name"])
        _record_cat_care_event(state, f"给粮碗补充了{food_name}。", source=source)
    eaten = 0
    if original_remaining <= 0 and added > 0:
        eaten, _ = _trigger_food_bowl_roll(
            state,
            now=now,
            source=source,
            letter_context=letter_context,
        )
    return {
        "space": space,
        "added": added,
        "eaten": eaten,
        "refill_type": refill_type,
        "requested_food_type": requested_food_type,
        "original_remaining": original_remaining,
    }


def _refill_water_bowl(state, now=None, source=None, letter_context=None):
    bowl = state["cat_care"]["water_bowl"]
    original_remaining = _safe_nonnegative_int(bowl.get("remaining_portions", 0), 0)
    space = max(0, bowl["capacity"] - original_remaining)
    if space > 0:
        bowl["remaining_portions"] = original_remaining + space
        _record_cat_care_event(state, "给水碗补满了水。", source=source)
    drank = 0
    if original_remaining <= 0 and space > 0:
        drank, _ = _trigger_water_bowl_roll(
            state,
            now=now,
            source=source,
            letter_context=letter_context,
        )
    return {
        "space": space,
        "drank": drank,
        "original_remaining": original_remaining,
    }


def _switch_food_bowl(state, new_type, now=None, source=None, letter_context=None):
    bowl = state["cat_care"]["food_bowl"]
    old_type = str(bowl.get("food_type", DEFAULT_CAT_FOOD_TYPE))
    old_remaining = _safe_nonnegative_int(bowl.get("remaining_portions", 0), 0)
    if old_remaining > 0:
        _add_inventory_item(state, old_type, old_remaining)
    bowl["food_type"] = new_type
    bowl["remaining_portions"] = 0
    refill_amount = min(bowl["capacity"], state["inventory"]["items"].get(new_type, 0))
    if refill_amount > 0:
        _use_inventory_item(state, new_type, refill_amount)
        bowl["remaining_portions"] = refill_amount
    eaten = 0
    if refill_amount > 0 and _is_cat_near_bowls(state):
        eaten, _ = _trigger_food_bowl_roll(
            state,
            now=now,
            source=source,
            letter_context=letter_context,
        )
    return {
        "old_type": old_type,
        "old_remaining": old_remaining,
        "refill_amount": refill_amount,
        "eaten": eaten,
    }


def _can_finalize_adoption(state):
    phase = state.get("cat_state", {}).get("phase")
    return phase == CAT_PHASE_WAITING_NAME


def _normalize_bouquet_inventory(raw_inventory):
    inventory = []
    seen_ids = set()
    if not isinstance(raw_inventory, list):
        return inventory
    for entry in raw_inventory:
        if not isinstance(entry, dict):
            continue
        instance_id = str(entry.get("instance_id", "") or "").strip()
        bouquet_id = str(entry.get("bouquet_id", "") or "").strip()
        components = entry.get("components")
        if not instance_id or instance_id in seen_ids or not bouquet_id or not isinstance(components, dict):
            continue
        snapshot = {}
        for flower_id, quantity in components.items():
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue
            if quantity > 0:
                snapshot[str(flower_id)] = quantity
        if not snapshot:
            continue
        seen_ids.add(instance_id)
        inventory.append(
            {"instance_id": instance_id, "bouquet_id": bouquet_id, "components": snapshot}
        )
    return inventory


def _nullable_positive_int(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _default_flower_shop_pricing_profile():
    return [
        {"until_seconds": until_seconds, "multiplier": multiplier, "label": label}
        for until_seconds, multiplier, label in FLOWER_SHOP_BASE_PRICING_PROFILE
    ]


def _freshener_flower_shop_pricing_profile():
    return [
        {"until_seconds": until_seconds, "multiplier": multiplier, "label": label}
        for until_seconds, multiplier, label in FLOWER_SHOP_FRESHENER_PRICING_PROFILE
    ]


def _normalize_flower_shop_pricing_profile(raw_profile):
    if not isinstance(raw_profile, list) or not raw_profile:
        return _default_flower_shop_pricing_profile()
    profile = []
    previous_until = 0
    for entry in raw_profile:
        if not isinstance(entry, dict):
            return _default_flower_shop_pricing_profile()
        try:
            until_seconds = int(entry.get("until_seconds", 0))
            multiplier = float(entry.get("multiplier", 0))
        except (TypeError, ValueError):
            return _default_flower_shop_pricing_profile()
        if until_seconds <= previous_until or multiplier <= 0:
            return _default_flower_shop_pricing_profile()
        profile.append(
            {
                "until_seconds": until_seconds,
                "multiplier": multiplier,
                "label": str(entry.get("label", "") or ""),
            }
        )
        previous_until = until_seconds
    if profile[-1]["until_seconds"] != FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS:
        return _default_flower_shop_pricing_profile()
    return profile


def _normalize_flower_shop_slot(raw_slot):
    if not isinstance(raw_slot, dict):
        return None
    instance_id = str(raw_slot.get("instance_id", "") or "").strip()
    bouquet_id = str(raw_slot.get("bouquet_id", "") or "").strip()
    components = raw_slot.get("components")
    if not instance_id or not bouquet_id or not isinstance(components, dict):
        return None
    component_snapshot = {}
    for flower_id, quantity in components.items():
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            component_snapshot[str(flower_id)] = quantity
    if not component_snapshot:
        return None
    listed_at = _nullable_positive_int(raw_slot.get("listed_at"))
    last_settled_at = _nullable_positive_int(raw_slot.get("last_settled_at"))
    try:
        base_price = int(raw_slot.get("base_price", 0))
    except (TypeError, ValueError):
        base_price = 0
    will_sell = raw_slot.get("will_sell")
    if listed_at is None or last_settled_at is None or base_price <= 0 or not isinstance(will_sell, bool):
        return None
    try:
        remaining = int(raw_slot.get("sale_business_seconds_remaining", 0))
    except (TypeError, ValueError):
        return None
    if remaining < 0 or (not will_sell and remaining != 0):
        return None
    expires_at = listed_at + FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS
    return {
        "instance_id": instance_id,
        "bouquet_id": bouquet_id,
        "components": component_snapshot,
        "listed_at": listed_at,
        "last_settled_at": min(expires_at, max(listed_at, last_settled_at)),
        "base_price": base_price,
        "pricing_profile": _normalize_flower_shop_pricing_profile(raw_slot.get("pricing_profile")),
        "will_sell": will_sell,
        "sale_business_seconds_remaining": remaining,
    }


def _normalize_flower_shop(raw_shop, now=None):
    raw_shop = raw_shop if isinstance(raw_shop, dict) else {}
    established_at = _nullable_positive_int(raw_shop.get("established_at"))
    if established_at is None:
        return _default_flower_shop_state()

    start_minute = raw_shop.get("business_start_minute")
    pending_start_minute = raw_shop.get("pending_business_start_minute")
    try:
        start_minute = int(start_minute)
    except (TypeError, ValueError):
        start_minute = None
    try:
        pending_start_minute = int(pending_start_minute)
    except (TypeError, ValueError):
        pending_start_minute = None
    if start_minute is not None and not 0 <= start_minute < 24 * 60:
        start_minute = None
    if pending_start_minute is not None and not 0 <= pending_start_minute < 24 * 60:
        pending_start_minute = None

    pending_effective_at = _nullable_positive_int(raw_shop.get("pending_business_effective_at"))
    if pending_effective_at is None:
        pending_start_minute = None
    elif pending_start_minute is not None and start_minute is not None:
        # 旧 pending 同时保留原营业时段。无法还原修改日期，安全重排到明天。
        pending_effective_at = _next_flower_shop_business_date(
            int(time.time()) if now is None else now
        )
        start_minute = None
    elif pending_start_minute is None and start_minute is None:
        pending_effective_at = None
    launched_at = _nullable_positive_int(raw_shop.get("launched_at")) if (
        start_minute is not None or pending_start_minute is not None
    ) else None
    raw_slots = raw_shop.get("slots", [])
    slots = []
    if isinstance(raw_slots, list):
        slots = [_normalize_flower_shop_slot(slot) for slot in raw_slots]
    try:
        raw_capacity = int(raw_shop.get("shelf_capacity", FLOWER_SHOP_SHELF_CAPACITY))
    except (TypeError, ValueError):
        raw_capacity = FLOWER_SHOP_SHELF_CAPACITY
    occupied_count = max((index + 1 for index, slot in enumerate(slots) if slot is not None), default=0)
    capacity = raw_capacity if raw_capacity in FLOWER_SHOP_SHELF_CAPACITIES else FLOWER_SHOP_SHELF_CAPACITY
    required_capacity = max(FLOWER_SHOP_SHELF_CAPACITY, occupied_count)
    for candidate in FLOWER_SHOP_SHELF_CAPACITIES:
        if candidate >= required_capacity:
            capacity = max(capacity, candidate) if capacity >= required_capacity else candidate
            break
    if occupied_count > FLOWER_SHOP_SHELF_CAPACITIES[-1]:
        # 没有合法容量能容下这些在售商品时，宁可保留异常 slots，也不能静默丢失商品。
        capacity = FLOWER_SHOP_SHELF_CAPACITIES[-1]
    if occupied_count <= FLOWER_SHOP_SHELF_CAPACITIES[-1]:
        slots = slots[:capacity]
    while len(slots) < capacity:
        slots.append(None)
    return {
        "established_at": established_at,
        "launched_at": launched_at,
        "shelf_capacity": capacity,
        "has_freshener": bool(raw_shop.get("has_freshener", False)),
        "shop_buff_until": _safe_nonnegative_int(raw_shop.get("shop_buff_until", 0), 0),
        "shop_buff_collectible_id": (
            raw_shop.get("shop_buff_collectible_id")
            if get_collectible_by_id(raw_shop.get("shop_buff_collectible_id")) is not None
            else None
        ),
        "business_start_minute": start_minute,
        "pending_business_start_minute": pending_start_minute,
        "pending_business_effective_at": pending_effective_at,
        "slots": slots,
    }


def normalize_state(data, now=None):
    """补齐旧存档字段，并修复 JSON 字典键类型。"""
    if now is None:
        now = int(time.time())
    if not isinstance(data, dict):
        return get_default_state()

    had_harvest_counts = "flower_harvest_counts" in data
    had_direct_flower_sale_earned = "direct_flower_sale_earned" in data
    had_cat_state = isinstance(data.get("cat_state"), dict)
    had_last_active_at = "last_active_at" in data
    had_ai_v5_update_notice_seen = "ai_v5_update_notice_seen" in data
    had_bouquet_read_count = "human_last_read_bouquet_gift_count" in data
    defaults = get_default_state()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    if not had_ai_v5_update_notice_seen:
        data["ai_v5_update_notice_seen"] = False

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

    raw_harvest_counts = data.get("flower_harvest_counts", {})
    harvest_counts = {}
    if isinstance(raw_harvest_counts, dict):
        for flower_id, value in raw_harvest_counts.items():
            flower_id = str(flower_id)
            if flower_id not in FLOWERS:
                continue
            try:
                count = int(value)
            except (TypeError, ValueError):
                continue
            if count > 0:
                harvest_counts[flower_id] = count
    if not had_harvest_counts:
        # 旧存档无法还原已经售出或插花的历史，只以升级时仍在背包里的鲜花作为最低起点。
        for flower_id, quantity in data["inventory"]["flowers"].items():
            if flower_id in FLOWERS and quantity > harvest_counts.get(flower_id, 0):
                harvest_counts[flower_id] = quantity
    data["flower_harvest_counts"] = harvest_counts

    bouquet_gifts = []
    raw_bouquet_gifts = data.get("bouquet_gifts", [])
    if isinstance(raw_bouquet_gifts, list):
        for entry in raw_bouquet_gifts:
            if not isinstance(entry, dict):
                continue
            bouquet_id = str(entry.get("bouquet_id", "") or "")
            components = entry.get("components", {})
            if not bouquet_id or not isinstance(components, dict):
                continue
            snapshot = {}
            for flower_id, quantity in components.items():
                try:
                    quantity = int(quantity)
                except (TypeError, ValueError):
                    continue
                if quantity > 0:
                    snapshot[str(flower_id)] = quantity
            if not snapshot:
                continue
            try:
                sent_at = int(entry.get("sent_at", 0))
            except (TypeError, ValueError):
                continue
            if sent_at <= 0:
                continue
            message = entry.get("message")
            bouquet_gifts.append(
                {
                    "bouquet_id": bouquet_id,
                    "components": snapshot,
                    "sent_at": sent_at,
                    "message": str(message) if message else None,
                }
            )
    data["bouquet_gifts"] = bouquet_gifts
    data["bouquet_inventory"] = _normalize_bouquet_inventory(data.get("bouquet_inventory", []))
    data["flower_shop"] = _normalize_flower_shop(data.get("flower_shop"), now)
    raw_bouquet_read_count = data.get("human_last_read_bouquet_gift_count")
    if not had_bouquet_read_count:
        # 花束功能上线前已有的赠送记录，在首次升级时默认已查看。
        bouquet_read_count = len(bouquet_gifts)
    else:
        try:
            bouquet_read_count = int(raw_bouquet_read_count)
        except (TypeError, ValueError):
            bouquet_read_count = len(bouquet_gifts)
    data["human_last_read_bouquet_gift_count"] = max(
        0, min(bouquet_read_count, len(bouquet_gifts))
    )

    if data.get("weather") not in WEATHER:
        data["weather"] = "sunny"
    weather_data = WEATHER[data["weather"]]

    try:
        data["weather_change_time"] = int(data.get("weather_change_time", now))
    except (TypeError, ValueError):
        data["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)
    if data["weather_change_time"] <= 0:
        data["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)

    try:
        data["next_butterfly_at"] = int(data.get("next_butterfly_at", 0))
    except (TypeError, ValueError):
        data["next_butterfly_at"] = 0
    try:
        data["last_butterfly_at"] = int(data.get("last_butterfly_at", 0))
    except (TypeError, ValueError):
        data["last_butterfly_at"] = 0

    try:
        data["game_start_time"] = int(data.get("game_start_time", now))
    except (TypeError, ValueError):
        data["game_start_time"] = now
    try:
        data["last_update"] = int(data.get("last_update", now))
    except (TypeError, ValueError):
        data["last_update"] = now
    try:
        data["last_active_at"] = int(data.get("last_active_at", data["last_update"]))
    except (TypeError, ValueError):
        data["last_active_at"] = now if had_last_active_at else data["last_update"]
    if had_last_active_at and data["last_active_at"] <= 0:
        data["last_active_at"] = now

    for field in (
        "cat_last_pet_real_time",
        "last_letter_check",
        "last_collectible_check",
        "last_butterfly_check",
        "last_pest_check_time",
        "rainbow_until",
        "butterfly_until",
        "pending_cat_mood_bonus",
        "total_earned",
    ):
        try:
            data[field] = int(data.get(field, defaults[field]))
        except (TypeError, ValueError):
            data[field] = defaults[field]

    try:
        direct_flower_sale_earned = int(data.get("direct_flower_sale_earned", 0))
    except (TypeError, ValueError):
        direct_flower_sale_earned = 0
    if not had_direct_flower_sale_earned:
        direct_flower_sale_earned = data["total_earned"]
    data["direct_flower_sale_earned"] = max(0, direct_flower_sale_earned)

    # 旧版检查时间为0时，从本次加载开始计时，避免连续刷命令抽事件。
    for field in ("last_letter_check", "last_collectible_check", "last_butterfly_check"):
        if data[field] <= 0:
            data[field] = now
    if data["next_butterfly_at"] <= 0:
        base_time = max(now, data.get("last_butterfly_check", now))
        data["next_butterfly_at"] = base_time + random.randint(
            BUTTERFLY_APPEAR_MIN_SECONDS,
            BUTTERFLY_APPEAR_MAX_SECONDS,
        )

    # v4.6.7 及更早版本把害虫检查时间保存为“游戏小时”整数。
    # 这类数值远小于 Unix 时间戳，迁移时从当前时刻重新开始5分钟冷却。
    if data["last_pest_check_time"] < 1_000_000_000:
        data["last_pest_check_time"] = now

    if not isinstance(data.get("events"), list):
        data["events"] = []
    for event in data["events"]:
        if isinstance(event, dict) and event.get("area") not in EVENT_AREAS:
            event.pop("area", None)
    _retain_latest_events(data["events"])

    if data.get("last_rainbow_reward") is not None and not isinstance(data.get("last_rainbow_reward"), dict):
        data["last_rainbow_reward"] = None
    if data.get("last_butterfly_reward") is not None and not isinstance(data.get("last_butterfly_reward"), dict):
        data["last_butterfly_reward"] = None
    if not isinstance(data.get("garden_events"), dict):
        data["garden_events"] = {}
    offline_summary = data.get("offline_summary")
    if not isinstance(offline_summary, dict):
        offline_summary = {}
    normalized_offline_summary = _default_offline_summary()
    for key, default_value in normalized_offline_summary.items():
        value = offline_summary.get(key, default_value)
        if key in ("message",):
            normalized_offline_summary[key] = str(value or "")
        elif key in ("is_frozen",):
            normalized_offline_summary[key] = bool(value)
        else:
            normalized_offline_summary[key] = _safe_nonnegative_int(value, default_value)
    data["offline_summary"] = normalized_offline_summary
    data["is_frozen"] = bool(data.get("is_frozen", False))
    data["garden_frozen_until"] = _safe_nonnegative_int(data.get("garden_frozen_until", 0), 0)
    data["frozen_reason"] = str(data.get("frozen_reason", "") or "")
    data["ai_v5_update_notice_seen"] = bool(data.get("ai_v5_update_notice_seen", False))

    if not isinstance(data.get("permanent_items"), list):
        data["permanent_items"] = []
    data["permanent_items"] = [item for item in data["permanent_items"] if item in ITEMS]

    raw_cottage = data.get("cottage")
    if not isinstance(raw_cottage, dict):
        raw_cottage = {}
    raw_cottage_items = raw_cottage.get("items")
    cottage_items = {}
    if isinstance(raw_cottage_items, dict):
        for item_id, record in raw_cottage_items.items():
            item_id = str(item_id or "").strip()
            if not item_id or not isinstance(record, dict):
                continue
            canonical_item_id = COTTAGE_REWARD_ID_ALIASES.get(item_id, item_id)
            acquired_at = _safe_nonnegative_int(record.get("acquired_at", 0), 0)
            source = normalize_event_source(record.get("source"))
            normalized_record = {"acquired_at": acquired_at, "source": source}
            existing_record = cottage_items.get(canonical_item_id)
            if (
                existing_record is None
                or acquired_at < existing_record["acquired_at"]
                or (acquired_at == existing_record["acquired_at"] and item_id == canonical_item_id)
            ):
                cottage_items[canonical_item_id] = normalized_record
    data["cottage"] = {"items": cottage_items}

    if not isinstance(data.get("encyclopedia"), list):
        data["encyclopedia"] = []
    data["encyclopedia"] = list(dict.fromkeys(fid for fid in data["encyclopedia"] if fid in FLOWERS))

    if not isinstance(data.get("collectibles"), dict):
        data["collectibles"] = {}
    data["collectibles"] = _positive_inventory(data["collectibles"])

    first_found = {}
    raw_first_found = data.get("collectible_first_found", {})
    if isinstance(raw_first_found, dict):
        for collectible_id, timestamp in raw_first_found.items():
            if get_collectible_by_id(str(collectible_id)) is None:
                continue
            try:
                timestamp = int(timestamp)
            except (TypeError, ValueError):
                continue
            if timestamp > 0:
                first_found[str(collectible_id)] = timestamp
    data["collectible_first_found"] = first_found
    collectible_total = sum(int(count or 0) for count in data["collectibles"].values())
    existing_unlocked = data.get("cat_collectibles_unlocked", False)
    data["cat_collectibles_unlocked"] = bool(existing_unlocked) or collectible_total > 0
    unlocked_at = _safe_nonnegative_int(data.get("cat_collectibles_unlocked_at", 0), 0)
    if data["cat_collectibles_unlocked"] and unlocked_at <= 0 and first_found:
        unlocked_at = min(first_found.values())
    data["cat_collectibles_unlocked_at"] = unlocked_at

    if not isinstance(data.get("garden_collectibles"), dict):
        data["garden_collectibles"] = {}
    data["garden_collectibles"] = {
        collectible_id: count
        for collectible_id, count in _positive_inventory(data["garden_collectibles"]).items()
        if collectible_id in GARDEN_COLLECTIBLE_IDS
    }

    garden_first_found = {}
    raw_garden_first_found = data.get("garden_collectible_first_found", {})
    if isinstance(raw_garden_first_found, dict):
        for collectible_id, timestamp in raw_garden_first_found.items():
            if get_garden_collectible_by_id(str(collectible_id)) is None:
                continue
            try:
                timestamp = int(timestamp)
            except (TypeError, ValueError):
                continue
            if timestamp > 0:
                garden_first_found[str(collectible_id)] = timestamp
    data["garden_collectible_first_found"] = garden_first_found

    garden_collection_log = []
    raw_garden_log = data.get("garden_collection_log", [])
    if isinstance(raw_garden_log, list):
        for entry in raw_garden_log:
            if not isinstance(entry, dict):
                continue
            collectible_id = str(entry.get("id", "") or "")
            if collectible_id not in GARDEN_COLLECTIBLE_IDS:
                continue
            try:
                found_at = int(entry.get("time", 0))
            except (TypeError, ValueError):
                continue
            if found_at <= 0:
                continue
            garden_collection_log.append(
                {
                    "id": collectible_id,
                    "time": found_at,
                    "source": str(entry.get("source", "") or ""),
                }
            )
    data["garden_collection_log"] = garden_collection_log[-40:]

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
    data["letter_affection_progress"] = _safe_nonnegative_int(
        data.get("letter_affection_progress", 0),
        0,
    )

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

    if data.get("cat") is None:
        data["cat_max_affection"] = 0.0
    else:
        try:
            recorded_max = float(data.get("cat_max_affection", 0))
        except (TypeError, ValueError):
            recorded_max = 0.0
        current_affection = float(data["cat_stats"].get("affection", 0))
        data["cat_max_affection"] = min(
            100.0,
            max(0.0, recorded_max, current_affection),
        )

    _normalize_v5_cat_foundation(data, now, had_cat_state=had_cat_state)
    refresh_garden_events(data, now)

    return data


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            state = normalize_state(json.load(f))
        if apply_offline_progress(state):
            save_game(state)
        return state
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        backup_file = SAVE_FILE + ".backup"
        if os.path.exists(backup_file):
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_data = normalize_state(json.load(f))
                if apply_offline_progress(backup_data):
                    save_game(backup_data)
                os.replace(backup_file, SAVE_FILE)
                return backup_data
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        return None


def save_game(state):
    now = int(time.time())
    state["last_update"] = now
    state.pop("_interaction_accepted", None)
    state.pop("_auto_food_servings_used", None)
    state.pop("_auto_water_servings_used", None)
    state["last_active_at"] = now
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
    state["inventory"]["seeds"]["daisy"] = 3
    state["inventory"]["items"]["basic_food"] = 5
    save_game(state)
    return (
        "🌱 新游戏开始！你有50块钱，3盆花，5份普通猫粮。\n"
        "先种花、照料花园，耐心等猫咪来花园做客吧！\n\n"
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
    requirement = FLOWER_UNLOCK_REQUIREMENTS.get(flower_id, {})
    if isinstance(requirement, dict):
        return {
            "encyclopedia": int(requirement.get("encyclopedia", 0) or 0),
            "harvests": int(requirement.get("harvests", 0) or 0),
        }
    value = int(requirement or 0)
    return {"encyclopedia": value, "harvests": 0}


def is_bouquet_discovered(state, bouquet_id):
    bouquet = BOUQUETS.get(bouquet_id)
    if not bouquet:
        return False
    encyclopedia = set(state.get("encyclopedia", []))
    return all(flower_id in encyclopedia for flower_id in bouquet["components"])


def get_bouquet_options(state):
    inventory = state.get("inventory", {}).get("flowers", {})
    options = []
    for bouquet_id, bouquet in BOUQUETS.items():
        if not is_bouquet_discovered(state, bouquet_id):
            continue
        missing = {}
        for flower_id, required in bouquet["components"].items():
            available = int(inventory.get(flower_id, 0) or 0)
            if available < required:
                missing[flower_id] = required - available
        options.append(
            {
                "bouquet_id": bouquet_id,
                "name": bouquet["name"],
                "components": dict(bouquet["components"]),
                "can_make": not missing,
                "missing": missing,
            }
        )
    return options


def _format_bouquet_options(options):
    lines = ["💐 花束配方"]
    for option in options:
        components = "、".join(
            f"{FLOWERS[flower_id]['name']}×{quantity}"
            for flower_id, quantity in option["components"].items()
        )
        if option["can_make"]:
            status = "可以制作"
        else:
            missing = "、".join(
                f"{FLOWERS.get(flower_id, {'name': flower_id})['name']}×{quantity}"
                for flower_id, quantity in option["missing"].items()
            )
            status = f"缺少：{missing}"
        lines.append(f"  {option['bouquet_id']}｜{option['name']}｜{components}｜{status}")
    return "\n".join(lines)


def is_flower_unlocked(state, flower_id):
    if flower_id not in FLOWERS:
        return False
    if flower_id in state.get("encyclopedia", []):
        return True
    requirement = get_flower_unlock_requirement(flower_id)
    encyclopedia_count = len(state.get("encyclopedia", []))
    harvest_total = get_total_flower_harvests(state)
    return (
        encyclopedia_count >= requirement["encyclopedia"]
        and harvest_total >= requirement["harvests"]
    )


def get_unlock_message(flower_id):
    requirement = get_flower_unlock_requirement(flower_id)
    if requirement["encyclopedia"] <= 0 and requirement["harvests"] <= 0:
        return "默认解锁"
    parts = []
    if requirement["encyclopedia"] > 0:
        parts.append(f"图鉴收录{requirement['encyclopedia']}种")
    if requirement["harvests"] > 0:
        parts.append(f"累计收获{requirement['harvests']}朵")
    return "，".join(parts) + "后解锁"


def get_total_flower_harvests(state):
    return sum(
        int(qty or 0)
        for qty in state.get("flower_harvest_counts", {}).values()
    )


def get_flower_shop_eligibility_progress(state):
    return {
        "encyclopedia": len(state.get("encyclopedia", [])),
        "harvests": get_total_flower_harvests(state),
        "direct_flower_sale_earned": max(0, int(state.get("direct_flower_sale_earned", 0) or 0)),
    }


def is_flower_shop_eligible(state):
    progress = get_flower_shop_eligibility_progress(state)
    return (
        progress["encyclopedia"] >= 10
        and progress["harvests"] >= 42
        and progress["direct_flower_sale_earned"] >= 3000
    )


def _flower_shop_local_cycle_start(start_minute, now):
    local_now = datetime.fromtimestamp(now, DISPLAY_TIMEZONE)
    return local_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        minutes=start_minute
    )


def _next_flower_shop_business_date(now):
    return int((_flower_shop_local_cycle_start(0, now) + timedelta(days=1)).timestamp())


def _flower_shop_is_open(shop, now):
    if shop.get("pending_business_start_minute") is not None:
        return False
    start_minute = shop.get("business_start_minute")
    effective_at = shop.get("pending_business_effective_at")
    if effective_at is not None and start_minute is not None:
        if now < effective_at + start_minute * 60:
            return False
    return _flower_shop_is_open_for_start(start_minute, now)


def _flower_shop_is_open_for_start(start_minute, now):
    if start_minute is None:
        return False
    local_now = datetime.fromtimestamp(now, DISPLAY_TIMEZONE)
    local_minute = local_now.hour * 60 + local_now.minute
    elapsed_minutes = (local_minute - start_minute) % (24 * 60)
    return elapsed_minutes < FLOWER_SHOP_BUSINESS_DURATION_MINUTES


def _iter_flower_shop_business_windows(from_timestamp, to_timestamp, start_minute):
    if to_timestamp <= from_timestamp:
        return
    local_from = datetime.fromtimestamp(from_timestamp, DISPLAY_TIMEZONE)
    local_to = datetime.fromtimestamp(to_timestamp, DISPLAY_TIMEZONE)
    day = local_from.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    last_day = local_to.replace(hour=0, minute=0, second=0, microsecond=0)
    while day <= last_day:
        window_start = int((day + timedelta(minutes=start_minute)).timestamp())
        window_end = window_start + FLOWER_SHOP_BUSINESS_DURATION_MINUTES * 60
        overlap_start = max(from_timestamp, window_start)
        overlap_end = min(to_timestamp, window_end)
        if overlap_end > overlap_start:
            yield overlap_start, overlap_end
        day += timedelta(days=1)


def get_flower_shop_business_seconds(from_timestamp, to_timestamp, start_minute):
    try:
        from_timestamp = int(from_timestamp)
        to_timestamp = int(to_timestamp)
        start_minute = int(start_minute)
    except (TypeError, ValueError):
        return 0
    if to_timestamp <= from_timestamp or not 0 <= start_minute < 24 * 60:
        return 0
    return sum(
        overlap_end - overlap_start
        for overlap_start, overlap_end in _iter_flower_shop_business_windows(
            from_timestamp, to_timestamp, start_minute
        )
    )


def _locate_flower_shop_business_timestamp(from_timestamp, to_timestamp, start_minute, seconds_needed):
    seconds_needed = max(0, int(seconds_needed))
    if seconds_needed == 0:
        return int(from_timestamp)
    for overlap_start, overlap_end in _iter_flower_shop_business_windows(
        int(from_timestamp), int(to_timestamp), int(start_minute)
    ):
        available = overlap_end - overlap_start
        if seconds_needed <= available:
            return overlap_start + seconds_needed
        seconds_needed -= available
    return None


def _round_flower_shop_price(value):
    return max(1, int(float(value) + 0.5))


def get_flower_shop_base_price(components):
    direct_sale_value = sum(
        FLOWERS[flower_id]["sell_price"] * int(quantity)
        for flower_id, quantity in components.items()
        if flower_id in FLOWERS and int(quantity) > 0
    )
    return _round_flower_shop_price(direct_sale_value * FLOWER_SHOP_BASE_PRICE_MULTIPLIER)


def _roll_flower_shop_sale_plan():
    will_sell = random.random() < FLOWER_SHOP_SALE_CHANCE
    if not will_sell:
        return False, 0
    return True, int(
        round(
            random.triangular(
                0,
                FLOWER_SHOP_SALE_WAIT_MAX_SECONDS,
                FLOWER_SHOP_SALE_WAIT_MODE_SECONDS,
            )
        )
    )


def _get_flower_shop_price_details(slot, at_timestamp):
    age_seconds = max(0, int(at_timestamp) - int(slot["listed_at"]))
    profile = slot.get("pricing_profile") or _default_flower_shop_pricing_profile()
    stage = profile[-1]
    for candidate in profile:
        if age_seconds < int(candidate["until_seconds"]):
            stage = candidate
            break
    return {
        "price": _round_flower_shop_price(int(slot["base_price"]) * float(stage["multiplier"])),
        "stage": str(stage.get("label", "") or ""),
    }


def _flower_shop_sale_has_cat_buff(
    sold_at,
    settlement_start,
    previous_shop_buff_until,
    shop_buff_windows,
):
    sold_at = int(sold_at)
    settlement_start = int(settlement_start)
    previous_shop_buff_until = _safe_nonnegative_int(previous_shop_buff_until, 0)
    if settlement_start <= sold_at < previous_shop_buff_until:
        return True
    for window in shop_buff_windows or ():
        if not isinstance(window, dict):
            continue
        start_at = _safe_nonnegative_int(window.get("start_at", 0), 0)
        until_at = _safe_nonnegative_int(window.get("until_at", 0), 0)
        if start_at <= sold_at < until_at:
            return True
    return False


def settle_flower_shop(
    state,
    now=None,
    *,
    previous_shop_buff_until=None,
    shop_buff_windows=None,
):
    if now is None:
        now = int(time.time())
    now = int(now)
    shop = state.get("flower_shop")
    if not isinstance(shop, dict) or not shop.get("launched_at"):
        return []
    if previous_shop_buff_until is None:
        previous_shop_buff_until = shop.get("shop_buff_until", 0)
    start_minute = shop.get("business_start_minute")
    if not isinstance(start_minute, int):
        return []
    slots = shop.get("slots")
    if not isinstance(slots, list):
        return []

    results = []
    for slot_index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            continue
        listed_at = int(slot["listed_at"])
        expires_at = listed_at + FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS
        from_timestamp = max(listed_at, int(slot["last_settled_at"]))
        target_timestamp = min(now, expires_at)
        if target_timestamp < from_timestamp:
            continue

        sold_at = None
        if slot["will_sell"]:
            remaining = int(slot["sale_business_seconds_remaining"])
            if remaining <= 0:
                sold_at = from_timestamp
            else:
                business_seconds = get_flower_shop_business_seconds(
                    from_timestamp, target_timestamp, start_minute
                )
                if business_seconds >= remaining:
                    sold_at = _locate_flower_shop_business_timestamp(
                        from_timestamp, target_timestamp, start_minute, remaining
                    )
                else:
                    slot["sale_business_seconds_remaining"] = remaining - business_seconds

        if sold_at is not None and sold_at < expires_at:
            price_details = _get_flower_shop_price_details(slot, sold_at)
            sale_price = price_details["price"]
            if _flower_shop_sale_has_cat_buff(
                sold_at,
                from_timestamp,
                previous_shop_buff_until,
                shop_buff_windows,
            ):
                sale_price = _round_flower_shop_price(
                    sale_price * FLOWER_SHOP_CAT_BUFF_MULTIPLIER
                )
            state["money"] += sale_price
            state["total_earned"] += sale_price
            bouquet_name = BOUQUETS.get(slot["bouquet_id"], {}).get("name", slot["bouquet_id"])
            add_event(
                state,
                f"🏪 货架{slot_index + 1}的「{bouquet_name}」以{sale_price}块成交，货架重新空出来了。",
                now=sold_at, area="flower_shop",
            )
            slots[slot_index] = None
            results.append(
                {"type": "sold", "slot": slot_index + 1, "sold_at": sold_at, "price": sale_price}
            )
            continue

        slot["last_settled_at"] = target_timestamp
        if now >= expires_at:
            bouquet_name = BOUQUETS.get(slot["bouquet_id"], {}).get("name", slot["bouquet_id"])
            add_event(
                state,
                f"🥀 货架{slot_index + 1}的「{bouquet_name}」超过24小时仍未售出，已经报废。",
                now=expires_at, area="flower_shop",
            )
            slots[slot_index] = None
            results.append({"type": "expired", "slot": slot_index + 1, "expired_at": expires_at})
    return results


def _settle_cat_then_flower_shop(
    state,
    cat_target_time,
    *,
    flower_shop_target_time=None,
    letter_context=None,
    before_cat_transition=None,
):
    if flower_shop_target_time is None:
        flower_shop_target_time = cat_target_time
    shop = state.get("flower_shop")
    previous_shop_buff_until = (
        _safe_nonnegative_int(shop.get("shop_buff_until", 0), 0)
        if isinstance(shop, dict)
        else 0
    )
    shop_buff_windows = []
    lifecycle_messages = settle_cat_lifecycle(
        state,
        cat_target_time,
        letter_context=letter_context,
        shop_buff_windows=shop_buff_windows,
        before_transition=before_cat_transition,
    )
    flower_shop_results = settle_flower_shop(
        state,
        flower_shop_target_time,
        previous_shop_buff_until=previous_shop_buff_until,
        shop_buff_windows=shop_buff_windows,
    )
    return lifecycle_messages, flower_shop_results


def get_next_flower_shop_cycle_at(state, now=None, start_minute=None):
    if now is None:
        now = int(time.time())
    shop = state.get("flower_shop", {})
    if start_minute is None:
        pending_start = shop.get("pending_business_start_minute")
        effective_at = shop.get("pending_business_effective_at")
        scheduled_start = pending_start if pending_start is not None else shop.get("business_start_minute")
        if effective_at is not None and scheduled_start is not None:
            first_open_at = effective_at + scheduled_start * 60
            if now < first_open_at:
                return first_open_at
        start_minute = shop.get("business_start_minute") if isinstance(shop, dict) else None
    if not isinstance(start_minute, int) or not 0 <= start_minute < 24 * 60:
        return None
    candidate = _flower_shop_local_cycle_start(start_minute, now)
    if candidate.timestamp() <= now:
        candidate += timedelta(days=1)
    return int(candidate.timestamp())


def _refresh_flower_shop_schedule(state, now):
    shop = state.get("flower_shop")
    if not isinstance(shop, dict):
        return
    pending_start = shop.get("pending_business_start_minute")
    pending_effective_at = shop.get("pending_business_effective_at")
    if (
        isinstance(pending_start, int)
        and isinstance(pending_effective_at, int)
        and now >= pending_effective_at
    ):
        shop["business_start_minute"] = pending_start
        shop["pending_business_start_minute"] = None
    # 午夜启用新规则，但跨午夜时段不得凭空继承前一天的营业窗口。
    # 沿用生效时间作首个开店边界，到首次真实开店后即可清除。
    start_minute = shop.get("business_start_minute")
    if (
        isinstance(pending_effective_at, int)
        and isinstance(start_minute, int)
        and shop.get("pending_business_start_minute") is None
        and now >= pending_effective_at + start_minute * 60
    ):
        shop["pending_business_effective_at"] = None


def get_flower_shop_public_summary(state, now=None):
    if now is None:
        now = int(time.time())
    shop = state.get("flower_shop", {})
    if not isinstance(shop, dict):
        shop = _default_flower_shop_state()
    start_minute = shop.get("business_start_minute")
    established = bool(shop.get("established_at"))
    is_open = bool(
        established
        and shop.get("launched_at")
        and _flower_shop_is_open(shop, now)
    )
    slots = shop.get("slots", []) if isinstance(shop.get("slots"), list) else []
    shelf_capacity = int(shop.get("shelf_capacity", 0) or 0)
    shop_buff_until = _safe_nonnegative_int(shop.get("shop_buff_until", 0), 0)
    shop_buff_active = bool(established and now < shop_buff_until)
    next_shelf_capacity = next(
        (capacity for capacity in FLOWER_SHOP_SHELF_CAPACITIES if capacity > shelf_capacity),
        None,
    )
    public_slots = []
    for index, slot in enumerate(slots):
        if slot is None:
            public_slots.append({"slot": index + 1, "empty": True})
            continue
        bouquet_id = str(slot.get("bouquet_id", "") or "")
        bouquet = BOUQUETS.get(bouquet_id, {})
        price_details = _get_flower_shop_price_details(slot, now)
        public_slots.append(
            {
                "slot": index + 1,
                "empty": False,
                "bouquet_id": bouquet_id,
                "name": str(bouquet.get("name", bouquet_id) or bouquet_id),
                "components": dict(slot.get("components", {})),
                "listed_at": int(slot.get("listed_at", 0) or 0),
                "base_price": int(slot.get("base_price", 0) or 0),
                "current_price": price_details["price"],
                "price_stage": price_details["stage"],
                "expires_in_seconds": max(
                    0,
                    int(slot.get("listed_at", 0) or 0)
                    + FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS
                    - now,
                ),
                "is_open": is_open,
            }
        )
    return {
        "eligible": is_flower_shop_eligible(state),
        "eligibility_progress": get_flower_shop_eligibility_progress(state),
        "established": established,
        "launched": bool(shop.get("launched_at")),
        "capacity": shelf_capacity,
        "shelf_capacity": shelf_capacity,
        "can_upgrade_shelf": bool(established and next_shelf_capacity is not None),
        "next_shelf_capacity": next_shelf_capacity,
        "next_shelf_upgrade_cost": FLOWER_SHOP_SHELF_UPGRADE_COSTS.get(shelf_capacity),
        "has_freshener": bool(shop.get("has_freshener", False)),
        "freshener_cost": None if shop.get("has_freshener", False) else FLOWER_SHOP_FRESHENER_COST,
        "pricing_profiles": {
            "normal": _default_flower_shop_pricing_profile(),
            "freshener": _freshener_flower_shop_pricing_profile(),
        },
        "bouquet_lifetime_seconds": FLOWER_SHOP_BOUQUET_LIFETIME_SECONDS,
        "shop_buff_active": shop_buff_active,
        "shop_buff_until": shop_buff_until if shop_buff_active else None,
        "shop_buff_collectible_id": shop.get("shop_buff_collectible_id") if shop_buff_active else None,
        "shop_buff_remaining_seconds": max(0, shop_buff_until - now) if shop_buff_active else 0,
        "shop_buff_effect": "成交金额 +10%" if shop_buff_active else None,
        "business_start_minute": start_minute,
        "business_duration_minutes": FLOWER_SHOP_BUSINESS_DURATION_MINUTES,
        "pending_business_start_minute": shop.get("pending_business_start_minute"),
        "pending_business_effective_at": shop.get("pending_business_effective_at"),
        "is_open": is_open,
        "next_business_cycle_at": get_next_flower_shop_cycle_at(state, now),
        "occupied_slots": sum(1 for slot in slots if slot is not None),
        "empty_slots": sum(1 for slot in slots if slot is None),
        "slots": public_slots,
    }


def get_bouquet_inventory_public(state):
    public_inventory = []
    for entry in state.get("bouquet_inventory", []):
        if not isinstance(entry, dict):
            continue
        bouquet_id = str(entry.get("bouquet_id", "") or "")
        bouquet = BOUQUETS.get(bouquet_id, {})
        public_inventory.append(
            {
                "id": str(entry.get("instance_id", "") or ""),
                "bouquet_id": bouquet_id,
                "name": str(bouquet.get("name", bouquet_id) or bouquet_id),
                "components": dict(entry.get("components", {})),
            }
        )
    return public_inventory


def get_stage_unlocks(
    before_count,
    after_count,
    encyclopedia_before,
    harvest_total_before,
    harvest_total_after,
):
    newly_unlocked = []
    known_before = set(encyclopedia_before)
    for flower_id in FLOWER_UNLOCK_REQUIREMENTS:
        requirement = get_flower_unlock_requirement(flower_id)
        if flower_id in known_before:
            continue
        was_unlocked = (
            before_count >= requirement["encyclopedia"]
            and harvest_total_before >= requirement["harvests"]
        )
        is_unlocked = (
            after_count >= requirement["encyclopedia"]
            and harvest_total_after >= requirement["harvests"]
        )
        if not was_unlocked and is_unlocked:
            newly_unlocked.append(FLOWERS[flower_id]["name"])
    return newly_unlocked


def is_pot_withered(pot):
    return isinstance(pot, dict) and bool(pot.get("withered", False))


def pot_needs_water(pot):
    return pot is not None and not is_pot_withered(pot) and not pot.get("watered", True)


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


def sync_cottage_rewards(state, now=None, *, record_events=False):
    """按既有图鉴事实补齐确定性小屋奖励；返回本次新获得的 item id。"""
    if now is None:
        now = int(time.time())
    cottage = state.setdefault("cottage", {"items": {}})
    items = cottage.setdefault("items", {})
    encyclopedia = set(state.get("encyclopedia", []))
    granted = []
    for item_id, requirement in COTTAGE_REWARD_REQUIREMENTS.items():
        if item_id in items or not requirement["flowers"].issubset(encyclopedia):
            continue
        items[item_id] = {"acquired_at": int(now), "source": "system"}
        granted.append(item_id)
        if record_events:
            add_event(state, f"🏠 解锁了小屋纪念物「{COTTAGE_ITEM_CATALOG[item_id]['name']}」。", now=now, area="cottage")
    return granted


def get_cottage_public_summary(state):
    """返回网页与 AI 共用的小屋公开摘要，不泄露原始存档。"""
    cottage_items = state.get("cottage", {}).get("items", {})
    if not isinstance(cottage_items, dict):
        cottage_items = {}

    owned_items = []
    for item_id, record in cottage_items.items():
        catalog_item = COTTAGE_ITEM_CATALOG.get(item_id)
        if catalog_item is not None and catalog_item.get("legacy_only", False):
            continue
        if catalog_item is None:
            # 兼容未来 catalog 变更留下的合法历史 ownership，不将原始 record 直接公开。
            catalog_item = {
                "id": item_id,
                "name": "历史小屋物品",
                "category": "legacy",
                "slot_key": item_id,
                "asset_key": "",
            }
        owned_items.append(
            {
                "id": item_id,
                "name": catalog_item["name"],
                "category": catalog_item["category"],
                "acquired_at": _safe_nonnegative_int(record.get("acquired_at", 0), 0),
                "source": normalize_event_source(record.get("source")),
                "slot_key": catalog_item["slot_key"],
                "asset_key": catalog_item["asset_key"],
            }
        )

    purchasable_items = [
        {
            "id": item_id,
            "name": item["name"],
            "price": item["price"],
            "owned": item_id in cottage_items,
            "description": item["description"],
            "slot_key": item["slot_key"],
            "asset_key": item["asset_key"],
        }
        for item_id, item in COTTAGE_ITEM_CATALOG.items()
        if not item.get("reward_only", False) and not item.get("legacy_only", False) and "price" in item
    ]

    care = state.get("cat_care", {}) if isinstance(state.get("cat_care"), dict) else {}
    cat_area = {
        "bed": dict(care.get("bed", {})) if isinstance(care.get("bed"), dict) else {},
        "food_bowl": dict(care.get("food_bowl", {})) if isinstance(care.get("food_bowl"), dict) else {},
        "water_bowl": dict(care.get("water_bowl", {})) if isinstance(care.get("water_bowl"), dict) else {},
        "permanent_items": list(state.get("permanent_items", [])),
    }
    return {
        "owned_items": owned_items,
        "purchasable_items": purchasable_items,
        "total_owned": len(owned_items),
        "cat_area": cat_area,
    }


def _retain_latest_events(events):
    # Stable sorting keeps insertion order for events with equal timestamps.
    events[:] = sorted(events, key=lambda event: _safe_nonnegative_int(
        event.get("time", 0), 0) if isinstance(event, dict) else 0)[-EVENT_HISTORY_LIMIT:]


def add_event(state, event_text, *, now=None, source="system", area=None):
    event = {
        "time": int(time.time() if now is None else now),
        "text": event_text,
        "source": normalize_event_source(source),
    }
    if area in EVENT_AREAS:
        event["area"] = area
    state["events"].append(event)
    _retain_latest_events(state["events"])


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
        flower_data = FLOWERS[pot["flower_id"]]
        flower_name = flower_data["name"]
        pot.pop("pest_time", None)
        pot["watered"] = False
        state["pest_treatment"].pop(i, None)
        current_progress = float(pot.get("growth_progress", 0.0))
        setback = min(float(flower_data["grow_time"]) * 0.15, 90.0)
        pot["growth_progress"] = max(0.0, current_progress - setback)
        messages.append(f"\n💀 盆{i + 1}的{flower_name}被害虫害死，已经枯萎了！")
        messages.append(f"   使用 'clear {i + 1}' 清理花盆")
        add_event(state, f"{flower_name}枯萎（盆{i + 1}）")

    # 新虫害每5分钟最多判定一次。离线再久也只在回来时检查一轮，
    # 不补算错过的次数，避免“越频繁互动越容易长虫”。
    last_pest_check = int(state.get("last_pest_check_time", now))
    if now - last_pest_check < PEST_CHECK_INTERVAL:
        refresh_garden_events(state, now)
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
            pot["watered"] = False
            messages.append(f"\n🐛 警告：盆{i + 1}的{FLOWERS[flower_id]['name']}长虫子了！")
            messages.append(f"   使用 'treat {i + 1}' 治疗（花费{PEST_TREATMENT_COST}块）")
            messages.append(f"   不治疗的话，花会在{format_time(pest_death_seconds)}后枯萎！")
            add_event(state, f"盆{i + 1}出现害虫")

    refresh_garden_events(state, now)
    return messages


def get_game_time_info(state, now=None):
    if now is None:
        now = int(time.time())
    elapsed_real_seconds = max(0, now - state.get("game_start_time", now))
    game_days = elapsed_real_seconds // REAL_SECONDS_PER_DAY + 1
    current_local_time = datetime.fromtimestamp(now, tz=DISPLAY_TIMEZONE)
    game_hour = current_local_time.hour
    game_minute = current_local_time.minute
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
    if _is_premium_bed(state.get("cat_care", {}).get("bed")):
        mood_decay *= 0.6
    net_mood = -mood_decay
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

        pot_status = get_pot_ai_status(state, i, pot)
        pest_paused = pot_status == "pest_blocked"
        if pot_status == "ready":
            status = "🌸 可收获！"
        elif pest_paused:
            if progress_value >= grow_time:
                status = f"🐛 有虫害，暂不可收获（{progress_pct}%）；需先处理虫害"
            else:
                status = f"🐛 有虫害，生长暂停（{progress_pct}%）；需先处理虫害"
        elif pot_status == "needs_water":
            status = f"🏜️ 未浇水，生长暂停（{progress_pct}%）"
        else:
            remaining_real_seconds = (grow_time - progress_value) / speed
            status = f"🌱 {progress_pct}% (还需约{format_time(remaining_real_seconds)})"

        pest_warning = ""
        if not pest_paused and "pest_time" in pot and now < pot["pest_time"]:
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
        lines.append("\n【猫咪】未正式收养")
        if state.get("pending_cat_mood_bonus", 0) > 0:
            lines.append(f"  🎁 已保存猫咪心情奖励+{state['pending_cat_mood_bonus']}，收养后生效")
        lines.append("  猫咪会先来花园做客，愿意留下后可使用 adopt [名字] 为它取名并正式收养")
    else:
        stats = state["cat_stats"]
        cat_name = state["cat"].get("name", "小猫")
        lines.append(f"\n【猫咪】{cat_name}")
        lines.append(f"  饱食度：{get_bar(stats['hunger'])} {int(stats['hunger'])}")
        lines.append(f"  口渴度：{get_bar(stats['thirst'])} {int(stats['thirst'])}")
        facility_labels = _get_cat_facility_labels(state)
        lines.append(f"  心情  ：{get_bar(stats['mood'])} {int(stats['mood'])}")
        lines.append(f"  亲密度：{get_bar(stats['affection'])} {int(stats['affection'])}")
        lines.append(f"  💧 {facility_labels['water_bowl']}")
        lines.append(f"  🍽️ {facility_labels['food_bowl']}")
        lines.append(f"  🛏️ {facility_labels['bed']}")

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

    lines.append(f"\n📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/{len(FLOWERS)}")
    if state["cat"]:
        collectible_count = sum(state["collectibles"].values())
        letter_count = len(state["letters_received"])
        if collectible_count > 0 or letter_count > 0:
            lines.append(f"🎁 收集品{get_collectible_unique_count(state)}/{len(CAT_COLLECTIBLES)}种（共{collectible_count}件） ✉️ 信件{letter_count}/{len(CAT_LETTERS)}封")

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


def update_cat_stats(
    state, now, weather_data, letter_context=None, *, mood_hours_limit=MOOD_OFFLINE_CAP_REAL_HOURS,
):
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
    thirst_decay = 5.0

    hunger_floor = min(CAT_PASSIVE_STAT_FLOOR, start_hunger)
    thirst_floor = min(CAT_PASSIVE_STAT_FLOOR, start_thirst)
    stats["hunger"] = max(hunger_floor, start_hunger - hunger_decay * hours)
    stats["thirst"] = max(thirst_floor, start_thirst - thirst_decay * hours)

    mood_decay = MOOD_BASE_DECAY
    if _is_premium_bed(state.get("cat_care", {}).get("bed")):
        mood_decay *= 0.6
    mood_hours = min(hours, mood_hours_limit)
    mood_change = -mood_decay * mood_hours
    mood_floor = min(CAT_PASSIVE_STAT_FLOOR, stats["mood"])
    stats["mood"] = min(100.0, max(mood_floor, stats["mood"] + mood_change))

    if state.get("cat_state", {}).get("phase") == CAT_PHASE_ADOPTED:
        affection_loss = AFFECTION_NATURAL_DECAY * hours
        affection_floor = min(30.0, stats["affection"])
        stats["affection"] = max(affection_floor, stats["affection"] - affection_loss)

    should_food_roll = _should_auto_food_roll(start_hunger, stats["hunger"])
    should_water_roll = _should_auto_water_roll(start_thirst, stats["thirst"])
    if should_food_roll or should_water_roll:
        _trigger_cat_bowls_for_auto_node(
            state,
            now=now,
            source="stat_drop",
            food=should_food_roll,
            water=should_water_roll,
            letter_context=letter_context,
        )

    # 吃喝会同步并替换 cat_stats；保留奖励后的当前视图。
    stats = state["cat_stats"]

    state["last_update"] = now


def _consume_offline_cat_portions(state):
    used_food = _safe_nonnegative_int(state.pop("_auto_food_servings_used", 0), 0)
    used_water = _safe_nonnegative_int(state.pop("_auto_water_servings_used", 0), 0)
    _sync_cat_stats_views(state)
    return used_food, used_water


def _cheapest_unlocked_seed_price(state):
    prices = [
        flower_data["seed_price"]
        for flower_id, flower_data in FLOWERS.items()
        if is_flower_unlocked(state, flower_id)
    ]
    return min(prices) if prices else None


def _has_free_flower_recovery_path(state):
    for pot_idx, pot in enumerate(state.get("pots", [])):
        if not isinstance(pot, dict) or is_pot_withered(pot):
            continue
        if pot.get("flower_id") not in FLOWERS:
            continue
        if not _has_pest_blocker(state, pot_idx, pot):
            return True
        if state.get("money", 0) >= PEST_TREATMENT_COST:
            return True
    return False


def apply_economic_softlock_safety_net(state):
    """在没有确定经济恢复路径时，补发一颗雏菊种子。"""
    cheapest_seed_price = _cheapest_unlocked_seed_price(state)
    inventory = state["inventory"]
    if cheapest_seed_price is None or state.get("money", 0) >= cheapest_seed_price:
        return False
    if inventory["seeds"] or inventory["flowers"]:
        return False
    if _has_free_flower_recovery_path(state):
        return False
    inventory["seeds"]["daisy"] = 1
    return True


def get_weather_info(state, now):
    weather_id = state.get("weather", "sunny")
    if weather_id not in WEATHER:
        weather_id = "sunny"
        state["weather"] = weather_id
    weather_data = WEATHER[weather_id]
    weather_data, messages = _settle_garden_timeline(
        state,
        now,
        collect_messages=True,
        advance_growth=False,
    )
    if weather_data.get("auto_water"):
        auto_watered = _auto_water_pots(state, now)
        if auto_watered > 0:
            messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花。")
    refresh_garden_events(state, now)
    return weather_data, messages


def _advance_offline_weather(state, now):
    weather_id = state.get("weather", "sunny")
    if weather_id not in WEATHER:
        weather_id = "sunny"
        state["weather"] = weather_id
    weather_data = WEATHER[weather_id]
    weather_data, _ = _settle_garden_timeline(
        state,
        now,
        collect_messages=False,
        advance_growth=True,
    )
    if weather_data.get("auto_water"):
        _auto_water_pots(state, now)
    return weather_data


def apply_offline_progress(state, now=None, *, letter_context=None):
    if now is None:
        now = int(time.time())
    normalize_state(state, now)
    _refresh_flower_shop_schedule(state, now)

    last_active_at = _safe_nonnegative_int(state.get("last_active_at", state.get("last_update", now)), now)
    elapsed = max(0, now - last_active_at)
    if elapsed <= 0:
        flower_shop_results = settle_flower_shop(state, now)
        state["last_active_at"] = now
        return bool(flower_shop_results)

    settled_seconds = min(elapsed, OFFLINE_PROGRESS_MAX_SECONDS)
    skipped_seconds = max(0, elapsed - settled_seconds)
    settle_at = last_active_at + settled_seconds
    if letter_context is None:
        letter_context = {"messages": [], "remaining_deliveries": 1}

    weather_data = _advance_offline_weather(state, settle_at)
    update_flower_growth(state, settle_at, weather_data)
    check_pests(state, settle_at)
    mood_hours_remaining = MOOD_OFFLINE_CAP_REAL_HOURS

    def advance_cat_stats(until):
        nonlocal mood_hours_remaining
        elapsed_hours = max(0, until - state["last_update"]) / 3600
        if state.get("cat") is None:
            state["last_update"] = max(state["last_update"], until)
            return
        update_cat_stats(
            state, until, weather_data, letter_context=letter_context,
            mood_hours_limit=mood_hours_remaining,
        )
        mood_hours_remaining = max(0.0, mood_hours_remaining - elapsed_hours)

    _, flower_shop_results = _settle_cat_then_flower_shop(
        state,
        settle_at,
        flower_shop_target_time=now,
        letter_context=letter_context,
        before_cat_transition=advance_cat_stats,
    )
    advance_cat_stats(settle_at)
    _resolve_letter_progress(state, now=settle_at, letter_context=letter_context)
    if skipped_seconds > 0:
        # 超限时间不再执行：保留结算终点的状态和计划剩余等待。
        # 只移动尚未到期的计划，已发生事件及状态变化时间保持原值。
        cat_state = state["cat_state"]
        for field in (
            "next_visit_at", "current_visit_leave_at", "stay_deadline_at",
            "next_outing_at", "outing_return_at",
        ):
            if cat_state.get(field, 0) > settle_at:
                cat_state[field] += skipped_seconds
        cat_state["last_lifecycle_settled_at"] = now
    used_food, used_water = _consume_offline_cat_portions(state)

    for pot in state.get("pots", []):
        if isinstance(pot, dict) and not is_pot_withered(pot):
            pot["last_growth_update"] = now
    state["last_pest_check_time"] = now
    if state.get("weather_change_time", now) <= now:
        _schedule_next_weather_change(state, now)
    if state.get("next_butterfly_at", now) <= now:
        _schedule_next_butterfly(state, now)

    state["last_update"] = now
    state["last_active_at"] = now
    state["is_frozen"] = skipped_seconds > 0
    state["garden_frozen_until"] = settle_at if skipped_seconds > 0 else 0
    state["frozen_reason"] = "offline_cap_exceeded" if skipped_seconds > 0 else ""
    state["offline_summary"] = {
        "offline_seconds": elapsed,
        "settled_seconds": settled_seconds,
        "skipped_seconds": skipped_seconds,
        "is_frozen": skipped_seconds > 0,
        "message": (
            f"离线{format_time(elapsed)}，已结算{format_time(settled_seconds)}。"
            + (" 花园在安全状态下暂停等待你回来。" if skipped_seconds > 0 else "")
        ),
        "processed_at": now,
        "auto_food_servings_used": used_food,
        "auto_water_servings_used": used_water,
    }

    apply_economic_softlock_safety_net(state)
    refresh_garden_events(state, now)
    return True


def _summary(state):
    text = (
        f"📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/{len(FLOWERS)} "
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


def _parse_bouquet_arguments(parts):
    bouquet_id = ""
    message_parts = []
    for part in parts[1:]:
        if part.startswith("bouquet_id="):
            bouquet_id = part.split("=", 1)[1].strip().lower()
        elif part.startswith("message="):
            message_parts.append(part.split("=", 1)[1])
        elif not bouquet_id:
            bouquet_id = part.lower()
        else:
            message_parts.append(part)
    return bouquet_id, " ".join(message_parts).strip() or None


def _craft_bouquet_instance(state, bouquet_id):
    if bouquet_id not in BOUQUETS:
        return None, "❌ 没有这款花束，请先使用 make_bouquet 查看配方。"
    bouquet = BOUQUETS[bouquet_id]
    options = {item["bouquet_id"]: item for item in get_bouquet_options(state)}
    option = options.get(bouquet_id)
    if option is None:
        return None, f"❌ 还没有发现「{bouquet['name']}」的配方，先收获所需花材吧。"
    if not option["can_make"]:
        missing = "、".join(
            f"{FLOWERS.get(flower_id, {'name': flower_id})['name']}×{quantity}"
            for flower_id, quantity in option["missing"].items()
        )
        return None, f"❌ 鲜花不够，无法制作{bouquet['name']}。缺少：{missing}"
    for flower_id, quantity in bouquet["components"].items():
        state["inventory"]["flowers"][flower_id] -= quantity
        if state["inventory"]["flowers"][flower_id] <= 0:
            del state["inventory"]["flowers"][flower_id]
    return {
        "instance_id": uuid.uuid4().hex,
        "bouquet_id": bouquet_id,
        "components": dict(bouquet["components"]),
    }, None


def _record_bouquet_gift(state, bouquet_instance, now, message=None, *, event_source="system"):
    bouquet_id = bouquet_instance["bouquet_id"]
    bouquet = BOUQUETS[bouquet_id]
    state.setdefault("bouquet_gifts", []).append(
        {
            "bouquet_id": bouquet_id,
            "components": dict(bouquet_instance["components"]),
            "sent_at": now,
            "message": message,
        }
    )
    event_text = f"💐 送出了一束「{bouquet['name']}」。"
    if message:
        event_text = event_text[:-1] + "，还附了一张小卡片。"
    add_event(state, event_text, now=now, source=event_source, area="flower_shop")


def _parse_flower_shop_start_minute(value):
    value = str(value or "").strip()
    if ":" in value:
        pieces = value.split(":")
        if len(pieces) != 2:
            return None
        try:
            hour, minute = (int(piece) for piece in pieces)
        except ValueError:
            return None
        return hour * 60 + minute if 0 <= hour < 24 and 0 <= minute < 60 else None
    try:
        minute = int(value)
    except ValueError:
        return None
    return minute if 0 <= minute < 24 * 60 else None



@dataclass(frozen=True)
class CommandResult:
    ok: bool
    message: str
    action_message: str | None = None


def process_command(state, command, *, event_source="system", letter_context=None) -> str:
    """保留纯文本调用方式；命令执行与结果判断由 execute_command 统一负责。"""
    return execute_command(
        state, command, event_source=event_source, letter_context=letter_context,
    ).message


def execute_command(state, command, *, event_source="system", letter_context=None) -> CommandResult:
    """在传入的存档字典上执行命令，并原地更新状态。

    该入口供 Flask API / 数据库存档调用，不读取或写入本地 JSON 文件。
    """
    if not isinstance(state, dict):
        raise TypeError("state 必须是字典")

    if not isinstance(command, str) or not command.strip():
        return CommandResult(False, "❌ 请输入命令，输入 help 查看帮助")

    parts = command.strip().split()
    action = parts[0].lower()
    event_source = normalize_event_source(event_source)
    now = int(time.time())
    normalize_state(state, now)
    sync_cottage_rewards(state, now)
    _refresh_flower_shop_schedule(state, now)
    if state.get("is_frozen"):
        state["is_frozen"] = False
        state["garden_frozen_until"] = 0
        state["frozen_reason"] = ""

    if letter_context is None:
        letter_context = {"messages": [], "remaining_deliveries": 1}

    # 先按旧天气结算到当前时刻，再允许天气在此刻变化，避免追溯修改过去。
    previous_weather_data = WEATHER[state["weather"]]
    update_flower_growth(state, now, previous_weather_data)
    update_cat_stats(state, now, previous_weather_data, letter_context=letter_context)
    weather_data, weather_messages = get_weather_info(state, now)
    pest_messages = check_pests(state, now)
    lifecycle_messages, _ = _settle_cat_then_flower_shop(
        state,
        now,
        letter_context=letter_context,
    )
    _consume_offline_cat_portions(state)
    softlock_recovered = apply_economic_softlock_safety_net(state)

    ok, result = False, ""
    all_event_messages = weather_messages + pest_messages + lifecycle_messages
    if softlock_recovered:
        all_event_messages.append("🌱 花园送来1颗雏菊种子。")

    if action == "shop":
        ok, result = True, "🏪 商店\n\n【种子】\n"
        for flower_id, flower_data in FLOWERS.items():
            rarity = flower_data["rarity"]
            emoji = "⚪" if rarity == "common" else "🟢" if rarity == "uncommon" else "🔵" if rarity == "rare" else "🟣"
            if is_flower_unlocked(state, flower_id):
                result += (
                    f"  {emoji} {flower_data['name']}（{flower_id}） - {flower_data['seed_price']}块 "
                    f"({format_time(flower_data['grow_time'])}基础成熟时间, 卖{flower_data['sell_price']}块)\n"
                )
            else:
                result += f"  🔒 {flower_data['name']}（{flower_id}） - {get_unlock_message(flower_id)}\n"
        result += "\n【猫咪用品】\n"
        for item_id in SHOP_CAT_ITEM_IDS:
            item_data = ITEMS[item_id]
            result += f"  {item_data['name']}（{item_id}） - {item_data['price']}块\n"

    elif action == "buy":
        if len(parts) < 2:
            ok, result = False, "❌ 要买什么？"
        else:
            item_id = parts[1].lower()
            quantity = 1 if len(parts) < 3 else parse_positive_int(parts[2])
            if quantity is None:
                ok, result = False, "❌ 数量必须是正整数"
            elif len(parts) > 3:
                ok, result = False, "❌ 用法：buy <物品> [数量]"
            elif item_id in FLOWERS:
                if not is_flower_unlocked(state, item_id):
                    ok, result = False, f"🔒 {FLOWERS[item_id]['name']}尚未解锁，{get_unlock_message(item_id)}"
                else:
                    price = FLOWERS[item_id]["seed_price"] * quantity
                    if state["money"] < price:
                        ok, result = False, f"❌ 钱不够！需要{price}块"
                    else:
                        state["money"] -= price
                        state["inventory"]["seeds"][item_id] = state["inventory"]["seeds"].get(item_id, 0) + quantity
                        ok, result = True, f"✅ 买了{quantity}包{FLOWERS[item_id]['name']}种子！(-{price}块)"
            elif item_id in ITEMS:
                item_data = ITEMS[item_id]
                if item_data["type"] == "permanent":
                    if quantity != 1:
                        ok, result = False, "❌ 永久物品每次只能购买1个"
                    elif _owns_facility(state, item_id):
                        ok, result = False, f"❌ 已经有{item_data['name']}了"
                    elif state["money"] < item_data["price"]:
                        ok, result = False, f"❌ 钱不够！需要{item_data['price']}块"
                    else:
                        state["money"] -= item_data["price"]
                        _apply_facility_purchase(state, item_id)
                        ok, result = True, f"✅ 买了{item_data['name']}！永久生效 (-{item_data['price']}块)"
                else:
                    price = item_data["price"] * quantity
                    if state["money"] < price:
                        ok, result = False, f"❌ 钱不够！需要{price}块"
                    else:
                        package_size = CAT_ITEM_PACKAGE_SIZES.get(item_id, 1)
                        total_portions = quantity * package_size
                        state["money"] -= price
                        _add_inventory_item(state, item_id, total_portions)
                        ok, result = True, f"✅ 买了{quantity}个{item_data['name']}！(-{price}块)"
            else:
                ok, result = False, "❌ 商店没有这个东西"

    elif action == "buy_cottage_furniture":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：buy_cottage_furniture <furniture_id>"
        else:
            item_id = parts[1].lower()
            item = COTTAGE_ITEM_CATALOG.get(item_id)
            cottage_items = state["cottage"]["items"]
            if item is None:
                ok, result = False, "❌ 小屋里没有这件家具"
            elif item.get("legacy_only", False):
                ok, result = False, f"❌ {item['name']}已在 v1-B 停售，不能购买"
            elif item.get("reward_only") or "price" not in item:
                ok, result = False, f"❌ {item['name']}是纪念奖励，不能购买"
            elif item_id in cottage_items:
                ok, result = False, f"❌ 已经拥有{item['name']}了"
            elif state["money"] < item["price"]:
                ok, result = False, f"❌ 金币不足，{item['name']}需要{item['price']}块。"
            else:
                state["money"] -= item["price"]
                cottage_items[item_id] = {"acquired_at": now, "source": event_source}
                add_event(state, f"为小屋添置了{item['name']}", now=now, source=event_source, area="cottage")
                ok, result = True, f"🏠 添置了{item['name']}！(-{item['price']}块)"

    elif action == "plant":
        if len(parts) != 3:
            ok, result = False, "❌ 用法：plant <花> <盆号>"
        else:
            flower_id = parts[1].lower()
            pot_idx = get_pot_index(parts[2], state)
            if flower_id not in FLOWERS:
                ok, result = False, "❌ 没有这种花"
            elif not is_flower_unlocked(state, flower_id):
                ok, result = False, f"🔒 {FLOWERS[flower_id]['name']}尚未解锁，{get_unlock_message(flower_id)}"
            elif pot_idx is None:
                ok, result = False, f"❌ 盆号必须是1-{state['max_pots']}"
            elif state["pots"][pot_idx] is not None:
                if is_pot_withered(state["pots"][pot_idx]):
                    ok, result = False, f"❌ 这个盆里有枯萎的花，请先使用 clear {pot_idx + 1} 清理"
                else:
                    ok, result = False, "❌ 这个盆已经有花了"
            elif state["inventory"]["seeds"].get(flower_id, 0) <= 0:
                ok, result = False, "❌ 没有这种种子"
            else:
                state["pest_treatment"].pop(pot_idx, None)
                is_rainy = bool(weather_data.get("auto_water"))
                state["pots"][pot_idx] = {
                    "flower_id": flower_id,
                    "planted_time": now,
                    "watered": is_rainy,
                    "growth_progress": 0.0,
                    "last_growth_update": now,
                    **_build_pest_plan(flower_id),
                }
                state["inventory"]["seeds"][flower_id] -= 1
                if state["inventory"]["seeds"][flower_id] <= 0:
                    del state["inventory"]["seeds"][flower_id]

                ok, result = True, f"🌱 在盆{pot_idx + 1}种下了{FLOWERS[flower_id]['name']}！"
                if is_rainy:
                    actual_time = FLOWERS[flower_id]["grow_time"] / weather_data["grow_speed"]
                    result += f"\n   🌧️ 雨水自动滋润，预计约{format_time(actual_time)}成熟"
                else:
                    result += f"\n   🏜️ 未浇水，花尚未开始生长，请使用 water {pot_idx + 1}"

    elif action == "water":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：water <盆号> 或 water all"
        else:
            target = parts[1].lower()
            target_indices = []
            if target == "all":
                target_indices = list(range(state["max_pots"]))
            else:
                pot_idx = get_pot_index(target, state)
                if pot_idx is None:
                    ok, result = False, f"❌ 盆号必须是1-{state['max_pots']}，或使用 water all"
                else:
                    target_indices = [pot_idx]

            if not result:
                watered_count = 0
                has_growing_flower = False
                has_withered_flower = False
                has_pest_blocked_flower = False
                for i in target_indices:
                    pot = state["pots"][i]
                    if pot is None:
                        continue
                    if is_pot_withered(pot):
                        has_withered_flower = True
                        continue
                    has_growing_flower = True
                    if get_pot_ai_status(state, i, pot) == "pest_blocked":
                        has_pest_blocked_flower = True
                    if pot_needs_water(pot):
                        pot["watered"] = True
                        pot["last_growth_update"] = now
                        watered_count += 1

                if weather_data.get("auto_water") and has_growing_flower:
                    ok = True
                    if has_pest_blocked_flower:
                        result = "🌧️ 花盆已被雨水滋润；虫害未处理的花仍会暂停生长，需先处理虫害"
                    else:
                        result = "🌧️ 正在下雨，所有生长中的花已经被雨水滋润了"
                elif watered_count > 0:
                    ok = True
                    if has_pest_blocked_flower:
                        result = f"💧 浇水完成！{watered_count}盆花已浇水；虫害未处理的花仍会暂停生长，需先处理虫害"
                    else:
                        result = f"💧 浇水完成！{watered_count}盆花开始生长"
                elif has_withered_flower and not has_growing_flower:
                    ok, result = False, "❌ 枯萎的花无法浇水，请先清理花盆"
                elif not has_growing_flower:
                    ok, result = False, "❌ 指定花盆里没有可浇水的花"
                else:
                    ok, result = False, "❌ 没有需要浇水的花（可能都已经浇过了）"

    elif action == "harvest":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：harvest <盆号> 或 harvest all"
        elif parts[1].lower() == "all":
            ready_indices = []
            for pot_idx, pot in enumerate(state["pots"][: state["max_pots"]]):
                if get_pot_harvest_blocker(state, pot_idx, pot) is None:
                    ready_indices.append(pot_idx)

            if not ready_indices:
                ok, result = False, "❌ 现在没有可以收获的成熟花朵"
            else:
                harvested_messages = [
                    _harvest_one_pot_result(state, pot_idx, now, weather_data, event_source=event_source).message
                    for pot_idx in ready_indices
                ]
                ok, result = True, (
                    f"🧺 一键收获完成，共收获{len(ready_indices)}朵花！\n\n"
                    + "\n\n".join(harvested_messages)
                )
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                ok, result = False, f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                harvest_result = _harvest_one_pot_result(state, pot_idx, now, weather_data, event_source=event_source)
                ok, result = harvest_result.ok, harvest_result.message

    elif action == "treat":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：treat <盆号>"
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                ok, result = False, f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                pot = state["pots"][pot_idx]
                if pot is None:
                    ok, result = False, "❌ 这个盆是空的"
                elif is_pot_withered(pot):
                    ok, result = False, f"❌ 这盆花已经枯萎，无法治疗，请使用 clear {pot_idx + 1} 清理"
                elif not _has_pest_blocker(state, pot_idx, pot):
                    ok, result = False, "❌ 这盆花没有长虫"
                elif state["money"] < PEST_TREATMENT_COST:
                    ok, result = False, f"❌ 治疗需要{PEST_TREATMENT_COST}块，钱不够！"
                else:
                    state["money"] -= PEST_TREATMENT_COST
                    pot.pop("pest_time", None)
                    pot["pest_active"] = False
                    pot["pest_triggered"] = True
                    pot["pest_resolved"] = True
                    pot["last_growth_update"] = now
                    state["pest_treatment"].pop(pot_idx, None)
                    refresh_garden_events(state, now)
                    ok, result = True, (
                        f"✅ 治疗了盆{pot_idx + 1}的花！(-{PEST_TREATMENT_COST}块)\n"
                        "   这盆花在本轮生长周期内不会再长虫。"
                    )

    elif action == "clear":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：clear <盆号>"
        else:
            pot_idx = get_pot_index(parts[1], state)
            if pot_idx is None:
                ok, result = False, f"❌ 盆号必须是1-{state['max_pots']}"
            else:
                pot = state["pots"][pot_idx]
                if pot is None:
                    ok, result = False, "❌ 这个盆是空的"
                elif not is_pot_withered(pot):
                    ok, result = False, "❌ 这盆花还活着，不能清理"
                else:
                    flower_id = pot["flower_id"]
                    flower_name = FLOWERS[flower_id]["name"]
                    state["pots"][pot_idx] = None
                    state["pest_treatment"].pop(pot_idx, None)
                    reward = max(1, FLOWERS[flower_id]["seed_price"] // 2)
                    if random.random() < WITHERED_CLEAR_REWARD_CHANCE:
                        state["money"] += reward
                        ok, result = True, (
                            f"🧹 清理了盆{pot_idx + 1}枯萎的{flower_name}。"
                            f"\n🪙 翻土时找到了{reward}块金币！"
                        )
                    else:
                        ok, result = True, f"🧹 清理了盆{pot_idx + 1}枯萎的{flower_name}，花盆重新空出来了。"
                    add_event(state, f"清理枯萎的{flower_name}（盆{pot_idx + 1}）", now=now, source=event_source, area="garden")

    elif action == "make_bouquet":
        bouquet_id, message = _parse_bouquet_arguments(parts)
        if not bouquet_id:
            ok, result = True, _format_bouquet_options(get_bouquet_options(state))
        else:
            bouquet_instance, error = _craft_bouquet_instance(state, bouquet_id)
            if error:
                ok, result = False, error
            else:
                _record_bouquet_gift(state, bouquet_instance, now, message, event_source=event_source)
                ok, result = True, f"💐 已将{BOUQUETS[bouquet_id]['name']}送给人类！"
                if message:
                    result += " 已附上小卡片。"

    elif action == "craft_bouquet":
        bouquet_id, _ = _parse_bouquet_arguments(parts)
        if not bouquet_id:
            ok, result = False, "❌ 用法：craft_bouquet bouquet_id=<花束ID>"
        else:
            bouquet_instance, error = _craft_bouquet_instance(state, bouquet_id)
            if error:
                ok, result = False, error
            else:
                state.setdefault("bouquet_inventory", []).append(bouquet_instance)
                bouquet_name = BOUQUETS[bouquet_id]["name"]
                add_event(state, f"制作了一束「{bouquet_name}」", now=now, source=event_source, area="flower_shop")
                ok, result = True, f"💐 已制作{bouquet_name}，可从花束背包赠送给人类。"

    elif action == "gift_bouquet":
        instance_id = ""
        message_parts = []
        for part in parts[1:]:
            if part.startswith("instance_id="):
                instance_id = part.split("=", 1)[1].strip()
            elif part.startswith("message="):
                message_parts.append(part.split("=", 1)[1])
            elif not instance_id:
                instance_id = part
            else:
                message_parts.append(part)
        if not instance_id:
            ok, result = False, "❌ 用法：gift_bouquet instance_id=<花束实例ID> [message=...]"
        else:
            bouquet_inventory = state.setdefault("bouquet_inventory", [])
            instance_index = next(
                (index for index, entry in enumerate(bouquet_inventory) if entry.get("instance_id") == instance_id),
                None,
            )
            if instance_index is None:
                ok, result = False, "❌ 背包里没有这束花。"
            else:
                bouquet_instance = bouquet_inventory.pop(instance_index)
                message = " ".join(message_parts).strip() or None
                _record_bouquet_gift(state, bouquet_instance, now, message, event_source=event_source)
                ok, result = True, f"💐 已将{BOUQUETS[bouquet_instance['bouquet_id']]['name']}送给人类！"
                if message:
                    result += " 已附上小卡片。"

    elif action == "list_bouquet":
        instance_id = ""
        requested_slot = None
        invalid_slot = False
        for part in parts[1:]:
            if part.startswith("instance_id="):
                instance_id = part.split("=", 1)[1].strip()
            elif part.startswith("slot="):
                try:
                    requested_slot = int(part.split("=", 1)[1])
                except ValueError:
                    invalid_slot = True
            elif not instance_id:
                instance_id = part
            elif requested_slot is None:
                try:
                    requested_slot = int(part)
                except ValueError:
                    invalid_slot = True
        shop = state["flower_shop"]
        bouquet_inventory = state.setdefault("bouquet_inventory", [])
        inventory_index = next(
            (index for index, entry in enumerate(bouquet_inventory) if entry.get("instance_id") == instance_id),
            None,
        )
        slots = shop.get("slots", [])
        if not instance_id or invalid_slot:
            ok, result = False, "❌ 用法：list_bouquet instance_id=<花束实例ID> [slot=1]"
        elif not shop.get("established_at"):
            ok, result = False, "❌ 请先建造花店。"
        elif not shop.get("launched_at"):
            ok, result = False, "❌ 花店尚未正式开业。"
        elif shop.get("pending_business_start_minute") is not None:
            ok, result = False, "❌ 新营业时间正在等待生效，请在生效后再上架花束。"
        elif not _flower_shop_is_open(shop, now):
            ok, result = False, "❌ 当前是闭店时间，只能在营业时间内上架花束。"
        elif inventory_index is None:
            ok, result = False, "❌ 花束背包里没有这个实例。"
        else:
            if requested_slot is None:
                slot_index = next((index for index, slot in enumerate(slots) if slot is None), None)
            elif 1 <= requested_slot <= len(slots):
                slot_index = requested_slot - 1
            else:
                slot_index = None
                invalid_slot = True
            if invalid_slot:
                ok, result = False, f"❌ 货架位置应为1-{len(slots)}。"
            elif slot_index is None:
                ok, result = False, "❌ 当前没有空货架。"
            elif slots[slot_index] is not None:
                ok, result = False, f"❌ 货架{slot_index + 1}已经有在售花束。"
            else:
                bouquet_instance = bouquet_inventory[inventory_index]
                will_sell, sale_wait = _roll_flower_shop_sale_plan()
                slots[slot_index] = {
                    "instance_id": bouquet_instance["instance_id"],
                    "bouquet_id": bouquet_instance["bouquet_id"],
                    "components": dict(bouquet_instance["components"]),
                    "listed_at": now,
                    "last_settled_at": now,
                    "base_price": get_flower_shop_base_price(bouquet_instance["components"]),
                    "pricing_profile": (
                        _freshener_flower_shop_pricing_profile()
                        if shop.get("has_freshener")
                        else _default_flower_shop_pricing_profile()
                    ),
                    "will_sell": will_sell,
                    "sale_business_seconds_remaining": sale_wait,
                }
                bouquet_inventory.pop(inventory_index)
                bouquet_name = BOUQUETS.get(bouquet_instance["bouquet_id"], {}).get(
                    "name", bouquet_instance["bouquet_id"]
                )
                add_event(state, f"🏪 将「{bouquet_name}」放上货架{slot_index + 1}开始销售。", now=now, source=event_source, area="flower_shop")
                settlement_results = settle_flower_shop(state, now)
                immediate_sale = next(
                    (entry for entry in settlement_results if entry.get("slot") == slot_index + 1),
                    None,
                )
                if immediate_sale and immediate_sale["type"] == "sold":
                    ok, result = True, f"🏪 「{bouquet_name}」上架后立即以{immediate_sale['price']}块成交。"
                else:
                    ok, result = True, f"🏪 已将「{bouquet_name}」上架到货架{slot_index + 1}。上架后不可撤回。"

    elif action == "establish_flower_shop":
        shop = state["flower_shop"]
        if shop.get("established_at"):
            ok, result = False, "❌ 花店已经建好了，不会重复扣款。"
        elif not is_flower_shop_eligible(state):
            progress = get_flower_shop_eligibility_progress(state)
            ok, result = False, (
                "❌ 还不满足建店条件："
                f"图鉴{progress['encyclopedia']}/10，累计收获{progress['harvests']}/42，"
                f"直接卖花收入{progress['direct_flower_sale_earned']}/3000。"
            )
        elif state["money"] < FLOWER_SHOP_ESTABLISH_COST:
            ok, result = False, f"❌ 建造花店需要{FLOWER_SHOP_ESTABLISH_COST}块金币。"
        else:
            state["money"] -= FLOWER_SHOP_ESTABLISH_COST
            state["flower_shop"] = {
                **_default_flower_shop_state(),
                "established_at": now,
                "shelf_capacity": FLOWER_SHOP_SHELF_CAPACITY,
                "slots": [None] * FLOWER_SHOP_SHELF_CAPACITY,
            }
            add_event(state, "建好了花店，准备了3个空货架", now=now, source=event_source, area="flower_shop")
            ok, result = True, "🏪 花店建好了！现在有3个空货架，请先设置每天的营业开始时间。"

    elif action == "upgrade_flower_shop_shelf":
        shop = state["flower_shop"]
        current_capacity = int(shop.get("shelf_capacity", 0) or 0)
        next_capacity = next(
            (capacity for capacity in FLOWER_SHOP_SHELF_CAPACITIES if capacity > current_capacity),
            None,
        )
        upgrade_cost = FLOWER_SHOP_SHELF_UPGRADE_COSTS.get(current_capacity)
        if not shop.get("established_at"):
            ok, result = False, "❌ 请先建造花店。"
        elif next_capacity is None or upgrade_cost is None:
            ok, result = False, "❌ 货架已经扩至最大容量。"
        elif state["money"] < upgrade_cost:
            ok, result = False, f"❌ 金币不足，扩建至{next_capacity}格需要{upgrade_cost}块。"
        else:
            slots = shop.setdefault("slots", [])
            state["money"] -= upgrade_cost
            shop["shelf_capacity"] = next_capacity
            slots.extend([None] * (next_capacity - len(slots)))
            ok, result = True, f"🏪 货架已扩建至{next_capacity}格，花费{upgrade_cost}块。"

    elif action == "buy_flower_shop_freshener":
        shop = state["flower_shop"]
        if not shop.get("established_at"):
            ok, result = False, "❌ 请先建造花店。"
        elif shop.get("has_freshener"):
            ok, result = False, "❌ 保鲜设备已经安装好了。"
        elif state["money"] < FLOWER_SHOP_FRESHENER_COST:
            ok, result = False, f"❌ 金币不足，保鲜设备需要{FLOWER_SHOP_FRESHENER_COST}块。"
        else:
            state["money"] -= FLOWER_SHOP_FRESHENER_COST
            shop["has_freshener"] = True
            add_event(state, "🏪 安装了花店保鲜设备。", now=now, source=event_source, area="flower_shop")
            ok, result = True, "🏪 保鲜设备已安装；之后新上架的花束会更晚进入折价阶段，但仍会在24小时后报废。"

    elif action == "set_flower_shop_hours":
        shop = state["flower_shop"]
        if not shop.get("established_at"):
            ok, result = False, "❌ 请先建造花店。"
        elif len(parts) != 2:
            ok, result = False, "❌ 用法：set_flower_shop_hours <HH:MM>"
        elif shop.get("launched_at") and _flower_shop_is_open(shop, now):
            ok, result = False, "❌ 花店营业中，闭店后且货架全空时才能调整营业开始时间。"
        elif any(slot is not None for slot in shop.get("slots", [])):
            ok, result = False, "❌ 货架尚有上架商品，清空后才能调整营业开始时间。"
        else:
            start_minute = _parse_flower_shop_start_minute(parts[1])
            if start_minute is not None:
                end_minute = start_minute + FLOWER_SHOP_BUSINESS_DURATION_MINUTES
                end_label = (
                    "24:00" if end_minute == 24 * 60 else
                    f"{'次日 ' if end_minute > 24 * 60 else ''}{(end_minute // 60) % 24:02d}:{end_minute % 60:02d}"
                )
            if start_minute is None:
                ok, result = False, "❌ 营业开始时间请使用 HH:MM（例如 09:30）。"
            elif not shop.get("launched_at"):
                shop["business_start_minute"] = start_minute
                shop["pending_business_start_minute"] = None
                shop["pending_business_effective_at"] = None
                ok, result = True, "🕙 已设置花店每天营业10小时的开始时间。"
            else:
                effective_at = _next_flower_shop_business_date(now)
                shop["business_start_minute"] = None
                shop["pending_business_start_minute"] = start_minute
                shop["pending_business_effective_at"] = effective_at
                ok, result = True, (
                    "🕙 营业时间已调整，新时间将于下一自然日生效。今天剩余时间花店保持闭店。"
                    f"\n新营业时段：{start_minute // 60:02d}:{start_minute % 60:02d}–{end_label}。"
                )

            if ok:
                add_event(state, f"🕙 设置花店营业时段：{start_minute // 60:02d}:{start_minute % 60:02d}–{end_label}。",
                          now=now, source=event_source, area="flower_shop")

    elif action == "launch_flower_shop":
        shop = state["flower_shop"]
        if not shop.get("established_at"):
            ok, result = False, "❌ 请先建造花店。"
        elif shop.get("launched_at"):
            ok, result = False, "❌ 花店已经正式开业了。"
        elif shop.get("business_start_minute") is None:
            ok, result = False, "❌ 请先设置每天的营业开始时间。"
        else:
            shop["launched_at"] = now
            if _flower_shop_is_open_for_start(shop.get("business_start_minute"), now):
                ok, result = True, "🎉 花店正式开业！当前正处于营业时间。"
            else:
                ok, result = True, "🎉 花店正式开业！当前已闭店，等待下一次营业周期。"

    elif action == "arrange":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：arrange <花>"
        else:
            flower_id = parts[1].lower()
            vase = state.setdefault("vase", [])
            if flower_id not in FLOWERS:
                ok, result = False, "❌ 没有这种花"
            elif len(vase) >= VASE_CAPACITY:
                ok, result = False, f"❌ 花瓶已经插满了（最多{VASE_CAPACITY}朵）"
            elif state["inventory"]["flowers"].get(flower_id, 0) <= 0:
                ok, result = False, "❌ 背包里没有这种已经收获的花"
            else:
                state["inventory"]["flowers"][flower_id] -= 1
                if state["inventory"]["flowers"][flower_id] <= 0:
                    del state["inventory"]["flowers"][flower_id]
                vase.append({"flower_id": flower_id, "arranged_time": now})
                ok, result = True, (
                    f"💐 把一朵{FLOWERS[flower_id]['name']}插进了花瓶。"
                    f"\n   花瓶里的花不能再出售，可保持约{VASE_LIFESPAN_REAL_HOURS}小时。"
                )
                add_event(state, f"把{FLOWERS[flower_id]['name']}插进花瓶", now=now, source=event_source, area="garden")

    elif action == "vase":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：vase"
        else:
            ok, result = True, get_vase_status(state, now)

    elif action == "remove_vase":
        if len(parts) != 2:
            ok, result = False, "❌ 用法：remove_vase <位置>"
        else:
            vase = state.setdefault("vase", [])
            try:
                vase_idx = int(parts[1]) - 1
            except ValueError:
                ok, result = False, "❌ 花瓶位置必须是数字"
            else:
                if vase_idx < 0 or vase_idx >= len(vase):
                    if vase:
                        ok, result = False, f"❌ 花瓶位置应为1-{len(vase)}"
                    else:
                        ok, result = False, "❌ 花瓶现在是空的"
                else:
                    entry = vase.pop(vase_idx)
                    flower_name = FLOWERS[entry["flower_id"]]["name"]
                    ok, result = True, (
                        f"🧹 从花瓶位置{vase_idx + 1}移除了{flower_name}。"
                        "\n   花朵和金币都不会返还。"
                    )
                    add_event(state, f"从花瓶移除{flower_name}", now=now, source=event_source, area="garden")

    elif action == "sell":
        if len(parts) < 2:
            ok, result = False, "❌ 要卖什么？"
        elif parts[1].lower() == "all":
            if len(parts) != 2:
                ok, result = False, "❌ 用法：sell all"
            else:
                total = sum(
                    FLOWERS[flower_id]["sell_price"] * qty
                    for flower_id, qty in state["inventory"]["flowers"].items()
                    if flower_id in FLOWERS and qty > 0
                )
                if total <= 0:
                    ok, result = False, "❌ 背包里没有花可卖"
                else:
                    state["money"] += total
                    state["total_earned"] += total
                    state["direct_flower_sale_earned"] += total
                    state["inventory"]["flowers"] = {}
                    add_event(state, f"卖掉所有花，赚了{total}块", source=event_source, area="garden")
                    ok, result = True, f"💰 卖掉所有花，赚了{total}块！"
        else:
            flower_id = parts[1].lower()
            quantity = 1 if len(parts) < 3 else parse_positive_int(parts[2])
            if len(parts) > 3:
                ok, result = False, "❌ 用法：sell <花> [数量]"
            elif quantity is None:
                ok, result = False, "❌ 出售数量必须是大于0的整数"
            elif flower_id not in FLOWERS or state["inventory"]["flowers"].get(flower_id, 0) <= 0:
                ok, result = False, "❌ 没有这种花"
            elif state["inventory"]["flowers"][flower_id] < quantity:
                ok, result = False, "❌ 数量不够"
            else:
                price = FLOWERS[flower_id]["sell_price"] * quantity
                state["money"] += price
                state["total_earned"] += price
                state["direct_flower_sale_earned"] += price
                state["inventory"]["flowers"][flower_id] -= quantity
                if state["inventory"]["flowers"][flower_id] <= 0:
                    del state["inventory"]["flowers"][flower_id]
                add_event(
                    state,
                    f"卖了{quantity}朵{FLOWERS[flower_id]['name']}，赚了{price}块",
                    source=event_source, area="garden",
                )
                ok, result = True, f"💰 卖了{quantity}朵{FLOWERS[flower_id]['name']}，赚了{price}块！"

    elif action == "adopt":
        requested_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        cat_name = normalize_cat_name(requested_name, default=None)
        if cat_name is None:
            ok, result = False, f"❌ 猫咪名字不能为空，且不能超过{CAT_NAME_MAX_LENGTH}个字符"
        elif _has_adopted_cat(state):
            ok, result = False, "❌ 已经有猫了"
        elif state["cat"] is not None and state.get("cat_state", {}).get("phase") == CAT_PHASE_ADOPTED:
            ok, result = False, "❌ 已经有猫了"
        elif not _can_finalize_adoption(state):
            ok, result = False, "❌ 当前猫咪状态还不能正式收养"
        else:
            _ensure_cat_stats_for_lifecycle(state)
            _normalize_v5_cat_foundation(state, now)
            state["cat"]["name"] = cat_name
            _set_cat_phase(state, CAT_PHASE_ADOPTED, now)
            _set_cat_location(state, CAT_LOCATION_HOME, now)
            state["cat_state"]["next_visit_at"] = 0
            state["cat_state"]["current_visit_started_at"] = 0
            state["cat_state"]["current_visit_leave_at"] = 0
            state["cat_state"]["outing_return_at"] = 0
            _schedule_next_adopted_outing(state["cat_state"], now)
            if state.get("cat_last_pet_real_time", 0) <= 0:
                state["cat_last_pet_real_time"] = now - (PET_COOLDOWN_REAL_MINUTES * 60)
            _sync_cat_stats_views(state)
            ok, result = True, f"🎉 成功收养了{cat_name}！记得喂它哦~"

    elif action == "rename_cat":
        if state["cat"] is None:
            ok, result = False, "❌ 还没有猫"
        elif len(parts) < 2:
            ok, result = False, "❌ 用法：rename_cat <名字>"
        else:
            new_name = normalize_cat_name(" ".join(parts[1:]), default=None)
            if new_name is None:
                ok, result = False, f"❌ 猫咪名字不能为空，且不能超过{CAT_NAME_MAX_LENGTH}个字符"
            else:
                old_name = state["cat"].get("name", "小猫")
                state["cat"]["name"] = new_name
                ok, result = True, f"🐱 {old_name}现在叫{new_name}了！"

    elif action == "feed":
        if state["cat"] is None:
            ok, result = False, "❌ 还没有猫"
        elif len(parts) != 2 or parts[1].lower() not in ("basic", "premium"):
            ok, result = False, "❌ 用法：feed <basic|premium>"
        else:
            food_type = CAT_CARE_FOOD_TYPES[parts[1].lower()]
            refill_result = _refill_food_bowl(
                state,
                food_type,
                now=now,
                source=f"feed:{food_type}",
                letter_context=letter_context,
            )
            food_name = ITEMS[refill_result["refill_type"]]["name"]
            cat_name = get_current_cat_name(state)
            if refill_result["space"] <= 0:
                ok, result = False, "❌ 粮碗已经满了"
            elif refill_result["added"] <= 0:
                ok, result = False, f"❌ 背包里的{food_name}不够"
            elif refill_result["eaten"] > 0:
                ok, result = True, f"🍽️ 已给粮碗补充{food_name}，{cat_name}吃了{refill_result['eaten']}份。"
            elif not _is_cat_near_bowls(state):
                ok, result = True, f"🍽️ 已给粮碗补充{refill_result['added']}份{food_name}。{cat_name}现在不在碗边。"
            else:
                ok, result = True, f"🍽️ 已给粮碗补充{refill_result['added']}份{food_name}。"

    elif action == "give_water":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：give_water"
        elif state["cat"] is None:
            ok, result = False, "❌ 还没有猫"
        else:
            refill_result = _refill_water_bowl(
                state,
                now=now,
                source="give_water",
                letter_context=letter_context,
            )
            cat_name = get_current_cat_name(state)
            if refill_result["space"] <= 0:
                ok, result = False, "❌ 水碗已经满了"
            elif refill_result["drank"] > 0:
                ok, result = True, f"💧 已给水碗补满清水，{cat_name}喝了{refill_result['drank']}份。"
            elif not _is_cat_near_bowls(state):
                ok, result = True, f"💧 已给水碗补满清水。{cat_name}现在不在碗边。"
            else:
                ok, result = True, "💧 已给水碗补满清水。"

    elif action == "refill_food":
        if len(parts) not in (2, 3) or parts[1].lower() not in CAT_CARE_FOOD_TYPES:
            ok, result = False, "❌ 用法：refill_food <basic|premium> [份数]"
        elif state["cat"] is None:
            ok, result = False, "鉂?杩樻病鏈夌尗"
        else:
            refill_result = _refill_food_bowl(
                state,
                CAT_CARE_FOOD_TYPES[parts[1].lower()],
                now=now,
                source=f"refill_food:{parts[1].lower()}",
                letter_context=letter_context,
            )
            bowl = state["cat_care"]["food_bowl"]
            food_type = refill_result["refill_type"]
            if refill_result["space"] <= 0:
                ok, result = False, "❌ 粮碗已经满了"
            elif refill_result["added"] <= 0:
                ok, result = False, f"❌ 背包里的{ITEMS[food_type]['name']}不够"
            elif refill_result["eaten"] > 0:
                cat_name = get_current_cat_name(state)
                ok, result = True, (
                    f"✅ 已补充{ITEMS[food_type]['name']}，"
                    f"{cat_name}吃了{refill_result['eaten']}份，当前剩余 {bowl['remaining_portions']}/{bowl['capacity']}"
                )
            else:
                ok, result = True, f"✅ 已向粮碗补充{refill_result['added']}份{ITEMS[food_type]['name']}"

    elif action == "refill_water":
        if len(parts) not in (1, 2):
            ok, result = False, "❌ 用法：refill_water [份数]"
        elif state["cat"] is None:
            ok, result = False, "鉂?杩樻病鏈夌尗"
        else:
            refill_result = _refill_water_bowl(
                state,
                now=now,
                source="refill_water",
                letter_context=letter_context,
            )
            bowl = state["cat_care"]["water_bowl"]
            if refill_result["space"] <= 0:
                ok, result = False, "❌ 水碗已经满了"
            elif refill_result["drank"] > 0:
                cat_name = get_current_cat_name(state)
                ok, result = True, (
                    f"✅ 已补满清水，"
                    f"{cat_name}喝了{refill_result['drank']}份，当前剩余 {bowl['remaining_portions']}/{bowl['capacity']}"
                )
            else:
                ok, result = True, f"✅ 已向水碗补充{refill_result['space']}份清水"

    elif action == "switch_food":
        if len(parts) != 2 or parts[1].lower() not in CAT_CARE_FOOD_TYPES:
            ok, result = False, "❌ 用法：switch_food <basic|premium>"
        elif state["cat"] is None:
            ok, result = False, "鉂?杩樻病鏈夌尗"
        else:
            food_type = CAT_CARE_FOOD_TYPES[parts[1].lower()]
            switch_result = _switch_food_bowl(
                state,
                food_type,
                now=now,
                source=f"switch_food:{food_type}",
                letter_context=letter_context,
            )
            if False:
                ok, result = False, f"❌ 背包里没有{ITEMS[food_type]['name']}，无法切换"
            else:
                state["cat_care"]["food_bowl"]["food_type"] = food_type
                ok, result = True, f"✅ 当前猫粮已切换为{ITEMS[food_type]['name']}"

    elif action == "give_treat":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：give_treat"
        elif state["cat"] is None:
            ok, result = False, "鉂?杩樻病鏈夌尗"
        elif state["inventory"]["items"].get(CAT_TREAT_ITEM_ID, 0) <= 0:
            ok, result = False, "❌ 没有猫零食了"
        else:
            cat_name = get_current_cat_name(state)
            cat_present = _is_cat_present_for_interaction(state)
            state["_interaction_accepted"] = cat_present and _roll_interaction_acceptance(state, "give_treat")
            _use_inventory_item(state, CAT_TREAT_ITEM_ID, 1)
            _apply_cat_effects(
                state,
                ITEMS[CAT_TREAT_ITEM_ID]["effect"],
                now=now,
                source="give_treat",
                letter_context=letter_context,
            )
            add_affection(
                state,
                2 if state.get("_interaction_accepted") is not False else 0,
                now=now,
                source="give_treat",
                letter_context=letter_context,
            )
            if state.get("_interaction_accepted") is not False:
                ok, result = True, f"🍬 给{cat_name}喂了零食，心情和亲密都上升了一点"
            elif not cat_present:
                ok, result = False, f"🍬 {cat_name}现在不在这里，零食没有消耗"
            else:
                ok, result = False, f"🍬 {cat_name}闻了闻零食，暂时没有吃，零食没有消耗"

    elif action == "pet":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：pet"
        elif state["cat"] is None:
            ok, result = False, "❌ 还没有猫"
        elif not _is_cat_present_for_interaction(state):
            ok, result = False, f"❌ {get_current_cat_name(state)}现在不在这里，暂时不能摸猫。"
        else:
            last_pet_time = state.get("cat_last_pet_real_time", 0)
            cooldown_seconds = PET_COOLDOWN_REAL_MINUTES * 60
            time_since_last_pet = now - last_pet_time
            cat_name = get_current_cat_name(state)
            if time_since_last_pet < cooldown_seconds:
                ok, result = False, f"❌ {cat_name}现在不想被摸，过{format_time(cooldown_seconds - time_since_last_pet)}再试"
            else:
                state["cat_last_pet_real_time"] = now
                _change_cat_stat(state, "mood", 3)
                add_affection(
                    state,
                    1,
                    now=now,
                    source="pet",
                    letter_context=letter_context,
                )
                ok, result = True, f"🤗 抚摸了{cat_name}，它很开心！心情和亲密都上升了一点"

    elif action == "play":
        if state["cat"] is None:
            ok, result = False, "❌ 还没有猫"
        elif len(parts) != 2 or parts[1].lower() not in ("ball", "feather"):
            ok, result = False, "❌ 用法：play <ball|feather>"
        else:
            toy_id = "ball" if parts[1].lower() == "ball" else "feather_wand"
            if state["inventory"]["items"].get(toy_id, 0) <= 0:
                ok, result = False, "❌ 没有这个玩具"
            else:
                cat_name = get_current_cat_name(state)
                cat_present = _is_cat_present_for_interaction(state)
                state["_interaction_accepted"] = cat_present and _roll_interaction_acceptance(state, toy_id)
                _use_inventory_item(state, toy_id, 1)
                _apply_cat_effects(
                    state,
                    ITEMS[toy_id]["effect"],
                    now=now,
                    source=f"play:{toy_id}",
                    letter_context=letter_context,
                )
                add_affection(
                    state,
                    (1 if toy_id == "ball" else 2) if state.get("_interaction_accepted") is not False else 0,
                    now=now,
                    source=f"play:{toy_id}",
                    letter_context=letter_context,
                )
                if state.get("_interaction_accepted") is not False:
                    ok, result = True, f"🎾 和{cat_name}玩了{ITEMS[toy_id]['name']}！（玩具已消耗）"
                elif not cat_present:
                    ok, result = False, f"🎾 {cat_name}现在不在这里，玩具没有消耗"
                else:
                    ok, result = False, f"🎾 {cat_name}看了看{ITEMS[toy_id]['name']}，暂时不想玩，玩具没有消耗"

    elif action == "buy_pot":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：buy_pot"
        elif state["max_pots"] >= MAX_POTS:
            ok, result = False, f"❌ 已经有{MAX_POTS}个花盆了，无法再扩展！"
        else:
            next_pot_number = state["max_pots"] + 1
            pot_cost = get_next_pot_cost(state)
            if pot_cost is None:
                ok, result = False, f"❌ 已经有{MAX_POTS}个花盆了，无法再扩展！"
            elif state["money"] < pot_cost:
                ok, result = False, f"❌ 解锁第{next_pot_number}个花盆需要{pot_cost}块，钱不够！"
            else:
                state["money"] -= pot_cost
                state["pots"].append(None)
                state["max_pots"] += 1
                ok, result = True, (
                    f"✅ 解锁了第{next_pot_number}个花盆！"
                    f"现在有{state['max_pots']}个花盆 (-{pot_cost}块)"
                )

    elif action == "collectibles":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：collectibles"
        else:
            unique_count = get_collectible_unique_count(state)
            total_count = sum(state["collectibles"].values())
            max_affection = get_cat_max_affection(state)
            lines = [
                "🎁 猫咪的小小收藏",
                f"  已收集：{unique_count}/{len(CAT_COLLECTIBLES)}种（共{total_count}件）",
                f"  历史最高亲密度：{int(max_affection)}",
                "  条件满足后仅代表进入随机范围，仍可能重复带回已有物品。",
            ]

            for collectible in CAT_COLLECTIBLES:
                count = state["collectibles"].get(collectible["id"], 0)
                rarity_name = CAT_COLLECTIBLE_RARITY_LABELS.get(
                    collectible.get("rarity"), ""
                )

                if count > 0:
                    lines.append(
                        f"\n  {collectible['emoji']} {collectible['name']} x{count} · {rarity_name}"
                    )
                    lines.append(f"     {collectible['description']}")
                    first_found = state.get("collectible_first_found", {}).get(
                        collectible["id"], 0
                    )
                    if first_found:
                        date_text = datetime.fromtimestamp(first_found).strftime("%Y-%m-%d")
                        lines.append(f"     首次获得：{date_text}")
                else:
                    unlock_mark = "🔓" if is_collectible_unlocked(state, collectible) else "🔒"
                    lines.append(f"\n  {unlock_mark} ❓ 未知的小东西 · {rarity_name}")
                    lines.append(f"     {get_collectible_status_text(state, collectible)}")
                    boost_hint = get_collectible_boost_hint(collectible)
                    if boost_hint:
                        lines.append(f"     {boost_hint}")

            ok, result = True, "\n".join(lines)

    elif action == "letters":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：letters"
        else:
            lines = [
                "✉️ 猫咪来信",
                f"  已收集：{len(state['letters_received'])}/{len(CAT_LETTERS)}封",
            ]
            if not state["letters_received"]:
                lines.append("  还没有收到信")
            else:
                for idx in state["letters_received"]:
                    letter = CAT_LETTERS[idx]
                    lines.append(f"\n  第{idx + 1}封《{letter['title']}》")
                    lines.extend(f"    {line}" for line in letter["text"].splitlines())
            ok, result = True, "\n".join(lines)

    elif action == "encyclopedia":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：encyclopedia"
        else:
            lines = ["📚 图鉴"]
            for flower_id, flower_data in FLOWERS.items():
                if flower_id in state["encyclopedia"]:
                    lines.append(f"  ✅ {flower_data['name']} ({flower_data['rarity']})")
                else:
                    lines.append("  ❓ ???")
            lines.append(f"\n进度：{len(state['encyclopedia'])}/{len(FLOWERS)}")
            ok, result = True, "\n".join(lines)

    elif action == "status":
        if len(parts) != 1:
            ok, result = False, "❌ 用法：status"
        else:
            ok, result = True, get_status(state, weather_data)

    elif action == "help":
        weather_help = "\n".join(
            f"{weather['emoji']} {weather['name']}：花生长×{weather['grow_speed']:.1f}，"
            + ("自动浇水" if weather.get("auto_water") else "需手动浇水")
            for weather in WEATHER.values()
        )
        flower_unlock_help = "\n".join(
            f"- {flower['name']}：{get_unlock_message(flower_id)}"
            for flower_id, flower in FLOWERS.items()
        )
        ok, result = True, f"""💡 命令帮助：
shop - 查看商店
buy <商品ID> [数量] - 买东西；商品ID必须使用catalog中flowers/items的key（如daisy、basic_food），数量必须是正整数
buy_cottage_furniture <furniture_id> - 用共同余额为小屋添置一件主家具
plant <花> <盆号> - 种花（雨天自动浇水，否则需手动浇水才能生长）
water <盆号|all> - 给花浇水（浇一次永久有效，直到收获）
harvest <盆号|all> - 收获一盆，或一键收获全部成熟花朵
make_bouquet [bouquet_id=...] [message=...] - 查看或制作花束并送给人类
craft_bouquet bouquet_id=<花束ID> - 制作一束花并放进花束背包
gift_bouquet instance_id=<花束实例ID> [message=...] - 从花束背包赠送
list_bouquet instance_id=<花束实例ID> [slot=1] - 营业时将花束上架到空货架
establish_flower_shop - 满足条件后花费{FLOWER_SHOP_ESTABLISH_COST}块建造花店
upgrade_flower_shop_shelf - 将花店货架扩建至下一档容量
buy_flower_shop_freshener - 安装保鲜设备，之后新上架花束更晚折价
set_flower_shop_hours <HH:MM> - 设置每天固定10小时营业的开始时间
launch_flower_shop - 在已建店并设置营业时间后正式开业
sell <花> [数量] - 卖花，或 sell all
treat <盆号> - 治疗害虫({PEST_TREATMENT_COST}块，本轮不再长虫)
clear <盆号> - 清理枯萎花（50%概率获得少量金币）
buy_pot - 解锁下一个花盆(第4盆20块 / 第5盆35块 / 第6盆50块)
arrange <花> - 把已收获鲜花插入花瓶（插入后不可出售）
vase - 查看花瓶与鲜花枯萎度
remove_vase <位置> - 移除花瓶中任意状态的花（不返还花朵或金币）
adopt [名字] - 正式收养猫咪并可选取名
rename_cat <名字> - 给已收养的猫咪改名
feed <basic|premium> - 给粮碗补充猫粮
give_water - 给水碗补水
pet - 抚摸猫(冷却{PET_COOLDOWN_REAL_MINUTES}分钟)
play <ball|feather> - 和猫玩（消耗玩具）
encyclopedia - 查看图鉴
collectibles - 查看猫咪收集品
letters - 查看猫咪信件
status - 查看状态
help - 显示帮助

🌤️ 天气系统（真实时间）：
{weather_help}
天气不直接改变猫咪心情数值。
天气按现实时间变化；离线期间的天气事件按时间顺序补算

💧 浇水系统：
- 花种下后默认不生长，需浇水才能开始生长
- 未浇水期间不会积累进度，之后浇水也不会补算
- 手动浇水一次后永久有效，直到本轮收获
- 雨天自动滋润所有花盆

🐱 猫咪系统（真实时间）：
  饱食度：-5/小时    口渴度：-5/小时
  心情：基础衰减-{MOOD_BASE_DECAY:g}/小时；单次离线最多结算前{MOOD_OFFLINE_CAP_REAL_HOURS:g}小时
  亲密度：visitor / stayed_waiting_name 不发生被动衰减
         adopted 每小时被动衰减{AFFECTION_NATURAL_DECAY:g}，最低到30
         已低于30的旧状态不会自动抬高；主动互动增益保持原规则

🌸 花卉解锁：
{flower_unlock_help}
已收录的花卉保持解锁。

🎉 特殊事件：
🌈 雨后彩虹：获得金币或普通种子
🦋 蝴蝶飞过：每5分钟最多检查一次，可能掉落少量金币
🎁 猫咪收集品：首次实际吃喝后开启；完整来访结束或外出回家时可能带回，允许重复
✉️ 猫咪写信：正向亲密按4点一批做50%判定，按亲密度顺序收12封信
🐛 种植时确定虫害，达到触发点后暂停生长，治疗后继续

💐 花瓶系统：
- 花瓶最多插{VASE_CAPACITY}朵已经收获的花
- 插花后不能再出售，可保持约{VASE_LIFESPAN_REAL_HOURS}小时
- vase 可查看新鲜程度与枯萎度
- 任意状态都可使用 remove_vase <位置> 移除，且不返还花朵或金币"""

    else:
        ok, result = False, "❌ 未知命令，输入 help 查看帮助"

    if action != "pet" or _is_cat_present_for_interaction(state):
        _resolve_letter_progress(state, now=now, letter_context=letter_context)
    update_cat_max_affection(state)

    action_message = result
    if all_event_messages:
        result = "\n".join(all_event_messages) + "\n\n" + result
    if letter_context["messages"]:
        result = result + "\n" + "\n".join(letter_context["messages"])

    if action != "status" or (not ok and not all_event_messages):
        result += "\n\n" + _summary(state)

    state["last_active_at"] = now
    return CommandResult(ok, result, action_message)


_BASE_NORMALIZE_STATE = normalize_state


def _roll_pest_trigger_progress(flower_id):
    grow_time = float(FLOWERS[flower_id]["grow_time"])
    trigger_percent = random.randint(PEST_TRIGGER_MIN_PERCENT, PEST_TRIGGER_MAX_PERCENT)
    return grow_time * (trigger_percent / 100.0)


def _build_pest_plan(flower_id):
    if random.random() >= 0.10:
        return {
            "pest_trigger_progress": None,
            "pest_triggered": False,
            "pest_active": False,
            "pest_resolved": False,
        }
    return {
        "pest_trigger_progress": _roll_pest_trigger_progress(flower_id),
        "pest_triggered": False,
        "pest_active": False,
        "pest_resolved": False,
    }


def _get_pest_trigger_progress(pot, flower_id):
    trigger_progress = pot.get("pest_trigger_progress")
    if trigger_progress in (None, ""):
        return None
    try:
        trigger_progress = float(trigger_progress)
    except (TypeError, ValueError):
        return None
    grow_time = float(FLOWERS[flower_id]["grow_time"])
    minimum = grow_time * (PEST_TRIGGER_MIN_PERCENT / 100.0)
    return min(grow_time, max(minimum, trigger_progress))


def _has_pest_blocker(state, pot_idx, pot):
    if not isinstance(pot, dict):
        return False
    if bool(pot.get("pest_active", False)):
        return True
    if pot.get("pest_resolved", False):
        return False
    return pot.get("pest_time") is not None


def get_pot_harvest_blocker(state, pot_idx, pot):
    """Return why a pot cannot be harvested, or None when it is ready."""
    if pot_idx < 0 or pot_idx >= int(state.get("max_pots", 0) or 0):
        return "invalid_index"
    if pot is None:
        return "empty"
    if is_pot_withered(pot):
        return "withered"
    if _has_pest_blocker(state, pot_idx, pot):
        return "pest"
    flower = FLOWERS.get(pot.get("flower_id")) if isinstance(pot, dict) else None
    if flower is None:
        return "unknown_flower"
    progress = float(pot.get("growth_progress", 0.0))
    if progress < float(flower["grow_time"]):
        return "growing"
    return None


def get_pot_ai_status(state, pot_idx, pot):
    """Return the shared decision status used by structured and text summaries."""
    blocker = get_pot_harvest_blocker(state, pot_idx, pot)
    if blocker is None:
        return "ready"
    if blocker == "pest":
        return "pest_blocked"
    if blocker in ("empty", "withered"):
        return blocker
    if pot_needs_water(pot):
        return "needs_water"
    return "growing"


def _activate_pest(state, pot_idx, now):
    pot = state["pots"][pot_idx]
    if not isinstance(pot, dict):
        return False
    if pot.get("pest_resolved", False):
        pot["pest_active"] = False
        return False
    if pot.get("pest_active", False):
        pot["last_growth_update"] = now
        return False
    flower_id = pot["flower_id"]
    trigger_progress = _get_pest_trigger_progress(pot, flower_id)
    current_progress = float(pot.get("growth_progress", 0.0))
    if trigger_progress is None:
        trigger_progress = current_progress
    pot["pest_trigger_progress"] = trigger_progress
    pot["growth_progress"] = min(float(FLOWERS[flower_id]["grow_time"]), max(current_progress, trigger_progress))
    pot["pest_triggered"] = True
    pot["pest_active"] = True
    pot["pest_resolved"] = False
    pot["last_growth_update"] = now
    pot.pop("pest_time", None)
    state.get("pest_treatment", {}).pop(pot_idx, None)
    add_event(state, f"盆{pot_idx + 1}出现虫害", now=now, area="garden")
    return True


def _normalize_v5_pests(data, now):
    for i, pot in enumerate(data.get("pots", [])):
        if not isinstance(pot, dict) or pot.get("flower_id") not in FLOWERS:
            continue
        flower_id = pot["flower_id"]
        grow_time = float(FLOWERS[flower_id]["grow_time"])
        if pot.get("withered", False):
            pot["pest_trigger_progress"] = None
            pot["pest_triggered"] = False
            pot["pest_active"] = False
            pot["pest_resolved"] = False
            pot.pop("pest_time", None)
            data.get("pest_treatment", {}).pop(i, None)
            continue
        pot["pest_trigger_progress"] = _get_pest_trigger_progress(pot, flower_id)
        pot["pest_triggered"] = bool(pot.get("pest_triggered", False))
        pot["pest_active"] = bool(pot.get("pest_active", False))
        pot["pest_resolved"] = bool(pot.get("pest_resolved", False))
        if pot["pest_active"]:
            pot["pest_triggered"] = True
        if pot["pest_resolved"]:
            pot["pest_active"] = False
        if pot.get("pest_time") is not None:
            if not pot["pest_resolved"]:
                if pot["pest_trigger_progress"] is None:
                    current_progress = min(grow_time, max(0.0, float(pot.get("growth_progress", 0.0))))
                    pot["pest_trigger_progress"] = current_progress
                pot["pest_triggered"] = True
                pot["pest_active"] = True
            pot.pop("pest_time", None)
            data.get("pest_treatment", {}).pop(i, None)


def normalize_state(data, now=None):
    normalized = _BASE_NORMALIZE_STATE(data, now=now)
    if now is None:
        now = int(time.time())
    _normalize_v5_pests(normalized, now)
    refresh_garden_events(normalized, now)
    return normalized


def refresh_garden_events(state, now=None):
    if now is None:
        now = int(time.time())
    weather_id = state.get("weather", "sunny")
    if weather_id not in WEATHER:
        weather_id = "sunny"
    pest_pots = []
    for idx, pot in enumerate(state.get("pots", [])):
        if _has_pest_blocker(state, idx, pot):
            pest_pots.append(idx + 1)
    rainbow_until = _safe_nonnegative_int(state.get("rainbow_until", 0), 0)
    butterfly_until = _safe_nonnegative_int(state.get("butterfly_until", 0), 0)
    existing = state.get("garden_events")
    if not isinstance(existing, dict):
        existing = {}
    garden_events = dict(existing)
    garden_events.update(
        {
            "weather": weather_id,
            "has_pests": bool(pest_pots),
            "pest_pots": pest_pots,
            "rainbow_active": rainbow_until > now,
            "rainbow_until": rainbow_until,
            "rainbow_reward": _garden_event_reward_text(state.get("last_rainbow_reward")),
            "butterfly_active": butterfly_until > now,
            "butterfly_until": butterfly_until,
            "butterfly_reward": _garden_event_reward_text(state.get("last_butterfly_reward")),
            "updated_at": now,
        }
    )
    state["garden_events"] = garden_events
    return garden_events


def update_flower_growth(state, now, weather_data):
    for pot_idx, pot in enumerate(state.get("pots", [])):
        if pot is None or is_pot_withered(pot):
            continue
        if _has_pest_blocker(state, pot_idx, pot):
            if pot.get("pest_time") is not None:
                _activate_pest(state, pot_idx, now)
            pot["last_growth_update"] = now
            continue
        if not pot.get("watered", True):
            continue
        try:
            last_update = int(pot.get("last_growth_update", now))
        except (TypeError, ValueError):
            last_update = now
        elapsed = max(0, now - last_update)
        if elapsed <= 0:
            pot["last_growth_update"] = now
            continue
        flower_id = pot["flower_id"]
        grow_time = float(FLOWERS[flower_id]["grow_time"])
        progress = min(grow_time, max(0.0, float(pot.get("growth_progress", 0.0))))
        speed = get_actual_grow_speed(pot, weather_data)
        if speed <= 0:
            pot["last_growth_update"] = now
            continue
        projected = min(grow_time, progress + (elapsed * speed))
        trigger_progress = _get_pest_trigger_progress(pot, flower_id)
        if (
            trigger_progress is not None
            and not pot.get("pest_triggered", False)
            and not pot.get("pest_resolved", False)
            and progress < trigger_progress <= projected
        ):
            pot["growth_progress"] = trigger_progress
            _activate_pest(state, pot_idx, now)
            continue
        pot["growth_progress"] = projected
        pot["last_growth_update"] = now


def check_pests(state, now):
    messages = []
    state["last_pest_check_time"] = now
    for pot_idx, pot in enumerate(state.get("pots", [])):
        if not isinstance(pot, dict) or is_pot_withered(pot):
            continue
        if pot.get("pest_time") is not None and not pot.get("pest_active", False):
            before_active = bool(pot.get("pest_active", False))
            if _activate_pest(state, pot_idx, now) and not before_active:
                messages.append(f"\n🐛 盆{pot_idx + 1}的{FLOWERS[pot['flower_id']]['name']}长虫了，需要先治疗。")
        elif pot.get("pest_active", False):
            pot["last_growth_update"] = now
    refresh_garden_events(state, now)
    return messages


def _harvest_one_pot(state, pot_idx, now, weather_data):
    return _harvest_one_pot_result(state, pot_idx, now, weather_data).message


def _harvest_one_pot_result(state, pot_idx, now, weather_data, *, event_source="system") -> CommandResult:
    pot = state["pots"][pot_idx] if 0 <= pot_idx < len(state["pots"]) else None
    blocker = get_pot_harvest_blocker(state, pot_idx, pot)
    if blocker == "invalid_index":
        return CommandResult(False, f"❌ 盆号必须是1-{state['max_pots']}")
    if blocker == "empty":
        return CommandResult(False, "❌ 这个盆是空的")
    if blocker == "withered":
        return CommandResult(False, f"❌ 这盆花已经枯萎，请使用 clear {pot_idx + 1} 清理")
    if blocker == "pest":
        return CommandResult(False, "❌ 花有虫害，先治疗后才能收获")
    if blocker == "unknown_flower":
        return CommandResult(False, "❌ 这盆没有可收获的花")
    flower_id = pot["flower_id"]
    flower_data = FLOWERS[flower_id]
    grow_time = flower_data["grow_time"]
    progress = float(pot.get("growth_progress", 0.0))
    encyclopedia_before = list(state["encyclopedia"])
    harvest_total_before = get_total_flower_harvests(state)
    if blocker == "growing":
        if not pot.get("watered", True):
            return CommandResult(False, "❌ 这盆花还没浇水，生长暂停")
        speed = weather_data["grow_speed"]
        remaining = (grow_time - progress) / speed
        return CommandResult(False, f"❌ 还没成熟，还需约{format_time(remaining)}")
    state["inventory"]["flowers"][flower_id] = state["inventory"]["flowers"].get(flower_id, 0) + 1
    harvest_counts = state.setdefault("flower_harvest_counts", {})
    harvest_counts[flower_id] = int(harvest_counts.get(flower_id, 0) or 0) + 1
    harvest_total_after = get_total_flower_harvests(state)
    state["pots"][pot_idx] = None
    state["pest_treatment"].pop(pot_idx, None)
    if flower_id in state["encyclopedia"]:
        result = f"🌸 收获了{flower_data['name']}！"
        reward = {}
    else:
        state["encyclopedia"].append(flower_id)
        result = (
            f"🎉 收获{flower_data['name']}！图鉴+1！\n"
            f"✨ 新发现！{flower_data['name']}已加入图鉴 ({len(state['encyclopedia'])}/{len(FLOWERS)})"
        )
        reward = ENCYCLOPEDIA_REWARDS.get(flower_id, {})
    add_event(state, f"收获了{flower_data['name']}", now=now, source=event_source, area="garden")
    reward_text = []
    before_count = len(encyclopedia_before)
    after_count = len(state["encyclopedia"])
    if reward:
        if "money" in reward:
            state["money"] += int(reward["money"])
            reward_text.append(f"获得{reward['money']}块")
        for seed_id, qty in reward.get("seeds", {}).items():
            state["inventory"]["seeds"][seed_id] = (
                state["inventory"]["seeds"].get(seed_id, 0) + qty
            )
            reward_text.append(f"{FLOWERS[seed_id]['name']}种子x{qty}")
        for item_id, qty in reward.get("items", {}).items():
            _add_inventory_item(state, item_id, qty)
            reward_text.append(f"{ITEMS[item_id]['name']}x{qty}")
    if reward_text:
        result += "\n🎁 解锁奖励：" + ", ".join(reward_text)
    cottage_rewards = sync_cottage_rewards(state, now, record_events=True)
    if cottage_rewards:
        result += "\n🏠 小屋获得纪念物：" + "、".join(
            COTTAGE_ITEM_CATALOG[item_id]["name"] for item_id in cottage_rewards
        )
    newly_unlocked = get_stage_unlocks(
        before_count,
        after_count,
        encyclopedia_before,
        harvest_total_before,
        harvest_total_after,
    )
    if newly_unlocked:
        result += "\n🔁 商店新解锁：" + "、".join(newly_unlocked)
    return CommandResult(True, result)


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
