# Maintenance

This skill pack is a **living artifact**. It is not a one-time authoring job — it has to keep up with:

- Changes in Claude Code's skill / plugin / hook system
- New LLM failure modes as models evolve
- New static analysis and refactoring tools
- New security patterns and CVEs
- New CI/CD conventions (GitHub Actions, deployment targets)
- Feedback from real vibe-coder users via issues

This document defines **how** the pack is maintained so the maintainer (and future AI sessions) have a rhythm to follow.

---

## Update cadence

| Scope | Frequency | Trigger |
|---|---|---|
| **Frontmatter / schema audit** | Every release of Claude Code that touches skills or plugins | Upstream changelog mention |
| **Refactoring methodology review** | Quarterly | Spot-check `understandlegacycode.com`, OpenRewrite changelog, Martin Fowler's site, recent ICSE/FSE papers |
| **Security pattern list** | Quarterly | OWASP Top 10 updates, CVE digests for major runtimes |
| **Language smoke-test table** | Biannually | New mainstream linters/type checkers (e.g., `ty`, `pyrefly`, `oxc`) |
| **Real-world issue sweep** | Monthly | Triage open issues, incorporate reproducible bug reports |
| **Failure-mode log** | Ad hoc, on session insight | Whenever an AI session reveals a failure pattern not yet covered |

---

## What to update when

### When a new Claude Code version ships

1. Check the Claude Code release notes for any changes to:
   - `SKILL.md` frontmatter fields (new fields, removed fields, renamed fields)
   - Plugin marketplace format (`.claude-plugin/marketplace.json`, `plugin.json`)
   - Hook events (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, new events)
   - Skill invocation mechanics (progressive disclosure rules, nested reference limits)
2. Validate every `SKILL.md` in the pack still parses. Run a lint pass if one is available.
3. Bump the pack's "last tested against Claude Code version" note at the bottom of this file.

### When a new failure mode is observed

A "failure mode" is a concrete mistake an AI makes during a real session that the pack should have prevented.

1. Open an issue titled `[failure-mode] <short description>`.
2. Identify which skill should have caught it.
3. Add the pattern to that skill's `references/llm-failure-modes.md` (or equivalent).
4. If applicable, add a detection grep/command to `scripts/`.
5. Reference the issue in a commit: `fix(refactor-verify): guard against missed callsite after rename (#NN)`.

### When a skill file grows past 500 lines

Claude Code partially reads long SKILL.md files. If any `SKILL.md` exceeds ~500 lines:

1. Extract the tail sections into `references/*.md`.
2. Replace them with one-line links from `SKILL.md`.
3. Verify progressive disclosure still works — Claude should only pull the reference when it needs the detail.

### When a new language needs coverage

The pack aims to be language-agnostic. Adding a new language means:

1. Add an entry to `plugins/vibesubin/skills/refactor-verify/references/language-smoke-tests.md`:
   - Canonical build / typecheck / test command chain
   - Standard linter
   - Common refactoring pitfalls for that language
   - Security scanner considerations for the language (scanners and patterns are folded into this file — there is no separate `language-scanners.md`).
2. If the language needs bespoke LOC / complexity tooling beyond `lizard` / `scc` / `cloc`, document it inline in the relevant section of `plugins/vibesubin/skills/fight-repo-rot/SKILL.md`. Rot metrics are captured per-scan (churn × complexity, LOC, god-file thresholds) — there is no sidecar metrics file.
3. Update any smoke-test script in `scripts/` to auto-detect the new language.

Do **not** add a new top-level skill per language. Everything stays language-agnostic.

### When adding a new skill

See [`docs/ADDING-A-SKILL.md`](./docs/ADDING-A-SKILL.md) for the canonical walkthrough — file layout, required `SKILL.md` sections (including harsh-mode and sweep-mode), umbrella wiring, README touch-ups, validator expectations, and CHANGELOG entry. Do not describe the procedure inline here; keep this file focused on cadence.

---

## What NOT to change

Some decisions are load-bearing for the pack's identity. Changing them is a major version bump, not a routine update.

- **The 6-step recursive verification procedure.** `refactor-verify/SKILL.md` is built around this. If the sequence changes, every skill that references it needs review.
- **Tidy First separation.** Structural commits must stay separated from behavioral commits across the entire pack.
- **Third-person description frontmatter.** Claude's discovery heuristics rely on this. First-person descriptions break triggering.
- **"One level deep" reference structure.** Never chain `SKILL.md → a.md → b.md`. Always flatten.
- **Issue-only contribution model.** PRs are not accepted. This is a design choice; the pack has a single voice. (If this ever changes, update README, CONTRIBUTING, and the issue-only section everywhere in one commit.)

