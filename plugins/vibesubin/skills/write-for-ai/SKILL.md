---
name: write-for-ai
description: Writes documentation, commit messages, and PR descriptions optimized for the NEXT AI session to understand the project cold. Templates for README, CLAUDE.md / AGENTS.md, conventional commits, and PR bodies. Prioritizes tables and checklists over prose, absolute file paths over vague references, invariants over narrative.
when_to_use: Trigger on "write README", "document this", "commit message", "PR description", "CLAUDE.md", "AGENTS.md", "write for AI", or when preparing docs for the next session (human or AI) to pick up cold.
allowed-tools: Read Write Edit Grep Glob Bash(git log *) Bash(git diff *) Bash(npm test *) Bash(pnpm test *) Bash(pytest *) Bash(go test *) Bash(cargo test *)
---

# write-for-ai

Documentation in this pack has a different primary audience than usual. Most docs are written for a human who will skim them once. These are written for an **AI assistant in a future session** — same operator, same model, but zero context from this conversation.

AI reads tables faster than prose. It follows explicit file paths better than vague references. It needs "always do X, never do Y" stated declaratively, not implied. It re-reads the same file every session, so the payoff for writing once is large.

This skill produces docs in that style. Humans benefit too — the structure is also friendlier for cold skimmers.

## Doc schema — what goes where

Every doc this skill produces is built from a fixed set of sections. The section tree below is the vocabulary. Different doc types use different subsets.

```
Doc
├── Header
│   ├── Title (one line, noun phrase)
│   └── One-sentence description (what this is, in plain terms)
│
├── Orientation (always first)
│   ├── Why this exists         # one paragraph, not three
│   ├── Target audience         # who reads this
│   └── Status                  # early/stable/deprecated, last updated
│
├── Repo map (for README / CLAUDE.md)
│   └── Directory tree with one-line comment per file
│       (absolute paths, in backticks, no wildcards)
│
├── Invariants (for CLAUDE.md / AGENTS.md)
│   ├── Never-do list           # hard rules, reasons stated
│   ├── Always-do list          # mandatory rituals, verification command
│   └── Trade-offs              # decisions already made, don't re-litigate
│
├── How-to (for README)
│   ├── Quick start             # 5 minutes from clone to running
│   ├── Environment variables   # every var, with example value
│   ├── Common tasks            # top 5 things the operator does weekly
│   └── Troubleshooting         # top 5 errors the operator hits
│
├── Architecture (for README / ARCHITECTURE.md)
│   ├── Text diagram            # ASCII art, not Mermaid (AI parses text better)
│   ├── Data flow               # request → handler → service → DB
│   └── Key modules             # what each major module does and owns
│
├── Change log (for CHANGELOG.md)
│   └── Per-version entries with breaking / features / fixes / security
│
├── Conventions (for CONTRIBUTING.md)
│   ├── Language                # of code, of docs, of commits
│   ├── Branch strategy         # one-paragraph summary
│   ├── Commit prefix           # feat / fix / chore / refactor / docs / test / ci / perf
│   └── Review process          # if any
│
└── Pointers (for all docs)
    └── Links to deeper docs, with one-line "what you'll find there"
```

A README for a small project uses: Header + Orientation + Repo map + How-to + Pointers.
A CLAUDE.md uses: Header + Invariants + Repo map + Pointers.
A CONTRIBUTING.md uses: Header + Conventions + Pointers.

## What goes into written artifacts — redaction rules

Every README, CLAUDE.md, commit message, and PR body this skill produces is a potential leak surface. LLM-generated docs tend to be chatty and accidentally embed details that should not live in a file the operator will push to a public remote. Apply this table before emitting any artifact.

| Category | Always safe | Redact unless obviously public | Never write |
|---|---|---|---|
| **File paths** | Repo-relative (`src/auth/session.ts`) | — | Absolute paths with user/hostname (`/Users/alice/...`, `C:\Users\...`, `/home/bob/...`) |
| **Hostnames / URLs** | Public docs URLs, the project's own domain, `localhost` | Staging domains, internal IPs behind a company VPN | Literal production database hostnames, internal office network IPs |
| **Credentials** | Placeholder tokens (`__REPLACE_ME__`, `<YOUR_TOKEN>`) | — | Real tokens, passwords, API keys, SSH private keys |
| **User identities** | Anonymized labels (`operator`, `admin`, `reviewer`) | First names only when the project is tiny and they're already public | Full real names, emails, phone numbers, GitHub handles of private collaborators |
| **Customer data** | Schema names, column descriptions | Sample rows with synthetic data | Real rows, real user IDs, real PII, dumps from production |
| **Infrastructure** | Public service names (`GitHub Actions`, `Fly.io`) | Internal service nicknames | Internal IPs, on-call phone numbers, pager schedules |
| **Business context** | Public product name, public features | High-level roadmap | Unannounced features, unreleased pricing, confidential partnerships |

**Rule of thumb:** if an artifact will be committed to a public repository, assume a competitor and a reporter are reading it. Redact accordingly.

