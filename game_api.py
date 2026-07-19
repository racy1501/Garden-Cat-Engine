"""
"game": "花园与猫咪 v4.9.8 🌸" - Flask REST API + 可视化网页
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
    get_cat_max_affection,
    get_collectible_boost_hint,
    get_collectible_status_text,
    get_collectible_unlock_hint,
    get_game_time_info,
    get_next_pot_cost,
    is_collectible_unlocked,
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


APP_VERSION = "v4.9.8"
app = Flask(__name__)

API_KEY = os.environ.get("GARDEN_API_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SQLITE_PATH = os.environ.get("SQLITE_PATH", "garden_cat.db")
DEFAULT_SESSION = "default"
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,60}$")
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
WEB_TOKEN_FIELD = "_web_token_hash"
NOTE_MAX_CHARS = 20
NOTE_COOLDOWN_SECONDS = 2 * 60 * 60
NOTE_PAGE_SIZE = 10
NOTE_AUTHOR_TYPES = {"human", "ai"}


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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS garden_notes (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    author_type TEXT NOT NULL CHECK (author_type IN ('human', 'ai')),
                    content TEXT NOT NULL,
                    created_at BIGINT NOT NULL
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
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS garden_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    author_type TEXT NOT NULL CHECK (author_type IN ('human', 'ai')),
                    content TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_garden_notes_timeline "
            "ON garden_notes (session_id, created_at DESC, id DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_garden_notes_cooldown "
            "ON garden_notes (session_id, author_type, created_at DESC, id DESC)"
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
            cur.execute("DELETE FROM garden_notes WHERE session_id = %s", (session_id,))
            cur.execute("DELETE FROM garden_saves WHERE session_id = %s", (session_id,))
        else:
            cur.execute("DELETE FROM garden_notes WHERE session_id = ?", (session_id,))
            cur.execute("DELETE FROM garden_saves WHERE session_id = ?", (session_id,))
        deleted = cur.rowcount
        conn.commit()
    return deleted > 0


def _normalize_note_content(value: Any) -> str:
    """Normalize a note into one short line; validation is based on Unicode characters."""
    return " ".join(str(value or "").split())


def _note_iso_time(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def _note_row_to_dict(row: Any) -> dict[str, Any]:
    timestamp = int(row["created_at"])
    return {
        "id": int(row["id"]),
        "author_type": str(row["author_type"]),
        "content": str(row["content"]),
        "created_at": timestamp,
        "created_at_iso": _note_iso_time(timestamp),
    }


def db_list_notes(
    session_id: str,
    author_type: str,
    page: int = 1,
    page_size: int = NOTE_PAGE_SIZE,
    now: int | None = None,
) -> dict[str, Any]:
    """Return one page of append-only notes, newest first."""
    ensure_schema()
    if author_type not in NOTE_AUTHOR_TYPES:
        raise ValueError("invalid note author type")
    if now is None:
        now = int(time.time())
    page = max(1, int(page or 1))
    page_size = max(1, min(50, int(page_size or NOTE_PAGE_SIZE)))
    offset = (page - 1) * page_size

    with _get_conn() as conn:
        if USE_POSTGRES:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT COUNT(*) AS total FROM garden_notes WHERE session_id = %s",
                    (session_id,),
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    """
                    SELECT id, author_type, content, created_at
                    FROM garden_notes
                    WHERE session_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (session_id, page_size, offset),
                )
                rows = cur.fetchall()
                cur.execute(
                    """
                    SELECT created_at
                    FROM garden_notes
                    WHERE session_id = %s AND author_type = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    (session_id, author_type),
                )
                latest = cur.fetchone()
        else:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) AS total FROM garden_notes WHERE session_id = ?",
                (session_id,),
            )
            total = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT id, author_type, content, created_at
                FROM garden_notes
                WHERE session_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (session_id, page_size, offset),
            )
            rows = cur.fetchall()
            cur.execute(
                """
                SELECT created_at
                FROM garden_notes
                WHERE session_id = ? AND author_type = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (session_id, author_type),
            )
            latest = cur.fetchone()

    last_written_at = int(latest["created_at"]) if latest else 0
    cooldown_remaining = max(0, last_written_at + NOTE_COOLDOWN_SECONDS - now)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "notes": [_note_row_to_dict(row) for row in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "can_write": cooldown_remaining == 0,
        "cooldown_remaining_seconds": cooldown_remaining,
        "max_chars": NOTE_MAX_CHARS,
        "cooldown_seconds": NOTE_COOLDOWN_SECONDS,
    }


