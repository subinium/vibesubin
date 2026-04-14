---
name: vibesubin
description: The vibesubin command and vibe. Runs every skill in the plugin across a repository in parallel and synthesizes their findings into a single prioritized report. Invoke by name (/vibesubin) for a full sweep, or let it route a vague request to the right sub-skill when the operator isn't sure where to start. Read-only by default; fixes apply only after the operator approves items from the report.
when_to_use: Trigger on "/vibesubin", "use vibesubin", "run vibesubin on this repo", "full check", "audit my repo", "where do I start", "is my repo okay", "my repo is a mess", "vibe check", or when the operator's request is vague enough that routing to a single specialist isn't obvious.
context: fork
agent: general-purpose
---

# /vibesubin

`/vibesubin` is two things at once:

1. **A command** — one word that runs every skill in the pack across the current repo in parallel and returns a single prioritized report. One operator input, one AI output, full repo coverage.
2. **A vibe** — a meme-y shorthand for "take a look at my repo with the whole pack and tell me what's up." It's the thing you type when you want the full treatment without having to pick a skill.

Both meanings are intentional. The word doubles as a greeting, a command, and a self-description of what the operator is already doing ("vibing with AI on a codebase").

## ⚠ Incident fast-path — run this **before** anything else

Certain phrases mean "something just leaked" and need an immediate response, not a polite routing menu. If the operator's request contains any of these, skip the normal modes and jump directly to `audit-security` in incident mode:

- `.env` + any verb like `committed`, `pushed`, `leaked`, `exposed`
- `secret leaked`, `token leaked`, `key leaked`, `credential leaked`
- `api key committed`, `private key exposed`
- `accidentally pushed`, `accidentally committed`
- `breach`, `compromised`, `hacked`
- `revoke`, `rotate now`, `urgent security`
- `pushed my password`, `in git history`

For any of these, the response is:

1. **Acknowledge the urgency in one sentence.** "Got it — this is an incident. We're going to rotate first, ask questions second."
2. **Hand off to `audit-security`'s incident runbook immediately.** Do not ask what else the operator wants.
3. **Do not run the full parallel sweep.** The sweep is for tidy repos, not for active leaks. Time spent scanning is time the leaked credential is still live.

Only after the incident is contained — credentials rotated, history rewritten, collaborators notified — does it make sense to come back and run the normal sweep for related issues.

## Two modes (for non-incident requests)

### Mode 1 — Full sweep (the command)

When the operator types `/vibesubin` directly, or says "run vibesubin on this repo" / "full check" / "vibe check", run the **full parallel sweep**. Do not ask what to do first. Run everything, synthesize, report.

### Mode 2 — Router (the fallback)

When the operator gives a vague ask ("help", "where do I start", "my repo is a mess") without typing `/vibesubin` explicitly, fall back to the **router** below. Ask one short question, then hand off to the right specialist.

The two modes exist because different users need different entry points. The command mode is for "do everything"; the router mode is for "help me narrow down."

---

## Mode 1 — Full sweep procedure

### Step 1 — Confirm scope in one sentence

Before running, confirm once:

> *"Running the full vibesubin sweep on this repo. That's six checks in parallel — refactor safety, security, repo rot, docs, CI setup, and config/env/branch conventions. It'll take a couple of minutes and produce one prioritized report at the end. Sound good?"*

If the operator says yes, proceed. If they want to narrow the scope (one directory, one file, one area), adjust before launching.

### Step 2 — Launch the six specialists in parallel

Run all six sub-skills as **parallel task agents** (or parallel subagents, depending on the host framework). Do not serialize. The whole point of this command is that the operator gets results in minutes, not an hour.

Each specialist runs with **read-only scope** for this sweep — they produce findings, not fixes. Fixes are applied only after the operator reviews the synthesized report and approves next steps.

Parallel launch targets:

