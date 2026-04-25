---
name: ship-cycle
description: Issue-driven development orchestrator. Turns improvement intent into a well-specified, bilingual issue set; clusters issues into milestones that map 1:1 to semver versions; enforces branch, commit, and PR conventions (GitHub Flow — `<type>/<issue-N>-<slug>`, Conventional Commits, mandatory PR template, rebase-first merge); generates changelog entries and release notes deterministically from closed issues; leaves a durable audit trail for the next AI session. Direct-call only — not part of the /vibesubin parallel sweep. Two tracks — **GitHub track** (default) on GitHub with authenticated `gh` CLI; **PRD track** on any other host, using local markdown files under `docs/release-cycle/vX.Y.Z/` as the durable audit trail. Operator picks at Step 1.5. Every external mutation follows preview → confirm → mutate; created resources carry idempotency markers so re-runs noop instead of duplicating.
mutates: [direct, external]
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

## Host check and track selection

ship-cycle runs in one of two tracks. Both follow the same 11-step methodology and the same conventions (see `references/pr-branch-conventions.md`); they differ only in where the audit trail lives.

- **GitHub track** (default) — GitHub repo with authenticated `gh` CLI. Issues, milestones, PRs, and releases live on GitHub. The `Closes #<N>` footer auto-closes issues at merge.
- **PRD track** — any other host (GitLab, Gitea, Forgejo, Bitbucket, self-hosted, plain git with no remote, or `gh` unauthenticated). Issues are markdown files under `docs/release-cycle/vX.Y.Z/issues/NNN-slug.md`; release artifacts live in the same directory. See `references/prd-track.md` for the full step-by-step mapping.

Detection at Step 1:

```bash
gh repo view --json name  >/dev/null 2>&1 && HAS_GH_REPO=1   || HAS_GH_REPO=0
gh auth status            >/dev/null 2>&1 && HAS_GH_AUTH=1   || HAS_GH_AUTH=0
```

If both are `1` → default to GitHub track. If either is `0` → default to PRD track. Step 1.5 surfaces the detection and lets the operator override.

## State assumptions — before acting

Before proceeding past Step 2, write an explicit `Assumptions` block to the session and ask the operator to confirm. A wrong assumption here silently corrupts every downstream step.

```
## Assumptions
- Track:                   <GitHub | PRD (local)>
- Repo state:              <clean | dirty (N staged, M unstaged) | detached HEAD>
- Default branch:          <main | master | dev>
- Current version:         <from manifests — path and value — or "pre-1.0 / no manifests, using latest tag">
- Work scope:              <pasted findings | sweep output at /tmp/... | user-named area "perf in src/api/">
- Issue language:          <Korean | English | Japanese | Chinese>
- Milestone target:        <new version to cut — vX.Y.Z | just-issues mode, no release this cycle>
- Branch convention:       <default: <type>/<issue-N>-<slug> per pr-branch-conventions.md — or detected existing convention (e.g., "feature/<topic>") if CONTRIBUTING.md / CLAUDE.md / last 20 branches show one>
- Merge strategy:          <squash (default) | rebase | merge — detected from repo settings + CONTRIBUTING.md>
```

Stop and ask when:

- Scope is ambiguous (*"clean up"* with no target).
- Language signal is missing — prompt returned by the operator has no dominant language and no direct answer to the language question.
- Working tree is dirty with a staged-plus-unstaged mix (unclear which changes the cycle is building on).
- Current version can't be determined (no manifests, no tags) — operator must state a starting version.

Never invent assumptions to keep moving. An invented default branch or an invented current version is worse than a blocked step.

## Mutation contract — preview, confirm, mutate

`ship-cycle` mutates external state (`gh issue create`, `gh api ... -X PATCH`, `gh release create`, `git tag -a`, `git push`). Every such call follows the same three-step contract:

1. **Preview** — print the exact command and the rendered `BODY` content. No execution yet.
2. **Confirm** — block on operator response. Accept `approve` / `proceed` / `yes` to advance; anything else (including silence) holds.
3. **Mutate** — execute the command, capture its output (issue number, release URL, tag SHA), record the captured value in the audit trail.

Created resources carry an idempotency marker so re-runs detect prior runs and noop instead of duplicating:

- Issue bodies and release notes contain `<!-- ship-cycle:vX.Y.Z -->` near the top.
- Branch names follow the deterministic shape `<type>/issue-<N>-<slug>` from `references/pr-branch-conventions.md` §1 — re-creating the same branch is a noop.
- Milestone titles are `vX.Y.Z` exactly; reusing a title fetches the existing milestone instead of creating a duplicate.

`dry-run` mode (operator says `dry-run` at Step 7 or sets it via Step 1.5 override) skips every Mutate step and prints the would-be commands. Useful for sanity-check before a real run.

**Rollback.** Every external mutation has an inverse:

| Mutation | Inverse |
|---|---|
| `gh issue create` | `gh issue close <N> --comment "rolled back — see <reason>"` |
| `gh api repos/.../milestones` (create) | `gh api repos/.../milestones/<N> -X PATCH -f state=closed` |
| `gh release create vX.Y.Z` | `gh release delete vX.Y.Z --yes` (only if not yet announced; otherwise cut a follow-up patch) |
| `git tag -a vX.Y.Z` + push | `git push --delete origin vX.Y.Z` then `git tag -d vX.Y.Z` (rare; usually cut a follow-up patch instead) |
| Branch + PR | `gh pr close <PR> --delete-branch` |

Never rewrite a published tag or release. If a release shipped with a mistake, cut a patch (`vX.Y.Z+1`) and edit the broken release's notes only to add a *"Known issue — use vX.Y.Z+1"* banner.

## Procedure — 11 steps

Run in order. Each step has a verification or a confirm-gate. Do not skip.

### Step 0.5 — Offer upstream review

If the operator's intake at Step 4 will already include a concrete findings list (pasted sweep report, `codex-fix` output, PR review, scanner output, explicit named scope with evidence), skip this step with a one-liner — *"Findings already provided, skipping upstream review offer."* — and move on.

Otherwise, before running the host check, offer three paths and block until the operator picks one:

- **(a)** Invoke `/vibesubin` for a parallel sweep and wait for its report; consume it as Step 4(a) input.
- **(b)** Invoke a targeted worker if the operator named a specific concern — `/audit-security` for a security focus, `/fight-repo-rot` for dead code or god files, `/refactor-verify` baseline snapshot for "is the repo green?". Consume the worker's output as Step 4(a) input.
- **(c)** Proceed with operator-pasted findings as-is — even rough notes are acceptable if the operator owns the scope.

Explicitly: `ship-cycle` does **not** run the review itself. It orchestrates around review output. If the operator picks (a) or (b), surface the exact invocation and wait; do not auto-invoke. If the operator picks (c) without evidence, Step 4's evidence-check will catch gaps and block.

### Step 1 — Host check

Run the two `gh` checks from the Host-check section above. On success, capture:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name)
```

On failure (not a GitHub repo, or `gh` unauthenticated), do NOT stop. Fall through to Step 1.5 — the PRD track is the fallback path, not an exit.

### Step 1.5 — Track selection

Surface the detected track and let the operator confirm or override:

```
## Track
Detected: <GitHub | PRD (local)>
Reason: <gh repo + gh auth both OK | gh repo missing | gh unauthenticated | non-GitHub remote: <URL>>

