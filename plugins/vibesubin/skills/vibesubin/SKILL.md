---
name: vibesubin
description: The vibesubin command and vibe. Runs every code-hygiene specialist in the plugin across a repository in parallel and synthesizes their findings into a single prioritized report. Process skills like `/ship-cycle` and host-specific wrappers like `/codex-fix` are direct-call only and not part of the sweep. Invoke by name (/vibesubin) for a full sweep, or let it route a vague request to the right sub-skill when the operator isn't sure where to start. Read-only by default; fixes apply only after the operator approves items from the report. Two optional output modifiers — `tone=harsh` for direct, no-hedging framing, and `explain=layperson` for plain-language translation (3-dimension box format with "왜 해야 / 왜 중요 / 무엇을 할지" per finding); the two combine. When two specialists give contradictory advice on the same file, the umbrella emits a skill-conflict block (gap / reason / basis per side) instead of silently picking one.
mutates: []
when_to_use: Trigger on "/vibesubin", "use vibesubin", "run vibesubin on this repo", "full check", "audit my repo", "where do I start", "is my repo okay", "my repo is a mess", "vibe check", or when the operator's request is vague enough that routing to a single specialist isn't obvious.
context: fork
agent: general-purpose
---

# /vibesubin

`/vibesubin` is two things at once:

1. **A command** — one word that runs every code-hygiene specialist in the pack across the current repo in parallel and returns a single prioritized report. One operator input, one AI output, full repo coverage. Process skills like `/ship-cycle` and host-specific wrappers like `/codex-fix` are direct-call only and not part of the sweep.
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

## Harsh mode — no hedging

Every sweep runs in one of two tones. The default is **balanced** — honest but warm, direct but not cold. Operators opt in to **harsh** when they want a review that refuses to soften anything.

### When to switch to harsh mode

Any of these signals activates harsh mode:

- `/vibesubin harsh` or `/vibesubin spicy`
- *"brutal review"*, *"harsh review"*, *"harsh mode"*
- *"don't sugarcoat"*, *"don't hold back"*, *"no hedging"*, *"give it to me straight"*
- *"매운 맛"* / *"더 세게 피드백"* / *"봐주지 말고"*
- *"厳しめ"* / *"遠慮なく"* / *"手加減せずに"*
- *"严厉模式"* / *"别嘴软"* / *"说狠一点"*

The explicit Korean / Japanese / Chinese phrases are there on purpose — non-English operators ask for harsh tone in their own language.

### What changes in harsh mode

1. **Marker propagation.** Every specialist task description is prefixed with `tone=harsh` in addition to `sweep=read-only`. Specialists check for this marker and switch to their own harsh-mode output rules.
2. **No hedging.** Drop *"probably"*, *"might be"*, *"consider"*, *"you could"*, *"it may be worth"*. Replace with direct subject-verb sentences. *"Fix this"*, not *"you might want to fix this"*.
3. **No *"looks fine"* closures at severity above clean.** If any finding is HIGH or CRITICAL, the verdict line cannot end on a positive note. *"Two polish items"* becomes *"three fixes blocking a clean bill"*.
4. **Worst-first ranking, no tails.** The top-10 list is ordered strictly by blast radius. No *"also consider"* footer, no *"nice-to-haves"* at the bottom.
5. **Verdict line is direct.** *"Do not ship"*, *"Ship only after items 1–3"*, *"This is not ready"*. No *"solid with a few things to watch"*.
6. **Vibe check paragraph leads with the worst finding.** *"This repo will break within three releases if you don't fix items 1–3"* rather than *"decent mid-stage project with two things that stand out"*.

Harsh mode is **not** about being rude, exaggerating, or inventing findings. It is about refusing to soften the framing when the findings are real. Every harsh statement must still be backed by evidence — the same evidence the balanced version would cite.

### What does NOT change in harsh mode

- Findings themselves. Same metrics, same counts, same confidence tags.
- Read-only behavior. Harsh mode is still a read-only sweep.
- Professional tone. Harsh ≠ unprofessional. No profanity, no insults toward the operator, no personal attacks on prior contributors.
- Factual accuracy. If a file is actually fine, the harsh report says it's fine — it just doesn't pad the report with filler praise.

