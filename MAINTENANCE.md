# Maintenance

This skill pack is a **living artifact**. It is not a one-time authoring job — it has to keep up with:

- Changes in Claude Code's skill / plugin / hook system
- New LLM failure modes as models evolve
- New static analysis and refactoring tools
- New security patterns and CVEs
- New CI/CD conventions (GitHub Actions, deployment targets)
- Feedback from real vibe-coder users via issues

This document defines **how** the pack is maintained so the maintainer (and future AI sessions) have a rhythm to follow.

---

## Update cadence

| Scope | Frequency | Trigger |
|---|---|---|
| **Frontmatter / schema audit** | Every release of Claude Code that touches skills or plugins | Upstream changelog mention |
| **Refactoring methodology review** | Quarterly | Spot-check `understandlegacycode.com`, OpenRewrite changelog, Martin Fowler's site, recent ICSE/FSE papers |
| **Security pattern list** | Quarterly | OWASP Top 10 updates, CVE digests for major runtimes |
| **Language smoke-test table** | Biannually | New mainstream linters/type checkers (e.g., `ty`, `pyrefly`, `oxc`) |
| **Real-world issue sweep** | Monthly | Triage open issues, incorporate reproducible bug reports |
| **Failure-mode log** | Ad hoc, on session insight | Whenever an AI session reveals a failure pattern not yet covered |

---

## What to update when

### When a new Claude Code version ships

1. Check the Claude Code release notes for any changes to:
   - `SKILL.md` frontmatter fields (new fields, removed fields, renamed fields)
   - Plugin marketplace format (`.claude-plugin/marketplace.json`, `plugin.json`)
   - Hook events (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, new events)
   - Skill invocation mechanics (progressive disclosure rules, nested reference limits)
2. Validate every `SKILL.md` in the pack still parses. Run a lint pass if one is available.
3. Bump the pack's "last tested against Claude Code version" note at the bottom of this file.

### When a new failure mode is observed

A "failure mode" is a concrete mistake an AI makes during a real session that the pack should have prevented.

1. Open an issue titled `[failure-mode] <short description>`.
2. Identify which skill should have caught it.
3. Add the pattern to that skill's `references/llm-failure-modes.md` (or equivalent).
4. If applicable, add a detection grep/command to `scripts/`.
5. Reference the issue in a commit: `fix(refactor-verify): guard against missed callsite after rename (#NN)`.

### When a skill file grows past 500 lines

Claude Code partially reads long SKILL.md files. If any `SKILL.md` exceeds ~500 lines:

1. Extract the tail sections into `references/*.md`.
2. Replace them with one-line links from `SKILL.md`.
3. Verify progressive disclosure still works — Claude should only pull the reference when it needs the detail.

### When a new language needs coverage

The pack aims to be language-agnostic. Adding a new language means:

1. Add an entry to `plugins/vibesubin/skills/refactor-verify/references/language-smoke-tests.md`:
   - Canonical build / typecheck / test command chain
   - Standard linter
   - Common refactoring pitfalls for that language
2. Add corresponding patterns to `audit-security/references/language-scanners.md`.
3. Add LOC / complexity tooling to `fight-repo-rot/references/rot-metrics.md`.
4. Update any smoke-test script in `scripts/` to auto-detect the new language.

Do **not** add a new top-level skill per language. Everything stays language-agnostic.

---

## What NOT to change

Some decisions are load-bearing for the pack's identity. Changing them is a major version bump, not a routine update.

- **The 6-step recursive verification procedure.** `refactor-verify/SKILL.md` is built around this. If the sequence changes, every skill that references it needs review.
- **Tidy First separation.** Structural commits must stay separated from behavioral commits across the entire pack.
- **Third-person description frontmatter.** Claude's discovery heuristics rely on this. First-person descriptions break triggering.
- **"One level deep" reference structure.** Never chain `SKILL.md → a.md → b.md`. Always flatten.
- **Issue-only contribution model.** PRs are not accepted. This is a design choice; the pack has a single voice. (If this ever changes, update README, CONTRIBUTING, and the issue-only section everywhere in one commit.)

---

## How future AI sessions should read this file

If you are an AI agent picking up maintenance of this pack in a new session, read these files in order:

1. `README.md` — overview and skill list
2. `docs/PHILOSOPHY.md` — invariants
3. This file (`MAINTENANCE.md`) — what to update and when
4. The specific skill's `SKILL.md` and `references/`
5. Recent issues on the repo (via `gh issue list`)

Do not propose structural rewrites on first session. Confirm with the maintainer before touching schemas, install mechanics, or the philosophy.

---

## Last tested against

- Claude Code: _set at release_
- Plugin marketplace spec: `v1` (as of 2026-04)
- Official skill docs: `code.claude.com/docs/en/skills`
