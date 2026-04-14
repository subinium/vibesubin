# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/). Plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## [Unreleased]

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

[Unreleased]: https://github.com/subinium/vibesubin/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/subinium/vibesubin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/subinium/vibesubin/releases/tag/v0.1.0
