# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/). Plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## [Unreleased]

## [0.7.0] — 2026-04-25

### Added

- `mutates: [<tokens>]` frontmatter field on all 11 SKILL.md files plus the `vibesubin` umbrella. Tokens drawn from `{direct, external}`. Empty list `[]` for the three pure-diagnosis workers (`audit-security`, `fight-repo-rot`, `manage-assets`) and the umbrella. `[direct]` for the six editable sweep workers (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`). `[direct, external]` for the two direct-call-only skills that mutate external systems (`ship-cycle`, `codex-fix`). The field is the umbrella's runtime contract for sweep eligibility and the validator's machine-enforced category check.
- `scripts/validate_skills.py` — five new invariant checks. **Check 7** asserts every SKILL.md frontmatter declares a `mutates` field with a bracketed list of valid tokens. **Check 8** asserts `mutates` is consistent with the skill's category — sweep specialists cannot include `external`, the three pure-diagnosis workers must declare `[]`, the six editable sweep workers must include `direct`. **Check 9** asserts every `references/*.md` file is ≤500 lines (same cap as SKILL.md, prevents content from hiding in references to dodge the SKILL.md cap). **Check 10** asserts every backtick-quoted `/<skill-name>` invocation resolves to a real skill in the pack (`KNOWN_SKILLS` set), with a hyphen-or-`vibesubin` heuristic to avoid false positives on URL examples like `/pricing` or `/docs`. **Check 11** asserts frontmatter declares `name`, `description`, and `allowed-tools` (or `context` + `agent` for the umbrella), with `description` 1-1024 chars and `name` matching the directory.
- `tests/test_validate_skills.py` — 11 new pytest cases covering the new validator checks: missing `mutates` field, invalid `mutates` token, `external` in a sweep specialist, non-empty `mutates` on a pure-diagnosis worker, missing `direct` on an editable sweep worker, oversized references file, unknown skill invocation, URL-path no-false-positive, missing description, name-directory mismatch. Total suite now 21 tests, all green.
- `plugins/vibesubin/skills/refactor-verify/references/review-driven-fix.md` — new 112-line reference. Hosts the full Review-driven fix mode procedure (capture review snapshot, parse and triage findings, plan as dependency tree, execute leaves-up with relaxed AST diff for behavior-changing fixes, commit with `<type>(<scope>): resolve <review-source>#<item-id> — <subject>` back-reference, resolution-report table, stale-snapshot handling). Allows `refactor-verify/SKILL.md` to drop from 500 → 413 lines for new frontmatter headroom.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — new "Sweep contract enforcement (frontmatter check)" paragraph in Step 2 launch block. Umbrella reads each worker's `mutates` field before launching; if `external` appears, the worker is direct-call only and the umbrella refuses to include it in the parallel sweep. Closes the contract loop the validator already enforces statically.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — new `## Mutation contract — preview, confirm, mutate` section (~30 lines) inserted before Step 1. Every external mutation (`gh issue create`, `gh api ... -X PATCH`, `gh release create`, `git tag -a`, `git push`) follows preview → confirm (operator says `approve` / `proceed` / `yes`) → mutate. Created resources carry `<!-- ship-cycle:vX.Y.Z -->` idempotency markers; deterministic branch names and milestone titles make re-runs noop. New rollback table maps every mutation to its inverse `gh` command (`gh issue close`, `gh api ... state=closed`, `gh release delete`, `git push --delete`, `gh pr close`). `dry-run` mode skips every Mutate step.
- `plugins/vibesubin/skills/audit-security/SKILL.md` — new "Output rule for secret findings — fingerprint, never the raw value" paragraph in §1. Secret findings print only file path, line number, value length, first 4 chars (or 7 for known prefixes like `sk-`, `ghp_`, `xoxb-`), and a provider guess. Doubles down on the "never print raw secret" principle by making the safe output shape explicit.
- `plugins/vibesubin/skills/fight-repo-rot/SKILL.md` — new "Path exclusions — never flag generated code as dead" subsection. Excludes `node_modules/`, `vendor/`, `target/`, `.venv/`, `dist/`, `build/`, `out/`, `.next/`, `__pycache__/`, `.tox/`, schema migrations (`migrations/`, `db/migrate/`, `alembic/versions/`), test fixtures (`tests/fixtures/`, `__fixtures__/`, `testdata/`, `*.fixture.*`, `*.golden.*`, `*.snap`, `__snapshots__/`), generated-header files (`// @generated`, `# AUTO-GENERATED`), and Storybook stories from dead-code analysis before confidence tagging.
- `plugins/vibesubin/skills/project-conventions/SKILL.md` — new `## Repo type — app, library, or monorepo` section with detection-signal table for `app | library | monorepo | template | docs-only`. Each repo type maps to a different pinning strategy: app → exact pin + lockfile + CVE auditing; library → semver range + lockfile for tests + explicit compatibility matrix; monorepo → per-package strategy with shared root lockfile; template → exact pin (forks update at fork time); docs-only → devDependencies only.
- `plugins/vibesubin/skills/manage-assets/SKILL.md` — finding classification is now a structured output field (`artifact | source | media | database | secret-shaped | generated`) the umbrella can consume directly. Replaces ad-hoc prose grouping with a fixed taxonomy.

### Changed

- Plugin version `0.6.0` → `0.7.0` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`. Minor bump: new machine-enforced `mutates` contract (frontmatter schema for sweep eligibility), expanded validator (Checks 1–11, was 1–6), `MAINTENANCE.md` absorbs the operational policy (was in `CLAUDE.md`), language READMEs reorganized under `docs/i18n/`, `ship-cycle` mutation contract (preview/confirm/mutate with idempotency markers and rollback table), per-skill output schema additions (`audit-security` fingerprint, `manage-assets` classification, `project-conventions` repo_type, `fight-repo-rot` path exclusions).
- `README.ko.md`, `README.ja.md`, `README.zh.md` moved from repo root to `docs/i18n/README.{ko,ja,zh}.md` via `git mv`. Inter-language link paths in each translated README updated to use `../../README.md` for English and sibling paths for the other two translations. Root-level housekeeping — root file count 10 → 7. `README.md` language switcher updated to `./docs/i18n/...` paths.
- `MAINTENANCE.md` — absorbed the operational policy from the (now gitignored) `CLAUDE.md`. New sections: **🛑 Never do** (9 items, was 8 — added "never put `external` in a sweep specialist's mutates"), **✅ Always do** (8 items, was 6 — added "run pytest" and "declare mutates"), **🚀 Release process** (10 steps), **📋 Change type → file matrix** (with `docs/i18n/` paths and validator+pytest verification command), **🔒 Load-bearing invariants** (10-row table with "Enforced by" column citing validator check numbers), **🎭 Recently decided** (12 entries — preserves the v0.3.0–v0.7.0 decision log; adds `mutates` contract, language-README move, `CLAUDE.md` gitignore rationale). "How future AI sessions should read this file" reading-order updated to start at `MAINTENANCE.md` (was `CLAUDE.md`).
- `docs/ADDING-A-SKILL.md` — frontmatter schema now includes `mutates: [<tokens>]` with field rules; canonical-doc disambiguation paragraph at top references `MAINTENANCE.md` (was `CLAUDE.md`); category-cap reference updated; validator-contract section lists the new Checks 7–11; file-checklist references `docs/i18n/README.{ko,ja,zh}.md` (was root paths); checklist adds `KNOWN_SKILLS` validator update step + `pytest tests/` to verification; "per `MAINTENANCE.md` change-type matrix" replaces the old `CLAUDE.md` reference.
- `plugins/vibesubin/skills/ship-cycle/references/issue-body-template.md` — docs-plan table references `MAINTENANCE.md` (was `CLAUDE.md`) for always-do rules and never-do framing; READMEs row uses `docs/i18n/` paths; `CLAUDE.md` table row replaced with `MAINTENANCE.md`.
- `plugins/vibesubin/skills/ship-cycle/references/release-pipeline.md` — preamble references `MAINTENANCE.md` as the policy authority (was root `CLAUDE.md`); both-manifests invariant cite updated.
- `plugins/vibesubin/skills/refactor-verify/SKILL.md` — `## Review-driven fix mode` reduced from ~103 inline lines to a 13-line summary + pointer to `references/review-driven-fix.md`. Trigger phrases, two-difference summary (input source, behavior-changing scope), and the back-reference commit format stay inline; full procedure with stale-snapshot handling moves to references. SKILL.md size 500 → 413.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — Step 2 launch block adds the sweep-contract enforcement paragraph (frontmatter `mutates` check before launching). Description field expanded to mention the contract.
- `plugins/vibesubin/skills/manage-assets/SKILL.md` — classification block reformatted from prose-with-bold to a structured fixed-token taxonomy (six tokens) with one-line meaning per token.
- `plugins/vibesubin/skills/project-conventions/SKILL.md` — description mentions "adapts to repo type — app / library / monorepo" alongside existing GitHub Flow / pinned deps framing.

### Removed

- `CLAUDE.md` — added to `.gitignore`, untracked from git (`git rm --cached`). Project-wide rules redistributed: operational policy (never-do, always-do, release process, change-type matrix, invariants, recently-decided) → `MAINTENANCE.md`; pack-level invariants → `docs/PHILOSOPHY.md`; skill-authoring mechanics → `docs/ADDING-A-SKILL.md`; contribution model → `CONTRIBUTING.md`. Maintainer's local copy unchanged; AI tools (Claude Code, Cursor, Aider, Codex plugin) that auto-load `CLAUDE.md` from local working directory continue to do so. `AGENTS.md` also added to `.gitignore` for symmetry. Cross-references in the four shipping docs that pointed to vibesubin's own `CLAUDE.md` updated to point to `MAINTENANCE.md` instead; references to user-repo `CLAUDE.md` (in `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`, `vibesubin`) preserved — those remain about the operator's project, not vibesubin's.

## [0.6.0] — 2026-04-24

### Added

- `plugins/vibesubin/skills/ship-cycle/references/pr-branch-conventions.md` — new 294-line reference enforcing GitHub Flow branch naming (`<type>/<issue-N>-<slug>`), Conventional Commits + mandatory `Closes #<N>` footer, 6-section PR template (Context / What changed / Test plan / Docs plan / Risk / Handoff notes), merge-strategy detection (repo settings → `CONTRIBUTING.md` → `--squash` default), rebase-first workflow with `--force-with-lease`, CI green gate rules (all checks including optional must be SUCCESS or NEUTRAL; SKIPPED is yellow; flaky gets one re-run), force-push policy (never to `main`/`master`/`release/*`), protected-branch invariants, worked examples for both GitHub and PRD tracks.
- `plugins/vibesubin/skills/ship-cycle/references/prd-track.md` — new 221-line reference for the local-file track on non-GitHub hosts. File layout under `docs/release-cycle/vX.Y.Z/` (PRD.md + `issues/NNN-slug.md` + CHANGELOG.draft.md + release-notes.md), issue-as-markdown template with frontmatter (`number`, `title`, `status`, `labels`, `milestone`, `branch`, `pr`, `closes_via`), step-by-step GitHub→PRD mapping table, closing-an-issue procedure, CHANGELOG aggregation shell script, release-notes-as-commit rule (differs from GitHub track's `/tmp` file — this is the only invariant that differs between tracks), host adapter pointer table for GitLab / Gitea / Bitbucket / plain-git.
- `plugins/vibesubin/skills/vibesubin/references/layperson-translation.md` — new 123-line reference for the opt-in `explain=layperson` marker. 3-dimension block per finding (*"왜 이것을 해야 하나요? / Why should you do this?"* + *"왜 중요한 작업인가요? / Why is it important?"* + *"그래서 무엇을 하나요? / So what gets done?"*), severity-to-urgency translation (CRITICAL → *"지금 당장"*, HIGH → *"이번 주 안에"*, MEDIUM → *"다음 릴리즈 전까지"*, LOW → *"시간 날 때"*), pretty box format with box-drawing characters, jargon glossary (SQL injection / dependency / lint / hotspot / CI / rebase / force push / semver / lockfile), bilingual examples (Korean + English full boxes, Japanese/Chinese localized header pointers), combination rule with `tone=harsh`, when-not-to-use.
- `plugins/vibesubin/skills/vibesubin/references/skill-conflicts.md` — new 196-line canonical catalog of 4 skill-pair conflicts with gap / reason / basis per side. Pair 1: `refactor-verify` ↔ `audit-security` on sequencing (ACTIVE vuln → audit first; LATENT → refactor first). Pair 2: `unify-design` ↔ `refactor-verify` on component consolidation (hand-off, not conflict — unify-design drafts, refactor-verify runs 4-check). Pair 3: `fight-repo-rot` ↔ `project-conventions` on dead dependencies (remove, then verify lockfile resolves). Pair 4: `manage-secrets-env` ↔ `audit-security` on tracked `.env` (required sequence: rotate first, then structural fix). Conflict-surface output shape with box-drawing template. Hand-off vs. true-conflict decision rule. Layperson-mode plain-words supplement rule. Extension rule for new entries.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — new `## Layperson mode — plain-language translation` section (~50 lines). Trigger phrase list (`/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"explain like I'm non-technical"*, *"initiate easy mode"*, *"非開発者でも分かるように"*, *"やさしい言葉で"*, *"用通俗的话解释"*, *"给外行看的版本"*). Marker propagation rule (`explain=layperson` stacks with `tone=harsh` and `sweep=read-only`). 3-dimension block, severity translation, pretty box format pointer, what-does-NOT-change rule.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — new `## Skill conflicts — gap, reason, basis` section (~15 lines). Pointer to catalog with output shape and layperson-mode supplement rule.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — Step 3 synthesis rules gained two entries: rule 6 (*"Check for skill conflicts against `references/skill-conflicts.md`; emit `⚠ Skill conflict` block if triggered"*) and rule 7 (*"Apply layperson layer if `explain=layperson` marker active"*). Step 4 report format gained a `## Skill conflicts (if any fired)` section with a worked example.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — Step 2 parallel launch block gained the layperson marker propagation example (`"tone=harsh, explain=layperson, sweep=read-only — …"`). Router tree (Mode 2) gained a layperson-mode trigger branch (between "full check" and "none of the above").
- Every 11 worker SKILL.md file gained a new `## Layperson mode — plain-language translation` section (15-27 lines each), inserted immediately after the existing `## Harsh mode — no hedging`. Each section declares the trigger phrases, the 3-dimension block with skill-specific content (what human impact / what urgency / what concrete action per that skill's findings), skill-specific severity translation mapping, pointer to the shared `layperson-translation.md` for the box format, and the what-does-NOT-change rule. Workers: `refactor-verify`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`, `codex-fix`, `ship-cycle`.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — new `### Step 1.5 — Track selection` sub-step between Step 1 and Step 2. Surfaces the detected track (GitHub / PRD) and accepts operator override (e.g., GitHub-repo operator may prefer PRD track for a local-first audit trail). ship-cycle no longer hard-exits on non-GitHub hosts.

### Changed

- `plugins/vibesubin/skills/ship-cycle/SKILL.md` frontmatter `description` — now mentions GitHub Flow branch enforcement, Conventional Commits, mandatory PR template, rebase-first merge, and the two-track system. "On any non-GitHub host emits a one-line fallback and exits" phrasing removed.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — `## Host requirement and preconditions` section renamed to `## Host check and track selection`. Detection snippet now sets `HAS_GH_REPO` / `HAS_GH_AUTH` flags rather than printing string markers. Hard-exit path replaced with PRD track fallback pointer.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — Assumptions block gained `Track:` and `Merge strategy:` fields. `Existing branch convention:` field now references `references/pr-branch-conventions.md` for detection rules.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — Step 9 (Branch + execute) default branch shape changed from `issue-<N>-<slug>` to `<type>/issue-<N>-<kebab-slug>` (type prefix added per `pr-branch-conventions.md` §1). Explicit link to the conventions file for branch / commit / PR rules.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — Step 9 commit/PR hygiene now references `pr-branch-conventions.md` §2 (Conventional Commits + `Closes #<N>` footer), §3 (6-section PR template), §4 (merge strategy detection), and §5 (rebase-first workflow, `--force-with-lease` only, no force-push to protected branches).
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — Step 9b CI green gate tightened per `pr-branch-conventions.md` §7: all checks (including optional) must be SUCCESS or NEUTRAL; SKIPPED requires operator confirmation before merge; flaky checks get one re-run. Merge strategy flag is now variable (`--squash` | `--rebase` | `--merge`) per §4 repo-setting detection.
- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — "When not to use ship-cycle" list: removed "Non-GitHub host: the host check exits gracefully" entry. The PRD track now handles that case.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` frontmatter `description` — now mentions layperson mode (3-dimension box format) and skill-conflict surfacing alongside the existing harsh-mode mention.
- `README.md` — "What vibesubin is, and what it isn't" section tightened. The verbose "Read-only sweeps vs. skills that actually edit" sub-section was collapsed into a 3-bullet "Two ways to use it — sweep vs. direct call" block.
- `README.md` — single 11-row "Today's lineup" table replaced with 5 category-grouped tables: **Code quality** (5: refactor-verify, audit-security, fight-repo-rot, manage-assets, unify-design), **Docs & AI-friendliness** (2: write-for-ai, project-conventions), **Infra & config** (2: setup-ci, manage-secrets-env), **Release process** (1: ship-cycle), **Host-specific wrappers** (1: codex-fix).
- `README.md` — `/vibesubin` command section: tightened prose, added **Layperson mode** bullet (trigger phrases + 3-dimension block mention + link to `references/layperson-translation.md`) and **Skill conflicts** bullet (link to `references/skill-conflicts.md`).
- `README.md` — "The skills" deep-dive reorganized under the same 5 category headings. Per-skill writeups tightened (same technical content, shorter prose). Skill anchors changed from `#1-refactor-verify` / `#2-audit-security` / … style to `#refactor-verify` / `#audit-security` / … (plain, no numbers).
- `README.md` — `ship-cycle` writeup gained a two-track mention (GitHub default + PRD-on-disk under `docs/release-cycle/vX.Y.Z/`) and an enforced-conventions block (GitHub Flow branches `<type>/<issue-N>-<slug>`, Conventional Commits + mandatory `Closes #<N>`, 6-section PR template, rebase-first with `--force-with-lease`, no force-push to `main`/`master`/`release/*`). Links to `references/pr-branch-conventions.md`.
- `README.ko.md`, `README.ja.md`, `README.zh.md` — same structural changes as EN (5 category tables, tightened skills section, Layperson-mode + Skill-conflicts bullets, two-track ship-cycle mention with enforced conventions, plain anchors) with each file's voice preserved. Line counts: `README.ko.md` 316 → 299, `README.ja.md` 312 → 297, `README.zh.md` 312 → 297.
- Plugin version `0.5.0` → `0.6.0` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`. Minor bump: opt-in layperson mode (new output style), skill-conflict surfacing (new umbrella behavior), ship-cycle two-track split (PRD track is a new execution path), enforced branch/PR conventions (new contractual rules for workers).

### Removed

- `plugins/vibesubin/skills/ship-cycle/SKILL.md` — hard-exit path on non-GitHub hosts. Replaced by fall-through to Step 1.5 (Track selection) with the PRD track as the fallback.

### Security

- `.gitignore` — explicit entries for `.mypy_cache/` and `.pytest_cache/` added under the Python-tooling section. Previously covered only by each tool's auto-generated internal `.gitignore` inside the cache directory; root-level explicit ignore prevents the cache from leaking if a user removes the internal file or if tool defaults change. Caches must never be tracked under any circumstance.

## [0.5.0] — 2026-04-22

### Added

- `scripts/validate_skills.py` — four new invariant checks. **Check A** asserts `## Harsh mode — no hedging` heading is present in every worker SKILL.md (mirrors root `CLAUDE.md` never-do #4). **Check B** asserts the `sweep=read-only` marker is present in the six editable workers (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`) — enforces never-do #7. **Check C** asserts manifest version sync between `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json` — enforces never-do #8. **Check D** asserts no path-traversal attempts in backtick-quoted promised paths (a hostile `` `references/../../../outside.md` `` now fails validation instead of stat-ing outside the repo). Success line now enumerates all checks; verbose output adds per-skill summary `N/500 lines, harsh=✓, sweep-marker=✓ (or N/A), asset-paths=M`.
- `scripts/validate_skills.py` — new `--root <path>` CLI flag for pointing the validator at a fixture tree. Default behavior unchanged; enables the test suite to run without mutating the real repo.
- `tests/test_validate_skills.py` — pytest suite covering all six validator checks with `tmp_path` fixtures. Tests include: good-skill passes, 501-line overflow fails, missing asset fails, path-traversal rejected, harsh-mode missing fails, sweep-marker missing fails for editable workers, sweep-marker exempt for diagnosis-only workers, manifest version mismatch fails, manifest version sync passes. 11 tests in total.
- `.github/workflows/validate-skills.yml` — new `pytest` step runs after the validator check. CI green now requires both the validator AND the test suite to pass.
- `docs/ADDING-A-SKILL.md` — new canonical doc (136 lines) for contributors and AI sessions authoring new skills. Covers: category cap check, directory layout, frontmatter schema with field rules, required sections in order (state-assumptions, procedure, sweep-mode, harsh-mode, things-not-to-do, 4-part output, hand-offs), the validator contract, the 4-part output shape template, the per-change-type file checklist, wrapper-skill rules (PHILOSOPHY #9), common failure modes. Linked from `CLAUDE.md`.
- `plugins/vibesubin/skills/audit-security/SKILL.md` — new `## Sweep mode — read-only audit` section (~16 lines). audit-security is pure-diagnosis by default, so the `sweep=read-only` marker is decorative, but the section documents the trimmed output shape for `/vibesubin` synthesis (stats + stoplight + CRITICAL/HIGH only; defers per-finding triage dialog; direct `/audit-security` call keeps the full 10-category report).
- `ship-cycle/SKILL.md` — `### Step 0.5 — Offer upstream review` inserted before Step 1. When intake has no findings, the skill offers three paths (invoke `/vibesubin` sweep, invoke a targeted worker, proceed with operator-pasted findings) before running the rest of the procedure. ship-cycle does not run the review itself; it orchestrates around review output.
- `ship-cycle/SKILL.md` — `### Step 5.5 — Write PRD.md` inserted between Step 5 and Step 6. Produces a single PRD file (or inline block for <3-issue cycles) that themes the candidate issues, names north-star goals, success metrics, and deferred items. Follows the new template at `references/prd-template.md`. Operator approves the PRD before clustering runs.
- `ship-cycle/SKILL.md` — `#### Step 9a — Parallel dispatch for independent issues` sub-step. When candidate issues share no files and have no cross-issue dependency, dispatch them as parallel Task-tool subagents. Documents the `opus` model default (per project global CLAUDE.md), max-effort default, and 10+-worker simultaneous ceiling. Sequential only when issues share files or depend on each other.
- `ship-cycle/SKILL.md` — `#### Step 9b — CI green gate before merge` sub-step. Explicit `gh pr view ... statusCheckRollup` check before `gh pr merge`, with the shell snippet. Defense-in-depth on top of branch protection; PRs in a milestone no longer merge with red CI by accident.
- `ship-cycle/SKILL.md` — Step 5 now requires three mandatory acceptance-criteria fields per issue: test plan (scoped by label), docs plan (every doc that updates in the same PR), handoff notes (what the next AI session needs + already-done-at links). Missing any field blocks Step 6 (cluster) until the operator fills it.
- `ship-cycle/SKILL.md` — Step 11 (audit trail) now requires the handoff-notes block to be copied from the issue body into the close comment at merge time.
- `ship-cycle/references/issue-body-template.md` — three new mandatory sections with matching bilingual (English + Korean) worked examples: `## Test plan (required — scoped by label)` with a label-to-required-test table covering bug / feat / perf / refactor / docs / chore / security / ci; `## Docs plan (required — lands in same PR as the code fix)` with a file-to-change-type table enforcing atomic docs updates; `## Handoff notes (required — for the next AI session)` with "what next session needs to know" and "already-done-at" subsections.
- `ship-cycle/references/release-pipeline.md` — two new CI-green verification blocks. Preflight: every merged PR in the milestone closed with SUCCESS status on required checks. Pre-tag: `main`'s latest run is green before `git tag -a`. Both use `gh` + `statusCheckRollup` as the authoritative source.
- `ship-cycle/references/prd-template.md` — new 84-line template for the PRD file that Step 5.5 produces. Sections: Context, 북극성 목표 (north-star goals), Themes (per-theme Objective + Issues + Success criterion + Priority), Milestone cluster plan, Success metrics, Out of scope, Already-done-at.

### Changed

- `.gitignore` — added `*.pem *.key id_rsa* id_ed25519* *credentials* secrets/ *.pfx *.p12` under a new `# secrets — keep ignored` block. Root `.gitignore` now matches the pack's own `manage-secrets-env` template defaults — the pack publishes a secrets-hygiene skill and now eats its own dogfood.
- `install.sh:62` — `mkdir -p "${dst}"` now guarded by `${DRY_RUN}` check. Dry-run no longer creates `~/.claude/skills` directories — previously it violated its own no-mutation contract.
- `install.sh:91` — `--force` path now branches on `[ -L "${target}" ]` before destructive action. Symlinks are removed via plain `rm "${target}"`; real files / directories via `rm -rf -- "${target}"` with `--` to block option-injection on exotic filenames. Blocks the local foot-gun where a pre-existing symlink at the install target could cause `rm -rf` to follow the link.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` — umbrella's `## Tone: balanced (default) vs. harsh (opt-in)` heading renamed to `## Harsh mode — no hedging` to match the canonical heading used by all 11 worker skills. Sub-sections unchanged. Aligns with new validator Check A (the umbrella was the lone exception before the rename).
- `plugins/vibesubin/skills/codex-fix/SKILL.md` — `## Harsh mode` heading updated to canonical `## Harsh mode — no hedging` (added em-dash suffix). Body content (delegation-only) unchanged. Required by validator Check A.
- `MAINTENANCE.md` — "Add language coverage" procedure no longer references `audit-security/references/language-scanners.md` or `fight-repo-rot/references/rot-metrics.md` (neither file ever existed). Now points at `refactor-verify/references/language-smoke-tests.md` (actual file) and notes that bespoke LOC / complexity tooling goes inline into the relevant `SKILL.md`.
- `MAINTENANCE.md` — AI-session reading order now lists `CLAUDE.md` as item 1. Was missing entirely; `CLAUDE.md` itself says *"read this file first in every new session"* so the omission was a direct contradiction.
- `MAINTENANCE.md` — new sub-section pointing to `docs/ADDING-A-SKILL.md` as the canonical skill-authoring walkthrough.
- `CLAUDE.md` — after the change-type matrix, added one line: *"Canonical skill-authoring mechanics: see `docs/ADDING-A-SKILL.md`..."*. Matrix itself unchanged.
- `CHANGELOG.md` [0.4.0] — P2-bullet description accuracy fix. Previously claimed *"universal bullet 'Don't add features the operator did not request' in all 10 existing worker skills"* — actually 6 skills use the universal phrase, 4 use skill-specific anchored variants (`audit-security` → *"Don't expand the audit scope beyond what was asked"*, `project-conventions` → *"Don't impose conventions the operator didn't ask for"*, `manage-assets` → *"Don't expand the diagnosis scope beyond what was asked"*, `setup-ci` → *"Don't scaffold workflows the operator didn't ask for"*, `fight-repo-rot` → *"Don't expand the diagnosis scope beyond what was asked"*). Corrected entry lists both forms.
- Plugin version `0.4.0` → `0.5.0` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`. Minor bump reflects validator capability expansion, ship-cycle skill improvements, new contributor doc, and new test harness.

### Fixed

- `plugins/vibesubin/skills/fight-repo-rot/SKILL.md` frontmatter description and body — two occurrences of `manage-config-env` (skill split in v0.3.0 into `manage-secrets-env` + `project-conventions`) replaced with `project-conventions` for hardcoded-path hand-off routing.
- `README.md:161` — `manage-config-env` hand-off reference replaced with `project-conventions`. The three translated READMEs (`README.ko.md`, `README.ja.md`, `README.zh.md`) were already clean from the v0.3.0 translation pass — verified.
- `plugins/vibesubin/skills/manage-secrets-env/templates/.env.example.template:8` — *"See `manage-config-env`'s 'Startup validation' section"* corrected to *"See `manage-secrets-env`'s 'Startup validation' section"*. Template ships into user repos, so the broken reference was leaking into every project running the skill.

### Removed

- Five empty `references/` directories deleted: `fight-repo-rot/references/`, `setup-ci/references/`, `vibesubin/references/`, `manage-assets/references/`, `write-for-ai/references/`. The empty dirs were not tracked by git but surfaced as ambiguous structure cues.

### Security

- `.gitignore` additions prevent accidental commit of common secret-shape filenames even when operators skip the `manage-secrets-env` skill.
- `install.sh --force` symlink-traversal guard blocks the rare local foot-gun where a pre-existing symlink at the install target could cause `rm -rf` to follow the link and delete the linked directory's contents.
- `scripts/validate_skills.py` path-traversal guard on promised paths (Check D above) — a hostile `SKILL.md` with `` `references/../../../etc/passwd` `` in a backtick now fails validation instead of silently triggering a `stat` outside the repo.

## [0.4.1] — skipped

v0.4.1 was considered during dogfood review (2026-04-22) as a fast-follow patch for the four genuine skill-file bugs (manage-config-env ghosts × 3, audit-security Sweep mode missing, CHANGELOG P2 claim inaccuracy, install.sh dry-run contract). Those fixes were bundled into v0.5.0 instead because the same cycle also added validator teeth (harsh-mode / sweep-marker / manifest-sync / path-traversal checks) and the new `docs/ADDING-A-SKILL.md` — all minor-version scope. No separate 0.4.1 tag exists; every change intended for it is in 0.5.0.

## [0.4.0] — 2026-04-21

### Added

- `ship-cycle` skill — the 11th worker and the pack's first process-category skill. Issue-driven development orchestrator. Direct-call only; not part of the `/vibesubin` parallel sweep. Host requirement — GitHub repo with authenticated `gh` CLI; graceful one-line fallback on any other host. 11-step procedure: host check, state assumptions, language elicitation (Korean / English / Japanese / Chinese), intake (pasted list / `/vibesubin` sweep output / named scope), draft bilingual issues, cluster into milestones by semver rules (bug / perf / refactor / test / docs-only → patch; additive feature → minor; breaking → major) with ~5-item patch cap, confirm plan with operator, `gh issue create` per item, branch scaffolding `issue-<N>-<slug>`, per-label hand-off to the right worker (bug / refactor → `refactor-verify`; security → `audit-security` chained to `refactor-verify`; docs → `write-for-ai`; CI → `setup-ci`; secrets → `manage-secrets-env`; deps / branches → `project-conventions`; design → `unify-design`; perf → `refactor-verify` with perf focus), release pipeline (aggregate closed issues → functional-only CHANGELOG entry → bump both manifests → commit → annotated tag → `gh release create` → verify with `gh release view`), close-comment and milestone close for audit trail.
- `ship-cycle/references/issue-body-template.md` — bilingual issue body template. Section headings stay in English (Problem / Acceptance criteria / Implementation notes / Linked) for `gh` parsing stability; body prose in operator-chosen language.
- `ship-cycle/references/milestone-rules.md` — semver cadence decision tree with worked examples, ~5-item patch cap, same-milestone clustering heuristics.
- `ship-cycle/references/release-pipeline.md` — actionable release checklist mirroring the process in root `CLAUDE.md`.
- `## State assumptions — before acting` section in all 10 existing worker skills (`refactor-verify`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`, `codex-fix`). Each section surfaces an explicit `Assumptions` block (input shape / environment / intent) before any procedural step, with skill-specific typical items and stop-and-ask triggers. Karpathy Principle 1 (Think Before Coding) enforced in-skill, not via pack philosophy alone.
- `## Things not to do` now includes a Karpathy P2 anchor in every worker skill — 6 skills use the universal phrase *"Don't add features the operator did not request"*, 4 skills use skill-specific anchored variants (e.g., *"Don't expand the audit scope beyond what was asked"* for `audit-security`, *"Don't impose conventions the operator didn't ask for"* for `project-conventions`) that enforce the same principle against each skill's concrete scope-creep scenarios. Anchored variants were an intentional v0.4.0 polish — the principle is enforced in all 10 existing worker skills; the wording is not uniform and that is by design.
- `docs/PHILOSOPHY.md` invariant #10 — "Code hygiene and process are different categories". Documents the 10-hygiene + 1-process split and why the two buckets do not share a cap.
- `README.md`, `README.ko.md`, `README.ja.md`, `README.zh.md` — new § 11 `ship-cycle` section in each, skill-table row 11 with locale-appropriate trigger phrases, new workflow bullet *"Planning a release"* in the four language variants, and the *"Read-only sweeps vs. skills that actually edit"* subsection updated from 3 + 6 + 1 to 3 + 6 + 2 with explicit "10 code-hygiene workers + 1 process worker" category framing.

### Changed

- Plugin version `0.3.3` → `0.4.0` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`. Minor bump reflects one new worker skill and one new skill category.
- Plugin descriptions in both manifests updated to mention the new issue-driven release-cycle orchestrator.
- `CLAUDE.md` never-do #2 — rewritten from *"Never add a new worker skill past 10"* to *"Never add a new worker skill past the 10 + 1 category cap"*. As of v0.4.0 all 11 slots are used: 10 code hygiene (`refactor-verify`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`, `codex-fix`) + 1 process (`ship-cycle`). Each category has its own cap; future growth must extend, split, or displace within the category.
- `CLAUDE.md` change-type matrix — added "Cut a release via ship-cycle" row pointing the end-to-end flow at the new skill.
- `CLAUDE.md` load-bearing invariants table — added "Category split is enforced (10 hygiene + 1 process)" row with violation symptom documented.
- `CLAUDE.md` "Recently decided" — two new 2026-04-21 entries: the 10 + 1 category split decision, and the karpathy-principles internalization decision (no README shoutout — the four principles are now first-class vibesubin invariants enforced in every worker).
- `docs/PHILOSOPHY.md` "Load-bearing vs flexible" — updated *"the nine rules above"* to *"the ten rules above"* following the addition of invariant #10.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` routing tree — new branch for `ship-cycle` trigger phrases (*"plan a release"*, *"이슈로 남기고 처리"*, *"cut a release"*, *"이슈 드리븐"*, *"리리즈 계획"*, *"bundle these findings into issues"*, etc.). Branch documents the GitHub + `gh` host requirement and graceful fallback.
- `plugins/vibesubin/skills/vibesubin/SKILL.md` integration notes — new bullet on post-sweep issue generation: after the sweep, the operator invokes `/ship-cycle` explicitly with the sweep output as input. The parallel sweep launch block stays at exactly 9 specialists — `ship-cycle` is not added, consistent with the wrapper-skills-don't-sweep rule established with `codex-fix`.

## [0.3.3] — 2026-04-15

### Fixed

- `codex-fix/SKILL.md` — the 0.3.2 version instructed Claude to *"invoke `/codex:rescue` with the templated prompt"* and embedded a code block with plain-text slash-command syntax. Slash-command text inside a response body is just a text string and does nothing — it does not execute the slash command and does not dispatch the Codex plugin. The skill now invokes the Codex rescue subagent via the `Task` tool with `subagent_type: "codex:codex-rescue"`, which is the actual Claude Code plugin dispatch mechanism. The templated prompt is passed as the `prompt` argument of the Task call.
- `codex-fix/SKILL.md` frontmatter `allowed-tools` — added `Task`, `Bash(ls *)`, and `Bash(test *)`. Without `Task` the skill could not invoke the subagent at all; without `ls` / `test` the filesystem-based plugin-presence check could not run. The 0.3.2 allowed-tools list omitted all three.
- `codex-fix/SKILL.md` Step 1 (host check) — now documents two detection paths: primary (inspect Claude Code's available-subagents list for `codex:codex-rescue`) and secondary (filesystem check `test -d ~/.claude/plugins/codex`). Previously the check was described as "confirm `/codex:rescue` is available" without specifying the mechanism, which led to the subagent-invocation regression above.
- `codex-fix/SKILL.md` Step 3 (invocation) — rewritten from a plain-text slash-command block to an explicit `Task(subagent_type="codex:codex-rescue", description, prompt)` tool call. The templated review prompt is unchanged; only the dispatch mechanism is fixed. New paragraph added: if the `Task` call itself fails (subagent disabled mid-call, Codex CLI timeout, unexpected subagent error), emit a one-line failure that references the underlying error and stop — do not retry automatically.
- `codex-fix/SKILL.md` "Things not to do" — new bullet: *"Don't write `/codex:rescue ...` as plain text in a response."* Documents the 0.3.2 regression explicitly so future maintainers do not reintroduce it.
- `README.ja.md` — skill-table trigger examples for `codex-fix` on line 59 were in Korean (`「codex 돌려서 고쳐줘」`, `「run codex and fix」`, `「codex driven fix」`) in 0.3.2 because the ko/ja batch copied without per-language localization. Replaced with Japanese equivalents (`「Codex でチェックして直して」`, `「codex fix」`, `「run codex and fix」`).
- `README.zh.md` — same translation leakage as above on line 59. Replaced with Chinese equivalents (`"用 codex 跑一遍再修"`, `"codex fix"`, `"run codex and fix"`).
- `README.ko.md` § 10 — two minor prose-polish fixes: `"의도된 유일한"` → `"의도적으로 유일한"` (less translated feel), and `"소리내서 에러나지 않아요"` → `"시끄럽게 에러를 뱉지도 않습니다"` (more idiomatic).

### Changed

- Plugin version `0.3.2` → `0.3.3` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`.

## [0.3.2] — 2026-04-15

### Added

- `refactor-verify/SKILL.md` — new "Review-driven fix mode" section. Accepts external review reports from any source (pasted notes, PR review, Sentry alert, `gitleaks`/`pip-audit`/`cargo audit`/`govulncheck`, Semgrep/Bandit, hand-off from a wrapper skill). Procedure: capture review snapshot SHA, capture recent commit context (`git log`, `git diff --stat`, `git status`), parse and normalize findings, triage each (real / false-positive / defer / duplicate), plan as dependency tree, execute leaves-up with 4-check verification (relaxed AST-diff for intentionally behavior-changing fixes, full call-site closure on the untouched surface), commit each fix with a back-reference to the review item (`<type>(<scope>): resolve <review-source>#<item-id> — <subject>`), produce a resolution report table.
- `codex-fix` skill — thin Claude Code + Codex plugin wrapper (~100 lines). Direct-call only; not part of the `/vibesubin` parallel sweep. First action: host check for `/codex:rescue` availability. On matching host: capture branch diff scope (`BASE = merge-base HEAD main`, `REVIEW_SHA = git rev-parse HEAD`, `git diff --stat`, `git log`, `git status`), warn if working tree is dirty, invoke `/codex:rescue` with a templated prompt (security / correctness / performance / resource management / concurrency categories), collect raw findings, hand off to `refactor-verify`'s review-driven fix mode with `review_source=codex-rescue`, `review_sha`, `findings_raw`, `branch_context`. On any non-matching host: emit one-line fallback (*"Codex plugin not detected — this skill is Claude Code + Codex specific..."*) and exit without error.
- `docs/PHILOSOPHY.md` — new invariant 9 "Portable engines can have host-specific wrappers". Wrappers declare host dependency in frontmatter, check host as first action, emit graceful one-line fallback on non-matching hosts, delegate everything substantial to a portable engine skill, have no sweep mode. Load-bearing-vs-flexible summary updated from "seven rules above" to "nine rules above".
- `vibesubin/SKILL.md` routing tree — two new branches: one for `codex-fix` triggers (`"codex 돌려서 고쳐"`, `"codex fix"`, `"rescue 돌리고 수정"`, `"run codex and fix"`, `"codex로 한번 검사"`, `"codex driven fix"`), and one for `refactor-verify` review-driven mode triggers (`"resolve these findings"`, `"fix this review"`, `"리뷰 사항 처리"`, `"이 리뷰 고쳐줘"`, pasted review reports).
- `README.md` skill table — row 10 for `codex-fix` with explicit host-requirement note. New § 10 section covering the skill's rationale, thinness, host requirement, `/codex-fix` vs `/refactor-verify` direct-call decision table, and link to invariant 9. Direct-call list adds `/codex-fix` as a host-specific entry. "Three skills never edit" phrasing updated to split the 10 workers into "three never-edit (fight-repo-rot, audit-security, manage-assets) / six real workers / one host-specific wrapper". New "End-of-edit Codex loop" workflow bullet.
- `README.ko.md`, `README.ja.md`, `README.zh.md` — matching targeted edits in natural voice for each language: direct-call list bullet, three-skills phrasing, skill table row, § 10 section, workflow bullet. No prose or section restructuring.

### Changed

- Plugin version `0.3.1` → `0.3.2` in `.claude-plugin/marketplace.json` and `plugins/vibesubin/.claude-plugin/plugin.json`. Both descriptions updated to note the Codex wrapper.
- Pack worker count: 9 → 10 (umbrella not counted). The 10-worker cap is now exactly reached; any future new capability must extend, split, or displace an existing skill.
- `CLAUDE.md` — "Never add a new worker skill past 10" updated to note the cap is now reached and to enumerate the 10 slots. "Recently decided" section adds the portable-engine-plus-thin-wrapper precedent (invariant 9) decided 2026-04-15.

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

[Unreleased]: https://github.com/subinium/vibesubin/compare/v0.3.3...HEAD
[0.3.3]: https://github.com/subinium/vibesubin/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/subinium/vibesubin/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/subinium/vibesubin/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/subinium/vibesubin/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/subinium/vibesubin/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/subinium/vibesubin/releases/tag/v0.1.0
