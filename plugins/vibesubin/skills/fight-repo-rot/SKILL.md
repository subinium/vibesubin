---
name: fight-repo-rot
description: Finds what's rotting in a repo and returns a prioritized diagnosis — dead code first, then god files / hotspots / hardcoded paths / stale TODOs / lopsided import graphs. Dead-code candidates are tagged HIGH / MEDIUM / LOW confidence so the operator can delete with calibrated risk. Pure diagnosis — never edits code, never plans fixes, never runs verification. Hand off to refactor-verify for deletions and restructures, to manage-config-env for config issues, to audit-security for CVE dependency rot. Language-agnostic.
when_to_use: Trigger on "find dead code", "what can I delete", "is any of this unused", "clean up this repo", "what's rotting", "what should I clean up", "where should I refactor next", "too messy", "too many files", "is my repo okay" (health check), before a major new feature (survey first), or before open-sourcing.
allowed-tools: Grep Glob Read Bash(git log *) Bash(git blame *) Bash(git ls-files *) Bash(git grep *) Bash(wc *) Bash(find *)
---

# fight-repo-rot

Repos don't break in a day. They rot over months as dead code accumulates, god files grow, hardcoded paths get committed, and six-month-old `TODO`s turn into forever-`TODO`s. This skill surfaces what's rotting — it never edits code.

**What this skill is:** a diagnosis, sorted by confidence and leverage, with a pointer to the skill that should handle each finding.

**What this skill is not:** an executor. It never deletes, refactors, rewrites, or runs tests. When the operator approves a finding, it hands off to another skill (`refactor-verify` for deletions and restructures, `manage-config-env` for config fixes, `audit-security` for CVE dependency rot). This boundary is load-bearing — the moment this skill starts editing, the evidence chain breaks.

## When to trigger

