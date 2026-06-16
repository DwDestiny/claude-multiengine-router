#!/usr/bin/env python3
"""Input: MCP stdio calls. Output: Grok Build research/code tools.
Pos: portable stdio MCP server for the claude-multiengine-router project.

Start command:
    .venv/bin/python server.py

Claude registration shape:
    claude mcp add -s user grok -e GROK_BIN=/path/to/grok -- .venv/bin/python server.py
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


DEFAULT_GROK_MODEL = "grok-build"
RESEARCH_TIMEOUT_SECONDS = 180
CODE_TIMEOUT_SECONDS = 600
MAX_CAPTURE_CHARS = 12000

mcp = FastMCP("grok-mcp")


class GrokOutputError(ValueError):
    """Raised when Grok stdout is not the expected official JSON shape."""


def _truncate(text: str | None, limit: int = MAX_CAPTURE_CHARS) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


def resolve_grok_bin() -> str:
    """Resolve official Grok Build CLI path from env, PATH, or a clear error."""
    env_bin = os.environ.get("GROK_BIN", "").strip()
    if env_bin:
        candidate = Path(env_bin).expanduser()
        if candidate.exists() and (platform.system() == "Windows" or os.access(candidate, os.X_OK)):
            return str(candidate)
        raise FileNotFoundError(
            f"GROK_BIN points to a missing or non-executable file: {candidate}. "
            "Install Grok Build or export GROK_BIN=/absolute/path/to/grok."
        )

    path_bin = shutil.which("grok")
    if path_bin:
        return path_bin

    if platform.system() == "Windows":
        try:
            completed = subprocess.run(
                ["where.exe", "grok"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            completed = None
        if completed and completed.returncode == 0:
            for line in completed.stdout.splitlines():
                candidate = line.strip()
                if candidate:
                    return candidate

    raise FileNotFoundError(
        "Grok Build CLI was not found. Install it from https://x.ai/cli, "
        "then run `grok login`, or export GROK_BIN=/absolute/path/to/grok."
    )


def grok_model() -> str:
    return os.environ.get("GROK_MODEL", DEFAULT_GROK_MODEL).strip() or DEFAULT_GROK_MODEL


def parse_grok_stdout(stdout: str) -> dict[str, Any]:
    """Normalize Grok JSON/stdout variants into the server payload shape."""
    raw_stdout = stdout.strip()
    if not raw_stdout:
        raise GrokOutputError("empty Grok stdout")

    try:
        payload = json.loads(raw_stdout)
    except json.JSONDecodeError:
        return {"output_text": stdout}

    if (
        isinstance(payload, dict)
        and payload.get("ok") is True
        and isinstance(payload.get("data"), dict)
        and isinstance(payload["data"].get("output_text"), str)
    ):
        data = dict(payload["data"])
        data.setdefault("tool_calls", [])
        return data

    if isinstance(payload, dict):
        if payload.get("ok") is False or "error" in payload:
            error = payload.get("error") or payload.get("message") or payload
            if not isinstance(error, str):
                error = json.dumps(error, ensure_ascii=False)
            raise GrokOutputError(f"Grok returned error: {_truncate(error, 1000)}")

        if isinstance(payload.get("text"), str):
            data = dict(payload)
            data["output_text"] = payload["text"]
            data.setdefault("finish_reason", payload.get("stopReason"))
            data.setdefault("tool_calls", [])
            return data

        if isinstance(payload.get("output_text"), str):
            data = dict(payload)
            data.setdefault("tool_calls", [])
            return data

    return {"output_text": json.dumps(payload, ensure_ascii=False)}


def is_login_error(stderr: str, stdout: str) -> bool:
    combined = f"{stderr}\n{stdout}".lower()
    return (
        "grok login" in combined
        or "not logged in" in combined
        or "not authenticated" in combined
        or "login required" in combined
        or ("authentication" in combined and "login" in combined)
    )


def build_research_prompt(query: str, recency_days: int = 0) -> str:
    recency = ""
    if recency_days and recency_days > 0:
        recency = (
            f"\nFreshness requirement: prioritize sources from the last {recency_days} days; "
            "older sources may only be used as background."
        )

    return f"""You are a one-shot Grok research executor.

User query:
{query}

