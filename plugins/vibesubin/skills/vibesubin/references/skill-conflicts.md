# Skill conflicts — catalog and surfacing rules

## Purpose

This catalog enumerates the known cases where two vibesubin specialists give contradictory advice about the same file during a sweep. The umbrella consults this file before synthesis: if a conflict pair matches what two specialists reported on the same path, the umbrella emits a **conflict surface block** instead of silently picking one side or burying the disagreement inside the by-specialist section. Principle: **contradiction is information, not a bug — surface it.** The operator is the tie-breaker; the umbrella's job is to show both sides' basis honestly.

## Conflict surface output shape

When a catalog conflict fires, the umbrella emits this block in the sweep's output, directly under the affected file's heading:

```
⚠ Skill conflict — <file> : <line or "(whole file)">

Two specialists disagree on what to do here.

├─ Specialist A — <skill-name>
│  Recommends: <one-line recommendation>
│  Reason: <why this specialist thinks they're right>
│  Basis: <concrete evidence / rule citation>
│
├─ Specialist B — <skill-name>
│  Recommends: <one-line recommendation>
│  Reason: <why this specialist thinks they're right>
│  Basis: <concrete evidence / rule citation>
│
└─ Recommendation: <umbrella's judgment call — usually "defer to operator">
   Operator decides: <the two concrete paths forward>
```

## Canonical conflict catalog

### Conflict 1 — `refactor-verify` ↔ `audit-security` on sequencing

**Scenario**: A security-sensitive file (auth flow, crypto wrapper, input validator, session handler) needs both a structural refactor AND a security fix. Both specialists flag the same file; their proposed first moves contradict.

```
⚠ Skill conflict — <path> : (whole file)

Two specialists disagree on what to do here.

├─ Specialist A — refactor-verify
│  Recommends: refactor first, then re-run audit-security on the result
│  Reason: structural-first — auditing the old shape wastes effort because
│          the refactor will change the attack surface the audit just mapped
│  Basis: refactor-verify SKILL.md §"Security-sensitive changes" (lines 469–470)
│         — "run audit-security on the result"
│
├─ Specialist B — audit-security
│  Recommends: audit first, then refactor the fix with verification
│  Reason: exploitability-first — a refactor that preserves a vulnerability
│          is not safer; unverified-safe refactors can introduce new code paths
│          exploitable via the original vector
│  Basis: incident runbook — containment before structural work; refactors
│         can silently rename the vulnerable entrypoint without removing the bug
│
└─ Recommendation: sequence depends on liveness of the vulnerability
   Operator decides:
     • ACTIVE vuln (live exploitability right now) → audit-security first, then refactor
     • LATENT vuln (requires conditions that don't currently hold) → refactor-verify first, then re-audit
```

### Conflict 2 — `unify-design` ↔ `refactor-verify` on component consolidation

**Scenario**: `unify-design` detects duplicate primitives (two Button components, three Card variants) and wants to consolidate into a single source of truth. `refactor-verify` flags the same file because consolidation is a cross-file structural change and its "don't touch adjacent code during a move" rule applies.

```
⚠ Skill conflict — <path> : (whole file)

Two specialists disagree on what to do here.

├─ Specialist A — unify-design
│  Recommends: consolidate the duplicates now; update tokens and call sites
│  Reason: design-system drift is this skill's explicit scope; single source of
│          truth is the load-bearing invariant it enforces
│  Basis: unify-design SKILL.md — consolidation is in-scope, cross-file rewrites
│         for tokens + call-site updates are expected
│
├─ Specialist B — refactor-verify
│  Recommends: pause — consolidation is a multi-file structural change that
│              needs the 4-check verification pass before commit
│  Reason: unify-design alone cannot prove no caller broke; symbol audit +
│          compile/type + behavioral + call-site checks are required for any
│          move/rename/merge
│  Basis: refactor-verify SKILL.md — 4-check protocol for structural changes
│
└─ Recommendation: this is a hand-off, not a conflict — treat it as a sequence
   Operator decides:
     • unify-design drafts the token rename / component merge
     • refactor-verify runs the 4-check pass on the draft before commit
     • commit only if all 4 checks pass
```

### Conflict 3 — `fight-repo-rot` ↔ `project-conventions` on dead dependencies

**Scenario**: `fight-repo-rot` flags packages in `package.json` / `requirements.txt` / `Cargo.toml` that are never imported ("dead dependencies") and recommends removal. `project-conventions` has a lockfile-integrity rule and resists manual pruning.

