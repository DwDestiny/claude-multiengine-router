#!/usr/bin/env bash
# Input: this repository plus installed claude/codex/grok/Python CLIs. Output: user-scoped Claude router install.
# Pos: Unix thin wrapper for the cross-platform Python installer.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON="$PYTHON_BIN"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON="$(command -v python)"
else
  printf '[claude-multiengine-router] ERROR: Python 3 is required. Install Python 3 or set PYTHON_BIN.\n' >&2
  exit 1
fi

exec "$PYTHON" "$SCRIPT_DIR/install.py" "$@"
