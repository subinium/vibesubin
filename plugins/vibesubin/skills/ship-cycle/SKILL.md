---
name: ship-cycle
description: Issue-driven development orchestrator. Turns improvement intent into a well-specified, bilingual issue set; clusters issues into milestones that map 1:1 to semver versions; guides branch, commit, and PR hygiene; generates changelog entries and release notes deterministically from closed issues; leaves a durable audit trail for the next AI session. Direct-call only — not part of the /vibesubin parallel sweep. Host requirement — GitHub repo with authenticated `gh` CLI; on any other host or with `gh` unauthenticated, emits a one-line fallback and exits.
when_to_use: Trigger on "plan a release", "릴리즈 계획", "cut a release", "릴리즈 하자", "이슈로 남기고 처리", "make issues for this", "bundle these findings into issues", "turn sweep findings into issues", "issue-driven", "이슈 드리븐", "roadmap for 0.N.0", "ship cycle", "tag and release", "release notes 써줘", "generate changelog from PRs", "여러 수정을 묶어서 릴리즈".
allowed-tools: Read Grep Glob Task Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git diff-index *) Bash(git branch *) Bash(git checkout *) Bash(git tag *) Bash(git push *) Bash(git rev-parse *) Bash(git merge-base *) Bash(gh issue *) Bash(gh pr *) Bash(gh release *) Bash(gh api *) Bash(gh repo *) Bash(gh auth *) Bash(ls *) Bash(test *) Bash(cat *) Bash(wc *)
---

# /ship-cycle

Turns improvement intent into shipped versions, deterministically: *intent → issues → milestones = versions → tagged release*. Direct-call only. Given a backlog (pasted notes, a `/vibesubin` sweep report, or a named scope), this skill writes a well-specified bilingual issue set, clusters items into semver milestones, dispatches the implementation to the correct vibesubin specialist, and — when a milestone closes — runs the full release pipeline end-to-end: changelog aggregation, manifest bump, annotated tag, GitHub release, audit trail. No interpretation, no flourish — the milestone state is the release state.

## What this skill owns vs. hands off

Owns:

- **Issue specification** — titles, bodies, labels, dependency links, language.
- **Milestone clustering** — semver classification, cluster heuristics, cap enforcement.
- **Release pipeline** — preflight checks, changelog aggregation, version bump, annotated tag, `gh release create`, verification.
- **Audit trail** — close-comments on issues, milestone closure, release ↔ issue linkage.

Hands off:

- **Actual code changes** — the fix itself is always another skill's job (`refactor-verify`, `audit-security`, etc.).
- **Release-note prose** — `write-for-ai` writes the user-facing narrative when the operator wants polish; this skill produces the functional-only scaffold.
- **CI wiring** — `setup-ci` owns workflow files.

Not a replacement for:

- **`write-for-ai`** — owns commit-message and PR-body style. This skill enforces *when* commits happen (`Closes #N` footer on each) and *which* PRs block a release, but not the prose inside them.
- **`project-conventions`** — owns branch-strategy defaults. This skill suggests `issue-<N>-<slug>` branch names, but defers to an existing project convention when one exists.

## Host requirement and preconditions

GitHub repo with authenticated `gh` CLI. Check both in Step 1; on any non-GitHub host or with `gh` unauthenticated, emit a one-line fallback and stop — no retry, no alternative path.

```bash
gh repo view --json name >/dev/null 2>&1   || echo "not-a-gh-repo"
gh auth status >/dev/null 2>&1             || echo "gh-not-authenticated"
```

If either prints a marker, respond with exactly one sentence and stop:

> *"`/ship-cycle` requires a GitHub repo with authenticated `gh` CLI — run `gh auth login` or invoke the underlying workers (`/refactor-verify`, `/audit-security`, etc.) directly on non-GitHub hosts."*

Graceful pass is the expected outcome on non-matching hosts; it is not an error.

## State assumptions — before acting

Before proceeding past Step 2, write an explicit `Assumptions` block to the session and ask the operator to confirm. A wrong assumption here silently corrupts every downstream step.

