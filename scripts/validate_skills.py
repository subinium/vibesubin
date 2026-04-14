#!/usr/bin/env python3
"""Validate that every backtick-quoted path mentioned in a SKILL.md actually exists.

The vibesubin pack promises a set of references/, scripts/, templates/ files
inside each skill directory. If a SKILL.md links to a file that does not
exist, the promise is empty and the pack loses trust.

This validator walks every `plugins/*/skills/*/SKILL.md`, extracts every
backtick-quoted path that looks like it lives inside the skill's own
directory tree, and asserts the target is present on disk.

Exit code:
  0 — all references resolve
  1 — one or more missing

Usage:
  python scripts/validate_skills.py
  python scripts/validate_skills.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = REPO_ROOT / "plugins"

# A backtick-quoted path is considered an "internal asset" if it starts with
# one of these path components (relative to the skill directory) and ends
# with an extension we care about.
INTERNAL_PREFIXES = ("references/", "scripts/", "templates/")
INTERNAL_EXTS = (
    ".md",
    ".sh",
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".template",
)

# Regex: a backtick span whose content matches an internal path.
# We intentionally ignore backticks that contain spaces, command lines,
# or anything that obviously isn't a repo path.
BACKTICK = re.compile(r"`([^`\s]+)`")


def extract_promised_paths(skill_md: Path) -> list[str]:
    """Return every backtick-quoted internal asset path mentioned in a SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    found = []
    for match in BACKTICK.finditer(text):
        token = match.group(1).strip()
        if not token.startswith(INTERNAL_PREFIXES):
            continue
        if not token.endswith(INTERNAL_EXTS):
            # `references/patterns.md` is tracked; `references/` alone is not.
            # Only assert files, not directory mentions.
            continue
        found.append(token)
    # Dedupe while preserving order.
    seen = set()
    ordered = []
    for p in found:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def validate_skill(skill_dir: Path, verbose: bool) -> list[str]:
    """Return a list of missing file references inside a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.relative_to(REPO_ROOT)}: SKILL.md missing"]

    missing: list[str] = []
    promised = extract_promised_paths(skill_md)
    for rel in promised:
        target = skill_dir / rel
        if not target.exists():
            missing.append(f"{skill_dir.relative_to(REPO_ROOT)}/{rel}")
        elif verbose:
            print(f"  ok  {skill_dir.relative_to(REPO_ROOT)}/{rel}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not PLUGINS_DIR.exists():
        print(f"no plugins directory at {PLUGINS_DIR}", file=sys.stderr)
        return 1

    skill_dirs = sorted(PLUGINS_DIR.glob("*/skills/*"))
    if not skill_dirs:
        print(f"no skills found under {PLUGINS_DIR}", file=sys.stderr)
        return 1

    total_missing: list[str] = []
    for skill_dir in skill_dirs:
        if not skill_dir.is_dir():
            continue
        missing = validate_skill(skill_dir, verbose=args.verbose)
        if missing:
            print(f"\n{skill_dir.name}: {len(missing)} missing")
            for m in missing:
                print(f"  ✗ {m}")
            total_missing.extend(missing)
        elif args.verbose:
            print(f"\n{skill_dir.name}: all references present")

    print()
    if total_missing:
        print(
            f"FAIL — {len(total_missing)} promised assets missing across {len(skill_dirs)} skills"
        )
        return 1
    print(f"OK — every promise in {len(skill_dirs)} skills resolves to an actual file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
