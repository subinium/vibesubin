# PRD track — ship-cycle for any host

## Purpose

The PRD track is ship-cycle's local-file path: same methodology, same 11 steps, same invariants, but the `gh` API calls become markdown-file operations on disk. Use it on any host that is not GitHub, or when `gh` is unauthenticated, or when the operator wants a local-first audit trail.

When to use:

- Remote is GitLab / Gitea / Forgejo / Bitbucket / self-hosted / non-existent.
- `gh` is installed but not authenticated and the operator cannot authenticate right now.
- Air-gapped environment or explicit local-first preference.
- A bridge cycle before migrating the repo to a host with issues support.

This is the fallback for SKILL Step 1's host check. Instead of exiting with the one-line fallback, fall through to this track when the operator confirms they want local tracking.

## File layout

The PRD track produces this tree at the repo root. One directory per milestone:

```
docs/
  release-cycle/
    v0.6.0/
      PRD.md                        ← theme-level PRD (reuse prd-template.md shape)
      issues/
        001-fix-auth-regression.md  ← one file per issue, NNN prefix is the issue number
        002-refactor-user-api.md
        003-add-dark-mode.md
      CHANGELOG.draft.md            ← aggregated from closed issues at release time
      release-notes.md              ← committed — this IS the release artifact on non-GitHub hosts
```

Rules:

- `docs/release-cycle/vX.Y.Z/` keeps release artifacts together and separate from the active root `CHANGELOG.md`.
- Closed issue files stay on disk. They are the durable audit trail that the GitHub track gets from `gh issue list --state closed`.
- `CHANGELOG.draft.md` is scratch space during a cycle; its contents move into the root `CHANGELOG.md` at Step 10.
- `release-notes.md` is committed on the PRD track (unlike the GitHub track's `/tmp` file) because on a host without a release API, the in-repo file IS the release artifact.

## Issue-as-markdown template

Every issue file in `docs/release-cycle/vX.Y.Z/issues/NNN-slug.md` uses this shape. Frontmatter fields mirror the GitHub issue fields exposed via API, so a future migration to GitHub can be scripted (see "Migration" below).

```markdown
---
number: 001
title: Fix auth regression in session refresh
status: open                         # open | in-progress | closed | blocked
labels: [bug, auth, priority:critical]
milestone: v0.6.0
assignee: null
opened: 2026-04-24
closed: null
branch: bug/issue-001-fix-auth-regression
pr: null                             # link to MR/PR when created
closes_via: commit                   # commit | manual
---

## Problem
<what's wrong, with concrete evidence — file:line, metric, grep count, log excerpt>

## Acceptance criteria
- [ ] <verifiable criterion 1>
- [ ] <verifiable criterion 2>

## Implementation notes
- Scope files: src/api/auth.ts, src/lib/session.ts
- Hand-off skill: /refactor-verify
- Out of scope: <explicit list>
- Depends on: (#003)

## Test plan (required — scoped by label)
<same shape as issue-body-template.md — regression test, benchmark, before/after equivalence, etc.>

## Docs plan (required — same PR as the code fix)
- <file> — <what changes, one line>
- <file> — <what changes, one line>

## Handoff notes (required — for the next AI session)

What next session needs:
- <one- or two-sentence context>

Already done at:
- <scope>: #<issue or sha or path>

## Resolution log
<append commit SHAs, PR/MR links, test results as work progresses>
```

Section headings stay English for grep stability across sessions. Prose language follows the operator's choice at SKILL Step 3.

## Step-by-step mapping: GitHub track → PRD track

| Step | GitHub track | PRD track |
|---|---|---|
| 1 (Host check) | `gh repo view && gh auth status` | `test -d .git` — any git repo works, even without a remote |
| 2 (State assumptions) | Assumptions block | Same block, add `Track: PRD (local)` line |
| 3 (Language elicitation) | Ask if ambiguous | Same |
| 4 (Intake) | Three input shapes (paste / sweep / named scope) | Same |
| 5 (Draft issues) | In-session drafts, not yet mutated | Draft one file per issue at `docs/release-cycle/vX.Y.Z/issues/NNN-slug.md`. Not committed yet — drafts only. |
| 5.5 (Write PRD.md) | Write to repo root or `/tmp` | Write to `docs/release-cycle/vX.Y.Z/PRD.md`. Always committed. |
| 6 (Classify milestones) | Semver decision tree (`milestone-rules.md`) | Same — milestone = one directory under `docs/release-cycle/` |
| 7 (Confirm plan) | Table, operator approves | Same |
| 8 (Create issues) | `gh issue create` per item | `git add docs/release-cycle/vX.Y.Z/issues/*.md && git commit -m "chore: draft issues for vX.Y.Z"`. Issue "number" = the file's `NNN` prefix. |
| 9 (Branch + execute) | `git checkout -b issue-<N>-slug` + hand-off | Same — branch name from the issue's frontmatter `branch:` field. On merge, set `status: closed` + append to resolution log. |
| 9a (Parallel dispatch) | Parallel Task subagents | Same |
| 9b (CI green gate) | `gh pr view … statusCheckRollup` | Host adapter: `glab mr view --json` / `tea pr status`. Plain git / no remote: run the local test command (from CI config or repo conventions) and require exit 0 before merge. Do not merge without green. |
| 10 (Release) | `gh release create vX.Y.Z` | Write release notes to `docs/release-cycle/vX.Y.Z/release-notes.md`. Annotated tag + push same as GitHub track. Host release objects: GitLab → `glab release create`; Gitea → `tea release create`; plain git → tag only, notes stay as the in-repo file. |
| 11 (Audit trail) | `gh issue comment` per closed issue | For each closed issue file, append a "Shipped in vX.Y.Z" block to the resolution log and set frontmatter `status: closed`. |

## Closing an issue in PRD track

On merge, ship-cycle performs this exact sequence on the issue file:

1. Open `docs/release-cycle/vX.Y.Z/issues/NNN-slug.md`.
2. Update frontmatter:
   - `status: closed`
   - `closed: <YYYY-MM-DD>`
   - `pr: <URL or local SHA>`
3. Append to the `## Resolution log` section:

```
### Resolved — 2026-04-24
- Commit: abc1234
- PR/MR: https://gitlab.com/org/repo/-/merge_requests/42   (or "N/A — local merge")
- Test plan status: all 3 checklist items passed
- Docs plan status: CHANGELOG.md, README.md updated in same commit
- Handoff notes:
  - What next session needs: <copy from template, fill in>
  - Already-done-at: <scope> — #<issue or sha>
```

4. Commit: `chore: close #001 (fix auth regression)` — `#001` references the file prefix, not a GitHub issue.

The resolution log section is the PRD track's equivalent of `gh issue comment` — a future session grepping closed issues for context finds the handoff notes here.

## Aggregating to CHANGELOG at release time

At Step 10, enumerate closed issues and produce CHANGELOG bullets:

```bash
MILESTONE_DIR="docs/release-cycle/v0.6.0/issues"
for f in "$MILESTONE_DIR"/*.md; do
  STATUS=$(awk '/^status:/{print $2; exit}' "$f")
  [ "$STATUS" = "closed" ] || continue
  NUM=$(basename "$f" | cut -c1-3)
  TITLE=$(awk '/^title:/{sub(/title: /, ""); print; exit}' "$f")
  TYPE=$(awk '/^labels:/{sub(/labels: /, ""); print; exit}' "$f" \
           | grep -oE '(bug|feat|refactor|perf|docs|chore|security)' | head -1)
  echo "- $TYPE: $TITLE (#$NUM)"
done > "$MILESTONE_DIR/../CHANGELOG.draft.md"
```

Then sort the draft bullets into Keep-a-Changelog groups and append to the root `CHANGELOG.md` under a new `[X.Y.Z] — YYYY-MM-DD` heading:

| `type` label | CHANGELOG group |
|---|---|
| `feat` | `### Added` |
| `refactor`, `perf`, `chore` | `### Changed` |
| `bug` | `### Fixed` |
| (removal) | `### Removed` |
| `security` | `### Security` |

Functional-only style — same rule as the GitHub track. No narrative, no meta-rationale. Every bullet describes an observable change.

## Release notes

Same content, different destination. The GitHub track writes notes to `/tmp` and passes them via `gh release create --notes-file`. The PRD track writes notes to `docs/release-cycle/vX.Y.Z/release-notes.md` and commits them — the in-repo file IS the release artifact on a host without a release API.

Link the notes file from the root `CHANGELOG.md` version heading:

```markdown
## [0.6.0] — 2026-04-24

Release notes: [docs/release-cycle/v0.6.0/release-notes.md](./docs/release-cycle/v0.6.0/release-notes.md).

### Added
- ...
```

Section order inside `release-notes.md` matches the GitHub track's template — TL;DR, breaking (if any), new features, fixes, under the hood.

## Host-specific adapters

On a non-GitHub remote, the operator uses their host's CLI if installed. ship-cycle does not bundle adapters — keep the concerns local to the host.

| Remote | Adapter to use | Release artifact |
|---|---|---|
| GitLab | `glab mr create` / `glab mr merge` / `glab release create` | host release page + `release-notes.md` |
| Gitea / Forgejo | `tea pr …` / `tea release …` | host release page + `release-notes.md` |
| Bitbucket / other | host's own CLI or web UI | `release-notes.md` (in-repo) |
| Plain git / no remote | `git merge --no-ff`, tag only | `release-notes.md` (in-repo) |

Frontmatter field names (`status`, `labels`, `milestone`, `branch`, `pr`, `closes_via`) are stable so a future migration to GitHub is a scripted conversion — write the migration script when it's actually needed, not speculatively.

## Things the PRD track does NOT do

- Does not auto-close issues on commit messages. The PRD track has no webhook equivalent. The operator (or ship-cycle itself) must edit the frontmatter.
- Does not sync with any external system. The issue file IS the source of truth.
- Does not enforce branch protection without a remote host adapter. In plain-git mode, the operator owns `main`'s safety.
- Does not create comments, reactions, or assignment notifications. All of that is manual frontmatter edits.
- Does not produce the release artifact on a platform Releases page — on a host without a release API, the committed `release-notes.md` is the artifact.

## Invariants preserved across both tracks

These do not change between the GitHub track and the PRD track:

- Semver classification (bug / refactor / perf → patch; feat → minor; breaking → major).
- 5-item patch cap.
- Milestone = version, one-to-one, always.
- Functional-only CHANGELOG style — no narrative, no meta-rationale.
- Annotated tag (not lightweight) for every release.
- 4-part output shape (what I did / found / verified / you should do next) for every response.
- Harsh-mode framing-only rule — never inflate severity, never invent issues.
- Evidence-required rule at Step 4 — no evidence, no issue.
- Mandatory Test plan + Docs plan + Handoff notes in every issue body.

One deliberate difference:

- **Release-notes commit rule**: GitHub track does NOT commit the notes temp file. PRD track DOES commit `release-notes.md` because it is the release artifact on hosts without a release API. This is the only invariant that differs between tracks.