```
## Assumptions
- Repo state:              <clean | dirty (N staged, M unstaged) | detached HEAD>
- Default branch:          <main | master | dev>
- Current version:         <from manifests — path and value — or "pre-1.0 / no manifests, using latest tag">
- Work scope:              <pasted findings | sweep output at /tmp/... | user-named area "perf in src/api/">
- Issue language:          <Korean | English | Japanese | Chinese>
- Milestone target:        <new version to cut — vX.Y.Z | just-issues mode, no release this cycle>
- Existing branch convention: <detected from CONTRIBUTING.md / root CLAUDE.md / last 20 branch names — e.g., "feature/<topic>" from project-conventions; default fallback: "issue-<N>-<slug>">
```

Stop and ask when:

- Scope is ambiguous (*"clean up"* with no target).
- Language signal is missing — prompt returned by the operator has no dominant language and no direct answer to the language question.
- Working tree is dirty with a staged-plus-unstaged mix (unclear which changes the cycle is building on).
- Current version can't be determined (no manifests, no tags) — operator must state a starting version.

Never invent assumptions to keep moving. An invented default branch or an invented current version is worse than a blocked step.

## Procedure — 11 steps

Run in order. Each step has a verification or a confirm-gate. Do not skip.

### Step 1 — Host check

Run the two `gh` checks above. On failure, one-line fallback and stop. On success, capture:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
```

### Step 2 — State assumptions

Populate the Assumptions block above. Detect each value:

```bash
git status --porcelain | head
git rev-parse --abbrev-ref HEAD
git describe --tags --abbrev=0 2>/dev/null || echo "no-tags"
test -f package.json             && cat package.json             | grep '"version"' | head -1
test -f Cargo.toml               && cat Cargo.toml               | grep '^version'  | head -1
test -f pyproject.toml           && cat pyproject.toml           | grep '^version'  | head -1
test -f .claude-plugin/marketplace.json && cat .claude-plugin/marketplace.json | grep '"version"' | head -1
```

Surface the block. Wait for operator confirmation. Stop-and-ask conditions above apply.

### Step 3 — Language elicitation

If the operator's prompt is unambiguously in one language, use it. Otherwise ask:

> *"Issue language: 한국어 / English / 日本語 / 中文?"*

Chosen language is the issue body's primary language. Section headings and checkboxes stay in English for `gh` parsing stability (see `references/issue-body-template.md`). English mirror is optional — default off, enable only on explicit request.

### Step 4 — Intake

Three input paths:

- **(a) Pasted improvement list** — operator pastes items as prose, a checklist, or a scanner report. Parse into a flat candidate list.
- **(b) Hand off to `/vibesubin` first** — if the operator says *"sweep first, then issues"*, surface the instruction to invoke `/vibesubin` and wait for the sweep report. Consume the report as path (a) once it arrives. Do not auto-invoke the sweep — that is the operator's call.
- **(c) Named scope** — operator says *"perf in src/api/"*. Grep, `git log --since`, or targeted `Read` to enumerate candidate items within that scope. Surface the enumeration for confirmation before converting to issues.

Normalize every source into a flat candidate-item list: `[{summary, evidence, suggested_type, suggested_priority, suggested_area}]`. Evidence is concrete (`file:line`, metric, grep count, log excerpt) — if an item has no evidence, flag it and ask for one before drafting the issue.

### Step 5 — Draft candidate issues

For each candidate item, fill the template at `references/issue-body-template.md`. Body sections: Problem / Acceptance criteria / Implementation notes (with skill hand-off) / Linked. Title <72 chars, imperative, domain-prefixed. Labels: one `type`, one `priority`, one `area`.

Body goes in the language chosen at Step 3. Section headings and checkbox markers stay in English — load-bearing for cross-session tooling.

Do NOT `gh issue create` yet. Drafts stay in the session until Step 7 is confirmed.

### Step 6 — Classify into milestones

Apply the semver decision tree in `references/milestone-rules.md`:

- `bug` / `perf` / `refactor` / `test` / `docs` / `chore` → **patch** (~5 items cap)
- `feat` (additive) / new skill / new endpoint / new config with default → **minor**
- `breaking` / removed API / renamed exported symbol → **major**

Cluster heuristics: related items stay together; same-module items stay together; security-critical items get a dedicated milestone and cut immediately. Do not mix breaking + additive in one milestone — split into major + follow-up minor (see worked example 3 in `milestone-rules.md`).

Every milestone has a title `vX.Y.Z` matching the manifest version convention of the repo.

### Step 7 — Confirm plan

Surface the plan as a table and block until the operator replies `approve` / `merge` / `split` / `edit`.

```
| Milestone | Version  | Issues                  | Est size | Type  |
|-----------|----------|-------------------------|----------|-------|
| v0.4.1    | patch    | 3 bugs in src/api/      | small    | patch |
| v0.5.0    | minor    | 1 new skill + 2 docs    | medium   | minor |
| v1.0.0    | major    | 1 rename (breaking)     | small    | major |
```

`approve` → Step 8. `merge` / `split` / `edit` → revise and re-present. **Do not proceed to Step 8 until the operator explicitly approves.**

### Step 8 — Create issues

Create milestones first, then issues. Capture `gh` output to record real issue numbers — never invent them.

```bash
# 1. Create each milestone (idempotent — reuse if title already exists)
gh api repos/"$REPO"/milestones -f title="vX.Y.Z" -f description="..." 2>/dev/null \
  || gh api repos/"$REPO"/milestones --jq '.[] | select(.title=="vX.Y.Z") | .number'

