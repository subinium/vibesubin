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

A small bundle of AI skills — `SKILL.md` files — that your agent picks up automatically whenever a request matches. You don't memorize trigger phrases. You just say what you want in plain words — *"split this file safely"*, *"is anything leaking?"*, *"set up deploy"* — and the right skill runs.

The rule every skill shares: **they don't say *done* until they can show you the evidence.** A refactor isn't finished because the AI rewrote the file; it's finished because four independent checks confirm nothing was dropped, moved, or mis-wired. A security sweep isn't a vibes-based paragraph; it's a triaged list where each hit is either real, a false alarm, or flagged for human review, with a file and a line number.

What it is **not**: not a SaaS (nothing leaves your machine), not a compliance tool (no SOC 2 / HIPAA), not a code generator. It improves the repo you already have.

### Read-only sweeps vs. skills that actually edit

This is the thing to get straight early. There are two ways to use the plugin, and they behave very differently.

- **Sweep mode (`/vibesubin`).** Every skill runs in parallel, *read-only*. They produce findings, not fixes. Nothing in your repo changes until you approve items from the report. This is the "I want an honest second opinion" mode.
- **Direct call (`/refactor-verify`, `/setup-ci`, `/write-for-ai`, `/manage-secrets-env`, `/project-conventions`, `/unify-design`).** The skill does its full job, which includes editing files. `refactor-verify` rewrites your code across the dependency tree. `setup-ci` drops working YAML into `.github/workflows/`. `write-for-ai` edits your README. `manage-secrets-env` scaffolds `.env.example`, `.gitignore`, and runs the full secret lifecycle. `project-conventions` scaffolds Dependabot, enforces pinning, fixes hardcoded paths. `unify-design` scaffolds the tokens file and rewrites components to reference it. These are the "do the work" modes.

Three skills never edit regardless of how you call them: **`fight-repo-rot`** (pure diagnosis — finds dead code and smells, hands off to `refactor-verify` for deletions), **`audit-security`** (static triage report only), and **`manage-assets`** (bloat report only — never rewrites history, never deletes files). Everything else — `refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design` — is a real worker skill when called directly, and a read-only reporter when invoked via the sweep.

