---
name: codex-fix
description: Post-edit loop that invokes `/codex:rescue` for a second-model review of the current branch, collects the findings, and hands them off to `refactor-verify`'s review-driven fix mode for triage, verification, and committed resolution. A thin host-specific wrapper — the portable review-driven engine lives in `refactor-verify`. Requires Claude Code with the Codex plugin installed; on every other host the skill emits a one-line fallback and exits without error. Operators whose review findings come from any other source (pasted notes, human PR review, Sentry alert, gitleaks output, Semgrep report, GitHub Advanced Security) should invoke `refactor-verify` directly and skip this wrapper entirely.
when_to_use: Trigger on "codex 돌려서 고쳐줘", "codex로 한번 검사하고 수정", "codex fix", "codex driven fix", "rescue 돌리고 수정해줘", "run codex rescue and fix", "/codex-fix", typically at the end of a batch of edits and before a merge. For review-driven fixes from any other source (pasted findings, a PR review, a scanner report, Sentry), skip this wrapper and invoke `refactor-verify` directly with the findings — the engine is the same, only the input adapter differs.
allowed-tools: Read Grep Glob Bash(git diff *) Bash(git log *) Bash(git status *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git blame *)
---

# codex-fix

A thin, deliberately host-specific wrapper for one workflow: *"I've finished a batch of edits — run Codex for a second-model review, feed the findings back, let Claude resolve them with verification."*

This wrapper owns only the Codex-specific glue: the host check, the templated `/codex:rescue` prompt, the output collection, and the hand-off. Everything after the hand-off — parsing and normalizing findings, triaging real / false-positive / defer / duplicate, mapping each finding to a commit via `git blame`, planning a dependency tree, executing leaves-up, verifying each fix with the applicable checks, committing with a back-reference to the review item, and producing the resolution report — belongs to `refactor-verify`'s review-driven fix mode. This skill **does not duplicate any of it**.

If you are not on Claude Code with the Codex plugin installed, you do not need this skill. `refactor-verify` accepts pasted review findings from any source directly — this wrapper just automates the invocation step for operators who run the Codex loop often enough that the copy-paste was adding friction.

## Host requirement

This skill only fires on **Claude Code with the Codex plugin installed**. On every other host (Codex CLI itself, Cursor, Copilot, Cline, or Claude Code without the plugin), the skill's first action is a graceful one-line fallback and exit. It never hangs, never errors loudly, never falls back to asking the operator for pasted findings (that is `refactor-verify`'s path directly — this wrapper has nothing to add there).

## Procedure

**1. Check host.** Confirm `/codex:rescue` is available in the current session. If the command is not registered — because the Codex plugin is not installed, or the session is not Claude Code, or the plugin is disabled — respond with exactly one sentence and stop:

> *"Codex plugin not detected — this skill is Claude Code + Codex specific. To resolve a review from a different source (pasted findings, a PR review, a scanner report), invoke `/refactor-verify` directly with the findings."*

No retry loop, no stack trace, no pasted-findings prompt. Graceful pass is the expected outcome on non-matching hosts, and it is **not an error** — just log it and stop.

**2. Capture the branch state as the review scope.** The default scope is the current branch's diff against its base — not the whole repo. Reviewing the whole repo is what `/vibesubin` is for.

```bash
BASE=$(git merge-base HEAD main 2>/dev/null \
       || git merge-base HEAD master 2>/dev/null \
       || echo "HEAD~10")
REVIEW_SHA=$(git rev-parse HEAD)
git diff --stat "$BASE"...HEAD          # what changed
git log  --oneline "$BASE"..HEAD        # commits on the branch
git status                              # current dirty state
```

If the working tree is dirty, warn the operator: *"Uncommitted changes present. Codex should review a clean snapshot — commit or stash before the review?"* Do not proceed without confirmation. A dirty review snapshot injects bugs because Codex's findings become ambiguous (was it fixed in the uncommitted diff or not?).

**3. Invoke `/codex:rescue` with the templated prompt.** The prompt scopes the review to the branch diff, names the categories the operator cares about, and asks for a structured response:

```
/codex:rescue Run a deep code review of the current branch's changes
($BASE..HEAD). Return findings as markdown with file:line references.
Focus on: (1) security — injection, auth bypass, secret exposure,
unsafe deserialization; (2) correctness — null handling, race
conditions, error swallowing, off-by-one, incorrect async; (3)
performance — N+1 queries, hot-path allocations, unnecessary work;
(4) resource management — connection leaks, handle leaks, memory
leaks, missing cleanup; (5) concurrency — unsynchronized shared
state, deadlock risk, TOCTOU bugs.

One finding per bullet. Each finding: file:line, one-line description,
severity (CRITICAL / HIGH / MEDIUM / LOW). Skip style nits and missing
comments unless they hide a bug. If the diff is clean, say so
explicitly and return an empty findings list.
```

