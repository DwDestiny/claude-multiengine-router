# Phase 2 / Phase 3 TODO

## Phase 2: Windows

Implemented in `docs/phase-2-windows.md`:

- Chose the cross-platform Python installer architecture.
- Added PowerShell thin wrappers for native Windows entrypoints.
- Kept the same user-scoped `.claude` layout on Windows, rooted at `%USERPROFILE%`.
- Added Windows-safe backup names and timestamp formatting.
- Added local fake-CLI tests for portable installer behavior.

Remaining Windows work is now Phase 3 CI / true-machine verification.

## Phase 3: CI and Release

Implemented in Phase 3 release prep:

- Added GitHub Actions CI for Ubuntu, macOS, and Windows.
- Added Unix shell syntax checks and Windows PowerShell parser checks.
- Added Python installer tests, Grok MCP unittest, fake-CLI install dry-run, and private-leak gate.
- Added contribution guide, `.gitignore` release hygiene, and GitHub issue/PR templates.

Still deferred to release owner:

- Record the README demo GIF.
- Create and push the real GitHub repository.
- Replace README `<you>` placeholders with the real owner/repo.
- Run a true integration test for real `claude mcp add` on a disposable Claude profile.
- Add versioned changelog and release tags.
- Decide later whether to publish a Homebrew tap or one-line remote installer.
