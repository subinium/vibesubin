# Milestone rules

Milestones map 1:1 to semver versions. Every open milestone is a version the operator intends to cut. Closing a milestone triggers the release pipeline (see `release-pipeline.md`).

## Semver decision tree

```
Does any item change a public contract in a backward-incompatible way?
├── YES → MAJOR (X+1.0.0)
│         Examples: renamed exported symbol, removed CLI flag, changed response shape,
│                   required new input, dropped Node/Python version, schema migration
│                   without back-compat shim.
└── NO → Does any item add a new user-visible capability?
         ├── YES → MINOR (X.Y+1.0)
         │         Examples: new skill, new API endpoint, new config option with a
         │                   default, new CLI subcommand, additive optional field.
         └── NO → PATCH (X.Y.Z+1)
                   Examples: bug fix, perf improvement, internal refactor, test-only
                             change, docs-only change, dependency bump without API
                             change, typo in user-visible string.
```

## Version → label mapping

| Semver | Typical labels | Cap per milestone |
|---|---|---|
| **PATCH** | `bug`, `perf`, `refactor`, `test`, `docs`, `chore` | ~5 items |
| **MINOR** | `feat` (plus supporting `bug` / `docs`) | ~10 items |
| **MAJOR** | `breaking` (plus anything else that ships with the break) | no hard cap; usually small and focused |

The cap is a soft heuristic, not a wall. Three tightly-related items are one milestone. Eight unrelated items are two milestones.

## Cluster heuristics

Group items into the same milestone when any of these apply:

- They touch the same module or subsystem.
- One's acceptance criteria cite another (`Depends on: #N`).
- They share a single reviewer or owner.
- They came from the same sweep report and share an area label.
- Fixing one without the others produces an incoherent user-facing state.

Split items into separate milestones when:

- A breaking change would trap a bug fix behind a major version the operator is not ready to cut. Patch the bug first, then cut the major.
- A security-critical item needs to ship immediately — cut a dedicated patch, do not wait on the rest.
- One item has an indefinite timeline (needs design, needs data, blocked on an external party). Park it in a future milestone, ship the rest now.

## Naming

- Milestone title: exact string `vX.Y.Z`. Match `.claude-plugin/marketplace.json` `plugins[0].version`.
- Description: one sentence — what the milestone ships. Example: *"Fixes for the 0.4.x series of sweep findings."*
- Due date: optional. Set it only when there is a real external deadline; otherwise leave blank.

## Don't mix breaking and additive

A milestone is either **breaking + anything** (major) or **additive + patches** (minor) or **patches only** (patch). Do not put a breaking rename and a new config option in the same milestone — split into a major for the break, and a follow-up minor for the new capability. Reason: if the major has to slip, the minor is blocked for no reason; and if the minor ships first on the pre-break version, the rename migration path stays cleaner.

## Worked examples

**Example 1 — three bug fixes from a sweep.** Three `bug` items, two in `src/api/`, one in `src/auth/`. All `p1`. → One PATCH milestone (`v0.4.1`), three issues. Cut when all three close.

**Example 2 — new skill plus README updates.** One `feat` (new skill), two `docs` items (README updates referencing the new skill), one `chore` (CHANGELOG entry). → One MINOR milestone (`v0.5.0`), four issues. The docs depend on the feat closing first.

**Example 3 — breaking rename, bug fix, new config option.** `breaking` (rename exported symbol), `bug` (null deref), `feat` (new optional config field). → Three milestones:
  - `v0.4.1` — just the bug (patch, ships immediately)
  - `v0.5.0` — the new config option (minor, ships next)
  - `v1.0.0` — the rename (major, ships last with migration notes)

Do not collapse this into a single milestone for convenience. The operator loses the ability to ship the urgent bug fix without the unrelated rename.

**Example 4 — security-critical.** One `security` + `p0` item from an audit. → Dedicated PATCH milestone, does not wait on any other open milestone. Cut within hours, not days. The rest of the backlog stays parked.

## Edge cases

- **Milestone already exists with a matching version.** Reuse it. Do not create a second `v0.4.1`.
- **Operator wants a different version number than the rules suggest.** Respect the override, but state the reason the rules suggested differently (*"Rules say PATCH; you asked for MINOR because this is the first release after a quiet period. Proceeding with MINOR."*).
- **An item matches no milestone and is not time-sensitive.** Assign it to a `backlog` milestone (no version). Never leave an issue with no milestone — unmilestoned issues vanish from release planning.
