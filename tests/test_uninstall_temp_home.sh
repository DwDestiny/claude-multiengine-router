#!/usr/bin/env bash
# Input: repository uninstall script plus a fake installed tree. Output: backup/removal assertions.
# Pos: non-destructive smoke test for wrapper uninstall behavior.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cmr-uninstall-test.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

TEST_HOME="$TMP_ROOT/home"
CLAUDE_HOME="$TEST_HOME/.claude"
mkdir -p \
  "$CLAUDE_HOME/skills/agent-router" \
  "$CLAUDE_HOME/agents" \
  "$CLAUDE_HOME/mcp-servers/grok-mcp" \
  "$CLAUDE_HOME/agent-router"

printf 'installed_by: claude-multiengine-router\n' >"$CLAUDE_HOME/skills/agent-router/SKILL.md"
for agent in codex-exec codex-fast codex-image codex-review grok-research grok-coder; do
  printf 'installed_by: claude-multiengine-router\n' >"$CLAUDE_HOME/agents/$agent.md"
done
printf 'claude-multiengine-router\n' >"$CLAUDE_HOME/mcp-servers/grok-mcp/server.py"
printf 'export OUTPUT_DIR=/tmp/router\n' >"$CLAUDE_HOME/agent-router/config.sh"

export HOME="$TEST_HOME"
export AGENT_ROUTER_SKIP_MCP_REMOVE=1

bash "$ROOT/uninstall.sh"

test ! -e "$CLAUDE_HOME/skills/agent-router"
test ! -e "$CLAUDE_HOME/agents/codex-exec.md"
test ! -e "$CLAUDE_HOME/mcp-servers/grok-mcp"
test ! -e "$CLAUDE_HOME/agent-router"

BACKUP_DIR="$(find "$CLAUDE_HOME/backups" -maxdepth 1 -type d -name 'claude-multiengine-router-uninstall-*' | head -n 1)"
test -n "$BACKUP_DIR"
find "$BACKUP_DIR" -type f | grep -q 'codex-exec.md'
find "$BACKUP_DIR" -type f | grep -q 'SKILL.md'
find "$BACKUP_DIR" -type f | grep -q 'server.py'

echo "temp HOME uninstall smoke test passed"
