# Tests Folder Guide

## Boundary

Tests here must be safe for developer machines and CI. They should avoid touching real `~/.claude`.

## Rules

- Use temporary `HOME` values for installer tests.
- Use fake CLIs for install smoke tests unless a test explicitly opts into real integration.
- Keep assertions focused on copy/render/backup behavior, path replacement, and private-reference removal.
