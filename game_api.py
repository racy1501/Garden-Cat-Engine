"""
花园与猫咪 v4.8.10 - Flask REST API + 可视化网页
双入口多存档版：AI 使用 REST API，人类使用可视化网页；支持 PostgreSQL 持久化。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Iterator

from flask import Flask, jsonify, render_template, request

from game_engine import (
    CAT_COLLECTIBLES,
    CAT_LETTERS,
    FLOWERS,
    FLOWER_UNLOCK_REQUIREMENTS,
    ITEMS,
    MAX_POTS,
    POT_UNLOCK_COSTS,
    VASE_CAPACITY,
    WEATHER,
    get_actual_grow_speed,
    get_game_time_info,
    get_next_pot_cost,
    PET_COOLDOWN_REAL_MINUTES,
    get_default_state,
    get_vase_flower_status,
    is_flower_unlocked,
    is_pot_withered,
    normalize_state,
    process_command,
)

try:
    import psycopg2
    import psycopg2.extras
except ImportError:  # 本地仅使用 SQLite 时允许不安装 PostgreSQL 驱动
    psycopg2 = None


APP_VERSION = "v4.8.10"
app = Flask(__name__)

API_KEY = os.environ.get("GARDEN_API_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SQLITE_PATH = os.environ.get("SQLITE_PATH", "garden_cat.db")
DEFAULT_SESSION = "default"
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,60}$")
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
WEB_TOKEN_FIELD = "_web_token_hash"


# ─── 数据库 ───────────────────────────────────────────────────────────────────

@contextmanager
def _get_conn() -> Iterator[Any]:
    """获取数据库连接。云端优先 PostgreSQL，本地默认 SQLite。"""
    if USE_POSTGRES:
        if psycopg2 is None:
            raise RuntimeError("检测到 DATABASE_URL，但未安装 psycopg2-binary")
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def ensure_schema() -> None:
    """创建存档表；重复执行不会覆盖已有数据。"""
    with _get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS garden_saves (
                    session_id TEXT PRIMARY KEY,
                    state JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS garden_saves (
                    session_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        conn.commit()


def _decode_state(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
    return dict(value) if hasattr(value, "items") else None


def db_load_state(session_id: str) -> dict[str, Any] | None:
    ensure_schema()
    with _get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT state FROM garden_saves WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute(
                "SELECT state FROM garden_saves WHERE session_id = ?",
                (session_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    state = _decode_state(row["state"])
    return normalize_state(state) if state is not None else None


def db_save_state(session_id: str, state: dict[str, Any]) -> None:
    ensure_schema()
    normalize_state(state)
    state["last_update"] = int(time.time())
    payload = json.dumps(state, ensure_ascii=False)
    with _get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """
                INSERT INTO garden_saves (session_id, state, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET state = EXCLUDED.state, updated_at = NOW()
                """,
                (session_id, payload),
            )
        else:
            updated_at = datetime.now(timezone.utc).isoformat()
            cur.execute(
                """
                INSERT INTO garden_saves (session_id, state, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id)
                DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at
                """,
                (session_id, payload, updated_at),
            )
        conn.commit()


def db_list_sessions() -> list[dict[str, Any]]:
    ensure_schema()
    with _get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT session_id, state, updated_at FROM garden_saves ORDER BY updated_at DESC"
                )
                rows = cur.fetchall()
        else:
            cur = conn.cursor()
            cur.execute(
                "SELECT session_id, state, updated_at FROM garden_saves ORDER BY updated_at DESC"
            )
            rows = cur.fetchall()

    result = []
    for row in rows:
        state = _decode_state(row["state"]) or {}
        updated_at = row["updated_at"]
        if hasattr(updated_at, "isoformat"):
            updated_at = updated_at.isoformat()
        result.append(
            {
                "session_id": row["session_id"],
                "garden_name": state.get("garden_name", ""),
                "money": state.get("money", 0),
                "has_cat": state.get("cat") is not None,
                "encyclopedia": len(state.get("encyclopedia", [])),
                "updated_at": updated_at,
            }
        )
    return result


def db_count_sessions() -> int:
    ensure_schema()
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM garden_saves")
        return int(cur.fetchone()[0])


def db_delete_session(session_id: str) -> bool:
    ensure_schema()
    with _get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("DELETE FROM garden_saves WHERE session_id = %s", (session_id,))
        else:
            cur.execute("DELETE FROM garden_saves WHERE session_id = ?", (session_id,))
        deleted = cur.rowcount
        conn.commit()
    return deleted > 0


def _new_state(name: str = "") -> dict[str, Any]:
    state = get_default_state()
    state["inventory"]["items"]["basic_food"] = 3
    if name:
        state["garden_name"] = name[:30]
    return state


def _get_or_create_state(session_id: str) -> dict[str, Any]:
    state = db_load_state(session_id)
    if state is None:
        state = _new_state()
        db_save_state(session_id, state)
    return state


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _safe_session_id(sid: Any) -> str:
    if not sid:
        return DEFAULT_SESSION
    sid = str(sid).strip()
    if SESSION_ID_RE.fullmatch(sid):
        return sid
    clean = re.sub(r"[^A-Za-z0-9_\-]", "_", sid)[:60]
    return clean or DEFAULT_SESSION


def _hash_web_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_web_token(state: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    state[WEB_TOKEN_FIELD] = _hash_web_token(token)
    return token


def _load_authorized_web_state(session_id: str, token: str) -> dict[str, Any] | None:
    if not session_id or not token:
        return None
    state = db_load_state(session_id)
    if state is None:
        return None
    expected = str(state.get(WEB_TOKEN_FIELD, ""))
    if not expected or not hmac.compare_digest(expected, _hash_web_token(token)):
        return None
    return state


def _web_auth_error():
    return jsonify({"ok": False, "message": "花园钥匙无效，请重新创建或导入花园钥匙。"}), 401


def _daypart_label(hour: int) -> str:
    if 5 <= hour < 8:
        return "清晨"
    if 8 <= hour < 12:
        return "上午"
    if 12 <= hour < 14:
        return "中午"
    if 14 <= hour < 18:
        return "下午"
    if 18 <= hour < 21:
        return "傍晚"
    return "夜晚"


def _summary(state: dict[str, Any]) -> dict[str, Any]:
    """给网页或其他 AI 返回易用的结构化状态摘要。"""
    now = int(time.time())
    normalize_state(state, now)
    weather_id = state.get("weather", "sunny")
    weather = WEATHER.get(weather_id, WEATHER["sunny"])
    game_day, game_hour, game_minute = get_game_time_info(state)

    pots = []
    for index, pot in enumerate(state.get("pots", [])):
        slot = index + 1
        if pot is None:
            pots.append({"slot": slot, "status": "empty"})
            continue

        flower_id = pot["flower_id"]
        flower = FLOWERS[flower_id]
        if is_pot_withered(pot):
            pots.append(
                {
                    "slot": slot,
                    "status": "withered",
                    "flower": flower_id,
                    "flower_name": flower["name"],
                    "clear_command": f"clear {slot}",
                }
            )
            continue

        progress = min(float(pot.get("growth_progress", 0.0)), flower["grow_time"])
        progress_pct = min(100, int(progress / flower["grow_time"] * 100))
        speed = get_actual_grow_speed(pot, weather)
        remaining = None
        if progress < flower["grow_time"] and speed > 0:
            remaining = max(0, int((flower["grow_time"] - progress) / speed))

        pots.append(
            {
                "slot": slot,
                "status": "ready" if progress >= flower["grow_time"] else "growing",
                "flower": flower_id,
                "flower_name": flower["name"],
                "progress_pct": progress_pct,
                "ready": progress >= flower["grow_time"],
                "watered": bool(pot.get("watered", True)),
                "remaining_seconds": remaining,
                "has_pest": "pest_time" in pot and now < int(pot["pest_time"]),
                "pest_deadline": pot.get("pest_time"),
                "grow_speed": round(speed, 2),
            }
        )

    vase = []
    for position, entry in enumerate(state.get("vase", []), start=1):
        label, wither_pct, remaining = get_vase_flower_status(entry, now)
        flower_id = entry["flower_id"]
        vase.append(
            {
                "position": position,
                "flower": flower_id,
                "flower_name": FLOWERS[flower_id]["name"],
                "freshness_label": label,
                "wither_pct": wither_pct,
                "remaining_seconds": remaining,
            }
        )

    cat_summary = None
    if state.get("cat") and state.get("cat_stats"):
        stats = state["cat_stats"]
        pet_ready_at = int(state.get("cat_last_pet_real_time", 0)) + PET_COOLDOWN_REAL_MINUTES * 60
        pet_cooldown_remaining = max(0, pet_ready_at - now)
        cat_summary = {
            "name": state["cat"].get("name", "小猫"),
            "hunger": round(stats["hunger"], 1),
            "thirst": round(stats["thirst"], 1),
            "mood": round(stats["mood"], 1),
            "affection": round(stats["affection"], 1),
            "permanent_items": state.get("permanent_items", []),
            "letters_received": len(state.get("letters_received", [])),
            "collectibles_count": sum(state.get("collectibles", {}).values()),
            "pet_cooldown_remaining_seconds": pet_cooldown_remaining,
        }

    return {
        "garden_name": state.get("garden_name", ""),
        "money": state.get("money", 0),
        "weather": weather_id,
        "weather_emoji": weather.get("emoji", ""),
        "weather_name": weather.get("name", ""),
        "weather_grow_speed": weather.get("grow_speed", 1.0),
        "game_day": game_day,
        "game_hour": game_hour,
        "game_minute": game_minute,
        "daypart": _daypart_label(game_hour),
        "encyclopedia_count": len(state.get("encyclopedia", [])),
        "encyclopedia": state.get("encyclopedia", []),
        "unlocked_flowers": [fid for fid in FLOWERS if is_flower_unlocked(state, fid)],
        "total_earned": state.get("total_earned", 0),
        "max_pots": state.get("max_pots", len(pots)),
        "pot_capacity": MAX_POTS,
        "next_pot_cost": get_next_pot_cost(state),
        "permanent_items": state.get("permanent_items", []),
        "pots": pots,
        "vase": {"capacity": VASE_CAPACITY, "flowers": vase},
        "inventory": {
            "seeds": state.get("inventory", {}).get("seeds", {}),
            "flowers": state.get("inventory", {}).get("flowers", {}),
            "items": state.get("inventory", {}).get("items", {}),
        },
        "has_cat": state.get("cat") is not None,
        "cat": cat_summary,
        "collectibles": state.get("collectibles", {}),
        "letters_received": state.get("letters_received", []),
        "letters": [
            {"index": idx + 1, "text": CAT_LETTERS[idx]["text"]}
            for idx in state.get("letters_received", [])
            if isinstance(idx, int) and 0 <= idx < len(CAT_LETTERS)
        ],
        "recent_events": [event.get("text", "") for event in state.get("events", [])[-5:]],
    }


# ─── 鉴权 ─────────────────────────────────────────────────────────────────────

def require_api_key(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        # 本地未设置密钥时允许调试；正式部署请务必设置 GARDEN_API_KEY。
        if API_KEY and request.headers.get("X-API-Key", "") != API_KEY:
            return jsonify(
                {"ok": False, "message": "❌ 无效的 API Key，请在请求头加上 X-API-Key"}
            ), 401
        return func(*args, **kwargs)

    return decorated


# ─── 路由 ─────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", app_version=APP_VERSION)


@app.route("/api/healthz", methods=["GET"])
def health():
    try:
        ensure_schema()
        database = "postgresql" if USE_POSTGRES else "sqlite"
        return jsonify({"status": "ok", "game": f"花园与猫咪 {APP_VERSION}", "database": database})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/info", methods=["GET"])
def info():
    """公开接口。AI 可先阅读此页，再注册自己的独立花园。"""
    base = request.host_url.rstrip("/") + "/api"
    try:
        garden_count = db_count_sessions()
    except Exception:
        garden_count = 0

    return jsonify(
        {
            "game": f"花园与猫咪 {APP_VERSION} 🌸",
            "welcome": (
                "欢迎来到花园世界。\n"
                "在这里，每个 AI 都可以拥有一座独立保存的小花园：\n"
                "种下喜欢的花，布置花瓶，攒钱收养猫咪，慢慢留下自己的生活痕迹。"
            ),
            "world": f"🌍 目前共有 {garden_count} 个花园在这个世界里",
            "description": "一个同时支持 AI 接口与人类可视化网页的养成游戏。每个 session_id 都对应独立花园。",
            "how_to_start": [
                "第一步：注册并获得专属 session_id（只需一次）",
                f"  POST {base}/register",
                "  Header: X-API-Key: <密钥>",
                '  可选 Body: {"name": "花园名字"}',
                "",
                "第二步：保存返回的 session_id，之后每次操作都带上它",
                f"  POST {base}/cmd",
                "  Header: X-API-Key: <密钥>",
                '  Body: {"command": "status", "session_id": "你的ID"}',
                "",
                "也可以直接查看状态：",
                f"  GET {base}/status?session_id=你的ID",
            ],
            "quick_start_commands": [
                "help                 - 查看所有命令",
                "shop                 - 查看商店与解锁条件",
                "buy daisy 2          - 买2包雏菊种子",
                "plant daisy 1        - 在1号盆种雏菊",
                "water 1              - 给1号盆浇水",
                "harvest 1            - 收获指定花盆",
                "harvest all          - 一键收获全部成熟花朵",
                "arrange daisy        - 把已收获的雏菊插入花瓶",
                "vase                 - 查看花瓶",
                "sell all             - 卖掉背包里的全部鲜花",
                "adopt [名字]         - 花100块收养猫咪，可同时取名",
                "rename_cat 名字       - 给猫咪改名",
                "status               - 查看完整花园状态",
            ],
            "features": [
                "🌱 未浇水的花暂停生长，雨天自动浇水",
                "🌸 稀有花随图鉴进度分层解锁",
                "💐 花瓶最多插3朵花，保鲜约12小时",
                "🐛 害虫每5分钟最多检查一次；枯萎花需手动清理",
                "🐱 猫咪拥有饱食、口渴、心情与亲密度",
                "✉️ 猫咪信件与随机收集品",
                "🖱️ 人类可通过首页按钮操作自己的独立花园",
                "💾 每个 session_id 对应一份独立数据库存档",
            ],
            "endpoints": {
                f"GET  {base}/info": "游戏说明（无需密钥）",
                f"POST {base}/register": "注册独立花园",
                f"POST {base}/cmd": "执行游戏命令",
                f"GET  {base}/status?session_id=xxx": "查看并结算状态",
                f"GET  {base}/state?session_id=xxx": "获取完整 JSON 存档",
                f"POST {base}/new_game": "重置指定存档（慎用）",
                f"GET  {request.host_url.rstrip('/')}/": "人类玩家可视化网页",
            },
        }
    )


@app.route("/api/catalog", methods=["GET"])
def catalog():
    rarity_names = {
        "common": "普通",
        "uncommon": "稀有",
        "rare": "珍贵",
        "legendary": "传说",
    }
    return jsonify(
        {
            "ok": True,
            "version": APP_VERSION,
            "flowers": {
                flower_id: {
                    **flower,
                    "unlock_requirement": FLOWER_UNLOCK_REQUIREMENTS.get(flower_id, 0),
                    "rarity_name": rarity_names.get(flower.get("rarity", ""), ""),
                }
                for flower_id, flower in FLOWERS.items()
            },
            "items": ITEMS,
            "vase_capacity": VASE_CAPACITY,
            "max_pots": MAX_POTS,
            "pot_unlock_costs": POT_UNLOCK_COSTS,
        }
    )


# ─── 人类网页入口：使用每座花园自己的钥匙，不暴露全局 API Key ───────────────

@app.route("/web/register", methods=["POST"])
def web_register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:30]
    session_id = "web_" + uuid.uuid4().hex[:16]
    state = _new_state(name or "我的小花园")
    state["owner_type"] = "human"
    token = _issue_web_token(state)
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "garden_token": token,
            "message": "🌱 新花园已经准备好了。花园钥匙已保存在当前浏览器。",
            "state": _summary(state),
        }
    )


@app.route("/web/status", methods=["GET"])
def web_status():
    session_id = _safe_session_id(request.args.get("session_id", ""))
    token = request.headers.get("X-Garden-Token", "")
    state = _load_authorized_web_state(session_id, token)
    if state is None:
        return _web_auth_error()
    result = process_command(state, "status")
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/web/cmd", methods=["POST"])
def web_cmd():
    data = request.get_json(silent=True) or {}
    command = str(data.get("command", "")).strip()
    session_id = _safe_session_id(data.get("session_id", ""))
    token = request.headers.get("X-Garden-Token", "")
    if not command:
        return jsonify({"ok": False, "message": "请选择一个操作。"}), 400
    state = _load_authorized_web_state(session_id, token)
    if state is None:
        return _web_auth_error()
    result = process_command(state, command)
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": not result.lstrip().startswith("❌"),
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/web/new_game", methods=["POST"])
def web_new_game():
    data = request.get_json(silent=True) or {}
    session_id = _safe_session_id(data.get("session_id", ""))
    token = request.headers.get("X-Garden-Token", "")
    old_state = _load_authorized_web_state(session_id, token)
    if old_state is None:
        return _web_auth_error()
    name = str(data.get("name") or old_state.get("garden_name") or "我的小花园").strip()[:30]
    state = _new_state(name)
    state["owner_type"] = "human"
    state[WEB_TOKEN_FIELD] = old_state[WEB_TOKEN_FIELD]
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "message": "🌱 花园已经重新开始。",
            "state": _summary(state),
        }
    )


@app.route("/api/register", methods=["POST"])
@require_api_key
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()[:30]
    session_id = "sess_" + uuid.uuid4().hex[:12]
    state = _new_state(name)
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "message": (
                f"你的专属花园 ID：{session_id}\n"
                "请保存好这个 ID，之后每次回来都需要带上它。\n\n"
                "初始状态：50块钱 · 3个花盆 · 3包普通猫粮\n"
                "发送 help 查看玩法，发送 shop 购买第一批种子。\n\n"
                "🌱 花盆已经摆好，泥土还是新的。"
            ),
            "state": _summary(state),
        }
    )


@app.route("/api/new_game", methods=["POST"])
@require_api_key
def new_game():
    data = request.get_json(silent=True) or {}
    session_id = _safe_session_id(data.get("session_id", DEFAULT_SESSION))
    name = str(data.get("name", "")).strip()[:30]
    state = _new_state(name)
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "message": f"🌱 [{session_id}] 新游戏开始！你有50块钱、3个花盆和3包普通猫粮。",
            "state": _summary(state),
        }
    )


@app.route("/api/cmd", methods=["POST"])
@require_api_key
def cmd_route():
    data = request.get_json(silent=True) or {}
    command = str(data.get("command", "")).strip()
    session_id = _safe_session_id(data.get("session_id", DEFAULT_SESSION))
    if not command:
        return jsonify({"ok": False, "message": "❌ 请在请求体中提供 command 字段"}), 400

    state = _get_or_create_state(session_id)
    result = process_command(state, command)
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": not result.lstrip().startswith("❌"),
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/api/status", methods=["GET"])
@require_api_key
def status():
    session_id = _safe_session_id(request.args.get("session_id", DEFAULT_SESSION))
    state = _get_or_create_state(session_id)
    result = process_command(state, "status")
    db_save_state(session_id, state)
    return jsonify(
        {
            "ok": True,
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/api/help", methods=["GET"])
@require_api_key
def help_route():
    state = _new_state()
    result = process_command(state, "help")
    return jsonify({"ok": True, "message": result})


@app.route("/api/state", methods=["GET"])
@require_api_key
def raw_state():
    session_id = _safe_session_id(request.args.get("session_id", DEFAULT_SESSION))
    state = _get_or_create_state(session_id)
    return jsonify({"ok": True, "session_id": session_id, "state": state})


@app.route("/api/sessions", methods=["GET"])
@require_api_key
def list_sessions():
    sessions = db_list_sessions()
    return jsonify({"ok": True, "count": len(sessions), "sessions": sessions})


@app.route("/api/delete_session", methods=["POST"])
@require_api_key
def delete_session():
    data = request.get_json(silent=True) or {}
    session_id = _safe_session_id(data.get("session_id", ""))
    if not session_id or session_id == DEFAULT_SESSION:
        return jsonify({"ok": False, "message": "❌ 不能删除默认存档"}), 400
    if db_delete_session(session_id):
        return jsonify({"ok": True, "message": f"✅ 已删除存档 [{session_id}]"})
    return jsonify({"ok": False, "message": f"❌ 存档 [{session_id}] 不存在"}), 404


# ─── 启动 ─────────────────────────────────────────────────────────────────────

ensure_schema()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    storage = "PostgreSQL" if USE_POSTGRES else f"SQLite ({SQLITE_PATH})"
    print(f"🌸 花园与猫咪 {APP_VERSION} API 启动在端口 {port}，存储：{storage}")
    app.run(host="0.0.0.0", port=port, debug=False)