```
parallel {
  refactor-safely      → "Snapshot current state. Baseline tests, typecheck, lint.
                          Identify any recent refactor risk. Report: is the repo
                          in a green baseline, or already in a red state?"

  audit-security       → "Run the ten-category security sweep across the whole
                          repo. Triage every finding. Report: critical, high,
                          medium, false-positive counts."

  fight-repo-rot       → "Compute churn × complexity. List top 10 hotspots,
                          god files, dead code, hardcoded paths, stale TODOs,
                          dependency rot. Report: prioritized fix list."

  write-for-ai         → "Audit existing docs: README, CLAUDE.md/AGENTS.md,
                          recent commit messages, recent PR descriptions. Score
                          each against the AI-friendly schema. Report: what's
                          missing, what's stale, what to rewrite first."

  setup-ci             → "Inspect current CI/CD setup: .github/workflows,
                          .gitlab-ci.yml, or equivalent. What exists, what's
                          missing, what's broken. Report: current state +
                          concrete next-step recommendation."

  manage-config-env    → "Audit .env layout, .gitignore, dependency pinning,
                          branch strategy, directory structure, path portability.
                          Report: deviations from opinionated defaults."
}
```

Each specialist writes into the SKILL.md's own output format. No cross-contamination during the parallel phase.

### Step 3 — Synthesize into one report

When all six specialists return, merge their findings into a single prioritized report. The synthesis rules:

1. **Criticals first, across all categories.** A security critical beats a refactor medium beats a doc nit.
2. **Cross-skill evidence wins.** If three specialists independently flag the same file (e.g., `src/api/user.ts` is both a churn×complexity hotspot AND has a SQL injection AND has no tests), that file is top priority.
3. **Group by file, not by specialist.** The operator fixes files, not categories.
4. **Show the chain of causation.** If the security finding is downstream of the repo rot (complex file → missed validation), say so.
5. **One recommendation per file.** "Fix this by: <concrete next step, one sentence>." Link to the specialist that should handle the fix.

### Step 4 — Report format

```markdown
# /vibesubin sweep — <repo name> — <date>

## Vibe check

<One paragraph, warm tone, honest summary. "Your repo is in decent shape but
three things stand out..." or "There are four things I'd fix before you ship
the next release..." or "Honestly, this looks clean — here are two small
polish items if you have 20 minutes.">

## What ran

Six skills in parallel. Each one's full report is in the section below.

- refactor-safely:      <green | yellow | red> — <one-line summary>
- audit-security:       <green | yellow | red> — <one-line summary>
- fight-repo-rot:       <green | yellow | red> — <one-line summary>
- write-for-ai:         <green | yellow | red> — <one-line summary>
- setup-ci:             <green | yellow | red> — <one-line summary>
- manage-config-env:    <green | yellow | red> — <one-line summary>

## Prioritized fix list (top 10)

| # | File / area | What | Severity | Fix with | Est. time |
|---|---|---|---|---|---|
| 1 | src/api/user.ts:187 | SQL injection in `get_user_by_email` | CRITICAL | audit-security → refactor-safely | 20 min |
| 2 | src/api/user.ts (whole file) | Hotspot: 870 LOC, 18 CCN, 47 commits / 6mo | HIGH | refactor-safely | 2–3 hours |
| 3 | .env committed in git history | Secret exposure | CRITICAL | audit-security → manage-config-env | 30 min + rotate |
| ... |

## By specialist

### refactor-safely
<full specialist output>

### audit-security
<full specialist output>

...

## Recommended order of operations

1. **Fix #1 first** — it's a critical security issue and takes 20 minutes
2. **Rotate exposed secrets in #3** — concurrently, since no code change needed
3. **Then tackle #2** — the hotspot — because fixing #1 there ties into the split
4. ...

## What I did NOT do

This sweep is read-only. No files were modified. No commits were made.
Approve the fix list and I'll hand off each item to the right specialist.

## Vibe check — verdict

<One-sentence verdict. "Ship it after #1 and #3." or "Don't ship until all
criticals are resolved." or "This is honestly fine; ignore the noise below
the fold.">
```

### Meme elements (keep light, don't overdo)

The "vibe" part is real but subtle. Specific to-dos:

- **Tone**: warm, first-person, a little casual. "Honestly, this looks fine." / "Yeah, that SQL bit is spicy." / "Your docs are ghosts."
- **Section header 'Vibe check'** is the one place the meme is explicit. Everywhere else, normal professional language.
- **No emojis beyond structural markers.** No 🚀🔥💯. The meme is in the phrasing, not the decoration.
- **Green / yellow / red light indicators** per specialist — familiar stoplight metaphor, readable at a glance.
- **"What I did NOT do" section** is a subtle meme referencing LLMs that silently do things. vibesubin is explicit about staying read-only in sweep mode.
- **The closing "verdict" line** is the operator's favorite part — one sentence, direct, honest. Never hedge.

Do not push the meme further. Adding more "vibe" language makes the report feel juvenile. One section-header joke is enough.

---

## Mode 2 — Router (when the operator didn't type /vibesubin explicitly)

If the operator's request is vague but they didn't invoke the command, route to a specific specialist instead of launching the full sweep. Running all six is expensive; don't do it unless the operator really wants it.

### Routing decision tree

```
User request
│
├── Contains "refactor" / "move" / "rename" / "split" / "is this working"
│   → refactor-safely
│
├── Contains "secure" / "safe" / "leak" / "vulnerability" / "audit"
│   → audit-security
│
├── Contains "clean up" / "rotting" / "dead code" / "mess" / "hotspot"
│   → fight-repo-rot
│
├── Contains "README" / "document" / "commit message" / "PR" / "CLAUDE.md"
│   → write-for-ai
│
├── Contains "CI" / "deploy" / "GitHub Actions" / "workflow" / "automate deploy"
│   → setup-ci
│
├── Contains ".env" / "secret" / "branch" / "main or dev" / "config" / "gitignore"
│   → manage-config-env
│
├── Contains "full check" / "run vibesubin" / "vibe check" / "everything"
│   → MODE 1 (full sweep)
│
└── None of the above — ambiguous
    → Ask one question: "What's bothering you most right now — the code is
      hard to change, something feels unsafe, your repo is messy, your docs
      are stale, deploy is manual, or something structural (config / branches
      / env)?"
```

### Router examples

**User:** *"help"* → Ambiguous. Ask the one question above.

**User:** *"can you look at this file"* → Too broad. Ask: "What do you want me to look for — is it broken, unsafe, messy, or something else?"

**User:** *"my whole repo is a mess and I don't know where to start"* → This is the command mode signal even without `/vibesubin`. Offer: *"I can run the full vibesubin sweep — all six skills in parallel, one prioritized report at the end. Want me to?"*

**User:** *"I pushed my .env to github"* → Immediate `audit-security` + `manage-config-env` tandem. Don't route through the umbrella; the urgency is specific.

---

## Things not to do

- **Don't run mode 1 without confirming.** The full sweep takes minutes and produces a lot of output. Confirm scope first.
- **Don't run mode 1 serially.** The whole point is parallelism. If the host framework doesn't support parallel task agents, warn the operator that it'll be slower and proceed sequentially.
- **Don't have mode 1 make changes.** It's read-only. The operator approves the fix list; the specialists apply fixes.
- **Don't force mode 1 on a specific request.** If the operator clearly wants one thing (`"fix this SQL injection"`), route to the specialist. Don't up-sell the full sweep.
- **Don't repeat the full specialist reports in the synthesis.** The top of the report is a summary; the details go below the fold. Operators skim.
- **Don't over-meme.** The vibe is in one section header and the tone of the verdict. Not in every line.

## Integration notes

- The six specialists' output formats should be stable enough that the synthesis step doesn't have to reverse-engineer them. If a specialist's format changes, update the synthesis template in this SKILL.md.
- If a specialist fails (can't run, errors out), report its failure in the "What ran" section and continue with the others. Do not block the whole sweep on one failed specialist.
- If the repo is too large for a single sweep (e.g., > 10k files), mode 1 should partition and run per-subdirectory, then merge. Warn the operator about the partitioning first.

## When this skill is not the right answer

If the operator has a specific, narrow task, don't route through vibesubin at all — let the matching specialist fire directly. The umbrella is for exploration and full sweeps, not for tasks that already have an obvious home.

---

*vibesubin is the thing you type when you want your AI to just **look**. Not to fix, not to explain, not to lecture — just to look and tell you what it sees.*
