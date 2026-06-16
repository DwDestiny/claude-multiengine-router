#!/usr/bin/env bash
# Input: repository install script plus fake local CLIs. Output: temp-HOME install assertions.
# Pos: non-destructive smoke test for Phase 1 install rendering and copying.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/cmr-install-test.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

FAKE_BIN="$TMP_ROOT/bin"
TEST_HOME="$TMP_ROOT/home"
mkdir -p "$FAKE_BIN" "$TEST_HOME"

cat >"$FAKE_BIN/claude" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  --version)
    echo "claude-code test"
    ;;
  mcp)
    case "${2:-}" in
      add)
        echo "mcp add ${*:3}" >>"${CLAUDE_MCP_LOG:?}"
        ;;
      list)
        printf 'codex: Connected\n'
        printf 'grok: Connected\n'
        ;;
      remove)
        echo "mcp remove ${*:3}" >>"${CLAUDE_MCP_LOG:?}"
        ;;
      *)
        echo "unsupported claude mcp command: ${2:-}" >&2
        exit 2
        ;;
    esac
    ;;
  *)
    echo "unsupported claude command: ${1:-}" >&2
    exit 2
    ;;
esac
FAKE

cat >"$FAKE_BIN/codex" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  --version)
    echo "codex-cli test"
    ;;
  login)
    if [[ "${2:-}" == "status" ]]; then
      echo "Logged in"
    else
      echo "unsupported codex login command" >&2
      exit 2
    fi
    ;;
  exec)
    if [[ "$*" == *"AGENT_ROUTER_LOGIN_PROBE"* ]]; then
      echo "ok"
    else
      echo "codex exec probe"
    fi
    ;;
  mcp-server)
    echo "codex mcp server"
    ;;
  *)
    echo "unsupported codex command: ${1:-}" >&2
    exit 2
    ;;
esac
FAKE

cat >"$FAKE_BIN/grok" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  --version)
    echo "grok test"
    ;;
  models)
    printf 'grok-build\n'
    ;;
  -p|--single)
    printf '{"ok":true,"data":{"output_text":"ok","model":"grok-build","finish_reason":"stop","tool_calls":[]}}\n'
    ;;
  login)
    echo "login stub"
    ;;
  *)
    echo "unsupported grok command: ${1:-}" >&2
    exit 2
    ;;
esac
FAKE

chmod +x "$FAKE_BIN/claude" "$FAKE_BIN/codex" "$FAKE_BIN/grok"

export HOME="$TEST_HOME"
export PATH="$FAKE_BIN:$PATH"
export CLAUDE_MCP_LOG="$TMP_ROOT/mcp.log"
export AGENT_ROUTER_SKIP_VENV=1
export AGENT_ROUTER_SKIP_MCP_ADD=1
export OUTPUT_DIR="$TEST_HOME/router-output"
export ENABLE_WIKI_LOG=false
export CODEX_MODEL="test-codex-model"
export GROK_MODEL="grok-build"

bash "$ROOT/install.sh"

test -f "$TEST_HOME/.claude/skills/agent-router/SKILL.md"
test -f "$TEST_HOME/.claude/agents/codex-exec.md"
test -f "$TEST_HOME/.claude/agents/grok-coder.md"
test -f "$TEST_HOME/.claude/mcp-servers/grok-mcp/server.py"
test -f "$TEST_HOME/.claude/agent-router/config.sh"

grep -q "$FAKE_BIN/codex" "$TEST_HOME/.claude/agents/codex-exec.md"
grep -q "$FAKE_BIN/grok" "$TEST_HOME/.claude/agents/grok-coder.md"
grep -q "$TEST_HOME/router-output/images" "$TEST_HOME/.claude/agents/codex-image.md"
grep -q "ENABLE_WIKI_LOG=false" "$TEST_HOME/.claude/agent-router/config.sh"

if rg -n "/Users/dw|Desktop/claude|老党|~/wiki|~/.claude/CLAUDE.md" "$TEST_HOME/.claude/skills/agent-router" "$TEST_HOME/.claude/agents" "$TEST_HOME/.claude/mcp-servers/grok-mcp"; then
  echo "found private local references after install" >&2
  exit 1
fi

if rg -n "__CODEX_BIN__|__GROK_BIN__|__OUTPUT_DIR__|__GROK_MODEL__|__CODEX_MODEL_FLAG__|__CODEX_MODEL_LABEL__" "$TEST_HOME/.claude/skills/agent-router" "$TEST_HOME/.claude/agents"; then
  echo "found unreplaced template placeholders after install" >&2
  exit 1
fi

echo "temp HOME install smoke test passed"
