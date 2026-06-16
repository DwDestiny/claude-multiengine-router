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

- Add CI for `bash -n`, shell smoke tests, and Python unit tests.
- Add GitHub Actions Windows smoke tests with fake `.cmd` CLIs.
- Add PowerShell syntax checks once `pwsh` is available in CI.
- Add shell linting once script behavior stabilizes.
- Add release packaging checks for missing placeholders and private path leaks.
- Add integration-test documentation for real `claude mcp add` runs on a disposable Claude profile.
- Add versioned changelog and release tags.
- Decide whether to publish a Homebrew tap or a one-line remote installer.
