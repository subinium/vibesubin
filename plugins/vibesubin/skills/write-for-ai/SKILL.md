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

## State assumptions — before acting

Before starting the procedure, write an explicit Assumptions block. Don't pick silently between interpretations; surface the choice. If any assumption is wrong or ambiguous, pause and ask — do not proceed on a guess.

Required block:

```
Assumptions:
- Target artifact:   <README | CLAUDE.md | AGENTS.md | commit message | PR body | changelog | architecture doc>
- Audience:          <AI primary (default) | humans primary (explicit request)>
- Edit mode:         <new doc | surgical edit (preserve voice + structure) | full rewrite (explicit operator approval required)>
- Verifiable claims: <list of commands the doc will cite — each must actually run before writing>
```

Typical items for this skill:

- The target artifact (README / CLAUDE.md / commit / PR body / AGENTS.md)
- The verification commands the repo actually supports — every capability claim requires one
- The audience (AI is primary, humans are secondary; reverse only on explicit request)

Stop-and-ask triggers:

- Operator requests marketing copy, superlatives, or unbacked claims — refuse per Objectivity section, explain why
- A verification command does not exist for a claim the operator asked to include — ask whether to drop the claim or add the verification

Silent picks are the most common failure mode: the skill runs, produces plausible output, and the operator doesn't notice the wrong interpretation was chosen. The Assumptions block is cheap insurance.

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

## Objectivity — no exaggeration, no marketing

Every sentence written into a document must be either a verifiable fact or an opinion that is clearly labeled as one. LLM-generated docs drift toward enthusiastic framing ("fast", "best-in-class", "production-ready") because LLMs were trained on marketing copy and the enthusiastic version is the higher-probability next token. That drift is a bug in this pack.

The rules below are enforced on every artifact this skill produces. A violation is not a style preference; it's a failure to ship.

1. **No unbacked adjectives.** *"Fast"*, *"lightweight"*, *"robust"*, *"production-ready"*, *"scalable"*, *"best-in-class"*, *"seamless"*, *"intuitive"*, *"blazing"*, *"modern"* are marketing words. Delete them or back them immediately with a measurement, a link, or a date. A library is not *"fast"*; it's *"3.2× faster than the baseline on <benchmark>"*. A framework is not *"production-ready"*; it's *"running in production at <example> since <date>"*.

2. **No superlatives without comparison.** *"The best"*, *"the most"*, *"the only"*, *"the simplest"*, *"the cleanest"* — if the comparison is not explicitly in the text, delete the superlative. *"Simple"* with a 3-line code example is fine; *"the simplest possible"* with nothing to compare against is marketing.

3. **No marketing metaphors.** *"Battle-tested"* → *"running in production since YYYY-MM"* or delete. *"Zero-config"* → explicit list of defaults. *"Plug and play"* → concrete install steps. *"Out of the box"* → name the box.

4. **No weasel hedging either.** The opposite failure mode is prose that commits to nothing: *"may work"*, *"can be useful for"*, *"might help"*, *"generally well-suited"*, *"depending on your needs"*, *"in some cases"*. Replace with a concrete yes/no and the condition, or delete.

5. **Every capability claim has a verification command.** If the doc says *"this passes type check"*, the exact command that verifies it is on the next line. If the doc says *"works on Python 3.11+"*, the CI matrix or a `python_requires` entry backs it up. If neither exists, drop the claim.

6. **Numbers are specific or absent.** *"About 500 lines"* is fine. *"A few hundred lines"* is not. *"Roughly 10,000 users"* is fine if you cite the source; *"many users"* is not.

7. **Status flags are load-bearing.** *"early"*, *"stable"*, *"deprecated"*, *"experimental"* go in the header of every doc and they commit the writer to a maturity claim. Never default to *"stable"* to sound confident — if you're not sure, *"early"* is the honest answer.

8. **No self-congratulation.** The doc does not compliment the project it describes. No *"cleanly written"*, no *"elegant API"*, no *"beautiful code"*. Those are the reader's call, not the writer's.

This rule applies to the artifact the skill emits, not to how the operator ends up writing their own commits later. When the operator asks for a README and the repo genuinely is fast, the doc cites the benchmark; when the operator asks for a README and there is no benchmark, the doc does not say *"fast"* at all.

## Mandatory self-review before emitting anything

This pack is published as open source. Do a final sanity pass on every artifact before you show it to the operator or write it to disk.

Checklist:

1. **Repo-specific, not generic** — the commands, framework names, and file paths match the actual repo markers (`pnpm-lock.yaml`, `uv.lock`, `Cargo.toml`, `Gemfile`, `composer.json`, etc.)
2. **No fabricated facts** — every path, command, env var, branch name, and workflow filename exists or is clearly labeled as a placeholder
3. **No leak surface** — no real secrets, no local absolute paths, no internal hostnames, no customer data
4. **No weird public-facing prose** — no memes in formal docs, no chatty filler, no wording that looks machine-generated for its own sake
5. **Verification claims are real** — if the doc says "tests pass" or "typecheck is clean," there is a concrete command next to it
6. **Objective tone** — every rule from the Objectivity section above has been applied: no unbacked adjectives, no superlatives without comparison, no marketing metaphors, no weasel hedging, no self-congratulation. If you wrote *"fast"*, either there's a benchmark cited or the word is gone.

