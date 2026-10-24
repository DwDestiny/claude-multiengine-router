# Mac mini CI boundary

Trusted macOS compilation, unit/CLI tests and deterministic fixtures run on the dedicated `githubci` account using `[self-hosted, macOS, ARM64, macmini, headless]`. Fixed-data browser screenshots or offscreen rendering also require `offscreen-render`. Work, temporary files and caches use the dedicated external CI volume. Jobs share a global execution slot across repository registrations.

Native desktop interaction, IME, system dialogs, window lifecycle, physical hardware acceptance and desktop performance require computer use on the primary Mac in a genuine user session. A passing CI job covers its executed assertions only. Offscreen images and image comparisons do not prove visual approval or real-device acceptance; baseline changes require review.

The root-owned `/Library/Application Support/DwMacCI/RUNNER-CONTRACT.md` and `CAPABILITIES.json` describe the host contract. Root-owned hooks admit exact workflow files and job keys, reject foreign pull requests and unknown jobs, and serialize Worker execution. These are admission rules and a cooperative lock, not an OS sandbox. Review code changes to admitted workflows. Do not add desktop jobs or real model calls under an existing admitted key.

Use fake Claude/provider fixtures in CI. Do not load personal profiles, credentials or projects; the CI account has no administrator membership or passwordless sudo. Only the dedicated native launcher has the approved external-volume privacy authorization. Hosted fallback remains available for foreign-fork PRs where the workflow supports them. Linux and Windows routing is unchanged.

Termvia `perf-bench` is disabled in GitHub because it launches real native windows. Run its existing bench command on the primary Mac during the relevant version acceptance. `ui-screens` is a manual headless-browser artifact aid and may run on the mini; no per-page screenshot document maintenance is introduced here.
