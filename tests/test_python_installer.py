#!/usr/bin/env python3
"""Input: Python installer modules plus fake CLIs. Output: cross-platform install assertions.
Pos: Phase 2 guardrail tests for portable installer behavior.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


install = load_module("cmr_install", ROOT / "install.py")
uninstall = load_module("cmr_uninstall", ROOT / "uninstall.py")


def write_executable(path: Path, body: str) -> None:
    newline = "\r\n" if path.suffix.lower() == ".cmd" else "\n"
    path.write_text(body, encoding="utf-8", newline=newline)
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def fake_cli_path(fake_bin: Path, name: str) -> Path:
    if os.name == "nt":
        return fake_bin / f"{name}.cmd"
    return fake_bin / name


def write_fake_cli(fake_bin: Path, name: str, unix_body: str, windows_body: str) -> Path:
    path = fake_cli_path(fake_bin, name)
    write_executable(path, windows_body if os.name == "nt" else unix_body)
    return path


def expected_native_path(posix_style_path: str) -> str:
    if os.name == "nt":
        return str(Path(posix_style_path))
    return posix_style_path


class PythonInstallerUnitTest(unittest.TestCase):
    def test_windows_home_prefers_userprofile_over_home(self) -> None:
        home = install.home_from_env({"USERPROFILE": r"C:\Users\Ada", "HOME": "/wrong"}, "Windows")

        self.assertEqual(str(home), r"C:\Users\Ada")

    def test_windows_venv_python_uses_scripts_directory(self) -> None:
        mcp_target = Path("C:/Users/Ada/.claude/mcp-servers/grok-mcp")

        venv_python = install.venv_python_path(mcp_target, "Windows")

        self.assertEqual(venv_python.parts[-3:], (".venv", "Scripts", "python.exe"))

    def test_mcp_add_commands_are_unquoted_argument_lists(self) -> None:
        mcp_target = Path("C:/Users/Ada/.claude/mcp-servers/grok-mcp")
        claude_bin = Path("C:/Tools/claude.exe")
        codex_bin = Path("C:/Tools/codex.exe")
        grok_bin = Path("C:/Tools/grok.exe")

        commands = install.build_mcp_add_commands(
            claude_bin=claude_bin,
            codex_bin=codex_bin,
            grok_bin=grok_bin,
            grok_model="grok-build",
            mcp_target=mcp_target,
            platform_name="Windows",
        )

        self.assertEqual(
            commands["codex"],
            [
                expected_native_path("C:/Tools/claude.exe"),
                "mcp",
                "add",
                "-s",
                "user",
                "codex",
                "--",
                expected_native_path("C:/Tools/codex.exe"),
                "mcp-server",
            ],
        )
        grok_command = commands["grok"]
        self.assertEqual(
            grok_command[:6],
            [expected_native_path("C:/Tools/claude.exe"), "mcp", "add", "-s", "user", "grok"],
        )
        self.assertIn(f"GROK_BIN={expected_native_path('C:/Tools/grok.exe')}", grok_command)
        self.assertIn("GROK_MODEL=grok-build", grok_command)
        self.assertEqual(Path(grok_command[-2]).parts[-3:], (".venv", "Scripts", "python.exe"))
        self.assertEqual(Path(grok_command[-1]).name, "server.py")

    def test_windows_backup_names_are_drive_and_separator_safe(self) -> None:
        name = uninstall.backup_name_for(r"C:\Users\Ada\.claude\agents\codex-exec.md")

        self.assertNotIn(":", name)
        self.assertNotIn("\\", name)
        self.assertIn("codex-exec.md", name)


class PythonInstallerSmokeTest(unittest.TestCase):
    def test_install_uses_temp_home_and_fake_clis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmr-python-install.") as tmp:
            tmp_root = Path(tmp)
            fake_bin = tmp_root / "bin"
            test_home = tmp_root / "home"
            fake_bin.mkdir()
            test_home.mkdir()

            write_fake_cli(
                fake_bin,
                "claude",
                """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  mcp)
    case "${2:-}" in
      add) echo "mcp add ${*:3}" >>"${CLAUDE_MCP_LOG:?}" ;;
      list) printf 'codex: Connected\\n'; printf 'grok: Connected\\n' ;;
      remove) echo "mcp remove ${*:3}" >>"${CLAUDE_MCP_LOG:?}" ;;
      *) exit 2 ;;
    esac
    ;;
  *) exit 2 ;;
