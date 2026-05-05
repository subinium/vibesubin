# Branch model selection

ship-cycle assumes **GitHub Flow** — a single long-lived `main` branch plus short-lived feature branches that merge back via PR. Other models exist; this file documents which ones ship-cycle handles, which it defers on, and what the operator sees when ship-cycle meets a non-GitHub-Flow repo.

The conventions in `pr-branch-conventions.md` (branch naming, commits, PR template, merge strategy, rebase policy, force-push rules, CI green gate) all assume GitHub Flow. They still apply on Trunk-based repos with minor adjustments. They do **not** apply cleanly on GitFlow.

## Three models

```
GitHub Flow                  Trunk-based                  GitFlow
─────────────                ───────────                  ───────

main ──┬───┬───┬──            main ──┬─┬─┬──              main  ──────┬──┐
       │   │   │                     │ │ │                            │  │
       fix-A    fix-C                f f f                  release/* ┤  │
        \   \   /                     \│/                             │  │
         \   \ /                       │                              │  │
          \   ▼                        ▼ (always green)         dev ──┼──┴──┐
           merge                  cut release/v1.x                    │     │
                                                                feature/*    │
                                                                              │
                                                                   hotfix/*  │
                                                                              ▼
                                                                          dev + main
```

| Property | GitHub Flow | Trunk-based | GitFlow |
|---|---|---|---|
| Long-lived branches | `main` | `main` | `main`, `dev` |
| Feature branch lifetime | hours-to-days | hours-only | days-to-weeks |
| Release branches | none | cut at tag time only | always-on `release/*` |
| Hotfix branches | none (just patch from main) | none | dedicated `hotfix/*` → main + dev backport |
| Best fit | SaaS, single production line, strong CI | monorepo + feature flags, very strong CI | multi-version LTS, parallel maintenance lines |
| AI-worker friendliness | high (short branches → low conflict surface) | very high | low (multi-merge graph confuses parallel dispatch) |

## Why ship-cycle picks GitHub Flow

Three reasons, in order of weight:

1. **Audit-trail simplicity.** `PR merge → issue auto-close → milestone close → release pipeline` is a single causal chain. GitFlow's double-merge (`release/*` → `main` *and* → `dev`) splits the chain — an issue closed by a `release/*` PR doesn't always close cleanly on `main`, breaking the milestone aggregator.
2. **Parallel worker safety.** Each ship-cycle worker owns one branch, one PR, one merge. Long-lived branches (`dev`, `release/*`) raise the chance two workers operating on the same milestone touch the same long branch and fight over rebase / force-push.
3. **Fewer load-bearing rules.** GitHub Flow's invariants (force-push policy §6, CI green gate §7, rebase-first §5 in `pr-branch-conventions.md`) are short and orthogonal. GitFlow needs additional rules per branch type — different merge strategy on `release/*`, different force-push policy on `dev`, different validation gate on `hotfix/*` — and each rule is an extra surface area for AI mistakes.

This is a deliberate scope choice, not a deficiency. ship-cycle does not "support all branch models"; it picks one and goes deep.

## What happens when ship-cycle meets a GitFlow repo

The detection step at `pr-branch-conventions.md §1.1` determines whether the repo has an existing branch convention. ship-cycle treats GitFlow as "an existing convention that ship-cycle does not own."

**Detection signals for GitFlow:**

- `dev` (or `develop`) branch exists alongside `main`, both tracked.
- `CONTRIBUTING.md` or `CLAUDE.md` documents `feature/*` / `release/*` / `hotfix/*` patterns.
- `git for-each-ref refs/heads/` shows ≥ 10 of the last 20 branches following `feature/*` / `release/*` / `hotfix/*` shape.

When these match, ship-cycle's behavior at Step 1.5 (track selection) and Step 9 (branch + execute):

1. **Surface the detection.** ship-cycle prints a one-line note: *"Detected GitFlow-shaped convention (`feature/*`, `release/*`, `hotfix/*`). ship-cycle defers its branch convention to the existing one and only enforces commit / PR-body / CI conventions."*
2. **Defer branch naming.** Branch shape follows the repo's convention (`feature/<slug>`, `hotfix/<slug>`) instead of ship-cycle's `<type>/issue-<N>-<slug>`. Issue number is still embedded somewhere (in the slug, in the PR title, or in the commit footer).
3. **Block release pipeline (Step 10) for GitFlow-shaped flows.** ship-cycle's release pipeline assumes `main` is the integration target. On GitFlow, release-branch merge → main + dev backport is a separate workflow not modeled here. Operator must run the GitFlow release dance manually; ship-cycle stops at Step 9 and reports.
4. **Keep what still applies.** Conventional Commits with `Closes #N` footer, 6-section PR body, CI green gate, force-push policy on protected branches — these all remain in force regardless of branch model.

**Detection signals for Trunk-based:**

- Single long branch (typically `main`), no `dev`.
- `release/*` branches exist but are short-lived (created at tag cut, deleted after).
- Feature flags or canary deploys show up in code (LaunchDarkly, GrowthBook, Statsig, custom flag system).

Trunk-based is functionally GitHub Flow with `release/*` branches at tag time. ship-cycle handles it the same way as GitHub Flow at Steps 1–9; at Step 10 (release pipeline), if a `release/*` branch is present, ship-cycle tags off that branch instead of `main`. The pipeline commands are otherwise unchanged.

## What the operator sees in the Assumptions block (Step 2)

The `Branch convention:` line of the Assumptions block surfaces the detection result:

```
- Branch convention:       <type>/<issue-N>-<slug>  (default — ship-cycle owns)
- Branch convention:       feature/<slug>           (detected GitFlow — ship-cycle defers, see references/branch-models.md)
- Branch convention:       feat/<slug>              (detected per CONTRIBUTING.md — ship-cycle defers, see references/branch-models.md)
```

When the convention is detected and deferred, ship-cycle adds a sub-note:

```
- Release pipeline (Step 10) is GitHub-Flow-shaped — incompatible with GitFlow's
  release-branch merge cycle. ship-cycle will stop at Step 9 and hand off the
  release dance to the operator. Continue?
```

Operator confirms or aborts.

## What ship-cycle does NOT do for non-GitHub-Flow repos

- **Does not migrate GitFlow → GitHub Flow.** That is a multi-cycle refactor of the team's working agreement, not a ship-cycle concern.
- **Does not run release pipeline on `release/*` branches in GitFlow.** Stops at Step 9 instead.
- **Does not infer hotfix backport targets.** If a hotfix needs to land on `main` + `dev` + a parallel `v0.5.x` line, the operator drives those merges; ship-cycle records each as a separate issue.
- **Does not treat absence of `pr-branch-conventions.md §1.1` detection signals as "no convention detected" silently.** It surfaces *"no existing convention detected, defaulting to ship-cycle's `<type>/issue-<N>-<slug>`"* explicitly so the operator can correct if wrong.

## Adding a new branch-model adapter

If a future cycle needs ship-cycle to handle GitFlow as a first-class track (not just deferral), the change is large enough to warrant a major decision and a new `references/gitflow-track.md` parallel to `prd-track.md`. Don't extend this file — branch-model support is already at the limit of what one reference file should carry.

The same applies to other models (release-trains, stacked branches, monorepo per-package). Each is a separate reference, not a section in this one.
