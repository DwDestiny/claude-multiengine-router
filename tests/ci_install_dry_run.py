#!/usr/bin/env python3
"""Input: installer plus fake CLIs. Output: dry-run JSON assertions in a temp home.
Pos: cross-platform CI smoke test that avoids real Claude MCP registration.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fake_cli_path(fake_bin: Path, name: str) -> Path:
    if os.name == "nt":
        return fake_bin / f"{name}.cmd"
    return fake_bin / name


def write_fake_cli(fake_bin: Path, name: str) -> Path:
    path = fake_cli_path(fake_bin, name)
    if os.name == "nt":
        path.write_text("@echo off\r\necho fake\r\n", encoding="utf-8")
    else:
        path.write_text("#!/usr/bin/env bash\nset -euo pipefail\necho fake\n", encoding="utf-8", newline="\n")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="cmr-ci-dry-run.") as tmp:
        tmp_root = Path(tmp)
        fake_bin = tmp_root / "bin"
        test_home = tmp_root / "home"
        fake_bin.mkdir()
        test_home.mkdir()

        for name in ("claude", "codex", "grok"):
            write_fake_cli(fake_bin, name)

        env = os.environ.copy()
        env.update(
            {
                "HOME": str(test_home),
                "USERPROFILE": str(test_home),
                "PATH": f"{fake_bin}{os.pathsep}{env.get('PATH', '')}",
                "AGENT_ROUTER_SKIP_AUTH_CHECK": "1",
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

        completed = subprocess.run(
            [sys.executable, str(ROOT / "install.py"), "--dry-run", "--json"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            print(completed.stdout, end="")
            print(completed.stderr, end="", file=sys.stderr)
            return completed.returncode

        payload = json.loads(completed.stdout)
        assert payload["dry_run"] is True
        assert payload["claude_home"] == str(test_home / ".claude")
        assert payload["skips"]["auth_check"] is True
        assert payload["skips"]["venv"] is True
        assert payload["skips"]["mcp_add"] is True
        assert not (test_home / ".claude").exists()

        print(f"Install dry-run smoke passed: temp home {test_home} was not modified.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