esac
""",
                """@echo off
if "%1"=="mcp" (
  if "%2"=="add" exit /b 0
  if "%2"=="list" (
    echo codex: Connected
    echo grok: Connected
    exit /b 0
  )
  if "%2"=="remove" exit /b 0
)
exit /b 2
""",
            )
            codex_path = write_fake_cli(
                fake_bin,
                "codex",
                """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  login) [[ "${2:-}" == "status" ]] && echo "Logged in" || exit 2 ;;
  mcp-server) echo "codex mcp server" ;;
  *) exit 2 ;;
esac
""",
                """@echo off
if "%1"=="login" (
  if "%2"=="status" (
    echo Logged in
    exit /b 0
  )
)
if "%1"=="mcp-server" (
  echo codex mcp server
  exit /b 0
)
exit /b 2
""",
            )
            grok_path = write_fake_cli(
                fake_bin,
                "grok",
                """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  models) printf 'grok-build\\n' ;;
  *) exit 2 ;;
esac
""",
                """@echo off
if "%1"=="models" (
  echo grok-build
  exit /b 0
)
exit /b 2
""",
            )

            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(test_home),
                    "USERPROFILE": str(test_home),
                    "PATH": f"{fake_bin}{os.pathsep}{env.get('PATH', '')}",
                    "CLAUDE_MCP_LOG": str(tmp_root / "mcp.log"),
                    "AGENT_ROUTER_SKIP_VENV": "1",
                    "AGENT_ROUTER_SKIP_MCP_ADD": "1",
                    "OUTPUT_DIR": str(test_home / "router-output"),
                    "ENABLE_WIKI_LOG": "false",
                    "CODEX_MODEL": "test-codex-model",
                    "GROK_MODEL": "grok-build",
                }
            )
            if os.name == "nt":
                env["PATHEXT"] = f".COM;.EXE;.BAT;.CMD;{env.get('PATHEXT', '')}"

            subprocess.run([sys.executable, str(ROOT / "install.py")], cwd=ROOT, env=env, check=True)
            expected_codex_path = shutil.which("codex", path=env["PATH"]) or str(codex_path)
            expected_grok_path = shutil.which("grok", path=env["PATH"]) or str(grok_path)

            claude_home = test_home / ".claude"
            self.assertTrue((claude_home / "skills/agent-router/SKILL.md").is_file())
            self.assertTrue((claude_home / "agents/codex-exec.md").is_file())
            self.assertTrue((claude_home / "mcp-servers/grok-mcp/server.py").is_file())
            self.assertTrue((claude_home / "agent-router/config.sh").is_file())
            self.assertTrue((claude_home / "agent-router/config.ps1").is_file())
            self.assertIn(
                expected_codex_path,
                (claude_home / "agents/codex-exec.md").read_text(encoding="utf-8"),
            )
            self.assertIn(
                expected_grok_path,
                (claude_home / "agents/grok-coder.md").read_text(encoding="utf-8"),
            )
            self.assertIn(str(test_home / "router-output/images"), (claude_home / "agents/codex-image.md").read_text(encoding="utf-8"))

    def test_dry_run_json_does_not_create_claude_home(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cmr-python-dry-run.") as tmp:
            tmp_root = Path(tmp)
            fake_bin = tmp_root / "bin"
            test_home = tmp_root / "home"
            fake_bin.mkdir()
            test_home.mkdir()
            for name in ("claude", "codex", "grok"):
                write_fake_cli(fake_bin, name, "#!/usr/bin/env bash\necho fake\n", "@echo off\necho fake\n")

            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(test_home),
                    "USERPROFILE": str(test_home),
                    "PATH": f"{fake_bin}{os.pathsep}{env.get('PATH', '')}",
                    "AGENT_ROUTER_SKIP_AUTH_CHECK": "1",
                }
            )
            if os.name == "nt":
                env["PATHEXT"] = f".COM;.EXE;.BAT;.CMD;{env.get('PATHEXT', '')}"

            completed = subprocess.run(
                [sys.executable, str(ROOT / "install.py"), "--dry-run", "--json"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["dry_run"], True)
            self.assertEqual(payload["claude_home"], str(test_home / ".claude"))
            self.assertFalse((test_home / ".claude").exists())


if __name__ == "__main__":
    unittest.main()
