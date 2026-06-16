# Phase 2 Windows Support Report

## Architecture Decision

Phase 2 uses option (b): a cross-platform Python installer (`install.py`) and uninstaller (`uninstall.py`), with `install.sh`, `uninstall.sh`, `install.ps1`, and `uninstall.ps1` as thin wrappers.

Reasoning:

- The project already requires Python 3 for the Grok MCP server, so Python adds no meaningful prerequisite for target users.
- One Python implementation avoids duplicating backup, template rendering, venv, auth-check, and `claude mcp add` logic across Bash and PowerShell.
- PowerShell still remains the native Windows entrypoint for user ergonomics and execution-policy guidance.
- Python `subprocess` argument lists handle paths with spaces and Windows backslashes without shell-quoting rewrites.

## Windows-Specific Handling

- CLI detection:
  - `install.ps1` uses `Get-Command` to locate `python3`, `python`, or `py -3`.
  - `install.py` uses `shutil.which`, with `where.exe` fallback on Windows for CLI discovery.
- Home directory:
  - Windows defaults to `%USERPROFILE%\.claude`.
  - macOS/Linux continue to use `$HOME/.claude`.
- Virtualenv:
  - Windows MCP runtime uses `.venv\Scripts\python.exe`.
  - macOS/Linux continue to use `.venv/bin/python`.
- MCP registration:
  - Commands are built as argv lists, not shell strings.
  - `claude mcp add -s user codex -- <codex> mcp-server`.
  - `claude mcp add -s user grok -e GROK_BIN=<grok> -e GROK_MODEL=<model> -- <venv-python> <server.py>`.
- Grok MCP path resolution:
  - `GROK_BIN` wins.
  - Existing Windows `.cmd` / `.exe` paths are accepted.
  - PATH lookup falls back to `where.exe grok`.
  - Missing Grok still returns an install/login-oriented error.
- Runtime config:
  - Installs both `config.sh` and `config.ps1` under `~/.claude/agent-router/`.

## Self-Test Coverage

- Python unit/smoke tests cover Windows home resolution, Windows venv interpreter path, MCP argv construction, Windows-safe backup names, dry-run JSON, and temp-HOME fake CLI install.
- Existing Bash temp-HOME tests now exercise the Unix wrappers calling Python.
- Grok MCP unit tests cover Windows `GROK_BIN=.cmd` and `where.exe` fallback by mocking platform behavior.

## P3 True Windows Verification

These still require a real Windows machine or GitHub Actions Windows runner:

- `.\install.ps1 --dry-run --json` under Windows PowerShell 5.1 and PowerShell 7.
- `.\install.ps1` with fake `claude.cmd`, `codex.cmd`, `grok.cmd`, and real Windows temp `%USERPROFILE%`.
- Actual `python -m venv` creation and `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Real `claude mcp add -s user ...` behavior on Windows Claude Code.
- Real `claude mcp list` connected-output format on Windows.
- PowerShell execution-policy UX on a clean user profile.
