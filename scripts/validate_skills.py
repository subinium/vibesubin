#!/usr/bin/env python3
"""Validate the vibesubin skill pack against its own promises.

Eleven checks, all blocking:

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

7. Every SKILL.md frontmatter must declare a ``mutates`` field with a
   bracketed list of tokens drawn from {direct, external}. Empty list is
   fine (diagnosis-only or umbrella). The field is a contract the umbrella
   reads at sweep time.

8. ``mutates`` must be consistent with the skill's category:
   - sweep specialists must NOT include ``external`` (sweep is read-only)
   - the three pure-diagnosis sweep workers must have an empty list
   - the six editable sweep workers must include ``direct``
   - non-sweep skills are free to include ``external``

9. Every references file (``references/*.md`` under any skill) must be at
   most 500 lines too. Without this cap, content can hide in references
   to circumvent the SKILL.md cap.

10. Every ``/<skill-name>`` reference inside backticks must point to a
    skill that exists in this pack. Catches stale renames, typos, and
    references to skills that were never built.

11. Every SKILL.md frontmatter must declare ``name``, ``description``, and
    ``allowed-tools`` (or be the umbrella, which uses ``context`` and
    ``agent`` instead of ``allowed-tools``). Description must be 1-1024
    chars per the plugin spec.

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

# Hard cap on SKILL.md length. Documented in MAINTENANCE.md and
# docs/PHILOSOPHY.md. Enforced here so the rule has teeth.
SKILL_MD_LINE_CAP = 500

# Same cap applies per-references-file. Without this, content can hide in
# references to dodge the SKILL.md cap. References are still meant to be
# detailed (progressive disclosure is load-bearing) but not unbounded.
REFERENCES_FILE_LINE_CAP = 500

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
# documented as a regression in the contributor docs.
HARSH_MODE_HEADING = re.compile(r"^## Harsh mode — no hedging\s*$", re.MULTILINE)

# Sweep-mode marker. Editable workers must check for this string in their
# sweep-mode section; without it they default to full edit behavior.
SWEEP_MARKER = "sweep=read-only"

# Frontmatter parsers. Frontmatter is ``---``-delimited at the top of every
# SKILL.md. We do not pull in PyYAML — the field shapes here are simple
# enough for regex.
FRONTMATTER_BLOCK = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FRONTMATTER_FIELD = re.compile(r"^([a-zA-Z][a-zA-Z0-9_-]*):\s*(.*)$", re.MULTILINE)
MUTATES_LIST = re.compile(r"^\s*\[(.*?)\]\s*$")

# A ``/<skill-name>`` reference inside backticks. We exclude colons so
# cross-plugin references like ``/codex:rescue`` are skipped (those are
# external, not vibesubin-internal).
SKILL_INVOCATION = re.compile(r"`/([a-z][a-z0-9-]+)`")

ALLOWED_MUTATES_TOKENS = {"direct", "external"}

# The nine specialists the umbrella launches in its parallel sweep block.
# Sweep is read-only by invariant; ``external`` is forbidden in this set.
SWEEP_SPECIALISTS = {
    "refactor-verify",
    "audit-security",
    "fight-repo-rot",
    "write-for-ai",
    "setup-ci",
    "manage-secrets-env",
    "project-conventions",
    "manage-assets",
    "unify-design",
}

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

# Pure-diagnosis sweep workers — they may launch in the sweep but never
# edit, regardless of the marker. Their ``mutates`` must be empty.
PURE_DIAGNOSIS_WORKERS = {
    "audit-security",
    "fight-repo-rot",
    "manage-assets",
}

# Skills that exist outside the sweep entirely (umbrella + wrappers +
# process). These may carry ``external`` in mutates.
NON_SWEEP_SKILLS = {
    "vibesubin",
    "codex-fix",
    "ship-cycle",
}

# Every skill the pack ships, used to validate ``/<name>`` invocation
# references in backticks.
KNOWN_SKILLS = SWEEP_SPECIALISTS | NON_SWEEP_SKILLS

# Skills that legitimately use ``context`` + ``agent`` instead of
# ``allowed-tools`` in their frontmatter.
TASK_AGENT_SKILLS = {"vibesubin"}


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
        mutates: list[str] | None,
    ) -> None:
        self.name = name
        self.line_count = line_count
        self.harsh_ok = harsh_ok
        self.sweep_marker_applicable = sweep_marker_applicable
        self.sweep_marker_ok = sweep_marker_ok
        self.asset_path_count = asset_path_count
        self.mutates = mutates

    def format_verbose(self) -> str:
        if self.sweep_marker_applicable:
            sweep = "sweep-marker=" + ("ok" if self.sweep_marker_ok else "MISSING")
        else:
            sweep = "sweep-marker=n/a"
        harsh = "harsh=" + ("ok" if self.harsh_ok else "MISSING")
        if self.mutates is None:
            mutates_str = "mutates=MISSING"
        else:
            mutates_str = (
                f"mutates=[{','.join(self.mutates)}]" if self.mutates else "mutates=[]"
            )
        return (
            f"{self.name}: {self.line_count}/{SKILL_MD_LINE_CAP} lines, "
            f"{harsh}, {sweep}, {mutates_str}, asset-paths={self.asset_path_count}"
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
            continue
        found.append(token)
    seen: set[str] = set()
    ordered: list[str] = []
    for p in found:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered


def extract_skill_invocations(text: str) -> list[str]:
    """Return every ``/<skill-name>`` reference inside backticks."""
    seen: set[str] = set()
    ordered: list[str] = []
    for m in SKILL_INVOCATION.finditer(text):
        name = m.group(1)
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def parse_frontmatter(text: str) -> dict[str, str] | None:
    """Return frontmatter as a flat dict of raw string values, or None if absent."""
    match = FRONTMATTER_BLOCK.match(text)
    if not match:
        return None
    block = match.group(1)
    fields: dict[str, str] = {}
    for line_match in FRONTMATTER_FIELD.finditer(block):
        key = line_match.group(1)
        value = line_match.group(2).rstrip()
        fields[key] = value
    return fields


def parse_mutates(raw: str) -> tuple[list[str] | None, str | None]:
    """Parse ``mutates`` raw value. Returns (list, error) — error is None on success."""
    list_match = MUTATES_LIST.match(raw)
    if not list_match:
        return None, "mutates must be a bracketed list (e.g., `mutates: [direct]`)"
    inner = list_match.group(1).strip()
    if not inner:
        return [], None
    tokens = [t.strip() for t in inner.split(",")]
    bad = [t for t in tokens if t not in ALLOWED_MUTATES_TOKENS]
    if bad:
        return (
            None,
            f"mutates contains invalid token(s) {bad!r}; "
            f"allowed tokens are {sorted(ALLOWED_MUTATES_TOKENS)}",
        )
    return tokens, None


def count_lines(path: Path) -> int:
    """Return the number of newline-terminated lines in a file."""
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
            SkillReport(str(rel_name), 0, False, False, False, 0, None),
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

    # Frontmatter checks
    frontmatter = parse_frontmatter(text)
    mutates_value: list[str] | None = None

    if frontmatter is None:
        violations.append(f"{rel_name}: SKILL.md missing frontmatter block")
    else:
        # Check required fields
        for required in ("name", "description"):
            if required not in frontmatter:
                violations.append(
                    f"{rel_name}: frontmatter missing required field '{required}'"
                )
        if "name" in frontmatter and frontmatter["name"] != skill_dir.name:
            violations.append(
                f"{rel_name}: frontmatter name {frontmatter['name']!r} "
                f"does not match directory {skill_dir.name!r}"
            )
        if "description" in frontmatter:
            desc_len = len(frontmatter["description"])
            if not (1 <= desc_len <= 1024):
                violations.append(
                    f"{rel_name}: frontmatter description length {desc_len} "
                    f"outside 1-1024 char range"
                )
        if (
            "allowed-tools" not in frontmatter
            and skill_dir.name not in TASK_AGENT_SKILLS
        ):
            violations.append(
                f"{rel_name}: frontmatter missing 'allowed-tools' "
                f"(use 'context: fork' + 'agent: ...' for task agents)"
            )

        # Mutates check
        if "mutates" not in frontmatter:
            violations.append(
                f"{rel_name}: frontmatter missing 'mutates' field "
                f"(declare as `mutates: [direct]`, `mutates: [direct, external]`, "
                f"or `mutates: []`)"
            )
        else:
            tokens, error = parse_mutates(frontmatter["mutates"])
            if error is not None:
                violations.append(f"{rel_name}: {error}")
            else:
                mutates_value = tokens
                violations.extend(
                    _validate_mutates_consistency(rel_name, skill_dir.name, tokens)
                )

    # References file size cap (Check 9)
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref_path in sorted(refs_dir.iterdir()):
            if not ref_path.is_file():
                continue
            if ref_path.suffix != ".md":
                continue
            ref_lines = count_lines(ref_path)
            if ref_lines > REFERENCES_FILE_LINE_CAP:
                violations.append(
                    f"{rel_name}/references/{ref_path.name}: "
                    f"{ref_lines} lines exceeds {REFERENCES_FILE_LINE_CAP}-line cap"
                )

    # Skill-invocation cross-check (Check 10).
    # Only flag candidates that LOOK like vibesubin skill invocations —
    # a hyphenated identifier, or the literal `vibesubin`. This avoids
    # false positives on backtick URL-paths (`/pricing`, `/docs`, `/api`).
    for invoked in extract_skill_invocations(text):
        looks_like_skill = invoked == "vibesubin" or "-" in invoked
        if not looks_like_skill:
            continue
        if invoked not in KNOWN_SKILLS:
            violations.append(
                f"{rel_name}: backtick reference to /{invoked} but no such skill "
                f"in pack (known: {sorted(KNOWN_SKILLS)})"
            )

    return (
        violations,
        SkillReport(
            name=str(rel_name),
            line_count=line_count,
            harsh_ok=harsh_ok,
            sweep_marker_applicable=sweep_applicable,
            sweep_marker_ok=sweep_ok,
            asset_path_count=len(promised),
            mutates=mutates_value,
        ),
    )


def _validate_mutates_consistency(
    rel_name: object, name: str, tokens: list[str]
) -> list[str]:
    """Cross-check ``mutates`` against the skill's category."""
    violations: list[str] = []
    in_sweep = name in SWEEP_SPECIALISTS
    if in_sweep and "external" in tokens:
        violations.append(
            f"{rel_name}: mutates includes 'external' but {name} is in the sweep "
            f"(sweep workers cannot mutate external systems — invariant #6)"
        )
    if name in PURE_DIAGNOSIS_WORKERS and tokens:
        violations.append(
            f"{rel_name}: mutates is non-empty but {name} is pure-diagnosis "
            f"(must declare `mutates: []`)"
        )
    if name in EDITABLE_SWEEP_WORKERS and "direct" not in tokens:
        violations.append(
            f"{rel_name}: mutates missing 'direct' but {name} edits in direct-call mode"
        )
    return violations


def validate_manifests(repo_root: Path) -> list[str]:
    """Return violations for marketplace.json <-> plugin.json version sync."""
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
        f"actual file, every SKILL.md and references file is "
        f"<={SKILL_MD_LINE_CAP} lines, harsh-mode + sweep marker intact, "
        f"frontmatter mutates contract enforced, manifests synced"
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
