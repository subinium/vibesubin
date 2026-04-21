---
name: manage-assets
description: Finds oversized files, binary bloat, and accidental artifact commits in a repo — large files currently tracked, large blobs hiding in git history, LFS migration candidates, asset directories growing without a policy, duplicate binaries. Pure diagnosis — never edits, never deletes, never rewrites history. Hands off to manage-secrets-env if secrets are found inside blobs, to refactor-verify if history rewriting is required, to fight-repo-rot if assets are unused. Language-agnostic.
when_to_use: Trigger on "my repo is huge", "why is this repo so big", "large files", "binary bloat", "git clone is slow", "should I use LFS", "delete a big file from history", "repo size", "hundreds of MB of images", "DB file in git", or before open-sourcing a repo that might have accidentally committed artifacts.
allowed-tools: Grep Glob Read Bash(git log *) Bash(git ls-files *) Bash(git rev-list *) Bash(git cat-file *) Bash(git verify-pack *) Bash(du *) Bash(find *) Bash(file *) Bash(wc *) Bash(sort *) Bash(awk *)
---

# manage-assets

Repos don't get slow from code. They get slow from binaries — a PDF committed last year, a 400 MB SQLite file a junior engineer checked in, a `node_modules/` that snuck past `.gitignore`, a `dist/` directory nobody bothered to exclude. A single 200 MB blob in git history turns `git clone` into a coffee break for every new collaborator, forever.

This skill surfaces that bloat. It is **diagnosis-only** — it never deletes a file, never rewrites history, never runs `git filter-repo`, never migrates to LFS. When the operator approves a finding, the skill hands off: `refactor-verify` for delete-from-history operations (it owns the verification discipline), `manage-secrets-env` if a leaked credential turns up inside a blob, `fight-repo-rot` if the asset is unused.

**What this skill is:** a sorted list of what's making the repo heavy, with provenance and a proposed fix owner.

