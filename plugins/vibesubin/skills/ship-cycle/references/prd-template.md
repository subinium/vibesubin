# PRD template

The PRD is the theme-level view that individual issues cannot provide. A future AI session reading a single PRD must be able to reconstruct *why these N issues exist together* without re-reading every issue body. Keep the filled PRD between 80 and 200 lines for a typical 5–15 issue cycle. Section headings stay in English for `gh`/grep stability; prose follows the operator's chosen language.

Default location: `PRD.md` at the repo root. Use `/tmp/<repo>-prd-vX.Y.Z.md` when the operator wants a non-committed draft. For patch cycles with fewer than 3 issues, skip the file and inline a one-paragraph PRD in the Step 7 approval prompt.

## Structure

```markdown
# PRD — <project name> <milestone target>

## Context
One or two paragraphs. What prompted this cycle — pasted `/vibesubin` sweep findings, external audit, `codex-fix` output, operator initiative? Include the date and the upstream trigger (sweep timestamp, commit SHA, issue number, PR link). State the repo state at cycle start (current version, default branch, last release date).

## 북극성 목표 (North-star goals)
Three to five one-line goals this cycle moves toward. Each goal is a user-visible outcome, not an internal task.

- <Goal 1 — user-visible improvement>
- <Goal 2 — user-visible improvement>
- <Goal 3 — user-visible improvement>

## Themes
Group candidate issues into 2–5 themes. Each theme is one operator-memorable unit of work.

### Theme A — <one-line name>
- **Objective** — what this theme achieves if all its issues close
- **Issues**
  - #<N or draft-slug>: <one-line title>
  - #<N or draft-slug>: <one-line title>
- **Success criterion** — the single concrete check that proves the theme shipped (a command, a grep count, a user-visible state)
- **Priority** — P0 (release blocker) / P1 (ship together) / P2 (defer if scope creeps)

### Theme B — <one-line name>
- **Objective** —
- **Issues**
  - #<N>: <title>
- **Success criterion** —
- **Priority** —

## Milestone cluster plan
Apply `references/milestone-rules.md`. Each row maps themes to a semver version.

| Milestone | Version | Themes included | Issue count | Size estimate |
|---|---|---|---|---|
| vX.Y.Z | patch | Theme A | N | S/M/L |
| vX.Y+1.0 | minor | Theme B, Theme C | N | S/M/L |

## Success metrics
Observable, checkable by a fresh session. Examples:

- `git grep <pattern>` returns zero in non-CHANGELOG files
- `python3 scripts/validate_skills.py` exits 0
- p95 on `/users?limit=50` under 50ms on staging
- Every worker SKILL.md has a Harsh-mode section (`grep -l '^## Harsh mode' | wc -l` equals worker count)

## Out of scope for this cycle
Items surfaced during review that will NOT ship this cycle. One-line reason for each. Recording these prevents scope creep and prevents the same items resurfacing in a later review.

- <item>: <reason — too large / defer to next minor / not a real issue / needs design work>
- <item>: <reason>

## Already-done-at
Prior work this PRD builds on. Keeps the next session from duplicating completed work.

- <commit SHA | issue #N | PR #N>: <one-line summary>
- <commit SHA | issue #N | PR #N>: <one-line summary>
```

## Fill guidance

- **Context** stays to two paragraphs max. If it grows longer, the trigger is too broad — split the cycle.
- **Themes** under 3 signals the cycle is too small for a PRD file; inline in the Step 7 prompt instead. Over 5 signals the cycle is too broad; split into sequential cycles.
- **Success criterion** per theme must be executable or observable. "Code is cleaner" is not a criterion; `git grep <pattern> | wc -l` returning zero is.
- **Milestone cluster plan** rows must match the Step 7 approval table exactly. If they diverge, the PRD is stale and must be updated before Step 8.
- **Out of scope** is mandatory, not optional. An empty section means the operator did not audit adjacent work.
- **Already-done-at** is mandatory for any cycle that follows a prior related release. Empty is fine only for the very first cycle on a fresh repo.

## When not to write a PRD file

Inline a one-paragraph PRD in the Step 7 approval prompt instead of creating a file when:

- The cycle has fewer than 3 issues.
- The cycle is a single-theme patch (e.g., three bugs in the same module).
- The operator explicitly says *"skip the PRD"* — log the skip decision in the Step 7 approval prompt for audit.
