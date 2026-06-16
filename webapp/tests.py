import json
import os
import tempfile
from pathlib import Path

from django.test import TestCase

from .aida_controller import CodeGenerator, CodeRuntime, ReasoningEngine
from .models import AccessKey
from .security import generate_access_key_with_profile

BASE = Path(__file__).resolve().parent.parent


class StatusApiTests(TestCase):
    def test_status_returns_ok(self):
        resp = self.client.get("/api/status/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("provider", data)
        self.assertIn("model", data)
        self.assertIn("platform", data)

    def test_status_includes_provider_name(self):
        resp = self.client.get("/api/status/")
        data = resp.json()
        self.assertIsInstance(data.get("provider"), str)
        self.assertTrue(len(data["provider"]) > 0)


class SessionTests(TestCase):
    def test_create_session_returns_uuid(self):
        resp = self.client.post(
            "/api/sessions/create/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        sid = resp.json().get("session_id")
        self.assertIsNotNone(sid)
        self.assertEqual(len(sid), 36)

    def test_list_sessions_returns_list(self):
        resp = self.client.get("/api/sessions/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json().get("sessions"), list)

    def test_session_history_empty_for_new_session(self):
        resp = self.client.get("/api/sessions/new-session-test/history/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["session_id"], "new-session-test")
        self.assertEqual(data["messages"], [])


class ChatApiTests(TestCase):
    def test_chat_returns_message(self):
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "Salom", "session_id": "chat-test-1"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("message", data)
        self.assertTrue(len(data["message"]) > 0)

    def test_chat_empty_prompt_returns_error(self):
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "", "session_id": "chat-test-2"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())

    def test_chat_missing_prompt_returns_error(self):
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"session_id": "chat-test-3"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_chat_invalid_json_returns_error(self):
        resp = self.client.post(
            "/api/chat/",
            data="not json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_chat_with_research_flag(self):
        resp = self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "Test", "research": True, "session_id": "chat-test-4"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("message", resp.json())

    def test_chat_stream_returns_sse(self):
        resp = self.client.post(
            "/api/chat/stream/",
            data=json.dumps({"prompt": "Salom", "session_id": "stream-test-1"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/event-stream")
        content = resp.content.decode("utf-8")
        self.assertIn("data:", content)
        self.assertIn("session_id", content)

    def test_chat_memory_db_updated(self):
        self.client.post(
            "/api/chat/",
            data=json.dumps({"prompt": "Xotira test", "session_id": "memory-test"}),
            content_type="application/json",
        )
        resp = self.client.get("/api/sessions/memory-test/history/")
        data = resp.json()
        messages = data.get("messages", [])
        self.assertGreaterEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertIn("Xotira test", messages[0]["content"])


class CodeGenerationTests(TestCase):
    def test_generate_python_code(self):
        resp = self.client.post(
            "/api/code/generate/",
            data=json.dumps({"prompt": "print('hello') funksiyasi", "language": "python"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("code", data)
        self.assertEqual(data["language"], "python")
        self.assertIn("trace", data)
        self.assertIn("analysis", data)

    def test_generate_html(self):
        resp = self.client.post(
            "/api/code/generate/",
            data=json.dumps({"prompt": "Sahifa yarat", "language": "html"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["language"], "html")

    def test_generate_empty_prompt_returns_error(self):
        resp = self.client.post(
            "/api/code/generate/",
            data=json.dumps({"prompt": "", "language": "python"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_analyze_code(self):
        resp = self.client.post(
            "/api/code/analyze/",
            data=json.dumps({"code": "print('hello')", "language": "python"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("analysis", data)
        self.assertIn("fixed", data)
        self.assertEqual(data["language"], "python")

    def test_analyze_empty_code_returns_error(self):
        resp = self.client.post(
            "/api/code/analyze/",
            data=json.dumps({"code": "", "language": "python"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_preview_html(self):
        resp = self.client.post(
            "/api/code/preview/",
            data=json.dumps({"code": "<h1>Test</h1>", "language": "html"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["type"], "html")
        self.assertIn("<h1>Test</h1>", data["html"])

    def test_preview_css(self):
        resp = self.client.post(
            "/api/code/preview/",
            data=json.dumps({"code": "body{color:red}", "language": "css"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("<style>", resp.json()["html"])

    def test_code_generator_class_direct(self):
        cg = CodeGenerator()
        code = cg.generate("hello world print", language="python")
        self.assertIn("print", code)
        self.assertIsInstance(code, str)
        analysis = cg.analyze(code, language="python")
        self.assertIsInstance(analysis, str)

    def test_code_fix_errors(self):
        cg = CodeGenerator()
        fixed = cg.fix_errors("print('hello'", language="python")
        self.assertIsInstance(fixed, str)

    def test_reasoning_engine(self):
        reng = ReasoningEngine()
        trace = reng.reason("test prompt", "code", ["test"], [])
        self.assertIsInstance(trace, str)
        self.assertTrue(len(trace) > 0)


class CodeWorkspaceTests(TestCase):
    def test_code_page_loads(self):
        resp = self.client.get("/code/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AIDA Code", resp.content.decode("utf-8"))

    def test_login_page_loads(self):
        resp = self.client.get("/login/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AIDA", resp.content.decode("utf-8"))

    def test_root_redirects_to_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("AIDA", resp.content.decode("utf-8"))


class RuntimeApiTests(TestCase):
    def setUp(self):
        self.runtime = CodeRuntime()

    def test_save_and_read_file(self):
        resp = self.client.post(
            "/api/runtime/save/",
            data=json.dumps({"path": "test_abc.py", "content": "print('ok')"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("path", resp.json())

        resp2 = self.client.post(
            "/api/runtime/read/",
            data=json.dumps({"path": "test_abc.py"}),
            content_type="application/json",
        )
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("print('ok')", resp2.json()["content"])

        self.client.post(
            "/api/runtime/delete/",
            data=json.dumps({"path": "test_abc.py"}),
            content_type="application/json",
        )

    def test_save_empty_path_returns_error(self):
        resp = self.client.post(
            "/api/runtime/save/",
            data=json.dumps({"path": "", "content": "code"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_read_nonexistent_returns_error(self):
        resp = self.client.post(
            "/api/runtime/read/",
            data=json.dumps({"path": "nonexistent_file_xyz.py"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.json())

    def test_delete_nonexistent_returns_error(self):
        resp = self.client.post(
            "/api/runtime/delete/",
            data=json.dumps({"path": "nonexistent_file_xyz.py"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("error", resp.json())

    def test_files_list_returns_list(self):
        resp = self.client.get("/api/runtime/files/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json().get("files"), list)

    def test_run_nonexistent_returns_error(self):
        resp = self.client.post(
            "/api/runtime/run/",
            data=json.dumps({"path": "nonexistent_run_test.py"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue("error" in data or "stdout" in data)


class ProjectApiTests(TestCase):
    def test_project_current_when_closed(self):
        self.client.post(
            "/api/project/close/",
            data=json.dumps({}),
            content_type="application/json",
        )
        resp = self.client.get("/api/project/current/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("is_open", data)
        self.assertFalse(data["is_open"])

    def test_project_open_with_valid_path(self):
        resp = self.client.post(
            "/api/project/open/",
            data=json.dumps({"path": str(BASE)}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("name", data)
        self.assertIn("path", data)

    def test_project_open_invalid_path_returns_error(self):
        resp = self.client.post(
            "/api/project/open/",
            data=json.dumps({"path": "Z:\\nonexistent"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertIn("error", data)

    def test_project_list_returns_list(self):
        resp = self.client.get("/api/project/list/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json().get("projects"), list)

    def test_project_close(self):
        self.client.post(
            "/api/project/open/",
            data=json.dumps({"path": str(BASE)}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/project/close/",
            data=json.dumps({}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("status"), "closed")


class AccessKeyTests(TestCase):
    def test_create_key(self):
        resp = self.client.post(
            "/api/keys/create/",
            data=json.dumps({
                "name": "Test Key",
                "platform_name": "Test Platform",
                "business_type": "test",
                "audience": "testers",
                "tone": "professional",
                "assistant_goal": "testing",
                "custom_instructions": "Test qil",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["name"], "Test Key")
        self.assertIn("secret", data)
        self.assertIn("prefix", data)

    def test_list_keys(self):
        generate_access_key_with_profile("List Key", {})
        resp = self.client.get("/api/keys/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data.get("items"), list)
        self.assertGreaterEqual(len(data["items"]), 1)

    def test_platform_chat_with_missing_key(self):
        resp = self.client.post(
            "/api/platform/chat/",
            data=json.dumps({"prompt": "Salom"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_platform_chat_with_valid_key(self):
        key_obj, secret = generate_access_key_with_profile("Plat Key", {
            "platform_name": "Test",
            "business_type": "test",
            "audience": "test",
            "tone": "neutral",
            "assistant_goal": "test",
            "custom_instructions": "Test",
        })
        resp = self.client.post(
            "/api/platform/chat/",
            data=json.dumps({"prompt": "Salom", "session_id": "plat-test-1"}),
            content_type="application/json",
            HTTP_X_AIDA_KEY=secret,
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("message", data)
        self.assertEqual(data["key_name"], "Plat Key")

    def test_platform_chat_with_bearer_token(self):
        _, secret = generate_access_key_with_profile("Bearer Key", {})
        resp = self.client.post(
            "/api/platform/chat/",
            data=json.dumps({"prompt": "Test"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {secret}",
        )
        self.assertEqual(resp.status_code, 200)
