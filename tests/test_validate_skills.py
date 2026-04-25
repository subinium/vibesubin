"""Unit tests for ``scripts/validate_skills.py``.

Each test builds a minimal fixture tree on ``tmp_path`` that mirrors the
real repo layout::

    <root>/
      .claude-plugin/marketplace.json
      plugins/<plugin>/.claude-plugin/plugin.json
      plugins/<plugin>/skills/<skill>/SKILL.md
      plugins/<plugin>/skills/<skill>/references/...

then invokes the validator via ``main(argv=[...])`` and asserts on
(exit code, captured stdout). The tests do not touch the real plugin
tree — keeping fixture-based invariants independent of the evolving
shipping skills.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

import pytest

# Make ``scripts/`` importable as a package root so tests can call
# ``validate_skills.main`` directly. This avoids subprocess overhead and
# lets pytest's ``capsys`` capture output cleanly.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_skills  # noqa: E402  (sys.path mutation intentional)


# --------------------------------------------------------------------------- #
# Fixture builders
# --------------------------------------------------------------------------- #


def _write_manifests(
    root: Path,
    marketplace_version: str = "0.0.1",
    plugin_version: str = "0.0.1",
    plugin_dir: str = "vibesubin",
) -> None:
    """Create both plugin manifests under ``root`` with the given versions."""
    marketplace_dir = root / ".claude-plugin"
    marketplace_dir.mkdir(parents=True, exist_ok=True)
    (marketplace_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "name": plugin_dir,
                "plugins": [
                    {
                        "name": plugin_dir,
                        "source": f"./plugins/{plugin_dir}",
                        "version": marketplace_version,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    plugin_manifest_dir = root / "plugins" / plugin_dir / ".claude-plugin"
    plugin_manifest_dir.mkdir(parents=True, exist_ok=True)
    (plugin_manifest_dir / "plugin.json").write_text(
        json.dumps({"name": plugin_dir, "version": plugin_version}),
        encoding="utf-8",
    )


def _write_skill(
    root: Path,
    name: str,
    *,
    body: str,
    plugin: str = "vibesubin",
    extra_files: dict[str, str] | None = None,
) -> Path:
    """Create a SKILL.md plus any extra files under the skill directory."""
    skill_dir = root / "plugins" / plugin / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    if not body.endswith("\n"):
        body += "\n"
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    for rel, contents in (extra_files or {}).items():
        target = skill_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8")
    return skill_dir


# A minimal SKILL.md that passes every check when assets exist.
# The skill name `good-skill` is not in any of the validator's category
# sets, so it is treated as a generic non-sweep skill (mutates: [] is fine).
GOOD_BODY = """\
---
name: good-skill
description: fixture skill
mutates: []
allowed-tools: Read
---

# good-skill

Some prose.

## Harsh mode — no hedging

Harsh bullet list here.

## References

- `references/notes.md` — exists in this fixture.
"""

# An editable-sweep-worker body: names a file plus the sweep=read-only marker.
EDITABLE_SWEEP_BODY = """\
---
name: refactor-verify
description: fixture clone
mutates: [direct]
allowed-tools: Read Edit
---

# refactor-verify

## Sweep mode — read-only audit

When the umbrella passes the `sweep=read-only` marker, produce findings only.

## Harsh mode — no hedging

Harsh bullet list.

## References

- `references/patterns.md`
"""

# A pure-diagnosis sweep worker — must declare mutates: [].
PURE_DIAGNOSIS_BODY = """\
---
name: fight-repo-rot
description: fixture clone
mutates: []
allowed-tools: Read
---

# fight-repo-rot

Pure diagnosis. No sweep marker mentioned anywhere.

## Harsh mode — no hedging