- "find dead code" / "what can I delete"
- "is any of this unused"
- "clean up this repo" / "what's rotting"
- "what should I clean up"
- "where should I refactor"
- "my repo is a mess"
- "is my repo okay" (ambiguous — run this as a health check)
- before a major new feature (survey the rot first)
- before open-sourcing (don't surprise strangers)

## Primary category: dead code

Dead code is the core finding this skill produces. Non-obvious dead code is the highest-leverage cleanup target: it's the thing the operator can delete with calibrated confidence, reducing surface area without touching live behavior. Everything else in this skill is secondary.

### What counts as dead code

- Functions, methods, or classes that nothing calls
- Exports that no other file imports
- Files that nothing imports
- Whole directories that are orphaned from the dependency graph
- Dependencies in the manifest that are never imported
- Config keys / env vars never read
- Feature flags that have long since been decided and never cleaned up

### How to find it

Language-specific tools first (they're accurate), grep second (a lower bound).

```bash
# Python
pip install vulture && vulture src/
pyflakes src/

# JavaScript / TypeScript
npx ts-prune                    # TS unused exports
npx knip                        # TS/JS unreferenced files + exports + deps
npx unimported                  # unreferenced JS files

# Rust
cargo +nightly udeps            # unused dependencies
cargo clippy -- -W dead_code    # unreachable code

# Go
deadcode ./...                  # unreachable functions
go vet ./...                    # various unused warnings

# Universal fallback — LSP find-references
# (run in the operator's editor, or via the LSP CLI — accurate for cross-file symbols)

# Grep fallback — coarsest, lower bound only
git grep -w 'symbol_name' | wc -l
```

### Confidence levels — always tag every finding

Static dead-code detection produces false positives. Dynamic imports, reflection, test-only usage, CLI entrypoints, and cross-language boundaries can all make a function *look* dead when it isn't. Every dead-code finding gets a confidence level so the operator doesn't delete something load-bearing.

| Confidence | What it means | Safe to delete? |
|---|---|---|
| **HIGH** | No textual reference anywhere in the repo (`git grep -w`, `ts-prune`, `vulture`, `deadcode`, etc.), not in tests, not in docs, not in entrypoints, not in config files, and the symbol is not exported for external use | Yes — hand off to `refactor-verify` for the actual delete + verification |
| **MEDIUM** | No reference in the main source tree, but appears in test files, or the language uses dynamic dispatch (Python, Ruby, JS without strict types), or the symbol name could be built dynamically | Ask the operator before deleting — the test may be load-bearing, or a dynamic caller may exist |
| **LOW** | Symbol is exported from a package, appears in generated code, is referenced via reflection / codegen / dependency injection (Go, Java annotations, .NET DI), or the language's find-references is unreliable | Do not delete without explicit human review and a second signal |

Never emit a dead-code finding without a confidence tag. Never emit "DELETE THIS" in any form.

### Dead-code output

```markdown
## Dead code (diagnosis only — verify + delete via refactor-verify)

### HIGH confidence (safe to delete after verification)
- `utils/legacy_helpers.py::format_v1`           — no grep hits, no test refs, not exported
- `src/api/users_v1.py`                          — entire file unreferenced since `v2` rename
- `pkg/cli/deprecated_commands/`                 — directory orphaned from the dependency graph

### MEDIUM confidence (ask before deleting)
- `src/api/users.py::get_user_v2`                — referenced only in `tests/api/test_users_v2.py` (is the test obsolete too?)
- `lib/utils.js::formatLegacy`                   — JS, dynamic dispatch possible via `utils[fnName]`

### LOW confidence (do not delete without human review)
- `pkg/exported/Config.Validate`                 — exported symbol, downstream consumers unknown
- `src/plugins/payment_stripe.py::process`       — loaded via plugin registry at runtime
- `internal/handlers/handler_admin.go::register` — registered via reflection-based router

### Deletion candidates summary
- HIGH: <N> items
- MEDIUM: <N> items (requires operator confirmation)
- LOW: <N> items (requires human review)

Hand off to `refactor-verify` with the HIGH list for safe deletion. Each item becomes a delete-dead node in its verification tree.
```

## Secondary categories

Everything below is additional rot worth knowing about, but the primary deliverable is the dead-code list.

### God files and god functions

- Files > 500 lines of code
- Functions > 50 lines of body
- Files with > 20 top-level definitions
- Classes with > 15 methods

These are candidates for splitting. Report them with the metric that triggered the flag. Hand off to `refactor-verify` for the safe split when the operator approves.

### Churn × complexity hotspots

A file that changes often *and* is complicated is where bugs live. Either dimension alone is not enough:

- **High churn, low complexity** — a config file that gets touched every day. Boring, not a refactor target.
- **High complexity, low churn** — a legacy util that's complicated but stable. Probably fine; leave it.
- **High churn, high complexity** — this is the hotspot. Flag it.

How to compute (language-agnostic):

```bash
# Churn per file — commits touching it, last 6 months
git log --since='6 months ago' --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn

# Complexity per file — preferred: lizard (Python) or scc (Go)
lizard . --CCN 10 --length 50
scc . --no-cocomo
```

Multiply churn rank × complexity rank. Flag anything in the top 10 as a hotspot.

**Fallback** when `lizard` and `scc` aren't installed: use LOC as a weak proxy for complexity. Flag files in the intersection of top-20-churn and top-20-LOC. Tell the operator the fallback is in use and offer to install `lizard` (`pip install lizard`) or `scc` (`brew install scc`) for a sharper signal.

This is the "Code as a Crime Scene" methodology (Adam Tornhill) — churn × complexity identifies the files that carry the most risk. Nicolas Carlo's `understandlegacycode.com` has the best free write-up.

### Hardcoded paths and platform assumptions

Grep patterns that almost always indicate a portability bug:

- `C:\\` / `c:\\` / `C:/` — Windows absolute path
- `/Users/` / `/home/` — Unix absolute home path
- `~/` in string literals (not shell commands)
- Literal IPv4 / IPv6 addresses in source (`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`)
- `\\` as a path separator in string literals
- References to usernames or machine names in paths

Hand off to `manage-config-env` — it owns the fix pattern (constant vs env var decision).

### Stale TODOs

Any `TODO` / `FIXME` / `XXX` / `HACK` comment older than six months (via `git blame`). Either the author never came back, or the operator forgot the context. Both cases need a decision: fix it, delete it, or turn it into an issue.

### Lopsided import graphs

- **High fan-in** — files that everything imports. Candidates to split if they're also complex, because touching them risks everything downstream.
- **High fan-out** — files that import 20+ other files. Candidates for coupling review — they might be doing too much.

Compute with a language-specific import parser (`madge` for JS/TS, `pydeps` for Python) or approximate with `grep -rn "import <module>"` counts.

### Dependency rot

- Unpinned dependencies in production
- Dependencies with known CVEs (`pip-audit`, `npm audit`, `cargo audit`, `govulncheck`)
- Dependencies not updated in 2+ years (often abandoned)
- Packages in the manifest but never imported (can be removed — dead dependencies are dead code)
- Packages imported but not in the manifest (hallucinated import, or a missing install — `refactor-verify`'s job to fix)

## Output — prioritized diagnosis

```markdown
# Repo rot report — <date>

## Stats
- Files: <N>
- Total LOC: <N>
- Dead-code candidates: <N HIGH> / <N MEDIUM> / <N LOW>
- God files (>500 LOC): <N>
- Hotspots (churn × complexity): <N>

## Dead code
<HIGH / MEDIUM / LOW sections as shown above>

## God files / functions
- `src/api/user.py` — 1203 LOC, 24 top-level functions
- `src/auth/session.ts::handleLogin` — 87-line function body
- ...

## Hotspots (churn × complexity, top 10)
| # | File | LOC | CCN avg | Commits (6mo) | Notes |
|---|------|-----|---------|---------------|-------|
| 1 | src/auth/session.ts | 870 | 18 | 47 | also flagged as god file |
| 2 | ... | | | | |

## Hardcoded paths and platform assumptions
- `src/config.ts:42` — `/Users/alice/Projects/foo`
- `scripts/deploy.sh:15` — literal IP `192.168.1.10`
- ...

## Stale TODOs (>6 months)
- `src/db.py:87` — `TODO: handle connection timeout` (authored 2024-11, 17 months old)
- ...

## Dependency rot
- `requirements.txt` — 3 unpinned, 1 with CVE
- `package.json` — `left-pad` last updated 2018
- ...

## Hand-off summary
- **Dead-code HIGH** (<N> items) → `refactor-verify` for safe deletion
- **God files** (<N> items) → `refactor-verify` for safe splits
- **Hotspots** (<N> items) → `refactor-verify` when the operator picks one
- **Hardcoded paths** (<N> items) → `manage-config-env`
- **Dependency CVEs** (<N> items) → `audit-security`
- **Stale TODOs becoming real work** → `write-for-ai` to file issues

## What this report did NOT do
Pure diagnosis. No files edited, no commits made. Approve any item and it gets handed to the specialist that owns the fix.
```

The bias is **high-leverage + low-risk first**. Dead code HIGH is usually the cleanest starting point — every deletion shrinks surface area with zero behavioral risk. Hotspot refactors are higher leverage but higher risk.

## Things not to do

- **Don't edit, delete, rewrite, or run tests.** This skill is diagnosis-only. If you find yourself about to make a file change, stop — that's `refactor-verify`'s job.
- **Don't produce a "clean code" style report.** Cyclomatic complexity > 10 is not a moral failing. If a file is stable and low-churn, it's fine.
- **Don't emit dead-code findings without a confidence tag.** Every dead-code line must be tagged HIGH / MEDIUM / LOW.
- **Don't recommend fixes without evidence.** Every finding must cite the metric or signal that triggered it — a grep count, a commit count, a file size, an LSP reference count.
- **Don't scope-creep into planning.** "Here's what's wrong" is the deliverable. "Here's the fix plan" belongs in the hand-off skill.

## Hand-offs

- **Dead code (HIGH)** → `refactor-verify` with the list, each item becoming a delete-dead node
- **Dead code (MEDIUM)** → operator confirmation required, then `refactor-verify`
- **Dead code (LOW)** → human review required; never auto-hand-off
- **God file, hotspot, or coupling smell** → `refactor-verify` for the safe split (operator picks one target)
- **Hardcoded path / platform assumption** → `manage-config-env` for the fix pattern
- **Dependency CVE** → `audit-security` for severity and incident response
- **Stale TODO becomes real work** → `write-for-ai` to file the issue

## Details and tools

The full methodology is inlined in this `SKILL.md` rather than split into references. Tools worth knowing (install-on-demand):

- `scc` — fast LOC + complexity, works on any language
- `lizard` — cyclomatic complexity per function, most mainstream languages
- `tokei` — fast LOC (no complexity, faster than scc on huge repos)
- `madge` — JS/TS import graph visualizer
- `radon` — Python cyclomatic complexity
- `vulture` / `pyflakes` — Python dead-code detection
- `ts-prune` / `knip` / `unimported` — TypeScript / JavaScript dead-code detection
- `deadcode` — Go dead-code detection
- `cargo +nightly udeps` — Rust unused-dependency detection
- `git log --numstat` — the universal churn primitive, always available

Scripts and references in this skill directory are intentionally minimal — the primary deliverable is the diagnostic report, and the analysis lives in the single SKILL.md so nothing drifts out of sync.