When in doubt, emit a placeholder and tell the operator: *"I've written `<YOUR_DB_HOSTNAME>` where the real hostname would go — replace it before you push, or leave it if the repo is private and the hostname is already public."*

## Mandatory self-review before emitting anything

This pack is published as open source. Do a final sanity pass on every artifact before you show it to the operator or write it to disk.

Checklist:

1. **Repo-specific, not generic** — the commands, framework names, and file paths match the actual repo markers (`pnpm-lock.yaml`, `uv.lock`, `Cargo.toml`, `Gemfile`, `composer.json`, etc.)
2. **No fabricated facts** — every path, command, env var, branch name, and workflow filename exists or is clearly labeled as a placeholder
3. **No leak surface** — no real secrets, no local absolute paths, no internal hostnames, no customer data
4. **No weird public-facing prose** — no memes in formal docs, no chatty filler, no wording that looks machine-generated for its own sake
5. **Verification claims are real** — if the doc says "tests pass" or "typecheck is clean," there is a concrete command next to it

If any of the five fail, fix the artifact before returning it. Open-source docs get screenshotted and quoted out of context; assume zero forgiveness.

## Output principles (applied to every doc)

1. **Tables and checklists beat paragraphs.** Always reach for a table first. Prose only when the structure would be forced.
2. **Repo-relative canonical paths in backticks.** `src/auth/session.ts`, not "in the auth module." Always relative to the repo root, never absolute. **Never write `/Users/<name>/...`, `/home/<name>/...`, `C:\Users\...`, or any path that leaks a local machine** — those paths are different on every machine and betray internal directory structure. If you need to reference a user's home, use `~/` in prose and an environment variable (`$HOME`) in commands.
3. **Declarative tone.** "Never commit `.env`" not "we try to avoid committing secrets."
4. **Invariants separated from history.** Don't tell a story. State the rule.
5. **Verification commands sit next to the claim they verify.** If a doc says "this passes type check," the exact command to reproduce is on the next line.
6. **"Recently decided" lock-box.** Decisions already made go in a section labeled clearly. Future AI sessions read this before proposing alternatives.
7. **Anti-decoration.** No banners, no ASCII art headers, no emoji strings in headings (single-character semantic emojis are fine, decorative ones are not), no "welcome!" paragraphs.
8. **Short over complete.** A one-page doc that covers the top 5 things is better than a ten-page doc the operator never finishes reading.

## Templates

### README.md (for a project)

```markdown
# <Project name>

<One-sentence description>

> Status: <early | stable | deprecated>. Last updated: <YYYY-MM-DD>.

## What this is

<One paragraph. Why it exists, who uses it, what problem it solves.>

## Quick start

```bash
<exact commands — clone, install, run>
```

## Repo map

<tree with one-line comments>

## Environment variables

| Name | Required? | Example | What it's for |
|---|---|---|---|
| `EXAMPLE_VAR` | yes | `hello` | <one-line explanation> |

## Common tasks

- `<command>` — <what it does>
- `<command>` — <what it does>

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `<error message>` | <reason> | <command> |

## More docs

- [`CLAUDE.md`](./CLAUDE.md) — AI-facing invariants and conventions
- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — data flow and module map (if applicable)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute
```

Full template with placeholders in `templates/README.template.md`.

### CLAUDE.md / AGENTS.md (for AI maintainers)

Two names, one purpose. Claude Code uses `CLAUDE.md`, some other agent frameworks use `AGENTS.md`. The content is identical; only the filename changes. Default to `CLAUDE.md` unless the operator says otherwise.

```markdown
# <Project name> — AI operator guide

Read this file first in every new session. It encodes the invariants.

## 🛑 Never do

1. <Hard rule>. Reason: <one sentence>.
2. <Hard rule>. Reason: <one sentence>.

## ✅ Always do

1. <Ritual>. Verification: `<command>`.
2. <Ritual>. Verification: `<command>`.

## 📋 Change type → file matrix

| What you want to change | Files to touch (in order) | Verification |
|---|---|---|
| Add a route | `routes/` → `handlers/` → test | `<command>` |
| Migrate schema | `migrations/` → `models/` → test | `<command>` |
| Add env var | `.env.example` → `config/` → README §env | `<command>` |

## 🔒 Invariants

| Invariant | Violation symptom |
|---|---|
| <Rule> | <What breaks if you violate it> |

## 🗺️ Repo map

<tree with one-line comments>

## 🚀 Deployment

<How the project deploys. One paragraph. Link to deeper docs.>

## 🎭 Recently decided (don't re-argue)

- <Decision>. Reason: <why>. Date: <when>.

## More

- [`README.md`](./README.md) — overview and quick start
```

Full template in `templates/CLAUDE.template.md`. Same content copies to `AGENTS.md` verbatim for non-Claude agent frameworks — just rename the file.

### Commit message

Format: conventional commits with Korean or English body, explicit "why" and "how verified."

```
<type>(<scope>): <subject in imperative, lowercase, no period>

<Body paragraph 1 — the motivation. Why did this change need to happen?
What problem does it fix or what capability does it add? Be specific.>

<Body paragraph 2 — the approach. Which files and which functions were
touched. Any non-obvious decisions go here. Anyone reading git blame in
six months should understand why this commit looks the way it does.>

## Verification
- <command 1 run, result>
- <command 2 run, result>

## Risks
- <One risk the reviewer should know about. Omit section if no risk.>
```