# 2. For each drafted issue, write body to a temp file and create
BODY=/tmp/ship-cycle-issue-<slug>.md
cat > "$BODY" <<'EOF'
<rendered body from Step 5>
EOF

gh issue create \
  --title   "<title>" \
  --body-file "$BODY" \
  --label   "<type>,<priority>,<area>" \
  --milestone "vX.Y.Z"
# → capture stdout: https://github.com/owner/repo/issues/<N>
```

Dry-run mode: if the operator requested `dry-run`, print the commands and `BODY` contents without executing. Skip to Step 11 and report.

### Step 9 — Branch + execute

For each created issue, suggest a branch name and hand off to the right worker. If the Assumptions block detected an existing convention (e.g., `feature/<topic>` from `project-conventions`), use that and derive the topic from the issue slug; use `issue-<N>-<slug>` only as the fallback.

```bash
BRANCH="issue-<N>-<kebab-slug>"   # fallback when no project convention was detected
```

Routing by label (hand-off, not invocation — `ship-cycle` does not execute code changes):

| Label | Hand-off skill |
|---|---|
| `bug`, `refactor` | `/refactor-verify` |
| `perf` | `/refactor-verify` (perf focus) |
| `security` | `/audit-security` |
| `docs` | `/write-for-ai` |
| `chore` + `ci` | `/setup-ci` |
| `chore` + `secrets` | `/manage-secrets-env` |
| `chore` + `deps` | `/project-conventions` |
| `design`, `ui` | `/unify-design` |
| `chore` + `assets` | `/manage-assets` |
| `chore` + `dead-code` | `/fight-repo-rot` → `/refactor-verify` |

Commit footer: `Closes #<N>`. PR body: `Closes #<N>` as the first line after the summary. Both are load-bearing for GitHub's auto-close and for Step 10's aggregation query.

When the worker reports done and the PR merges, GitHub auto-closes the issue. If the worker cannot complete the item (baseline-red, missing context), leave the issue open and tag it `blocked` with a reason in a comment.

### Step 10 — Release when milestone closes

Follow `references/release-pipeline.md`. Short version — 10 commands, in order:

1. **Preflight** — milestone has zero open issues and zero open PRs; CI is green on the default branch; validator (if any) passes.
2. **Aggregate** — `gh issue list --milestone vX.Y.Z --state closed --json number,title,labels` → one CHANGELOG bullet per issue, functional-only style, grouped Added / Changed / Fixed / Removed / Security. CHANGELOG bullet style (functional-only, observable changes only, no narrative or meta-rationale) follows `write-for-ai`'s Change log doc type — this skill owns the aggregation mechanics (semver bucketing, issue-to-bullet mapping, group classification), not the style rules themselves. If the operator asks for release-note prose polish (TL;DR phrasing, migration tables, feature-highlight narrative), hand off to `write-for-ai` for the notes file while `ship-cycle` continues with the tag/release mechanics.
3. **Move `[Unreleased]` entries** under a new `[X.Y.Z] — YYYY-MM-DD` heading.
4. **Bump every manifest** — `package.json` / `Cargo.toml` / `pyproject.toml` / `.claude-plugin/marketplace.json` + `plugins/*/plugin.json` — all in one commit.
5. **Run tests and validator** — halt on red.
6. **Commit** — `chore(release): vX.Y.Z`.
7. **Push** the commit and wait for CI green.
8. **Tag** — `git tag -a vX.Y.Z -m "<one-line summary>"`, then `git push origin vX.Y.Z`. Annotated, not lightweight.
9. **Release notes to a temp file** — TL;DR, breaking (only if any), new features, fixes, under-the-hood, link to `CHANGELOG.md`.
10. **Create + verify** — `gh release create vX.Y.Z --title "<project> X.Y.Z" --notes-file <tmp>` → `gh release view vX.Y.Z`.

