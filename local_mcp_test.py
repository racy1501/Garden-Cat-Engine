"""本地开发 / 发布前黑盒测试专用的 stdio MCP 壳。

仅转发现有 HTTP API，不复制游戏规则，不读取游戏实现或数据库；不用于正式部署。

先启动 game_api.py，并通过本地网页创建花园。客户端配置环境变量：
GARDEN_API_BASE_URL（默认 http://127.0.0.1:8080）、GARDEN_API_KEY、
GARDEN_SESSION_ID。依赖见 requirements-local-mcp.txt。
"""

import json
import os
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError


mcp = FastMCP("Garden local API test")
HTTP_TIMEOUT_SECONDS = 10


def _session_id() -> str:
    value = os.environ.get("GARDEN_SESSION_ID", "").strip()
    if not value:
        raise ToolError("未配置 GARDEN_SESSION_ID；请先从本地网页取得花园编号。")
    return value


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    authenticated: bool = True,
) -> dict[str, Any]:
    base = os.environ.get("GARDEN_API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    url = base + path + ("?" + urlencode(params) if params else "")
    headers = {"Accept": "application/json"}
    if authenticated:
        headers["X-API-Key"] = os.environ.get("GARDEN_API_KEY", "")
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    try:
        request = Request(url, data=data, headers=headers, method=method)
        with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            raw = response.read()
    except HTTPError as exc:
        with exc:
            try:
                payload = json.loads(exc.read())
            except (ValueError, OSError):
                payload = {}
        detail = (payload.get("message") or payload.get("error")) if isinstance(payload, dict) else None
        reason = {
            401: "API 密钥认证失败，请检查 GARDEN_API_KEY",
            403: "API 拒绝此操作",
            400: "API 参数无效，请检查 session_id 和请求参数",
            404: "API 未找到资源，请检查 session_id 和本地 API 地址",
        }.get(exc.code, "API 请求失败")
        suffix = f"；{str(detail)[:300]}" if detail else ""
        raise ToolError(f"HTTP {exc.code}：{reason}{suffix}") from None
    except (URLError, OSError):
        raise ToolError("无法连接本地 API 或请求超时；请确认 game_api 已启动且地址正确。") from None
    except ValueError:
        raise ToolError("API 地址或请求头无效，请检查 GARDEN_API_BASE_URL 和配置。") from None
    try:
        payload = json.loads(raw)
    except ValueError:
        raise ToolError("API 返回非 JSON 响应，请检查本地 API 地址。") from None
    if not isinstance(payload, dict):
        raise ToolError("API 返回的 JSON 不是对象，请检查本地 API 地址。")
    return payload


@mcp.tool()
def garden_reference(kind: Literal["info", "catalog", "help"]) -> dict[str, Any]:
    """读取游戏介绍、正式商品目录或命令帮助。"""
    if kind not in ("info", "catalog", "help"):
        raise ToolError("kind 只能是 info、catalog 或 help。")
    return _request("GET", f"/api/{kind}", authenticated=kind == "help")


@mcp.tool()
def garden_status() -> dict[str, Any]:
    """读取并结算配置中的现有花园状态。"""
    return _request("GET", "/api/status", params={"session_id": _session_id()})


@mcp.tool()
def garden_command(command: str) -> dict[str, Any]:
    """原样执行游戏命令，保留 API 的 ok、message 和公开结果。"""
    if not command.strip():
        raise ToolError("command 不能为空。")
    return _request("POST", "/api/cmd", params={"compact": "1"},
                    body={"session_id": _session_id(), "command": command})


@mcp.tool()
def garden_notes(
    action: Literal["read", "write"], page: int | None = None, content: str | None = None,
) -> dict[str, Any]:
    """读取或写入共享便签；read 可带页码，write 必须带内容，业务限制由 API 判断。"""
    if action == "read":
        if content is not None or (page is not None and (type(page) is not int or page < 1)):
            raise ToolError("读取便签只接受正整数 page，不接受 content。")
        params: dict[str, Any] = {"session_id": _session_id()}
        if page is not None:
            params["page"] = page
        return _request("GET", "/api/notes", params=params)
    if action == "write":
        if page is not None or content is None or not content.strip():
            raise ToolError("写便签需要非空 content，不接受 page。")
        return _request("POST", "/api/notes", body={"session_id": _session_id(), "content": content})
    raise ToolError("action 只能是 read 或 write。")


if __name__ == "__main__":
    mcp.run(transport="stdio")
