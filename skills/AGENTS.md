# Skills Folder Guide

## Boundary

This folder contains Claude skill templates installed under `~/.claude/skills/`.

## Rules

- Keep the router skill focused on routing, context serialization, result schema, monitoring, and safety boundaries.
- Do not hardcode user-specific paths or private workflows.
- If new placeholders are added, update `install.sh` rendering and the temp-HOME smoke test.
