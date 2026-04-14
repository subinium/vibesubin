# LLM refactor failure modes

A taxonomy of the ways AI assistants fail when asked to refactor, and the specific guard in the 6-step procedure that catches each one. Use this as a mental checklist during step 4 and step 6.

## 1. Missed call sites (the #1 failure)

**What it looks like.** The AI renames or moves a symbol. The definition is updated correctly. One or several *references* are not. Tests pass because the uncovered references are dynamic, optional, or in untested code paths. Production crashes when a user hits the missed path.

**Why it happens.** The AI completes the obvious edit, checks the file it's currently focused on, and doesn't run a repo-wide find-references. The test run "passes" because coverage is incomplete.

**Guard:** Step 6 — `scripts/callsite-count.sh "$SNAP" HEAD <symbol>`. Reference counts from the old ref and the new ref must match. If they drop, you missed call sites.

**Defense in depth:** use LSP find-references when available, fall back to `git grep -w <symbol>`.

---

## 2. Hallucinated imports

**What it looks like.** The AI adds `from foo.bar import baz` or `import { baz } from 'foo/bar'`. The module `foo.bar` exists but does not export `baz`. Or worse: the module doesn't exist at all. The AI was confident because it "remembered" that pattern from training data.

**Why it happens.** Base rate is high — studies show ~20% of LLM-suggested package references are fabricated. The AI pattern-matches "modules that sound like they should exist" against "modules that do exist" and sometimes gets it wrong.

**Guard:** Step 5 — the import smoke test. `python -c "from foo.bar import baz"` or `node -e "require('foo/bar').baz"`. If the import fails at load time, you catch the hallucination before it reaches a test or a runtime.

---

## 3. Silent field / branch omission

**What it looks like.** The AI copies a dict, class, config block, or enum from one location to another. One key disappears in the copy. Nothing else changes. The test for the missing key is either absent or passes by coincidence.

**Why it happens.** Long structured literals are at the edge of the model's attention span. When the AI produces a new copy, it approximates from memory rather than copying exactly. A key in the middle can vanish without the AI noticing.

**Guard:** Step 1 — symbol-set diff captures exported names, so a class or top-level constant that disappears is caught. Step 4 — per-node AST/byte diff catches keys inside a dict or branches inside a match statement. When the normalized text diff is non-empty, the omission is visible.

**Watch especially for:** dicts with 10+ keys, enum-like constants, match/switch statements with many arms, config files, i18n string tables.

---

## 4. Scope promotion

**What it looks like.** During an extraction, a local variable gets accidentally promoted to module-level, or a private helper becomes public. The semantics are subtly different: the value now persists across calls when it used to be re-initialized each time, or the helper is now part of the public API and callers could start depending on it.

**Why it happens.** The AI pulls a block of code out of a function, adjusts indentation, and doesn't re-check whether every variable was previously local or captured.

**Guard:** Step 4 — normalized AST diff will show the missing `def` / `let` / `const` that turned a local into a module-level binding. Step 6 — symbol-set diff may show a new "public" name the operator didn't intend.

---

## 5. Partial edits across multiple files

**What it looks like.** The AI updates files A and B but forgets C. Or it updates the first 12 of 15 call sites. The remaining sites use the old API and break at runtime.

**Why it happens.** Long edit sessions tax the AI's attention. Files scrolled off the visible context can be forgotten.

**Guard:** Step 6 — call-site closure. The count-match check catches partial updates because the "new name" count will be lower than the "old name" count was.

**Defense:** always produce the Mikado plan first and execute leaves in a disciplined order. A plan that lists every file in advance is much harder to skip.

---

## 6. Comment / docstring drift

**What it looks like.** The AI refactors the code but leaves the comment or docstring describing the old behavior. Future readers (human or AI) are misled about what the function does.

**Why it happens.** Comments live in a different "layer" of the file from the code, and the AI's edit focused on code. The comment was not in the attention window.

**Guard:** Step 4 — treat comments inside moved symbols as part of the AST diff. The diff should not be "blank except for the comment"; if it is, the comment was left stale.

**Defense:** when reviewing any refactor, re-read the docstring of every touched function. If it mentions a parameter, return value, or exception that no longer applies, fix the comment in the same commit.

---

## 7. Lost error-handling paths

**What it looks like.** The original function had a `try / except` or `if / else` branch that handled a specific error case. The refactored version is "cleaner" because that branch is gone. The error path is silently unhandled.

**Why it happens.** LLMs are trained to produce clean-looking code. "Clean" and "robust" are often in tension. The AI optimizes for readability and discards what looks like boilerplate.

**Guard:** Step 4 — AST diff shows the missing branch. Step 5 — tests for the error case fail (if you have them).

**Defense:** if the baseline tests do not cover every error branch, add a test for the specific branch before the refactor. Then the diff check will be real instead of theoretical.

---

## 8. Circular or self-referential imports introduced

**What it looks like.** The refactor splits module A into A1 and A2. A1 imports from A2, A2 imports from A1, and everything dies on first load. Typically manifests as `ImportError: cannot import name '...'` or `circular dependency`.

**Why it happens.** The AI didn't build the full import graph before splitting.

**Guard:** Step 5 — the import smoke test catches circular imports at load time, before any test runs.

**Defense:** in the Mikado plan, write down every import the new modules will have, and check that the import graph is a DAG before executing.

---

## 9. Dead code left behind

**What it looks like.** The AI moves a function but forgets to remove the original. Now there are two implementations — the callers are updated to use the new one, but the old one sits there as dead code, accumulating.

**Why it happens.** The AI's edit was additive; the cleanup step was forgotten.

**Guard:** Step 1 — symbol-set diff. If the "after" set has both `old.foo` and `new.foo`, something is wrong.

**Defense:** in the Mikado plan, make "delete old" an explicit node. Don't leave it as implicit cleanup.

---

## 10. Git history confusion

**What it looks like.** The refactor rewrites history (rebase, amend, force-push) and the operator's local checkout is now out of sync with remote. Recovery requires git rescue operations the operator doesn't know how to perform.

**Why it happens.** The AI reaches for `git rebase -i` or `git commit --amend` because those look cleaner than "more commits." Non-developer operators have no mental model for history rewriting.

**Guard:** **Never rewrite history during a refactor.** New commits only. If cleanup is needed, a separate "squash the last N commits" session can happen after the refactor is verified — but only with the operator's explicit go-ahead.

---

## How to use this list

- Before starting a refactor, skim this file as a warm-up
- During step 4 and step 6, re-check the failure modes that apply to the specific edit
- When a refactor passes all verification but feels wrong, look for #1, #3, or #6 specifically — those are the ones that can pass the automated checks while still being incorrect
- When reviewing someone else's refactor commit, use this as a review checklist
