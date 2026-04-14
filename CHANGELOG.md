# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/). Plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## [Unreleased]

## [0.3.1] — 2026-04-15

### Added

- `CLAUDE.md` at the repo root — operational rules read at the start of every Claude Code session on this repo. Contains the Never-do list (no bulk README rewrites, no new skill past the 10 cap, no `SKILL.md` over 500 lines, no worker without harsh mode, no task-done claim without `validate_skills.py` passing, no committed credentials, no missing `sweep=read-only` marker, no single-manifest version bump), Always-do list (run the validator after every skill edit, functional-only CHANGELOG, update all four READMEs together, sync both manifests, verify harsh-mode coverage, 4-part output shape), full release process (tag + `gh release create`), change-type → file matrix, load-bearing invariants table, and a "Recently decided" section for rules that should not be re-argued.
- `scripts/validate_skills.py` now enforces the 500-line `SKILL.md` cap as a machine check. Previously only documented in `MAINTENANCE.md` and `docs/PHILOSOPHY.md`. The current largest `SKILL.md` is `write-for-ai/SKILL.md` at 379 lines — all 10 skills fit under the cap. Violation output points at the offending file with its line count and the "extract into references/*.md" remediation.
- `scripts/validate_skills.py` now emits both checks in the success line: `OK — every promise in N skills resolves to an actual file and every SKILL.md is ≤500 lines`. Verbose mode (`--verbose`) reports per-file line counts as `N/500 lines`.

### Changed

- Plugin version `0.3.0` → `0.3.1` in `.claude-plugin/marketplace.json`.
- Plugin version `0.3.0` → `0.3.1` in `plugins/vibesubin/.claude-plugin/plugin.json`.
- `scripts/validate_skills.py` docstring rewritten to document both checks (asset-path existence + `SKILL.md` line cap).
- `scripts/validate_skills.py` internal rename: `missing` → `violations` to reflect that the validator now reports more than one category of failure.

## [0.3.0] — 2026-04-15

### Added

- `manage-secrets-env` skill — secrets-and-env slice of the former `manage-config-env`. Owns the four-bucket decision tree, `.env` / `.env.example` rules, startup validation, drift check, build-time vs runtime env vars, `.env` precedence, `.gitignore` default-safe template, and the full secret lifecycle (add / update / rotate / remove / migrate / audit drift / provision new environment).
- `project-conventions` skill — conventions slice of the former `manage-config-env`. Owns dependency versioning, GitHub Flow branch strategy, directory layout, path portability audit.
- `manage-assets` skill — diagnosis-only bloat scan. Detects large files in the working tree (>10 MB, >50 MB, >100 MB tiers), large blobs in git history, LFS migration candidates, asset-directory growth, duplicate binaries. Never deletes, never rewrites history. Hands off to `refactor-verify` for destructive operations, to `manage-secrets-env` for `.gitignore` gaps, to `fight-repo-rot` for unused assets.
- `unify-design` skill — web-dev design-system auditor and token extractor. Detects the framework (Tailwind v3, Tailwind v4, CSS Modules, styled-components, Emotion, Material UI, Chakra UI, vanilla CSS), establishes the tokens file as the BI source of truth (scaffolds one if missing with opinionated spacing/typography/radius/shadow scales and operator-filled palette slots), audits for drift (hardcoded hex/rgb/oklch outside tokens, arbitrary Tailwind values like `w-[432px]`, inline style objects, duplicate Button/Card/Nav/Logo components, near-match colors), and fixes drift by extracting values to tokens. Multi-file component consolidations hand off to `refactor-verify`. Includes `references/token-scaffolds.md` with framework-specific starter tokens files.
- "Objectivity — no exaggeration, no marketing" section in `write-for-ai/SKILL.md`. Eight rules: no unbacked adjectives, no superlatives without comparison, no marketing metaphors, no weasel hedging, verification command required on every capability claim, numbers are specific or absent, status flags are load-bearing, no self-congratulation. Enforced via a new checklist item in the mandatory self-review.
- "Harsh mode — no hedging" sections in `refactor-verify/SKILL.md`, `setup-ci/SKILL.md`, `write-for-ai/SKILL.md`, `manage-secrets-env/SKILL.md`, `project-conventions/SKILL.md`, `manage-assets/SKILL.md`, `unify-design/SKILL.md`. Every specialist that can receive the `tone=harsh` marker now implements the switch.
- "Test rot" section in `fight-repo-rot/SKILL.md` — dead tests, obsolete fixtures, snapshot rot, skipped-tests older than 6 months, hardcoded sleeps inside tests, oversized test files / functions. Test-rot deletions hand off to `refactor-verify` with the same HIGH/MEDIUM/LOW confidence framing.
- `docs/PHILOSOPHY.md` — pack invariants in seven rules.

