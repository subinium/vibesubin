---
name: project-conventions
description: Opinionated defaults for the lower-stakes structural conventions every project has to pick — branch strategy, directory layout, dependency pinning, path portability. The companion to manage-secrets-env (which owns the high-stakes secrets/env slice). Picks GitHub Flow, enforces pinned dependencies, nudges toward domain-first directory structure, and audits for hardcoded absolute paths. Language-agnostic.
when_to_use: Trigger on "branch strategy", "main or dev", "GitHub Flow", "directory layout", "folder structure", "dependency version", "pin this", "Dependabot", "Renovate", "hardcoded path", "absolute path", "Windows path", "path portability", "lockfile", or when starting a new project that needs a baseline layout.
allowed-tools: Read Write Edit Glob Grep Bash(grep *) Bash(git *) Bash(find *) Bash(ls *)
---

# project-conventions

The operator has to make a handful of structural decisions on every new project that are not about secrets: which branch do I work on, where do files go, do I pin dependencies, how do I avoid hardcoding my home directory into source. Each one is a small tax on attention. Most of them have one answer that works for 95% of projects.

This skill pre-pays that tax with one opinionated answer per question. The high-stakes slice — secrets, `.env`, secret-shaped gitignore entries, CI secret stores — lives in `manage-secrets-env`. Split this way so the operator can trigger the right depth of care for the right question.

**The principle**: the best convention is the one the operator doesn't have to invent. When they ask *"should I make a dev branch?"*, answer in one sentence and move on. Don't present a decision framework; make the decision.

## Dependency versioning — pin or bleed

Unpinned dependencies are time bombs. The rule is simple and per-language.

**Required everywhere**: every production dependency is pinned to an exact version, and the lockfile is committed.

- Python: `requirements.txt` with `package==1.2.3` or `pyproject.toml` + `uv.lock` / `poetry.lock`.
- Node: `package.json` + `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` / `bun.lockb`.
- Rust: `Cargo.toml` + committed `Cargo.lock` (yes, even for libraries now).
- Go: `go.mod` + `go.sum`, both committed.
- Ruby: `Gemfile` + `Gemfile.lock`.
- PHP: `composer.json` + `composer.lock`.
- Java / Kotlin: explicit versions in `pom.xml` / `build.gradle` — never `latest` or `+`.

**Strongly recommended**: a dependency-update bot is active. GitHub ships Dependabot; Renovate works for GitLab and self-hosted. Weekly frequency for non-security updates, immediate for security. A starter `dependabot.yml` is in `templates/dependabot.yml.template`.

**Optional**: CVE auditing in CI — `pip-audit` / `npm audit` / `cargo audit` / `govulncheck`. Add it as a warning first; promote to a hard fail once the baseline is clean.

When the operator adds a new dependency, the skill confirms: (1) the version is pinned, (2) the lockfile is updated and committed, and (3) the dependency actually exists. LLM-recommended packages are occasionally hallucinations — catch them before they ship.

## Branch strategy — GitHub Flow by default

Most vibe-coder projects do not need `git-flow`. GitHub Flow is simpler, safer, and widely supported. Use it unless there's a specific reason not to:

- **One long-lived branch**: `main`. Always deployable. Protected. No direct pushes after the first day.
- **Short-lived feature branches**: `feature/<topic>`, `fix/<topic>`, `refactor/<topic>`, `chore/<topic>`, `docs/<topic>`, `hotfix/<topic>`. Lifetime: hours to days, never weeks.
- **Merged via** pull request → review → squash or merge commit → delete the branch.
- **Tags for releases** — optional for apps, recommended for libraries.

The full discussion — when NOT to use GitHub Flow, what to do about inherited `dev` branches, staging environments, library maintainers with multiple major versions — lives in `references/branch-strategy.md`. Read it only if the operator has a specific reason to deviate from the default.

## Directory layout — three quiet rules

Directory structure is the most underrated form of documentation. A clean tree tells a cold reader (human or AI) what the project does in 30 seconds.

Three cross-language rules the skill applies quietly:

1. **Domain-first, type-second.** Group by feature (`auth/`, `billing/`), not by file type (`handlers/`, `services/`). Type-based layouts stop scaling around 20 domains.
2. **No flat directory above ~15 files.** At the threshold, sub-group by intent or by date.
3. **Names are predictions.** Every directory name should predict what's inside. Match the naming conventions the skill recommends — verbs for functions, nouns for types, `is_` / `has_` for booleans, `UPPER_SNAKE_CASE` for constants.

The full naming table and structural-smell detection list is in `references/directory-layout.md`.

## Path portability — the audit

Every absolute path, IP literal, username, or platform separator in source is a time bomb. This sub-skill audits for them and offers one-line fixes.

Core patterns to grep for: `C:\\`, `/Users/<name>`, `/home/<name>`, literal IPv4 addresses, `\\` in string literals, `/tmp/<specific>`. The full pattern-and-fix table with language-specific equivalents is in `references/path-portability.md`. When the audit finds more than a couple of files, hand off to `refactor-verify` for the 1:1 preservation work.

