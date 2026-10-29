"""本地 MCP 转发契约测试；HTTP 全部 mock，不访问真实花园。"""

import asyncio
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

if importlib.util.find_spec("mcp") is None:
    raise unittest.SkipTest("本地 MCP 测试需先安装 requirements-local-mcp.txt")

import local_mcp_test as shell
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp.exceptions import ToolError


class ForwardingTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "GARDEN_API_BASE_URL": "http://127.0.0.1:18080/",
            "GARDEN_API_KEY": "mock-key", "GARDEN_SESSION_ID": "mock-session",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.http = patch.object(shell, "urlopen")
        self.urlopen = self.http.start()
        self.addCleanup(self.http.stop)
        self.payload = {"ok": True, "message": "mock API result", "state": {"public": True}}
        self.urlopen.side_effect = lambda *a, **kw: io.BytesIO(json.dumps(self.payload).encode())

    def assert_request(self, method, endpoint, *, query=None, body=None, auth=True):
        request = self.urlopen.call_args.args[0]
        self.assertEqual(self.urlopen.call_args.kwargs["timeout"], 10)
        self.assertEqual(request.get_method(), method)
        url = urlsplit(request.full_url)
        self.assertEqual(url.netloc, "127.0.0.1:18080")
        self.assertEqual(url.path, endpoint)
        self.assertEqual(parse_qs(url.query), query or {})
        self.assertEqual(json.loads(request.data) if request.data else None, body)
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(headers.get("x-api-key"), "mock-key" if auth else None)
        if body is not None:
            self.assertEqual(headers["content-type"], "application/json")

    def test_reference_routes_and_auth(self):
        for kind in ("info", "catalog", "help"):
            with self.subTest(kind=kind):
                self.assertEqual(shell.garden_reference(kind), self.payload)
                self.assert_request("GET", f"/api/{kind}", auth=kind == "help")

    def test_status_uses_configured_session(self):
        self.assertEqual(shell.garden_status(), self.payload)
        self.assert_request("GET", "/api/status", query={"session_id": ["mock-session"]})

    def test_command_preserves_business_failure_and_original_command(self):
        self.payload = {"ok": False, "message": "材料不足", "state": {"money": 5}}
        command = "  craft_bouquet bouquet_id=first_meeting  "
        self.assertEqual(shell.garden_command(command), self.payload)
        self.assert_request("POST", "/api/cmd", query={"compact": ["1"]},
                            body={"session_id": "mock-session", "command": command})

    def test_notes_read_write(self):
        shell.garden_notes("read", page=2)
        self.assert_request("GET", "/api/notes", query={"session_id": ["mock-session"], "page": ["2"]})
        shell.garden_notes("write", content="  今晚的花  ")
        self.assert_request("POST", "/api/notes", body={"session_id": "mock-session", "content": "  今晚的花  "})

    def test_default_base_and_no_cache(self):
        os.environ.pop("GARDEN_API_BASE_URL")
        shell.garden_reference("info")
        self.assertEqual(self.urlopen.call_args.args[0].full_url, "http://127.0.0.1:8080/api/info")
        self.payload = {"ok": False, "message": "changed"}
        self.assertEqual(shell.garden_reference("info"), self.payload)
        self.assertEqual(self.urlopen.call_count, 2)

    def test_invalid_arguments_do_not_send_http(self):
        for call in (
            lambda: shell.garden_reference("register"),
            lambda: shell.garden_command(" "),
            lambda: shell.garden_notes("delete"),
            lambda: shell.garden_notes("read", page=0),
            lambda: shell.garden_notes("read", content="wrong"),
            lambda: shell.garden_notes("write"),
            lambda: shell.garden_notes("write", page=1, content="wrong"),
        ):
            with self.subTest(call=call), self.assertRaises(ToolError):
                call()
        os.environ.pop("GARDEN_SESSION_ID")
        with self.assertRaisesRegex(ToolError, "GARDEN_SESSION_ID"):
            shell.garden_status()
        self.urlopen.assert_not_called()

    def test_connection_and_timeout_errors_are_sanitized(self):
        for error in (URLError("mock-key secret detail"), TimeoutError("trace detail")):
            self.urlopen.side_effect = error
            with self.assertRaisesRegex(ToolError, "无法连接本地 API 或请求超时") as caught:
                shell.garden_status()
            self.assertNotIn("mock-key", str(caught.exception))
            self.assertNotIn("trace detail", str(caught.exception))

    def test_http_errors_keep_api_message(self):
        for code, message in ((401, "无效的 API Key"), (403, "AI 不可使用"),
                              (400, "请提供有效的 session_id"), (404, "session_id 不存在"),
                              (429, "便签冷却中")):
            self.urlopen.side_effect = HTTPError("http://mock", code, "error", {},
                                                io.BytesIO(json.dumps({"error": message}).encode()))
            with self.subTest(code=code), self.assertRaises(ToolError) as caught:
                shell.garden_status()
            self.assertIn(f"HTTP {code}", str(caught.exception))
            self.assertIn(message, str(caught.exception))

    def test_non_json_response_is_brief_error(self):
        self.urlopen.side_effect = lambda *a, **kw: io.BytesIO(b"<html>not an API</html>")
        with self.assertRaisesRegex(ToolError, "非 JSON"):
            shell.garden_status()


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_lists_four_tools_and_returns_mcp_error(self):
        script = Path(__file__).resolve().parents[1] / "local_mcp_test.py"
        params = StdioServerParameters(command=sys.executable, args=["-B", str(script)], env={
            "GARDEN_SESSION_ID": "", "GARDEN_API_KEY": "", "PYTHONIOENCODING": "utf-8",
        })
        async with asyncio.timeout(20):
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    self.assertEqual({tool.name for tool in tools}, {
                        "garden_reference", "garden_status", "garden_command", "garden_notes",
                    })
                    schema = {tool.name: tool.inputSchema for tool in tools}
                    self.assertEqual(schema["garden_reference"]["properties"]["kind"]["enum"], ["info", "catalog", "help"])
                    self.assertEqual(schema["garden_command"]["required"], ["command"])
                    self.assertEqual(schema["garden_notes"]["required"], ["action"])
                    result = await session.call_tool("garden_status", {})
                    self.assertTrue(result.isError)
                    self.assertIn("GARDEN_SESSION_ID", result.content[0].text)
                    self.assertNotIn("Traceback", result.content[0].text)


if __name__ == "__main__":
    unittest.main()