### When *not* to use harsh mode

- When the operator is clearly new to coding. Harsh mode is for operators who explicitly want calibration, not for intimidating beginners.
- When the repo is already clean. A harsh verdict on a clean repo reads as rude, not honest.
- When the operator didn't ask for it. Never default to harsh.

---

## Layperson mode — plain-language translation

Balanced and harsh modes both assume the operator reads technical findings fluently. Layperson mode (`explain=layperson`) adds a plain-language layer for non-developer vibe-coders — a 3-dimension box format per finding, jargon glossary, severity-to-urgency translation. Opt-in only; never defaults on. Combines freely with `tone=harsh`. Full rules at `references/layperson-translation.md`.

### When to switch to layperson mode

Any of these signals activates it:

- `/vibesubin explain`, `/vibesubin easy`, `/vibesubin layperson`
- *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"비개발자 모드로"*
- *"explain like I'm non-technical"*, *"initiate easy mode"*, *"no jargon"*
- *"非開発者でも分かるように"*, *"やさしい言葉で"*
- *"用通俗的话解释"*, *"给外行看的版本"*

### What changes in layperson mode

1. **Marker propagation.** Every specialist task description is prefixed with `explain=layperson` alongside `sweep=read-only`. Specialists check for it and add a 3-dimension block to each finding. Stacks with `tone=harsh`.
2. **3-dimension block per finding.** Every finding gets three questions answered in plain language:
   - **왜 이것을 해야 하나요? / Why should you do this?** — human-impact framing (who gets hurt, when, how).
   - **왜 중요한 작업인가요? / Why is this an important task?** — severity translation + concrete consequence timeline.
   - **그래서 무엇을 하나요? / So what will be done?** — concrete action in plain language; any unavoidable term defined in parens.
3. **Severity translation.** CRITICAL → "지금 당장 (ship하기 전에 필수)"; HIGH → "이번 주 안에"; MEDIUM → "다음 릴리즈 전까지"; LOW → "시간 날 때 정리". Plain-language phrase replaces the raw label in finding headers.
4. **Pretty box format** around each finding (box-drawing characters framing the 3 dimensions + file + which skill will fix it). Makes findings scannable for operators who skip technical detail.
5. **Jargon glossary** inline. "SQL injection", "dependency", "lint", "hotspot", "CI", "rebase", "force push", "semver", "lockfile" get a one-line definition on first use in the report.

### What does NOT change in layperson mode

- Findings themselves — same files, same line numbers, same counts, same evidence.
- Read-only behavior.
- Accuracy — plain language is never imprecise. "SQL injection" becomes "공격자가 비밀번호 없이도 사용자 데이터를 읽을 수 있는 버그" — not "a little security thing".
- Severity — never softened beyond the underlying finding.

### When *not* to use layperson mode

- Operator is a developer and asked for the technical report.
- Repo is already clean. Wrapping "nothing to fix" in plain-language framing reads condescending; emit a one-line clean result instead.
- Operator explicitly asked for jargon ("show me the CVEs", "give me the raw findings"). Respect the override.

---

## Skill conflicts — gap, reason, basis

Sometimes two specialists give contradictory advice on the same file — refactor-verify says "pause until 4-check passes" while unify-design says "consolidate now"; fight-repo-rot says "remove this dep" while project-conventions says "don't prune manually". Today the umbrella would silently pick one or bury the disagreement; now it surfaces the conflict explicitly.

When a catalog conflict pair matches two specialists' recommendations on the same path, the umbrella emits a `⚠ Skill conflict` block directly under the affected file in the synthesized report. The block shows both specialists' recommendation, reason, and evidence basis in full — the operator is the tie-breaker, not the umbrella.

Full catalog (four seeded pairs: refactor-verify↔audit-security sequencing, unify-design↔refactor-verify consolidation hand-off, fight-repo-rot↔project-conventions dead deps, manage-secrets-env↔audit-security tracked `.env`), decision rule (hand-off vs. true conflict), and output shape at `references/skill-conflicts.md`.

