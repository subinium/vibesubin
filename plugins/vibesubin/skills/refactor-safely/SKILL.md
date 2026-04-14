---
name: refactor-safely
description: Plans any refactor (move, rename, split, merge, extract, inline) as a Mikado-style dependency tree and executes it from the leaves up. After each step, proves 1:1 semantic equivalence through four independent checks — exported symbol-set diff, per-node AST diff, full behavioral test suite, and call-site closure via find-references. Runs before claiming any refactor is done. Works for any language with a test runner and a way to grep for symbols.
when_to_use: Trigger on "refactor this", "move this function", "split this file", "extract this class", "rename X to Y", "is this still working after my change", "clean this up but don't break anything", or any request that restructures code without intentional behavior change.
allowed-tools: Read Edit Grep Glob Bash(git diff *) Bash(git status *) Bash(git log *) Bash(npm *) Bash(pnpm *) Bash(yarn *) Bash(pytest *) Bash(cargo *) Bash(go test *) Bash(tsc *) Bash(ruff *) Bash(eslint *) Bash(mypy *) Bash(python *)
---

# refactor-safely

The operator asked for a refactor. Your job is to prove the refactor preserved behavior, not just produce a diff that looks right.

Refactoring is the single biggest source of silent regressions when an LLM touches code. The classic failure is: the AI moves a function, updates the definition, and misses one of several call sites. The tests still pass because coverage was never complete. No one notices until a user hits the broken path.

This skill exists to stop that from happening.

## The invariant

A refactor is **not done** until all four of these pass:

1. **Symbol-set diff** — every public/exported name that existed before the refactor still exists after it (or was deliberately removed). No silent drops.
2. **AST body diff** — every moved function/class body is structurally equivalent to its original, normalizing whitespace and comments.
3. **Behavioral verification** — typecheck, lint, smoke test (can the code even load?), test suite. All green.
4. **Call-site closure** — every reference to the moved symbol has been updated. The count of references before and after must match.

If any of the four fails, fix it and re-run all four. Do not partially claim success.

## Procedure — 6 steps, run in order

Each step produces an artifact or an assertion. Never skip.

### Step 1 — Snapshot and isolate before touching anything

Record the starting state. You will diff against this at the end, and you will need it to roll back cleanly if something goes wrong.

**Isolation — pick one, in this priority order:**

1. **Preferred: `git worktree`.** Create a separate working directory for the refactor. Nothing in the operator's main checkout is touched while you work. Rollback = `git worktree remove`.

   ```bash
   SNAP=$(git rev-parse HEAD)
   git worktree add ../refactor-<topic> "$SNAP"
   cd ../refactor-<topic>
   git switch -c refactor/<topic>
   ```

2. **Acceptable: temporary work branch on the main checkout.** Only if worktree isn't available.

   ```bash
   SNAP=$(git rev-parse HEAD)
   git switch -c refactor/<topic>
   ```

3. **Last resort: `git stash`.** Only if the working tree is already dirty and the operator does not want a new branch. Record the stash ref so you can restore later:

   ```bash
   STASH_REF=$(git stash create -m "refactor-safely pre-snapshot")
   git stash store -m "refactor-safely pre-snapshot" "$STASH_REF"
   ```

   If you ever need to recover: `git stash apply "$STASH_REF"`.

**Never work directly on the operator's main branch.** Even a three-line refactor gets a branch.

**Capture the baseline — language-agnostic:**

- `SNAP=$(git rev-parse HEAD)` — the commit you'll diff against and roll back to
- Exported symbol set per file (helper: `scripts/symbol-diff.sh`)
- Full test run result (pass/fail, counts) — save to `/tmp/refactor-baseline-tests.txt`
- Build/typecheck result — save to `/tmp/refactor-baseline-build.txt`
- Lint result — save to `/tmp/refactor-baseline-lint.txt`

**Bootstrap the isolated workspace before behavioral checks.** Fresh worktrees often do **not** contain project-local state like `.venv/`, `node_modules/`, `vendor/`, generated clients, or compiled assets. A "module not found" failure in a brand-new worktree is an environment problem until proven otherwise.

**If the baseline is already red, stop.** You cannot refactor on top of broken code — every failure afterwards becomes ambiguous (did I cause it or was it already broken?). Ask the operator whether to fix the existing failures first. Do not proceed.

**Rollback plan (write it down before starting):**

```bash
# If anything goes wrong, this restores the operator's world exactly:
git switch main                           # leave the refactor branch
git worktree remove ../refactor-<topic>   # if you used a worktree
# or: git branch -D refactor/<topic>      # if you used a branch
git reset --hard "$SNAP"                  # only if you somehow touched main
```

Keep `$SNAP` visible throughout the session. It is the single most important value.

### Step 2 — Plan as a Mikado dependency tree

Do not start editing. Write the refactor down as a tree where each node is a small change, and its children are the prerequisite changes that must happen first. Execute leaves before parents.

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

Each node in the tree has three fields:

- **Files touched** (concrete paths — never `src/*`)
- **Verification command** (how you'll prove this node succeeded)
- **Invariant preserved** (what must still be true after this node commits)

Write the tree as a comment or a scratch file. Show it to the operator before proceeding if the refactor touches more than 3 files. Let them approve or adjust.

Detailed pattern: see the "Step 2 — Plan as a Mikado DAG" section of `references/verification-procedure.md`.

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

This is the step that catches the #1 LLM refactor failure mode: a rename that updated the definition but missed half the callers.

**Before the refactor** (from step 1 snapshot), count every reference to each moved/renamed symbol:

```bash
# LSP preferred (if available)
# find-references via language server → accurate count

# fallback: grep (coarse but works for every language)
git grep -n 'old_symbol_name' | wc -l   # from the snapshot state
```

**After the refactor**, count references to the **new** name — plus any remaining references to the old name that shouldn't exist:

```bash
git grep -n 'new_symbol_name' | wc -l   # should equal the old count
git grep -n 'old_symbol_name' | wc -l   # should equal 0 (or the number of deliberately-kept aliases)
```

If the counts don't match, you missed a callsite. Go find it. Do not report done.

For a rename, treat this as two assertions, not one:

1. old-name count **before** == new-name count **after**
2. old-name count **after** == `0`

The helper supports this directly:

```bash
scripts/callsite-count.sh "$SNAP" HEAD old_name new_name
```

For cross-file symbols, use the language's find-references feature if possible — `gopls`, `rust-analyzer`, `pyright`, `typescript-language-server`, etc. Grep is the universal fallback.

## When to stop and report

Report refactor complete **only when**:

- All six steps passed for every node in the plan
- The behavioral verification is green on the post-refactor commit
- The symbol-set diff, AST diff, smoke tests, and call-site closure all pass
- You can produce the verification commands the operator can re-run

Report template (use in the PR description or session output):

```
## refactor-safely verification

Plan: <1-line summary of the Mikado tree>

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
- **Silent field omission** — When copying a dict, class, or config block, one key disappears. Guard: symbol-set diff (step 1 vs post-refactor) and AST body diff (step 4).
- **Scope promotion** — A local variable accidentally became a module-level variable during extraction. Guard: step 4 normalized diff.
- **Partial edits** — Three of four callers were updated. Guard: step 6 count-match.
- **Comment/docstring drift** — The refactor updated the code but not the docstring describing the old shape. Guard: treat comments inside moved symbols as part of the AST diff.

Full catalog with examples and detection notes: `references/llm-failure-modes.md`.

## Information preservation during doc rewrites

If the refactor includes a README or architecture doc rewrite, apply the same discipline:

1. **Before**: extract the full list of concrete facts from the old doc (file paths, function names, environment variables, URLs, numbers, personal names, proper nouns).
2. **After rewrite**: grep each of those terms in the new doc. Any term that was in the old doc and is missing from the new doc is either a deliberate simplification (document the decision) or a silent loss (fix).
3. If the new doc changed section headers, keep a "moved from" note at least briefly so search still works.

See "Information preservation during doc rewrites" and the general preservation pattern in `references/verification-procedure.md`.

## When not to use this skill

- Typo fix in a single comment → just edit it
- Adding a new feature (non-refactor) → this skill is for changes that preserve behavior, not for new behavior
- Deleting code that the operator knows is dead → use `fight-repo-rot` to confirm it's dead first, then delete
- A rename that the operator says is trivial and is confined to one file → still run step 5 and 6, but step 2's Mikado tree is overkill

## What to do if the baseline is red

You cannot refactor on top of broken tests. If step 1 discovers failing tests or typecheck errors:

1. Tell the operator which tests/checks are failing
2. Ask whether they are known failures (to be excluded from the baseline) or unknown failures (to be fixed first)
3. If unknown, offer to investigate the failures before the refactor
4. Do not proceed into step 2 with a red baseline

A refactor on top of red is indistinguishable from a refactor that caused red. You lose the ability to prove causation.

## Integration with other vibesubin skills

- Before a large refactor, run `fight-repo-rot` to confirm you're aiming at a real hotspot
- After a refactor, hand off the commit/PR writing to `write-for-ai` — it knows how to document verification results
- If the refactor touches configuration, coordinate with `manage-config-env` on where the new config values should live
- If the refactor touches security-sensitive paths (auth, crypto, input handling), run `audit-security` on the result

## Language-agnostic core, language-specific tooling

The 6-step procedure above is language-agnostic. The specific commands for each language (how to typecheck, how to run tests, how to find references) live in references:

- `references/language-smoke-tests.md` — per-language command chains
- `references/verification-procedure.md` — deep-dive into each of the six steps, including Mikado planning, AST diffing, and information preservation for doc rewrites
- `references/llm-failure-modes.md` — the catalog of mistakes to guard against, with the specific step that catches each one

Scripts (invoked, not read):

- `scripts/symbol-diff.sh` — print symbol-set diff between two git refs
- `scripts/smoke-test.sh` — auto-detect language, prefer project-local toolchains when present, and warn when an isolated worktree is not bootstrapped enough to trust failures
- `scripts/callsite-count.sh` — count references before/after, with explicit rename support and stale old-name detection