Do not commit the release-notes temp file. CHANGELOG is the in-repo source of truth; the notes file is the GitHub-only extract.

### Step 11 — Audit trail

For every closed issue in the milestone:

```bash
gh issue comment <N> --body "Shipped in vX.Y.Z — <release URL>. Resolved by #<PR-number>."
```

Close the milestone if it is still open:

```bash
MILESTONE_ID=$(gh api repos/"$REPO"/milestones --jq '.[] | select(.title=="vX.Y.Z") | .number')
gh api repos/"$REPO"/milestones/$MILESTONE_ID -X PATCH -f state=closed
```

Verify `CHANGELOG.md` has the dated heading. Link the release back to the milestone in the release notes' footer. Report done.

## Sweep mode — ship-cycle is not in the sweep

`/vibesubin` does not launch this skill in its parallel sweep. `ship-cycle` mutates — it creates issues, suggests branches, commits release prep, pushes tags, publishes GitHub releases. That breaks the sweep's read-only invariant and its portable-engine invariant (it requires `gh` CLI + GitHub). If a sweep-style request arrives (*"sweep and then turn findings into issues"*), the operator invokes `/vibesubin` first, reviews the sweep report, then calls `/ship-cycle` separately with the approved findings as Step 4(a) input.

Documented here explicitly so a future maintainer does not add a `sweep=read-only` branch by mistake. Its absence is deliberate — this is a process-category skill (see `docs/PHILOSOPHY.md` rule 10), and process skills are direct-call only by that rule. Same read-only-invariant logic keeps host-specific wrappers like `codex-fix` out of the sweep (rule 9) for a different reason: wrappers write files and invoke external tools. Both rules converge on the same exclusion — process and wrapper skills stay out of `/vibesubin`.

## Harsh mode — no hedging

When the task context contains `tone=harsh` (from `/vibesubin harsh` or direct phrasing like *"don't sugarcoat"* / *"매운 맛"* / *"厳しめ"*), switch output rules on every step:

- **Issue bodies**: direct subject-verb — *"Fix the N+1 query in `/api/users`"*, not *"Consider refactoring the user query for better performance"*. No *"you could"*, no *"we might want to"*.
- **Milestone classification**: do not pad a patch version with nice-to-haves to look busy. If three items match and five were proposed, the milestone has three.
- **Release notes**: lead with what was broken and what is fixed — *"Fixed session-redirect data loss (#42)"*, not *"We're thrilled to ship improvements to the auth flow"*.
- **Verdict is binary**: *"Ready to tag"* or *"Blocker: N open issues in milestone, M failing checks"*. No *"mostly ready"*, no *"a few small items"*.
- **Stale-snapshot warnings are refusals**: *"HEAD moved since the sweep report — re-run the sweep or proceed against the stale snapshot with explicit confirmation. Not proceeding silently."*

Framing only. Evidence is identical to balanced mode — same issue count, same CI state, same manifest SHAs. Never inflate severity. Never invent issues. Never write issues the operator did not approve in Step 7.

## Review modes — full and partial

- **Full review**: every issue in the milestone. Runs Steps 9–10 until the milestone closes.
- **Partial review**: operator names specific issue numbers (*"review 5, 7, 9"*). Run Steps 9–10 only on those. Release at Step 10 only if the named subset forms a complete unit of work on its own — otherwise advance the issues through Step 9, leave the milestone open, and report.

Partial-review output names the issues still open in the milestone so the operator sees the gap between what shipped and what the milestone promised.

## Things not to do

