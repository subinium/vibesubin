# Review-driven fix mode

A variant of the standard `refactor-verify` procedure where the trigger is an **external review report** — findings from a second-model pass (via the `codex-fix` wrapper or a hand-pasted `/codex:rescue` output), a human PR review, a security scanner (`gitleaks`, `pip-audit`, `cargo audit`, `govulncheck`), a SAST tool (Semgrep, Bandit), a runtime alert (Sentry), or the operator's own hand-written notes — and the task is to **resolve every item** in the report against the repo's current state.

**Trigger on:** *"resolve these findings"*, *"fix this review"*, *"go through these and fix them"*, *"take this review and apply the fixes"*, *"리뷰 사항 처리해줘"*, *"이 리뷰 고쳐줘"*, *"レビュー項目を直して"*, *"修复这个 review"*, pasted review reports with file:line references, hand-offs from `codex-fix`, or any variant where the operator has a review to resolve.

This mode is **distinct from the standard procedure** in two ways:

1. The work is **seeded from external input**, not from an operator-phrased refactor. The input may arrive as pasted text, a file path, a hand-off from a wrapper skill (like `codex-fix` passing `/codex:rescue` output), or a structured JSON report.
2. Most review-driven fixes **intentionally change behavior** (a security patch, a bug fix, a correctness fix, a missing-mutex addition). The standard "every public name still exists" and "zero-byte AST diff" invariants are relaxed **only for the fixed code**. They still apply with full force to every file the fix did not touch.

Everything else — the snapshot, the dependency tree, the leaves-up execution, the behavioral verification, the call-site closure on the untouched surface — is the same procedure as `SKILL.md`.

## Procedure

**1. Capture the review snapshot.** Record the HEAD SHA the review was taken against. If the operator has committed new changes since the review, flag it and ask whether to re-run the review source or proceed against the stale snapshot. A review is only valid for the commit it was taken on; silently resolving against a moved HEAD injects bugs (a finding might already be fixed, or the line numbers might have shifted).

```bash
REVIEW_SHA=$(git rev-parse HEAD)   # the SHA the review was actually taken on
```

**2. Capture recent commit context.** The skill needs to know which findings came from recent edits (surgical, high confidence) and which are pre-existing (possibly load-bearing, require care):

```bash
git log --oneline -30                                # recent commits
git log --oneline main..HEAD                         # commits on this branch
git diff --stat $(git merge-base HEAD main)...HEAD   # files touched by this branch
git status                                           # current uncommitted state
```

**3. Parse and normalize the findings** into a uniform internal list: `[{id, file, line, severity, category, description, source, excerpt}]`. Source formats vary (Codex markdown, PR review comment, JSON report, plain notes); normalize all to this shape before triaging. A malformed or ambiguous item is its own triage bucket (see step 4).

**4. Triage each finding.** Same four-way classification as `audit-security`:

| Classification | Action |
|---|---|
| **REAL — fix now** | Proceed to planning |
| **REAL — defer** | Log with rationale; not addressed in this session |
| **FALSE POSITIVE** | Explain why in one specific sentence (*"`days` is already clamped to 0..365 on line 391"*); do not "fix" it |
| **DUPLICATE** | Already covered by an existing vibesubin specialist's prior finding; link to that |

For each REAL item, also tag **introduced by recent edits** (fix is surgical, high confidence) or **pre-existing** (fix may touch load-bearing code, confidence LOWer). Use `git blame` on the offending line against `$REVIEW_SHA` to decide.

**5. Plan the fixes as a dependency tree.** This is step 2 of the standard procedure, reused: items that depend on each other (fix the shared helper before the caller that uses it) become parent/child nodes; independent items become parallel leaves. Commit the tree to a scratch file (`.verify-plan.md`, gitignored) before touching any code.

**6. Execute leaves-up, verify each item with the checks that apply.**