### Today's lineup

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`refactor-verify`](#1-refactor-verify) | *"rename this class"*, *"split this file"*, *"delete this dead code safely"* | A planned change — refactor, rename, split, or delete — executed bottom-up, with four verification passes before it calls itself done |
| [`audit-security`](#2-audit-security) | *"any secrets leaked?"*, *"is this safe?"* | A short triaged list of real findings with file and line, instead of a 500-line PDF |
| [`fight-repo-rot`](#3-fight-repo-rot) | *"find dead code"*, *"what can I delete?"* | Dead code tagged HIGH / MEDIUM / LOW confidence, plus god files, hotspots, hardcoded paths, and test rot. Pure diagnosis — never edits |
| [`write-for-ai`](#4-write-for-ai) | *"write a README / commit / PR"* | Docs the *next* AI session can actually read — and no unbacked marketing adjectives |
| [`setup-ci`](#5-setup-ci) | *"set up deploy"*, *"push to deploy"* | Working GitHub Actions workflows plus a plain-language walkthrough |
| [`manage-secrets-env`](#6-manage-secrets-env) | *"where does this secret go?"*, *"is my `.env` leaking?"* | One opinionated answer with a one-line reason, plus the full secret lifecycle |
| [`project-conventions`](#7-project-conventions) | *"main or dev branch?"*, *"should I pin this dep?"*, *"hardcoded path?"* | One default per decision — GitHub Flow, pinned deps, domain-first layout, no home-dir in source |
| [`manage-assets`](#8-manage-assets) | *"my repo is huge"*, *"should I use LFS?"* | Bloat report — large files, big blobs in git history, LFS candidates. Pure diagnosis — never rewrites history |
| [`unify-design`](#9-unify-design) | *"unify the buttons"*, *"these pages look different"*, *"extract these colors to tokens"* | A design-system audit — scaffolds the tokens file if missing, finds every hardcoded hex and magic px, consolidates duplicate components |

New skills drop into `plugins/vibesubin/skills/` and are picked up by `/vibesubin` automatically.

---

## The `/vibesubin` command

One word that runs every skill in the plugin against your repo in parallel, merges findings into a single report, and waits for approval before touching anything.

Here's what happens. The skill tells you in one sentence what it's about to do, and gives you a chance to narrow the scope (*"only src/api"*, *"only security and repo rot"*) before it launches. Otherwise it fans out every specialist as an isolated task agent — each run stays isolated so there's no cross-contamination between agents. All specialists are read-only on this pass; they produce findings, not fixes. If one can't run — say the test suite won't even start — it reports that as its finding and gets out of the way. A single dead specialist never blocks the sweep.

When they come back, findings get merged by synthesis rules. Criticals float to the top regardless of category (a leaked secret beats a hotspot beats a missing docstring). When multiple specialists independently flag the same file, that file's priority jumps. Findings are grouped by file because you fix files, not categories. Every item gets one concrete recommendation.

You get back a single markdown report: a vibe-check paragraph, a stoplight line per specialist, a top-ten fix list, a recommended order, and a one-sentence verdict. If everything's fine, the verdict says so. Nothing in your repo changes until you approve.

Full report template and synthesis rules live in the [umbrella `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md).

**Sweep vs. single skill.** Sweep for open-ended questions: *"I just inherited this repo"*, *"is this ready to ship?"*, *"second opinion"*. Call a skill directly when you already know what you want: *"refactor this file"* → `/refactor-verify`. *"I pushed my `.env`"* → `/audit-security`, urgency first. *"Write the README"* → `/write-for-ai`.

**Harsh mode.** The sweep runs in balanced tone by default — honest but warm. Ask for harsh mode and it stops softening anything: *"`/vibesubin harsh`"*, *"brutal review"*, *"don't sugarcoat"*, *"매운 맛으로"*, *"厳しめで"*. The report is still read-only, still backed by the same evidence, but drops hedging language, leads with the worst finding, and refuses to close on *"looks fine"* when real issues exist. Opt-in only — never defaults to harsh.

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

Each skill lives at [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/). The writeups below are the user-facing version; the full methodology is in each skill's `SKILL.md`, with deep references in a sibling `references/` folder. You don't need to read the skill files — the AI does that — but they're open source if you're curious.

### 1. `refactor-verify`

The skill I'd defend the hardest. The single biggest failure mode when an AI touches code is the silent one — a function got moved, the rename worked, tests passed, and three weeks later somebody hits a code path still pointing at the old name and the whole thing crashes. `refactor-verify` exists to make that specific kind of silent failure impossible.

It covers two change families — structural refactors (move, rename, split, merge, extract, inline) and safe deletions (removing code `fight-repo-rot` has confirmed is dead). Both use the same four-check proof.

Before touching anything, it snapshots the current state: which functions exist, which file each one lives in, whether tests pass right now, what the linter says. That's the *before* picture. Then it decomposes the change into a dependency tree and works from the leaves up, so you're never in a half-done state mid-run.

After every step, four independent checks run. One walks the symbol set and confirms every public name that existed before still exists (or was deliberately removed). One confirms the moved or kept code is bit-for-bit what it was, modulo whitespace. One re-runs typecheck, lint, tests, and a smoke run. And the fourth — the one that catches the most real bugs — walks every caller of every affected symbol and confirms it points at the right place, or at nothing if the symbol was deleted. If any of the four fails, the skill doesn't advance.

Some things it will not do: touch files you didn't ask it to touch, say *done* with any check failing, fabricate a test result when the suite can't start, rewrite function bodies during a move, or delete code that `fight-repo-rot` flagged LOW confidence without human review.

### 2. `audit-security`

Enterprise security scanners have a noise problem. They flag five hundred things, four hundred and ninety of which are false alarms, so after a week people ignore the whole thing. Real criticals drown. `audit-security` is the opposite shape: a short, hand-curated list of patterns that catch mistakes people actually make, with every hit triaged — real, false alarm, or needs-human-review — and a one-line reason.

It checks for the obvious (secrets in commits, SQL built by string concatenation, `eval`/`exec`/`pickle.loads` on untrusted input), the less obvious (user-controlled paths in file reads, unescaped input in HTML, cookies missing `httpOnly`/`Secure`, wildcard CORS), and the things people forget (`.env` in git history, `.pem` and SSH keys). Severities are in plain terms — *"a stranger can read every user's data"* beats *"CWE-89"*.

It does not replace a penetration test. It's a static sweep — no network, no running system. And it will not hide anything embarrassing behind a *"looks fine"* summary.

### 3. `fight-repo-rot`

A dead-code detector first, a clutter spotter second, and a pure diagnosis always. Functions nothing calls, files nothing imports, orphaned modules, exports that have no consumers, dependencies in the manifest that are never imported — those are the things it's actually built to find. On top of that it flags the usual smell set: god files, god functions, hardcoded absolute paths, literal IPs, `TODO` / `FIXME` / `HACK` older than six months, and the files at the top of the *"most likely to bite you next"* list (the ones that change a lot *and* are complicated).

Every dead-code candidate comes back with a confidence tag:

- **HIGH** — no references anywhere (grep, LSP, import graph, tests, config files). Safe to hand off to `refactor-verify` for deletion.
- **MEDIUM** — referenced only from tests, or the language uses dynamic dispatch (Python, Ruby, loose JS). Operator confirms before deletion.
- **LOW** — exported symbol, generated code, reflection / DI / annotations involved. Human review required; never auto-hand-off.

This skill is deliberately hands-off: it never edits, never deletes, never runs verification. It surfaces problems with evidence next to each one, and hands off to `refactor-verify` for deletions and splits, to `manage-config-env` for hardcoded-path fixes, and to `audit-security` for CVE dependency rot. Nothing gets touched until you approve the list.

### 4. `write-for-ai`

Most docs are written for a human reader who skims once. AI reads them differently: it re-parses them fresh every session, prefers tables over prose, follows explicit file paths in backticks, and needs *"never do X"* stated declaratively rather than buried in a story. `write-for-ai` writes for that reader — and the docs happen to work better for humans too, because structure is structure.

You give it a thing to write — README, commit, PR description, architecture doc, `CLAUDE.md`, `AGENTS.md` — and it starts by reading the repo cold, the way a fresh AI session would. Then it extracts the invariants: not just *what* the project does, but the rules it follows. It fills in the relevant template and, critically, verifies every claim before writing it. If the README says `pnpm test` runs the suite, the skill runs `pnpm test` first.

What this prevents: you ask an AI to rewrite the README and it does a good job, except a paragraph about the environment variables silently disappears. You don't notice because you don't remember what was there. The next AI session starts from the new README and has no idea your env layout exists.

### 5. `setup-ci`

CI is the biggest productivity unlock in the plugin — once it's set up correctly, *deploy* stops being a thing you think about and becomes `git push`. Unfortunately, *setting it up correctly* is where most non-developers give up.

The skill starts by explaining the concepts in plain language — what a runner is, what Secrets are, why `concurrency` groups matter, why you want a health check after every deploy. Then it detects your stack from `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod`, picks the right test and lint commands, and scaffolds two working workflows. `test.yml` runs tests and lint on every push and PR with explicit timeouts. `deploy.yml` deploys on success using the pattern that fits your host — SSH, Vercel, Fly.io, Cloud Run, Netlify — with concurrency guards, SSH key cleanup, and a post-deploy health check.

Two things it won't do on purpose: it won't add Secrets for you (Secrets live in the GitHub UI; the skill tells you which ones and what they contain, but never handles credentials itself), and it won't guess your host.

### 6. `manage-secrets-env`

Secrets are the high-stakes slice of "where does this value go" — a misplaced credential is an incident, not a style preference. `manage-secrets-env` owns that slice: the four-bucket decision tree (source constant / env var / local `.env` / CI secret store), the `.env.example` ↔ `.env` drift check, the default-safe `.gitignore` template, and the full lifecycle (add / update / rotate / remove / migrate / audit drift / provision a new environment).

Defaults, shortest form: constants that never change at runtime go in code; local-only secrets go in `.env` with a committed `.env.example`; production secrets go in your CI provider's secret store; runtime config changes between environments as environment variables; `.gitignore` ships with every secret-shaped entry pre-filled.

On a new project it scaffolds `.env.example`, `.gitignore`, and startup validation. On an existing one it audits what's there, flags tracked-secret files as incident-class findings, and hands off to `audit-security` when something has already leaked.

### 7. `project-conventions`

The lower-stakes companion to `manage-secrets-env`. Every project has structural decisions that aren't about secrets: main-or-dev branch, pinned-or-floating dependencies, domain-or-type directory layout, absolute-path bugs creeping into source. Most of those have one answer that works for 95% of projects, and picking that answer should not be a session-long conversation.

Defaults: GitHub Flow (`main` plus short-lived feature branches, no `dev`), exact-pinned production dependencies with a committed lockfile, Dependabot or Renovate on a monthly cadence, domain-first directory layout, no absolute paths in source. Every rule has a one-sentence reason.

On a new project it scaffolds `dependabot.yml` and a branch-strategy note. On an existing one it audits branch deviations, unpinned dependencies, directory smells, and hardcoded paths — and hands off multi-file fixes to `refactor-verify` so nothing gets rewritten without a verification pass.

### 8. `manage-assets`

A bloat detector, not a code analyzer. Repos get slow from binaries — a 300 MB SQLite checked in last year, a `dist/` directory that snuck past `.gitignore`, a tracked `.psd` that really wanted to be LFS. `manage-assets` surfaces that weight: file sizes in the working tree, git-history blob sizes (the invisible ones), LFS migration candidates, asset-directory growth, duplicate binaries.

This skill is **diagnosis-only**. It never deletes a file, never rewrites history, never runs `git filter-repo` or `git lfs migrate`. When the operator approves a removal, the work hands off to `refactor-verify` (which owns verification for destructive operations like history rewrites), or to `manage-secrets-env` if the finding is `.gitignore`-shaped, or to `fight-repo-rot` if the asset is also unreferenced.

It pairs especially well with open-sourcing — the first clone on a slow connection is a blunt measurement of how much weight your repo is carrying.

### 9. `unify-design`

A web-dev skill for the thing every vibe-coded project eventually needs and never gets around to: one design system, consistently referenced, no drift. Most projects ship with three different primary blues, two button implementations, five slightly different paddings, a logo pasted into six files as raw `<img>` tags, and two pages whose navigation doesn't match. Each is invisible in isolation and obvious to a first-time visitor.

`unify-design` treats the project's brand identity — colors, spacing, typography, radii, shadows, breakpoints, and the core components — as the single source of truth, and rewrites drift back to tokens. It detects the framework (Tailwind v3 and v4, CSS Modules, styled-components, Emotion, Material UI, Chakra UI, vanilla CSS with custom properties) and uses the project's own idioms — Tailwind theme, CSS variables, or a theme object — never a foreign pattern.

It does three things. First, it establishes the source of truth: if there's no tokens file, it scaffolds one with opinionated defaults (spacing scale, typography scale, radius scale) and asks the operator for the two values it can't guess — the primary color and the display font. Second, it audits for drift — hardcoded hex values outside the tokens file, arbitrary Tailwind values like `w-[432px]`, inline style objects, duplicate Button/Card/Nav/Logo components, near-match colors that were obviously a copy-paste error. Third, it fixes the drift: small replacements apply directly, multi-file refactors hand off to `refactor-verify` so the token rename or component consolidation gets call-site verification.

Two things it won't do on purpose: invent a brand when the project has none (it asks), and rewrite across frameworks (if you're on styled-components, it uses your theme object, not Tailwind's).

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
