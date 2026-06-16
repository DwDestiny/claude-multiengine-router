# Input: optional user edits before install. Output: config values consumed by install.py.
# Pos: copy to config.local.sh or export these variables before running install.sh/install.ps1/install.py.

# Where generated images and other durable agent artifacts should go.
export OUTPUT_DIR="${OUTPUT_DIR:-$HOME/.agent-router/output}"

# Optional research knowledge-base reminder. Default is false for open-source users.
export ENABLE_WIKI_LOG="${ENABLE_WIKI_LOG:-false}"

# Empty means "use the user's Codex CLI configuration".
# Example: export CODEX_MODEL="gpt-5.5"
export CODEX_MODEL="${CODEX_MODEL:-}"

# Official Grok Build model used by the Grok MCP server and proxy agents.
export GROK_MODEL="${GROK_MODEL:-grok-build}"

# Advanced optional overrides if the CLIs are not on PATH:
# export CODEX_BIN="/absolute/path/to/codex"
# export GROK_BIN="/absolute/path/to/grok"
# export CLAUDE_BIN="/absolute/path/to/claude"
# export PYTHON_BIN="/absolute/path/to/python3"
