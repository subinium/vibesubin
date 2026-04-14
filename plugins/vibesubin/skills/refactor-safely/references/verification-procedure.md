# Verification procedure — detail

Every claim in this reference matches the order and numbering of the six steps in `SKILL.md`. Use this doc as the detail-level expansion: when a step feels mechanical in the main file, the expanded rationale and concrete commands live here.

---

## Step 1 — Snapshot + isolation

**Goal:** produce an immutable checkpoint you can roll back to, and a working directory that is not the operator's main checkout.

**Isolation modes, in priority order:**

| Mode | When to use | Rollback |
|---|---|---|
| `git worktree` | Default. Operator has a recent enough git (≥ 2.5, so any modern machine). | `git worktree remove <path>` |
| temporary branch on main checkout | No worktree, or the operator wants to see the changes live in their main editor. | `git switch main && git branch -D <branch>` |
| `git stash create` + `git stash store` | Last resort. Working tree already dirty, no appetite for a branch. | `git stash apply <ref>` |

**Why not just edit on main?** Because the rollback path becomes ambiguous. If something goes wrong halfway, you need to reconstruct "what was there before" from git history, and every uncommitted file is a degree of freedom you don't want.

**Baseline capture — what to save and where:**

```bash
SNAP=$(git rev-parse HEAD)
mkdir -p /tmp/vibesubin-$$
scripts/smoke-test.sh > /tmp/vibesubin-$$/baseline.txt 2>&1 || BASELINE_RED=1
scripts/symbol-diff.sh "$SNAP" "$SNAP" > /tmp/vibesubin-$$/symbols.txt || true
```

The `BASELINE_RED` flag matters. **If the baseline is red, stop.** Refactoring on top of existing failures means every subsequent failure is ambiguous — you can't tell whether you caused it or inherited it. The operator must either:

1. Fix the existing failures first (which is itself a refactor, run a separate session)
2. Explicitly acknowledge the red baseline and accept that the verification will be weaker
3. Narrow the refactor scope to files that don't touch the red area

Never skip past a red baseline silently.

---

## Step 2 — Plan as a Mikado DAG

**Goal:** sequence the refactor so no step depends on a later step, and each step is independently verifiable.

**What a node looks like:**

```
Node: split BigModule into BigCore + BigHelpers
  files:
    - src/big_module.py
    - src/big_core.py       (new)
    - src/big_helpers.py    (new)
  verification:
    - python -c "from src import big_core, big_helpers"
    - pytest tests/test_big_module.py
  preserves:
    - BigModule.export_a, BigModule.export_b, BigModule._internal_c
```

**How to build the tree:**

1. Start with the *goal* as the root. "Move class X to module Y."
2. Ask: "What must already be true before I can do this?" Those are the root's children.
3. Repeat on each child until you hit actions that have no prerequisites. Those are the leaves.
4. Execute leaves first. Walk up to parents only when all children are green.

**When to prune:** if a leaf turns out to be unnecessary (the parent was doable without it), delete it. Don't keep it just because you drew it.

**When to abort:** if the tree grows to more than about 10 nodes, the refactor is probably too big for one session. Pick a subtree, finish it, commit, and treat the rest as a follow-up session.

---

## Step 3 — Execute structural-first (Tidy First)

**Goal:** every commit is either *pure structure* (move, rename, extract, inline) **or** *pure behavior* (logic change). Never both.

**Why:**

- Structural commits can be verified with cheap AST/byte-level checks — no tests needed if the AST matches
- Behavioral commits need full test runs
- Mixing them means you can't tell whether a test failure comes from structure or behavior

**Commit order inside a Mikado leaf:**

1. Structural move (copy the body, update imports on the sender side)
2. Verify: `scripts/symbol-diff.sh $SNAP HEAD` and `scripts/smoke-test.sh`
3. Commit: `refactor: move X from A to B`
4. (Optional) Behavioral cleanup — rename variables for clarity, fold in a bug fix, etc.
5. Verify: full `scripts/smoke-test.sh`
6. Commit: `refactor: clean up X after move` or `fix: ...`

Never collapse these into one commit.

---

## Step 4 — Per-node AST (or byte) diff

**Goal:** prove the moved body is identical to the original, whitespace and comment changes aside.

**Tool priority:**

1. **AST diff via `ast-grep` or `tree-sitter`** — if either is installed and the language is supported
2. **Normalized text diff via `git show` + `diff`** — fallback when the tooling isn't available

**Normalized text diff (language-agnostic fallback):**

```bash
# Extract the function body from the old ref
git show "$SNAP":old_path.py | python3 -c "
import sys, re
text = sys.stdin.read()
# naive extractor: from 'def foo' to the next def at the same indent
# replace with a real extractor for your language
" > /tmp/old-body.txt

# Extract from the new location (same logic)
cat new_path.py | python3 -c "..." > /tmp/new-body.txt

# Normalize: strip leading/trailing whitespace per line, collapse blank lines
normalize() { sed 's/^[[:space:]]*//;s/[[:space:]]*$//' "$1" | sed '/^$/N;/^\n$/d'; }
diff <(normalize /tmp/old-body.txt) <(normalize /tmp/new-body.txt)
```

A zero-byte diff is the success condition. Any diff means you mutated the body, which is a behavioral change hiding in a structural commit — go back to Step 3 and split the commits.

---

## Step 5 — Behavioral verification chain

**Goal:** prove the code still runs and tests still pass.

**Order (cheap to expensive, fail fast):**

```
1. Syntax / parse check        (≤ 1 s)
2. Typecheck                   (seconds)
3. Lint                        (seconds)
4. Import smoke test           (≤ 5 s)
5. Unit tests                  (seconds to minutes)
6. Integration tests           (minutes)
7. Local run / dev server      (seconds to start, one endpoint hit)
```

Run them in order. Stop on the first failure — continuing past a typecheck failure to run tests just burns time.

The `scripts/smoke-test.sh` helper auto-detects the language and runs the canonical chain for it. Use it whenever possible instead of hand-rolling.

---

## Step 6 — Call-site closure

**Goal:** every reference to the moved symbol has been updated. The number of references before and after must match.

**Canonical check:**

```bash
scripts/callsite-count.sh "$SNAP" HEAD old_symbol_name
```

The script counts word-boundary matches in both refs and reports the delta. A drop means you missed sites; zero delta (or positive delta for intentional additions) is the success condition.

**LSP-based find-references is strictly better** than grep when the language has a working language server — it handles scoping, imports, and shadowing. If `pylsp` / `typescript-language-server` / `gopls` / `rust-analyzer` is available, prefer it. The grep fallback is there because not every project has LSP set up.

**Cross-file renames are the highest-risk case.** A method rename inside a class is easy; a global function rename across 80 files is where LLM refactors fall apart. Always run call-site closure on cross-file renames, even if the AST diff passed.

---

## Putting it all together — the end-of-refactor checklist

```
[ ] SNAP recorded
[ ] Isolated in worktree or branch
[ ] Baseline was green (or red was explicitly acknowledged)
[ ] Mikado tree written and approved
[ ] All leaves executed in order
[ ] Every commit is either structural OR behavioral, never mixed
[ ] symbol-diff.sh "$SNAP" HEAD returns 0
[ ] smoke-test.sh returns 0
[ ] callsite-count.sh returns 0 for every renamed/moved symbol
[ ] Rollback plan is still runnable ($SNAP still reachable)
```

If every box is checked, report done with the evidence in the template from `SKILL.md`. If any box is unchecked, the refactor is not done yet.
