#!/usr/bin/env python3
"""Input: local MCP server.py. Output: initialize/tools-list self-test JSON.
Pos: durable stdio JSON-RPC smoke test for this Grok MCP server.

Run with:
    .venv/bin/python selftest_stdio.py
"""

from __future__ import annotations

import json
import select
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "bin" / "python"
SERVER = ROOT / "server.py"


def _read_message(proc: subprocess.Popen[bytes], timeout: float = 10.0) -> dict:
    assert proc.stdout is not None
    ready, _, _ = select.select([proc.stdout], [], [], timeout)
    if not ready:
        stderr = ""
        if proc.stderr is not None:
            err_ready, _, _ = select.select([proc.stderr], [], [], 0)
            if err_ready:
                stderr = proc.stderr.read1(8192).decode("utf-8", errors="replace")
        raise TimeoutError(f"timed out waiting for server response; stderr={stderr!r}")

    line = proc.stdout.readline()
    if not line:
        stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr is not None else ""
        raise RuntimeError(f"server closed stdout before sending a response; stderr={stderr!r}")
    return json.loads(line.decode("utf-8"))


def _write_message(proc: subprocess.Popen[bytes], payload: dict) -> None:
    body = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    assert proc.stdin is not None
    proc.stdin.write(body)
    proc.stdin.flush()


def main() -> int:
    python = PYTHON if PYTHON.exists() else Path(sys.executable)
    proc = subprocess.Popen(
        [str(python), str(SERVER)],
        cwd=str(ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _write_message(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "grok-mcp-selftest", "version": "0.1.0"},
                },
            },
        )
        initialize = _read_message(proc)

        _write_message(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        _write_message(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = _read_message(proc)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

    output = {"initialize": initialize, "tools_list": tools}
    print(json.dumps(output, ensure_ascii=False, indent=2))

    names = {tool["name"] for tool in tools.get("result", {}).get("tools", [])}
    expected = {"grok_research", "grok_code"}
    missing = sorted(expected - names)
    if missing:
        print(f"missing tools: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