Proceed on this track? (yes / switch to <other>)
```

Default is the detected track. Accept the operator's override — an operator on a GitHub repo may still prefer the PRD track for a local-first audit trail, and vice versa. Wait for confirmation before Step 2.

On the **PRD track**, the rest of this SKILL.md applies with the step-by-step mapping at `references/prd-track.md` — read it alongside the main procedure. The conventions at `references/pr-branch-conventions.md` apply to both tracks.

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

**Mandatory acceptance-criteria fields for every issue** (enforced by the issue-body template at `references/issue-body-template.md`):

- A concrete **test plan** scoped to the issue's label. Bug → regression test that reproduces the failure and then passes. Feat → new test or fixture covering the added behavior. Refactor → before/after equivalence (AST-diff or grep-count assertion). Docs/chore → `validate_skills.py` + grep assertions that the doc changed as stated.
- A concrete **docs plan** naming every file that must update in the same PR: `CHANGELOG.md` section entry, README table row or section edit, `SKILL.md` edit, `CLAUDE.md` change-type matrix entry — whichever apply. Docs updates land in the SAME PR as the code fix, not in a follow-up.
- A **handoff-notes** block at the bottom listing (a) what the next AI session needs to know to pick up adjacent work, (b) already-done-at references so a future session does not duplicate this work.

If a candidate issue is missing any of these three fields after drafting, block Step 6 (cluster) and report the gap for operator input.

### Step 5.5 — Write PRD.md

Before clustering, aggregate the candidate-issue set into a single `PRD.md` at the repo root (default) or at `/tmp/<repo>-prd-vX.Y.Z.md` if the operator prefers a non-committed draft. The PRD provides the theme-level view that individual issues cannot — *why these N issues matter, what success looks like, what is deferred*.

Follow the template at `references/prd-template.md`. Sections produced:

- **Context** — the trigger (sweep, review, named scope), the state of the repo, the cycle window.
- **북극성 목표 / North-star goals** — 1–3 sentences naming the outcome the cycle exists to produce.
- **Themes** — each theme groups related issues under a shared objective (e.g., *"Fix auth regressions"*, *"Harden CI"*).
- **Success metrics** — observable signals that tell the operator the cycle succeeded (tests green, N issues closed, CHANGELOG entries dated, release tag live).
- **Issue cluster summary** — flat list of issue titles with labels and milestone target.
- **Deferred items** — candidate items explicitly pushed to a later cycle, with one-line reasons.

PRD is operator-facing — surface it for approval before Step 6 clustering runs. If the operator requests edits, revise and re-surface; do not proceed to Step 6 until the PRD is approved.

If the cycle is a 1-milestone patch with fewer than 5 issues, the PRD may be inlined in the Step 7 approval prompt instead of a file — operator's choice. Default to file for minor and major cycles; default to inline for patch cycles unless the operator asks otherwise.

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

For each created issue, derive the branch name per `references/pr-branch-conventions.md` §1 and hand off to the right worker. Default shape:

```bash
BRANCH="<type>/issue-<N>-<kebab-slug>"   # e.g., fix/issue-42-auth-session-refresh
```

`<type>` matches the issue's primary `type` label (`feat`, `fix`, `refactor`, `perf`, `docs`, `chore`, `security`, `test`, `ci`, `design`). If the repo has a detected existing convention per §1's detection rule (≥10 of last 20 branches matching, or explicit `CONTRIBUTING.md` / `CLAUDE.md` rule), defer to that convention and still embed the issue number.

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

Commit format: Conventional Commits + mandatory `Closes #<N>` footer per `references/pr-branch-conventions.md` §2. PR body: the six-section template (Context / What changed / Test plan / Docs plan / Risk / Handoff notes) per §3, with `Closes #<N>` as the first line. These are load-bearing for GitHub's auto-close, for Step 10's aggregation query, and for the Step 11 audit trail.

Rebase and conflict handling follow §5 — rebase-first workflow, `--force-with-lease` only (never plain `--force`), no force-push to `main` / `master` / `release/*`. Merge strategy per §4 (repo settings first, `CONTRIBUTING.md` second, `--squash` default).

When the worker reports done and the PR merges, GitHub auto-closes the issue (GitHub track) or ship-cycle updates the issue file's frontmatter (PRD track — see `references/prd-track.md`). If the worker cannot complete the item (baseline-red, missing context), leave the issue open and tag it `blocked` with a reason in a comment (or PRD-track frontmatter edit).

#### Step 9a — Parallel dispatch for independent issues

When multiple issues in a milestone have no cross-file overlap — derived from each issue body's *Implementation notes — scope files* list — dispatch them simultaneously as parallel Task-tool subagents. Sequential only when issues share files or one depends on another's output.