## Output format — when asked a structural question

Don't dump the entire skill. Answer the specific question in one paragraph and offer a concrete next step:

**Operator:** *"Should I make a dev branch?"*
**You:** *"Probably not — GitHub Flow (just `main` with short-lived feature branches) is simpler for 95% of projects. What's driving the question?"*

**Operator:** *"Dependabot is annoying, can I turn it off?"*
**You:** *"You can pause it, but I'd recommend keeping it on at a monthly cadence. Most CVE exposure on small projects comes from ignored dependency updates. Want me to switch it to monthly?"*

**Operator:** *"Where does this helper function go?"*
**You:** *"Group by feature, not file type — if it's part of auth, `src/auth/helpers.ts`; if it's generic, `src/lib/...`. Flat `utils/` folders stop scaling around 15 files."*

## Things not to do

- Don't offer multiple options when one is clearly better. Pick the default.
- Don't teach git when the operator asked a branch question. Answer the branch question; they can learn git separately.
- Don't silently change the existing layout. If the repo already has a specific structure, propose changes and wait for confirmation — this skill is advisory, not autonomous.
- Don't touch `.env`, `.gitignore`, or any secret-shaped file. Those are `manage-secrets-env`'s responsibility.
- Don't lecture about `git-flow` vs GitHub Flow vs trunk-based development. Pick GitHub Flow, state the reason in one sentence, move on.

## Sweep mode — read-only audit

When invoked from `/vibesubin` (the umbrella skill's parallel sweep), this skill runs in **read-only audit mode**. Do not scaffold any files, do not edit any config, do not touch the directory structure.

Instead, produce a findings-only report:

- Branch strategy: does the repo deviate from GitHub Flow, and if so, is the deviation documented anywhere?
- Dependency pinning: unpinned prod dependencies, missing lockfile, unused packages in the manifest, Dependabot/Renovate not configured.
- Directory layout smells: flat directories over 15 files, type-first grouping where domain-first would work better, orphaned top-level directories.
- Hardcoded path audit: absolute paths, literal IPs, username references in source, Windows path separators in string literals.
- Stoplight verdict: 🟢 conventions are clean / 🟡 drift or minor hygiene gaps / 🔴 unpinned prod deps, portability bugs that will break on another machine.
- A one-line "fix with" pointer indicating `/project-conventions` will apply the scaffolds or fixes when invoked directly.

The operator reviews the sweep report and, if they want the fixes applied, invokes `/project-conventions` directly.

How to tell: the task context from the umbrella will include a `sweep=read-only` marker or an explicit "produce findings only, do not edit" instruction. Obey it. If the operator invokes this skill by name, the full procedure applies and editing is expected.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"*), switch output rules:

- **Lead with the worst finding.** If production dependencies are unpinned or the repo has `/Users/alice/...` in source, that's the first line of the report — with file, line, and a one-sentence consequence.
- **No softening words.** Drop *"consider pinning"*, *"might want to check"*, *"probably should"*. Replace with direct verbs: *"pin every dep in `requirements.txt` — `requests` is floating and broke last month"*, not *"you may want to consider pinning dependencies"*.
- **Portability bugs get blast-radius framing.** Balanced mode says *"hardcoded path in `src/config.ts:42`"*. Harsh mode says *"`src/config.ts:42` hardcodes `/Users/alice/Projects/foo` — this repo does not run on any other machine."*
- **Branch deviations get a verdict.** *"This repo uses `dev` branch for no documented reason. Either document why, or delete `dev` and move to GitHub Flow."* Not *"branch strategy deviates from GitHub Flow; consider documenting."*
- **No *"nice to have"* trailing items.** If something is below MEDIUM severity, omit it entirely in harsh mode.
- **Summary line is direct.** *"Three unpinned deps, one hardcoded home path, no lockfile — fix the three before the next deploy."* Not *"a few items to clean up when you have time."*

Harsh mode does not invent findings, exaggerate severities, or become rude. Every harsh statement must still cite the same file, line, or lockfile absence the balanced version would cite. The change is framing, not substance.

## Hand-offs

- `.env`, secrets, `.gitignore` entries for secret-shaped files, anything where a mistake leaks a credential → `manage-secrets-env`. That skill owns the high-stakes slice.
- Dependency audit finds CVEs → `audit-security` for severity, `refactor-verify` for the upgrade diff.
- Layout refactor touching many files (directory rename, domain-first reorganization) → `refactor-verify` for the 1:1 preservation and symbol-level proof.
- Hardcoded-path audit finds more than a couple of files → `refactor-verify` to apply fixes across the codebase safely.
- Documentation of the chosen conventions in `CLAUDE.md` or `README.md` → `write-for-ai` with the rationale.
- Binary bloat or oversized asset files found during the layout audit → `manage-assets`.

## References and templates

- `references/branch-strategy.md` — when NOT to use GitHub Flow, inherited `dev` branches, release branches
- `references/directory-layout.md` — full naming table and structural-smell detection
- `references/path-portability.md` — pattern-and-fix table with language-specific equivalents
- `templates/dependabot.yml.template` — starter dependency-update config
