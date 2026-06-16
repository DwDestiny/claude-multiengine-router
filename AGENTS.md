# Project Guide

## Purpose

`claude-multiengine-router` packages a portable Claude Code setup where Claude remains the controller and delegates execution to Codex and official Grok Build through proxy agents and MCP servers.

## Structure

- `install.py`: idempotent cross-platform installer. It detects CLIs, checks auth, backs up existing same-name files, renders templates, installs the Grok MCP venv, and registers MCP servers.
- `uninstall.py`: cross-platform backup-then-remove uninstaller.
- `install.sh` / `uninstall.sh`: Unix thin wrappers around the Python entrypoints.
- `install.ps1` / `uninstall.ps1`: Windows PowerShell thin wrappers around the Python entrypoints.
- `config.example.sh`: optional install-time configuration.
- `skills/agent-router/`: Claude skill template.
- `agents/`: Claude proxy agent templates.
- `mcp-servers/grok-mcp/`: Python stdio MCP server for official Grok Build.
- `tests/`: non-destructive installer smoke tests.
- `.github/`: CI workflow and issue/PR templates.
- `docs/`: roadmap and maintenance notes.
- `CONTRIBUTING.md`: contributor checks, style, and PR flow.

## Commands

```bash
bash -n install.sh uninstall.sh tests/test_install_temp_home.sh tests/test_uninstall_temp_home.sh
bash tests/test_install_temp_home.sh
bash tests/test_uninstall_temp_home.sh
python3 tests/test_python_installer.py
python3 -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'
python3 tests/ci_install_dry_run.py
python3 tests/private_leak_gate.py .
python3 -c 'import yaml, pathlib; yaml.safe_load(pathlib.Path(".github/workflows/ci.yml").read_text())'
```

## Safety Rules

- Never modify the user's source `~/.claude` files while developing this repository.
- Installer tests must use a temporary `HOME` / `USERPROFILE` or explicit skip flags.
- Keep generated/user-local files out of git: `config.local.sh`, `.venv`, backups, caches.
- Preserve the explicit `danger-full-access` warning in README and agent docs.

## GEB Notes

For structural changes, update nearby folder guides first, then this root guide if the repository map changes. Important scripts and Python files should keep short `Input / Output / Pos` headers.