Layperson mode adds one extra line per conflict block: *"쉽게 말해서 / In plain words: 두 스킬이 다른 걸 하라고 해요. A는 <짧은 이유>, B는 <짧은 이유>. 당신이 골라야 합니다."*

---

## Mode 1 — Full sweep procedure

### Step 1 — Confirm scope in one sentence

Before running, confirm once:

> *"Running the full vibesubin sweep on this repo. That's nine checks in parallel — refactor safety, security, repo rot, docs, CI setup, secrets/env, project conventions, repo bloat, and design unification. Read-only — nothing gets edited until you approve items from the report. Sound good?"*

If the operator says yes, proceed. If they want to narrow the scope (one directory, one file, one area), adjust before launching.

### Step 2 — Launch the nine specialists in parallel, all in read-only mode

Run all nine sub-skills as **parallel task agents** (or parallel subagents, depending on the host framework). Do not serialize. Parallelism is load-bearing — sequential execution defeats the whole purpose of the command.

**Read-only mode is enforced by the launch instruction itself.** Every specialist task MUST begin with the exact token `sweep=read-only` followed by "produce findings only, do not edit any files, do not run lifecycle workflows." Each specialist has a matching "Sweep mode — read-only audit" section in its SKILL.md that checks for this marker and switches to audit-only output. If a specialist does not see the marker, it will default to its full edit-capable behavior, which is incorrect for a sweep.

Three specialists (`fight-repo-rot`, `audit-security`, `manage-assets`) are pure-diagnosis by default and edit nothing regardless of the marker. The other six (`refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design`) rely on this marker to stay read-only. Do not launch any of them without it.

**Sweep contract enforcement (frontmatter check).** Before adding a worker to the parallel launch block, read the worker's `SKILL.md` frontmatter `mutates` field. If `external` appears in the list, the worker is direct-call only and **must not** participate in the sweep — refuse and skip silently. Today this excludes `codex-fix` and `ship-cycle`. The check is cheap (one read of frontmatter), and protects the sweep's read-only invariant from a future worker that violates it without updating this launch block. `validate_skills.py` also enforces this contract, but the umbrella reads it at runtime so the protection holds even on hosts without the validator wired in.

Parallel launch targets (the `sweep=read-only` prefix is mandatory — copy it into every task description verbatim):

```
parallel {
  refactor-verify      → "sweep=read-only — produce findings only, do not edit
                          any files, do not plan a dependency tree, do not run
                          the 6-step procedure. Snapshot baseline state (tests,
                          typecheck, lint). Report whether the repo is in a
                          green baseline ready for refactors, or already red."

  audit-security       → "sweep=read-only — produce findings only. Run the
                          ten-category security sweep. Triage every finding.
                          Report critical / high / medium / false-positive counts."

  fight-repo-rot       → "sweep=read-only — produce diagnosis only, never edit.
                          Run the full dead-code scan with HIGH/MEDIUM/LOW
                          confidence tagging. Also report god files, hotspots,
                          hardcoded paths, stale TODOs, dependency rot. Include
                          the hand-off summary."

  write-for-ai         → "sweep=read-only — produce findings only, do not edit
                          or create any documentation files. Audit existing docs
                          (README, CLAUDE.md/AGENTS.md, recent commits and PRs)
                          against the AI-friendly schema. Report gaps, stale
                          sections, and the stoplight verdict."

  setup-ci             → "sweep=read-only — produce findings only, do not
                          scaffold any workflow files, do not write to
                          .github/workflows. Inspect the current CI/CD setup.
                          Report what exists, what's missing, what's broken,
                          with the stoplight verdict."

  manage-secrets-env   → "sweep=read-only — produce findings only, do not
                          scaffold or edit any config files, do not run any
                          lifecycle workflow (rotate/remove/migrate/provision).
                          Audit four-bucket placement, .env drift, secret-shaped
                          .gitignore coverage, tracked-secret files. Report
                          deviations with stoplight. Any tracked secret is an
                          immediate hand-off to audit-security."

  project-conventions  → "sweep=read-only — produce findings only, do not
                          scaffold or edit any files. Audit branch strategy
                          vs GitHub Flow, dependency pinning and lockfile
                          presence, directory layout smells, hardcoded absolute
                          paths and portability bugs. Report deviations with
                          stoplight."

  manage-assets        → "sweep=read-only — produce diagnosis only, never edit.
                          Scan for large files in the working tree (>10 MB),
                          large blobs in git history, LFS migration candidates,
                          asset-directory growth, duplicate binaries. Report
                          top offenders with size, severity, and hand-off."

  unify-design         → "sweep=read-only — produce findings only, do not
                          scaffold any tokens file, do not edit any component.
                          Detect the framework (Tailwind v3/v4, CSS Modules,
                          styled-components, MUI, Chakra, vanilla), identify
                          the BI source of truth (or flag its absence), audit
                          for hardcoded hex/rgb, arbitrary Tailwind values,
                          magic px/rem numbers, duplicate Button/Card/Nav/Logo
                          components. Report drift by file with hotspots."
}
```