```
⚠ Skill conflict — <manifest-file> : <line range for dead deps>

Two specialists disagree on what to do here.

├─ Specialist A — fight-repo-rot
│  Recommends: remove the unused packages from the manifest
│  Reason: dead code is dead code even in the manifest; keeping unused deps
│          pays for security scanning churn and auto-update noise you never
│          benefit from
│  Basis: fight-repo-rot SKILL.md — "packages in the manifest but never
│         imported… can be removed" (lines 203–204)
│
├─ Specialist B — project-conventions
│  Recommends: do not manually prune — Dependabot/Renovate may need the dep
│              resolved for a transitive the lockfile depends on
│  Reason: removing a direct dep could surface a transitive you were implicitly
│          relying on; lockfile-integrity is the load-bearing invariant
│  Basis: project-conventions SKILL.md — exact pinning + lockfile invariant
│
└─ Recommendation: remove, then verify lockfile still resolves
   Operator decides:
     • run `npm install` / `pip install -r requirements.txt` / `cargo check`
       after removal
     • if resolution fails or a transitive goes missing → the dep was
       load-bearing despite appearing unused; restore it and add a code
       comment explaining why it stays
     • if resolution succeeds → removal was safe; commit
```

### Conflict 4 — `manage-secrets-env` ↔ `audit-security` on a tracked `.env`

**Scenario**: Both specialists flag a `.env` file currently tracked by git. They agree it's a problem; they disagree on the first move and on what "done" means.

```
⚠ Skill conflict — .env : (whole file)

Two specialists disagree on what to do here.

├─ Specialist A — manage-secrets-env
│  Recommends: remove .env from tracking, add to .gitignore, populate
│              .env.example with keys only
│  Reason: structural issue — .env is local-only by the four-bucket lifecycle
│          rule; tracking is the structural defect to eliminate
│  Basis: manage-secrets-env SKILL.md — four-bucket lifecycle; .env is always
│         local-only
│
├─ Specialist B — audit-security
│  Recommends: rotate every credential in the file immediately; run the
│              exposed-secret incident runbook (rotate → rewrite history if
│              required → notify downstream)
│  Reason: a committed secret is a live attack surface until it is rotated;
│          removing the file from future tracking does not un-leak the value
│  Basis: audit-security SKILL.md — exposed-secret incident runbook; exposure
│         is active until rotation
│
└─ Recommendation: this is a required sequence, not a conflict — both are right
   Operator decides (in order):
     1. audit-security's incident runbook: rotate every credential, rewrite
        history if the commit is within the rotation window's risk tolerance
     2. manage-secrets-env's structural fix: remove from tracking, update
        .gitignore, publish .env.example with keys only (no values)
```

## When to classify as a conflict vs. a hand-off

Before emitting a conflict block, the umbrella decides which shape applies:

- **Hand-off**: both specialists agree on the *goal*; they differ on *who executes which step*. Umbrella output: `"do A, then B"` — a sequence, not a fork. Conflicts 2 and 4 above are hand-offs dressed as conflicts.
- **True conflict**: specialists disagree on the *goal itself*. Umbrella output: `"you must pick — here is each side's basis"` — a fork. Conflict 1 (sequencing depends on liveness) and Conflict 3 (remove vs. keep) can be true conflicts depending on facts the operator has that the umbrella doesn't.

Decision rule, applied in this order:
1. Do both specialists' recommendations end in the same final state? → **hand-off**. Emit the sequence.
2. Does one recommendation negate the other? → **true conflict**. Emit the fork.
3. Does the choice depend on a fact neither specialist can check (e.g., liveness of a vuln, whether a dep is used via dynamic import)? → **true conflict**. Emit the fork and name the fact the operator must supply.

Treating hand-offs as conflicts is noise. Treating conflicts as hand-offs is silent corruption — the umbrella picks a side the operator never approved.

## Layperson mode

When the sweep is invoked with `layperson=on`, every conflict block gets one extra line immediately below the `Recommendation:` line:

```
   쉽게 말해서 / In plain words: 두 스킬이 다른 걸 하라고 해요.
   A는 <짧은 이유>, B는 <짧은 이유>. 당신이 골라야 합니다.
```

The plain-words line never replaces the basis — it supplements. Evidence stays visible; the operator still sees both sides' citations.

## What NOT to do

- **Don't invent conflicts.** Only pairs that match entries in this catalog, or genuinely contradictory recommendations on the same path, qualify. Emitting a conflict block for two specialists who happen to touch the same file is noise.
- **Don't resolve conflicts automatically when the basis is genuine disagreement.** Rare but real cases (e.g., rotate-vs-rewrite-history trade-off, active-vs-latent sequencing) require operator context the umbrella does not have.
- **Don't strip evidence when summarizing.** Both specialists' basis lines must appear verbatim — not paraphrased, not collapsed into "they disagree". The operator decides on evidence.
- **Don't treat severity differences as conflicts.** If both specialists say "fix it" and only disagree on urgency (blocker vs. warning), that's a priority stack question, not a conflict. The umbrella's existing severity ordering handles it.
- **Don't re-emit a catalog block when the specialists already agreed.** If two specialists flagged the same file but the actual recommendations are identical after reading the specialist outputs, skip the block — it's not a conflict, it's a corroboration.

## Extending this catalog

New entries go here when: a real sweep produced two contradictory recommendations on the same path, the disagreement has a durable rule-level basis (not a one-off), and resolving silently would make the umbrella lose information the operator needed. Each new entry carries the same shape as the four above: scenario, both blocks with reason + basis, resolution default (hand-off sequence or true-conflict fork).