If any of the six fail, fix the artifact before returning it. Open-source docs get screenshotted and quoted out of context; assume zero forgiveness.

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
- **Don't add features the operator did not request — and especially don't silently rewrite an existing doc when they asked for a surgical edit.** The #1 failure mode this skill fights is a rewrite that loses information the operator didn't know was there. When asked to update a section, update that section; note any adjacent issues in the final output as hand-off suggestions.

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

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"* / *"厳しめ"*), switch output rules on both the doc audit and the direct-invocation report:

- **Lead with the worst doc failure.** First line is the single most important gap — *"this repo has no `CLAUDE.md`, so every new AI session starts blind"*, *"the README still documents `npm install` but the repo is on pnpm"*, *"the env-var table is 40% stale — `STRIPE_KEY` and `SENTRY_DSN` are missing"*. No preamble.
- **No *"ghost docs"* euphemisms.** Balanced mode says *"docs are a bit thin in places"*. Harsh mode says *"the next AI session will reverse-engineer this project from code because the docs are lying about which commands work."*
- **Marketing violations get called out by line.** Every *"fast"*, *"robust"*, *"production-ready"*, *"best-in-class"* that slipped into the existing doc gets a line-level flag: *"`README.md:14` claims `production-ready` with no production example — either cite a user, drop the claim, or downgrade the status to `early`."*
- **Unverified claims are framed as lies-by-omission.** *"The README says the tests pass; there is no test command and no CI. Either add the command or delete the claim."*
- **Doc rewrites get info-loss warnings in the verdict.** *"This rewrite drops 7 env-var entries from the old README. Either reinstate them or explicitly document why they were removed."*
- **No *"mostly good with some polish"* closures when any doc is factually wrong.** Wrong commands are not polish. Missing invariants are not polish. Outdated paths are not polish.

Harsh mode does not invent missing docs, exaggerate staleness, or become rude. Every harsh statement must cite the same file, line, or git-log evidence the balanced version would cite. The change is framing, not substance.

## Layperson mode — plain-language translation

When the task context contains `explain=layperson` (from `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"explain like I'm non-technical"*, *"非開発者でも分かるように"*, *"用通俗的话解释"*), add a plain-language layer to every finding this skill emits. Combines freely with `tone=harsh`. Full rules at `/plugins/vibesubin/skills/vibesubin/references/layperson-translation.md`.

### Three dimensions per finding

Every finding gets three questions answered in plain language, in the operator's language (Korean / English / Japanese / Chinese):

- **왜 이것을 해야 하나요? / Why should you do this?** — *"AI는 매 세션 맨땅에서 당신의 레포를 다시 읽어요. README·CLAUDE.md·커밋 메시지가 비어 있거나 스타일이 프로즈에 가까우면, 다음 세션의 AI가 파일 구조·규칙·'이건 건드리지 마'를 알 방법이 없습니다."*
- **왜 중요한 작업인가요? / Why is it an important task?** — *"문서가 정적이면 다음 AI 세션이 '이게 뭐하는 프로젝트지?'부터 시작합니다. 결과: 이미 있는 기능을 다시 만들거나, 이미 정한 규칙을 어기고 리팩터를 진행합니다."*
- **그래서 무엇을 하나요? / So what gets done?** — *"README·CLAUDE.md·커밋·PR 본문을 AI가 읽기 좋은 구조(테이블 > 산문, 명시적 파일 경로, '하지 마' 규칙 선언)로 씁니다. 쓰기 전에 레포를 먼저 읽고, 쓴 내용 중 사실이 아닌 문장이 없는지 검증합니다."*

### Severity translation

- 🔴 missing → *"문서 자체가 없음 — 다음 세션 AI가 맨땅에서 추측 시작"*
- 🟡 stale → *"있는데 현실과 달라요 — AI가 거짓 정보 기반으로 작업"*
- 👻 ghost → *"과거에 있었는데 조용히 사라짐 — env 변수나 스크립트 섹션이 증발"*
- 🟢 healthy → *"충분함 — 새 세션이 바로 일 시작 가능"*

### Box format

Wrap each finding in the box format from the shared reference. Header uses urgency phrase and the finding number. Footer names the hand-off skill.

### What does NOT change

Findings, counts, file:line references, evidence, and severity are identical to balanced/harsh output. Only the wrapping and dimension annotations are added.

## Hand-offs

- If rewriting a doc risks losing concrete facts → borrow the info-preservation check from `refactor-verify` (grep old doc's concrete terms, verify they appear in the new doc, or are deliberately dropped)
- If documenting CI/CD → coordinate with `setup-ci` to make sure commands in the README match the workflow file
- If documenting secrets, `.env`, `.gitignore`, or anything in the env-var table → coordinate with `manage-secrets-env` for the canonical defaults and the lifecycle wording
- If documenting branch strategy, directory layout, dependency pinning, or path portability → coordinate with `project-conventions`

## Details

The AI-friendly doc principles, section-by-section README structure, and commit/PR conventions are inlined in this SKILL.md rather than split into reference files. One readable file beats six fragmented ones.

Working templates in `templates/`:

- `templates/README.template.md` — full starter README with every section labeled
- `templates/CLAUDE.template.md` — AI-facing invariants doc. Same content works as `AGENTS.md` for non-Claude agent frameworks — copy and rename.
- `templates/commit.template.md` — conventional commit body with verification notes
- `templates/pr.template.md` — PR description with goal / changes / verification / risks
