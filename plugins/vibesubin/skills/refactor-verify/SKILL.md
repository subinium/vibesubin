---
name: refactor-verify
description: Proves a behavior-preserving code change (refactor, rename, split, merge, extract, inline, or delete of confirmed-dead code) is actually complete. Plans the change as a dependency tree, executes it from the leaves up, and after each step proves 1:1 semantic equivalence through four independent checks — exported symbol-set diff, per-node AST diff, full behavioral test suite, and call-site closure via find-references. Runs before claiming any such change is done. Works for any language with a test runner and a way to grep for symbols.
mutates: [direct]
when_to_use: Trigger on "refactor this", "move this function", "split this file", "extract this class", "rename X to Y", "delete this dead code safely", "is this still working after my change", "clean this up but don't break anything", or any request that restructures or removes code without intentional behavior change.
allowed-tools: Read Edit Grep Glob Bash(git diff *) Bash(git status *) Bash(git log *) Bash(git worktree *) Bash(git switch *) Bash(git stash *) Bash(git rev-parse *) Bash(git show *) Bash(git branch *) Bash(git reset *) Bash(git grep *) Bash(npm *) Bash(pnpm *) Bash(yarn *) Bash(pytest *) Bash(cargo *) Bash(go test *) Bash(tsc *) Bash(ruff *) Bash(eslint *) Bash(mypy *) Bash(python *) Bash(node *)
---

# refactor-verify

The operator asked for a change that's supposed to preserve behavior — a refactor, a rename, a split, an extract, a dead-code deletion. Your job is to *prove* that behavior was preserved, not just produce a diff that looks right.

Behavior-preserving changes are the single biggest source of silent regressions when an LLM touches code. The classic failure is: the AI moves a function, updates the definition, and misses one of several call sites. The tests still pass because coverage was never complete. No one notices until a user hits the broken path.

This skill exists to stop that from happening. It covers two change families:

1. **Structural refactors** — move, rename, split, merge, extract, inline. The behavior is supposed to be identical afterward.
2. **Safe deletions** — removing code the operator has confirmed is dead (usually via `fight-repo-rot`). The behavior is supposed to be identical because the code wasn't running.

Both families use the same four verification checks.

## The invariant

A change is **not done** until all four of these pass:

1. **Symbol-set diff** — every public/exported name that existed before the refactor still exists after it (or was deliberately removed). No silent drops.
2. **AST body diff** — every moved function/class body is structurally equivalent to its original, normalizing whitespace and comments.
3. **Behavioral verification** — typecheck, lint, smoke test (can the code even load?), test suite. All green.
4. **Call-site closure** — every reference to the moved symbol has been updated. The count of references before and after must match.

If any of the four fails, fix it and re-run all four. Do not partially claim success.

## State assumptions — before acting

Before starting the procedure, write an explicit Assumptions block. Don't pick silently between interpretations; surface the choice. If any assumption is wrong or ambiguous, pause and ask — do not proceed on a guess.

Required block:

```
Assumptions:
- Change type:       <move | rename | split | merge | extract | inline | delete>
- Scope files:       <list of files in scope — everything else untouched>
- Baseline status:   <green (tests + typecheck + lint pass) | red (report blocks before touching anything)>
- Delete confidence: <N/A | HIGH (auto-ok) | MEDIUM (operator confirms) | LOW (require explicit approval)>
```

Typical items for this skill:

- The change type named (move / rename / split / merge / extract / inline / delete)
- The files or symbols in scope, and the ones deliberately untouched
- Whether the pre-change baseline is green (tests + typecheck + lint) — if unknown, Step 1 snapshot is still required before proceeding

Stop-and-ask triggers:

- A move request without a target file specified
- A vague "clean this up" without a concrete change type — refuse to proceed until the operator names one of the seven change types
- A delete request on a symbol `fight-repo-rot` flagged LOW confidence — never auto-proceed, require operator confirmation

Silent picks are the most common failure mode: the skill runs, produces plausible output, and the operator doesn't notice the wrong interpretation was chosen. The Assumptions block is cheap insurance.

