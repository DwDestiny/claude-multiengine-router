#!/usr/bin/env bash
# Input: user-scoped Claude install. Output: backup then removal of router files and MCP registrations.
# Pos: conservative uninstaller for claude-multiengine-router.

set -euo pipefail

PROJECT_NAME="claude-multiengine-router"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

info() {
  printf '[%s] %s\n' "$PROJECT_NAME" "$*"
}

warn() {
  printf '[%s] WARNING: %s\n' "$PROJECT_NAME" "$*" >&2
}

backup_path() {
  local target="$1"
  [[ -e "$target" ]] || return 0
  mkdir -p "$BACKUP_DIR"
  local name
  name="$(printf '%s' "$target" | sed 's|^/||; s|/|__|g')"
  info "Backing up $target -> $BACKUP_DIR/$name"
  mv "$target" "$BACKUP_DIR/$name"
}

main() {
  case "$(uname -s)" in
    Darwin|Linux)
      ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      warn "Windows native uninstall is planned for Phase 2. If installed under WSL, run this script inside WSL."
      ;;
  esac

  CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
  BACKUP_DIR="$CLAUDE_HOME/backups/${PROJECT_NAME}-uninstall-$TIMESTAMP"

  backup_path "$CLAUDE_HOME/skills/agent-router"

  local agent
  for agent in codex-exec codex-fast codex-image codex-review grok-research grok-coder; do
    backup_path "$CLAUDE_HOME/agents/$agent.md"
  done

  backup_path "$CLAUDE_HOME/mcp-servers/grok-mcp"
  backup_path "$CLAUDE_HOME/agent-router"

  if [[ "${AGENT_ROUTER_SKIP_MCP_REMOVE:-0}" == "1" ]]; then
    warn "Skipping Claude MCP removal because AGENT_ROUTER_SKIP_MCP_REMOVE=1."
  elif command -v claude >/dev/null 2>&1; then
    claude mcp remove -s user codex >/dev/null 2>&1 || true
    claude mcp remove -s user grok >/dev/null 2>&1 || true
  else
    warn "Claude CLI not found; skipped MCP registration removal."
  fi

  info "Uninstall complete. Backup directory: $BACKUP_DIR"
}

main "$@"
