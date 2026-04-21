# Release pipeline

Step-by-step checklist for closing a milestone and cutting a tagged release. Run this once every issue in the milestone is closed and CI is green on the default branch.

This file is the operational expansion of the release process declared in the root `CLAUDE.md`. The root `CLAUDE.md` owns the policy (what must be true at each phase); this file owns the commands (how to verify each phase, including validator preflight, CI wait loops, manifest detection across language ecosystems, and rollback decisions). If they drift, the root `CLAUDE.md` wins on policy; this file wins on commands. Both must stay in sync on the ordering of steps.

## Preflight

Before starting, verify:

```bash
# 1. Working tree is clean on the default branch
git status
git rev-parse --abbrev-ref HEAD     # should match the default branch

# 2. Milestone has zero open issues and zero open PRs
gh issue list --milestone "vX.Y.Z" --state open      # expect empty
gh pr list --search "milestone:vX.Y.Z" --state open  # expect empty

# 3. CI is green on the default branch
gh run list --branch main --limit 1                  # expect conclusion: success

# 4. Validator passes (vibesubin-specific; repos without this skip)
test -f scripts/validate_skills.py && python3 scripts/validate_skills.py
```

If any check fails, stop and report. Do not paper over a red CI run by retagging later — cut a new patch instead.

## 10-step pipeline

**1. Aggregate closed issues into a CHANGELOG entry.**

```bash
gh issue list \
  --milestone "vX.Y.Z" \
  --state closed \
  --json number,title,labels \
  --limit 100 > /tmp/ship-cycle-closed.json
```

Convert each closed issue to one functional-only CHANGELOG bullet. Format:

```
### Added
- <one-line observable change> (#<issue-number>)

### Changed
- <one-line observable change> (#<issue-number>)

### Fixed
- <one-line observable change> (#<issue-number>)
```

Functional-only style: every bullet describes an observable change. No narrative, no *"we decided to"*, no emotional framing. Group by `Added` / `Changed` / `Fixed` / `Removed` / `Security` per Keep-a-Changelog.

Move the aggregated entries under a new `[X.Y.Z] — YYYY-MM-DD` heading in `CHANGELOG.md`. The `[Unreleased]` section stays as a placeholder for the next cycle.

**2. Bump version in every manifest.** Detect which manifests exist; update all of them in the same commit.

| Project shape | Files to bump |
|---|---|
| Node / npm / pnpm | `package.json` (`version`) |
| Rust / cargo | `Cargo.toml` (`[package].version`), `Cargo.lock` |
| Python (pyproject) | `pyproject.toml` (`[project].version` or `[tool.poetry].version`) |
| Python (setup.py) | `setup.py` (`version=`) |
| Claude Code plugin | `.claude-plugin/marketplace.json` (`plugins[0].version`) AND `plugins/<name>/.claude-plugin/plugin.json` (`version`) — both files, same commit |
| Go module | git tag is authoritative, no file bump needed |

For the vibesubin pack specifically, both `marketplace.json` and `plugin.json` must change together — invariant in root `CLAUDE.md`.

**3. Run the project's validator and test suite.**

```bash
# vibesubin-specific
python3 scripts/validate_skills.py     # expect: OK

# language-standard
npm test       || pnpm test       || yarn test
pytest
cargo test
go test ./...
```

If any fails, fix before continuing. Do not tag a release that did not pass its own tests.

**4. Commit the release prep.** Conventional commits format.

```bash
git add CHANGELOG.md \
        package.json \
        .claude-plugin/marketplace.json \
        plugins/vibesubin/.claude-plugin/plugin.json
# (adjust file list to the actual manifests touched)

git commit -m "chore(release): vX.Y.Z"
```

Body is optional here because the CHANGELOG entry already documents what shipped.

**5. Push the commit.**

```bash
git push
```

Wait for CI to complete on this commit before tagging. A tag on top of an untested commit is a regression vector.

**6. Create an annotated tag.**

```bash
git tag -a vX.Y.Z -m "<one-line summary of the release>"
```

Annotated, not lightweight. The tag message appears in GitHub's tag list and `git tag -l -n1`. Lightweight tags leave the list blank.

**7. Push the tag.**

```bash
git push origin vX.Y.Z
```

**8. Write release notes to a temp file.** Not committed to the repo — release notes live on GitHub only.

```bash
NOTES=/tmp/<project>-vX.Y.Z-release-notes.md
cat > "$NOTES" <<'EOF'
<one-sentence TL;DR>

## Breaking changes
<only if any — migration table with before/after; omit the section otherwise>

## New features
- <item> (#<issue>)

## Fixes
- <item> (#<issue>)

## Under the hood
- <item> (#<issue>)

Full history: [CHANGELOG.md](./CHANGELOG.md).
EOF
```

Section order and wording match the project's previous releases. If this is the first release, follow the template above.

**9. Create the GitHub release.**

```bash
gh release create vX.Y.Z \
  --title "<project> X.Y.Z" \
  --notes-file "$NOTES"
```

Do not pass `--draft` unless the operator asks — the pipeline's endpoint is a published release. Do not pass `--prerelease` for a standard cut; reserve that flag for release candidates.

**10. Verify.**

```bash
gh release view vX.Y.Z          # confirm body rendered, tag is live
gh api repos/:owner/:repo/releases/tags/vX.Y.Z --jq '.html_url'
```

Open the URL, eyeball it once. If the notes look wrong, do NOT rewrite the release — cut `vX.Y.Z+1` with corrections. Rewriting a published release loses the audit trail.

## After the release

- Link the release URL back into each closed issue's final comment (ship-cycle Step 11 handles this).
- Close the milestone if it is still open: `gh api repos/:owner/:repo/milestones/<N> -X PATCH -f state=closed`.
- Remove the temp release-notes file: `rm "$NOTES"`. It is not committed and not preserved — CHANGELOG is the source of truth.

## Rollback

You cannot rollback a pushed tag without rewriting history, and rewriting history is banned. If a release shipped broken:

1. Cut a patch (`vX.Y.Z+1`) with the fix, following the full pipeline.
2. Edit the broken release's notes on GitHub to add a *"Known issue — use vX.Y.Z+1"* banner at the top. Do not delete the broken release.
3. If the break is severe (data loss, security), also mark the broken release as `gh release edit vX.Y.Z --prerelease` so the Latest badge moves to the fix.

Never `git tag -f` and never `git push --force origin vX.Y.Z`. Operators and CI systems cache tag SHAs; moving a tag silently invalidates them.
