# PR, Branch, Commit, and Merge Conventions

GitHub Flow-based conventions that ship-cycle enforces on both the GitHub track and the PRD track (see `prd-track.md`). The conventions are load-bearing for two downstream steps — the aggregator in Step 10 reads commit prefixes and `Closes #<N>` footers to build the CHANGELOG, and the audit trail in Step 11 reads the PR-body structure to find handoff notes. Deviations break the pipeline; that's why the rules are explicit, not "suggested".

## 1. Branch naming — single convention

Every branch opened by a ship-cycle worker follows exactly this shape:

```
<type>/<issue-N>-<kebab-slug>
```

- **`<type>`** — matches the primary `type` label on the issue. One of: `feat`, `fix`, `refactor`, `perf`, `docs`, `chore`, `security`, `test`, `ci`, `design`.
- **`<issue-N>`** — the issue number from `gh issue create` stdout (GitHub track) or the file prefix `NNN` from `docs/release-cycle/vX.Y.Z/issues/NNN-slug.md` (PRD track). Three digits on PRD track (`001`), variable width on GitHub track (`42`, `137`).
- **`<kebab-slug>`** — the issue title reduced to lowercase kebab-case, 3-6 words, stripped of punctuation and stopwords. Keep it mnemonic — a reviewer should guess the topic from the branch name alone.

Worked examples:

| Issue title | Label | Branch |
|---|---|---|
| "Fix auth regression in session refresh" | `fix` | `fix/issue-42-auth-session-refresh` |
| "Add dark mode toggle to settings page" | `feat` | `feat/issue-51-dark-mode-toggle` |
| "Refactor user API to split controller and service" | `refactor` | `refactor/issue-63-split-user-controller` |
| "Rotate exposed API keys" | `security` | `security/issue-44-rotate-api-keys` |
| "Unify button primitives into one component" | `design` | `design/issue-58-unify-button-primitive` |

Previous fallback (`issue-<N>-<slug>`, no type prefix) is deprecated. If a project already uses a different convention detected by `project-conventions`, ship-cycle defers to that convention — but still embeds the issue number, and emits one line at Step 9: *"Deferring to existing branch convention `<detected>`. Issue number `<N>` embedded; type prefix omitted."*

### What counts as a detected existing convention

`project-conventions` (or ship-cycle directly) confirms an existing convention exists when AT LEAST ONE of:

- `CONTRIBUTING.md` explicitly documents a pattern (e.g., *"branches are named `feature/<jira-id>`"*).
- The repo's root `CLAUDE.md` / `AGENTS.md` documents a pattern.
- `git for-each-ref refs/heads/` shows **≥ 10 of the last 20 branches** matching a single non-default pattern with high structural confidence (≥ 80% match).

If zero signals match, no convention is "detected"; the default (`<type>/<issue-N>-<slug>`) applies. Never guess — guessing leads to silent inconsistency across contributors.

## 2. Commit message convention — Conventional Commits + `Closes #<N>`

Every commit a ship-cycle worker makes follows Conventional Commits plus a mandatory issue-close footer:

```
<type>(<scope>): <subject>

<body — explains WHY, not WHAT; ≤ 5 lines preferred>

Closes #<N>
```

Rules:

- **`<type>`** matches the branch type prefix exactly. Mismatch blocks the commit at Step 9 — the worker runs `grep -E '^<type>/' <branch-name>` and aborts if the pattern does not hold. This catches the case where a worker drifted off-plan.
- **`<scope>`** is the area of change (domain, module, file family). Keep it short — one word preferred. For the vibesubin pack itself, examples: `skill`, `umbrella`, `ship-cycle`, `refactor-verify`, `readme`, `ci`, `docs`. For generic projects: `auth`, `api`, `ui`, `db`, `config`, `middleware`. Omit the parens when no sensible scope exists: `chore: bump lockfile` is valid.
- **`<subject>`** — imperative mood, lowercase, no trailing period, ≤ 72 chars. *"add dark mode toggle"* — not *"added dark mode toggle"* or *"Adds dark mode toggle."*.
- **`<body>`** — optional, but if present it explains the **why**. The diff shows what changed; the body answers what the diff can't show: the trigger, the constraint, the trade-off. If you're narrating the diff, delete the body.
- **`Closes #<N>`** footer — load-bearing. On GitHub it auto-closes the issue on merge. On PRD track it signals "this commit resolves issue NNN" for the aggregator. Always the last line, always by itself. Multiple issues: `Closes #42, #43` on one line.
- **Breaking change** — add `!` after type/scope: `feat(api)!: change response shape for /users endpoint`. A `BREAKING CHANGE:` block in the body is also required.

