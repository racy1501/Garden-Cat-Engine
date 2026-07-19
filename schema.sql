-- 花园与猫咪 v4.9.9 PostgreSQL 建表参考
-- 程序启动时 game_api.py 会自动执行同等的 CREATE TABLE IF NOT EXISTS。

CREATE TABLE IF NOT EXISTS garden_saves (
    session_id TEXT PRIMARY KEY,
    state JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI 与人类共用的追加式便签流。
-- 发送方由调用入口自动识别，不接受客户端伪造 sender 字段。
CREATE TABLE IF NOT EXISTS garden_notes (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    author_type TEXT NOT NULL CHECK (author_type IN ('human', 'ai')),
    content TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_garden_notes_timeline
    ON garden_notes (session_id, created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS idx_garden_notes_cooldown
    ON garden_notes (session_id, author_type, created_at DESC, id DESC);
