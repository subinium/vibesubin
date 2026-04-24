# vibesubin

A portable skill plugin that teaches your AI assistant to refactor, audit, and deploy your code the way I wish it would by default — and lets you run all of it at once with `/vibesubin`.

It's built for people who ship real things with AI but weren't trained as developers. These are the habits I use when I'm coding with an AI myself, packaged as skills so your assistant can follow them without you having to know every rule.

The same `SKILL.md` files work in **Claude Code**, **Codex CLI**, and **any agent supported by [skills.sh](https://skills.sh)** — Cursor, Copilot, Cline, and others. Write once; every host picks it up.

> [한국어](./README.ko.md) · [中文](./README.zh.md) · [日本語](./README.ja.md)

---

## Quick start

Install [Claude Code](https://code.claude.com), then run:

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

Open a repo. Type `/vibesubin`. Every skill fans out across your code in parallel, read-only, and comes back with a single prioritized report — nothing is modified until you approve items. When you want a skill to actually *do* the work, call it by name (`/refactor-verify`, `/setup-ci`, etc.) and it edits your files directly.

Using Codex CLI, Cursor, Copilot, or Cline? Jump to [Install](#install).

---

## What vibesubin is, and what it isn't

A small bundle of AI skills — `SKILL.md` files — that your agent picks up automatically whenever a request matches. You say what you want in plain words (*"split this file safely"*, *"is anything leaking?"*, *"set up deploy"*) and the right skill runs.

The rule every skill shares: **they don't say *done* until they can show you the evidence.** A refactor is finished because four independent checks confirm nothing was dropped, moved, or mis-wired — not because the AI rewrote the file. A security sweep is a triaged list with file:line, not a vibes-based paragraph.

Not a SaaS (nothing leaves your machine), not a compliance tool (no SOC 2 / HIPAA), not a code generator. It improves the repo you already have.

### Two ways to use it — sweep vs. direct call

- **Sweep mode** (`/vibesubin`). Every code-hygiene skill runs in parallel, *read-only*. You get one prioritized report; nothing changes until you approve items.
- **Direct call** (`/refactor-verify`, `/setup-ci`, ...). The skill does its full job, including editing files.
- **Process skills** (`/ship-cycle`) and **host-specific wrappers** (`/codex-fix`) are direct-call only — they're not in the sweep because they mutate external systems (GitHub, Codex) or manage release state.

Three skills (`fight-repo-rot`, `audit-security`, `manage-assets`) are diagnosis-only and never edit regardless of how you call them.

### The skills by area

**Code quality (5)**

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`refactor-verify`](#refactor-verify) | *"rename this class"*, *"split this file"*, *"delete this dead code safely"* | A planned refactor with four verification passes before it calls itself done |
| [`audit-security`](#audit-security) | *"any secrets leaked?"*, *"is this safe?"* | A short triaged list of real findings with file:line, not a 500-line PDF |
| [`fight-repo-rot`](#fight-repo-rot) | *"find dead code"*, *"what can I delete?"* | Dead code tagged HIGH / MEDIUM / LOW confidence, plus god files and hotspots. Diagnosis-only |
| [`manage-assets`](#manage-assets) | *"my repo is huge"*, *"should I use LFS?"* | Bloat report — large files, big blobs in git history, LFS candidates. Never rewrites history |
| [`unify-design`](#unify-design) | *"unify the buttons"*, *"extract these colors to tokens"* | Design-system audit — scaffolds tokens, finds hardcoded hex and magic px, consolidates duplicates |

**Docs & AI-friendliness (2)**

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`write-for-ai`](#write-for-ai) | *"write a README / commit / PR"* | Docs the *next* AI session can actually read — no unbacked marketing adjectives |
| [`project-conventions`](#project-conventions) | *"main or dev branch?"*, *"should I pin this dep?"* | One default per decision — GitHub Flow, pinned deps, domain-first layout |

**Infra & config (2)**

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`setup-ci`](#setup-ci) | *"set up deploy"*, *"push to deploy"* | Working GitHub Actions for test + deploy with a plain-language walkthrough |
| [`manage-secrets-env`](#manage-secrets-env) | *"where does this secret go?"*, *"is my `.env` leaking?"* | One opinionated answer per decision, plus the full secret lifecycle |

**Release process (1)**

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`ship-cycle`](#ship-cycle) | *"plan a release"*, *"이슈 드리븐"*, *"cut a release"* | Issue-driven release orchestrator — drafts bilingual issues, clusters into milestones = versions, hands each off to the right worker, aggregates CHANGELOG, cuts tag + release. **Two tracks** — GitHub (default) or PRD-on-disk for any other host |

**Host-specific wrappers (1)**

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`codex-fix`](#codex-fix) | *"codex 돌려서 고쳐줘"*, *"run codex and fix"* | Thin wrapper: `/codex:rescue` → `refactor-verify`'s review-driven fix mode. **Claude Code + Codex plugin only**; one-line fallback elsewhere |

New skills drop into `plugins/vibesubin/skills/` and are picked up by `/vibesubin` automatically.

---

## The `/vibesubin` command

One word runs every code-hygiene skill in parallel against your repo, merges findings into a prioritized report, and waits for approval before touching anything.

You can narrow scope before launch (*"only src/api"*, *"only security and repo rot"*). Specialists are read-only in sweep mode; they produce findings, not fixes. Criticals float to the top across categories; multi-specialist hits on the same file jump in priority. You get a vibe-check paragraph, stoplight line per specialist, top-ten fix list, recommended order, and a one-sentence verdict. Full synthesis rules in the [umbrella `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md).

**Sweep vs. single skill.** Sweep for open-ended questions (*"is this ready to ship?"*, *"second opinion"*). Call a skill directly when you already know what you want (*"refactor this file"* → `/refactor-verify`). Leaked secrets go straight to `/audit-security`'s incident path, skipping the sweep.

**Harsh mode.** Opt-in direct framing — `/vibesubin harsh`, *"brutal review"*, *"don't sugarcoat"*, *"매운 맛으로"*, *"厳しめで"*. Read-only still, same evidence, no hedging. Never defaults on.

**Layperson mode.** Opt-in plain-language translation — `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"non-technical"*, *"用通俗的话解释"*. Every finding gets a 3-dimension block (*왜 해야 / 왜 중요 / 무엇을 할지*) in a box format, with severity translated to urgency (CRITICAL → *"지금 당장"*). Stacks with harsh mode. See [`references/layperson-translation.md`](./plugins/vibesubin/skills/vibesubin/references/layperson-translation.md).

**Skill conflicts.** When two specialists disagree on the same file (e.g., *refactor-verify* says "pause" and *unify-design* says "consolidate"), the report surfaces a `⚠ Skill conflict` block with gap, reason, and each side's basis — operator picks. Catalog in [`references/skill-conflicts.md`](./plugins/vibesubin/skills/vibesubin/references/skill-conflicts.md).

---

## Install

| Path | Agent | Best when |
|---|---|---|
| **A. Claude Code marketplace** | Claude Code | Simplest, auto-updates |
| **B. `skills.sh`** | Cursor, Copilot, Cline, Codex CLI, Claude Code | Cross-agent |
| **C. Manual symlinks** | Claude Code and/or Codex CLI | Hacking on the plugin |

**A — Claude Code marketplace** (recommended)

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

Update with `/plugin marketplace update`. Uninstall via `/plugin uninstall vibesubin`.

**B — skills.sh** (cross-agent, powered by [skills.sh](https://skills.sh))

```bash
npx skills add subinium/vibesubin
```

Re-run the command to update. Remove with `npx skills remove vibesubin`. Supported hosts are listed in `npx skills --help`.

**C — Manual symlinks** (editable, offline, `git pull` pushes changes live)

```bash
git clone https://github.com/subinium/vibesubin.git
cd vibesubin
bash install.sh                  # Claude Code (default)
bash install.sh --to codex       # Codex CLI
bash install.sh --to all         # both
bash install.sh --dry-run        # preview
```

`git pull` to update. Uninstall with `bash uninstall.sh [--to codex|all]` — only symlinks the script created get removed.

Install problems? Close every agent session and start a fresh one (skills cache per session). Anything else, [open an issue](https://github.com/subinium/vibesubin/issues).

---

## The skills

Each skill lives at [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/). The writeups below are the user-facing version; full methodology is in each skill's `SKILL.md`, with deep references in a sibling `references/` folder.

### Code quality

#### `refactor-verify`

The skill I'd defend the hardest. The single biggest failure mode when AI touches code is the silent one — a rename worked, tests passed, and three weeks later somebody hits a code path still pointing at the old name and the whole thing crashes. `refactor-verify` exists to make that impossible.

Covers structural refactors (move, rename, split, merge, extract, inline) and safe deletions (removing code `fight-repo-rot` confirmed dead). Both use the same four-check proof: symbol set preservation, byte-equivalence of moved code, re-run of typecheck/lint/tests/smoke, and caller-audit across the import graph. If any of the four fails, the skill doesn't advance. It will not touch files you didn't ask about, say *done* with any check failing, or delete LOW-confidence dead code without review.

#### `audit-security`

Enterprise scanners flag 500 things, 490 of which are false alarms. `audit-security` is the opposite: a short, hand-curated list of patterns that catch real mistakes, every hit triaged as real / false-alarm / needs-review with a one-line reason.

Checks for the obvious (secrets in commits, SQL concatenation, `eval`/`exec`/`pickle.loads`), the less obvious (user-controlled file paths, unescaped HTML, cookies without `httpOnly`/`Secure`, wildcard CORS), and the forgotten (`.env` in git history, `.pem`, SSH keys). Severities are in plain terms — *"a stranger can read every user's data"* beats *"CWE-89"*. Not a penetration test; static only, no network.

#### `fight-repo-rot`

Dead-code detector first, clutter spotter second, pure diagnosis always. Finds functions nothing calls, files nothing imports, orphaned modules, dependencies in the manifest that are never imported. Also flags god files, hotspots (high churn × high complexity), hardcoded absolute paths, literal IPs, stale `TODO`/`FIXME` older than six months.

Every dead-code candidate carries a confidence tag: **HIGH** (no references anywhere — safe to hand off to `refactor-verify`), **MEDIUM** (referenced only from tests or via dynamic dispatch — operator confirms), **LOW** (exported symbol, generated code, reflection/DI — human review required). Never edits, never deletes. Hands off to `refactor-verify` for deletions, `project-conventions` for hardcoded-path fixes, `audit-security` for CVE-class dep rot.

#### `manage-assets`

Bloat detector, not a code analyzer. Surfaces binary weight: file sizes in the working tree, git-history blob sizes (the invisible ones), LFS migration candidates, asset-directory growth, duplicate binaries. **Diagnosis-only** — never deletes, never rewrites history, never runs `git filter-repo` or `git lfs migrate`. Approved removals hand off to `refactor-verify` (for verified history rewrites), `manage-secrets-env` (if `.gitignore`-shaped), or `fight-repo-rot` (if also unreferenced).

#### `unify-design`

Design-system consistency for frontends — tokens + duplicates audit. Treats brand identity (colors, spacing, typography, radii, shadows, breakpoints, core components) as the single source of truth and rewrites drift back to tokens. Detects the framework (Tailwind v3/v4, CSS Modules, styled-components, Emotion, MUI, Chakra, vanilla CSS) and uses the project's own idioms, never a foreign pattern.

Three moves: scaffolds tokens if missing (asks operator for primary color + display font), audits drift (hardcoded hex, arbitrary Tailwind values like `w-[432px]`, inline style objects, duplicate Button/Card/Nav), fixes drift (small replacements direct; multi-file consolidation hands off to `refactor-verify`). Won't invent a brand and won't rewrite across frameworks.

### Docs & AI-friendliness

#### `write-for-ai`

Docs written for the *next* AI session as well as humans. Reads the repo cold the way a fresh AI session would, extracts invariants (not just what the project does, but the rules it follows), fills the relevant template (README, commit, PR description, architecture doc, `CLAUDE.md`, `AGENTS.md`), and verifies every claim before writing it — if the README says `pnpm test` runs the suite, the skill runs `pnpm test` first.

Prevents the classic failure mode: AI rewrites the README and does a good job, except a paragraph about environment variables silently disappears. You don't notice. The next session starts from the new README and has no idea your env layout exists.

#### `project-conventions`

Lower-stakes structural defaults: branch strategy, dep pinning, directory layout, absolute-path hygiene. Defaults — GitHub Flow (`main` + short-lived feature branches, no `dev`), exact-pinned prod deps with a committed lockfile, Dependabot/Renovate monthly, domain-first layout, no absolute paths in source. Every rule has a one-sentence reason.

On a new project it scaffolds `dependabot.yml` and a branch-strategy note. On existing ones it audits deviations and hands off multi-file fixes to `refactor-verify`.

### Infra & config

#### `setup-ci`

CI is the biggest productivity unlock in the pack — once it's set up, deploy stops being a thing you think about and becomes `git push`. Starts by explaining the concepts in plain language (runners, Secrets, `concurrency` groups, post-deploy health checks), detects your stack from `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod`, and scaffolds two workflows: `test.yml` (tests + lint with timeouts) and `deploy.yml` (per-host pattern — SSH, Vercel, Fly.io, Cloud Run, Netlify — with concurrency guards, SSH key cleanup, health check).

Won't handle Secrets for you (they live in the GitHub UI) and won't guess your host.

#### `manage-secrets-env`

The high-stakes slice of "where does this value go" — a misplaced credential is an incident, not a style preference. Four-bucket decision tree (source constant / env var / local `.env` / CI secret store), `.env.example` ↔ `.env` drift check, default-safe `.gitignore` template, full lifecycle (add / update / rotate / remove / migrate / audit / provision).

Defaults: runtime-invariant constants in code; local secrets in `.env` with committed `.env.example`; production secrets in CI secret store; environment-variable runtime config; `.gitignore` ships with every secret-shape pattern pre-filled. On an existing project it audits and flags tracked-secret files as incident-class findings — handing off to `audit-security` when something already leaked.

### Release process

#### `ship-cycle`

The pack's only **process-category** skill. Acts on the lifecycle around the code — issues, milestones, versions, tags, releases, changelog. Runs the loop: intake → draft → cluster → confirm → create → branch → execute → release. Bilingual issue bodies (Korean / English / Japanese / Chinese), semver decision tree (bug/perf/refactor → patch; additive feat → minor; breaking → major), cap of ~5 items per patch.

**Two tracks**. **GitHub track** (default) uses `gh` API — issues, milestones, PRs, releases live on GitHub; `Closes #<N>` footer auto-closes on merge. **PRD track** (any other host) uses local markdown files under `docs/release-cycle/vX.Y.Z/` — same methodology, same conventions, different durable audit trail. Operator picks at Step 1.5. **Conventions are enforced** per [`references/pr-branch-conventions.md`](./plugins/vibesubin/skills/ship-cycle/references/pr-branch-conventions.md): GitHub Flow branches (`<type>/<issue-N>-<slug>`), Conventional Commits + mandatory `Closes #<N>` footer, PR template with six required sections (Context / What changed / Test plan / Docs plan / Risk / Handoff notes), rebase-first merge with `--force-with-lease`, no force-push to `main` / `master` / `release/*`.

Won't skip operator approval on the draft issue set, won't push a tag without CI green on main, won't mix unrelated items into one milestone.

### Host-specific wrappers

#### `codex-fix`

Thin wrapper (~100 lines) for one specific workflow: *"I've finished a batch of edits. Run Codex for a second-model review. Let Claude resolve with verification."* Invokes `/codex:rescue` on the current branch diff, hands findings to `refactor-verify`'s review-driven fix mode.

**Claude Code + Codex plugin only.** On any other host it prints *"Codex plugin not detected — invoke `/refactor-verify` directly with findings instead."* and exits cleanly.

Use `/codex-fix` when on Claude Code + Codex *and* the review source is Codex. Use `/refactor-verify` directly for any other source (human PR review, Sentry, `gitleaks`, Semgrep, pasted notes) — same engine, different input path. Covered by the portable-engine-plus-thin-wrapper pattern in [`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md) rule 9.

---

## Using it day to day

Three ways to invoke it, in order of how much you already know.

Don't know where to start? Type `/vibesubin` and it runs everything. Know what's bothering you? Say it in plain words — *"clean this up and don't break anything"* fires `refactor-verify`, *"any secrets leaked?"* fires `audit-security`, *"what should I fix first?"* fires `fight-repo-rot`, and so on. Know exactly which skill you want? Call it by name: `/refactor-verify`, `/audit-security`, etc.

Every skill follows the same four-part output shape: what it did, what it found, what it verified, and what you should do next. If a skill gives you a wall of prose without those four parts, that's a bug — [open an issue](https://github.com/subinium/vibesubin/issues).

### Workflows that come up often

- **Cleaning up a repo.** `fight-repo-rot` finds the worst offender → `refactor-verify` fixes it with verification → `write-for-ai` writes the commit and PR.
- **Preparing a release.** `audit-security` for secrets → `refactor-verify` on anything critical → `setup-ci` to catch regressions next time.
- **Onboarding to a new repo.** `/vibesubin` for the full sweep → `write-for-ai` fills in the missing `CLAUDE.md` → `manage-secrets-env` audits `.gitignore` and secrets → `project-conventions` audits branches, deps, layout.
- **Starting from scratch.** `manage-secrets-env` scaffolds `.env.example` and `.gitignore` → `project-conventions` scaffolds Dependabot and a branch note → `setup-ci` lays down workflows → `write-for-ai` writes README and `CLAUDE.md`.
- **"Why is my repo so big?"** `manage-assets` runs the bloat report → `refactor-verify` executes any history rewrite or LFS migration with verification.
- **"Why do my pages all look slightly different?"** `unify-design` scaffolds the tokens file (if missing), audits the drift, and rewrites components back to tokens → `refactor-verify` handles the multi-file consolidation.
- **"End-of-edit Codex loop" (Claude Code + Codex plugin only).** Finish a batch of edits → `codex-fix` invokes `/codex:rescue` on the branch diff → hand-off to `refactor-verify`'s review-driven fix mode → triaged, verified, committed with back-references. On any other host or from any other review source (PR review, Sentry, scanner, pasted notes), invoke `/refactor-verify` directly with the findings — same engine, different input path.
- **Planning a release (Claude Code + GitHub + `gh` only).** A batch of improvements lands, or a `/vibesubin` sweep produces a prioritized fix list → `ship-cycle` drafts bilingual issues from the list → clusters them into a milestone matching the next semver version → hands each issue off to the right worker for verified execution → on milestone close, aggregates closed issues into a functional-style changelog entry, bumps both manifests, cuts an annotated tag, and creates the GitHub release. On any non-GitHub host or without `gh` authenticated, `ship-cycle` emits a one-line fallback and exits; invoke the underlying workers directly in that case.

You don't plan these yourself; the skills suggest the next hand-off when it makes sense.

---

## Adding your own skill

A new skill is a self-contained directory under `plugins/vibesubin/skills/<skill-name>/`. Drop it in, restart your agent, and both `/vibesubin` and the autocomplete menu pick it up.

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # required, under 500 lines, with YAML frontmatter
├── references/           # optional deep-dive docs
├── scripts/              # optional executable helpers
└── templates/            # optional files the skill copies into projects
```

Rules new skills inherit: *done* means verified (not claimed), `SKILL.md` stays under 500 lines with depth in `references/`, output follows the four-part shape, any sweep-eligible skill needs a read-only mode, and every skill is explicit about where its confidence ends.

Want a skill included in the main plugin? [Open an issue](https://github.com/subinium/vibesubin/issues) with the trigger phrases, what it'd do, and a concrete example. See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## Philosophy

A handful of rules every skill is built around. You don't need to memorize them — they exist so current and future skills stay consistent.

**Your AI is a well-meaning junior developer.** Juniors work hard, and juniors sometimes forge ahead when they should have stopped to ask. The plugin inserts *"stop and ask"* moments where a more careful hand would.

**Done is proven, not claimed.** If a task says complete, there's an execution result behind it — a passing test, a matched hash, a live `200 OK`. Assertion without evidence is a bug.

**Docs are for the next AI session, not just for people.** The current conversation evaporates when the session ends; READMEs, commits, and PR bodies are written so a fresh session can rebuild the context.

**Existing conventions are the default.** The plugin doesn't silently rewrite your branch strategy, file layout, or config on a whim.

The plugin is [actively maintained](./MAINTENANCE.md). Refactoring tools evolve, skill systems change, and LLM failure modes shift — each skill is reviewed on a schedule.

---

## Contributing

Open source, but PRs aren't currently accepted. Found a bug, want a new language or runtime covered, spotted unclear docs, have a new skill idea? [Open an issue](https://github.com/subinium/vibesubin/issues). The maintainer reviews and incorporates directly, which keeps the voice consistent. Details in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](./LICENSE).

---

Changes over time are tracked in [`CHANGELOG.md`](./CHANGELOG.md). Plugin version lives in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json).
