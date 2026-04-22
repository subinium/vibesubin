#!/usr/bin/env python3
"""Validate the vibesubin skill pack against its own promises.

Six checks, all blocking:

1. Every backtick-quoted path mentioned in a SKILL.md that looks like an
   internal asset (references/, scripts/, templates/) must exist on disk.
   If a SKILL.md links to a file that is not present, the promise is empty
   and the pack loses trust.

2. Every SKILL.md must be at most 500 lines. Claude Code partially reads
   long SKILL.md files, silently dropping tail sections. When a file grows
   past the cap, extract content into references/*.md and replace with
   one-line links from SKILL.md.

3. Every SKILL.md must contain the canonical heading
   ``## Harsh mode — no hedging``. Partial coverage is a regression —
   ``/vibesubin harsh`` feels like balanced mode for the uncovered worker.

4. The six editable sweep workers must mention ``sweep=read-only`` at least
   once in their SKILL.md. Without the marker, they default to full edit
   behavior during ``/vibesubin`` sweeps, which is incorrect.

5. The two plugin manifests must agree on the plugin version:
   ``.claude-plugin/marketplace.json`` and
   ``plugins/vibesubin/.claude-plugin/plugin.json``.

6. Backtick-quoted internal asset paths must not escape the skill
   directory via ``..`` components.

Exit code:
  0 — every check passes
  1 — one or more checks failed

Usage:
  python scripts/validate_skills.py
  python scripts/validate_skills.py --verbose
  python scripts/validate_skills.py --root /path/to/alt-repo
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent

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

# Canonical harsh-mode heading. Must match exactly — partial coverage is
# documented as a regression in CLAUDE.md.
HARSH_MODE_HEADING = re.compile(r"^## Harsh mode — no hedging\s*$", re.MULTILINE)

# Sweep-mode marker. Editable workers must check for this string in their
# sweep-mode section; without it they default to full edit behavior.
SWEEP_MARKER = "sweep=read-only"

# The six workers the umbrella launches with editable potential. They are
# enumerated explicitly (not derived at runtime) so the invariant is
# visible in source. Derived from the umbrella launch block in
# plugins/vibesubin/skills/vibesubin/SKILL.md.
EDITABLE_SWEEP_WORKERS = {
    "refactor-verify",
    "setup-ci",
    "write-for-ai",
    "manage-secrets-env",
    "project-conventions",
    "unify-design",
}


class SkillReport:
    """Per-skill verification summary used in verbose output."""

    def __init__(
        self,
        name: str,
        line_count: int,
        harsh_ok: bool,
        sweep_marker_applicable: bool,
        sweep_marker_ok: bool,
        asset_path_count: int,
    ) -> None:
        self.name = name
        self.line_count = line_count
        self.harsh_ok = harsh_ok
        self.sweep_marker_applicable = sweep_marker_applicable
        self.sweep_marker_ok = sweep_marker_ok
        self.asset_path_count = asset_path_count

    def format_verbose(self) -> str:
        if self.sweep_marker_applicable:
            sweep = "sweep-marker=" + ("ok" if self.sweep_marker_ok else "MISSING")
        else:
            sweep = "sweep-marker=n/a"
        harsh = "harsh=" + ("ok" if self.harsh_ok else "MISSING")
        return (
            f"{self.name}: {self.line_count}/{SKILL_MD_LINE_CAP} lines, "
            f"{harsh}, {sweep}, asset-paths={self.asset_path_count}"
        )


def extract_promised_paths(skill_md: Path) -> list[str]:
    """Return every backtick-quoted internal asset path mentioned in a SKILL.md."""
    text = skill_md.read_text(encoding="utf-8")
    found: list[str] = []
    for match in BACKTICK.finditer(text):
        token = match.group(1).strip()
        if not token.startswith(INTERNAL_PREFIXES):
            continue
        if not token.endswith(INTERNAL_EXTS):
            # `references/patterns.md` is tracked; `references/` alone is not.
            continue
        found.append(token)
    seen: set[str] = set()
    ordered: list[str] = []
    for p in found:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def count_lines(path: Path) -> int:
    """Return the number of newline-terminated lines in a file.

    Matches the count ``wc -l`` would report; a trailing non-newline line is
    not counted, which is fine because SKILL.md files always end with a
    newline.
    """
    with path.open("rb") as fh:
        return sum(1 for _ in fh)


def _validate_asset_path(
    skill_dir: Path, rel: str, repo_root: Path
) -> tuple[bool, str | None]:
    """Return (ok, error_message). Catches path-traversal before existence."""
    target = skill_dir / rel
    try:
        resolved = target.resolve(strict=False)
        skill_root = skill_dir.resolve()
    except (OSError, RuntimeError):
        return (
            False,
            f"{skill_dir.relative_to(repo_root)}/{rel} (path resolution error)",
        )
    if not str(resolved).startswith(str(skill_root) + "/"):
        return (
            False,
            f"{skill_dir.relative_to(repo_root)}/{rel} (path-traversal attempt)",
        )
    if not target.exists():
        return False, f"{skill_dir.relative_to(repo_root)}/{rel}"
    return True, None


def validate_skill(skill_dir: Path, repo_root: Path) -> tuple[list[str], SkillReport]:
    """Return (violations, report) for a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    rel_name = (
        skill_dir.relative_to(repo_root)
        if skill_dir.is_relative_to(repo_root)
        else skill_dir
    )
    if not skill_md.exists():
        return (
            [f"{rel_name}: SKILL.md missing"],
            SkillReport(str(rel_name), 0, False, False, False, 0),
        )

    violations: list[str] = []
    text = skill_md.read_text(encoding="utf-8")

    line_count = count_lines(skill_md)
    if line_count > SKILL_MD_LINE_CAP:
        violations.append(
            f"{rel_name}/SKILL.md: "
            f"{line_count} lines exceeds {SKILL_MD_LINE_CAP}-line cap "
            f"(extract tail sections into references/*.md)"
        )

    harsh_ok = HARSH_MODE_HEADING.search(text) is not None
    if not harsh_ok:
        violations.append(
            f"{rel_name}: harsh-mode section missing — "
            f"add '## Harsh mode — no hedging'"
        )

    sweep_applicable = skill_dir.name in EDITABLE_SWEEP_WORKERS
    sweep_ok = SWEEP_MARKER in text if sweep_applicable else True
    if sweep_applicable and not sweep_ok:
        violations.append(
            f"{rel_name}: {SWEEP_MARKER} marker missing — "
            f"editable workers must check for the marker"
        )

    promised = extract_promised_paths(skill_md)
    for rel in promised:
        ok, error = _validate_asset_path(skill_dir, rel, repo_root)
        if not ok and error is not None:
            violations.append(error)

    return (
        violations,
        SkillReport(
            name=str(rel_name),
            line_count=line_count,
            harsh_ok=harsh_ok,
            sweep_marker_applicable=sweep_applicable,
            sweep_marker_ok=sweep_ok,
            asset_path_count=len(promised),
        ),
    )


