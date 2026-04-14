---
name: fight-repo-rot
description: Finds what's rotting in a repo and returns a prioritized fix list. Core metric is churn × complexity — files that change often AND are complicated are the highest-risk refactor targets. Also finds god files, dead code, hardcoded paths, stale TODOs, and lopsided import graphs. Language-agnostic.
when_to_use: Trigger on "clean this up", "what's rotting", "dead code", "is my repo okay", "where should I refactor next", "too messy", "too many files", before a major new feature, or before open-sourcing the project.
allowed-tools: Grep Glob Read Bash(git log *) Bash(git blame *) Bash(git ls-files *) Bash(wc *) Bash(find *)
---

# fight-repo-rot

Repos don't break in a day. They rot over months. This skill surfaces what's rotting so the operator can aim their limited refactor energy at the targets that matter.

The guiding principle: **measure before you refactor**. "Clean up" without data leads to cosmetic churn. This skill gives a prioritized list with a reason next to each item.

## When to trigger

- "clean up this repo" / "what needs cleaning"
- "what's rotting"
- "is there dead code"
- "where should I refactor"
- "my repo is a mess"
- "is my repo okay" (ambiguous — run this as a health check first)
- before a major new feature (fix the hotspots first)
- before open-sourcing (survey rot before strangers see it)

## The one metric that matters: churn × complexity

A file that changes often and is complicated is where bugs live. Either change frequency or complexity alone is not enough:

- **High churn, low complexity** — a config file that gets touched every day. Boring, not a refactor target.
- **High complexity, low churn** — a legacy util that's complicated but stable. Probably fine; don't touch it.
- **High churn, high complexity** — **this is the hotspot**. Fix it first.

How to compute it (language-agnostic):

```bash
# Churn per file — count of commits touching it, last 6 months
git log --since='6 months ago' --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn

# Complexity per file — use lizard (Python-based, any language) or scc (any language)
lizard . --CCN 10 --length 50   # functions with CCN>10 or length>50
scc . --no-cocomo               # LOC per file
```

Multiply churn rank × complexity rank. Top 10 is the refactor queue.

### Fallback when `lizard` and `scc` are not installed

Both tools are one-line installs, but the operator might not have them and might not want to install anything. Fall back to a pure-git + pure-POSIX computation:

```bash
# Churn (same as above)
git log --since='6 months ago' --name-only --pretty=format: | grep -v '^$' | sort | uniq -c | sort -rn > /tmp/churn.txt

# LOC as a weak proxy for complexity (large files ≈ complex files, roughly)
git ls-files | xargs -I{} sh -c 'wc -l "{}" 2>/dev/null' | sort -rn > /tmp/loc.txt

# Combine: files that appear in the top of both lists are the hotspots.
# Top 20 churn + top 20 LOC → intersection is the real candidate list.
```

This is coarser than `lizard --CCN` (a 500-line config file is not complex, just big) but it finds the 80% case. Tell the operator the fallback is in use and offer to install `lizard` (`pip install lizard`) or `scc` (`brew install scc` / `go install github.com/boyter/scc`) for a better measurement.

### Dead-code confidence levels

Static dead-code detection produces false positives. Dynamic imports, reflection, test-only usage, and CLI entry points can all make a function *look* dead while it isn't. Always tag each finding with a confidence level so the operator doesn't delete something load-bearing.

| Confidence | What it means | Safe to delete? |
|---|---|---|
| **HIGH** | No textual reference anywhere in the repo (via `git grep -w`), not in tests, not in docs, not in entrypoints, and the symbol is not exported for external use | Yes, after a final test run |
| **MEDIUM** | No textual reference in the main source tree, but appears in test files or is defined in a language with dynamic dispatch (Python, Ruby, JS) | Ask before deleting — the test may be load-bearing, or a dynamic caller may exist |
| **LOW** | Symbol is exported from a package, appears in generated files, or the language uses reflection/codegen heavily (Go, Java annotations, dependency injection) | Do not delete without human review |

Output format (extend the rot report):

```
## Dead code (probable)
Verify before removing.

- `utils/legacy_helpers.py::format_v1`    HIGH — no references in grep, no tests
- `src/api/users.py::get_user_v2`         MEDIUM — only called in tests/api/test_users.py
- `pkg/exported/Config.Validate`          LOW — exported, may be used by downstream consumers
```

Never output "DELETE THIS" without a confidence tag next to it.

This is the "Code as a Crime Scene" methodology popularized by Adam Tornhill — churn × complexity identifies the files that carry the most risk. Nicolas Carlo's `understandlegacycode.com` has the best free write-up if you want to go deeper.

## Other rot categories

Run these alongside the hotspot analysis. Output all findings in one consolidated report.

### God files / god functions

- Files > 500 lines of code
- Functions > 50 lines of body
- Files with > 20 top-level definitions
- Classes with > 15 methods

