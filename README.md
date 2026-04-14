# vibesubin

A portable skill plugin that teaches your AI assistant to refactor, audit, and deploy your code the way I wish it would by default — and then lets you run all of it at once with a single word: `/vibesubin`.

It's built for people who ship real things with AI but weren't trained as developers. These are the habits I use when I'm coding with an AI myself, packaged as skills so your assistant can follow them without you having to know every rule. The same skills happen to be useful to anyone else who'd rather automate the boring discipline than keep doing it by hand.

The same `SKILL.md` files drive three install paths: **Claude Code** (via the plugin marketplace), **Codex CLI** (via a `--to codex` symlink), and **any agent supported by [skills.sh](https://skills.sh)** — Cursor, Copilot, Cline, and others. There is no per-agent fork. You write the skill once; every host you care about picks it up.

> [한국어](./README.ko.md) · [中文](./README.zh.md) · [日本語](./README.ja.md)

---

## Quick start

Install [Claude Code](https://code.claude.com), then in any Claude Code session run:

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

Open a repo. Type `/vibesubin`. Every skill the plugin ships with fans out across your code in parallel, read-only, and comes back with a single prioritized report — a stoplight per specialist, a top-ten fix list grouped by file, a suggested order of operations, and a one-sentence verdict. Nothing is modified until you approve items from the list.

If you're on Codex CLI, Cursor, Copilot, or Cline instead, skip to [Path B](#path-b--skillssh-cross-agent) for the cross-agent install, or [Path C](#path-c--manual-symlinks-claude-code-andor-codex-cli) for a manual symlink. All three paths live under [Install](#install) below.

---

## Contents

- [What vibesubin is, and what it isn't](#what-vibesubin-is-and-what-it-isnt)
- [The `/vibesubin` command](#the-vibesubin-command)
- [Install](#install)
- [The skills](#the-skills)
- [Using it day to day](#using-it-day-to-day)
- [Workflows that come up often](#workflows-that-come-up-often)
- [Adding your own skill](#adding-your-own-skill)
- [Troubleshooting](#troubleshooting)
- [Under the hood](#under-the-hood)
- [What this plugin isn't for](#what-this-plugin-isnt-for)
- [Philosophy](#philosophy)
- [Contributing](#contributing)
- [License](#license)

---

## What vibesubin is, and what it isn't

The short version: it's a small bundle of AI skills, written as `SKILL.md` files, that your agent picks up automatically whenever a request matches one of them. You don't memorize trigger phrases. You just say what you want in plain words — *"split this file safely"*, *"is anything leaking?"*, *"set up deploy"* — and the right skill runs.

What makes these skills worth bundling is the one rule they all share: **they don't say *done* until they can show you the evidence.** A refactor isn't finished because the AI rewrote the file; it's finished because four independent checks confirm nothing was dropped, moved, or mis-wired. A security sweep isn't a vibes-based paragraph about what "looks fine"; it's a triaged list where each hit is either real, a false alarm, or flagged for human review, with a file and a line number. When a skill returns, everything it claims is backed by a command you could run yourself.

The other thing worth knowing early is what this plugin is **not** trying to be. It isn't a SaaS dashboard — there's no server, nothing leaves your machine except what your AI decides to send. It isn't a compliance tool; if you need SOC 2 or HIPAA audits, use something built for that. And it isn't a code generator or project scaffold. It improves the repo you already have, and it's very comfortable telling you when your question is outside its scope.

### Today's lineup

| Skill | What you'd ask for | What comes back |
|---|---|---|
| [`refactor-safely`](#1-refactor-safely) | *"rename this class"*, *"split this file"*, *"is it still working?"* | A planned change, executed bottom-up, with four verification passes before it calls itself done |
| [`audit-security`](#2-audit-security) | *"any secrets leaked?"*, *"is this safe?"* | A short list of real findings with a file and line for each, instead of the 500-line PDF nobody reads |
| [`fight-repo-rot`](#3-fight-repo-rot) | *"what should I clean up?"*, *"where's the mess?"* | The files most likely to bite you next, ranked by churn × complexity |
| [`write-for-ai`](#4-write-for-ai) | *"write a README / commit / PR"* | Docs the *next* AI session can actually read — tables over prose, claims backed by commands |
| [`setup-ci`](#5-setup-ci) | *"set up deploy"*, *"push to deploy"* | Working GitHub Actions workflows plus a plain-language walkthrough of why each bit is there |
| [`manage-config-env`](#6-manage-config-env) | *"where does this secret go?"*, *"main or dev?"* | One opinionated answer with a one-line reason, because picking is the tax this skill removes |

The lineup grows over time. New skills drop into `plugins/vibesubin/skills/` alongside the existing ones, inherit the same rules, and are picked up by `/vibesubin` automatically — there's nothing to reconfigure. See [Adding your own skill](#adding-your-own-skill) if you want to extend it yourself.

---

## The `/vibesubin` command

`/vibesubin` is two things at once, and both are on purpose.

It's a command — one word that runs every skill in the plugin against your repo in parallel, merges the findings into a single report, and waits for you to approve fixes before touching anything. You don't pick a skill, you don't chain them yourself, and you don't wait an afternoon while each one runs in sequence. You just type the word.

It's also a vibe. The whole plugin is named after a mode of working — *vibe coding*, where you're building something real with an AI instead of writing every line yourself — and `/vibesubin` is the thing you type when you want the full treatment without narrating each step. Half command, half meme. It's deliberate.

Here's what actually happens when you run it. The skill starts by telling you, in one sentence, what it's about to do, and gives you a chance to narrow the scope. If you want it to only look at `src/api/` or only check security and repo rot, say so before it launches. Otherwise, it fans out every specialist as a parallel task agent. The specialists don't share state with each other — if you've ever used an orchestrated LLM setup, you know cross-contamination between agents is a common failure mode, and `/vibesubin` sidesteps it by keeping each run isolated.

The specialists are all read-only on this pass. They produce findings, not fixes. If one of them can't run — say the test suite won't even start, so `refactor-safely` can't get a green baseline — it reports that as its finding and gets out of the way. The others keep going. A single dead specialist never blocks the sweep.

When they all come back, the findings get merged by a set of synthesis rules. Criticals float to the top regardless of which category they came from: a leaked secret beats a hotspot beats a missing docstring. When two or three specialists independently flag the same file, that file's priority jumps — a file that's a hotspot *and* has a SQL injection *and* has zero test coverage is the one you should fix first, and the report says so. Findings are grouped by file, because you fix files, not categories. And every item gets one concrete recommendation, with a pointer to the skill that should handle it.

What you see at the end is a single markdown report: a paragraph of overall *vibe*, a stoplight line per specialist, a top-ten fix list as a table, a recommended order for tackling the fixes, and a one-sentence verdict. If everything's fine, the verdict says so — "this looks clean, here are two polish items" is a valid output. Nothing in your repo changes until you say which items to apply.

### The report shape

Every run produces the same sections. The skeleton below is the template; the actual content comes from the specialists running against your code.

```markdown
# /vibesubin sweep — <repo> — <date>

## Vibe check

<One short paragraph. The overall state of the repo, the two or three things
that stand out, and whether you should ship it or fix things first. No
cheerleading, no hedging.>

## What ran

- refactor-safely:    🟢 | 🟡 | 🔴   <one-line summary>
- audit-security:     🟢 | 🟡 | 🔴   <one-line summary>
- fight-repo-rot:     🟢 | 🟡 | 🔴   <one-line summary>
- write-for-ai:       🟢 | 🟡 | 🔴   <one-line summary>
- setup-ci:           🟢 | 🟡 | 🔴   <one-line summary>
- manage-config-env:  🟢 | 🟡 | 🔴   <one-line summary>
  <... plus any skill you've added since ...>

## Top-10 fix list

| # | File | What's wrong | Severity | Fix with |
|---|---|---|---|---|
| 1 | <file:line> | <finding> | CRITICAL / HIGH / MEDIUM / LOW | <skill → skill> |

## Recommended order

1. <why this goes first>
2. <why this is next>

## What I did NOT do

Read-only sweep. No files changed, no commits made, no external systems
touched. Approve items and each one gets handed to the right specialist.

## Verdict

<One sentence. Direct, not hedged.>
```

The full template, including the synthesis rules the skill actually follows, lives in the umbrella [`SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md). Open it if you want to see what the skill is instructed to produce, word for word.

### When to run the sweep, and when to just call a skill

The sweep is great for open-ended questions. *"I just inherited this repo, what's the state?"* *"Is this ready to ship?"* *"I want a second opinion before I touch this."* Those are `/vibesubin` questions — you don't know what you're looking for, and you want the plugin to tell you.

But if you already know what you want, call the skill directly. *"Refactor this one file"* is `/refactor-safely`. *"I accidentally pushed my `.env` to GitHub"* is `/audit-security` right now, urgency first, breadth second. *"Write the README"* is `/write-for-ai`. Running the full sweep for a known target is just making yourself wait longer and giving yourself a longer report to skim.

### A few edge cases worth knowing

If a specialist fails mid-run, the rest keep going and the failed one is marked red in the *What ran* section with its error quoted. The sweep is never blocked on any single specialist.

If your repo is huge (north of ten thousand files or so), `/vibesubin` partitions the work by top-level subdirectory, runs each partition, and merges the reports. You'll see a *partitioning* note before it starts, so you know why it's taking longer.

If every specialist comes back clean, the verdict says so. You don't get a fake fix list to justify the command. *"This is fine, ignore the noise below the fold"* is a real outcome.

---

## Install

Same skill files, three install paths, depending on which agent you use and how you want updates to flow. They can coexist — there's no harm in having Path A installed for Claude Code and Path C pointing at Codex CLI at the same time.

| Path | Agent | Best when |
|---|---|---|
| **A. Claude Code marketplace** | Claude Code | You want auto-updates and the simplest possible flow |
| **B. `skills.sh` (npx)** | Claude Code, Cursor, Copilot, Cline, Codex CLI, and more | You use something other than Claude Code, or you use multiple agents |
| **C. Manual symlinks** | Claude Code and/or Codex CLI | You're hacking on the plugin or want `git pull` to push changes live |

### Path A — Claude Code plugin marketplace (recommended)

You'll need [Claude Code](https://code.claude.com) installed first. Then register the marketplace once:

```
/plugin marketplace add subinium/vibesubin
```

Install the plugin:

```
/plugin install vibesubin@vibesubin
```

The two `vibesubin` in that command are the plugin name and the marketplace name. They're identical on purpose — it's a single-plugin marketplace.

To confirm it worked, start a new Claude Code session, hit `/`, and start typing `refactor`. You should see `/refactor-safely` in the autocomplete along with the other skills. If they're there, you're done.

When you want updates, run `/plugin marketplace update`. Do it every few weeks, or whenever you see a release note on GitHub. Marketplace updates don't touch anything else you have installed.

A few things that might go wrong: if you see *"repository not found"*, check the spelling — it's `subinium/vibesubin`, lowercase, one slash. If the skills don't show up in autocomplete, close every Claude Code session (they cache skills per session) and start a fresh one. If registering the marketplace tells you it *"already exists"*, you added it before and can skip to `/plugin marketplace update` instead.

### Path B — `skills.sh` (cross-agent)

[`skills.sh`](https://skills.sh) is a cross-agent skill registry run by Vercel Labs. Its CLI speaks the same `SKILL.md` format vibesubin uses, which means the plugin works on every host the `skills` CLI supports — Claude Code, Cursor, GitHub Copilot, Cline, Codex CLI, and more.

One command installs everything:

```bash
npx skills add subinium/vibesubin
```

Under the hood, `skills` clones the repo, walks `plugins/vibesubin/skills/` looking for `SKILL.md` files with valid YAML frontmatter, and installs each one into your active agent's skills directory. Claude Code isn't required at any point.

Updates are re-running the same command. Uninstalling is `npx skills remove vibesubin`.

If `skills` can't find the skills, your agent might not be on its supported list yet — check `npx skills --help` for the current targets. If it's picking the wrong agent, there's an override flag in the same help output. And if `npx` is caching an old version, `--force` or `npx clear-npx-cache` usually clears it.

### Path C — Manual symlinks (Claude Code and/or Codex CLI)

Use this path when you're editing the plugin yourself, or when you need an offline install, or when you want `git pull` to make new changes live in your sessions without re-installing anything. The `install.sh` script symlinks each skill directory into the target agent's skills folder, so there's nothing to copy and nothing to refresh.

```bash
cd ~/Projects            # or wherever you keep code
git clone https://github.com/subinium/vibesubin.git
cd vibesubin

bash install.sh                  # Claude Code (~/.claude/skills) — the default
bash install.sh --to codex       # Codex CLI (~/.codex/skills)
bash install.sh --to all         # symlink both at once
bash install.sh --dry-run        # preview without touching anything
bash install.sh --force          # overwrite conflicting names
```

Verifying the install is the same as the other paths: start the agent, hit `/`, and look for the skills. Claude Code autocompletes them; Codex lists them in its command menu.

Updates come from the clone. `git pull` refreshes the source, and because the target directories are symlinks, the new files are live on the next session — no re-install, no re-register.

Uninstalling mirrors the install flags:

```bash
bash uninstall.sh                # Claude Code
bash uninstall.sh --to codex     # Codex CLI
bash uninstall.sh --to all       # both
```

The uninstaller only removes symlinks it created. If something in the target directory is a real file or a symlink pointing somewhere else, it's left alone. Your clone is never touched.

If `install.sh` tells you *"Permission denied"*, run `chmod +x install.sh` and try again. If you end up with name conflicts, `--dry-run` shows you what's in the way and `--force` replaces it. And if you accidentally installed via both Path A and Path C, run `bash uninstall.sh --to all` from the clone to clear the symlinks, then pick whichever path you want to keep.

One note on Codex CLI specifically: I'm assuming its user-level skills directory is `~/.codex/skills/`, based on Codex's convention of using `~/.codex/` for user config. If your Codex version uses a different path, open an issue with the version number and the real path and the script will be updated. In the meantime you can patch the target in `install.sh` or symlink the clone directly.

### Install matrix

|  | Auto-update | Cross-agent | Editable live | Offline |
|---|---|---|---|---|
| **A. Marketplace** | ✓ | — | — | — |
| **B. skills.sh** | on re-run | ✓ | — | — |
| **C. Manual symlinks** | ✓ (via `git pull`) | ✓ (Claude + Codex) | ✓ | ✓ |

---

## The skills

Each skill is a directory under [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/). The writeups below are the user-facing version; the full methodology for each one lives in its `SKILL.md`, with the deeper reference material in a sibling `references/` folder. You don't need to read the skill files to use them — the AI does that — but they're open source and readable if you're curious.

The list is current as of this release, and it will grow. New skills inherit the same rules and are automatically picked up by `/vibesubin`.

### 1. `refactor-safely`

If there's one skill in this plugin I'd defend the hardest, it's this one. The single biggest failure mode when an AI touches code is the silent one — the function got moved, the rename worked, tests passed, and three weeks later somebody hits a code path that still points at the old name and the whole thing crashes. `refactor-safely` exists to make that specific kind of silent failure impossible.

The way it works: before touching anything, it snapshots the current state of the repo. Which functions exist, which classes exist, which file each one lives in, whether the tests pass right now, what the linter says, what a smoke run outputs. That's the *before* picture. Then it decomposes the change into a dependency tree — "to split this file, first extract this helper; to extract the helper, first rename that variable" — and works from the leaves up, so you're never in a half-refactored state mid-run.

After every node in that tree, four independent verification passes run. The first one walks the symbol set and checks that every function, class, and exported name that existed before the change still exists somewhere — this catches silent drops. The second does an AST diff on the moved function bodies and confirms they're identical to before, line for line, modulo whitespace and comments. The third re-runs tests, typecheck, lint, and a smoke run to confirm the code still does what it did. And the fourth — the one that catches the most real bugs — walks every call site of every moved symbol and confirms it points at the new location. If any of the four fails, the skill doesn't advance. It fixes the cause and reruns the checks on the same node until they're green.

Some things `refactor-safely` will not do, and you should know about them:

- It will not touch files you didn't ask it to touch.
- It will not say *done* if any of the four verification passes fail. Either the cause gets fixed, or the skill halts and tells you why.
- It will not fabricate a test result. If the test suite can't start — missing deps, broken environment, whatever — it says so and stops, instead of guessing.
- During a *move*, it will not rewrite function bodies. Moves are bit-for-bit copies, and the skill verifies that explicitly.

The pitfall this prevents, in one sentence: the refactor that builds cleanly, passes tests, and breaks the one code path nobody had a test for. The call-site closure check is what catches it.

### 2. `audit-security`

Enterprise security scanners have a noise problem. They flag five hundred things, four hundred and ninety of which are false alarms, so after a week non-developers start ignoring the whole thing. Real criticals drown. `audit-security` is deliberately the opposite shape: a short, hand-curated list of patterns that catch the mistakes people actually make, with every hit triaged — real, false alarm, or needs-human-review — and a one-line reason for the classification.

It checks for the obvious stuff (secrets in commits, SQL built by string concatenation, shell commands built the same way, `eval`/`exec`/`pickle.loads` on untrusted input), the less obvious stuff (user-controlled paths going into file reads, unescaped user input in HTML, cookies missing `httpOnly` or `Secure`, wildcard CORS), and the things people forget (`.env` files in git history, not just in the working tree; `.pem` and SSH keys). Each real finding gets a severity in plain terms — *"a stranger can read every user's data"* beats *"CWE-89"* for a non-developer — and a one-sentence fix, with a pointer to whichever skill should apply it.

It will not replace a penetration test. It doesn't probe a running system, doesn't do authenticated scans, doesn't touch the network at all. It's a static sweep of the repo. And it will not hide anything embarrassing behind a *"looks fine"* summary; if there's a critical, it's at the top whether you like it or not.

The pitfall this prevents is the one where nobody reads the output. A ten-line triaged list you actually read is worth more than a five-hundred-line PDF you don't.

### 3. `fight-repo-rot`

Repos don't collapse overnight. They rot over months as god files grow, dead code accumulates, hardcoded paths get committed, and six-month-old `TODO`s turn into forever-`TODO`s. You usually notice the rot only after it breaks something. `fight-repo-rot` is the early-warning report you wish you'd had.

Its main metric is the one most developers eventually learn the hard way: **churn × complexity**. The file that changes all the time *and* is complicated is the file you'll most likely break next. Those files go to the top of the list. On top of that, the skill scans for god files (over 500 lines), god functions (over 50 lines), dead code (functions nothing calls, files nothing imports), hardcoded absolute paths and literal IP addresses, `TODO` / `FIXME` / `HACK` comments older than six months, and files that either everything imports (great refactor target) or import everything (a coupling smell).

What you get back is a table sorted by *"fix this first"*, with a pointer to the skill that should handle each item. The skill is a diagnosis, not a treatment — it doesn't refactor, rewrite, or delete. It just tells you where to look, so your refactor effort lands on the right target instead of the most recent file you happened to have open.

### 4. `write-for-ai`

Most docs are written for a human reader who will skim them once. AI reads them differently. It re-parses them fresh every session, it prefers tables over prose, it follows explicit file paths in backticks much better than vague references, and it needs "never do X" stated declaratively rather than buried in a story. `write-for-ai` writes for that reader — and the docs it produces happen to also work better for humans, because structure is structure.

You give it a thing to write — README, commit message, PR description, architecture doc, `CLAUDE.md`, `AGENTS.md` — and it starts by reading the repo cold, the way a fresh AI session would. Package manifests, config files, entry points, directory structure, whatever a new arrival would look at first. Then it extracts the invariants: not just *what* the project does, but the rules it follows (how branches work, where secrets live, what commands run the tests, what *"done"* means). It fills in the relevant template, and — this is the important part — it verifies every claim the document makes before writing it. If the README says `pnpm test` runs the suite, the skill runs `pnpm test` first. If it doesn't work, the document is updated to match reality.

The thing this skill really prevents: you ask an AI to rewrite the README and it does a good job, except that along the way a paragraph explaining the environment variables silently disappears. You don't notice because you don't remember what was there to miss. The next AI session starts from the new README and has no idea your env layout exists. By verifying claims before writing, `write-for-ai` treats the document as a contract with the next session, not as a one-shot prose generation task.

### 5. `setup-ci`

CI is the biggest productivity unlock in the whole plugin — once it's set up correctly, *deploy* stops being a thing you think about and becomes `git push`. Unfortunately, *setting it up correctly* is where most non-developers give up. You spend three days on Stack Overflow learning what a runner is, hit a concurrency bug, conclude CI is too much, and go back to SSHing into a server and typing `git pull && sudo systemctl restart myapp` whenever you want to ship. `setup-ci` collapses those three days into the part you actually need.

The skill starts by explaining the concepts — in plain language, with no assumed YAML literacy. What a runner is, what Secrets are, why `workflow_run` is different from `push`, why `concurrency` groups matter, why you want a health check after every deploy. Then it detects your stack from `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` / etc., picks the right test and lint commands, and scaffolds two working workflows. `test.yml` runs your tests and lint on every push and PR, with explicit timeouts and readable job names. `deploy.yml` deploys on success, using the pattern that fits your host — SSH, Vercel, Fly.io, Cloud Run, Netlify, whatever's there — with concurrency guards so two deploys can't race, SSH key cleanup so credentials don't end up in job logs, and a post-deploy health check so failures get caught before users are.

There are two things `setup-ci` will not do, and both are on purpose. It won't add Secrets for you — Secrets live in the GitHub UI, the skill tells you which ones to add and what they should contain, but it never handles credentials itself. And it won't guess your host. If the target isn't clear, it asks.

### 6. `manage-config-env`

Every non-developer setting up a new project has to pick between `main` and `dev`, between committing `.env` and not, between a config file and environment variables, between `feature/` and `feat/`, and probably a dozen other *"two reasonable options"* decisions before the first deploy. Each of those decisions is a tax on your attention, and most of them don't actually need a decision — 95% of projects are fine with the same defaults. `manage-config-env` pre-picks the defaults, explains each one in one sentence, and gets out of the way.

The defaults it recommends, in the shortest possible form: constants that never change at runtime go in code; local-only secrets go in `.env` with a committed `.env.example`; production secrets go in GitHub Secrets; runtime config that changes between environments goes in environment variables; branches follow GitHub Flow (one `main`, short-lived `feature/...` / `fix/...` / `refactor/...` branches, always merged through PRs); and `.gitignore` ships pre-filled with the usual suspects (`.env`, SSH keys, `__pycache__`, `node_modules`, `.venv`, `.DS_Store`, IDE folders). If you ask for a reason, you get one line per default — enough to judge whether it applies to your situation, not enough to be a lecture.

If you're starting a new project, the skill can scaffold `.env.example`, `.gitignore`, and a branch-strategy note at the repo root. If you're working on an existing project, it audits what's there and flags mismatches with the defaults — but it doesn't silently rewrite your conventions. You already made a choice; it just tells you when that choice disagrees with its opinion.

---

## Using it day to day

Three ways to invoke the plugin, roughly in order of how much you already know about what you want.

When you don't know where to start — new repo, messy state, pre-release jitters — type `/vibesubin`. It runs everything and hands back one report. This is the mode the plugin was named after.

When you know what's bothering you, just say it in plain words. *"Clean this up and make sure nothing breaks"* fires `refactor-safely`. *"Any secrets leaked?"* fires `audit-security`. *"What should I fix first?"* fires `fight-repo-rot`. *"Write me a README"* fires `write-for-ai`. *"Set up deploy"* fires `setup-ci`. *"Where should this secret go?"* fires `manage-config-env`. You don't have to memorize the trigger list; the skills respond to how non-developers actually phrase these requests.

When you know exactly which skill you want, call it by name: `/refactor-safely`, `/audit-security`, `/fight-repo-rot`, and so on. The skill asks for whatever context it needs (*"which file?"*, *"which host?"*) and gets to work.

### What a skill's output looks like

Every skill in the plugin follows the same four-part output shape: what it did, what it found, what it verified, and what you should do next. That's it. If a skill ever gives you a wall of prose without those four parts, that's a bug — [open an issue](https://github.com/subinium/vibesubin/issues) and it'll get fixed.

---

## Workflows that come up often

Skills hand off to each other naturally, and the same chains tend to show up over and over.

**Cleaning up the repo.** Start with `fight-repo-rot` to find the worst offender, let `refactor-safely` fix it with the four-step verification, and finish with `write-for-ai` to write the commit and PR description.

**Preparing a release.** Run `audit-security` for secrets and common holes, use `refactor-safely` on anything critical, and let `setup-ci` confirm your workflow will catch regressions next time around.

**Onboarding to a repo you just inherited.** Run `/vibesubin` for the full sweep, then `write-for-ai` to fill in the missing `CLAUDE.md` from the findings, then `manage-config-env` to audit `.gitignore`, `.env.example`, and the branch strategy.

**Starting a new project from scratch.** `manage-config-env` scaffolds the `.env.example`, `.gitignore`, and branch layout. `setup-ci` lays down the test and deploy workflows. `write-for-ai` writes the README and `CLAUDE.md` so the next session — human or AI — doesn't have to reverse-engineer the project.

You don't plan these chains yourself. The skills suggest the next hand-off when it makes sense, so you mostly just say yes.

---

## Adding your own skill

The plugin is built to grow. A new skill is a self-contained directory under `plugins/vibesubin/skills/<skill-name>/`. Drop it in, restart your agent, and both `/vibesubin` and the autocomplete menu pick it up — there's no registry file to touch.

The minimum viable structure looks like this:

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # required, under 500 lines, with YAML frontmatter
├── references/           # optional deep-dive docs, loaded only when SKILL.md links to them
├── scripts/              # optional executable helpers
└── templates/            # optional files the skill copies into user projects
```

And the minimum viable `SKILL.md` is this:

```markdown
---
name: my-new-skill
description: One sentence saying when this skill triggers and what it does. End with the trigger phrases so the AI can match user requests to the skill.
---

# my-new-skill

## When it runs
...

## What it does
1. ...
2. ...

## What it will not do
- ...

## Output format
1. What it did
2. What it found
3. What it verified
4. What you should do next
```

A few rules new skills should inherit — these aren't enforced in code, they're how the plugin stays consistent. *Done* means verified, not claimed, so every skill that makes changes has to produce evidence. The top-level `SKILL.md` stays under 500 lines, with depth pushed down into `references/`. Output follows the four-part shape — what it did, what it found, what it verified, what to do next. Any skill that can be called from `/vibesubin` needs a read-only mode. And every skill should be explicit about what it checks, what it doesn't, and where its confidence ends.

If you'd like a new skill included in the main plugin, open an issue with the trigger phrases, what it would do, and a concrete example of where you'd use it. See [Contributing](#contributing) below.

---

## Troubleshooting

**Skills don't show up in autocomplete.** Close every agent session, wait a few seconds, start a new one. Skills cache per session.

**`install.sh` says "Permission denied."** Run `chmod +x install.sh`, then `bash install.sh`.

**Marketplace says the plugin "already exists."** You added it before. Run `/plugin marketplace update` instead.

**`npx skills add` says no skills were found.** Your agent might not be on the `skills.sh` supported list yet. `npx skills --help` lists the current targets.

**You installed via two paths and something's broken.** Run `bash uninstall.sh --to all` from the manual clone to clear the symlinks, then pick one path and stick with it.

**Codex CLI doesn't see the skills after `install.sh --to codex`.** Confirm `~/.codex/skills/` exists after the run. If your Codex version uses a different skills directory, patch the target in `install.sh` or symlink the clone directly — and open an issue with the version and the actual path so the script can be fixed.

**A skill reported something that isn't true.** That's a blocker-severity bug. Open an issue with the command you ran, the output you got, and what you expected.

Anything else, [open an issue](https://github.com/subinium/vibesubin/issues) with the exact error and what you tried.

---

## Under the hood

The plugin lives at [`plugins/vibesubin/`](./plugins/vibesubin) and is published via the [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) manifest — that's the file the Claude Code marketplace reads to know what's in this repo. Each skill is a self-contained directory:

```
skills/<skill-name>/
├── SKILL.md              # required entry point the AI reads when the skill triggers
├── references/           # optional deep-dive docs, loaded only on demand
├── scripts/              # optional helper scripts the AI executes
└── templates/            # optional artifacts copied into the user's project
```

A few conventions the plugin follows throughout. `SKILL.md` stays under 500 lines so the AI can load it quickly; anything deeper goes into `references/`. References don't chain into more references — a single hop, no recursive rabbit holes, because long chains get only partially read. Scripts are *executed*, not read, so when a skill says *"run this script"*, the logic isn't also reproduced in the instructions. Templates are artifacts, which is to say the files under `templates/` get copied into your project with placeholders filled in, instead of being described in prose. And the top-level instructions stay language-agnostic, with per-language specifics pushed into `references/language-*.md`.

---

## What this plugin isn't for

vibesubin is deliberately scoped, and it's up-front about what it doesn't handle. If you need compliance audits — SOC 2, HIPAA, PCI-DSS — use a real compliance tool. If you need penetration testing, hire a pen tester. Full design systems or UI component libraries are out of scope. Deep language-specific refactoring (OpenRewrite for Java, AST codemods for TypeScript) belongs in the language-specific tool; vibesubin is language-agnostic by design. Project management and issue tracking are also out.

If you ask for something outside the scope, the plugin will say so. And if it's something you think the plugin *should* cover, open an issue — that's how new skills get added.

---

## Philosophy

A handful of rules every skill in the plugin is built around. You don't need to memorize them to use the plugin — they exist so current skills stay consistent and future skills inherit the same shape.

Your AI is a well-meaning junior developer. Juniors work hard, and juniors also sometimes forge ahead when they should have stopped to ask. The plugin inserts *"stop and ask"* moments where a more careful hand would.

*Done* is proven, not claimed. If a task says "complete", there has to be an execution result behind it — a passing test, a matched hash, a live `200 OK`. Assertion without evidence is, in this plugin's book, a bug.

Docs are for the next AI session, not just for people. The current conversation evaporates when the session ends, so READMEs, commits, and PR bodies are written to let a fresh session rebuild the context from scratch.

Existing conventions are the default. A contributor — including a non-developer with push access — doesn't rewrite the maintainer's branch strategy or file layout on a whim.

Paths are relative, values are environment variables, versions are pinned. Hardcoded absolute paths, IP literals, and unpinned dependencies are time bombs and the plugin treats them that way.

And refactoring is a recursive proof. Every moved symbol has to survive symbol-set diff, AST diff, smoke test, and call-site closure. If any of the four fails, the refactor is not done.

The plugin is [actively maintained](./MAINTENANCE.md). Refactoring tools evolve, skill systems change, and LLM failure modes shift — each skill is reviewed on a schedule.

---

## Contributing

This is open source, but PRs aren't currently accepted. If you find something broken, want a new language or runtime covered, think a refactor or security pattern slipped through the cracks, spotted unclear docs, found a translation error, or want to propose a new skill — [open an issue](https://github.com/subinium/vibesubin/issues). The maintainer reviews and incorporates fixes directly, which keeps the plugin's voice consistent. What makes an issue easy to act on is in [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](./LICENSE).
