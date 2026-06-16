# Tests Folder Guide

## Boundary

Tests here must be safe for developer machines and CI. They should avoid touching real `~/.claude`.

## Rules

- Use temporary `HOME` and, for Windows logic, temporary `USERPROFILE` values for installer tests.
- Use fake CLIs for install smoke tests unless a test explicitly opts into real integration.
- Keep assertions focused on copy/render/backup behavior, path replacement, Windows path handling, dry-run output, and private-reference removal.