**What this skill is not:** a history-rewriting tool, an LFS migration executor, or a dead-code detector (that's `fight-repo-rot`). It surfaces bloat; it does not remove bloat.

## State assumptions — before acting

Before starting the procedure, write an explicit Assumptions block. Don't pick silently between interpretations; surface the choice. If any assumption is wrong or ambiguous, pause and ask — do not proceed on a guess.

Required block:

```
Assumptions:
- Public clones:     <none known | public repo with active clones/forks (history rewrite requires coordination)>
- git-lfs:           <installed + initialized | available but uninitialized | not installed>
- Requested action:  <diagnosis only (default) | destructive hand-off to refactor-verify for history rewrite or LFS migration>
- Secret-shaped blob: <none | FOUND in history — hand off to audit-security, do not auto-propose removal>
```

Typical items for this skill:

- Whether the repo has public clones or forks (history rewrites require coordination with all of them)
- Whether `git lfs` is installed and initialized
- Whether the operator wants diagnosis-only (default) or is asking for a destructive action (history rewrite / LFS migration) — the skill itself is diagnosis-only and hands off destructive work to refactor-verify

Stop-and-ask triggers:

- History rewrite proposed on a repo with known public clones — require explicit acknowledgment of coordination burden before hand-off
- A "large file" is actually in active use — don't recommend removal, recommend LFS migration instead

Silent picks are the most common failure mode: the skill runs, produces plausible output, and the operator doesn't notice the wrong interpretation was chosen. The Assumptions block is cheap insurance.

## When to trigger

- "my repo is huge" / "why is this so big"
- "git clone is slow"
- "I committed a big file"
- "should I use LFS"
- "delete a big file from history"
- "hundreds of MB of images"
- "DB file in git"
- before open-sourcing (clone speed becomes a first impression)
- during a storage quota warning on the host (GitHub, GitLab free tiers)
- when `git gc` warns about loose objects or pack size

## Primary category: large files in the working tree

The simplest and highest-signal check. What files currently tracked by git exceed a size threshold? These are the first targets because they are the easiest to diagnose — the file still exists, you can open it, you can tell what it is.

```bash
# Every tracked file larger than 1 MB, sorted biggest first
git ls-files -z | xargs -0 du -b 2>/dev/null \
  | sort -rn | head -50

# Or using find over git-tracked files only
git ls-files | while read f; do
  [ -f "$f" ] && printf '%s\t%s\n' "$(wc -c <"$f")" "$f"
done | sort -rn | head -50
```

Thresholds the skill uses by default:

| Size | Severity | Why |
|---|---|---|
| **> 100 MB** | 🔴 CRITICAL | GitHub hard limit — host will reject the push. Must fix. |
| **> 50 MB** | 🔴 HIGH | GitHub warning threshold. `git clone` is painful on slow connections. |
| **> 10 MB** | 🟡 MEDIUM | Worth knowing about. Almost never source code; usually a binary artifact. |
| **> 1 MB** | 🟢 LOW | Normal for images, lockfiles, some PDFs. Only flag if suspicious. |

For every hit, classify by file type:

- **Source-like** (large JSON, large CSV, large SQL) — usually fine, but consider whether it belongs in LFS or a separate data repo.
- **Binary artifacts** (`.zip`, `.tar.gz`, `.exe`, `.dmg`, `.dll`, `.so`, compiled `.a`, built `dist/`, `node_modules/`) — almost always a mistake. Flag with HIGH confidence.
- **Media** (images, video, audio, PDFs, fonts) — may be intentional. Flag for LFS consideration if repeated or over 10 MB.
- **Databases** (`.sqlite`, `.db`, `.mdb`, `.realm`) — almost never belong in git. Flag as CRITICAL regardless of size.
- **Secrets-shaped** (`.pem`, `.key`, `.p12`, `id_rsa`, `*.credentials.json`) — incident. Hand off to `manage-secrets-env` immediately.

## Secondary category: large blobs in git history

A file currently in the working tree is visible. A file deleted from the working tree but still in git history is invisible to `ls` and `git ls-files`, but every `git clone` still downloads it. This is the single most common cause of an unexpectedly huge repo.

```bash
# Every object in the repo, ranked by on-disk size
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob" {print $3, $4}' \
  | sort -rn | head -30

# Which commit(s) introduced the blob? — useful for context
git log --all --oneline --find-object=<sha>
```

Findings here are tagged with an extra field: **reachable in HEAD** (still in the working tree) vs **historical only** (deleted from HEAD but preserved in history). Historical-only blobs require history rewriting to remove — which is destructive and breaks every existing clone.

**Never rewrite history as part of this skill.** If the operator approves a historical-blob removal, hand off to `refactor-verify` with the specific blob SHA and a removal plan. Force-push to a shared branch is a coordination problem, not a technical one.

## Secondary category: LFS migration candidates

Files that should probably have been in Git LFS from day one. Rule of thumb: any file that is both **binary** and **over 10 MB**, or **any file over 50 MB**.

```bash
# Is LFS already installed / configured?
git lfs env 2>/dev/null | head
git lfs ls-files 2>/dev/null | wc -l
cat .gitattributes 2>/dev/null | grep -E 'filter=lfs'
```

Report:

- **LFS already configured** — list which patterns are tracked and whether any large files in the working tree match none of them (escape hatches).
- **LFS not configured, large binaries present** — list the files and propose LFS patterns (e.g., `*.psd filter=lfs diff=lfs merge=lfs -text`).
- **Historical blobs that should have been LFS** — note that migration (`git lfs migrate import`) rewrites history, with the same warning as above.

The skill never runs `git lfs migrate`. It produces the list and the proposed `.gitattributes` additions; the operator decides.

## Secondary category: asset directory growth

Some directories are expected to grow — `assets/`, `public/`, `docs/images/`, `fixtures/`. The problem is not the directory; it's the lack of a policy. This audit answers: **is any directory growing without bound?**

```bash
# Disk usage per top-level directory, largest first
du -sh ./*/ 2>/dev/null | sort -rh | head -20

# Directories with more than 100 files
find . -type d -not -path '*/.git/*' -exec sh -c '
  count=$(find "$1" -maxdepth 1 -type f 2>/dev/null | wc -l)
  [ "$count" -gt 100 ] && printf "%s\t%s\n" "$count" "$1"
' _ {} \; | sort -rn | head -20
```

Flag:

- Any top-level directory over 100 MB that is not `node_modules` / `.venv` / `target/` (those should be gitignored).
- Any directory with more than 500 files that isn't obviously a code directory.
- `dist/` / `build/` / `out/` / `.next/` / `__pycache__/` / `.pytest_cache/` tracked in git (should be in `.gitignore`).

Hand off `.gitignore` gaps to `manage-secrets-env` (which owns the default-safe `.gitignore` template).

## Secondary category: duplicate binaries

Same file content under different paths is bloat twice over — you're paying storage for both copies, and you're guaranteed to edit one and forget the other. Detect by hash:

```bash
# Hash every tracked file, group by content
git ls-files -z | xargs -0 sha1sum 2>/dev/null \
  | sort | awk '{
      if ($1 == prev) { print prev, prev_path; print $1, substr($0, 42); }
      prev = $1; prev_path = substr($0, 42);
    }' | sort -u
```

Report clusters with 2+ files sharing the same SHA-1. Classify:

- **Identical assets in multiple locations** (same logo in `public/` and `src/assets/`) — candidate for a single-source-of-truth move, but not always wrong (build systems sometimes duplicate).
- **Duplicate lockfiles or config** — usually a bug.
- **Identical test fixtures** — candidate for a shared `fixtures/` directory.

## Output — prioritized diagnosis

```markdown
# Repo bloat report — <date>

## Stats
- Total repo size on disk: <N MB>
- .git directory size: <N MB>
- Working tree size: <N MB>
- Tracked files: <N>
- Files > 10 MB: <N>
- Files > 50 MB: <N>
- Historical blobs > 10 MB: <N>

## Critical (🔴)
- `data/users.sqlite` — 340 MB, tracked in HEAD. Database files never belong in git. **Fix with:** `refactor-verify` to delete from HEAD and history; `manage-secrets-env` to add `*.sqlite` to `.gitignore`.
- Historical blob `abc123...` — 180 MB, was `backup.tar.gz`, deleted in commit `def456` but still in history. **Fix with:** `refactor-verify` (rewrite history, coordinate force-push).

## High (🟡)
- `public/demo.mp4` — 42 MB, tracked in HEAD. Good LFS candidate. **Fix with:** LFS migration via `.gitattributes`, hand off to `refactor-verify` for the migration commit.
- `assets/fonts/` — 38 MB across 12 font files. Consider LFS or a CDN.

## Medium (🟢)
- `docs/images/` — 87 MB across 240 PNGs. Growing without a compression policy. **Fix with:** establish a max-size per image, batch-compress existing ones (not a skill job — the operator handles).

## LFS status
- LFS configured: no / yes
- If yes: patterns tracked = <list>
- Files that should be in LFS but aren't: <count>

## Proposed `.gitattributes` (if LFS migration is approved)
```gitattributes
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.psd filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
```

## `.gitignore` gaps found
- `dist/` tracked (should be ignored) — hand off to `manage-secrets-env`
- `.next/` tracked (should be ignored) — hand off to `manage-secrets-env`

## Hand-off summary
- **Delete from HEAD and history** (<N> items) → `refactor-verify`
- **LFS migration** (<N> items) → `refactor-verify` with proposed `.gitattributes`
- **`.gitignore` gaps** (<N> items) → `manage-secrets-env`
- **Unused assets that can be deleted outright** (<N> items) → `fight-repo-rot` to confirm unused, then `refactor-verify` to delete

## What this report did NOT do
Pure diagnosis. No files deleted, no history rewritten, no LFS migration run. Approve any item and it gets handed to the specialist that owns the fix.
```

## Things not to do

- **Never rewrite git history.** `git filter-repo`, `git filter-branch`, `bfg`, `git lfs migrate import` — none of these run from this skill. All of them destroy history and break every existing clone. They are always a `refactor-verify` handoff with operator confirmation and a coordinated force-push plan.
- **Never delete files.** Even a simple `git rm` of a 400 MB SQLite is not this skill's job. Diagnosis only. Flag it, hand it off.
- **Don't chase small wins.** A 1 MB file in a 10 GB repo is noise. Prioritize by size, not by count.
- **Don't confuse large with dead.** A file being big does not mean it's unused. A big asset might be actively referenced by the build. For "is this used" questions, that's `fight-repo-rot`.
- **Don't assume LFS is always the answer.** LFS costs money on most hosts and has its own operational overhead. Small teams with occasional large files often do fine with "just don't commit it." Recommend LFS only when the pattern is recurring.
- **Don't expand the diagnosis scope beyond what was asked.** This skill never edits; the scope-creep risk is in findings. If the operator asked about a specific large directory, don't hand back an all-repo blob scan with LFS recommendations for every binary. Adjacent findings go in a short "also worth looking at" footer — not the main bloat report.

## Sweep mode — read-only audit

This skill is **already diagnosis-only** — it never edits regardless of how it's invoked. When the umbrella runs it with `sweep=read-only`, behavior is identical to a direct invocation: produce the prioritized diagnosis report, hand off every approval to the right specialist.

The report format is the one above; the sweep just feeds the top-line stats and any CRITICAL / HIGH findings into the umbrella's synthesis step.

How to tell: if the task context includes `sweep=read-only`, shorten the report to stats + CRITICAL + HIGH only, skip the LFS proposed `.gitattributes`, and defer the operator-approval dialog to the umbrella's synthesis step.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"*), switch output rules:

- **Lead with the biggest file.** First line of the report is the worst offender, with exact size and the consequence. *"`data/users.sqlite` is 340 MB and is in every single clone of this repo, forever, until you rewrite history."* Not *"large SQLite file detected in the repo."*
- **No softening words.** Drop *"might want to consider"*, *"could be a candidate for"*, *"probably worth"*. Replace with direct verbs: *"delete this from history"*, *"move this to LFS now"*, *"this file should never have been committed"*.
- **Consequence framing on every finding.** Balanced mode says *"42 MB video tracked in git"*. Harsh mode says *"every `git clone` of this repo downloads this 42 MB video, even though nobody on the team needs it locally."*
- **LFS recommendations are directive, not suggestive.** *"Migrate `*.psd` to LFS before the next commit"* — not *"you might want to set up LFS for Photoshop files."*
- **No *"a few polish items"* closures.** If a repo has any file over 50 MB, the verdict line does not end on a positive note. *"Clean this up before you open-source — the first clone will take fifteen minutes on a hotel WiFi."*
- **Historical blobs get urgency language.** *"This 180 MB blob is no longer in the working tree but every past and future clone still downloads it. Fix with a history rewrite or stop recommending this repo to anyone on mobile."*

Harsh mode does not invent findings, exaggerate sizes, or become rude. Every harsh statement must cite the same `git rev-list` / `du` / `git ls-files` output the balanced version would cite. The change is framing, not substance.

## Hand-offs

- **Delete from HEAD only** (file is currently tracked, no history rewrite needed) → `refactor-verify` with `git rm` plus `.gitignore` addition
- **Delete from history** (large blob, deleted or not) → `refactor-verify` with `git filter-repo` plan and force-push coordination
- **LFS migration** → `refactor-verify` with proposed `.gitattributes` and migration steps; requires operator approval before touching history
- **`.gitignore` gaps** (build directories tracked, `node_modules/` tracked, etc.) → `manage-secrets-env` owns the default-safe `.gitignore` template
- **Asset is unused** (leftover from a prior feature) → `fight-repo-rot` to confirm unused, then `refactor-verify` to delete
- **Secret found inside a blob** (API key embedded in a committed binary, credentials in a ZIP) → `manage-secrets-env` and `audit-security` immediately; rotate first, delete second

## Details and tools

The full methodology is inlined in this `SKILL.md`. Tools worth knowing (install-on-demand):

- `git-sizer` — GitHub's official repo-size analyzer, flags path lengths, blob size distribution, tree depth
- `git-filter-repo` — the current recommended tool for history rewriting (replaces `git filter-branch`)
- `bfg-repo-cleaner` — older, Java-based; still useful for specific patterns
- `git lfs` — official LFS CLI; `git lfs migrate import` for bulk migration (history-rewriting)
- `du` / `find` — universal primitives, always available
- `scc` / `tokei` — not for bloat but for separating source LOC from "everything else"

Scripts and references are intentionally minimal — the primary deliverable is the diagnostic report, and the analysis lives in the single SKILL.md so nothing drifts out of sync.
