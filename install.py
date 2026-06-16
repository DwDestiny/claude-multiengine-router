#!/usr/bin/env python3
"""Input: this repository plus installed claude/codex/grok/Python CLIs. Output: user-scoped Claude router install.
Pos: cross-platform installer for claude-multiengine-router.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_NAME = "claude-multiengine-router"
SUPPORTED_PLATFORMS = {"Darwin", "Linux", "Windows"}
AGENTS = ("codex-exec", "codex-fast", "codex-image", "codex-review", "grok-research", "grok-coder")
CONFIG_KEYS = {
    "OUTPUT_DIR",
    "ENABLE_WIKI_LOG",
    "CODEX_MODEL",
    "GROK_MODEL",
    "CLAUDE_HOME",
    "CLAUDE_BIN",
    "CODEX_BIN",
    "GROK_BIN",
    "PYTHON_BIN",
}


class InstallError(RuntimeError):
    """Raised for user-actionable install failures."""


@dataclass(frozen=True)
class InstallConfig:
    repo_root: Path
    platform_name: str
    home: Path
    claude_home: Path
    output_dir: Path
    enable_wiki_log: str
    codex_model: str
    grok_model: str
    claude_bin: Path
    codex_bin: Path
    grok_bin: Path
    python_bin: Path
    timestamp: str
    dry_run: bool = False
    skip_auth_check: bool = False
    skip_venv: bool = False
    skip_mcp_add: bool = False


def _now_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def home_from_env(env: Mapping[str, str] | None = None, platform_name: str | None = None) -> Path:
    env = env or os.environ
    platform_name = platform_name or platform.system()
    if platform_name == "Windows" and env.get("USERPROFILE"):
        return Path(env["USERPROFILE"])
    if env.get("HOME"):
        return Path(env["HOME"])
    return Path.home()


def expand_env_vars(value: str, env: Mapping[str, str]) -> str:
    def replace_var(match: re.Match[str]) -> str:
        name = match.group("braced") or match.group("plain")
        return env.get(name, "")

    return re.sub(r"\$\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|\$(?P<plain>[A-Za-z_][A-Za-z0-9_]*)", replace_var, value)


def expand_shell_default(value: str, env: Mapping[str, str]) -> str:
    match = re.fullmatch(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*):-(?P<default>.*)\}", value)
    if not match:
        return expand_env_vars(value, env)
    current = env.get(match.group("name"), "")
    return current if current else expand_env_vars(match.group("default"), env)


def strip_shell_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_config_file(path: Path, env: Mapping[str, str]) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in CONFIG_KEYS:
            continue
        value = strip_shell_quotes(value.strip().rstrip(";"))
        values[key] = expand_shell_default(value, env)
    return values


def config_value(name: str, default: str, config_values: Mapping[str, str], env: Mapping[str, str]) -> str:
    if env.get(name, "") != "":
        return env[name]
    if config_values.get(name, "") != "":
        return config_values[name]
    return default


def expand_path(raw: str, home: Path, cwd: Path, env: Mapping[str, str] | None = None) -> Path:
    env = env or os.environ
    value = expand_env_vars(raw, env)
    if value == "~":
        return home
    if value.startswith("~/") or value.startswith("~\\"):
        return home / value[2:]
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return cwd / path


def is_executable_file(path: Path, platform_name: str) -> bool:
    if not path.exists() or path.is_dir():
        return False
    if platform_name == "Windows":
        return True
    return os.access(path, os.X_OK)


def find_on_path(command_name: str, env: Mapping[str, str], platform_name: str) -> Path | None:
    found = shutil.which(command_name, path=env.get("PATH"))
    if found:
        return Path(found)

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
                    return Path(candidate)

    return None


def resolve_cli(
    *,
    env_name: str,
    command_name: str,
    install_hint: str,
    configured: str,
    home: Path,
    cwd: Path,
    env: Mapping[str, str],
    platform_name: str,
) -> Path:
    if configured:
        candidate = expand_path(configured, home, cwd, env)
        if is_executable_file(candidate, platform_name):
            return candidate
        raise InstallError(f"{env_name} is set but not executable: {candidate}. {install_hint}")

    found = find_on_path(command_name, env, platform_name)
    if found:
        return found
    raise InstallError(f"Missing required CLI: {command_name}. {install_hint}")


def resolve_python_bin(configured: str, home: Path, cwd: Path, env: Mapping[str, str], platform_name: str) -> Path:
    if configured:
        candidate = expand_path(configured, home, cwd, env)
        if is_executable_file(candidate, platform_name):
            return candidate
        raise InstallError(f"PYTHON_BIN is set but not executable: {candidate}. Install Python 3.")

    for command_name in ("python3", "python"):
        found = find_on_path(command_name, env, platform_name)
        if found:
            return found
    return Path(sys.executable)


def venv_python_path(mcp_target: Path, platform_name: str) -> Path:
    if platform_name == "Windows":
        return mcp_target / ".venv" / "Scripts" / "python.exe"
    return mcp_target / ".venv" / "bin" / "python"


def build_mcp_add_commands(
    *,
    claude_bin: Path,
    codex_bin: Path,
    grok_bin: Path,
    grok_model: str,
    mcp_target: Path,
    platform_name: str,
) -> dict[str, list[str]]:
    venv_python = venv_python_path(mcp_target, platform_name)
    return {
        "codex": [
            str(claude_bin),
            "mcp",
            "add",
            "-s",
            "user",
            "codex",
            "--",
            str(codex_bin),
            "mcp-server",
        ],
        "grok": [
            str(claude_bin),
            "mcp",
            "add",
            "-s",
            "user",
            "grok",
            "-e",
            f"GROK_BIN={grok_bin}",
            "-e",
            f"GROK_MODEL={grok_model}",
            "--",
            str(venv_python),
            str(mcp_target / "server.py"),
        ],
    }


def sh_quote(value: str) -> str:
    if value and re.fullmatch(r"[A-Za-z0-9_@%+=:,./-]+", value):
        return value
    if value == "":
        return "''"
    return "'" + value.replace("'", "'\"'\"'") + "'"


def ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


class Installer:
    def __init__(self, config: InstallConfig, *, json_mode: bool = False) -> None:
        self.config = config
        self.json_mode = json_mode

    def info(self, message: str) -> None:
        if not self.json_mode:
            print(f"[{PROJECT_NAME}] {message}")

    def warn(self, message: str) -> None:
        print(f"[{PROJECT_NAME}] WARNING: {message}", file=sys.stderr)

    def run_subprocess(self, command: Sequence[str | Path], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [str(part) for part in command],
            check=False,
            text=True,
            capture_output=capture,
        )
        if completed.returncode != 0:
            output = ""
            if capture:
                output = f" stdout: {completed.stdout.strip()} stderr: {completed.stderr.strip()}".strip()
            raise InstallError(f"Command failed ({completed.returncode}): {' '.join(str(part) for part in command)}{output}")
        return completed

    def check_codex_auth(self) -> None:
        if self.config.skip_auth_check:
            return
        completed = subprocess.run(
            [str(self.config.codex_bin), "login", "status"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            output = (completed.stdout + completed.stderr).strip() or "<empty>"
            raise InstallError(f"Codex is installed but not authenticated. Run `codex login` first. Last output: {output}")

    def check_grok_auth(self) -> None:
        if self.config.skip_auth_check:
            return
        completed = subprocess.run(
            [str(self.config.grok_bin), "models"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            output = (completed.stdout + completed.stderr).strip() or "<empty>"
            raise InstallError(f"Grok Build is installed but not authenticated. Run `grok login` first. Last output: {output}")

    def is_managed_path(self, target: Path) -> bool:
        if target.is_file():
            return f"installed_by: {PROJECT_NAME}" in read_text(target)
        skill = target / "SKILL.md"
        if skill.is_file() and f"installed_by: {PROJECT_NAME}" in read_text(skill):
            return True
        server = target / "server.py"
        if server.is_file() and PROJECT_NAME in read_text(server):
            return True
        return False

    def backup_unmanaged_if_needed(self, target: Path) -> None:
        if not target.exists() or self.is_managed_path(target):
            return

        backup = Path(f"{target}.bak.{self.config.timestamp}")
        index = 1
        while backup.exists():
            backup = Path(f"{target}.bak.{self.config.timestamp}.{index}")
            index += 1

        self.info(f"Backing up existing {target} -> {backup}")
        shutil.move(str(target), str(backup))

    def render_template(self, src: Path, dest: Path) -> None:
        code_model_flag = f'-m "{self.config.codex_model}"' if self.config.codex_model else ""
        code_model_label = self.config.codex_model or "Codex config default"
        output_image_dir = self.config.output_dir / "images"
        replacements = {
            "__CODEX_BIN__": str(self.config.codex_bin),
            "__GROK_BIN__": str(self.config.grok_bin),
            "__OUTPUT_DIR__": str(self.config.output_dir),
            "__OUTPUT_IMAGE_DIR__": str(output_image_dir),
            "__ENABLE_WIKI_LOG__": self.config.enable_wiki_log,
            "__CODEX_MODEL__": self.config.codex_model,
            "__CODEX_MODEL_FLAG__": code_model_flag,
            "__CODEX_MODEL_LABEL__": code_model_label,
            "__GROK_MODEL__": self.config.grok_model,
        }
        text = read_text(src)
        for old, new in replacements.items():
            text = text.replace(old, new)
        dest.write_text(text, encoding="utf-8")

    def write_runtime_config(self) -> None:
        config_dir = self.config.claude_home / "agent-router"
        config_dir.mkdir(parents=True, exist_ok=True)
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        values = {
            "OUTPUT_DIR": str(self.config.output_dir),
            "ENABLE_WIKI_LOG": self.config.enable_wiki_log,
            "CODEX_MODEL": self.config.codex_model,
            "GROK_MODEL": self.config.grok_model,
            "CODEX_BIN": str(self.config.codex_bin),
            "GROK_BIN": str(self.config.grok_bin),
        }

        shell_lines = [f"# Generated by {PROJECT_NAME} install.py on {generated_at}"]
        shell_lines.extend(f"export {key}={sh_quote(value)}" for key, value in values.items())
        (config_dir / "config.sh").write_text("\n".join(shell_lines) + "\n", encoding="utf-8")

        ps_lines = [f"# Generated by {PROJECT_NAME} install.py on {generated_at}"]
        ps_lines.extend(f"$env:{key} = {ps_quote(value)}" for key, value in values.items())
        (config_dir / "config.ps1").write_text("\n".join(ps_lines) + "\n", encoding="utf-8")

    def install_router_files(self) -> None:
        skill_target = self.config.claude_home / "skills" / "agent-router"
        self.backup_unmanaged_if_needed(skill_target)
        skill_target.mkdir(parents=True, exist_ok=True)
        self.render_template(self.config.repo_root / "skills" / "agent-router" / "SKILL.md", skill_target / "SKILL.md")

        agents_target = self.config.claude_home / "agents"
        agents_target.mkdir(parents=True, exist_ok=True)
        for agent in AGENTS:
            target = agents_target / f"{agent}.md"
            self.backup_unmanaged_if_needed(target)
            self.render_template(self.config.repo_root / "agents" / f"{agent}.md", target)

        mcp_target = self.config.claude_home / "mcp-servers" / "grok-mcp"
        self.backup_unmanaged_if_needed(mcp_target)
        mcp_target.mkdir(parents=True, exist_ok=True)
        for name in ("server.py", "test_server.py", "selftest_stdio.py", "requirements.txt"):
            shutil.copy2(self.config.repo_root / "mcp-servers" / "grok-mcp" / name, mcp_target / name)

        self.write_runtime_config()

    def install_grok_venv(self) -> None:
        if self.config.skip_venv:
            self.warn("Skipping Grok MCP venv install because AGENT_ROUTER_SKIP_VENV=1.")
            return

        mcp_target = self.config.claude_home / "mcp-servers" / "grok-mcp"
        self.run_subprocess([self.config.python_bin, "-m", "venv", mcp_target / ".venv"])
        venv_python = venv_python_path(mcp_target, self.config.platform_name)
        self.run_subprocess([venv_python, "-m", "pip", "install", "--upgrade", "pip"])
        self.run_subprocess([venv_python, "-m", "pip", "install", "-r", mcp_target / "requirements.txt"])

    def register_mcp_servers(self) -> None:
        if self.config.skip_mcp_add:
            self.warn("Skipping Claude MCP registration because AGENT_ROUTER_SKIP_MCP_ADD=1.")
            return

        mcp_target = self.config.claude_home / "mcp-servers" / "grok-mcp"
        venv_python = venv_python_path(mcp_target, self.config.platform_name)
        if not is_executable_file(venv_python, self.config.platform_name):
            raise InstallError(f"Missing venv Python: {venv_python}")

        remove_codex = [self.config.claude_bin, "mcp", "remove", "-s", "user", "codex"]
        remove_grok = [self.config.claude_bin, "mcp", "remove", "-s", "user", "grok"]
        subprocess.run([str(part) for part in remove_codex], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([str(part) for part in remove_grok], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        commands = build_mcp_add_commands(
            claude_bin=self.config.claude_bin,
            codex_bin=self.config.codex_bin,
            grok_bin=self.config.grok_bin,
            grok_model=self.config.grok_model,
            mcp_target=mcp_target,
            platform_name=self.config.platform_name,
        )
        self.run_subprocess(commands["codex"])
        self.run_subprocess(commands["grok"])

        completed = self.run_subprocess([self.config.claude_bin, "mcp", "list"], capture=True)
        list_output = (completed.stdout or "") + (completed.stderr or "")
        print(list_output, end="" if list_output.endswith("\n") else "\n")
        if not re.search(r"codex.*connected", list_output, re.IGNORECASE):
            raise InstallError("Claude MCP list did not show codex as Connected.")
        if not re.search(r"grok.*connected", list_output, re.IGNORECASE):
            raise InstallError("Claude MCP list did not show grok as Connected.")

    def run(self) -> None:
        self.info("Checking authentication.")
        self.check_codex_auth()
        self.check_grok_auth()

        self.info(f"Installing router files into {self.config.claude_home}.")
        self.install_router_files()

        self.info("Installing Grok MCP Python environment.")
        self.install_grok_venv()

        self.info("Registering Claude MCP servers.")
        self.register_mcp_servers()

        self.info("Install complete.")
        print("\nUsage:")
        print("  1. Restart Claude Code if it was already running.")
        print("  2. Ask Claude to use the agent-router skill for multi-engine delegation.")
        print("  3. Available agents: codex-exec, codex-fast, codex-image, codex-review, grok-research, grok-coder.")
        print(
            "\nRisk reminder: Codex execution uses danger-full-access. "
            "Only delegate tasks after understanding the local filesystem and network risk."
        )


def build_config(args: argparse.Namespace, env: Mapping[str, str] | None = None) -> InstallConfig:
    env = env or os.environ
    repo_root = Path(__file__).resolve().parent
    detected_platform = platform.system()
    platform_name = detected_platform if args.platform == "auto" else args.platform
    if platform_name not in SUPPORTED_PLATFORMS:
        raise InstallError(f"Unsupported OS: {platform_name}. Supported: macOS, Linux, and Windows.")

    home = home_from_env(env, platform_name)
    config_file = Path(env.get("CONFIG_FILE", "") or repo_root / "config.local.sh")
    config_values = load_config_file(config_file, env)

    claude_home = expand_path(config_value("CLAUDE_HOME", str(home / ".claude"), config_values, env), home, repo_root, env)
    output_dir = expand_path(
        config_value("OUTPUT_DIR", str(home / ".agent-router" / "output"), config_values, env),
        home,
        repo_root,
        env,
    )
    enable_wiki_log = config_value("ENABLE_WIKI_LOG", "false", config_values, env).lower()
    if enable_wiki_log not in {"true", "false"}:
        raise InstallError("ENABLE_WIKI_LOG must be true or false.")

    claude_bin = resolve_cli(
        env_name="CLAUDE_BIN",
        command_name="claude",
        install_hint="Install Claude Code: https://code.claude.com/docs/en/setup",
        configured=config_value("CLAUDE_BIN", "", config_values, env),
        home=home,
        cwd=repo_root,
        env=env,
        platform_name=platform_name,
    )
    codex_bin = resolve_cli(
        env_name="CODEX_BIN",
        command_name="codex",
        install_hint="Install Codex CLI: https://developers.openai.com/codex/cli",
        configured=config_value("CODEX_BIN", "", config_values, env),
        home=home,
        cwd=repo_root,
        env=env,
        platform_name=platform_name,
    )
    grok_bin = resolve_cli(
        env_name="GROK_BIN",
        command_name="grok",
        install_hint="Install Grok Build: https://docs.x.ai/build/overview",
        configured=config_value("GROK_BIN", "", config_values, env),
        home=home,
        cwd=repo_root,
        env=env,
        platform_name=platform_name,
    )
    python_bin = resolve_python_bin(config_value("PYTHON_BIN", "", config_values, env), home, repo_root, env, platform_name)

    return InstallConfig(
        repo_root=repo_root,
        platform_name=platform_name,
        home=home,
        claude_home=claude_home,
        output_dir=output_dir,
        enable_wiki_log=enable_wiki_log,
        codex_model=config_value("CODEX_MODEL", "", config_values, env),
        grok_model=config_value("GROK_MODEL", "grok-build", config_values, env) or "grok-build",
        claude_bin=claude_bin,
        codex_bin=codex_bin,
        grok_bin=grok_bin,
        python_bin=python_bin,
        timestamp=_now_timestamp(),
        dry_run=args.dry_run,
        skip_auth_check=env.get("AGENT_ROUTER_SKIP_AUTH_CHECK") == "1",
        skip_venv=env.get("AGENT_ROUTER_SKIP_VENV") == "1",
        skip_mcp_add=env.get("AGENT_ROUTER_SKIP_MCP_ADD") == "1",
    )


def dry_run_payload(config: InstallConfig) -> dict[str, object]:
    mcp_target = config.claude_home / "mcp-servers" / "grok-mcp"
    return {
        "dry_run": True,
        "platform": config.platform_name,
        "home": str(config.home),
        "claude_home": str(config.claude_home),
        "output_dir": str(config.output_dir),
        "claude_bin": str(config.claude_bin),
        "codex_bin": str(config.codex_bin),
        "grok_bin": str(config.grok_bin),
        "python_bin": str(config.python_bin),
        "venv_python": str(venv_python_path(mcp_target, config.platform_name)),
        "mcp_add_commands": build_mcp_add_commands(
            claude_bin=config.claude_bin,
            codex_bin=config.codex_bin,
            grok_bin=config.grok_bin,
            grok_model=config.grok_model,
            mcp_target=mcp_target,
            platform_name=config.platform_name,
        ),
        "skips": {
            "auth_check": config.skip_auth_check,
            "venv": config.skip_venv,
            "mcp_add": config.skip_mcp_add,
        },
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install claude-multiengine-router into the user-scoped Claude home.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve config and print the planned install without writing files.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output for --dry-run.")
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
        if config.dry_run:
            payload = dry_run_payload(config)
            if args.json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                print(f"[{PROJECT_NAME}] Dry run only. No files will be written.")
                for key, value in payload.items():
                    if key != "mcp_add_commands":
                        print(f"{key}: {value}")
            return 0

        Installer(config, json_mode=args.json).run()
        return 0
    except InstallError as exc:
        print(f"[{PROJECT_NAME}] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