def db_add_note(
    session_id: str,
    author_type: str,
    content: Any,
    now: int | None = None,
) -> tuple[dict[str, Any] | None, int, str | None]:
    """Append a note. Returns (note, cooldown_remaining, validation_error)."""
    ensure_schema()
    if author_type not in NOTE_AUTHOR_TYPES:
        return None, 0, "发送身份无效。"
    normalized = _normalize_note_content(content)
    if not normalized:
        return None, 0, "便签不能为空。"
    if len(normalized) > NOTE_MAX_CHARS:
        return None, 0, f"便签最多 {NOTE_MAX_CHARS} 个字符。"
    if now is None:
        now = int(time.time())

    with _get_conn() as conn:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(
                """
                SELECT created_at
                FROM garden_notes
                WHERE session_id = %s AND author_type = %s
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (session_id, author_type),
            )
        else:
            cur.execute(
                """
                SELECT created_at
                FROM garden_notes
                WHERE session_id = ? AND author_type = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (session_id, author_type),
            )
        latest = cur.fetchone()
        if latest:
            last_written_at = int(latest[0])
            remaining = max(0, last_written_at + NOTE_COOLDOWN_SECONDS - now)
            if remaining > 0:
                return None, remaining, None

        if USE_POSTGRES:
            cur.execute(
                """
                INSERT INTO garden_notes (session_id, author_type, content, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (session_id, author_type, normalized, now),
            )
            note_id = int(cur.fetchone()[0])
        else:
            cur.execute(
                """
                INSERT INTO garden_notes (session_id, author_type, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, author_type, normalized, now),
            )
            note_id = int(cur.lastrowid)
        conn.commit()

    note = {
        "id": note_id,
        "author_type": author_type,
        "content": normalized,
        "created_at": now,
        "created_at_iso": _note_iso_time(now),
    }
    return note, NOTE_COOLDOWN_SECONDS, None


def _parse_positive_page(value: Any) -> int | None:
    try:
        page = int(value)
    except (TypeError, ValueError):
        return None
    return page if page > 0 else None


def _format_note_duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes = (remainder + 59) // 60
    if hours and minutes:
        return f"{hours}小时{minutes}分钟"
    if hours:
        return f"{hours}小时"
    return f"{max(1, minutes)}分钟"


def _format_notes_for_command(payload: dict[str, Any]) -> str:
    notes = payload["notes"]
    if not notes:
        lines = ["📝 花园便签", "  还没有人留下便签。"]
    else:
        lines = [
            f"📝 花园便签（第{payload['page']}/{payload['total_pages']}页，共{payload['total']}条）"
        ]
        for note in notes:
            sender = "AI" if note["author_type"] == "ai" else "人类"
            stamp = datetime.fromtimestamp(note["created_at"], tz=timezone.utc).strftime(
                "%Y-%m-%d %H:%M UTC"
            )
            lines.append(f"  [{sender}] {note['content']} · {stamp}")
    if payload["cooldown_remaining_seconds"] > 0:
        lines.append(
            "\n你的下一张便签还需等待："
            + _format_note_duration(payload["cooldown_remaining_seconds"])
        )
    else:
        lines.append("\n你现在可以写一张新便签。")
    return "\n".join(lines)


def _handle_note_command(
    session_id: str,
    command: str,
    author_type: str,
) -> str | None:
    """Handle note commands at the API layer so the game engine stays independent."""
    stripped = command.strip()
    lowered = stripped.lower()

    page_text: str | None = None
    if lowered == "notes" or stripped == "查看便签":
        page_text = "1"
    elif lowered.startswith("notes "):
        page_text = stripped[6:].strip()
    elif stripped.startswith("查看便签 "):
        page_text = stripped[5:].strip()

    if page_text is not None:
        page = _parse_positive_page(page_text)
        if page is None:
            return "❌ 用法：notes [页码]"
        return _format_notes_for_command(
            db_list_notes(session_id, author_type, page=page)
        )

    content: str | None = None
    if lowered.startswith("note "):
        content = stripped[5:]
    elif stripped.startswith("写便签 "):
        content = stripped[4:]
    elif lowered == "note" or stripped == "写便签":
        content = ""

    if content is None:
        return None

    note, remaining, error = db_add_note(session_id, author_type, content)
    if error:
        return f"❌ {error}"
    if note is None:
        return "❌ 便签冷却中，还需等待" + _format_note_duration(remaining) + "。"
    return f"📝 便签已贴好：{note['content']}"


