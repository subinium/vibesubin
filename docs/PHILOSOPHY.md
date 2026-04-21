# Philosophy

The invariants every skill in this pack is built around. Kept short on purpose — this file is read at the start of every maintenance session, so the rules have to fit on one screen.

## 1. Done is proven, not claimed

If a task says complete, there is execution evidence behind it: a passing test, a matched hash, a live `200 OK`, a `git grep` that returns the expected count. An assertion without evidence is a bug, regardless of how confident the output sounds. This is the single rule every other rule inherits from.

## 2. Your AI is a well-meaning junior developer

Juniors work hard and juniors sometimes forge ahead when they should have stopped to ask. The skills in this pack insert *"stop and ask"* moments where a more careful hand would — baseline checks before refactors, triage classifications before security verdicts, confidence tags before dead-code deletions. These pauses exist because the cost of a wrong silent success is higher than the cost of asking twice.

## 3. Docs are written for the next AI session, not just for people

The current conversation evaporates when the session ends; READMEs, commits, PR bodies, and `CLAUDE.md` files are the only things that survive. They are written so a fresh session can rebuild the context cold: tables over prose, absolute paths over vague references, invariants over narrative, declarative over implied. Humans happen to benefit from the same structure.

## 4. Existing conventions are the default

The pack does not silently rewrite a repo's branch strategy, file layout, or config on a whim. When the pack has a strong default (GitHub Flow, pinned dependencies, domain-first directory layout), it proposes — it does not impose. An existing working convention is load-bearing until proven otherwise.

## 5. One level of indirection, no deeper

`SKILL.md` may link into `references/`, `scripts/`, and `templates/`. `references/` files do **not** link further down the chain. If a reference file grows large enough to need its own references, either the skill is overloaded and should be split, or the reference should be inlined back into the `SKILL.md`. Flat beats nested; progressive disclosure beats endless indirection.

## 6. Read-only by default when the scope is broad

`/vibesubin` runs every skill in parallel across an entire repo. A sweep of that shape is too dangerous to auto-edit; it reports and waits for approval. Skills called by name are different — they are scoped to a specific task the operator asked for, so they edit directly. The line between "sweep" and "direct invocation" is hard-coded into every worker skill via the `sweep=read-only` marker check.

## 7. Framing is not substance

Harsh mode drops hedging language. It never inflates severity, fabricates findings, or invents CVSS scores. Every harsh statement must cite the same evidence the balanced version would cite — file, line, metric, `git grep` count. Framing is negotiable; evidence is not.

## 8. Objectivity beats enthusiasm in generated docs

Documentation written by the pack does not oversell, does not embellish, does not describe features that don't exist, and does not use marketing language where plain language fits. "Fast" without a benchmark is a lie. "Best-in-class" without a comparison is marketing noise. "Works" without a verification command is a claim. The `write-for-ai` skill enforces this on every doc it produces.

## 9. Portable engines can have host-specific wrappers

The pack's core skills are host-agnostic — they work on Claude Code, Codex CLI, Cursor, Copilot, Cline, or any agent that supports `SKILL.md` files. When a specific operator's workflow benefits from a host-specific convenience (e.g., auto-invoking a plugin's slash command to pipe its output into a portable skill), that convenience belongs in a thin **wrapper skill**, not in the core.

A wrapper skill:

- Declares its host dependency explicitly in `description` and `when_to_use`.
- Checks the host as its first action and emits a graceful one-line fallback on non-matching hosts — it never hangs, errors loudly, or blocks the workflow.
- Delegates everything substantial to a portable engine skill. The wrapper owns the invocation glue; the engine owns the logic.
- Has no sweep mode (wrappers are direct-call only — they invoke external tools and write files, which break the sweep's read-only + portable invariants).

Wrappers exist because a specific workflow is **frequent enough** to justify a worker slot for one operator's habit — not because every input source deserves its own skill. The engine is the contract; the wrapper is convenience. The first wrapper in the pack is `codex-fix`, delegating to `refactor-verify`'s review-driven fix mode.

## 10. Code hygiene and process are different categories

The pack carries two cognitively distinct categories of worker skill: **code hygiene** — anything that audits, refactors, documents, or secures the code on disk — and **process** — anything that orchestrates the lifecycle of work around the code (issues, milestones, versions, tags, releases, changelog). These do not share a cap. Code hygiene is capped at 10 to protect the operator's cognitive budget — nobody remembers 15 specialists. Process is capped at 1 for now, because one well-scoped orchestrator covers the full issue-to-release loop; a second process worker would fracture the audit trail the first one maintains. If either cap needs to grow, that's a major version decision — extend, split, or displace within the category first.

The umbrella `/vibesubin` command runs code-hygiene specialists only — process skills mutate external state (GitHub issues, tags, releases) and belong in direct-call only workflows like `codex-fix` and `ship-cycle`. Sweep is read-only by invariant #6; process is mutating by definition; these do not mix.

## What is load-bearing vs. what is flexible

Changing any of the rules above is a major version bump. Changing specific tooling recommendations, thresholds, or language coverage is routine.

- **Load-bearing** (major version bump if changed): the ten rules above, the 6-step refactor-verify procedure, Tidy First separation, the `sweep=read-only` marker protocol, third-person frontmatter descriptions, the one-level-deep reference structure, the issue-only contribution model.
- **Flexible** (routine updates): specific linter names, specific LOC thresholds, specific deploy targets, specific language-smoke-test commands, the set of skills in the pack, per-version phrasing of individual skills.

See [`MAINTENANCE.md`](../MAINTENANCE.md) for the cadence.
