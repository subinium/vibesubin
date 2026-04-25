---
name: codex-fix
description: Post-edit loop that invokes `/codex:rescue` for a second-model review of the current branch, collects the findings, and hands them off to `refactor-verify`'s review-driven fix mode for triage, verification, and committed resolution. A thin host-specific wrapper — the portable review-driven engine lives in `refactor-verify`. Requires Claude Code with the Codex plugin installed; on every other host the skill emits a one-line fallback and exits without error. Operators whose review findings come from any other source (pasted notes, human PR review, Sentry alert, gitleaks output, Semgrep report, GitHub Advanced Security) should invoke `refactor-verify` directly and skip this wrapper entirely.
mutates: [direct, external]
when_to_use: Trigger on "codex 돌려서 고쳐줘", "codex로 한번 검사하고 수정", "codex fix", "codex driven fix", "rescue 돌리고 수정해줘", "run codex rescue and fix", "/codex-fix", typically at the end of a batch of edits and before a merge. For review-driven fixes from any other source (pasted findings, a PR review, a scanner report, Sentry), skip this wrapper and invoke `refactor-verify` directly with the findings — the engine is the same, only the input adapter differs.
allowed-tools: Read Grep Glob Task Bash(git diff *) Bash(git log *) Bash(git status *) Bash(git rev-parse *) Bash(git merge-base *) Bash(git blame *) Bash(ls *) Bash(test *)
---

# codex-fix

A thin, deliberately host-specific wrapper for one workflow: *"I've finished a batch of edits — run Codex for a second-model review, feed the findings back, let Claude resolve them with verification."*

This wrapper owns only the Codex-specific glue: the host check, the templated `/codex:rescue` prompt, the output collection, and the hand-off. Everything after the hand-off — parsing and normalizing findings, triaging real / false-positive / defer / duplicate, mapping each finding to a commit via `git blame`, planning a dependency tree, executing leaves-up, verifying each fix with the applicable checks, committing with a back-reference to the review item, and producing the resolution report — belongs to `refactor-verify`'s review-driven fix mode. This skill **does not duplicate any of it**.

If you are not on Claude Code with the Codex plugin installed, you do not need this skill. `refactor-verify` accepts pasted review findings from any source directly — this wrapper just automates the invocation step for operators who run the Codex loop often enough that the copy-paste was adding friction.

## State assumptions — before acting

Before starting the procedure, write an explicit Assumptions block. Don't pick silently between interpretations; surface the choice. If any assumption is wrong or ambiguous, pause and ask — do not proceed on a guess.

Required block:

```
Assumptions:
- Host:              <Claude Code + Codex plugin (primary path) | any other (graceful one-line fallback, exit)>
- Review branch:     <current branch | specified — merge-base with main is the diff scope>
- Working tree:      <clean (proceed) | dirty (warn operator before handing mixed state to Codex)>
- Base reference:    <main (default) | explicit base when current branch has no merge-base with main>
```

Typical items for this skill:

- The branch under review (default: current branch vs its merge-base with main)
- Working tree state (clean required for a clean review; dirty triggers a warning before invocation)
- Codex plugin availability (host check in Step 1 — this Assumptions block is Step 0, the host check is Step 1)

Stop-and-ask triggers:

- Working tree is dirty — warn and confirm before handing the mixed state to Codex
- Current branch has no merge-base with main (detached / new repo / orphan branch) — ask for an explicit base reference instead of assuming main

Silent picks are the most common failure mode: the skill runs, produces plausible output, and the operator doesn't notice the wrong interpretation was chosen. The Assumptions block is cheap insurance.

## Host requirement

This skill only fires on **Claude Code with the Codex plugin installed**. On every other host (Codex CLI itself, Cursor, Copilot, Cline, or Claude Code without the plugin), the skill's first action is a graceful one-line fallback and exit. It never hangs, never errors loudly, never falls back to asking the operator for pasted findings (that is `refactor-verify`'s path directly — this wrapper has nothing to add there).

## Procedure