Forbidden:

- *"fix stuff"*, *"wip"*, *"update"*, *"misc"* — vague subjects that say nothing.
- Trailing periods in the subject line.
- Mixed-language subjects (pick one language per commit — match the repo's default).
- *"addressed review comments"* — squash those into the commit they belong to.
- Skipping the `Closes #<N>` footer on issue-linked work. The aggregator cannot recover it from elsewhere.

One logical change per commit. If the subject contains "and", split into two commits.

## 3. PR / MR template — required sections

Every PR (or MR on GitLab / Gitea) a ship-cycle worker opens MUST populate this body:

```markdown
Closes #<N>

## Context
<One paragraph — why this change exists, what triggered it, what constraint shaped it.>

## What changed
- <Bullet per user-visible change. Skip implementation trivia.>
- <…>

## Test plan
- [ ] <Specific test scoped by issue label — see issue body's "Test plan" section.>
- [ ] <…>

## Docs plan
- [ ] CHANGELOG.md entry under [Unreleased]
- [ ] <Other docs per issue's "Docs plan" — README row, SKILL.md edit, etc.>

## Risk
<Short: what's the blast radius if this ships wrong? What reverts look like?>

## Handoff notes
- **For the next AI session:** <what they need to know to continue adjacent work>
- **Already done at:** <file:line pointers that future sessions should not re-audit>
```

Rules:

- The first line is `Closes #<N>`. This is not the title — it's the first line of the **body**. GitHub parses this for auto-close linking; PRD track uses it for aggregation.
- All six sections (Context / What changed / Test plan / Docs plan / Risk / Handoff notes) are mandatory. A PR opened without them is not mergeable — the reviewer (human or AI) rejects at first pass.
- **Test plan** items are checkboxes that the reviewer or the author ticks as they run each test. A green CI signal does not auto-tick them — the reviewer confirms.
- **Docs plan** enforces the "docs land in the same PR as the code fix" rule. Separate docs PRs drift; same-PR docs stay in sync.
- **Risk** — one to three sentences, honest. If you don't know the risk, say so and flag for an upgrade review. Skipping this section is a sign the worker did not think about deployment.
- **Handoff notes** — a shortened copy of the issue's handoff-notes block (see `issue-body-template.md`). This is the durable record for the next AI session. Do not omit — the release audit trail at Step 11 copies this into the close comment.

## 4. Merge strategy — per-repo default, configurable

ship-cycle respects repo settings first, then falls back to a deterministic default.

**Detection order**:

1. **GitHub repo setting** — `gh api repos/:owner/:repo --jq '.allow_squash_merge, .allow_merge_commit, .allow_rebase_merge'`. Use the single enabled strategy when exactly one is on. When multiple are on, consult `CONTRIBUTING.md` for a stated preference.
2. **`CONTRIBUTING.md` / root `CLAUDE.md`** — literal strings: `"squash merge"`, `"rebase merge"`, `"merge commit"` each match their strategy. Exact phrasing is searchable and unambiguous.
3. **Default** — `--squash` with `--delete-branch`. Rationale: squash collapses work-in-progress commits into one clean `<type>(<scope>): <subject>` commit in main's history; for a worker that produces 3-8 commits per issue, squash keeps main readable. If the repo values commit-per-step history over compactness, the operator should set repo settings or `CONTRIBUTING.md` to `"rebase merge"` to override.

**Worked examples**:

| Repo signal | Strategy ship-cycle uses |
|---|---|
| GitHub squash-only | `gh pr merge <PR> --squash --delete-branch` |
| GitHub rebase-only | `gh pr merge <PR> --rebase --delete-branch` |
| GitHub all three enabled, `CONTRIBUTING.md` says "squash merge" | `--squash --delete-branch` |
| GitHub all three enabled, `CONTRIBUTING.md` silent | `--squash --delete-branch` (default) |
| PRD track, plain git | `git merge --no-ff <branch>` (merge commit preserves context without a remote PR) |

Never use the default without emitting the detection log:

> *"Merge strategy: squash (default — no repo setting or CONTRIBUTING.md preference detected). To change, set `CONTRIBUTING.md` to `"rebase merge"` or configure repo settings."*

## 5. Rebase-first workflow — how conflicts are resolved

ship-cycle uses a **rebase-first** workflow for keeping feature branches current with `main`. Merge commits from `main` into a feature branch are banned — they pollute the squash target and scramble the diff view.

### When to rebase

- Before opening a PR, if `main` has moved since the branch was cut.
- Before merging, if required status checks report the branch is behind and branch protection requires linear history.
- On demand, when conflicts need resolving (a conflict surfaced via `gh pr view` status or by the CI green gate).

### Rebase procedure — the exact commands

```bash
# 1. Update main locally
git fetch origin
git checkout main
git pull --ff-only

# 2. Switch back to the feature branch
git checkout <type>/<issue-N>-<slug>

# 3. Rebase onto updated main
git rebase main

# 4. If conflicts surface — resolve each, then continue
git status                                              # shows conflicted files
# (edit conflicted files, remove <<<<<<< ======= >>>>>>> markers)
git add <resolved-file>...
git rebase --continue

# 5. If mid-rebase and something is clearly wrong — abort cleanly
git rebase --abort                                      # safe, reversible

# 6. After a clean rebase — force-push the feature branch (lease-protected)
git push --force-with-lease origin <type>/<issue-N>-<slug>
```

**`--force-with-lease` is mandatory**. Never `--force` on a feature branch — `--force-with-lease` refuses to overwrite if someone else pushed to the branch between your last fetch and your push. This is the safety net that prevents the classic "I just overwrote my reviewer's commit" mistake.

### Conflict resolution playbook

1. **Read the conflict** — open each conflicted file; understand what `main` intended and what your branch intended.
2. **If the conflict is a trivial text overlap** (both sides added imports, both sides added a section heading) — keep both, reorder if needed.
3. **If the conflict is a semantic overlap** (both sides changed the same function) — ask: which change is load-bearing for which issue? Prefer the change that is closer to the merge target (usually `main`'s version, with your branch's addition layered on).
4. **If the conflict involves deleted-in-main + modified-on-branch** — check whether `main` deleted because the feature was removed. If yes, your branch is obsolete — close the PR and re-draft the issue. If no, the deletion was accidental; flag on the PR.
5. **Never "just accept theirs" or "just accept ours" blindly.** Every conflict is a decision the rebase is forcing you to make explicit.
6. **After resolving, re-run the four verification steps** (tests, lint, typecheck, smoke). Rebase conflicts are a re-entry into verification — you cannot assume the original CI pass still holds.

## 6. Force-push policy

Three rules:

1. **Never `--force` or `--force-with-lease` to `main`, `master`, `dev`, `release/*`, or any branch protected by the host.** ship-cycle refuses these commands. If somehow an operator calls a worker with `--force` targeting main, the worker emits a hard-stop: *"Refusing to force-push to main. This is a load-bearing invariant — if you need to rewrite main's history, do it manually with explicit confirmation."*
2. **`--force-with-lease` is the ONLY allowed force-push** for feature branches after a rebase. Plain `--force` is banned — it silently overwrites upstream changes; `--force-with-lease` refuses.
3. **Never rewrite history on a branch under review.** If a reviewer has posted comments anchored to commits, rewriting invalidates their comments. If the branch needs a rebase mid-review, post a note on the PR first: *"Rebasing on main — comments may re-anchor. Flag anything that moved."*

## 7. CI green gate — what counts as green

Before `gh pr merge` (or the PRD-track equivalent), the worker runs:

```bash
# GitHub track
gh pr view <PR> --json statusCheckRollup \
  -q '.statusCheckRollup[] | select(.conclusion != "SUCCESS" and .conclusion != "NEUTRAL") | .name'
```

The expected output is empty. Any non-SUCCESS, non-NEUTRAL check blocks merge.

**Stricter than the default `gh pr merge` behavior**: the built-in merge requires only the branch-protection required checks to pass. ship-cycle's gate requires **all checks** — including optional ones. Rationale: optional checks exist because they provide real signal; treating them as decorative means they rot.

**Skipped checks are NOT green**. A check with `conclusion: "SKIPPED"` gets flagged as yellow. The worker pauses and surfaces: *"Check `<name>` was skipped. Was this intentional (e.g., path filter excluded this PR) or a configuration error?"* Operator confirms before merge proceeds.

**Flaky checks** — if a check fails, the worker re-runs it once (`gh workflow run <workflow>` on the PR's head SHA). If it passes on re-run, merge proceeds with a note in the handoff-notes: *"Check `<name>` flaky — passed on re-run, flag for investigation."* If it fails a second time, merge blocks.

PRD-track equivalent — the worker runs the project's documented test command (detected from `package.json` / `Cargo.toml` / `pyproject.toml` / `Makefile`); exit 0 = green, non-zero = blocked.

## 8. Protected-branch invariants

ship-cycle enforces these even when the host does not:

- **`main` / `master` / `release/*` never receives direct pushes from a worker.** All changes land via PR. Workers that somehow find themselves on `main` abort with *"I'm on main — feature branches only. Switch to `<type>/<issue-N>-<slug>` first."*
- **No destructive ops on protected branches** — no `git reset --hard`, no `git push --force*` (see force-push policy), no `git branch -D` on a remote-tracked protected branch.
- **Tags are push-only, never rewritten** — see `release-pipeline.md`'s "Do not move an existing tag" rule.

## 9. What ship-cycle does NOT enforce

- **PR size limits** — there is no "max lines changed" cap. A 500-line PR is fine if it's one logical change; an 80-line PR is bad if it bundles three unrelated fixes.
- **Review approval count** — host setting; ship-cycle waits for whatever the host requires, does not add its own gate.
- **Branch age** — ship-cycle does not stale-out old branches. `fight-repo-rot` surfaces them separately.
- **Commit count per PR** — no cap. Squash collapses them anyway; pre-squash commit count is a working-style preference.
- **Reviewer assignment** — host / `CODEOWNERS` concern.

## 10. Worked examples — two full cycles end to end

### Example A — a bug fix on GitHub track

1. Issue #42 exists, labeled `bug`, in milestone `v0.6.1`.
2. Worker branches: `git checkout -b fix/issue-42-auth-session-refresh`.
3. Worker makes 3 commits:
   ```
   fix(auth): clear stale session cookie on refresh
   
   Session refresh was re-using the old cookie's expiry,
   which caused a race where a user's session appeared active
   for 15 seconds after they logged out.
   
   Closes #42
   ```
   ```
   test(auth): regression test for post-logout session staleness
   
   Closes #42
   ```
   ```
   docs(changelog): record session-refresh fix
   
   Closes #42
   ```
4. Worker rebases if `main` moved: `git fetch origin && git rebase origin/main && git push --force-with-lease origin fix/issue-42-auth-session-refresh`.
5. Worker opens PR with the mandatory template. Body first line: `Closes #42`.
6. CI goes green on all required + optional checks.
7. Worker runs the green-gate check; exits 0.
8. `gh pr merge <PR> --squash --delete-branch`. GitHub auto-closes #42.
9. Release pipeline (Step 10) aggregates the closed issue into the CHANGELOG under `[0.6.1]` Fixed.

### Example B — a feature on PRD track (no GitHub)

1. Issue file exists at `docs/release-cycle/v0.6.0/issues/051-dark-mode-toggle.md`, labels `[feat, ui]`.
2. Worker branches: `git checkout -b feat/issue-051-dark-mode-toggle`.
3. Worker makes 2 commits:
   ```
   feat(ui): add dark-mode toggle to settings
   
   Closes #051
   ```
   ```
   docs(changelog): record dark-mode toggle
   
   Closes #051
   ```
4. No remote PR — ship-cycle runs the project's test command, verifies green, then `git checkout main && git merge --no-ff feat/issue-051-dark-mode-toggle`.
5. Worker opens the issue file and updates frontmatter:
   ```yaml
   status: closed
   closed: 2026-04-24
   pr: N/A — local merge (commit abc1234)
   ```
6. Worker appends to the issue file's Resolution log section with the commit SHA and checklist status.
7. Release pipeline aggregates the closed issue file into `CHANGELOG.md` under `[0.6.0]` Added.

## 11. Integration with other skills

- **`project-conventions`** — owns the detection step for existing repo conventions. If an operator wants to *change* the branch convention, they call `/project-conventions` directly; ship-cycle never overwrites the detected convention.
- **`write-for-ai`** — owns the prose inside PR bodies and release notes. ship-cycle enforces *which sections exist*; `write-for-ai` enforces *how the prose reads*.
- **`refactor-verify`** — handles the actual code work for bug / refactor / perf issues. ship-cycle hands off; refactor-verify executes with the 4-check pass.
- **`audit-security`** — handles `security`-labeled issues. The conventions above apply; the only difference is the branch type prefix is `security/` and the issue frontmatter includes `priority: critical` by default.

## 12. What changes when `explain=layperson` is active

When the operator invoked ship-cycle with layperson mode, the **PR body template** is supplemented — not replaced — with a "쉽게 설명해서 / In plain words" line under `## Context`, and the `## Risk` section gets a plain-language consequence sketch. The six sections and their order are unchanged; only the text inside is friendlier.

Everything else on this page stays identical — conventions, not prose style, are the load-bearing contract.
