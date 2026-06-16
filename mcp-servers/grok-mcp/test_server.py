#!/usr/bin/env python3
"""Input: server helper functions. Output: focused unit checks for routing logic.
Pos: low-level guardrail tests for Grok CLI parsing, discovery, and commands.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import server


class GrokServerHelpersTest(unittest.TestCase):
    def test_parse_success_schema_returns_data(self) -> None:
        payload = server.parse_grok_stdout(
            '{"ok":true,"data":{"output_text":"OK","model":"grok-build","finish_reason":"stop","tool_calls":[]}}'
        )

        self.assertEqual(payload["output_text"], "OK")
        self.assertEqual(payload["model"], "grok-build")
        self.assertEqual(payload["finish_reason"], "stop")

    def test_parse_text_schema_returns_output_text(self) -> None:
        payload = server.parse_grok_stdout(
            '{"text":"OK from text","stopReason":"EndTurn","sessionId":"sid","requestId":"rid"}'
        )

        self.assertEqual(payload["output_text"], "OK from text")
        self.assertEqual(payload["finish_reason"], "EndTurn")
        self.assertEqual(payload["sessionId"], "sid")
        self.assertEqual(payload["requestId"], "rid")

    def test_parse_error_schema_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(server.GrokOutputError, "Grok returned error: bad"):
            server.parse_grok_stdout('{"ok":false,"error":"bad"}')

        with self.assertRaisesRegex(server.GrokOutputError, "Grok returned error"):
            server.parse_grok_stdout('{"error":{"code":"bad_request","message":"bad"}}')

    def test_parse_unknown_json_falls_back_to_raw_json_text(self) -> None:
        payload = server.parse_grok_stdout('{"type":"notice","message":"new schema"}')

        self.assertEqual(payload["output_text"], '{"type": "notice", "message": "new schema"}')

    def test_parse_non_json_falls_back_to_raw_text(self) -> None:
        payload = server.parse_grok_stdout("plain text result")

        self.assertEqual(payload["output_text"], "plain text result")

    def test_login_error_is_normalized(self) -> None:
        self.assertTrue(server.is_login_error("Authentication failed. Please run grok login.", ""))
        self.assertTrue(server.is_login_error("", "not logged in"))
        self.assertTrue(server.is_login_error("", "not authenticated"))

    def test_resolve_grok_bin_prefers_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            grok = Path(tmp) / "grok"
            grok.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            grok.chmod(0o755)

            with mock.patch.dict(os.environ, {"GROK_BIN": str(grok)}, clear=False):
                self.assertEqual(server.resolve_grok_bin(), str(grok))

    def test_resolve_grok_bin_falls_back_to_path(self) -> None:
        with mock.patch.dict(os.environ, {"GROK_BIN": ""}, clear=False), mock.patch(
            "shutil.which", return_value="/usr/local/bin/grok"
        ):
            self.assertEqual(server.resolve_grok_bin(), "/usr/local/bin/grok")

    def test_resolve_grok_bin_errors_clearly(self) -> None:
        with mock.patch.dict(os.environ, {"GROK_BIN": ""}, clear=False), mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "Grok Build CLI was not found"):
                server.resolve_grok_bin()

    def test_code_command_uses_resolved_grok_and_configured_model(self) -> None:
        with mock.patch.dict(os.environ, {"GROK_BIN": "/tmp/grok", "GROK_MODEL": "grok-test"}, clear=False), mock.patch(
            "pathlib.Path.exists", return_value=True
        ), mock.patch("os.access", return_value=True):
            command = server.build_code_command("/tmp/project", "fix bug", best_of_n=3, check=True)

        self.assertEqual(command[0], "/tmp/grok")
        self.assertIn("-p", command)
        self.assertIn("--cwd", command)
        self.assertIn("/tmp/project", command)
        self.assertIn("--best-of-n", command)
        self.assertIn("3", command)
        self.assertIn("--check", command)
        self.assertEqual(command[-2:], ["-m", "grok-test"])

    def test_grok_env_uses_writable_runtime_home_and_generic_auth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            auth = home / ".grok" / "auth.json"
            auth.parent.mkdir(parents=True)
            auth.write_text("{}", encoding="utf-8")

            with mock.patch("pathlib.Path.home", return_value=home):
                env = server.build_grok_env({})

        self.assertIn("grok-mcp-home", env["GROK_HOME"])
        self.assertIn("grok-mcp-leader.sock", env["GROK_LEADER_SOCKET"])
        self.assertEqual(env["GROK_CLAUDE_MCPS_ENABLED"], "0")
        self.assertEqual(env["GROK_CURSOR_MCPS_ENABLED"], "0")
        self.assertEqual(env["GROK_MANAGED_MCPS_ENABLED"], "0")
        self.assertEqual(env["GROK_AUTH_PATH"], str(auth))


if __name__ == "__main__":
    unittest.main()