---

## 🛑 Never do

1. **Never rewrite the root `README.md` wholesale.** Targeted edits only — skill table, direct-call list, workflow bullets, accuracy fixes. Never restructure sections, reorder content, or rewrite prose for style. Same rule applies to `docs/i18n/README.ko.md`, `docs/i18n/README.ja.md`, `docs/i18n/README.zh.md`. End-to-end rewrites of translations are acceptable only when the structural scope of the change (skill split, new skill, rename) makes surgical edits impossible — and even then, preserve the existing voice.
2. **Never add a new worker skill past the 10 + 1 category cap.** The pack caps at **10 code-hygiene workers** plus **1 process worker**, for 11 total (the `vibesubin` umbrella is not counted). As of v0.4.0 all 11 slots are used. Code hygiene (10): `refactor-verify`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`, `codex-fix`. Process (1): `ship-cycle`. Any future new capability must extend, split, or displace an existing skill within its category — do not expand either cap. The two-bucket split exists because process work (issue/release orchestration) is a distinct cognitive category from code hygiene; users don't confuse them.
3. **Never ship a `SKILL.md` over 500 lines.** Enforced by `scripts/validate_skills.py`. Extract tail sections into `references/*.md` and replace with one-line links from `SKILL.md`. Progressive disclosure is load-bearing — long `SKILL.md` files get partially read by Claude Code. Same cap applies to every individual `references/*.md` file.
4. **Never ship a worker skill without a "Harsh mode — no hedging" section.** Every worker the umbrella launches must implement the `tone=harsh` marker check. Partial coverage is the root cause of *"harsh mode doesn't feel harsh"*. Balanced-mode silent fallback is a regression.
5. **Never claim a task is done without `python3 scripts/validate_skills.py` passing.** The validator is the contract between what `SKILL.md` promises and what exists on disk. A failure is a ship blocker — not a warning.
6. **Never commit `.env`, credentials, marketplace tokens, or SSH private keys.** `.gitignore` covers the usual suspects; verify `git ls-files | grep -iE '\.env$|\.pem$|id_rsa'` before every release commit.
7. **Never skip the `sweep=read-only` marker in the umbrella's parallel launch block.** The 6 editable worker specialists (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`) rely on it to stay read-only during `/vibesubin` sweeps. Without the marker, they fall back to full edit behavior, which is incorrect for a sweep.
8. **Never bump the plugin version in only one manifest.** `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json` must both change together. `plugin.json` has been stale before — catch it in review.
9. **Never add `external` to a sweep specialist's `mutates` field.** The sweep is read-only by invariant; specialists that mutate external systems (`gh`, `codex`, deploy targets) belong in direct-call only skills (`ship-cycle`, `codex-fix`). Validator enforces this.

## ✅ Always do

1. **Run `python3 scripts/validate_skills.py` after any skill edit.** This is the before-you-commit check. Expected output: `OK — every promise in N skills resolves to an actual file...`.
2. **Run `pytest tests/` after any validator or test edit.** Same gate as the validator — both must be green before commit.
3. **Update `CHANGELOG.md` in functional-only style.** Rule: every bullet describes an observable change. No narrative, no meta-rationale, no "we decided to", no emotional framing. If you're explaining *why*, the bullet belongs in a commit body or release notes, not the CHANGELOG.
4. **Update all four READMEs together when a skill is added, renamed, or deleted.** Surgical edits only to `README.md`, `docs/i18n/README.ko.md`, `docs/i18n/README.ja.md`, `docs/i18n/README.zh.md` — skill table rows, direct-call list, workflow bullets, "never edit" phrasing, section headings. Korean/Japanese/Chinese users see the same structure as English, in natural voice for their language.
5. **Sync plugin version across both manifests in the same commit.** `marketplace.json` is the canonical source; `plugin.json` mirrors it. Description text should also stay in sync.
6. **Verify harsh-mode coverage before shipping a new worker.** Every worker that can receive the `tone=harsh` marker must have a "Harsh mode — no hedging" section in its `SKILL.md` that (a) checks for the marker, (b) switches output rules to direct / no-hedging framing, (c) preserves factual accuracy — never inflates severity, never invents findings.
7. **Respect the 4-part output shape in every worker.** Every skill's output follows: what it did, what it found, what it verified, what you should do next. This is load-bearing for the umbrella's synthesis step.
8. **Declare `mutates` in every SKILL.md frontmatter.** Tokens drawn from {`direct`, `external`}. Empty list `[]` for diagnosis-only or umbrella. The umbrella reads this field at sweep launch; misdeclaration silently breaks the read-only invariant.

## 🚀 Release process

Versions are managed via git tags + GitHub releases. No separate release-notes file lives in the repo — CHANGELOG is the in-repo source of truth, release notes live on GitHub as user-facing extracts.

Steps, in order:

1. **Finalize `CHANGELOG.md`.** Move `[Unreleased]` entries under a new `[X.Y.Z] — YYYY-MM-DD` heading. Apply the functional-only style rule.
2. **Bump version in both manifests.**
   - `.claude-plugin/marketplace.json` (`plugins[0].version`)
   - `plugins/vibesubin/.claude-plugin/plugin.json` (`version`)
   - Descriptions should also match if the skill lineup changed.
3. **Run the validator and tests.** `python3 scripts/validate_skills.py` and `pytest tests/` — both must pass. If either fails, fix before anything else.
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

Steps 1–10 above are the manual policy. The `ship-cycle` skill (`plugins/vibesubin/skills/ship-cycle/`) implements this policy as an automated pipeline — its `references/release-pipeline.md` is the operational expansion with explicit commands for each step. The two must stay in sync on ordering; if they drift, this policy file wins and the pipeline file updates to match.

## 📋 Change type → file matrix

| Change | Files to touch (in order) | Verification |
|---|---|---|
| Add a new worker skill | `plugins/vibesubin/skills/<name>/SKILL.md` (with harsh + sweep sections + `mutates` frontmatter) → `README.md` §§ table + skills + workflows → `docs/i18n/README.{ko,ja,zh}.md` matching edits → `plugins/vibesubin/skills/vibesubin/SKILL.md` umbrella (launch block + routing tree + What ran + pure-diagnosis count) → `CHANGELOG.md` Added → both manifests if the count changed the description | `python3 scripts/validate_skills.py && pytest tests/` |
| Rename a worker skill | `git mv` directory → replace all backtick references in `SKILL.md`, `README.md`, `docs/i18n/README.{ko,ja,zh}.md`, `CHANGELOG.md`, `plugins/vibesubin/skills/vibesubin/SKILL.md` → update `KNOWN_SKILLS` set in `scripts/validate_skills.py` | `python3 scripts/validate_skills.py` + `git grep <old-name>` returns zero |
| Split a worker skill | `git mv` references/scripts/templates into new directories → write new `SKILL.md` files → delete old directory → update every cross-reference → update umbrella, READMEs, CHANGELOG → update `SWEEP_SPECIALISTS` / `KNOWN_SKILLS` in validator | `python3 scripts/validate_skills.py` + `git grep <old-name>` returns zero |
| Add a section to an existing `SKILL.md` | `SKILL.md` → `CHANGELOG.md` Added | `python3 scripts/validate_skills.py` + `wc -l` ≤ 500 |
| Bump plugin version | Both manifests in sync → `CHANGELOG.md` new version heading → commit → `git tag -a vX.Y.Z -m "..."` → `git push origin vX.Y.Z` → `gh release create` with a temp notes file | `gh release view vX.Y.Z` |
| Cut a release via ship-cycle | `/ship-cycle` drives the whole flow → closed issues → `CHANGELOG.md` aggregation → both manifests → `git tag -a` → `gh release create` | `gh release view vX.Y.Z` + `python3 scripts/validate_skills.py` |
| Fix a broken internal link (docs) | The file with the link → `scripts/validate_skills.py` if it's a new category of check | `python3 scripts/validate_skills.py` |

**Canonical skill-authoring mechanics**: see [`docs/ADDING-A-SKILL.md`](./docs/ADDING-A-SKILL.md) for frontmatter schema, required sections, validator contract, output shape, and the per-change-type file checklist.

## 🔒 Load-bearing invariants

If any of these regress, something higher-level breaks. Most are enforced by `scripts/validate_skills.py`.

| Invariant | Violation symptom | Enforced by |
|---|---|---|
| Every worker specialist implements harsh mode | `/vibesubin harsh` feels like balanced mode for that specialist | validator (Check 3) |
| Every `SKILL.md` ≤ 500 lines | Claude Code partially reads the file, silently drops tail sections | validator (Check 2) |
| Every `references/*.md` ≤ 500 lines | Content hides in references to dodge the SKILL.md cap | validator (Check 9) |
| `marketplace.json` and `plugin.json` versions match | Marketplace install and manual install yield different versions | validator (Check 5) |
| Every promised asset path resolves on disk | `SKILL.md` promises a file the pack does not ship | validator (Check 1) |
| Translations match English structure | Korean / Japanese / Chinese users invoke stale skill names | review (no machine check yet) |
| Umbrella specialist list matches actual skill count | Parallel launch block skips a worker or launches a phantom one | review |
| Category split is enforced (10 hygiene + 1 process, 11 total) | User can't find the right tool; pack loses the cognitive budget of separate caps per category | review |
| `mutates` field declared in every frontmatter, valid tokens, consistent with category | Sweep silently includes a worker that mutates external state | validator (Checks 7-8) |
| Every `/<skill-name>` backtick reference resolves to a real skill | Stale rename leaves a dead pointer in docs | validator (Check 10) |

Pack-level philosophy invariants live in [`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md).

## 🎭 Recently decided (don't re-argue)

- **10-skill cap (superseded 2026-04-21 — see "Cap raised to 10 + 1" below).** Original decision: cap at 10, extend or split beyond. Decided during v0.3.0 scoping (2026-04-14).
- **Functional-only CHANGELOG style.** No narrative, no meta-rationale. Decided during v0.3.0 cleanup.
- **Harsh mode is framing only.** Never inflates severity, never invents findings, never inserts personal attacks. Every harsh statement cites the same evidence the balanced version would. Decided during v0.3.0 coverage review.
- **No bulk README rewrites.** Surgical edits only, preserve voice. Decided after reviewing external harsh feedback during v0.3.0.
- **`unify-design` is web-dev specific, language-agnostic is not required.** Every other worker is language-agnostic, but design-system concerns are inherently frontend. Decided during v0.3.0.
- **Release notes live on GitHub only.** The repo's source of truth is `CHANGELOG.md`. Release notes are user-facing extracts created at tag time from a temp file, not committed. Decided during v0.3.0 release.
- **Versions are managed via git tags + `gh release create`.** Annotated tags, not lightweight. Decided during v0.3.0 release.
- **The 500-line `SKILL.md` cap is enforced by `validate_skills.py`, not just documented.** Decided 2026-04-14.
- **Portable engines can have host-specific wrappers.** Wrappers declare host dependency in frontmatter, host-check first, graceful fallback, delegate to a portable engine, no sweep mode. First wrapper: `codex-fix` → `refactor-verify`. Rule formalized as PHILOSOPHY invariant 9. Decided 2026-04-15.
- **Cap raised to 10 + 1 with category split.** Code hygiene 10, process 1, separate caps. `ship-cycle` is the first process worker. Decided 2026-04-21.
- **Karpathy's four principles enforced in-skill, not just philosophy.** Each worker has "State assumptions — before acting" + Karpathy P2 anchor in Things-not-to-do. Decided 2026-04-21.
- **`mutates` frontmatter field is the umbrella's runtime contract.** Tokens drawn from {`direct`, `external`}; empty list for pure-diagnosis. Sweep specialists cannot include `external`. Validator enforces; umbrella reads at launch. Decided 2026-04-25 during v0.7.0.
- **Language READMEs live under `docs/i18n/`.** Root-level housekeeping — three translated READMEs at root cluttered the file tree. Moved to `docs/i18n/README.{ko,ja,zh}.md` in v0.7.0. The four READMEs are still synchronized in every change.
- **`CLAUDE.md` is gitignored.** Operational rules for this repo redistributed into `MAINTENANCE.md` (this file: never-do, always-do, release process, change-type matrix, invariants, recently-decided), `docs/PHILOSOPHY.md` (pack invariants), `docs/ADDING-A-SKILL.md` (skill-authoring mechanics), and `CONTRIBUTING.md` (contribution-specific rules). The local `CLAUDE.md` is the maintainer's personal session-rules file; the project-wide rules live in tracked docs. Decided 2026-04-25.

## How future AI sessions should read this file

If you are an AI agent picking up maintenance of this pack in a new session, read these files in order:

1. This file (`MAINTENANCE.md`) — operational rules, release process, never-do / always-do
2. `README.md` — overview and skill list
3. `docs/PHILOSOPHY.md` — pack invariants (load-bearing rules)
4. `docs/ADDING-A-SKILL.md` — skill-authoring mechanics (file checklist, frontmatter schema, validator contract)
5. The specific skill's `SKILL.md` and `references/`
6. Recent issues on the repo (via `gh issue list`)

Do not propose structural rewrites on first session. Confirm with the maintainer before touching schemas, install mechanics, or the philosophy.

---

## Last tested against

- Claude Code: _set at release_
- Plugin marketplace spec: `v1` (as of 2026-04)
- Official skill docs: `code.claude.com/docs/en/skills`
