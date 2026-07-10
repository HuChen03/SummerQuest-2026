#!/usr/bin/env python3
"""Create one A0 student directory from the reviewed public templates."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "students" / "_template"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="student's real name")
    parser.add_argument("--github", required=True, help="GitHub username")
    return parser.parse_args()


def validate_name(name: str) -> None:
    if not name or name.startswith("_") or any(char.isspace() for char in name):
        raise ValueError("--name must be a real name without spaces and cannot start with '_'")
    if any(char in name for char in ("/", "\\")):
        raise ValueError("--name cannot contain path separators")


def replace_tokens(directory: Path, name: str, github: str) -> None:
    replacements = {
        "<姓名>": name,
        "<同学真名>": name,
        "<GitHub ID>": github,
        "<填写真实姓名>": name,
        "<填写 GitHub username>": github,
    }
    for path in directory.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for source, target in replacements.items():
            text = text.replace(source, target)
        path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    name = args.name.strip()
    github = args.github.strip()
    validate_name(name)
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", github):
        raise ValueError("--github must be a valid GitHub username")

    destination = ROOT / "students" / name
    if destination.exists():
        raise FileExistsError(f"student directory already exists: {destination}")

    destination.mkdir()
    shutil.copy2(TEMPLATE / "PROFILE.md", destination / "PROFILE.md")
    shutil.copytree(TEMPLATE / "assignments" / "A0", destination / "assignments" / "A0")
    replace_tokens(destination, name, github)

    print(f"Created {destination.relative_to(ROOT)}")
    print(
        "Next: fill every remaining <...> placeholder and remove all "
        "[填写参考] blocks before opening the A0 PR."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
