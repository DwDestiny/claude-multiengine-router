# Grok MCP Folder Guide

## Boundary

This package exposes official Grok Build as stdio MCP tools for Claude Code.

## Owned Files

- `server.py`: MCP implementation and Grok command construction.
- `test_server.py`: unit tests for parsing, binary resolution, environment setup, and command construction.
- `selftest_stdio.py`: JSON-RPC smoke test for initialized tool listing.
- `requirements.txt`: runtime dependency list.

## Rules

- `GROK_BIN` must win over PATH lookup; Windows PATH fallback should work through `where.exe grok`.
- `GROK_MODEL` defaults to `grok-build`.
- Preserve clear login/install errors; do not attempt user login.
- Do not add direct references to private local paths.
