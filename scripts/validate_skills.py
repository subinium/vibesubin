#!/usr/bin/env python3
"""Validate the vibesubin skill pack against its own promises.

Two checks, both blocking:

1. Every backtick-quoted path mentioned in a SKILL.md that looks like an
   internal asset (references/, scripts/, templates/) must exist on disk.
   If a SKILL.md links to a file that is not present, the promise is empty
   and the pack loses trust.

2. Every SKILL.md must be at most 500 lines. Claude Code partially reads
   long SKILL.md files, silently dropping tail sections. When a file grows
   past the cap, extract content into references/*.md and replace with
   one-line links from SKILL.md.

Exit code:
  0 — every check passes
  1 — one or more checks failed

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

# Hard cap on SKILL.md length. Documented in CLAUDE.md, MAINTENANCE.md, and
# docs/PHILOSOPHY.md. Enforced here so the rule has teeth.
SKILL_MD_LINE_CAP = 500

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


def count_lines(path: Path) -> int:
    """Return the number of newline-terminated lines in a file.

    Matches the count `wc -l` would report; a trailing non-newline line is
    not counted, which is fine because SKILL.md files always end with a
    newline.
    """
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def validate_skill(skill_dir: Path, verbose: bool) -> list[str]:
    """Return a list of violations inside a single skill directory.

    Two categories of violation are reported here:
      - missing file references (backtick-quoted internal paths)
      - SKILL.md exceeding the line cap
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.relative_to(REPO_ROOT)}: SKILL.md missing"]

    violations: list[str] = []

    line_count = count_lines(skill_md)
    if line_count > SKILL_MD_LINE_CAP:
        violations.append(
            f"{skill_dir.relative_to(REPO_ROOT)}/SKILL.md: "
            f"{line_count} lines > {SKILL_MD_LINE_CAP} cap "
            f"(extract tail sections into references/*.md)"
        )
    elif verbose:
        print(
            f"  ok  {skill_dir.relative_to(REPO_ROOT)}/SKILL.md "
            f"({line_count}/{SKILL_MD_LINE_CAP} lines)"
        )

    promised = extract_promised_paths(skill_md)
    for rel in promised:
        target = skill_dir / rel
        if not target.exists():
            violations.append(f"{skill_dir.relative_to(REPO_ROOT)}/{rel}")
        elif verbose:
            print(f"  ok  {skill_dir.relative_to(REPO_ROOT)}/{rel}")
    return violations


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

    total_violations: list[str] = []
    for skill_dir in skill_dirs:
        if not skill_dir.is_dir():
            continue
        violations = validate_skill(skill_dir, verbose=args.verbose)
        if violations:
            print(f"\n{skill_dir.name}: {len(violations)} violation(s)")
            for v in violations:
                print(f"  ✗ {v}")
            total_violations.extend(violations)
        elif args.verbose:
            print(f"\n{skill_dir.name}: all checks pass")

    print()
    if total_violations:
        print(
            f"FAIL — {len(total_violations)} violation(s) across {len(skill_dirs)} skills"
        )
        return 1
    print(
        f"OK — every promise in {len(skill_dirs)} skills resolves to an actual file "
        f"and every SKILL.md is ≤{SKILL_MD_LINE_CAP} lines"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
