# Branch strategy — when NOT to use GitHub Flow

The default in `SKILL.md` is GitHub Flow: one `main`, short-lived feature branches, always merged via PR. For 95% of vibe-coder projects, that's the right answer. This reference covers the cases where it isn't.

## When a different strategy is justified

Only pick a different strategy if one of these is true:

- **You have a staging environment separate from production** and want every merge to `main` to deploy to staging before going to prod. Then add a `release/*` branch or a manual approval gate.
- **You're a library author with multiple supported major versions.** You might want long-lived version branches (`v1.x`, `v2.x`).
- **Your industry requires it** (regulated environments with formal release cycles and auditor sign-offs).

For everything else, GitHub Flow.

## Dealing with an inherited `dev` branch

Many operators inherit a `dev` branch from an older setup. If you see a `main` + `dev` split, ask:

1. Is there a real reason for two long-lived branches? (For example: `dev` is the integration branch, `main` is a release snapshot.)
2. Or is it vestigial? (It just drifted over time and nobody remembers why.)

**If vestigial**, suggest consolidating to just `main`. Document the consolidation in `CLAUDE.md` so future sessions don't re-create `dev` on reflex.

**If there's a real reason**, keep both and document the reason in `CLAUDE.md` so future sessions don't re-argue the choice.

## Branch naming rules (all strategies)

Regardless of which strategy, short-lived branches follow this naming:

| Prefix | Use for |
|---|---|
| `feature/<topic>` | New capability |
| `fix/<topic>` | Bug fix |
| `refactor/<topic>` | Structure-only change, no new behavior |
| `chore/<topic>` | Dependencies, config, tooling |
| `docs/<topic>` | Docs only |
| `hotfix/<topic>` | Emergency fix to production |

Lifetime: hours to days. Never weeks. If a branch has lived for more than a week without merging, it's either done (merge it) or abandoned (delete it).

## Release branches (optional)

For libraries or apps with formal releases, add:

- `release/vX.Y` — branched from `main` when a release candidate is cut, accepts only bug fixes and docs, gets tagged `vX.Y.Z` when ready to ship.
- Backport fixes: merge from `release/vX.Y` back into `main` so the fix doesn't disappear at the next release.

Do NOT use release branches as a general pattern. They add process overhead that most small projects can't afford.