Each specialist writes into its own SKILL.md output format, constrained to read-only. No cross-contamination during the parallel phase.

**If harsh mode is active**, prepend `tone=harsh` to every specialist task description above, before `sweep=read-only`. Example for `fight-repo-rot`: *"tone=harsh, sweep=read-only — produce diagnosis only, never edit. Apply harsh-mode output rules..."*. Every specialist checks for this marker and switches its output tone accordingly.

**If layperson mode is active**, additionally prepend `explain=layperson` to every specialist task description. Example combined: *"tone=harsh, explain=layperson, sweep=read-only — produce diagnosis only, never edit. Apply harsh-mode framing AND the 3-dimension plain-language block per finding; box-format each finding per `references/layperson-translation.md`."*. Markers stack; order is `tone`, `explain`, `sweep`.

### Step 3 — Synthesize into one report

When all nine specialists return, merge their findings into a single prioritized report. The synthesis rules:

1. **Criticals first, across all categories.** A security critical beats a refactor medium beats a doc nit.
2. **Cross-skill evidence wins.** If three specialists independently flag the same file (e.g., `src/api/user.ts` is both a churn×complexity hotspot AND has a SQL injection AND has no tests), that file is top priority.
3. **Group by file, not by specialist.** The operator fixes files, not categories.
4. **Show the chain of causation.** If the security finding is downstream of the repo rot (complex file → missed validation), say so.
5. **One recommendation per file.** "Fix this by: <concrete next step, one sentence>." Link to the specialist that should handle the fix.
6. **Check for skill conflicts.** Before emitting the per-file recommendation, consult `references/skill-conflicts.md`. If two specialists' advice on the same path matches a catalog entry OR if one specialist's recommendation negates another's, emit a `⚠ Skill conflict` block in the shape specified there — gap, reason, basis per side, with an operator-decides recommendation. Do not resolve silently.
7. **Apply layperson layer if marker active.** When `explain=layperson` is on, wrap each finding in the box format from `references/layperson-translation.md` and add the 3-dimension block (왜 해야 / 왜 중요 / 무엇을 할지) with severity-to-urgency translation. Findings, counts, and evidence stay identical.

### Step 4 — Report format

