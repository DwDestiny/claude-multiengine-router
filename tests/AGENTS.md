# Tests Folder Guide

## Boundary

Tests here must be safe for developer machines and CI. They should avoid touching real `~/.claude`.

## Owned Files

- `test_python_installer.py`: cross-platform unit and smoke checks for installer/uninstaller helpers.
- `test_install_temp_home.sh`: Unix wrapper install smoke test with fake CLIs and temp home.
- `test_uninstall_temp_home.sh`: Unix wrapper uninstall smoke test with fake installed files and backups.
- `ci_install_dry_run.py`: CI-friendly dry-run smoke test with fake CLIs and no writes.
- `private_leak_gate.py`: release gate for private local markers.

## Rules

- Use temporary `HOME` and, for Windows logic, temporary `USERPROFILE` values for installer tests.
- Use fake CLIs for install smoke tests unless a test explicitly opts into real integration.
- Keep assertions focused on copy/render/backup behavior, path replacement, Windows path handling, dry-run output, and private-reference removal.
