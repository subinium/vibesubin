# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/). Plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).

## [Unreleased]

## [0.4.0] — 2026-04-21

### Added

- `ship-cycle` skill — the 11th worker and the pack's first process-category skill. Issue-driven development orchestrator. Direct-call only; not part of the `/vibesubin` parallel sweep. Host requirement — GitHub repo with authenticated `gh` CLI; graceful one-line fallback on any other host. 11-step procedure: host check, state assumptions, language elicitation (Korean / English / Japanese / Chinese), intake (pasted list / `/vibesubin` sweep output / named scope), draft bilingual issues, cluster into milestones by semver rules (bug / perf / refactor / test / docs-only → patch; additive feature → minor; breaking → major) with ~5-item patch cap, confirm plan with operator, `gh issue create` per item, branch scaffolding `issue-<N>-<slug>`, per-label hand-off to the right worker (bug / refactor → `refactor-verify`; security → `audit-security` chained to `refactor-verify`; docs → `write-for-ai`; CI → `setup-ci`; secrets → `manage-secrets-env`; deps / branches → `project-conventions`; design → `unify-design`; perf → `refactor-verify` with perf focus), release pipeline (aggregate closed issues → functional-only CHANGELOG entry → bump both manifests → commit → annotated tag → `gh release create` → verify with `gh release view`), close-comment and milestone close for audit trail.
- `ship-cycle/references/issue-body-template.md` — bilingual issue body template. Section headings stay in English (Problem / Acceptance criteria / Implementation notes / Linked) for `gh` parsing stability; body prose in operator-chosen language.
- `ship-cycle/references/milestone-rules.md` — semver cadence decision tree with worked examples, ~5-item patch cap, same-milestone clustering heuristics.
- `ship-cycle/references/release-pipeline.md` — actionable release checklist mirroring the process in root `CLAUDE.md`.
- `## State assumptions — before acting` section in all 10 existing worker skills (`refactor-verify`, `audit-security`, `fight-repo-rot`, `write-for-ai`, `setup-ci`, `manage-secrets-env`, `project-conventions`, `manage-assets`, `unify-design`, `codex-fix`). Each section surfaces an explicit `Assumptions` block (input shape / environment / intent) before any procedural step, with skill-specific typical items and stop-and-ask triggers. Karpathy Principle 1 (Think Before Coding) enforced in-skill, not via pack philosophy alone.
- `## Things not to do` now includes the universal bullet *"Don't add features the operator did not request"* in all 10 existing worker skills. Karpathy Principle 2 (Simplicity First) enforced as a local invariant in every skill.
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