These are candidates for splitting. Hand-off to `refactor-safely` when the operator agrees.

### Dead code

- Functions that nothing calls (check via LSP find-references or `grep -r <name>`)
- Exports that no other file imports
- Files that nothing imports
- Whole directories that are orphaned from the dependency graph

Be careful: dynamic imports, reflection, and runtime dispatch can make code look dead when it isn't. Mark uncertain cases as "probably dead — verify before removing" and hand off to the operator.

### Hardcoded paths and platform assumptions

Grep patterns that almost always indicate a portability bug:

- `C:\\` / `c:\\` / `C:/` — Windows absolute path
- `/Users/` / `/home/` — Unix absolute home path
- `~/` in string literals (not shell commands)
- Literal IPv4 / IPv6 addresses in source (`\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`)
- `\\` as a path separator in string literals
- References to usernames in paths

Hand-off to `manage-config-env` for the fix pattern.

### Stale TODOs

Any `TODO` / `FIXME` / `XXX` / `HACK` comment that's older than six months (via `git blame`). Either the author never came back, or the operator forgot the context. Both cases need a decision: fix it, delete it, or turn it into an issue.

### Lopsided import graphs

- **High fan-in** — files that everything imports (candidates to split if they're also complex, because touching them risks everything downstream)
- **High fan-out** — files that import 20+ other files (candidates for coupling review; they might be doing too much)

Compute with a language-specific import parser, or approximate with `grep -rn "import <module>"` counts.

### Dependency rot

- Unpinned dependencies in production
- Dependencies with known CVEs (run `pip-audit`, `npm audit`, `cargo audit`, `go mod why` as available)
- Dependencies that haven't been updated in 2+ years (often abandoned)
- Packages in the manifest but never imported (can be removed)
- Packages imported but not in the manifest (hallucinated import — `refactor-safely`'s job to fix)

## Output — prioritized fix list

```markdown
# Repo rot report — <date>

## Stats
- Files: <N>
- Total LOC: <N>
- Tracked files with high churn × complexity: <N>

## Hotspots (top 10)
Sorted by churn × complexity. Fix these first.

| # | File | LOC | CCN avg | Commits (6mo) | Recommendation |
|---|------|-----|---------|---------------|----------------|
| 1 | src/auth/session.ts | 870 | 18 | 47 | Split into session-core + session-http — hand off to refactor-safely |
| 2 | ... | | | | |

## God files (> 500 LOC)
- `src/api/user.py` (1203 LOC, 24 functions) — split by concern
- ...

## Dead code (probable)
Verify before removing.
- `utils/legacy_helpers.py::format_v1` — no references anywhere
- ...

## Path hardcoding
- `src/config.ts:42` — `/Users/alice/Projects/foo` — move to env var
- ...

## Stale TODOs (>6 months)
- `src/db.py:87` — `TODO: handle connection timeout` (authored 2024-11, 17 months ago)
- ...

## Dependency rot
- `requirements.txt` — 3 unpinned, 1 with CVE (see `pip-audit` output)
- ...

## Recommended order of operations
1. Fix hotspot #1 (session.ts) — biggest leverage
2. Remove dead code in `utils/legacy_helpers.py` — low risk, high morale
3. Move hardcoded paths to env vars — quick wins
4. Resolve stale TODOs by deleting or filing issues
5. Update `requirements.txt` pinning
```

The recommendation order is biased toward **high leverage first, low risk last**. The operator can stop at any point and still have shipped value.

## Things not to do

- **Don't produce a "clean code" style report.** Cyclomatic complexity > 10 is not a moral failing. If the file is stable and low-churn, it's fine.
- **Don't auto-delete dead code.** Always hand off to the operator. Dynamic imports can fool static analysis.
- **Don't recommend a refactor without evidence.** Every recommendation must cite the metric that triggered it.
- **Don't scope-creep into "let me fix this for you right now."** This skill surfaces problems. Fixing is `refactor-safely`'s job.

## Hand-offs

- Hotspot or god file → `refactor-safely` for the safe split
- Hardcoded path → `manage-config-env` for the env var pattern
- Dependency CVE → `audit-security`
- Stale TODO becomes real work → use `write-for-ai` to file the issue

## Details

The full methodology is inlined in this SKILL.md rather than split into references. Specific tools worth knowing (install-on-demand):

- `scc` — fast LOC + complexity, works on any language
- `lizard` — cyclomatic complexity per function, most mainstream languages
- `tokei` — fast LOC (no complexity, but faster than scc on huge repos)
- `madge` — JS/TS import graph visualizer
- `radon` — Python cyclomatic complexity
- `pyflakes` / `vulture` — Python dead-code detection
- `ts-prune` — TypeScript unused exports
- `git log --numstat` — the universal churn primitive, always available