**1. Check host — confirm the Codex rescue subagent is registered.** This skill invokes Codex via the `Task` tool with `subagent_type: "codex:codex-rescue"`. That subagent is only registered when the Codex plugin is installed on a Claude Code session. Before attempting the Task call, verify availability via either of these detection paths:

- **Primary — inspect the available-subagents list.** Claude Code populates the available-subagents list at session start from installed plugins. Check whether `codex:codex-rescue` appears as a valid `subagent_type` in the current context. If yes, proceed. If no, fall through to the secondary path before giving up.
- **Secondary — filesystem check.**
  ```bash
  test -d "$HOME/.claude/plugins/codex" && echo "plugin-installed" || echo "plugin-missing"
  ```
  If the directory exists but the subagent is still not in the available-subagents list (e.g., the plugin is disabled or its registration step failed), treat that as "not available" and fall through — a present-but-non-functional plugin should still trigger graceful pass, not a half-broken attempt.

**If neither path confirms the subagent is registered**, respond with exactly one sentence and stop:

> *"Codex plugin not detected — this skill is Claude Code + Codex specific. To resolve a review from a different source (pasted findings, a PR review, a scanner report), invoke `/refactor-verify` directly with the findings."*

No retry loop, no stack trace, no pasted-findings prompt. **Graceful pass is the expected outcome on non-matching hosts**, and it is **not an error** — just log it and stop.

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

**3. Invoke the Codex rescue subagent via the `Task` tool.** **Do not** write `/codex:rescue ...` as plain text in your response — slash-command text inside a response body is just a text string and does nothing. The actual invocation mechanism is a `Task` tool call with `subagent_type: "codex:codex-rescue"`. The prompt scopes the review to the branch diff and names the categories the operator cares about:

```
Task(
  subagent_type = "codex:codex-rescue",
  description   = "Deep code review of branch diff",
  prompt        = """
    Run a deep code review of the current branch's changes
    ($BASE..HEAD, where $BASE is the captured base-branch merge-base).
    Return findings as markdown with file:line references.

    Focus on:
    (1) security — injection, auth bypass, secret exposure, unsafe deserialization;
    (2) correctness — null handling, race conditions, error swallowing,
        off-by-one, incorrect async;
    (3) performance — N+1 queries, hot-path allocations, unnecessary work;
    (4) resource management — connection leaks, handle leaks, memory leaks,
        missing cleanup;
    (5) concurrency — unsynchronized shared state, deadlock risk, TOCTOU bugs.

    One finding per bullet. Each finding: file:line, one-line description,
    severity (CRITICAL / HIGH / MEDIUM / LOW). Skip style nits and missing
    comments unless they hide a bug. If the diff is clean, say so explicitly
    and return an empty findings list.
  """
)
```

The `Task` tool returns the subagent's output as a single result message. Collect that output as raw markdown. **Do not interpret it here** — parsing and triage belong to `refactor-verify`, not this wrapper.

**If the `Task` call itself fails** (subagent disabled mid-call, Codex CLI timeout, unexpected subagent error), do not retry automatically. Emit a one-line failure that references the underlying error category — *"Codex rescue failed: `<error summary>`. Falling back — invoke `/refactor-verify` directly with manually-pasted review findings if you still want to run the post-edit loop."* — and stop. A failed subagent invocation is a transient state, not a bug in this wrapper.

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
- **Don't write `/codex:rescue ...` as plain text in a response.** Slash-command text inside a response body is just a text string — it does not execute the slash command and does not dispatch the plugin. The actual invocation mechanism is the `Task` tool with `subagent_type: "codex:codex-rescue"`. If you find yourself about to paste slash-command text into a response as if it were an instruction, stop — that was the 0.3.2 bug and 0.3.3 fixed it precisely to prevent that regression.
- **Don't add features the operator did not request.** This wrapper's job is the host check and the Codex invocation — nothing else. If during the host check you notice the repo has other obvious issues (missing CI, uncommitted secrets, stale deps), report them as hand-off suggestions to the relevant skills — do not act on them. A wrapper that silently expands its scope defeats the "thin wrapper" invariant.

## Harsh mode — no hedging