- **Default model**: `opus` (per the project's global CLAUDE.md rule *"All custom agents default to opus"*). Override per-agent with `model: sonnet` or `model: haiku` only when the operator explicitly asks for cost/speed.
- **Default effort**: max, unless the operator has specified otherwise.
- **Parallel ceiling**: the orchestrator can dispatch **10+ independent issue workers simultaneously** when the dependency graph is flat. Pattern to copy: the `/vibesubin` sweep launches 9 parallel specialists in one block — same shape here for issue execution.
- **Ownership per worker**: each parallel worker owns its branch, its commit, and its `gh pr create`. No cross-worker coordination until merge-time.
- If two issues touch the same file, serialize them and note the dependency in the second issue's body under *Depends on*.

#### Step 9b — CI green gate before merge

Per `references/pr-branch-conventions.md` §7: all checks must be SUCCESS or NEUTRAL — including optional ones. SKIPPED is yellow, not green; surface and confirm before merge. Flaky checks get one re-run; second failure blocks merge.

```bash
gh pr view <PR> --json statusCheckRollup \
  -q '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "NEUTRAL") | .name'
# expected: empty output. Any non-empty line blocks merge.
gh pr merge <PR> <strategy-flag> --delete-branch      # strategy-flag = --squash | --rebase | --merge per §4
```

PRD-track equivalent: run the project's documented test command (from `package.json` / `Cargo.toml` / `pyproject.toml` / `Makefile`); exit 0 = green. Do not merge without green on either track.

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

Verify `CHANGELOG.md` has the dated heading. Link the release back to the milestone in the release notes' footer.

When closing an issue (post-merge), copy its handoff-notes block from the issue body into the close comment. A fresh AI session grepping closed issues for context can then find the handoff notes without re-reading the PR diff — the comment becomes the durable reference.

Report done.

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

## Layperson mode — plain-language translation

When the task context contains `explain=layperson` (from `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"explain like I'm non-technical"*, *"非開発者でも分かるように"*, *"用通俗的话解释"*), add a plain-language layer to every finding this skill emits. Combines freely with `tone=harsh`. Full rules at `/plugins/vibesubin/skills/vibesubin/references/layperson-translation.md`.

### Three dimensions per finding

Every finding gets three questions answered in plain language, in the operator's language (Korean / English / Japanese / Chinese):

- **왜 이것을 해야 하나요? / Why should you do this?** — *"여러 수정을 '이거 다 고쳤으니 릴리즈' 한 마디로 묶으면 뭘 고쳤는지 한 달 뒤 본인도 모릅니다. 이슈 번호·PR·CHANGELOG·태그가 연결돼 있어야 다음 세션 AI가 맥락을 되찾아요."*
- **왜 중요한 작업인가요? / Why is it an important task?** — *"릴리즈 사이클은 한 번 잘못 엮으면 이슈 누락·CHANGELOG 누락·태그 오설정으로 이어지고, 나중에 특정 버전에서 뭐가 바뀐 건지 추적 불가해집니다. 배포 프로세스 자체가 디버깅 대상이 됨."*
- **그래서 무엇을 하나요? / So what gets done?** — *"intake → 이슈 draft → 밀스톤 클러스터 → 승인 → 생성 → 브랜치·PR → 병합 → CHANGELOG 집계 → 태그 → 릴리즈 노트 — 11단계를 하나씩 검증 게이트를 두고 돌립니다. GitHub이면 gh API로, 아니면 로컬 markdown 파일로 같은 방법론을 실행합니다."*

### Severity translation

- 🔴 blocker → *"지금 릴리즈 못 감 — 이슈가 열려 있거나 CI 빨간 상태"*
- 🟡 cleanup → *"릴리즈는 되는데 감사 흔적 빠짐"*
- 🟢 ready → *"태그 가능 — 모든 이슈 종료, CI green, CHANGELOG 기록"*

### Box format

Wrap each finding in the box format from the shared reference. Header uses urgency phrase and the finding number. Footer names the hand-off skill.

### What does NOT change

Findings, counts, file:line references, evidence, and severity are identical to balanced/harsh output. Only the wrapping and dimension annotations are added.

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
- No intent to cut a version soon: if the operator just wants to log one item, `gh issue create` by hand (GitHub track) or an inline note (PRD track) is lighter than running this skill.
- Operator is mid-refactor on a hot branch: finish the refactor with `refactor-verify`, come back to `ship-cycle` when the batch is ready.

## Integration with /vibesubin sweep

Umbrella produces findings; operator reads the sweep report; operator invokes `/ship-cycle` with *"turn these into issues"*. `ship-cycle` consumes the findings as Step 4(a) input, runs Steps 5–11, ends at a published release. The umbrella itself does not launch `ship-cycle` — `ship-cycle` is an explicit post-sweep handoff by the operator, same pattern as `codex-fix`.
