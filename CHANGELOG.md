# Changelog

All notable changes to vibesubin are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/).

The plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) and is bumped in the same commit that lands each release.

## [Unreleased]

_Nothing yet. Open an [issue](https://github.com/subinium/vibesubin/issues) to propose the next change._

## [0.2.0] — 2026-04-15

### Added

- **Harsh mode** for the `/vibesubin` sweep and the feedback skills. Trigger with `/vibesubin harsh`, *"brutal review"*, *"don't sugarcoat"*, or *"no hedging"*. Harsh mode drops hedging language, leads with criticism, refuses to close on *"looks fine"* when real findings exist, and tightens the verdict line. Default tone stays balanced — harsh is opt-in.
- **`manage-config-env` lifecycle workflows** — add, update, rotate, remove, migrate between buckets, audit drift across environments, provision a new environment. Each workflow documents the trap, the safe sequence, and the hand-off. New references: `secret-rotation.md` (provider-specific recipes for AWS / GCP / Stripe / OpenAI / DB users / JWT / OAuth) and `lifecycle-workflows.md` (deep-dive edge cases).
- **`manage-config-env` NEXT_PUBLIC_ / VITE_ / REACT_APP_ guidance** — explicit rule that secrets never go into build-time client-bundled env vars, plus `.env` precedence rules for Next.js, Vite, Node, Python, and Ruby.
- **Sweep mode — read-only audit** sections in `refactor-verify`, `setup-ci`, `write-for-ai`, `manage-config-env`. Each skill now explicitly handles the `sweep=read-only` marker from the `/vibesubin` umbrella and switches to findings-only output when the marker is present. Direct invocation remains fully edit-capable.
- **README "Read-only sweeps vs. skills that actually edit"** section in all four languages (EN / KO / JA / ZH), clarifying which skills edit when called directly and which are pure diagnosis regardless.
- **`CHANGELOG.md`** (this file).

### Changed

- **`refactor-safely` renamed to `refactor-verify`.** The old name was action-framed (*"do it safely"*) but the skill's core is proof-framed (*"prove done"*). The new name matches the operator's mental model: the skill that catches an AI's silent regressions. Scope explicitly expanded to cover confirmed-dead-code deletions, not just structural refactors.
- **`fight-repo-rot` narrowed to pure diagnosis.** Dead code is now the primary category, promoted from *"other rot"* to lead the report. Every dead-code finding gets a HIGH / MEDIUM / LOW confidence tag so the operator deletes with calibrated risk. The skill never edits, never plans fixes, never runs verification — it hands off to `refactor-verify` for deletions and splits, to `manage-config-env` for hardcoded paths, and to `audit-security` for dependency CVEs.
- **`refactor-verify` rollback plan**: removed `git stash` from the isolation options. Stashes are interruption-unsafe and recovery is manual. Branch or worktree only.
- **`refactor-verify` call-site closure**: explicitly documents grep as a *lower bound*, not a ground truth. Deletions based on a grep-zero result are labeled MEDIUM confidence and require a second signal (LSP find-references, import graph, or operator confirmation).
- **`check-env-drift.sh`** rewritten for correctness. Now handles `export KEY=value`, `KEY = value` with spaces around the equals sign, values containing `=` characters, and documents multiline values as unsupported (use a file reference instead). Script is now pre-commit-friendly rather than CI-only — CI environments usually have no local `.env` to compare against.
- **README English version shortened** from 458 to 232 lines. Install section dropped from 91 to 30 lines.
- **README Korean rewritten** from heavy translation-ese into natural Korean. Section headers aligned.
- **README Japanese and Chinese** expanded from 120-line stubs to full 232-line translations matching the new structure.
- **GitHub repo About** description and topic tags filled in.

### Removed

- `git stash` as an isolation option in `refactor-verify` Step 1 — interruption-unsafe.
- Mikado-only framing in `refactor-verify` Step 2. Mikado is now described as one valid dependency-tree style, not the only one — the principle is *"commit the plan before touching code"*, regardless of notation.
- `fight-repo-rot` treatment/action language (*"delete this"*, *"fix it"*). Replaced with explicit hand-off pointers only.

## [0.1.0] — initial release

- Six skills: `refactor-safely`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-config-env`.
- Umbrella `/vibesubin` command for the full parallel sweep.
- Three install paths: Claude Code marketplace, `skills.sh` cross-agent, manual symlinks.
- Four-language README (EN / KO / JA / ZH).

[Unreleased]: https://github.com/subinium/vibesubin/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/subinium/vibesubin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/subinium/vibesubin/releases/tag/v0.1.0
