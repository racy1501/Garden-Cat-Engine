# 🌸 花园与猫咪 v4.8.1 API

这是从原 Replit 项目整理出的多存档版本。每个 AI 通过 `/api/register` 获得独立 `session_id`，之后使用该 ID 继续自己的花园。

## 文件说明

- `game_engine.py`：v4.8.1 完整游戏规则
- `game_api.py`：Flask API、注册、独立存档与数据库读写
- `schema.sql`：PostgreSQL 建表语句
- `pyproject.toml` / `requirements.txt`：Python 依赖
- `.env.example`：环境变量示例
- `main.py`：兼容部分平台的启动入口
- `tests/`：核心逻辑与 API 测试

## 本地运行

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
pip install -r requirements.txt
set GARDEN_API_KEY=请替换成自己的密钥
python game_api.py
```

启动后打开：

```text
http://127.0.0.1:8080/api/info
```

未设置 `DATABASE_URL` 时会使用本地 `garden_cat.db`，关闭程序后存档仍保留。

## 云端数据库

正式部署时设置：

- `GARDEN_API_KEY`：访问密钥
- `DATABASE_URL`：PostgreSQL 连接地址
- `PORT`：通常由平台自动提供

程序启动时会自动创建 `garden_saves` 表，不会覆盖已有存档。

> 云端若不配置 PostgreSQL，只使用 SQLite，则必须选择带持久磁盘的平台，否则重新部署后数据库文件可能消失。

## 启动命令

```bash
gunicorn game_api:app
```

## API 快速示例

注册：

```http
POST /api/register
X-API-Key: <密钥>
Content-Type: application/json

{"name": "小恰花园"}
```

执行命令：

```http
POST /api/cmd
X-API-Key: <密钥>
Content-Type: application/json

{"session_id": "sess_xxxxxxxxxxxx", "command": "status"}
```

完整玩法可访问 `/api/info` 或执行 `help`。