### Changed

- Skill `plugins/vibesubin/skills/manage-config-env/` split into `manage-secrets-env/` and `project-conventions/`. The `manage-config-env` directory no longer exists.
- Reference `manage-config-env/references/secrets-cli.md` moved to `manage-secrets-env/references/secrets-cli.md`.
- Reference `manage-config-env/references/startup-validation.md` moved to `manage-secrets-env/references/startup-validation.md`.
- Reference `manage-config-env/references/secret-rotation.md` moved to `manage-secrets-env/references/secret-rotation.md`.
- Reference `manage-config-env/references/lifecycle-workflows.md` moved to `manage-secrets-env/references/lifecycle-workflows.md`.
- Script `manage-config-env/scripts/check-env-drift.sh` moved to `manage-secrets-env/scripts/check-env-drift.sh`.
- Template `manage-config-env/templates/.env.example.template` moved to `manage-secrets-env/templates/.env.example.template`.
- Template `manage-config-env/templates/.gitignore.template` moved to `manage-secrets-env/templates/.gitignore.template`.
- Reference `manage-config-env/references/branch-strategy.md` moved to `project-conventions/references/branch-strategy.md`.
- Reference `manage-config-env/references/directory-layout.md` moved to `project-conventions/references/directory-layout.md`.
- Reference `manage-config-env/references/path-portability.md` moved to `project-conventions/references/path-portability.md`.
- Template `manage-config-env/templates/dependabot.yml.template` moved to `project-conventions/templates/dependabot.yml.template`.
- `vibesubin/SKILL.md` scope-confirmation sentence: "six checks in parallel — refactor safety, security, repo rot, docs, CI setup, and config/env/branch conventions" → "eight checks in parallel — refactor safety, security, repo rot, docs, CI setup, secrets/env, project conventions, and repo bloat".
- `vibesubin/SKILL.md` "Run all six sub-skills" → "Run all eight sub-skills".
- `vibesubin/SKILL.md` "Two specialists (`fight-repo-rot`, `audit-security`) are pure-diagnosis by default" → "Three specialists (`fight-repo-rot`, `audit-security`, `manage-assets`) are pure-diagnosis by default. The other five (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`) rely on the `sweep=read-only` marker."
- `vibesubin/SKILL.md` parallel launch block: `manage-config-env` entry replaced with three entries — `manage-secrets-env`, `project-conventions`, `manage-assets`.
- `vibesubin/SKILL.md` routing decision tree: single `manage-config-env` branch split into three branches — `manage-secrets-env` (`.env`, secret, rotate, gitignore, api key), `project-conventions` (branch, dependency, folder structure, hardcoded path), `manage-assets` (repo is huge, big files, LFS, bloat).
- `vibesubin/SKILL.md` router example "I pushed my .env to github" hand-off updated from `manage-config-env` to `manage-secrets-env`.
- `vibesubin/SKILL.md` "What ran" report section: 6 rows → 8 rows.
- `vibesubin/SKILL.md` time-estimate phrasing removed from umbrella reports: "a couple of minutes" (scope confirmation), "get results in minutes, not an hour" (launch rationale), "Est. time" report-table column, "20 min" / "2–3 hours" / "30 min + rotate" example rows, "20 minutes" recommended-order example, "takes minutes" in Things Not To Do. Replaced with qualitative size buckets (S/M/L) in the prioritized fix-list table.
- Cross-reference `manage-config-env` → `manage-secrets-env` applied in: `audit-security/SKILL.md` (tracked `.env` hand-off, incident runbook `.gitignore` hand-off), `setup-ci/SKILL.md` (deploy-touches-config hand-off), `write-for-ai/SKILL.md` (documenting-env hand-off).
- Cross-reference `manage-config-env` → `project-conventions` applied in: `fight-repo-rot/SKILL.md` (hardcoded-path hand-off in main text and hand-off summary), `refactor-verify/SKILL.md` (config-touching-changes integration note, split between secrets-env and project-conventions), `setup-ci/SKILL.md` (new hand-off entry for branch-strategy and dep-pinning concerns).
- `fight-repo-rot/SKILL.md` hand-off summary adds explicit routes for dead-test / obsolete-fixture findings (→ `refactor-verify`) and oversized-binary findings (→ `manage-assets`).
- `README.md` "Today's lineup" table: 6 rows → 8 rows. `manage-config-env` row replaced with `manage-secrets-env`, `project-conventions`, `manage-assets` rows.
- `README.md` "Two skills never edit" phrasing → "Three skills never edit" (adds `manage-assets` alongside `fight-repo-rot` and `audit-security`).
- `README.md` direct-call list: `/manage-config-env` replaced with `/manage-secrets-env` and `/project-conventions`.
- `README.md` § 6 heading `manage-config-env` replaced with three new headings: § 6 `manage-secrets-env`, § 7 `project-conventions`, § 8 `manage-assets`. Old § 6 description removed.
- `README.md` "Workflows that come up often": "Onboarding to a new repo" and "Starting from scratch" bullets updated to reference `manage-secrets-env` and `project-conventions`; new "Why is my repo so big?" bullet references `manage-assets` and `refactor-verify`.
- Plugin version `0.2.0` → `0.3.0` in `.claude-plugin/marketplace.json`; description updated for 9-skill lineup (refactor verification, security, repo rot, AI-friendly docs, CI, secrets lifecycle, project conventions, repo bloat, design unification).
- Plugin version `0.1.0` → `0.3.0` in `plugins/vibesubin/.claude-plugin/plugin.json`. `plugin.json` was previously stuck at `0.1.0` while `marketplace.json` had already advanced to `0.2.0`. Description updated for 9-skill lineup.
- `README.ko.md`, `README.ja.md`, `README.zh.md` rewritten end-to-end for 0.3.0 structure: 9-skill table, new §§ 6-9 (`manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`), new "three skills never edit" phrasing (was "two"), new "objectivity — no exaggeration" principle in `write-for-ai` and Philosophy sections, new workflow bullets for bloat and design drift. Natural-voice translations in each target language, not literal word-for-word.

