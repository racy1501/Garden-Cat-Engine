# 🌸 花园与猫咪 v4.8.10

一个同时面向 **AI 玩家** 与 **人类玩家** 的多存档养成游戏。

- AI 继续通过 REST API 注册、读取状态和执行文字命令。
- 人类打开网站首页，即可通过可视化按钮种花、浇水、收获、插花和照顾猫咪。
- 每个 AI 或人类玩家默认拥有独立花园，不会互相串档。
- 云端使用 PostgreSQL 保存；本地开发自动使用 SQLite。

## v4.8.10 新增

- 天气生长倍率调整为：晴天 ×1.1、雨天 ×1.2、 多云 ×1.0
- 雨天继续自动浇水，并在花盆上显示当前生长倍率
- 网页天气卡新增游戏天数、时段和具体时间
- 已浇水花盆按钮灰显；雨天显示“雨水滋润中”
- 水碗和猫窝未解锁时以灰色状态展示
- 摸猫冷却期间按钮灰显并显示倒计时
- “花园存档码”改名为更明确的“花园存档码”
- 金币图标改为内置 SVG，避免部分系统无法显示 emoji

## v4.8.3 新增

- AI 可使用 `adopt <名字>` 在收养时为猫咪取名
- 新增 `rename_cat <名字>`，收养后可随时改名
- 人类网页收养与改名时会弹出名字输入框
- 猫咪名字最长12个字符；旧存档继续兼容
- 网页收藏页新增可展开阅读的猫咪信箱

## v4.8.2 新增

- 新增可视化网页首页 `/`
- 新增花盆、花瓶、商店、背包、图鉴和猫咪互动界面
- 浏览器自动保存人类玩家的专属花园存档码
- 支持复制、导入花园存档码，在其他设备继续同一座花园
- 网页不暴露全局 `GARDEN_API_KEY`
- AI API 保持原有调用方式，不受网页功能影响

## 两种入口

### 人类玩家

直接打开网站根地址：

```text
https://你的域名/
```

首次进入时创建花园。服务器会生成：

- `session_id`：花园编号
- `garden_token`：这座花园自己的钥匙

两者默认保存在浏览器 `localStorage`。建议点击页面右上角“花园存档码”，另行复制备份。

### AI 玩家

完整说明：

```text
GET /api/info
```

注册：

```http
POST /api/register
X-API-Key: <全局密钥>
Content-Type: application/json

{"name": "小恰花园"}
```

执行命令：

```http
POST /api/cmd
X-API-Key: <全局密钥>
Content-Type: application/json

{"session_id": "sess_xxxxxxxxxxxx", "command": "status"}
```

AI 与人类默认分别注册自己的 `session_id`，因此各自拥有独立花园。

猫咪取名示例：

```text
adopt 栗子
rename_cat 橘子
```

## 项目结构

```text
game_engine.py       游戏规则与状态结算
game_api.py          Flask、API、网页路由与数据库读写
templates/index.html 可视化网页结构
static/style.css     网页样式
static/app.js        网页交互与 API 调用
schema.sql           PostgreSQL 建表参考
tests/               游戏、API 与网页入口测试
```

## 环境变量

正式部署需要：

- `GARDEN_API_KEY`：AI API 使用的全局密钥
- `DATABASE_URL`：PostgreSQL 连接地址
- `PORT`：通常由 Render 自动提供

人类网页不会读取或展示 `GARDEN_API_KEY`。

## Render 部署

Build Command：

```bash
pip install -r requirements.txt
```

Start Command：

```bash
gunicorn game_api:app
```

把新版文件上传到原 GitHub 仓库后，Render 会自动重新部署。Neon 数据库独立存在，普通代码更新不会清空已有存档。

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

然后打开：

```text
http://127.0.0.1:8080/
```

未配置 `DATABASE_URL` 时，会在项目目录生成本地 `garden_cat.db`。

## 测试

```bash
pytest -q
```

当前包含游戏逻辑、AI API、多花园隔离、网页鉴权与可视化首页测试。

## 天气倍率

| 天气 | 生长倍率 | 浇水 |
|---|---:|---|
| ☀️ 晴天 | ×1.1 | 需要手动浇水 |
| 🌧️ 下雨 | ×1.2 | 自动浇水 |
| ☁️ 多云 | ×1.0 | 需要手动浇水 |
