# GitHub Folder Guide

## Boundary

This folder owns repository automation and collaboration templates for GitHub.

## Owned Files

- `workflows/ci.yml`: cross-platform release-readiness CI.
- `ISSUE_TEMPLATE/`: short issue templates for bug reports and feature requests.
- `pull_request_template.md`: PR checklist and release-safety prompts.

## Rules

- CI must use temporary homes and fake CLIs for installer checks; never touch a runner's real Claude profile.
- Keep private-leak checks release-focused and cross-platform.
- Keep templates concise and bilingual enough for English and Chinese contributors.
