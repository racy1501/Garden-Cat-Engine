"""
花园与猫咪 v4.9.9 - API与网页兼容游戏引擎
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
from datetime import datetime, timedelta, timezone

# 游戏数据
FLOWERS = {
    "daisy": {"name": "雏菊", "rarity": "common", "seed_price": 3, "sell_price": 4, "grow_time": 120},
    "tulip": {"name": "郁金香", "rarity": "common", "seed_price": 4, "sell_price": 5, "grow_time": 180},
    "pansy": {"name": "三色堇", "rarity": "common", "seed_price": 5, "sell_price": 7, "grow_time": 240},
    "sunflower": {"name": "向日葵", "rarity": "common", "seed_price": 6, "sell_price": 8, "grow_time": 300},
    "rose": {"name": "玫瑰", "rarity": "common", "seed_price": 8, "sell_price": 11, "grow_time": 360},
    "lavender": {"name": "薰衣草", "rarity": "uncommon", "seed_price": 10, "sell_price": 13, "grow_time": 420},
    "hydrangea": {"name": "绣球花", "rarity": "uncommon", "seed_price": 12, "sell_price": 16, "grow_time": 480},
    "lily": {"name": "百合", "rarity": "uncommon", "seed_price": 15, "sell_price": 19, "grow_time": 540},
    "iris": {"name": "鸢尾花", "rarity": "uncommon", "seed_price": 18, "sell_price": 23, "grow_time": 600},
    "cherry_blossom": {"name": "樱花", "rarity": "rare", "seed_price": 22, "sell_price": 28, "grow_time": 660},
    "peony": {"name": "牡丹", "rarity": "rare", "seed_price": 28, "sell_price": 35, "grow_time": 780},
    "moonflower": {"name": "月光花", "rarity": "legendary", "seed_price": 36, "sell_price": 44, "grow_time": 900},
}


# 图鉴数量和累计收获数达到要求后开放购买和种植；已收录过的花始终保持解锁，兼容旧存档。
FLOWER_UNLOCK_REQUIREMENTS = {
    "daisy": {"encyclopedia": 0, "harvests": 0},
    "tulip": {"encyclopedia": 0, "harvests": 0},
    "pansy": {"encyclopedia": 0, "harvests": 0},
    "sunflower": {"encyclopedia": 0, "harvests": 0},
    "rose": {"encyclopedia": 0, "harvests": 0},
    "lavender": {"encyclopedia": 4, "harvests": 8},
    "hydrangea": {"encyclopedia": 4, "harvests": 8},
    "lily": {"encyclopedia": 4, "harvests": 8},
    "iris": {"encyclopedia": 4, "harvests": 8},
    "cherry_blossom": {"encyclopedia": 8, "harvests": 20},
    "peony": {"encyclopedia": 8, "harvests": 20},
    "moonflower": {"encyclopedia": 11, "harvests": 36},
}

ENCYCLOPEDIA_REWARDS = {
    "daisy": {"seeds": {"daisy": 2}},
    "tulip": {"money": 3},
    "pansy": {"items": {"basic_food": 5}},
    "sunflower": {"money": 5},
    "rose": {"seeds": {"rose": 1}},
    "lavender": {"items": {"cat_treat": 2}},
    "hydrangea": {"money": 6},
    "lily": {"items": {"premium_food": 5}},
    "iris": {"seeds": {"iris": 1}},
    "cherry_blossom": {"items": {"ball": 1}},
    "peony": {"money": 10},
    "moonflower": {"items": {"feather_wand": 1}},
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
AFFECTION_NATURAL_DECAY = 0.5
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
        "unlock_affection": 10,
    },
    {
        "id": "faded_button",
        "name": "褪色纽扣",
        "emoji": "🔘",
        "rarity": "common",
        "description": "蓝色已经快看不出来了，边缘还有浅浅的牙印。",
        "unlock_affection": 10,
    },
    {
        "id": "gray_feather",
        "name": "灰白羽毛",
        "emoji": "🪶",
        "rarity": "common",
        "description": "插在猫窝边上时，会跟着风轻轻晃。",
        "unlock_affection": 10,
    },
    {
        "id": "maple_leaf",
        "name": "干枯的小树叶",
        "emoji": "🍂",
        "rarity": "common",
        "description": "叶脉很完整，像一张缩小的地图。",
        "unlock_affection": 10,
    },
    {
        "id": "bottle_cap",
        "name": "旧瓶盖",
        "emoji": "◉",
        "rarity": "common",
        "description": "猫咪一路踢回来的，发出了很响的声音。",
        "unlock_affection": 10,
    },
    {
        "id": "glass_marble",
        "name": "玻璃珠",
        "emoji": "🔮",
        "rarity": "common",
        "description": "对着太阳看，里面藏着一点绿色的光。",
        "unlock_affection": 30,
    },
    {
        "id": "red_yarn",
        "name": "红色毛线头",
        "emoji": "🧶",
        "rarity": "common",
        "description": "缠成了一个歪歪扭扭的小球。",
        "unlock_affection": 30,
    },
    {
        "id": "pine_needle",
        "name": "一小束松针",
        "emoji": "🌲",
        "rarity": "common",
        "description": "沾着一点泥土，闻起来像雨后的树林。",
        "unlock_affection": 30,
    },
    {
        "id": "wildflower",
        "name": "路边的小野花",
        "emoji": "🌼",
        "rarity": "common",
        "description": "花茎被压弯了一点，但猫咪把它完整带回来了。",
        "unlock_affection": 30,
    },
    {
        "id": "shell",
        "name": "完整的贝壳",
        "emoji": "🐚",
        "rarity": "uncommon",
        "description": "放在耳边，似乎还能听见很远的水声。",
        "unlock_affection": 30,
    },
    {
        "id": "silver_bell",
        "name": "银色铃铛",
        "emoji": "🔔",
        "rarity": "uncommon",
        "description": "已经不会响了，但猫咪还是很喜欢拨弄它。",
        "unlock_affection": 50,
    },
    {
        "id": "star_wrapper",
        "name": "星形糖纸",
        "emoji": "⭐",
        "rarity": "uncommon",
        "description": "阳光照上去时，会闪出彩色的光点。",
        "unlock_affection": 50,
    },
    {
        "id": "purple_ribbon",
        "name": "淡紫色丝带",
        "emoji": "🎀",
        "rarity": "uncommon",
        "description": "不知道从哪里捡来的，刚好可以系在花瓶上。",
        "unlock_affection": 50,
    },
    {
        "id": "clover",
        "name": "四叶草",
        "emoji": "🍀",
        "rarity": "uncommon",
        "description": "四片叶子都完完整整，像是猫咪认真挑过。",
        "unlock_affection": 50,
        "boost_hint": "猫咪心情很好时，出现概率会略微提高。",
    },
    {
        "id": "moonstone",
        "name": "月光石碎片",
        "emoji": "🌙",
        "rarity": "rare",
        "description": "夜里会泛起很淡的蓝光，像一小块凝固的月亮。",
        "unlock_affection": 75,
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
        "unlock_affection": 90,
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
    return [
        "✉️ 收到猫咪的一封信！",
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
            add_event(state, f"✉️ 收到猫咪第{next_idx + 1}封信")
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

    _set_cat_stat(state, "affection", stats.get("affection", 0.0) + amount_value)
    update_cat_max_affection(state)
    _advance_cat_commitment_phase(state, now)

    progress_gain = int(max(0.0, amount_value))
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


def is_collectible_unlocked(state, item):
    rarity = str(item.get("rarity", "common"))
    max_affection = get_cat_max_affection(state)
    if rarity == "common":
        return are_cat_collectibles_unlocked(state)
    if rarity in ("uncommon", "rare"):
        return max_affection >= 30
    return False


def get_collectible_unlock_hint(item):
    rarity = str(item.get("rarity", "common"))
    if rarity == "common":
        return "猫咪第一次实际吃饭或喝水后，完整来访或外出回家时可能带回。"
    return "曾达到历史最高亲密度30后，猫咪外出回家时可能带回。"


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
    if max_affection >= 30:
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
    add_event(state, f"🎁 {cat_name}带回了{collectible['emoji']}{collectible['name']}")
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
    return award_cat_collectible(state, collectible, now=now, source=source)


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


def settle_cat_lifecycle(state, target_time, letter_context=None):
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

            if location == CAT_LOCATION_AWAY and next_visit_at == next_transition_at:
                _ensure_cat_stats_for_lifecycle(state)
                stay_deadline_at = _safe_nonnegative_int(cat_state.get("stay_deadline_at", 0), 0)
                if stay_deadline_at > 0 and next_transition_at >= stay_deadline_at:
                    if _safe_nonnegative_int(cat_state.get("first_visit_at", 0), 0) <= 0:
                        cat_state["first_visit_at"] = next_transition_at
                    _enter_waiting_name_phase(state, next_transition_at)
                    cat_name = get_current_cat_name(state)
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。")
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
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}来了，正在花园里停留。")
                events.append(f"{cat_name}来了，正在花园里停留。")
                cat_state["last_lifecycle_settled_at"] = next_transition_at
                continue

            if location == CAT_LOCATION_GARDEN and current_visit_leave_at == next_transition_at:
                stay_deadline_at = _safe_nonnegative_int(cat_state.get("stay_deadline_at", 0), 0)
                max_affection = get_cat_max_affection(state)
                collectible_message = maybe_drop_cat_collectible(
                    state,
                    "visitor",
                    now=next_transition_at,
                    source="visit_complete",
                )
                if collectible_message:
                    events.append(collectible_message)
                if max_affection >= 30 or (stay_deadline_at > 0 and next_transition_at >= stay_deadline_at):
                    _enter_waiting_name_phase(state, next_transition_at)
                    cat_name = get_current_cat_name(state)
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。")
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
                    add_event(state, f"{cat_name}决定留下，正在等你正式取名。")
                    events.append(f"{cat_name}决定留下，正在等你正式取名。")
                    cat_state["last_lifecycle_settled_at"] = next_transition_at
                    continue
                if letter_context is None and letter_messages:
                    events.extend(letter_messages)
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}离开了花园，下次还会再来。")
                events.append(f"{cat_name}离开了花园，下次还会再来。")
                cat_state["last_lifecycle_settled_at"] = next_transition_at
                continue

        elif phase == CAT_PHASE_WAITING_NAME:
            _ensure_cat_stats_for_lifecycle(state)
            if location == CAT_LOCATION_AWAY:
                _set_cat_location(state, CAT_LOCATION_GARDEN, settled_at)
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
                _set_cat_location(state, CAT_LOCATION_AWAY, next_outing_at)
                cat_state["outing_return_at"] = next_outing_at + _roll_cat_outing_duration_seconds()
                cat_state["next_outing_at"] = 0
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}出门溜达了一会儿。")
                events.append(f"{cat_name}出门溜达了一会儿。")
                cat_state["last_lifecycle_settled_at"] = next_outing_at
                continue

            if location == CAT_LOCATION_AWAY:
                outing_return_at = _safe_nonnegative_int(cat_state.get("outing_return_at", 0), 0)
                if outing_return_at <= 0 or outing_return_at > target_time:
                    break
                _set_cat_location(state, CAT_LOCATION_HOME, outing_return_at)
                cat_state["outing_return_at"] = 0
                _schedule_next_adopted_outing(cat_state, outing_return_at)
                cat_name = get_current_cat_name(state)
                add_event(state, f"{cat_name}回家了。")
                events.append(f"{cat_name}回家了。")
                collectible_message = maybe_drop_cat_collectible(
                    state,
                    "adopted",
                    now=outing_return_at,
                    source="outing_return",
                )
                if collectible_message:
                    events.append(collectible_message)
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
        "last_active_at": now,
        "cat_last_pet": 0,
        "encyclopedia": [],
        "flower_harvest_counts": {},
        "total_earned": 0,
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
    add_event(state, "🌈 彩虹出现")


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
            add_event(state, f"天气变化：{WEATHER[old_weather]['name']} -> {new_weather_data['name']}")
        messages.append(
            f"\n🌤️ 天气变化：{WEATHER[old_weather]['emoji']}{WEATHER[old_weather]['name']} -> "
            f"{new_weather_data['emoji']}{new_weather_data['name']}"
        )
    if new_weather == "rainy":
        auto_watered = _auto_water_pots(state, now)
        if auto_watered > 0:
            messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花，它们开始生长了！")
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
        add_event(state, f"🦋 蝴蝶掉落了{gold}金币")


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
    elif phase == CAT_PHASE_ADOPTED and has_legacy_cat and location == CAT_LOCATION_AWAY:
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


def _record_cat_care_event(state, event_text, *, source=None):
    if source in {"offline_food", "offline_water"}:
        return
    add_event(state, event_text)


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
        _record_cat_care_event(state, f"{cat_name}吃了一份{food_name}。", source=source)
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
        _record_cat_care_event(state, f"{cat_name}喝了一份水。", source=source)
    return servings_drank, letter_messages


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


def normalize_state(data, now=None):
    """补齐旧存档字段，并修复 JSON 字典键类型。"""
    if now is None:
        now = int(time.time())
    if not isinstance(data, dict):
        return get_default_state()

    had_harvest_counts = "flower_harvest_counts" in data
    had_cat_state = isinstance(data.get("cat_state"), dict)
    had_last_active_at = "last_active_at" in data
    had_ai_v5_update_notice_seen = "ai_v5_update_notice_seen" in data
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
    data["events"] = data["events"][-5:]

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
    state["inventory"]["items"]["basic_food"] = 3
    save_game(state)
    return (
        "🌱 新游戏开始！你有50块钱，3盆花，3包普通猫粮。\n"
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


def is_flower_unlocked(state, flower_id):
    if flower_id not in FLOWERS:
        return False
    if flower_id in state.get("encyclopedia", []):
        return True
    requirement = get_flower_unlock_requirement(flower_id)
    encyclopedia_count = len(state.get("encyclopedia", []))
    harvest_total = sum(int(qty or 0) for qty in state.get("flower_harvest_counts", {}).values())
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


def get_stage_unlocks(before_count, after_count, encyclopedia_before):
    newly_unlocked = []
    known_before = set(encyclopedia_before)
    for flower_id in FLOWER_UNLOCK_REQUIREMENTS:
        requirement = get_flower_unlock_requirement(flower_id)
        if requirement["encyclopedia"] <= 0 or flower_id in known_before:
            continue
        if before_count < requirement["encyclopedia"] <= after_count:
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
            state["rainbow_until"] = now + GARDEN_EVENT_ACTIVE_SECONDS
            state["last_rainbow_reward"] = dict(reward)
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
            state["butterfly_until"] = now + GARDEN_EVENT_ACTIVE_SECONDS
            messages.append("🦋 一只蝴蝶飞过花园...")
            if random.random() < 0.30:
                gold = random.randint(3, 5)
                state["money"] += gold
                state["last_butterfly_reward"] = {"type": "money", "amount": gold}
                messages.append(f"   💰 蝴蝶掉落了{gold}块金币！")
                add_event(state, f"🦋 蝴蝶掉落了{gold}块金币")
            else:
                state["last_butterfly_reward"] = {"type": "text", "text": "just flew by"}
                add_event(state, "🦋 一只蝴蝶飞过花园")

    refresh_garden_events(state, now)
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

    lines.append(f"\n📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/12")
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
    thirst_decay = 5.0

    hunger_floor = min(CAT_PASSIVE_STAT_FLOOR, start_hunger)
    thirst_floor = min(CAT_PASSIVE_STAT_FLOOR, start_thirst)
    stats["hunger"] = max(hunger_floor, start_hunger - hunger_decay * hours)
    stats["thirst"] = max(thirst_floor, start_thirst - thirst_decay * hours)

    mood_decay = MOOD_BASE_DECAY
    if _is_premium_bed(state.get("cat_care", {}).get("bed")):
        mood_decay *= 0.6
    mood_hours = min(hours, MOOD_OFFLINE_CAP_REAL_HOURS)
    mood_change = (weather_data["cat_mood_change"] - mood_decay) * mood_hours
    mood_floor = min(CAT_PASSIVE_STAT_FLOOR, stats["mood"])
    stats["mood"] = min(100.0, max(mood_floor, stats["mood"] + mood_change))

    affection_loss = AFFECTION_NATURAL_DECAY * hours
    affection_floor = min(CAT_PASSIVE_STAT_FLOOR, stats["affection"])
    stats["affection"] = max(affection_floor, stats["affection"] - affection_loss)

    state["last_update"] = now


def _advance_offline_weather(state, now):
    weather_id = state.get("weather", "sunny")
    weather_data = WEATHER.get(weather_id, WEATHER["sunny"])
    if now >= state.get("weather_change_time", now):
        choices = [item for item in WEATHER if item != weather_id]
        if choices:
            weather_id = random.choice(choices)
            state["weather"] = weather_id
            weather_data = WEATHER[weather_id]
        state["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)
    if weather_data.get("auto_water"):
        _auto_water_pots(state, now)
    return weather_data


def _consume_offline_cat_portions(state):
    if not _is_cat_near_bowls(state):
        return 0, 0

    used_food, _ = _trigger_food_bowl_roll(state, source="offline_food")
    used_water, _ = _trigger_water_bowl_roll(state, source="offline_water")
    _sync_cat_stats_views(state)
    return used_food, used_water


def apply_offline_progress(state, now=None):
    if now is None:
        now = int(time.time())
    normalize_state(state, now)

    last_active_at = _safe_nonnegative_int(state.get("last_active_at", state.get("last_update", now)), now)
    elapsed = max(0, now - last_active_at)
    if elapsed <= 0:
        state["last_active_at"] = now
        return False

    settled_seconds = min(elapsed, OFFLINE_PROGRESS_MAX_SECONDS)
    skipped_seconds = max(0, elapsed - settled_seconds)
    settle_at = last_active_at + settled_seconds

    weather_data = _advance_offline_weather(state, settle_at)
    update_flower_growth(state, settle_at, weather_data)
    check_pests(state, settle_at)
    starting_mood = None
    if state.get("cat") is not None and isinstance(state.get("cat_stats"), dict):
        try:
            starting_mood = float(state["cat_stats"].get("mood", 0.0))
        except (TypeError, ValueError):
            starting_mood = 0.0
    update_cat_stats(state, settle_at, weather_data)
    if starting_mood is not None:
        state["cat_stats"]["mood"] = min(starting_mood, float(state["cat_stats"].get("mood", starting_mood)))
        _sync_cat_stats_views(state)
    settle_cat_lifecycle(state, settle_at)
    used_food, used_water = _consume_offline_cat_portions(state)

    for pot in state.get("pots", []):
        if isinstance(pot, dict) and not is_pot_withered(pot):
            pot["last_growth_update"] = now
    state["last_pest_check_time"] = now
    if state.get("weather_change_time", now) <= now:
        state["weather_change_time"] = now + random.randint(WEATHER_CHANGE_MIN, WEATHER_CHANGE_MAX)

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

    refresh_garden_events(state, now)
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
            messages.append(f"🌧️ 雨水滋润了{auto_watered}盆花，它们开始生长了！")
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


def apply_offline_progress(state, now=None):
    if now is None:
        now = int(time.time())
    normalize_state(state, now)

    last_active_at = _safe_nonnegative_int(state.get("last_active_at", state.get("last_update", now)), now)
    elapsed = max(0, now - last_active_at)
    if elapsed <= 0:
        state["last_active_at"] = now
        return False

    settled_seconds = min(elapsed, OFFLINE_PROGRESS_MAX_SECONDS)
    skipped_seconds = max(0, elapsed - settled_seconds)
    settle_at = last_active_at + settled_seconds

    weather_data = _advance_offline_weather(state, settle_at)
    update_flower_growth(state, settle_at, weather_data)
    check_pests(state, settle_at)
    starting_mood = None
    if state.get("cat") is not None and isinstance(state.get("cat_stats"), dict):
        try:
            starting_mood = float(state["cat_stats"].get("mood", 0.0))
        except (TypeError, ValueError):
            starting_mood = 0.0
    update_cat_stats(state, settle_at, weather_data)
    if starting_mood is not None:
        state["cat_stats"]["mood"] = min(starting_mood, float(state["cat_stats"].get("mood", starting_mood)))
        _sync_cat_stats_views(state)
    settle_cat_lifecycle(state, settle_at)
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

    refresh_garden_events(state, now)
    return True


def _summary(state):
    text = (
        f"📊 💰{state['money']} 🌸{len(state['encyclopedia'])}/12 "
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
    harvest_counts = state.setdefault("flower_harvest_counts", {})
    harvest_counts[flower_id] = int(harvest_counts.get(flower_id, 0) or 0) + 1
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
            _apply_facility_purchase(state, permanent_id)
            reward_text.append(ITEMS[permanent_id]["name"])
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
    if state.get("is_frozen"):
        state["is_frozen"] = False
        state["garden_frozen_until"] = 0
        state["frozen_reason"] = ""

    letter_context = {"messages": [], "remaining_deliveries": 1}

    # 先按旧天气结算到当前时刻，再允许天气在此刻变化，避免追溯修改过去。
    previous_weather_data = WEATHER[state["weather"]]
    update_flower_growth(state, now, previous_weather_data)
    update_cat_stats(state, now, previous_weather_data)
    weather_data, weather_messages = get_weather_info(state, now)
    pest_messages = check_pests(state, now)
    lifecycle_messages = settle_cat_lifecycle(state, now, letter_context=letter_context)

    result = ""
    all_event_messages = weather_messages + pest_messages + lifecycle_messages

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
        for item_id in SHOP_CAT_ITEM_IDS:
            item_data = ITEMS[item_id]
            result += f"  {item_data['name']} - {item_data['price']}块\n"

    elif action == "buy":
        if len(parts) < 2:
            result = "❌ 要买什么？"
        else:
            item_id = parts[1].lower()
            quantity = 1 if len(parts) < 3 else parse_positive_int(parts[2])
            if False:
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
                    elif _owns_facility(state, item_id):
                        result = f"❌ 已经有{item_data['name']}了"
                    elif state["money"] < item_data["price"]:
                        result = f"❌ 钱不够！需要{item_data['price']}块"
                    else:
                        state["money"] -= item_data["price"]
                        _apply_facility_purchase(state, item_id)
                        result = f"✅ 买了{item_data['name']}！永久生效 (-{item_data['price']}块)"
                else:
                    price = item_data["price"] * quantity
                    if state["money"] < price:
                        result = f"❌ 钱不够！需要{price}块"
                    else:
                        package_size = CAT_ITEM_PACKAGE_SIZES.get(item_id, 1)
                        total_portions = quantity * package_size
                        state["money"] -= price
                        _add_inventory_item(state, item_id, total_portions)
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
                    **_build_pest_plan(flower_id),
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
                if _has_pest_blocker(state, pot_idx, pot):
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
                elif not _has_pest_blocker(state, pot_idx, pot):
                    result = "❌ 这盆花没有长虫"
                elif state["money"] < PEST_TREATMENT_COST:
                    result = f"❌ 治疗需要{PEST_TREATMENT_COST}块，钱不够！"
                else:
                    state["money"] -= PEST_TREATMENT_COST
                    pot.pop("pest_time", None)
                    pot["pest_active"] = False
                    pot["pest_triggered"] = True
                    pot["pest_resolved"] = True
                    pot["last_growth_update"] = now
                    state["pest_treatment"].pop(pot_idx, None)
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
        requested_name = " ".join(parts[1:]) if len(parts) > 1 else ""
        cat_name = normalize_cat_name(requested_name, default=None)
        if cat_name is None:
            result = f"❌ 猫咪名字不能为空，且不能超过{CAT_NAME_MAX_LENGTH}个字符"
        elif _has_adopted_cat(state):
            result = "❌ 已经有猫了"
        elif state["cat"] is not None and state.get("cat_state", {}).get("phase") == CAT_PHASE_ADOPTED:
            result = "❌ 已经有猫了"
        elif not _can_finalize_adoption(state):
            result = "❌ 当前猫咪状态还不能正式收养"
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
            result = f"🎉 成功收养了{cat_name}！记得喂它哦~"

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
            food_type = CAT_CARE_FOOD_TYPES[parts[1].lower()]
            refill_result = _refill_food_bowl(
                state,
                food_type,
                now=now,
                source=f"feed:{food_type}",
                letter_context=letter_context,
            )
            if refill_result["space"] <= 0:
                result = "❌ 没有这种猫粮"
            else:
                result = f"🍽️ 喂了{ITEMS[food_type]['name']}！"

    elif action == "give_water":
        if len(parts) != 1:
            result = "❌ 用法：give_water"
        elif state["cat"] is None:
            result = "❌ 还没有猫"
        else:
            _refill_water_bowl(
                state,
                now=now,
                source="give_water",
                letter_context=letter_context,
            )
            result = "💧 给猫喝了水！"

    elif action == "refill_food":
        if len(parts) not in (2, 3) or parts[1].lower() not in CAT_CARE_FOOD_TYPES:
            result = "❌ 用法：refill_food <basic|premium> [份数]"
        elif state["cat"] is None:
            result = "鉂?杩樻病鏈夌尗"
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
                result = "❌ 粮碗已经满了"
            elif refill_result["added"] <= 0:
                result = f"❌ 背包里的{ITEMS[food_type]['name']}不够"
            elif refill_result["eaten"] > 0:
                cat_name = get_current_cat_name(state)
                result = (
                    f"✅ 已补满{ITEMS[food_type]['name']}，"
                    f"{cat_name}马上吃掉了1份，当前剩余 {bowl['remaining_portions']}/{bowl['capacity']}"
                )
            else:
                result = f"✅ 已向粮碗补充{refill_result['added']}份{ITEMS[food_type]['name']}"

    elif action == "refill_water":
        if len(parts) not in (1, 2):
            result = "❌ 用法：refill_water [份数]"
        elif state["cat"] is None:
            result = "鉂?杩樻病鏈夌尗"
        else:
            refill_result = _refill_water_bowl(
                state,
                now=now,
                source="refill_water",
                letter_context=letter_context,
            )
            bowl = state["cat_care"]["water_bowl"]
            if refill_result["space"] <= 0:
                result = "❌ 水碗已经满了"
            elif refill_result["drank"] > 0:
                cat_name = get_current_cat_name(state)
                result = (
                    f"✅ 已补满清水，"
                    f"{cat_name}马上喝掉了1份，当前剩余 {bowl['remaining_portions']}/{bowl['capacity']}"
                )
            else:
                result = f"✅ 已向水碗补充{refill_result['space']}份清水"

    elif action == "switch_food":
        if len(parts) != 2 or parts[1].lower() not in CAT_CARE_FOOD_TYPES:
            result = "❌ 用法：switch_food <basic|premium>"
        elif state["cat"] is None:
            result = "鉂?杩樻病鏈夌尗"
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
                result = f"❌ 背包里没有{ITEMS[food_type]['name']}，无法切换"
            else:
                state["cat_care"]["food_bowl"]["food_type"] = food_type
                result = f"✅ 当前猫粮已切换为{ITEMS[food_type]['name']}"

    elif action == "give_treat":
        if len(parts) != 1:
            result = "❌ 用法：give_treat"
        elif state["cat"] is None:
            result = "鉂?杩樻病鏈夌尗"
        elif state["inventory"]["items"].get(CAT_TREAT_ITEM_ID, 0) <= 0:
            result = "❌ 没有猫零食了"
        else:
            state["_interaction_accepted"] = _is_cat_present_for_interaction(state) and _roll_interaction_acceptance(state, "give_treat")
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
            result = "🍬 给猫咪喂了零食，心情和亲密都上升了一点"

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
                _change_cat_stat(state, "mood", 3)
                add_affection(
                    state,
                    1,
                    now=now,
                    source="pet",
                    letter_context=letter_context,
                )
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
                state["_interaction_accepted"] = _is_cat_present_for_interaction(state) and _roll_interaction_acceptance(state, toy_id)
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

            result = "\n".join(lines)

    elif action == "letters":
        if len(parts) != 1:
            result = "❌ 用法：letters"
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
            lines.append(f"\n进度：{len(state['encyclopedia'])}/12")
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
adopt [名字] - 正式收养猫咪并可选取名
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
  心情：基础衰减-0.5/小时，天气影响；单次离线最多结算前2小时
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
🎁 猫咪收集品：每5分钟最多检查一次；历史最高亲密度永久解锁阶段，允许随机重复
✉️ 猫咪写信：正向亲密按4点一批做50%判定，按亲密度顺序收12封信
🐛 害虫：每5分钟最多检查一次；成熟花不再长新虫，染虫后{PEST_DEATH_REAL_MINUTES}分钟内不治疗会枯萎
   枯萎花会留在花盆里，需使用 clear <盆号> 手动清理

💐 花瓶系统：
- 花瓶最多插{VASE_CAPACITY}朵已经收获的花
- 插花后不能再出售，可保持约{VASE_LIFESPAN_REAL_HOURS}小时
- vase 可查看新鲜程度与枯萎度
- 任意状态都可使用 remove_vase <位置> 移除，且不返还花朵或金币"""

    else:
        result = "❌ 未知命令，输入 help 查看帮助"

    update_cat_max_affection(state)

    if all_event_messages:
        result = "\n".join(all_event_messages) + "\n\n" + result
    if letter_context["messages"]:
        result = result + "\n" + "\n".join(letter_context["messages"])

    if action != "status" or result.startswith("❌"):
        result += "\n\n" + _summary(state)

    state["last_active_at"] = now
    return result


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
    add_event(state, f"盆{pot_idx + 1}出现虫害")
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
    if pot_idx < 0 or pot_idx >= state["max_pots"]:
        return f"❌ 盆号必须是1-{state['max_pots']}"
    pot = state["pots"][pot_idx]
    if pot is None:
        return "❌ 这个盆是空的"
    if is_pot_withered(pot):
        return f"❌ 这盆花已经枯萎，请使用 clear {pot_idx + 1} 清理"
    if _has_pest_blocker(state, pot_idx, pot):
        return "❌ 花有虫害，先治疗后才能收获"
    flower_id = pot["flower_id"]
    flower_data = FLOWERS[flower_id]
    grow_time = flower_data["grow_time"]
    progress = float(pot.get("growth_progress", 0.0))
    encyclopedia_before = list(state["encyclopedia"])
    if progress < grow_time:
        if not pot.get("watered", True):
            return "❌ 这盆花还没浇水，生长暂停"
        speed = weather_data["grow_speed"]
        remaining = (grow_time - progress) / speed
        return f"❌ 还没成熟，还需约{format_time(remaining)}"
    state["inventory"]["flowers"][flower_id] = state["inventory"]["flowers"].get(flower_id, 0) + 1
    harvest_counts = state.setdefault("flower_harvest_counts", {})
    harvest_counts[flower_id] = int(harvest_counts.get(flower_id, 0) or 0) + 1
    state["pots"][pot_idx] = None
    state["pest_treatment"].pop(pot_idx, None)
    if flower_id in state["encyclopedia"]:
        result = f"🌸 收获了{flower_data['name']}！"
    else:
        state["encyclopedia"].append(flower_id)
        result = (
            f"🎉 收获{flower_data['name']}！图鉴+1！\n"
            f"✨ 新发现！{flower_data['name']}已加入图鉴 ({len(state['encyclopedia'])}/12)"
        )
    add_event(state, f"收获了{flower_data['name']}")
    reward = flower_data.get("reward")
    reward_text = []
    before_count = len(encyclopedia_before)
    after_count = len(state["encyclopedia"])
    if reward:
        if "money" in reward:
            state["money"] += int(reward["money"])
            reward_text.append(f"获得{reward['money']}块")
        if "item" in reward:
            item_id = reward["item"]
            _add_inventory_item(state, item_id, int(reward.get("qty", 1) or 1))
            reward_text.append(f"{ITEMS[item_id]['name']}x{int(reward.get('qty', 1) or 1)}")
    if reward_text:
        result += "\n🎁 解锁奖励：" + ", ".join(reward_text)
    newly_unlocked = get_stage_unlocks(before_count, after_count, encyclopedia_before)
    if newly_unlocked:
        result += "\n🔁 商店新解锁：" + "、".join(newly_unlocked)
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
