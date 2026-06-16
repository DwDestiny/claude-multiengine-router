#!/usr/bin/env python3
"""Input: user-scoped Claude router install. Output: backup then removal of router files and MCP registrations.
Pos: cross-platform uninstaller for claude-multiengine-router.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_NAME = "claude-multiengine-router"
SUPPORTED_PLATFORMS = {"Darwin", "Linux", "Windows"}
AGENTS = ("codex-exec", "codex-fast", "codex-image", "codex-review", "grok-research", "grok-coder")


class UninstallError(RuntimeError):
    """Raised for user-actionable uninstall failures."""


@dataclass(frozen=True)
class UninstallConfig:
    platform_name: str
    home: Path
    claude_home: Path
    backup_dir: Path
    skip_mcp_remove: bool = False
    dry_run: bool = False


def home_from_env(env: Mapping[str, str] | None = None, platform_name: str | None = None) -> Path:
    env = env or os.environ
    platform_name = platform_name or platform.system()
    if platform_name == "Windows" and env.get("USERPROFILE"):
        return Path(env["USERPROFILE"])
    if env.get("HOME"):
        return Path(env["HOME"])
    return Path.home()


def backup_name_for(target: str | Path) -> str:
    raw = str(target).strip()
    raw = raw.replace(":", "")
    raw = raw.replace("\\", "__").replace("/", "__")
    raw = raw.lstrip("_")
    return raw or "root"


def find_on_path(command_name: str, env: Mapping[str, str], platform_name: str) -> str | None:
    found = shutil.which(command_name, path=env.get("PATH"))
    if found:
        return found
    if platform_name == "Windows":
        try:
            completed = subprocess.run(
                ["where.exe", command_name],
                check=False,
                capture_output=True,
                text=True,
                env=dict(env),
            )
        except OSError:
            return None
        if completed.returncode == 0:
            for line in completed.stdout.splitlines():
                candidate = line.strip()
                if candidate:
                    return candidate
    return None


class Uninstaller:
    def __init__(self, config: UninstallConfig, *, json_mode: bool = False) -> None:
        self.config = config
        self.json_mode = json_mode
        self.removed: list[str] = []

    def info(self, message: str) -> None:
        if not self.json_mode:
            print(f"[{PROJECT_NAME}] {message}")

    def warn(self, message: str) -> None:
        print(f"[{PROJECT_NAME}] WARNING: {message}", file=sys.stderr)

    def backup_path(self, target: Path) -> None:
        if not target.exists():
            return
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
        backup = self.config.backup_dir / backup_name_for(target)
        index = 1
        while backup.exists():
            backup = self.config.backup_dir / f"{backup_name_for(target)}.{index}"
            index += 1
        self.info(f"Backing up {target} -> {backup}")
        shutil.move(str(target), str(backup))
        self.removed.append(str(target))

    def remove_mcp_registration(self) -> None:
        if self.config.skip_mcp_remove:
            self.warn("Skipping Claude MCP removal because AGENT_ROUTER_SKIP_MCP_REMOVE=1.")
            return

        claude = find_on_path("claude", os.environ, self.config.platform_name)
        if not claude:
            self.warn("Claude CLI not found; skipped MCP registration removal.")
            return

        for name in ("codex", "grok"):
            subprocess.run(
                [claude, "mcp", "remove", "-s", "user", name],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def run(self) -> dict[str, object]:
        targets = [
            self.config.claude_home / "skills" / "agent-router",
            *(self.config.claude_home / "agents" / f"{agent}.md" for agent in AGENTS),
            self.config.claude_home / "mcp-servers" / "grok-mcp",
            self.config.claude_home / "agent-router",
        ]

        if self.config.dry_run:
            return {
                "dry_run": True,
                "platform": self.config.platform_name,
                "claude_home": str(self.config.claude_home),
                "backup_dir": str(self.config.backup_dir),
                "targets": [str(target) for target in targets],
            }

        for target in targets:
            self.backup_path(target)
        self.remove_mcp_registration()
        self.info(f"Uninstall complete. Backup directory: {self.config.backup_dir}")
        return {
            "dry_run": False,
            "platform": self.config.platform_name,
            "claude_home": str(self.config.claude_home),
            "backup_dir": str(self.config.backup_dir),
            "removed": self.removed,
        }


def build_config(args: argparse.Namespace, env: Mapping[str, str] | None = None) -> UninstallConfig:
    env = env or os.environ
    detected_platform = platform.system()
    platform_name = detected_platform if args.platform == "auto" else args.platform
    if platform_name not in SUPPORTED_PLATFORMS:
        raise UninstallError(f"Unsupported OS: {platform_name}. Supported: macOS, Linux, and Windows.")

    home = home_from_env(env, platform_name)
    claude_home = Path(env.get("CLAUDE_HOME") or home / ".claude")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = claude_home / "backups" / f"{PROJECT_NAME}-uninstall-{timestamp}"
    return UninstallConfig(
        platform_name=platform_name,
        home=home,
        claude_home=claude_home,
        backup_dir=backup_dir,
        skip_mcp_remove=env.get("AGENT_ROUTER_SKIP_MCP_REMOVE") == "1",
        dry_run=args.dry_run,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Uninstall claude-multiengine-router from the user-scoped Claude home.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned uninstall without moving files.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    parser.add_argument(
        "--platform",
        choices=("auto", "Darwin", "Linux", "Windows"),
        default="auto",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        config = build_config(args)
        payload = Uninstaller(config, json_mode=args.json).run()
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except UninstallError as exc:
        print(f"[{PROJECT_NAME}] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