def validate_manifests(repo_root: Path) -> list[str]:
    """Return violations for marketplace.json <-> plugin.json version sync.

    Missing files are reported as violations so the check fails loud rather
    than silently skipping.
    """
    marketplace = repo_root / ".claude-plugin" / "marketplace.json"
    plugin = repo_root / "plugins" / "vibesubin" / ".claude-plugin" / "plugin.json"

    if not marketplace.exists():
        return [f"manifest missing: {marketplace.relative_to(repo_root)}"]
    if not plugin.exists():
        return [f"manifest missing: {plugin.relative_to(repo_root)}"]

    try:
        marketplace_data = json.loads(marketplace.read_text(encoding="utf-8"))
        plugin_data = json.loads(plugin.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"manifest parse error: {exc}"]

    plugins = marketplace_data.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        return ["marketplace.json: plugins[] empty or missing"]

    marketplace_version = plugins[0].get("version")
    plugin_version = plugin_data.get("version")
    if marketplace_version != plugin_version:
        return [
            f"version drift: marketplace.json={marketplace_version!r} "
            f"but plugin.json={plugin_version!r}"
        ]
    return []


def run(repo_root: Path, verbose: bool) -> int:
    plugins_dir = repo_root / "plugins"
    if not plugins_dir.exists():
        print(f"no plugins directory at {plugins_dir}", file=sys.stderr)
        return 1

    skill_dirs = sorted(plugins_dir.glob("*/skills/*"))
    if not skill_dirs:
        print(f"no skills found under {plugins_dir}", file=sys.stderr)
        return 1

    total_violations: list[str] = []
    for skill_dir in skill_dirs:
        if not skill_dir.is_dir():
            continue
        violations, report = validate_skill(skill_dir, repo_root)
        if violations:
            print(f"\n{skill_dir.name}: {len(violations)} violation(s)")
            for v in violations:
                print(f"  x {v}")
            total_violations.extend(violations)
        elif verbose:
            print(f"  ok  {report.format_verbose()}")

    manifest_violations = validate_manifests(repo_root)
    if manifest_violations:
        print("\nmanifests:")
        for v in manifest_violations:
            print(f"  x {v}")
        total_violations.extend(manifest_violations)
    elif verbose:
        print("  ok  manifests synced")

    print()
    if total_violations:
        print(
            f"FAIL — {len(total_violations)} violation(s) across "
            f"{len(skill_dirs)} skills"
        )
        return 1
    print(
        f"OK — every promise in {len(skill_dirs)} skills resolves to an "
        f"actual file, every SKILL.md is <={SKILL_MD_LINE_CAP} lines, "
        f"harsh-mode section present, sweep markers intact, manifests synced"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help="Repository root to validate (defaults to this file's parent).",
    )
    args = parser.parse_args(argv)
    repo_root = args.root.resolve()
    return run(repo_root=repo_root, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