### Fixed

- `MAINTENANCE.md` referenced `docs/PHILOSOPHY.md` in the "future AI sessions should read this file" ordered list, but the file did not exist. Target file now present.

## [0.2.0] — 2026-04-15

### Added

- Harsh mode for the `/vibesubin` sweep. Triggered by `/vibesubin harsh`, `brutal review`, `don't sugarcoat`, `매운 맛으로`, `厳しめで`, `说狠一点`. Propagates `tone=harsh` marker to specialists.
- "Harsh mode" sections in `fight-repo-rot/SKILL.md`, `audit-security/SKILL.md`, and `vibesubin/SKILL.md` report template.
- "Sweep mode — read-only audit" sections in `refactor-verify`, `setup-ci`, `write-for-ai`, `manage-config-env`. Each specialist checks for the `sweep=read-only` marker before editing.
- `/vibesubin` umbrella: parallel launch block now prefixes every specialist task with `sweep=read-only` verbatim.
- `manage-config-env/SKILL.md`: new "Lifecycle workflows" section covering add, update, rotate, remove, migrate, audit drift, provision.
- `manage-config-env/SKILL.md`: "Build-time vs runtime env vars" subsection (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_`) and ".env file precedence" subsection.
- `manage-config-env/references/secret-rotation.md` — provider-specific rotation recipes (AWS IAM, GCP SA keys, Stripe, OpenAI, Anthropic, Postgres, JWT, OAuth, GitHub PAT).
- `manage-config-env/references/lifecycle-workflows.md` — deep-dive edge cases for each lifecycle operation.
- `README.md`: "Read-only sweeps vs. skills that actually edit" section.
- `README.ko.md`, `README.ja.md`, `README.zh.md`: section parity with the English structure (previously JA/ZH were 120-line stubs).
- `CHANGELOG.md` (this file).
- `.gitignore`: `.omx/`, `.claude/`, `.cursor/`, `!.env.example.template`, `!.env.*.template`.

### Changed

- Renamed skill directory `plugins/vibesubin/skills/refactor-safely/` → `plugins/vibesubin/skills/refactor-verify/`.
- `refactor-verify/SKILL.md`: frontmatter `name` updated; scope now includes `delete of confirmed-dead code` alongside refactor, rename, split, merge, extract, inline.
- `refactor-verify/SKILL.md`: Step 6 call-site closure adds a rename/delete/move assertion table; explicitly documents grep as a lower bound.
- `fight-repo-rot/SKILL.md`: "Primary category: dead code" section now precedes churn × complexity; dead-code findings tagged HIGH / MEDIUM / LOW with per-level deletion rules.
- `fight-repo-rot/SKILL.md`: `allowed-tools` removed Edit and Write; intro block asserts the skill never edits, plans, or runs verification.
- `manage-config-env/scripts/check-env-drift.sh`: handles `export KEY=value`, `KEY = value` with spaces, values containing `=`. Documents multiline values as unsupported. Intended for pre-commit, not CI.
- `manage-config-env/SKILL.md` frontmatter: `description` and `when_to_use` cover the lifecycle triggers (`rotate this secret`, `remove unused env var`, `migrate to env var`, `add staging environment`, `check env drift`).
- `README.md`: 458 → 232 lines. Install section: 91 → 30 lines.
- `README.ko.md`: rewritten in natural Korean; section headers `Philosophy` / `Contributing` / `License` → `철학` / `기여` / `라이선스`.
- `README.ja.md`, `README.zh.md`: expanded from 120-line stubs to 232 lines matching the English structure.
- Cross-references to `refactor-safely` updated to `refactor-verify` in: `audit-security/SKILL.md`, `setup-ci/SKILL.md`, `write-for-ai/SKILL.md`, `vibesubin/SKILL.md`, `manage-config-env/SKILL.md`, `manage-config-env/references/path-portability.md`, `MAINTENANCE.md`, `CONTRIBUTING.md`.
- Plugin version `0.1.0` → `0.2.0` in `.claude-plugin/marketplace.json`.

### Removed

- `git stash` from `refactor-verify/SKILL.md` Step 1 isolation options.
- `refactor-verify/SKILL.md` hard dependency on the term "Mikado" — now described as one dependency-tree style among others.
- `fight-repo-rot/SKILL.md` action language (`delete this`, `fix it`); replaced with hand-off pointers.

### Fixed

- `manage-config-env/templates/.env.example.template` was previously matched by `.env.*` in `.gitignore` and never tracked. Added ignore exception and force-added the file. CI validator (`scripts/validate_skills.py`) now passes.

## [0.1.0] — initial release

- Six skills: `refactor-safely`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-config-env`.
- `/vibesubin` umbrella command for parallel sweep.
- Install paths: Claude Code marketplace, `skills.sh`, manual symlink.
- READMEs: EN / KO / JA / ZH.

[Unreleased]: https://github.com/subinium/vibesubin/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/subinium/vibesubin/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/subinium/vibesubin/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/subinium/vibesubin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/subinium/vibesubin/releases/tag/v0.1.0