Inherited from `refactor-verify`. When the operator passes `tone=harsh` (from `/vibesubin harsh` or direct phrasing like *"don't sugarcoat"*, *"매운 맛"*, *"厳しめ"*), this wrapper forwards the marker as part of the hand-off in step 4; `refactor-verify`'s harsh-mode template takes over from there. No harsh-mode body lives in this file — duplicating `refactor-verify`'s rules would only let them drift. The canonical heading is present so `validate_skills.py`'s harsh-mode coverage check passes; the wrapper's job is to forward the marker, not restate the policy.

## Layperson mode — plain-language translation

When the task context contains `explain=layperson` (from `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"explain like I'm non-technical"*, *"非開発者でも分かるように"*, *"用通俗的话解释"*), add a plain-language layer to every finding this skill emits. Combines freely with `tone=harsh`. Full rules at `/plugins/vibesubin/skills/vibesubin/references/layperson-translation.md`.

### Three dimensions per finding

Every finding gets three questions answered in plain language, in the operator's language (Korean / English / Japanese / Chinese):

- **왜 이것을 해야 하나요? / Why should you do this?** — *"한 모델(Claude)이 쓴 코드를 같은 모델이 다시 리뷰하면 놓치는 게 생깁니다. Codex로 2차 리뷰를 받고 그 findings를 그대로 돌려주면 훨씬 정직한 리뷰가 됩니다."*
- **왜 중요한 작업인가요? / Why is it an important task?** — *"혼자 쓰고 혼자 리뷰하는 워크플로우는 'looks good'으로 끝나기 쉬워요. 브랜치 묶음 하나 끝낼 때마다 2차 모델 리뷰 → 검증 반영 루프가 돌면 회귀 리스크가 현저히 줄어요."*
- **그래서 무엇을 하나요? / So what gets done?** — *"Claude Code + Codex 플러그인 환경에서만 동작 — `/codex:rescue`를 현재 브랜치 diff에 돌리고, 나온 findings를 refactor-verify의 리뷰 기반 수정 모드로 넘겨 검증·적용합니다. 다른 호스트면 한 줄 안내 후 exit."*

### Severity translation

- CRITICAL → *"지금 당장 — Codex가 치명적 회귀를 잡음"*
- HIGH → *"이번 주 안에 — 중간 위험 이슈"*
- MEDIUM → *"다음 릴리즈 전까지 — 개선 제안"*
- false-positive → *"체크해 봤는데 문제 아니었음"*

### Box format

Wrap each finding in the box format from the shared reference. Header uses urgency phrase and the finding number. Footer names the hand-off skill.

### What does NOT change

Findings, counts, file:line references, evidence, and severity are identical to balanced/harsh output. Only the wrapping and dimension annotations are added.

## Hand-offs

- **Every fix** → `refactor-verify` (review-driven fix mode). This is the only hand-off; everything substantial delegates here.
- **If the operator wants review-driven fix from a non-Codex source** (pasted notes, PR review, Sentry alert, `gitleaks` output, Semgrep report, GitHub Advanced Security, any scanner) → redirect to `refactor-verify` directly. This wrapper is Codex-only by design; other input sources either get their own thin wrapper following the same pattern or go straight to `refactor-verify` with pasted input.

## Why this wrapper exists

Pack philosophy: **portable engine, optional host-specific wrappers.** The review-driven fix engine is portable and lives in `refactor-verify`. This wrapper exists because one specific maintainer runs the Codex loop often enough that the copy-paste step was adding friction session after session. Future host-specific wrappers (Sentry, gitleaks, etc.) would follow the same pattern — a thin adapter for the input source, delegating to `refactor-verify` for everything substantial.

Before adding another such wrapper, ask two questions: *"Is this workflow frequent enough for one operator to justify a worker slot?"* and *"Is the input source's invocation glue non-trivial enough that operators can't just paste it into `refactor-verify` directly?"* If both answers are yes, build the wrapper following this skill's shape: host check first, templated invocation, hand off to `refactor-verify`, no duplicated logic. If either answer is no, skip the wrapper.

This pattern is documented as rule 9 of `docs/PHILOSOPHY.md`: *"Portable engines can have host-specific wrappers."*
