#!/usr/bin/env python3
"""Input: repository or install-tree paths. Output: failure on private release markers.
Pos: release gate that keeps open-source artifacts free of personal local residues.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".serena",
    "backups",
    "build",
    "dist",
    "logs",
    "tmp",
    "temp",
}


def private_markers() -> list[tuple[str, bytes]]:
    return [
        ("absolute personal home path", ("/" + "Users" + "/" + "dw").encode("utf-8")),
        ("old private desktop project path", ("Desktop" + "/" + "claude").encode("utf-8")),
        ("private Chinese user alias", ("老" + "党").encode("utf-8")),
        ("private wiki shortcut", ("~" + "/" + "wiki").encode("utf-8")),
        ("private memory context marker", ("claude" + "-mem").encode("utf-8")),
    ]


def should_skip(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    return any(part in EXCLUDED_DIRS for part in relative.parts)


def iter_files(root: Path):
    if root.is_file():
        yield root
        return

    for path in root.rglob("*"):
        if should_skip(path, root):
            continue
        if path.is_file():
            yield path


def scan_path(root: Path) -> tuple[int, list[str]]:
    markers = private_markers()
    scanned = 0
    findings: list[str] = []

    for path in iter_files(root):
        scanned += 1
        try:
            content = path.read_bytes()
        except OSError as exc:
            findings.append(f"{path}: unable to read file: {exc}")
            continue

        for label, marker in markers:
            index = content.find(marker)
            if index == -1:
                continue
            line = content.count(b"\n", 0, index) + 1
            try:
                display_path = path.relative_to(root).as_posix()
            except ValueError:
                display_path = path.as_posix()
            findings.append(f"{display_path}:{line}: {label}")

    return scanned, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail if release artifacts contain private local markers.")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to scan.")
    args = parser.parse_args(argv)

    total_scanned = 0
    all_findings: list[str] = []
    for raw_path in args.paths:
        root = Path(raw_path).resolve()
        if not root.exists():
            all_findings.append(f"{raw_path}: path does not exist")
            continue
        scanned, findings = scan_path(root)
        total_scanned += scanned
        all_findings.extend(f"{root.name}/{finding}" for finding in findings)

    if all_findings:
        print("Private leak gate failed. Remove private local markers before release:", file=sys.stderr)
        for finding in all_findings:
            print(f"  {finding}", file=sys.stderr)
        return 1

    print(f"Private leak gate passed: scanned {total_scanned} files; no private markers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
