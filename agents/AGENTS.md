# Agents Folder Guide

## Boundary

This folder contains Claude proxy agent templates. `install.sh` renders placeholders such as `__CODEX_BIN__`, `__GROK_BIN__`, `__OUTPUT_DIR__`, and model values into the user's `~/.claude/agents/` directory.

## Rules

- Keep prompts English-first and open-source safe.
- Do not include private local paths, personal wiki rules, or machine-specific assumptions.
- Proxy agents should delegate to external CLIs and return structured results; they should not become full implementation guides.