## Procedure — 6 steps, run in order

Each step produces an artifact or an assertion. Never skip.

### Step 1 — Snapshot and isolate before touching anything

Record the starting state. You will diff against this at the end, and you will need it to roll back cleanly if something goes wrong.

**Isolation — pick one of two options:**

1. **Preferred: `git worktree`.** Create a separate working directory for the change. Nothing in the operator's main checkout is touched while you work. Rollback = `git worktree remove`.

   ```bash
   SNAP=$(git rev-parse HEAD)
   git worktree add ../verify-<topic> "$SNAP"
   cd ../verify-<topic>
   git switch -c verify/<topic>
   ```

2. **Acceptable: temporary work branch on the main checkout.** Only if worktree isn't available (e.g., the operator's filesystem doesn't support multiple worktrees, or the repo has submodules that don't co-exist).

   ```bash
   SNAP=$(git rev-parse HEAD)
   git switch -c verify/<topic>
   ```

**Do not use `git stash` as an isolation mechanism.** Stashes are interruption-unsafe — a crash, a power loss, or another `git stash` from a second session can lose the stash ref, and recovery is manual. A branch is cheap, always recoverable, and always preferable. This rule is non-negotiable.

**Never work directly on the operator's main branch.** Even a three-line change gets a branch.

**Capture the baseline — language-agnostic:**

- `SNAP=$(git rev-parse HEAD)` — the commit you'll diff against and roll back to
- Exported symbol set per file (helper: `scripts/symbol-diff.sh`)
- Full test run result (pass/fail, counts) — save to `/tmp/verify-baseline-tests.txt`
- Build/typecheck result — save to `/tmp/verify-baseline-build.txt`
- Lint result — save to `/tmp/verify-baseline-lint.txt`

**Bootstrap the isolated workspace before behavioral checks.** Fresh worktrees often do **not** contain project-local state like `.venv/`, `node_modules/`, `vendor/`, generated clients, or compiled assets. A "module not found" failure in a brand-new worktree is an environment problem until proven otherwise.

**If the baseline is already red, stop.** You cannot verify a change on top of broken code — every failure afterwards becomes ambiguous (did I cause it or was it already broken?). Ask the operator whether to fix the existing failures first. Do not proceed.

**Rollback plan (write it down before starting):**

```bash
# If anything goes wrong, this restores the operator's world exactly:
git switch main                           # leave the verify branch
git worktree remove ../verify-<topic>     # if you used a worktree
# or: git branch -D verify/<topic>        # if you used a branch
git reset --hard "$SNAP"                  # only if you somehow touched main
```

Keep `$SNAP` visible throughout the session. It is the single most important value.

### Step 2 — Plan as a dependency tree

Do not start editing. Write the change down as a tree where each node is a small step, and its children are the prerequisite steps that must happen first. Execute leaves before parents. The principle is old — Mikado Method is one well-known formalization — but the shape is what matters: **commit the dependency graph to a scratch file before touching any code**, so when something fails you can tell whether the plan was wrong or the execution was wrong.

Example tree for "split `big_module` into `big_module_core` and `big_module_helpers`":

```
Split big_module
├── Create big_module_helpers.* with helper functions
│   └── Identify which functions are pure helpers (no cross-refs into big_module)
├── Create big_module_core.* with the rest
│   └── Update imports inside the moved bodies
├── Replace `import big_module` with `import big_module_core` (plus helpers) everywhere
│   └── Inventory all current import sites
└── Delete the original big_module
    └── Confirm no remaining references
```

Example tree for "delete confirmed-dead `legacy_reports` module":

```
Delete legacy_reports
├── Verify zero external references (grep + LSP find-references)
├── Delete legacy_reports/ directory
├── Remove any import of legacy_reports from __init__.py / index.ts
└── Confirm symbol-set diff shows only the expected removals
```

Each node in the tree has three fields:

- **Files touched** (concrete paths — never `src/*`)
- **Verification command** (how you'll prove this node succeeded)
- **Invariant preserved** (what must still be true after this node commits)

Write the tree as a scratch file (e.g., `.verify-plan.md`, gitignored). Show it to the operator before proceeding if the change touches more than 3 files. Let them approve or adjust.

Detailed pattern, including when to linearize vs branch the tree and how to handle cross-cutting constraints: `references/verification-procedure.md`.

### Step 3 — Execute from the leaves up — structural commits only

Follow **Tidy First**: a commit is either *structural* (move, rename, extract, inline) or *behavioral* (logic change). Never mixed. This makes every commit independently verifiable.

For each leaf:

1. Make the change on disk
2. Run the leaf's verification command
3. If it passes, commit with a clear message (see `write-for-ai` skill for the format)
4. Move up the tree

If a leaf fails, do **not** move up. Fix the leaf or revise the tree. A failed leaf that you skip becomes a load-bearing bug later.

### Step 4 — Per-node AST diff (structural preservation)

For every function, class, or constant that got moved in this step, prove its body survived intact.

Extract the symbol from the **old location** (using the snapshot from step 1 — or `git show HEAD~1:old_path`). Extract it from the **new location**. Normalize both (strip whitespace, strip comments, strip trailing commas). Compare.

If the language has AST tooling:

- `ast-grep --lang <lang> --pattern '<pattern>' <path>` — find the symbol
- `tree-sitter parse <path>` — get the AST

If it doesn't, fall back to a normalized text diff:

```bash
# pseudocode
old_body=$(extract_symbol_from_git_show HEAD~1:old_path symbol_name | normalize)
new_body=$(extract_symbol_from_file new_path symbol_name | normalize)
diff <(echo "$old_body") <(echo "$new_body")
```

The goal is a **zero-byte diff** on the normalized form. If there's a diff, you didn't just move the symbol — you also mutated it. That's a behavioral change hiding in a structural commit, which violates Tidy First.

Detail: see the "Step 4 — Per-node AST (or byte) diff" section of `references/verification-procedure.md`.

### Step 5 — Behavioral verification (can it still run)

Run the full smoke-test chain for the language. Never skip because "it's just a rename."

Order matters — fail fast on the cheapest check first:

1. **Syntax/parse** (`python -c 'import x'`, `node -e "require('./')"`, `cargo check`, `go build ./...`)
2. **Typecheck** (`mypy`, `tsc --noEmit`, `cargo check`, `go vet`)
3. **Lint** (`ruff`, `eslint`, `clippy`, `golangci-lint`)
4. **Import smoke test** — attempt to load every module touched, not just the obvious ones
5. **Unit tests** (`pytest`, `jest`, `cargo test`, `go test ./...`)
6. **Integration tests** (if any)
7. **Local run / dev server** (if the project has one, hit one known endpoint and assert 200)

If any step fails, return to step 4 — something you thought was structural is actually behavioral.

Per-language details: `references/language-smoke-tests.md`

### Step 6 — Call-site closure

This is the step that catches the #1 LLM failure mode in refactors and deletions: a rename that updated the definition but missed half the callers, or a "dead code" deletion where one caller turns out to be live.

**Before the change** (from step 1 snapshot), count every reference to each affected symbol. Prefer an LSP find-references query — `gopls`, `rust-analyzer`, `pyright`, `typescript-language-server` — because grep is a lower bound, not a ground truth.

```bash
# LSP preferred (accurate for cross-file symbols, handles dynamic dispatch)
# — run your editor's find-references or the CLI equivalent

# grep fallback — works for every language but is a lower bound
git grep -n 'old_symbol_name' | wc -l   # from the snapshot state
```

**After the change**, count references to the **new** name — plus any remaining references to the old name that shouldn't exist:

```bash
git grep -n 'new_symbol_name' | wc -l   # should equal the old count (renames) or zero (deletions of confirmed-dead code)
git grep -n 'old_symbol_name' | wc -l   # should equal 0 (or the number of deliberately-kept aliases)
```

If the counts don't match, you missed a callsite or your "dead" symbol wasn't actually dead. Go find the reference. Do not report done.

Treat renames and deletions as two-assertion checks, not one:

| Operation | Assertion 1 | Assertion 2 |
|---|---|---|
| **Rename** | old-count **before** == new-count **after** | old-count **after** == `0` |
| **Delete (dead code)** | old-count **before** == `0` (confirmed before deleting) | old-count **after** == `0` |
| **Move** | old-path-count **after** == `0` | new-path-count **after** == old-path-count **before** |

The helper supports this directly:

```bash
scripts/callsite-count.sh "$SNAP" HEAD old_name new_name
```

**Grep is a lower bound.** A match count of zero in grep does not prove the symbol is unreferenced — dynamic dispatch, reflection, string-built symbol names, and cross-language boundaries all evade grep. When deleting code based on a grep-zero result, label the confidence as MEDIUM and require a second signal (LSP find-references, import graph analysis, or an explicit operator confirmation).

## When to stop and report

Report the change complete **only when**:

- All six steps passed for every node in the plan
- The behavioral verification is green on the post-change commit
- The symbol-set diff, AST diff, smoke tests, and call-site closure all pass
- You can produce the verification commands the operator can re-run

Report template (use in the PR description or session output):

```
## refactor-verify report

Change type: <refactor | rename | split | move | extract | inline | delete-dead>
Plan: <1-line summary of the dependency tree>

### Symbol-set diff
- Before: <N> exported symbols across <M> files
- After:  <N> exported symbols across <M'> files
- Diff:   <explicit delta, or "none">

### AST body preservation
- <N> moved symbols, all normalized-equivalent to source

### Behavioral
- Typecheck: ✅
- Lint:      ✅
- Tests:     ✅ (X/Y passing, unchanged from baseline)
- Smoke:     ✅ (imports + local run)

### Call-site closure
- Old references: <N> (from snapshot)
- New references: <N> (equal, verified)
- Orphans:        0

Verification commands (re-run anytime):
  <concrete command 1>
  <concrete command 2>
```

## LLM failure modes to guard against

Documented failure patterns. If any of these trip during execution, the verification system should catch them — but it's faster to avoid them upfront.

- **Missed call sites** — The #1 issue. Guard: step 6.
- **Hallucinated imports** — You added `from foo.bar import baz` but `foo.bar` doesn't have `baz`. Guard: step 5's import smoke test.
- **Silent field omission** — When copying a dict, class, or config block, one key disappears. Guard: symbol-set diff (step 1 vs post-change) and AST body diff (step 4).
- **Scope promotion** — A local variable accidentally became a module-level variable during extraction. Guard: step 4 normalized diff.
- **Partial edits** — Three of four callers were updated. Guard: step 6 count-match.
- **Comment/docstring drift** — The change updated the code but not the docstring describing the old shape. Guard: treat comments inside moved symbols as part of the AST diff.
- **False-dead deletion** — A "dead" symbol was actually reachable via dynamic dispatch / reflection / a string-built name. Guard: step 6 LSP-first references with explicit HIGH/MEDIUM/LOW confidence before deletion.

Full catalog with examples and detection notes: `references/llm-failure-modes.md`.

## Information preservation during doc rewrites

If the change includes a README or architecture doc rewrite, apply the same discipline:

1. **Before**: extract the full list of concrete facts from the old doc (file paths, function names, environment variables, URLs, numbers, personal names, proper nouns).
2. **After rewrite**: grep each of those terms in the new doc. Any term that was in the old doc and is missing from the new doc is either a deliberate simplification (document the decision) or a silent loss (fix).
3. If the new doc changed section headers, keep a "moved from" note at least briefly so search still works.

See "Information preservation during doc rewrites" and the general preservation pattern in `references/verification-procedure.md`.

## When not to use this skill

- Typo fix in a single comment → just edit it
- Adding a new feature (non-refactor) → this skill is for changes that preserve behavior, not for new behavior
- Deleting code without a dead-code confirmation → run `fight-repo-rot` first to confirm the target is dead with explicit confidence, then come back here for the delete + verify
- A single-file rename the operator says is trivial → still run step 5 and 6; step 2's tree is overkill but the verification isn't

## What to do if the baseline is red

You cannot verify a change on top of broken tests. If step 1 discovers failing tests or typecheck errors:

1. Tell the operator which tests/checks are failing
2. Ask whether they are known failures (to be excluded from the baseline) or unknown failures (to be fixed first)
3. If unknown, offer to investigate the failures before the change
4. Do not proceed into step 2 with a red baseline

A change on top of red is indistinguishable from a change that caused red. You lose the ability to prove causation.

## Things not to do

- **Don't add features the operator did not request.** During a move/rename/split, if you notice a bug in an adjacent function, a test that could be tighter, or a comment that's wrong, report it in the final output as a hand-off — do not fix it as part of this change. Every edited line must trace to the named change type; unrelated fixes contaminate the AST-diff verification and invite silent regressions.

## Sweep mode — read-only audit

When invoked from `/vibesubin` (the umbrella skill's parallel sweep), this skill runs in **read-only audit mode**. Do not snapshot, do not plan a dependency tree, do not execute any change, do not run the 6-step procedure.

Instead, produce a findings-only report:

- Current baseline state: do tests pass right now, does typecheck pass, does lint pass, does the project even build? (Capture the baseline status, do not run recovery.)
- Recent refactor risk: any commits in the last 30 days that restructured code without evidence of verification (no test results in PR bodies, no symbol-diff output, etc.).
- Obvious hidden regression risk: exported symbols that appear in the repo but never show a call-site count, files that match the god-file pattern AND have a recent high-churn count, pending renames visible in branch names but not yet merged.
- Stoplight verdict: 🟢 repo is in a green baseline and can accept a refactor / 🟡 baseline has known failures that block verification / 🔴 baseline is red and no refactor can be verified on top of it.
- A one-line "fix with" pointer indicating `/refactor-verify` will plan and execute any specific change when invoked directly.

The operator reviews the sweep report and, if they want a specific refactor applied, invokes `/refactor-verify` directly — which then runs the full 6-step procedure.

How to tell: the task context from the umbrella will include a `sweep=read-only` marker or an explicit "produce findings only, do not edit" instruction. Obey it. If the operator invokes this skill by name, the full procedure applies and editing is expected.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"* / *"厳しめ"*), switch output rules on both the sweep audit and the direct-invocation report:

- **Lead with the baseline verdict.** First line of the report is whether the project is in a green baseline (refactor-safe) or red (cannot verify anything on top). No preamble.
- **Pass/fail verdicts are binary.** Drop *"mostly passing"*, *"almost green"*, *"a couple of flakes"*. A refactor is done or not done. If three of four verification passes succeeded and the fourth didn't, the change is **not done** — say so in one sentence.
- **Direct attribution on every failure.** *"`src/api/user.ts::getUser` is referenced 12 times but only 11 were updated. The one missed call site is `tests/api/user.test.ts:47`."* Not *"some call sites may still reference the old name."*
- **No *"verification is strongly recommended"* hedging.** The pack's entire premise is that verification is mandatory. Harsh mode restates this as a refusal: *"Refusing to report done — the test suite did not run because the worktree was not bootstrapped."* Not *"you may want to run the tests first."*
- **Dead-code deletions are direct.** Balanced mode says *"candidate for removal, confirm the LSP reference count first"*. Harsh mode says *"LSP returns zero references, grep returns zero references — delete it."*
- **Call-site closure mismatches are escalations.** If the old-count and new-count don't match, harsh mode frames it as a bug-in-the-refactor, not a note-for-later. *"The rename is incomplete. Do not merge this PR."*

Harsh mode does not invent failures, skip verification steps, or become rude. Every harsh statement must cite the same symbol count, grep output, or test result the balanced version would cite. The change is framing, not substance.

## Layperson mode — plain-language translation

When the task context contains `explain=layperson` (from `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"explain like I'm non-technical"*, *"非開発者でも分かるように"*, *"用通俗的话解释"*), add a plain-language layer to every finding this skill emits. Combines freely with `tone=harsh`. Full rules at `/plugins/vibesubin/skills/vibesubin/references/layperson-translation.md`.

### Three dimensions per finding (in the operator's language — Korean / English / Japanese / Chinese)

- **왜 이것을 해야 하나요? / Why should you do this?** — *"지금 파일을 옮기거나 함수 이름을 바꾸면 다른 곳에서 그 코드를 부르는 부분이 조용히 망가질 수 있어요. 이 스킬이 그걸 미리 잡아줍니다."*
- **왜 중요한 작업인가요? / Why is it an important task?** — *"AI가 리팩터 끝내고 '완료'라고 해도, 사실은 호출부 한두 개가 옛날 이름을 계속 가리키고 있을 수 있어요. 배포 후 실제 사용자 흐름에서 터집니다."*
- **그래서 무엇을 하나요? / So what gets done?** — *"바꾸기 전 상태를 저장하고, 변경을 의존성 순서대로 적용한 뒤, 심볼·컴파일·동작·호출부 4단계 검증이 전부 통과할 때만 '완료'라고 말합니다."*

### Severity translation

- 🔴 blocker → *"리팩터가 망가진 상태 — 지금 고치지 않으면 배포 즉시 터집니다"*
- 🟡 caution → *"다음 커밋 전에 확인 필요"*
- 🟢 pass → *"4단계 검증 통과 — 안전하게 머지 가능"*

## Review-driven fix mode

A variant where the input is an **external review report** instead of an operator-phrased refactor — `codex-fix`/`/codex:rescue` output, a human PR review, scanner output (`gitleaks`, `pip-audit`, `cargo audit`, Semgrep), a Sentry alert, or pasted notes. The task is to resolve every item against the repo's current state.

**Trigger on:** *"resolve these findings"*, *"fix this review"*, *"리뷰 사항 처리해줘"*, *"이 리뷰 고쳐줘"*, *"レビュー項目を直して"*, *"修复这个 review"*, pasted review reports with file:line, hand-offs from `codex-fix`.

Two things differ from the standard procedure:

1. Input is seeded externally (pasted text, file path, structured report), not from an operator's refactor request.
2. Most review-driven fixes **intentionally change behavior** (security patch, bug fix, missing-mutex addition). The standard symbol-set and AST-diff invariants are relaxed **only for the fixed code** — they still apply with full force to every untouched file.

Everything else — `REVIEW_SHA` snapshot, dependency-tree planning, leaves-up execution, behavioral verification, call-site closure on the untouched surface, commit-with-back-reference (`<type>(<scope>): resolve <review-source>#<item-id> — <subject>`), per-item triage table — is identical to the standard 6-step flow.

Full procedure with stale-snapshot handling, triage rules, and resolution-report template: `references/review-driven-fix.md`.

## Integration with other vibesubin skills

- **Input from `fight-repo-rot`** — dead-code findings (with confidence) come in here as delete-dead jobs. The handoff includes the list of symbols and the confidence level; LOW-confidence deletions require an explicit operator OK.
- **Output to `write-for-ai`** — hand off the commit and PR writing; `write-for-ai` knows how to document verification results.
- **Config-touching changes** — coordinate with `manage-secrets-env` (if the change touches secrets, `.env`, or `.gitignore`) or `project-conventions` (if the change is about branch strategy, directory layout, dep pinning, or path portability) on where new values should live before restructuring.
- **Security-sensitive changes** — auth, crypto, input handling; run `audit-security` on the result.

## Language-agnostic core, language-specific tooling

The 6-step procedure above is language-agnostic. The specific commands for each language (how to typecheck, how to run tests, how to find references) live in references:

- `references/language-smoke-tests.md` — per-language command chains
- `references/verification-procedure.md` — deep-dive into each of the six steps, including dependency-tree planning, AST diffing, and information preservation for doc rewrites
- `references/llm-failure-modes.md` — the catalog of mistakes to guard against, with the specific step that catches each one

Scripts (invoked, not read):

- `scripts/symbol-diff.sh` — print symbol-set diff between two git refs
- `scripts/smoke-test.sh` — auto-detect language, prefer project-local toolchains when present, and warn when an isolated worktree is not bootstrapped enough to trust failures
- `scripts/callsite-count.sh` — count references before/after, with explicit rename support and stale old-name detection