```markdown
# /vibesubin sweep — <repo name> — <date>

## Vibe check

<One paragraph, warm tone, honest summary. "Your repo is in decent shape but
three things stand out..." or "There are four things I'd fix before you ship
the next release..." or "Honestly, this looks clean — here are two small
polish items.">

## What ran

Nine skills in parallel. Each one's full report is in the section below.

- refactor-verify:      <green | yellow | red> — <one-line summary>
- audit-security:       <green | yellow | red> — <one-line summary>
- fight-repo-rot:       <green | yellow | red> — <one-line summary>
- write-for-ai:         <green | yellow | red> — <one-line summary>
- setup-ci:             <green | yellow | red> — <one-line summary>
- manage-secrets-env:   <green | yellow | red> — <one-line summary>
- project-conventions:  <green | yellow | red> — <one-line summary>
- manage-assets:        <green | yellow | red> — <one-line summary>
- unify-design:         <green | yellow | red> — <one-line summary>

## Prioritized fix list (top 10)

Size bucket: **S** = quick win (single file, under an hour), **M** = multi-file or careful (rest of a day), **L** = multi-session (refactor, coordinated change, history rewrite).

| # | File / area | What | Severity | Fix with | Size |
|---|---|---|---|---|---|
| 1 | src/api/user.ts:187 | SQL injection in `get_user_by_email` | CRITICAL | audit-security → refactor-verify | S |
| 2 | src/api/user.ts (whole file) | Hotspot: 870 LOC, 18 CCN, 47 commits / 6mo | HIGH | refactor-verify | L |
| 3 | .env committed in git history | Secret exposure | CRITICAL | audit-security → manage-secrets-env | M |
| ... |

## Skill conflicts (if any fired)

⚠ Skill conflict — src/api/user.ts : (whole file)

Two specialists disagree on what to do here.

├─ Specialist A — refactor-verify
│  Recommends: refactor first, then re-run audit-security on the result
│  Reason: structural-first — auditing the old shape wastes effort
│  Basis: refactor-verify SKILL.md §"Security-sensitive changes"
│
├─ Specialist B — audit-security
│  Recommends: audit first, then refactor the fix with verification
│  Reason: exploitability-first — a refactor that preserves a vuln is not safer
│  Basis: incident runbook — containment before structural work
│
└─ Recommendation: sequence depends on liveness of the vulnerability
   Operator decides:
     • ACTIVE vuln → audit-security first, then refactor
     • LATENT vuln → refactor-verify first, then re-audit

(Full catalog + decision rule: `references/skill-conflicts.md`. Omit this section when no conflicts fired.)

## By specialist

### refactor-verify
<full specialist output>

### audit-security
<full specialist output>

...

## Recommended order of operations

1. **Fix #1 first** — it's a critical security issue and it's a quick win (size S)
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

### Harsh-mode report variant

If the sweep was launched in harsh mode, the report structure is the same but the tone changes at three specific places:

**Vibe check paragraph (harsh):** leads with the worst finding in one sentence, no warm-up. *"This repo ships a SQL injection, three confirmed-dead god files, and an .env in git history. Fix those before anything else; everything below is secondary."* No *"decent shape"* openings. No *"a few things"* softening.

**Prioritized fix list (harsh):** strictly worst-first. No *"nice-to-have"* tail. No items below severity MEDIUM. If there are fewer than 10 items above MEDIUM, the list is shorter than 10 — don't pad to reach the top-10 quota.

**Verdict line (harsh):** direct, no hedge. Acceptable forms:

- *"Do not ship. Fix items 1–N first."*
- *"Ship only after criticals rotate and hotspots split."*
- *"This repo is not ready for open-source release. Here's the list."*
- *"Clean. Ship it."* (only when the report has zero findings above 🟢)

Never *"solid with a few things to watch"*, never *"mostly fine"*, never *"some polish items"* when harsh mode is active.

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

If the operator's request is vague but they didn't invoke the command, route to a specific specialist instead of launching the full sweep. Running the full sweep is expensive; don't do it unless the operator really wants it.

### Routing decision tree

```
User request
│
├── Contains "refactor" / "move" / "rename" / "split" / "is this working"
│   → refactor-verify
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
├── Contains ".env" / "secret" / "rotate" / "gitignore" / "api key"
│   → manage-secrets-env
│
├── Contains "branch" / "main or dev" / "dependency" / "dependabot" / "folder structure" / "hardcoded path"
│   → project-conventions
│
├── Contains "repo is huge" / "big files" / "LFS" / "binary in git" / "bloat"
│   → manage-assets
│
├── Contains "design system" / "unify" / "match the brand" / "too many hardcoded"
│      / "why do these pages look different" / "extract to tokens"
│      / "브랜드 일관성" / "디자인 통일"
│   → unify-design
│
├── Contains "codex 돌려서 고쳐" / "codex fix" / "rescue 돌리고 수정"
│      / "run codex and fix" / "codex로 한번 검사" / "codex driven fix"
│   → codex-fix (Claude Code + Codex plugin only; graceful one-line pass on every other host)
│
├── Contains "resolve these findings" / "fix this review" / "리뷰 사항 처리"
│      / "이 리뷰 고쳐줘" / pasted review reports with file:line references
│   → refactor-verify (review-driven fix mode — portable, any review source)
│
├── Contains "plan a release" / "cut a release" / "릴리즈 계획"
│      / "이슈로 남기고 처리" / "make issues for this" / "bundle into issues"
│      / "turn sweep findings into issues" / "issue-driven" / "이슈 드리븐"
│      / "roadmap for 0.N.0" / "ship cycle" / "tag and release"
│      / "release notes 써줘" / "generate changelog from PRs"
│      / "여러 수정을 묶어서 릴리즈"
│   → ship-cycle (issue-driven development orchestrator; direct-call only; GitHub + gh CLI required, graceful fallback otherwise)
│
├── Contains "full check" / "run vibesubin" / "vibe check" / "everything"
│   → MODE 1 (full sweep)
│
├── Contains "쉽게 설명해줘" / "일반인도 이해되게" / "explain like I'm non-technical"
│      / "initiate easy mode" / "no jargon" / "/vibesubin explain" / "/vibesubin easy"
│      / "非開発者でも分かるように" / "用通俗的话解释"
│   → MODE 1 (full sweep) with `explain=layperson` marker (stackable with `tone=harsh`)
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