Requirements:
- Use web_search to gather evidence and include source links.
- If the request depends on real-time events, releases, prices, market sentiment, or community feedback, search relevant X discussions as well.
- Separate verified facts, inferences, and unresolved uncertainty.
- Be concise, and preserve clickable links.{recency}
"""


def build_research_command(query: str, recency_days: int = 0) -> list[str]:
    return [
        resolve_grok_bin(),
        "-p",
        build_research_prompt(query, recency_days),
        "--output-format",
        "json",
        "--always-approve",
        "--max-turns",
        "8",
        "-m",
        grok_model(),
    ]


def build_code_command(cwd: str, task: str, best_of_n: int = 1, check: bool = False) -> list[str]:
    command = [
        resolve_grok_bin(),
        "-p",
        task,
        "--output-format",
        "json",
        "--always-approve",
        "--cwd",
        cwd,
    ]
    if best_of_n > 1:
        command.extend(["--best-of-n", str(best_of_n)])
    if check:
        command.append("--check")
    command.extend(["-m", grok_model()])
    return command


def build_grok_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(base_env if base_env is not None else os.environ)
    tmp_dir = Path(tempfile.gettempdir())
    env.setdefault("GROK_HOME", str(tmp_dir / "grok-mcp-home"))
    env.setdefault("GROK_LEADER_SOCKET", str(tmp_dir / "grok-mcp-leader.sock"))
    env.setdefault("GROK_CLAUDE_MCPS_ENABLED", "0")
    env.setdefault("GROK_CURSOR_MCPS_ENABLED", "0")
    env.setdefault("GROK_MANAGED_MCPS_ENABLED", "0")

    default_auth = Path.home() / ".grok" / "auth.json"
    if "GROK_AUTH_PATH" not in env and default_auth.exists():
        env["GROK_AUTH_PATH"] = str(default_auth)

    Path(env["GROK_HOME"]).mkdir(parents=True, exist_ok=True)
    return env


def _error_payload(
    message: str,
    command: list[str],
    *,
    exit_code: int | None = None,
    stderr: str = "",
    stdout: str = "",
    timeout_seconds: int | None = None,
    elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": False,
        "error": message,
        "command": command,
    }
    if exit_code is not None:
        payload["exit_code"] = exit_code
    if timeout_seconds is not None:
        payload["timeout_seconds"] = timeout_seconds
    if elapsed_seconds is not None:
        payload["elapsed_seconds"] = round(elapsed_seconds, 3)
    if stderr:
        payload["stderr"] = _truncate(stderr)
    if stdout:
        payload["stdout"] = _truncate(stdout)
    return payload


def run_grok(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=build_grok_env(),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return _error_payload(
            f"Grok command timed out after {timeout_seconds}s",
            command,
            stdout=stdout,
            stderr=stderr,
            timeout_seconds=timeout_seconds,
            elapsed_seconds=elapsed,
        )
    except FileNotFoundError as exc:
        return _error_payload(str(exc), command)
    except OSError as exc:
        return _error_payload(f"Failed to start Grok: {exc}", command)

    elapsed = time.monotonic() - start
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""

    if completed.returncode != 0:
        message = "Run `grok login` before using this MCP server." if is_login_error(stderr, stdout) else "Grok command failed"
        return _error_payload(
            message,
            command,
            exit_code=completed.returncode,
            stderr=stderr,
            stdout=stdout,
            elapsed_seconds=elapsed,
        )

    try:
        data = parse_grok_stdout(stdout)
    except GrokOutputError as exc:
        return _error_payload(
            str(exc),
            command,
            stderr=stderr,
            stdout=stdout,
            elapsed_seconds=elapsed,
        )

    return {
        "ok": True,
        "output_text": data.get("output_text", ""),
        "model": data.get("model") or grok_model(),
        "finish_reason": data.get("finish_reason"),
        "tool_calls": data.get("tool_calls", []),
        "elapsed_seconds": round(elapsed, 3),
        "stderr": _truncate(stderr),
    }


@mcp.tool(
    name="grok_research",
    description=(
        "Research, search, real-time information, and X discussion lookup through official Grok Build. "
        "Use for external current context and source links; independently verify critical facts."
    ),
)
def grok_research(query: str, recency_days: int = 0) -> dict[str, Any]:
    """Run one-shot Grok research with web_search/X guidance."""
    if not query or not query.strip():
        return _error_payload("query must be a non-empty string", ["grok"])
    recency = max(int(recency_days or 0), 0)
    try:
        command = build_research_command(query.strip(), recency)
    except FileNotFoundError as exc:
        return _error_payload(str(exc), ["grok"])
    return run_grok(command, RESEARCH_TIMEOUT_SECONDS)


@mcp.tool(
    name="grok_code",
    description=(
        "Coding fallback and best-of-n executor through official Grok Build CLI. "
        "It may modify files under cwd, so callers must confirm scope and risk first."
    ),
)
def grok_code(task: str, cwd: str, best_of_n: int = 1, check: bool = False) -> dict[str, Any]:
    """Run official grok-build for a bounded coding task."""
    try:
        grok_bin = resolve_grok_bin()
    except FileNotFoundError as exc:
        return _error_payload(str(exc), ["grok"])

    if not task or not task.strip():
        return _error_payload("task must be a non-empty string", [grok_bin])
    if not cwd or not cwd.strip():
        return _error_payload("cwd must be a non-empty string", [grok_bin])

    target = Path(cwd).expanduser().resolve()
    if not target.exists() or not target.is_dir():
        return _error_payload(f"cwd does not exist or is not a directory: {target}", [grok_bin])

    try:
        best = int(best_of_n)
    except (TypeError, ValueError):
        return _error_payload("best_of_n must be an integer >= 1", [grok_bin])
    if best < 1:
        return _error_payload("best_of_n must be an integer >= 1", [grok_bin])

    return run_grok(build_code_command(str(target), task.strip(), best, bool(check)), CODE_TIMEOUT_SECONDS)


if __name__ == "__main__":
    mcp.run(transport="stdio")