Collect Codex's response as raw markdown. **Do not interpret it here** — parsing and triage belong to `refactor-verify`, not this wrapper.

**4. Hand off to `refactor-verify`'s review-driven fix mode.** Pass the following as structured input:

- `review_source`: `codex-rescue`
- `review_sha`: the value of `REVIEW_SHA` captured in step 2
- `findings_raw`: Codex's raw markdown output from step 3
- `branch_context`: the `git log`, `git diff --stat`, `git status` output from step 2

`refactor-verify` owns every step from here: parsing and normalizing findings, triaging (real / false-positive / defer / duplicate), mapping each item to a commit via `git blame`, planning the dependency tree, executing leaves-up, verifying each fix with the applicable checks (relaxed AST diff for intentionally behavior-changing fixes, full call-site closure on the untouched surface), committing with the `resolve codex-rescue#<item-id> — <subject>` back-reference format, and producing the resolution report. This wrapper's job ends at the hand-off.

**5. Do not re-parse, re-verify, or re-commit.** Every step after the hand-off belongs to `refactor-verify`. If `refactor-verify` returns with unresolved items, deferred items, a baseline-red warning, or a partial resolution, surface the result to the operator unchanged. This wrapper is **not** a second-opinion on the refactor-verify engine.

## Things not to do

- **Don't run without Codex.** If the host check fails, do not synthesize fake findings, do not fall back to the 9 umbrella specialists, do not prompt the operator for pasted findings (that path belongs to `refactor-verify` directly — invoke it instead). Emit the one-line fallback and stop.
- **Don't bypass `refactor-verify`'s verification.** The entire point of this wrapper is that it inherits `refactor-verify`'s 4-check discipline. Applying fixes without the verification layer is a regression of the pack's core promise.
- **Don't review the whole repo.** The default scope is the branch diff (`BASE..HEAD`). Reviewing the full repo is what `/vibesubin` is for — this skill is a post-edit loop, not a sweep.
- **Don't participate in the `/vibesubin` parallel sweep.** This wrapper is direct-call only. The umbrella does not launch it. It requires an external model and writes files; both break the sweep's read-only + portable invariants. If a future maintainer tries to add this skill to the umbrella's parallel launch block, stop and read `docs/PHILOSOPHY.md` rule 9.
- **Don't add a sweep-mode section to this SKILL.md.** Its absence is deliberate. Documented here explicitly so a future maintainer does not "fix" it by adding one.
- **Don't duplicate the review-driven procedure from `refactor-verify`.** If you find yourself writing parsing logic, triage logic, dependency-tree planning, or verification code in this wrapper, stop — that content belongs in `refactor-verify`. Delete it here and extend `refactor-verify` instead.

## Harsh mode

Inherited from `refactor-verify`. When the operator passes `tone=harsh` (from `/vibesubin harsh` or direct phrasing like *"don't sugarcoat"*, *"매운 맛"*, *"厳しめ"*), this wrapper forwards the marker as part of the hand-off in step 4; `refactor-verify`'s harsh-mode template takes over from there. No separate harsh-mode section lives in this file, and adding one is a mistake — it would duplicate `refactor-verify`'s rules and drift over time.

## Hand-offs

- **Every fix** → `refactor-verify` (review-driven fix mode). This is the only hand-off; everything substantial delegates here.
- **If the operator wants review-driven fix from a non-Codex source** (pasted notes, PR review, Sentry alert, `gitleaks` output, Semgrep report, GitHub Advanced Security, any scanner) → redirect to `refactor-verify` directly. This wrapper is Codex-only by design; other input sources either get their own thin wrapper following the same pattern or go straight to `refactor-verify` with pasted input.

## Why this wrapper exists

Pack philosophy: **portable engine, optional host-specific wrappers.** The review-driven fix engine is portable and lives in `refactor-verify`. This wrapper exists because one specific maintainer runs the Codex loop often enough that the copy-paste step was adding friction session after session. Future host-specific wrappers (Sentry, gitleaks, etc.) would follow the same pattern — a thin adapter for the input source, delegating to `refactor-verify` for everything substantial.

Before adding another such wrapper, ask two questions: *"Is this workflow frequent enough for one operator to justify a worker slot?"* and *"Is the input source's invocation glue non-trivial enough that operators can't just paste it into `refactor-verify` directly?"* If both answers are yes, build the wrapper following this skill's shape: host check first, templated invocation, hand off to `refactor-verify`, no duplicated logic. If either answer is no, skip the wrapper.

This pattern is documented as rule 9 of `docs/PHILOSOPHY.md`: *"Portable engines can have host-specific wrappers."*