**User:** *"my whole repo is a mess and I don't know where to start"* → This is the command mode signal even without `/vibesubin`. Offer: *"I can run the full vibesubin sweep — all nine skills in parallel, one prioritized report at the end. Want me to?"*

**User:** *"I pushed my .env to github"* → Immediate `audit-security` + `manage-secrets-env` tandem. Don't route through the umbrella; the urgency is specific.

---

## Things not to do

- **Don't run mode 1 without confirming.** The full sweep produces a lot of output. Confirm scope first.
- **Don't run mode 1 serially.** The whole point is parallelism. If the host framework doesn't support parallel task agents, warn the operator that it'll be slower and proceed sequentially.
- **Don't have mode 1 make changes.** It's read-only. The operator approves the fix list; the specialists apply fixes.
- **Don't force mode 1 on a specific request.** If the operator clearly wants one thing (`"fix this SQL injection"`), route to the specialist. Don't up-sell the full sweep.
- **Don't repeat the full specialist reports in the synthesis.** The top of the report is a summary; the details go below the fold. Operators skim.
- **Don't over-meme.** The vibe is in one section header and the tone of the verdict. Not in every line.

## Integration notes

- The nine specialists' output formats should be stable enough that the synthesis step doesn't have to reverse-engineer them. If a specialist's format changes, update the synthesis template in this SKILL.md.
- If a specialist fails (can't run, errors out), report its failure in the "What ran" section and continue with the others. Do not block the whole sweep on one failed specialist.
- If the repo is too large for a single sweep (e.g., > 10k files), mode 1 should partition and run per-subdirectory, then merge. Warn the operator about the partitioning first.
- **Post-sweep issue generation.** After a `/vibesubin` sweep, if the operator wants the top findings captured as trackable issues for a release cycle, route them to `/ship-cycle` with the sweep output. `ship-cycle` itself is direct-call only and not part of the parallel sweep, but it is the natural follow-up when a sweep's prioritized fix list needs to become a shipping plan.

## When this skill is not the right answer

If the operator has a specific, narrow task, don't route through vibesubin at all — let the matching specialist fire directly. The umbrella is for exploration and full sweeps, not for tasks that already have an obvious home.

---

*vibesubin is the thing you type when you want your AI to just **look**. Not to fix, not to explain, not to lecture — just to look and tell you what it sees.*
