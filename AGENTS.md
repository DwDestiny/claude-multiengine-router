# Project Guide

## Purpose

`claude-multiengine-router` packages a portable Claude Code setup where Claude remains the controller and delegates execution to Codex and official Grok Build through proxy agents and MCP servers.

## Structure

- `install.sh`: idempotent macOS/Linux installer. It detects CLIs, checks auth, backs up existing same-name files, renders templates, installs the Grok MCP venv, and registers MCP servers.
- `uninstall.sh`: conservative backup-then-remove uninstaller.
- `config.example.sh`: optional install-time configuration.
- `skills/agent-router/`: Claude skill template.
- `agents/`: Claude proxy agent templates.
- `mcp-servers/grok-mcp/`: Python stdio MCP server for official Grok Build.
- `tests/`: non-destructive installer smoke tests.
- `docs/`: roadmap and maintenance notes.

## Commands

```bash
bash -n install.sh uninstall.sh tests/test_install_temp_home.sh
bash tests/test_install_temp_home.sh
python3 -m unittest discover -s mcp-servers/grok-mcp -p 'test_*.py'
```

## Safety Rules

- Never modify the user's source `~/.claude` files while developing this repository.
- Installer tests must use a temporary `HOME` or explicit skip flags.
- Keep generated/user-local files out of git: `config.local.sh`, `.venv`, backups, caches.
- Preserve the explicit `danger-full-access` warning in README and agent docs.

## GEB Notes

For structural changes, update nearby folder guides first, then this root guide if the repository map changes. Important scripts and Python files should keep short `Input / Output / Pos` headers.
