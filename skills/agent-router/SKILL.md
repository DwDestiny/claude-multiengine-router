---
name: agent-router
description: Multi-engine subagent router. Use when Claude Code should stay in control while delegating implementation, review, image generation, or research tasks to Codex and official Grok Build through local proxy agents and MCP tools.
metadata:
  version: 1.0.0
  created: 2026-06-16
  installed_by: claude-multiengine-router
---

# Agent Router

## Role

Claude Code is the controller, architect, product lead, and router.
Concrete execution can be delegated to locally installed external engines through proxy agents in `~/.claude/agents/` and MCP tools registered under the user scope.

Each proxy agent is intentionally thin:

1. Receive a fully serialized task from Claude.
2. Run the relevant CLI with structured output enabled.
3. Wait for completion.
4. Return a structured result for Claude to verify and decide on.

## Engines

### Codex CLI

- Primary execution engine for coding, refactoring, debugging, tests, and code review.
- Default model: Codex user configuration. Optional install-time override: `CODEX_MODEL=__CODEX_MODEL__`.
- Required sandbox mode for unattended execution: `danger-full-access`.
- Non-interactive coding: `__CODEX_BIN__ exec`.
- Review: `__CODEX_BIN__ exec review` or `__CODEX_BIN__ review`.
- MCP server registration: `__CODEX_BIN__ mcp-server`.

### Official Grok Build

- Secondary execution engine for research, current web/X context, and coding fallback or best-of-n comparison.
- Default model: `__GROK_MODEL__`.
- Headless one-shot mode: `__GROK_BIN__ -p "<prompt>" --output-format json --always-approve`.
- Built-in web search is enabled by default; ask explicitly for X discussion when needed.
- This project uses official Grok Build, not third-party Grok CLIs.

## Routing Matrix

| Task | Engine | Proxy agent | Typical command |
|---|---|---|---|
| Architecture, product decisions, decomposition, final acceptance | Claude Code | none | none |
| Coding, refactoring, debugging, tests | Codex | `codex-exec` | `codex exec -s danger-full-access` |
| Small bounded coding tasks | Codex fast mode | `codex-fast` | `codex exec --enable fast_mode` |
| Coding fallback or best-of-n comparison | Grok Build | `grok-coder` | `grok -p ... --best-of-n` |
| Code review | Codex | `codex-review` | `codex exec review` |
| Image/material generation | Codex image generation | `codex-image` | `codex exec` prompt-triggered image generation |
| Research, search, real-time context, X discussion | Grok Build | `grok-research` | `grok -p ...` |

## Decision Tree

1. Is the task mostly about deciding what to build, reviewing direction, planning, or making a tradeoff? Claude should handle it directly.
2. Is it implementation work?
   - Complex or multi-file implementation: use `codex-exec`.
   - Small, bounded, low-risk implementation: use `codex-fast`.
   - Codex is stuck or the user asks for comparison: use `grok-coder`.
3. Is it review of existing changes? Use `codex-review`.
4. Is it an image or static visual asset? Use `codex-image`.
5. Does it need current external information, community sentiment, web search, or X context? Use `grok-research`.

## Context Serialization

Native Claude subagents do not inherit live context automatically. External engines do not either. Always serialize the task with this template:

```text
## Task
<one sentence objective>

## Context
<absolute paths, relevant rules, known facts, dependencies>

## Constraints
<what must not be touched, safety limits, technology boundaries>

## Acceptance
<how to verify completion, including commands when possible>

## Output
<what should be returned: changed files, conclusions, artifact paths>
```

## Result Schema

Proxy agents should return this shape:

```json
{
  "engine": "codex | grok",
  "model": "configured model or actual model",
  "status": "success | partial | failed",
  "summary": "what happened",
  "artifacts": ["absolute paths to changed files or generated assets"],
  "raw_output_path": "/tmp/<id>.md",
  "notes": "blockers, verification notes, or reroute suggestions"
}
```

## Monitoring Rules

- The proxy agent must wait for the external engine to finish before returning.
- Do not report success until the output file or artifact exists and the requested acceptance check has been run or explicitly marked as skipped.
- For Codex, prefer `--json -o /tmp/<label>.md` so the final message is durable.
- For Grok, prefer `--output-format json` and preserve stdout/stderr when reporting failures.

## Optional Wiki Logging

`ENABLE_WIKI_LOG` is rendered as `__ENABLE_WIKI_LOG__` for this installation.

When enabled, research agents may include a reminder that reusable findings should be written to the user's knowledge base. This is disabled by default for open-source installs.

## Safety Boundary

This router intentionally enables high-trust local automation. Codex execution uses `danger-full-access`, which can read and write arbitrary local paths and use the network. Claude must confirm destructive operations, migrations, credential work, production access, or anything that touches unique user data before delegating.
