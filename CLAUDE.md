# vibesubin — AI operator guide

Read this file first in every new session. It encodes the operational rules that apply to this repo. The pack-level invariants live in [`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md); the update cadence lives in [`MAINTENANCE.md`](./MAINTENANCE.md); the user-facing overview lives in [`README.md`](./README.md). This file is for the rules that have to be checked *every session*.

## 🛑 Never do

1. **Never rewrite the root `README.md` wholesale.** Targeted edits only — skill table, direct-call list, workflow bullets, accuracy fixes. Never restructure sections, reorder content, or rewrite prose for style. Same rule applies to `README.ko.md`, `README.ja.md`, `README.zh.md`. End-to-end rewrites of translations are acceptable only when the structural scope of the change (skill split, new skill, rename) makes surgical edits impossible — and even then, preserve the existing voice.
2. **Never add a new worker skill past 10.** The pack caps at 10 worker skills (the `vibesubin` umbrella is not counted in the 10). Above that, extend an existing skill or split one — do not expand the surface area. Users cannot remember more than ~10 tools.
3. **Never ship a `SKILL.md` over 500 lines.** Enforced by `scripts/validate_skills.py`. Extract tail sections into `references/*.md` and replace with one-line links from `SKILL.md`. Progressive disclosure is load-bearing — long `SKILL.md` files get partially read by Claude Code.
4. **Never ship a worker skill without a "Harsh mode — no hedging" section.** Every worker the umbrella launches must implement the `tone=harsh` marker check. Partial coverage is the root cause of *"harsh mode doesn't feel harsh"*. Balanced-mode silent fallback is a regression.
5. **Never claim a task is done without `python3 scripts/validate_skills.py` passing.** The validator is the contract between what `SKILL.md` promises and what exists on disk. A failure is a ship blocker — not a warning.
6. **Never commit `.env`, credentials, marketplace tokens, or SSH private keys.** `.gitignore` covers the usual suspects; verify `git ls-files | grep -iE '\.env$|\.pem$|id_rsa'` before every release commit.
7. **Never skip the `sweep=read-only` marker in the umbrella's parallel launch block.** The 6 editable worker specialists (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`) rely on it to stay read-only during `/vibesubin` sweeps. Without the marker, they fall back to full edit behavior, which is incorrect for a sweep.
8. **Never bump the plugin version in only one manifest.** `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json` must both change together. `plugin.json` has been stale before — catch it in review.

## ✅ Always do

1. **Run `python3 scripts/validate_skills.py` after any skill edit.** This is the before-you-commit check. Verification command: `python3 scripts/validate_skills.py`. Expected output: `OK — every promise in N skills resolves to an actual file`.
2. **Update `CHANGELOG.md` in functional-only style.** Rule: every bullet describes an observable change. No narrative, no meta-rationale, no "we decided to", no emotional framing. If you're explaining *why*, the bullet belongs in a commit body or release notes, not the CHANGELOG.
3. **Update all four READMEs together when a skill is added, renamed, or deleted.** Surgical edits only to `README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md` — skill table rows, direct-call list, workflow bullets, "never edit" phrasing, section headings. Korean/Japanese/Chinese users see the same structure as English, in natural voice for their language.
4. **Sync plugin version across both manifests in the same commit.** `marketplace.json` is the canonical source; `plugin.json` mirrors it. Description text should also stay in sync.
5. **Verify harsh-mode coverage before shipping a new worker.** Every worker that can receive the `tone=harsh` marker must have a "Harsh mode — no hedging" section in its `SKILL.md` that (a) checks for the marker, (b) switches output rules to direct / no-hedging framing, (c) preserves factual accuracy — never inflates severity, never invents findings.
6. **Respect the 4-part output shape in every worker.** Every skill's output follows: what it did, what it found, what it verified, what you should do next. This is load-bearing for the umbrella's synthesis step.

## 🚀 Release process

Versions are managed via git tags + GitHub releases. No separate release-notes file lives in the repo — CHANGELOG is the in-repo source of truth, release notes live on GitHub as user-facing extracts.

Steps, in order:

1. **Finalize `CHANGELOG.md`.** Move `[Unreleased]` entries under a new `[X.Y.Z] — YYYY-MM-DD` heading. Apply the functional-only style rule.
2. **Bump version in both manifests.**
   - `.claude-plugin/marketplace.json` (`plugins[0].version`)
   - `plugins/vibesubin/.claude-plugin/plugin.json` (`version`)
   - Descriptions should also match if the skill lineup changed.
3. **Run the validator.** `python3 scripts/validate_skills.py` — must print `OK`. If it fails, fix before anything else.
4. **Commit.** Conventional commits format. `feat:` for new capability, `fix:` for a bug, `refactor:` for structural work. Body explains the *why*, not the *what* (the diff shows what). End with `Co-Authored-By: Claude ...` when AI-assisted.
5. **Push the commit.** `git push`.
6. **Create an annotated tag.** `git tag -a vX.Y.Z -m "<one-line summary of the release>"`. Annotated, not lightweight — the tag message shows in GitHub's tag list.
7. **Push the tag.** `git push origin vX.Y.Z`.
8. **Write release notes to a temp file** (not committed to the repo). Structure:
   - One-sentence TL;DR
   - Breaking changes + migration table (only if any — skip the section otherwise)
   - New skills / features
   - Improvements
   - "Under the hood" small fixes
   - Link back to `CHANGELOG.md` for the full history
9. **Create the GitHub release.**
   ```bash
   gh release create vX.Y.Z --title "vibesubin X.Y.Z" --notes-file /tmp/vibesubin-X.Y.Z-release-notes.md
   ```
10. **Verify.** `gh release view vX.Y.Z` — confirm the body rendered and the tag is live.

Do not force-push to `main` and do not move an existing tag. If a release went out with a mistake, cut a new patch version (`vX.Y.Z+1`) with a fix; do not rewrite history.

## 📋 Change type → file matrix

| Change | Files to touch (in order) | Verification |
|---|---|---|
| Add a new worker skill | `plugins/vibesubin/skills/<name>/SKILL.md` (with harsh + sweep sections) → `README.md` §§ table + skills + workflows → `README.ko/ja/zh.md` matching edits → `plugins/vibesubin/skills/vibesubin/SKILL.md` umbrella (launch block + routing tree + What ran + pure-diagnosis count) → `CHANGELOG.md` Added → both manifests if the count changed the description | `python3 scripts/validate_skills.py` |
| Rename a worker skill | `git mv` directory → replace all backtick references in `SKILL.md`, `README.md`, `README.ko/ja/zh.md`, `CHANGELOG.md`, `plugins/vibesubin/skills/vibesubin/SKILL.md` | `python3 scripts/validate_skills.py` + `git grep <old-name>` returns zero |
| Split a worker skill | `git mv` references/scripts/templates into new directories → write new `SKILL.md` files → delete old directory → update every cross-reference → update umbrella, READMEs, CHANGELOG | `python3 scripts/validate_skills.py` + `git grep <old-name>` returns zero |
| Add a section to an existing `SKILL.md` | `SKILL.md` → `CHANGELOG.md` Added | `python3 scripts/validate_skills.py` + `wc -l` ≤ 500 |
| Bump plugin version | Both manifests in sync → `CHANGELOG.md` new version heading → commit → `git tag -a vX.Y.Z -m "..."` → `git push origin vX.Y.Z` → `gh release create` with a temp notes file | `gh release view vX.Y.Z` |
| Fix a broken internal link (docs) | The file with the link → `scripts/validate_skills.py` if it's a new category of check | `python3 scripts/validate_skills.py` |

## 🔒 Load-bearing invariants

If any of these regress, something higher-level breaks.

| Invariant | Violation symptom |
|---|---|
| Every worker specialist implements harsh mode | `/vibesubin harsh` feels like balanced mode for that specialist |
| Every `SKILL.md` ≤ 500 lines | Claude Code partially reads the file, silently drops tail sections |
| `docs/PHILOSOPHY.md` exists | `MAINTENANCE.md` references a missing file, trust decays |
| `marketplace.json` and `plugin.json` versions match | Marketplace install and manual install yield different versions |
| `validate_skills.py` passes | `SKILL.md` promises an asset the pack does not ship |
| Translations match English structure | Korean / Japanese / Chinese users invoke stale skill names |
| Umbrella specialist list matches actual skill count | Parallel launch block skips a worker or launches a phantom one |
| Pack stays at ≤10 worker skills | User can't remember which skill handles what |

## 🎭 Recently decided (don't re-argue)

- **10-skill cap.** Extend or split beyond that. Decided during v0.3.0 scoping (2026-04-14).
- **Functional-only CHANGELOG style.** No narrative, no meta-rationale. Decided during v0.3.0 cleanup.
- **Harsh mode is framing only.** Never inflates severity, never invents findings, never inserts personal attacks. Every harsh statement cites the same evidence the balanced version would. Decided during v0.3.0 coverage review.
- **No bulk README rewrites.** Surgical edits only, preserve voice. Decided after reviewing external harsh feedback during v0.3.0.
- **`unify-design` is web-dev specific, language-agnostic is not required.** Every other worker is language-agnostic, but design-system concerns are inherently frontend. Decided during v0.3.0 design.
- **Release notes live on GitHub only.** The repo's source of truth is `CHANGELOG.md`. Release notes are user-facing extracts created at tag time from a temp file, not committed. Decided during v0.3.0 release.
- **Versions are managed via git tags + `gh release create`.** Annotated tags, not lightweight. Decided during v0.3.0 release.
- **The 500-line `SKILL.md` cap is enforced by `validate_skills.py`, not just documented.** Turned from a social rule into a machine check during v0.3.0 post-release cleanup. Decided 2026-04-14.

## Size expectations for this file

This file is read at the start of every session, so it has to stay short enough that Claude Code does not truncate it. Target: under 200 lines. If this file needs to grow, move detail into `MAINTENANCE.md` (for cadence), `docs/PHILOSOPHY.md` (for invariants), or `CONTRIBUTING.md` (for contribution-specific rules) and link down from here.
