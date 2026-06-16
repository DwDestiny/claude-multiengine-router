# Phase 2 / Phase 3 TODO

## Phase 2: Windows

- Add native PowerShell installer and uninstaller.
- Validate Claude Code, Codex CLI, Grok Build, and Python path detection on Windows.
- Decide whether native Windows should support the same `~/.claude` layout or prefer WSL-first docs.
- Add Windows-safe backup paths and timestamp formatting.
- Add GitHub Actions Windows smoke tests with fake CLIs.

## Phase 3: CI and Release

- Add CI for `bash -n`, shell smoke tests, and Python unit tests.
- Add shell linting once script behavior stabilizes.
- Add release packaging checks for missing placeholders and private path leaks.
- Add integration-test documentation for real `claude mcp add` runs on a disposable Claude profile.
- Add versioned changelog and release tags.
- Decide whether to publish a Homebrew tap or a one-line remote installer.