- **Behavior-preserving fix** (*"simplify this confusing expression"*, *"deduplicate this logic"*, *"rename for clarity"*): full 4-check verification from the standard procedure applies — symbol-set diff, AST body diff, behavioral verification, call-site closure.
- **Behavior-changing fix** (*"patch this SQL injection"*, *"fix this null deref"*, *"add the missing mutex"*, *"handle the error instead of swallowing it"*):
  - **Step 1 (symbol diff)** applies to untouched files — no unexpected symbol should appear or vanish outside the fix's scope.
  - **Step 4 (AST diff)** is relaxed for the **fixed function itself** (the body change is the point) but still applies to every other function in the same file (an unintended side edit elsewhere is still a bug).
  - **Step 5 (behavioral verification)** applies in full — typecheck, lint, tests all pass after the fix.
  - **Step 6 (call-site closure)** applies in full — if the fix changed a signature, every caller must be updated; if the fix is purely internal, the call-site count is unchanged.

If any check fails for an item, the fix is not done — do not move to the next item. Fix it, re-verify, then advance.

**7. Commit with back-reference.** One commit per review item (or one per tightly-coupled cluster of items). Commit message format:

```
<type>(<scope>): resolve <review-source>#<item-id> — <one-line subject>

<Body: what the review item said, how it was fixed, what was verified.
  Reference the commit that introduced the bug if it is a recent
  regression, or note "pre-existing" if not.>

Verification:
- <command 1>
- <command 2>
```

`<type>` is `fix` for real bugs, `refactor` for behavior-preserving simplification, `perf` for performance, `security` (or `fix` with a `security` scope) for security patches. `<review-source>` is the review tool or human who produced it: `codex-rescue`, `pr-review-#123`, `gitleaks`, `sentry-alert-XYZ`, `manual-review-YYYY-MM-DD`.

**8. Report resolution.** After every item has been addressed, produce a summary table:

```markdown
## Review resolution report

Review source: <codex-rescue | PR #123 | gitleaks | manual>
Review snapshot: <REVIEW_SHA, note if HEAD has moved since>
Items: <N total> — <X resolved> / <Y FP> / <Z deferred> / <W duplicate>

| # | File:line | Severity | Verdict | Resolution | Commit |
|---|---|---|---|---|---|
| 1 | src/api/user.ts:47 | CRITICAL | FIXED | Parameterized query | abc1234 |
| 2 | src/utils/format.ts:91 | MEDIUM | FP | `len` already clamped +1 above | — |
| 3 | src/auth/session.ts:15 | HIGH | DEFERRED | Needs coordinated rotation, separate PR | — |
```

Surface the table to the operator. If any item is still unresolved, say so explicitly — *"3 of 12 items remain deferred; do you want to address them now or in a follow-up PR?"*

## What stays the same

- **Baseline-red rule**: if the repo is red before the session starts, resolution cannot be verified on top; ask the operator to fix the baseline first.
- **Isolation rule**: work in a branch (or worktree), never on `main`.
- **Snapshot rule**: record `REVIEW_SHA` before touching anything, so the diff scope is unambiguous even if the operator wanders into an unrelated edit.
- **Tidy First**: structural commits stay separated from behavioral commits, even inside a single review item's fix if the fix has both kinds.

## What changes

- The standard "preserve behavior" promise is scoped to **untouched files** only; the fixed code is intentionally different by construction.
- The 6-step procedure is **seeded from external review items** instead of the operator's own refactor request.
- Each commit **ties back to a specific review item** via the back-reference format, so reviewers can cross-check resolution item by item.

## Stale-snapshot handling

If the operator has new local commits since `REVIEW_SHA`, the choice is:

- **Re-run the review source** at the new HEAD — preferred when it's cheap (`codex-fix` to re-invoke Codex, paste a fresh `gitleaks` run).
- **Proceed against the stale snapshot** — only when the diff between `REVIEW_SHA` and HEAD is small and unrelated. Annotate every commit message with *"NOTE: review taken on $REVIEW_SHA, applied to $CURRENT_HEAD"* so reviewers see the temporal gap.
- **Refuse** — when the diff is large or touches review-flagged files. Tell the operator to either re-run or rebase.

In harsh mode, refuse becomes the default for any non-trivial drift: *"HEAD moved 12 commits since the review snapshot. Re-run the review or proceed against the stale snapshot with explicit confirmation. Not proceeding silently."*