NOTE_HELP_TEXT = (
    "\n\n【共享便签】\n"
    "notes [页码] - 查看共享便签，最新在前\n"
    "note <内容> - 写一张1-20字便签（AI与人类各自冷却2小时）"
)


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

    collectibles = state.get("collectibles", {})
    collectible_first_found = state.get("collectible_first_found", {})
    collectible_catalog = []
    rarity_names = {"common": "普通", "uncommon": "少见", "rare": "珍贵"}
    for item in CAT_COLLECTIBLES:
        count = int(collectibles.get(item["id"], 0) or 0)
        owned = count > 0
        unlocked = is_collectible_unlocked(state, item)
        collectible_catalog.append(
            {
                **item,
                "display_name": item["name"] if owned else "未知的小东西",
                "rarity_name": rarity_names.get(item.get("rarity", ""), ""),
                "description": item.get("description", "") if owned else "",
                "owned": owned,
                "count": count,
                "unlocked": unlocked,
                "unlock_hint": get_collectible_unlock_hint(item),
                "status_text": get_collectible_status_text(state, item),
                "boost_hint": get_collectible_boost_hint(item),
                "first_found_at": int(collectible_first_found.get(item["id"], 0) or 0),
            }
        )

    received_letter_indexes = set(state.get("letters_received", []))
    letter_catalog = [
        {
            "index": index + 1,
            "title": letter["title"] if index in received_letter_indexes else "未收到",
            "received": index in received_letter_indexes,
            "text": letter["text"] if index in received_letter_indexes else "",
        }
        for index, letter in enumerate(CAT_LETTERS)
    ]

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
            "max_affection": round(get_cat_max_affection(state), 1),
            "permanent_items": state.get("permanent_items", []),
            "letters_received": len(received_letter_indexes),
            "letters_capacity": len(CAT_LETTERS),
            "collectibles_count": sum(1 for count in collectibles.values() if int(count or 0) > 0),
            "collectibles_total_found": sum(int(count or 0) for count in collectibles.values()),
            "collectibles_capacity": len(CAT_COLLECTIBLES),
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
        "collectibles": collectibles,
        "collectibles_count": sum(1 for count in collectibles.values() if int(count or 0) > 0),
        "collectibles_total_found": sum(int(count or 0) for count in collectibles.values()),
        "collectibles_capacity": len(CAT_COLLECTIBLES),
        "collectible_catalog": collectible_catalog,
        "letters_received": state.get("letters_received", []),
        "letters_capacity": len(CAT_LETTERS),
        "letters": [
            {
                "index": idx + 1,
                "title": CAT_LETTERS[idx]["title"],
                "text": CAT_LETTERS[idx]["text"],
            }
            for idx in state.get("letters_received", [])
            if isinstance(idx, int) and 0 <= idx < len(CAT_LETTERS)
        ],
        "letter_catalog": letter_catalog,
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
            "description": "一个同时支持 AI 接口与人类可视化网页的养成游戏。绑定后，AI 与人类可在同一 session_id 下共享花园与便签。",
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
                "notes [页码]         - 查看共享便签，最新在前",
                "note 内容            - 写一张1-20字便签（AI端冷却2小时）",
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
                "📝 AI与人类可在同一花园共享便签，各自独立冷却2小时",
            ],
            "endpoints": {
                f"GET  {base}/info": "游戏说明（无需密钥）",
                f"POST {base}/register": "注册独立花园",
                f"POST {base}/cmd": "执行游戏命令",
                f"GET  {base}/status?session_id=xxx": "查看并结算状态",
                f"GET  {base}/state?session_id=xxx": "获取完整 JSON 存档",
                f"POST {base}/new_game": "重置指定存档（慎用）",
                f"GET/POST {base}/notes": "AI查看或写共享便签",
                f"GET/POST {request.host_url.rstrip('/')}/web/notes": "人类网页查看或写共享便签",
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
            "collectibles": [
                {
                    **item,
                    "rarity_name": {
                        "common": "普通",
                        "uncommon": "少见",
                        "rare": "珍贵",
                    }.get(item.get("rarity", ""), ""),
                    "unlock_hint": get_collectible_unlock_hint(item),
                    "boost_hint": get_collectible_boost_hint(item),
                }
                for item in CAT_COLLECTIBLES
            ],
            "collectibles_capacity": len(CAT_COLLECTIBLES),
            "letters_capacity": len(CAT_LETTERS),
            "notes": {
                "max_chars": NOTE_MAX_CHARS,
                "cooldown_seconds": NOTE_COOLDOWN_SECONDS,
                "page_size": NOTE_PAGE_SIZE,
            },
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
    result = _handle_note_command(session_id, command, "human")
    if result is None:
        result = process_command(state, command)
        if command.strip().lower() == "help":
            result += NOTE_HELP_TEXT
        db_save_state(session_id, state)
    return jsonify(
        {
            "ok": not result.lstrip().startswith("❌"),
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/web/notes", methods=["GET", "POST"])
def web_notes():
    data = (request.get_json(silent=True) or {}) if request.method == "POST" else {}
    session_id = _safe_session_id(
        data.get("session_id", "") if request.method == "POST" else request.args.get("session_id", "")
    )
    token = request.headers.get("X-Garden-Token", "")
    state = _load_authorized_web_state(session_id, token)
    if state is None:
        return _web_auth_error()

    if request.method == "POST":
        note, remaining, error = db_add_note(session_id, "human", data.get("content", ""))
        if error:
            return jsonify({"ok": False, "message": error}), 400
        if note is None:
            return jsonify(
                {
                    "ok": False,
                    "message": "便签冷却中，请稍后再写。",
                    "cooldown_remaining_seconds": remaining,
                }
            ), 429
        payload = db_list_notes(session_id, "human", page=1)
        return jsonify({"ok": True, "message": "便签已经贴好了。", "note": note, **payload})

    page = _parse_positive_page(request.args.get("page", 1))
    if page is None:
        return jsonify({"ok": False, "message": "页码必须是正整数。"}), 400
    return jsonify({"ok": True, **db_list_notes(session_id, "human", page=page)})


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
    result = _handle_note_command(session_id, command, "ai")
    if result is None:
        result = process_command(state, command)
        if command.strip().lower() == "help":
            result += NOTE_HELP_TEXT
        db_save_state(session_id, state)
    return jsonify(
        {
            "ok": not result.lstrip().startswith("❌"),
            "session_id": session_id,
            "message": result,
            "state": _summary(state),
        }
    )


@app.route("/api/notes", methods=["GET", "POST"])
@require_api_key
def api_notes():
    data = (request.get_json(silent=True) or {}) if request.method == "POST" else {}
    session_id = _safe_session_id(
        data.get("session_id", DEFAULT_SESSION)
        if request.method == "POST"
        else request.args.get("session_id", DEFAULT_SESSION)
    )
    _get_or_create_state(session_id)

    if request.method == "POST":
        note, remaining, error = db_add_note(session_id, "ai", data.get("content", ""))
        if error:
            return jsonify({"ok": False, "message": f"❌ {error}"}), 400
        if note is None:
            return jsonify(
                {
                    "ok": False,
                    "message": "❌ 便签冷却中，请稍后再写。",
                    "cooldown_remaining_seconds": remaining,
                }
            ), 429
        payload = db_list_notes(session_id, "ai", page=1)
        return jsonify({"ok": True, "message": "📝 便签已贴好。", "note": note, **payload})

    page = _parse_positive_page(request.args.get("page", 1))
    if page is None:
        return jsonify({"ok": False, "message": "❌ 页码必须是正整数。"}), 400
    return jsonify({"ok": True, **db_list_notes(session_id, "ai", page=page)})


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
    result = process_command(state, "help") + NOTE_HELP_TEXT
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
