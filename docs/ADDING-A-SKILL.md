# Adding a new skill to vibesubin

This doc is canonical for skill-authoring mechanics. If this file and `MAINTENANCE.md` ever disagree, `MAINTENANCE.md` wins on operational policy (what invariants exist, what release process applies); this file wins on mechanics (what files and sections are needed). Both must stay in sync on category caps (10 + 1).

## Before you start

Check the category cap:
- 10 code-hygiene workers (all slots used — see `MAINTENANCE.md` never-do #2)
- 1 process worker (used — `ship-cycle`)

A new worker requires extending, splitting, or displacing an existing skill. Adding an 11th code-hygiene or a 2nd process worker is a major-version decision — open an issue first.

Proceed below only after category space is confirmed.

## Directory layout

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # required, ≤500 lines
├── references/           # optional sidecars
│   └── *.md              # one level deep only (invariant #5)
├── scripts/              # optional executable helpers
└── templates/            # optional files the skill copies into user repos
```

`<skill-name>` must match the `name:` frontmatter field exactly. Lowercase, alphanumeric + hyphens. No leading/trailing/consecutive hyphens.

## Required SKILL.md frontmatter

```yaml
---
name: <skill-name>               # must equal directory name
description: <1-1024 chars>      # what the skill does, value prop first
mutates: [<tokens>]              # subset of {direct, external}; [] for diagnosis-only
when_to_use: <trigger phrases>   # include Korean, optionally Japanese + Chinese
context: fork                    # umbrella only (omit for workers + wrappers)
agent: general-purpose           # umbrella only (omit for workers + wrappers)
allowed-tools: <tool allow-list> # explicit; never widen without reason
---
```

Field rules:
- `name`: 1–64 chars, matches directory
- `description`: 1–1024 chars, non-empty, functional-tone (no marketing)
- `mutates`: bracketed list of tokens drawn from `{direct, external}`. Sweep specialists cannot include `external` (sweep is read-only by invariant). Pure-diagnosis workers must declare `[]`. Editable sweep workers must include `direct`. Direct-call-only skills (`codex-fix`, `ship-cycle`) typically include both.
- `when_to_use` + `description` combined ≤ 1,536 chars
- `allowed-tools`: list each tool the skill actually uses; wildcard Bash(*) is discouraged

## Required sections (order matters for reader navigation)

Every worker SKILL.md must contain these sections, in this order:

1. `# /<skill-name>` — H1 with the slash-command name
2. One-paragraph opening — value prop + direct-call vs sweep behavior
3. `## State assumptions — before acting` — explicit `Assumptions:` block with skill-specific items and stop-and-ask triggers (Karpathy P1 enforcement)
4. `## Procedure` — numbered steps, or the skill's actual workflow
5. `## Sweep mode — read-only audit` — if the skill is sweep-eligible (launched by `/vibesubin` parallel block); direct-call-only wrappers (`codex-fix`, `ship-cycle`) document their non-participation here instead
6. `## Harsh mode — no hedging` — MANDATORY for every worker (umbrella included); check for `tone=harsh` marker, switch framing, never inflate severity
7. `## Things not to do` — includes the Karpathy P2 bullet (universal *"Don't add features the operator did not request"* OR skill-specific anchored variant)
8. `## 4-part output shape` — reaffirm the what-did / what-found / what-verified / what-next shape
9. `## Hand-offs` — inputs and outputs to other skills

Optional but recommended:
- `## When not to use <skill-name>` — boundary with adjacent skills
- `## Integration with /vibesubin sweep` — direct-call-only skills document why they are not in the sweep

## The validator contract

After any edit, run:

```
python3 scripts/validate_skills.py
```

The validator enforces:
- Every backtick-quoted path reference resolves on disk
- Every SKILL.md ≤ 500 lines (same cap on each `references/*.md` file)
- `## Harsh mode — no hedging` section present in every worker
- `sweep=read-only` marker present in the 6 editable workers
- `marketplace.json` version == `plugin.json` version
- No path-traversal attempts in promised paths
- Frontmatter declares `name`, `description`, `mutates`, and `allowed-tools` (or `context` + `agent` for the umbrella)
- `mutates` tokens valid and consistent with skill category
- Every `/<skill-name>` backtick reference resolves to a real skill

If the validator fails, the skill does not ship. Run `pytest tests/` alongside; both gates must be green.

## Output shape every worker must produce

```
## What I did
<bullets — concrete actions taken>

## What I found
<bullets — discoveries, severities, evidence>

## What I verified
<bullets — commands run, counts matched, tests passed>

## What you should do next
<bullets — concrete operator actions in priority order>
```

Umbrella synthesis depends on this shape.

## Adding a worker: file checklist (per `MAINTENANCE.md` change-type matrix)

In a single PR:

- [ ] New SKILL.md under `plugins/vibesubin/skills/<name>/` with frontmatter (incl. `mutates`) + required sections
- [ ] Any `references/` sidecars the SKILL.md links to (otherwise validator fails)
- [ ] `README.md` skill-table row + § section + workflow bullet (surgical edit only)
- [ ] `docs/i18n/README.ko.md` + `docs/i18n/README.ja.md` + `docs/i18n/README.zh.md` matching edits in natural voice
- [ ] Umbrella `plugins/vibesubin/skills/vibesubin/SKILL.md`:
  - Routing tree branch
  - Parallel launch block (if sweep-eligible)
  - "What ran" stoplight list (if sweep-eligible)
- [ ] `CHANGELOG.md` `[Unreleased]` → `### Added` entry, functional-only
- [ ] Both manifests bumped if count changed description
- [ ] `KNOWN_SKILLS` set in `scripts/validate_skills.py` updated (and category sets if applicable)
- [ ] `python3 scripts/validate_skills.py && pytest tests/` passes
- [ ] All 4 READMEs have the same skill-table row count

## Adding a wrapper (direct-call only, like codex-fix)

Follow `docs/PHILOSOPHY.md` rule 9:
- Host dependency declared in frontmatter
- Host check is Step 1, graceful one-line fallback on non-match
- No sweep mode — wrappers do not participate in `/vibesubin`
- Delegate substantial logic to a portable engine skill; wrapper owns only glue

## Common failure modes

- 501-line SKILL.md — extract a section into `references/<topic>.md`
- Missing harsh-mode section — validator fails; add the canonical heading even for skills that don't particularly need different harsh framing
- Forgot the sweep marker in an editable worker — validator fails
- Translation skipped one language — validator's README-parity check fails (coming in v0.5.0)
- Asset referenced in backticks but not committed — validator's promise check fails

---

Questions: open an issue at https://github.com/subinium/vibesubin/issues.