- **Don't create issues without explicit operator approval** at Step 7. Drafting is cheap; creating is committing to a public record.
- **Don't push tags without verifying CI green** on the default branch. A tag on top of red CI is a regression vector.
- **Don't write release notes before CHANGELOG is updated.** CHANGELOG is the source of truth; notes are extracts. Writing the extract first guarantees drift.
- **Don't bundle unrelated issues into one milestone** for convenience. See `milestone-rules.md` example 3.
- **Don't use English-only templates when the operator chose Korean / Japanese / Chinese** at Step 3. Body language is the operator's choice; section headings stay English for parsing stability.
- **Don't auto-close issues via commits that did not pass the owning skill's verification.** If `refactor-verify` did not verify the fix, the issue does not get a `Closes #N` footer — tag `needs-verify` and surface to the operator.
- **Don't add features the operator did not request.** This skill specifies the issue set the operator approved. It does not propose new items mid-cycle.
- **Don't rewrite published tags or release notes.** If a release shipped broken, cut a new patch (`vX.Y.Z+1`). Edit the broken release's notes only to add a *"Known issue — use vX.Y.Z+1"* banner; never delete.
- **Don't invent issue numbers.** Always consume `gh issue create` stdout for the actual number; never predict it.
- **Don't participate in `/vibesubin`'s parallel sweep.** Direct-call only. Documented above.

## 4-part output shape

Every response ends with the standard umbrella-compatible shape. Example stub:

```
## What I did
- Drafted 7 issues from the 2026-04-21 sweep report.
- Clustered into 2 milestones: v0.4.1 (5 bugs) and v0.5.0 (2 features).
- Created issues and milestones on GitHub — #41 through #47.

## What I found
- Two items had no evidence section in the sweep report; added `needs-evidence` label and paused on those.
- The v0.4.1 cluster already exceeds the 5-item patch cap by 1. Split recommended.

## What I verified
- All 7 issues created with correct milestone, labels, and body language (Korean).
- `gh issue list --milestone v0.4.1 --state open` returns 5 issues.
- `gh auth status` returned authenticated before any mutation.

## What you should do next
- Confirm the split for v0.4.1 (5 + 1) or accept the cap override.
- Run `/refactor-verify` or `/audit-security` on the branches as they come up per Step 9's routing table.
- Return for Step 10 (release) once all 5 issues in v0.4.1 are closed.
```

## Hand-offs

**Inputs** (who produces, how it arrives):

| Source | Arrival |
|---|---|
| `/vibesubin` sweep report | Operator pastes the report or points to a file path; consumed in Step 4(a). |
| `/codex-fix` findings | Operator pastes the review-driven output; consumed in Step 4(a). |
| Pasted PR review | Operator pastes inline; consumed in Step 4(a). |
| Sentry / gitleaks / Semgrep | Operator pastes or points to output; consumed in Step 4(a). |
| Operator-named scope | `"perf in src/api/"`; consumed in Step 4(c). |

**Outputs** (which skill ships which label):

| Label / type | Target skill |
|---|---|
| `bug`, `refactor`, `perf` | `/refactor-verify` |
| `security` | `/audit-security` |
| `docs` | `/write-for-ai` |
| `chore` + `ci` | `/setup-ci` |
| `chore` + `secrets` | `/manage-secrets-env` |
| `chore` + `deps` / branch / layout | `/project-conventions` |
| `chore` + `assets` | `/manage-assets` |
| `design`, `ui` | `/unify-design` |
| `chore` + `dead-code` | `/fight-repo-rot` → `/refactor-verify` |

## When not to use ship-cycle

- Single-issue single-commit change: call the owning skill (`/refactor-verify`, `/audit-security`, `/write-for-ai`, etc.) directly. `ship-cycle` is for multi-item release cycles, not one-offs.
- No intent to cut a version soon: if the operator just wants to log one item, `gh issue create` by hand is lighter than running this skill.
- Non-GitHub host: the host check exits gracefully; invoke the underlying skills directly.
- Operator is mid-refactor on a hot branch: finish the refactor with `refactor-verify`, come back to `ship-cycle` when the batch is ready.

## Integration with /vibesubin sweep

Umbrella produces findings; operator reads the sweep report; operator invokes `/ship-cycle` with *"turn these into issues"*. `ship-cycle` consumes the findings as Step 4(a) input, runs Steps 5–11, ends at a published release. The umbrella itself does not launch `ship-cycle` — `ship-cycle` is an explicit post-sweep handoff by the operator, same pattern as `codex-fix`.