Harsh framing.
"""


Builder = Callable[..., int]


@pytest.fixture
def run_validator(
    capsys: pytest.CaptureFixture[str],
) -> Callable[[Path, bool], tuple[int, str]]:
    """Return a function that runs the validator against a fixture root."""

    def _run(root: Path, verbose: bool = False) -> tuple[int, str]:
        argv = ["--root", str(root)]
        if verbose:
            argv.append("--verbose")
        exit_code = validate_skills.main(argv)
        captured = capsys.readouterr()
        return exit_code, captured.out + captured.err

    return _run


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_good_skill_passes(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=GOOD_BODY,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 0, output
    assert "OK —" in output


def test_overflow_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    # 8 lines of frontmatter + heading + blank + N "line" entries + trailing \n.
    # Pick N so total newlines > 500. 600 produces ~608 total — well above cap.
    body = (
        "---\n"
        "name: bloat-skill\n"
        "description: bloat\n"
        "mutates: []\n"
        "allowed-tools: Read\n"
        "---\n"
        "\n"
        "## Harsh mode — no hedging\n" + "\n".join(["line"] * 600) + "\n"
    )
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "bloat-skill", body=body)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "exceeds 500-line cap" in output


def test_missing_asset_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    # Body promises references/foo.md but we never create it.
    body = GOOD_BODY.replace("references/notes.md", "references/foo.md")
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "broken-promise", body=body)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "references/foo.md" in output


def test_path_traversal_rejected(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    body = GOOD_BODY.replace("references/notes.md", "references/../../outside.md")
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "escaping-skill", body=body)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "path-traversal attempt" in output


def test_harsh_mode_missing_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    body = (
        "---\n"
        "name: no-harsh\n"
        "description: x\n"
        "mutates: []\n"
        "allowed-tools: Read\n"
        "---\n"
        "\n"
        "# title\n\nprose without the canonical heading\n"
    )
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "no-harsh", body=body)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "harsh-mode section missing" in output


def test_sweep_marker_missing_fails_for_editable(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    # refactor-verify is one of the six editable sweep workers.
    body = EDITABLE_SWEEP_BODY.replace(
        "the `sweep=read-only` marker", "the read-only marker"
    )
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "refactor-verify",
        body=body,
        extra_files={"references/patterns.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "sweep=read-only marker missing" in output


def test_sweep_marker_exempt_for_diagnosis(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    # fight-repo-rot is pure-diagnosis — exempt from the sweep marker check.
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "fight-repo-rot", body=PURE_DIAGNOSIS_BODY)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 0, output


def test_manifest_version_mismatch_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    _write_manifests(tmp_path, marketplace_version="0.4.0", plugin_version="0.3.9")
    _write_skill(
        tmp_path,
        "good-skill",
        body=GOOD_BODY,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "version drift" in output
    assert "0.4.0" in output and "0.3.9" in output


def test_manifest_version_sync_passes(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    _write_manifests(tmp_path, marketplace_version="1.2.3", plugin_version="1.2.3")
    _write_skill(
        tmp_path,
        "good-skill",
        body=GOOD_BODY,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 0, output


def test_verbose_emits_per_skill_summary(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=GOOD_BODY,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, True)
    assert exit_code == 0, output
    assert "harsh=ok" in output
    assert "sweep-marker=n/a" in output
    assert "asset-paths=1" in output
    assert "/500 lines" in output
    assert "mutates=[]" in output


# --------------------------------------------------------------------------- #
# v0.7.0 — frontmatter mutates contract
# --------------------------------------------------------------------------- #


def test_mutates_field_missing_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    body = GOOD_BODY.replace("mutates: []\n", "")
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "missing 'mutates' field" in output


def test_mutates_invalid_token_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    body = GOOD_BODY.replace("mutates: []", "mutates: [bogus]")
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "invalid token" in output


def test_mutates_external_in_sweep_specialist_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """Sweep specialists cannot mutate external systems — invariant #6."""
    body = EDITABLE_SWEEP_BODY.replace(
        "mutates: [direct]", "mutates: [direct, external]"
    )
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "refactor-verify",
        body=body,
        extra_files={"references/patterns.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "cannot mutate external systems" in output


def test_mutates_pure_diagnosis_must_be_empty(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """fight-repo-rot is pure-diagnosis; mutates must be []."""
    body = PURE_DIAGNOSIS_BODY.replace("mutates: []", "mutates: [direct]")
    _write_manifests(tmp_path)
    _write_skill(tmp_path, "fight-repo-rot", body=body)
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "pure-diagnosis" in output


def test_mutates_editable_worker_must_have_direct(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """refactor-verify edits in direct-call mode; mutates must include 'direct'."""
    body = EDITABLE_SWEEP_BODY.replace("mutates: [direct]", "mutates: []")
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "refactor-verify",
        body=body,
        extra_files={"references/patterns.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "missing 'direct'" in output


# --------------------------------------------------------------------------- #
# v0.7.0 — references file cap
# --------------------------------------------------------------------------- #


def test_oversized_references_file_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """References files >500 lines must fail."""
    oversized = "\n".join(["line"] * 501) + "\n"
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=GOOD_BODY,
        extra_files={"references/notes.md": oversized},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "exceeds 500-line cap" in output
    assert "references/notes.md" in output


# --------------------------------------------------------------------------- #
# v0.7.0 — skill-invocation cross-check
# --------------------------------------------------------------------------- #


def test_unknown_skill_invocation_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """Backtick `/some-skill` must reference a real skill."""
    body = GOOD_BODY.replace(
        "Some prose.",
        "Hand off to `/refractor-verify` (typo of refactor-verify).",
    )
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "/refractor-verify" in output


def test_url_path_in_backticks_does_not_false_positive(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """Backtick `/pricing` is a URL example, not a skill — must not flag."""
    body = GOOD_BODY.replace(
        "Some prose.",
        "Visit `/pricing` and `/docs` for examples.",
    )
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 0, output


# --------------------------------------------------------------------------- #
# v0.7.0 — frontmatter required fields
# --------------------------------------------------------------------------- #


def test_missing_description_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    body = GOOD_BODY.replace("description: fixture skill\n", "")
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "missing required field 'description'" in output


def test_name_directory_mismatch_fails(
    tmp_path: Path,
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """Frontmatter `name` must match directory name."""
    body = GOOD_BODY.replace("name: good-skill", "name: wrong-name")
    _write_manifests(tmp_path)
    _write_skill(
        tmp_path,
        "good-skill",
        body=body,
        extra_files={"references/notes.md": "stub"},
    )
    exit_code, output = run_validator(tmp_path, False)
    assert exit_code == 1
    assert "does not match directory" in output


# --------------------------------------------------------------------------- #
# Smoke test against the shipping repo
# --------------------------------------------------------------------------- #


def test_real_repo_passes(
    run_validator: Callable[[Path, bool], tuple[int, str]],
) -> None:
    """Smoke test: the shipping repo itself must stay green."""
    exit_code, output = run_validator(REPO_ROOT, False)
    assert exit_code == 0, output
    assert "OK —" in output