**Type** is one of: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ci`, `perf`, `style`, `build`. Use the one that matches the dominant change; don't invent new types.

**Scope** is the module or feature affected, in kebab-case.

**Subject** is under 72 characters, imperative (`add`, `fix`, `move`, not `added`/`adds`).

Full template in `templates/commit.template.md`.

### Pull request description

```markdown
## Summary

<1–3 sentences. What this PR does and why.>

## Changes

- <file or section> — <what changed, one line>
- <file or section> — <what changed, one line>

## Verification

| Check | Result |
|---|---|
| Typecheck | ✅ `<command>` |
| Lint | ✅ `<command>` |
| Tests | ✅ N/M passing (`<command>`) |
| Smoke | ✅ <local run check> |
| Call-site closure (if refactor) | ✅ <count before/after> |

## Risks

<Things the reviewer should specifically watch for. If none, say "none."
Be honest — reviewers appreciate flagged risks more than surprised risks.>

## For the reviewer / next AI session

<What to read first. Anything counter-intuitive. Any "I tried X, it didn't
work, so I used Y" notes.>

## After merge

- [ ] <action the reviewer or maintainer should take>
- [ ] <action, if any>
```

Full template in `templates/pr.template.md`.

## Things not to do

- **Don't write a welcome letter.** No "Welcome to <project>! We're so glad you're here."
- **Don't explain what git is.** The reader, human or AI, already knows.
- **Don't pad with history.** "This project was originally built in 2021 by Alice..." belongs in a separate `HISTORY.md` if anywhere.
- **Don't invent sections.** The schema above is the vocabulary. If a section doesn't fit, ask whether the information belongs in a different doc type.
- **Don't over-emoji.** A single emoji per heading is a structural marker. Ten emojis in a paragraph is noise.
- **Don't rewrite from scratch.** If a doc already exists, diff against it and preserve every concrete fact (file paths, env vars, numbers, personal names). Use the info-preservation procedure from `refactor-verify`'s references.
- **Don't format-shame existing docs.** If the operator prefers their existing README structure, keep it. Structure is a suggestion; information preservation is an invariant.

## When to call this skill vs just writing text yourself

Use this skill when:

- The operator asks for a new README, commit message, PR body, or AGENTS.md
- An existing doc is being rewritten for a new audience
- The current-session output needs to survive into future sessions

Don't use this skill when:

- A one-line comment is enough
- The operator just needs a quick explanation in chat
- The content is ephemeral (a debug note, a scratch plan)

## Sweep mode — read-only audit

When invoked from `/vibesubin` (the umbrella skill's parallel sweep), this skill runs in **read-only audit mode**. Do not write, edit, or create any documentation files. Do not touch README.md, CLAUDE.md, AGENTS.md, commit messages, or PR bodies.

Instead, produce a findings-only report:

- What docs currently exist (README, CLAUDE.md / AGENTS.md, CONTRIBUTING, ARCHITECTURE, changelogs) — list files with one-line condition assessments.
- What's missing for the AI-friendly doc schema (no CLAUDE.md, no env-var table, no verification commands, no invariants section).
- What's stale (docs claim a command that no longer works, paths that moved, env vars that were removed).
- What's ghostly (docs written in prose-only when a table would help, sections that add no invariants, "welcome to the project" padding).
- Stoplight verdict: 🟢 docs would survive a fresh AI session / 🟡 gaps the next session will trip over / 🔴 the next session would reverse-engineer the project from code because docs are missing or lying.
- A one-line "fix with" pointer indicating `/write-for-ai` will rewrite or fill in the gaps when invoked directly.

The operator reviews the sweep report and, if they want the fixes applied, invokes `/write-for-ai` directly — which then runs the full write/verify procedure.

How to tell: the task context from the umbrella will include a `sweep=read-only` marker or an explicit "produce findings only, do not edit" instruction. Obey it. If the operator invokes this skill by name, the full procedure applies and editing is expected.

## Hand-offs

- If rewriting a doc risks losing concrete facts → borrow the info-preservation check from `refactor-verify` (grep old doc's concrete terms, verify they appear in the new doc, or are deliberately dropped)
- If documenting CI/CD → coordinate with `setup-ci` to make sure commands in the README match the workflow file
- If documenting branches / config / env → coordinate with `manage-config-env` for the canonical defaults

## Details

The AI-friendly doc principles, section-by-section README structure, and commit/PR conventions are inlined in this SKILL.md rather than split into reference files. One readable file beats six fragmented ones.

Working templates in `templates/`:

- `templates/README.template.md` — full starter README with every section labeled
- `templates/CLAUDE.template.md` — AI-facing invariants doc. Same content works as `AGENTS.md` for non-Claude agent frameworks — copy and rename.
- `templates/commit.template.md` — conventional commit body with verification notes
- `templates/pr.template.md` — PR description with goal / changes / verification / risks
