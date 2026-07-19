# 🌸 花园与猫咪 v4.9.8b

一个同时支持 **AI 接口** 与 **人类可视化网页** 的治愈系养成小游戏。

## v4.9.8b 更新

- 修复真实网页意外回到宽版布局的问题，恢复 920px 固定窄版
- “一键收花 / 便签”恢复到花园、商店按钮右侧，不再漂到整行最右边
- 花盆内生长花苞与成熟花统一显示尺寸
- 花卉图鉴恢复宽弹窗与大图标四列卡片
- 静态资源增加版本参数，减少部署后浏览器继续读取旧样式

- 新增 AI 与人类共享的「花园便签」
- 每条便签 1～20 个字符，自动整理为单行
- AI 端与人类端分别拥有 2 小时写入冷却，互不影响
- 历史便签长期保存在独立数据库表中，最新在前，每页 10 条
- 便签为追加式记录，不提供修改或单条删除
- 人类网页在「一键收花」旁新增「便签」按钮，弹窗中可查看、翻页和留言
- AI 可继续使用原有 `/api/cmd`，通过 `notes [页码]` 查看、`note 内容` 写入
- 同步新版固定窄版网页、16 件猫咪收集品和 12 封猫咪信件展示
- **摸猫冷却仍为现实时间 10 分钟，没有改动**
- 兼容 v4.9.1 及更早存档

## 共享便签如何识别双方

花园服务不额外建立第二套绑定系统。

集合 MCP 完成「人类账号 ↔ AI 账号」绑定后，应让双方访问同一个花园 `session_id`：

- AI/MCP 从 `/api/...` 入口访问，服务端自动记为 `ai`
- 人类网页从 `/web/...` 入口访问，服务端自动记为 `human`
- 客户端不提交 `sender`，不能自行伪装身份

便签按 `session_id` 汇入同一条时间线。两端的冷却按发送方分别计算。

## 两种入口

### 人类玩家

直接打开网站根地址：

```text
https://你的域名/
```

首次进入时创建花园。服务器会生成：

- `session_id`：花园编号
- `garden_token`：这座花园的人类网页钥匙

两者默认保存在浏览器 `localStorage`。请使用页面中的「花园存档码」另行备份。

### AI / MCP

完整说明：

```http
GET /api/info
```

注册：

```http
POST /api/register
X-API-Key: <全局密钥>
Content-Type: application/json

{"name": "小恰花园"}
```

执行普通游戏命令：

```http
POST /api/cmd
X-API-Key: <全局密钥>
Content-Type: application/json

{"session_id": "sess_xxxxxxxxxxxx", "command": "status"}
```

### AI 便签命令

```text
notes       查看第 1 页
notes 2     查看第 2 页
note 今天的薄荷开花了
```

也可直接调用：

```http
GET /api/notes?session_id=你的ID&page=1
X-API-Key: <全局密钥>
```

```http
POST /api/notes
X-API-Key: <全局密钥>
Content-Type: application/json

{"session_id": "你的ID", "content": "今天的薄荷开花了"}
```

## 便签规则

- 内容长度：1～20 个 Unicode 字符
- 冷却：AI 2 小时、人类 2 小时，各自计时
- 排序：最新到最旧
- 分页：每页 10 条
- 保存：独立 `garden_notes` 表，不塞进主存档 JSON
- 修改：不支持
- 单条删除：不支持
- 重开花园：便签保留
- 删除整个 session：便签随整座花园一并清理

## 项目结构

```text
game_engine.py       游戏规则与状态结算
game_api.py          Flask、API、网页路由、存档与便签数据库读写
templates/index.html 可视化网页结构
static/style.css     网页样式
static/app.js        网页交互与 API 调用
schema.sql           PostgreSQL 建表参考
tests/               游戏、API、网页与便签测试
```

## 环境变量

正式部署需要：

- `GARDEN_API_KEY`：AI API 使用的全局密钥
- `DATABASE_URL`：PostgreSQL 连接地址
- `PORT`：通常由 Render 自动提供

人类网页不会读取或展示 `GARDEN_API_KEY`。

## Render 部署

Build Command：

```text
pip install -r requirements.txt
```

Start Command：

```text
gunicorn game_api:app
```

把新版文件上传到原 GitHub 仓库后，Render 会自动重新部署。Neon 数据库独立存在，普通代码更新不会清空已有花园存档；程序启动时会自动创建新的 `garden_notes` 表。

## 本地运行

```bash
python -m venv .venv
```

Windows：

```bat
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

## 关键时间规则

- 摸猫冷却：现实 10 分钟
- 便签冷却：AI 与人类各自现实 2 小时
- 花瓶保鲜：现实约 12 小时
- 害虫检查：现实 5 分钟最多检查一次

## About

花园与猫咪 v4.9.8b｜AI与人类共享便签的治愈系养成小游戏
