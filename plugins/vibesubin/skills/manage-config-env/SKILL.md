---
name: manage-config-env
description: Opinionated defaults for the structural decisions non-developers shouldn't have to invent. Decides where a value lives (constant in source, .env, CI secret, environment variable), scaffolds .env.example and .gitignore, picks a branch strategy (GitHub Flow by default), enforces dependency pinning, and audits for hardcoded paths. Language-agnostic.
when_to_use: Trigger on "where should this config go", ".env", "environment variable", "branch strategy", "main or dev", "gitignore", "dependency version", "pin this", "config management", or when onboarding a new project that needs a baseline layout.
allowed-tools: Read Write Edit Glob Grep Bash(grep *) Bash(git *) Bash(gh secret *) Bash(vercel env *) Bash(fly secrets *) Bash(netlify env *) Bash(railway variables *) Bash(gcloud *) Bash(aws *)
---

# manage-config-env

The operator has to make structural decisions every week: where does this value live? Should I pin this dependency? Is this `.env` entry right? Which branch should I work on? Each decision is a small tax on their attention. This skill pre-pays that tax with one opinionated answer per question.

**The principle**: the best structure is the one the operator doesn't have to invent. When they ask "where should this go?", answer immediately and explain in one sentence. Don't present a decision framework; make the decision.

## The four buckets — where does a value live?

Every value in a project fits into exactly one of these four buckets. Use this decision tree to place anything.

```
Value
│
├── Does it NEVER change at runtime? (colors, labels, fixed limits)
│   └── YES → Constant in source code
│       Example: MAX_RETRIES = 3
│       Rule: Commit it to git, give it a descriptive name, UPPER_SNAKE_CASE
│
├── Does it change per environment (dev/staging/prod)?
│   │
│   ├── Is it a secret? (token, password, private key, DB URL)
│   │   │
│   │   ├── Local development environment?
│   │   │   └── `.env` file (gitignored) + committed `.env.example`
│   │   │
│   │   └── Production / CI environment?
│   │       └── CI / platform secret store (GitHub Secrets, Vercel env vars, Fly secrets, etc.)
│   │           Rule: Never echo secrets in logs. Reference by name only.
│   │
│   └── Non-secret but env-specific? (log level, feature flag, port)
│       └── Environment variable
│           Example: LOG_LEVEL=debug, PORT=8080
│
└── Is it user-configurable at runtime? (theme, locale, preferences)
    └── Runtime config (database row, config file, API call)
        Not this skill's concern. Use whatever pattern the app already has.
```

When the operator asks where a value should go, walk down this tree with them in one sentence: *"This is a production database URL, so it belongs in your CI provider's secret store — not `.env`, because `.env` is local only."*

## Secrets management — CLI over dashboards

Every hosting provider has a web UI for secrets, and every one of them also has a CLI that does the same thing faster and scripts cleanly. **Prefer the CLI path** — it's reproducible, diffable, and can live in a `vm_setup.sh` or a bootstrap script.

**Do it the careful way**: never paste a real secret directly into a command. Load it into a shell variable or a gitignored local file first:

```bash
# Prompt without echoing the value to the terminal
read -sr DATABASE_URL && export DATABASE_URL && echo

# Or load from a local file that is already gitignored
export DATABASE_URL="$(< .secrets/database_url)"
```

Then reference `"$DATABASE_URL"` in the CLI call. This keeps the real value out of docs, screenshots, and casual copy-paste examples.

**Per-platform CLI cheatsheet** — GitHub, Vercel, Netlify, Fly.io, Railway, Cloud Run, AWS — is in `references/secrets-cli.md`. Open it only when the operator is actually setting secrets for a specific host.

**Core rules**, regardless of host:

- When in doubt, start with the CLI. A 5-line shell script that sets the secrets is reproducible and documentable.
- Never put a literal secret value in a commit message, PR body, screenshot, or shell history. Use placeholders, prompted input, shell variables, or file redirection in docs.
- OIDC-federated identity beats a static secret when the platform supports it (AWS, GCP, Azure, Vault). The operator never has to rotate a credential that doesn't exist.
- Rotate after every departing collaborator. It's a one-line CLI command.

The deploy-workflow side of secrets (how CI consumes them) lives in the `setup-ci` skill. This skill answers where the value *lives*; `setup-ci` answers how the workflow *uses* it.

## `.env` and `.env.example` — the rule

The rule about `.env` is short:

- **`.env`** — local only, never committed, contains real values.
- **`.env.example`** — always committed, contains every key with either a safe default or a `__REPLACE_ME__` placeholder, serves as the canonical list of required variables.
- **The key sets MUST match.** If `.env` has `DATABASE_URL` and `.env.example` doesn't, someone will clone the repo and not know about that variable. When the skill adds a new env var, it updates both files.

The ready-to-use starter `.env.example` with `__REPLACE_ME__` placeholders, commented sections for required vs optional, and safe defaults for common knobs lives in `templates/.env.example.template`. Copy it, fill in the real keys, and you're done.

### Startup validation

A `.env.example` with `__REPLACE_ME__` placeholders only works if the application **refuses to start** when it sees them. Add a check in the application's boot path, before any real work. Ready-to-paste patterns for Python, Node, and Go live in `references/startup-validation.md`.

The core rule is the same across languages: read the value, check for empty or placeholder, abort boot with a clear error. Do not continue with a fallback — fallbacks hide the problem.

### Drift check — keep `.env.example` honest

The example file becomes useless the moment it drifts from the real `.env`. A ready-to-run drift check lives at `scripts/check-env-drift.sh` — wire it into the project's test workflow so a missing variable in the example gets caught on every PR.

## `.gitignore` — the default-safe template

Non-developers routinely commit `.env`, SSH keys, build artifacts, and OS litter because they don't know to exclude them. The plugin ships a comprehensive default `.gitignore` at `templates/.gitignore.template` that blocks the usual suspects across Python, Node, Rust, Go, Java, OS / IDE, and local-only files.

Drop it in, trim the language sections the project doesn't use, and commit. If an existing `.gitignore` is missing secret-shaped entries (`.env`, `*.pem`, `id_rsa`), add them immediately — those are the ones that cause real incidents.

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

Core patterns to grep for: `C:\\`, `/Users/<name>`, `/home/<name>`, literal IPv4 addresses, `\\` in string literals, `/tmp/<specific>`. The full pattern-and-fix table with language-specific equivalents is in `references/path-portability.md`. When the audit finds more than a couple of files, hand off to `refactor-safely` for the 1:1 preservation work.

## Output format — when asked a structural question

Don't dump the entire skill. Answer the specific question in one paragraph and offer a concrete next step:

**Operator:** *"Where should my DB password go?"*
**You:** *"In `.env` for local dev, in your CI provider's secret store for production. Don't put it in source code or in `.env.example`. I can set up `.env.example` with `DATABASE_URL=__REPLACE_ME__` as a placeholder now — want me to?"*

**Operator:** *"Should I make a dev branch?"*
**You:** *"Probably not — GitHub Flow (just `main` with short-lived feature branches) is simpler for 95% of projects. What's driving the question?"*

**Operator:** *"Dependabot is annoying, can I turn it off?"*
**You:** *"You can pause it, but I'd recommend keeping it on at a monthly cadence. Most CVE exposure on small projects comes from ignored dependency updates. Want me to switch it to monthly?"*

## Things not to do

- Don't offer multiple options when one is clearly better. Pick the default.
- Don't teach git when the operator asked a branch question. Answer the branch question; they can learn git separately.
- Don't silently change the existing layout. If the repo already has a specific structure, propose changes and wait for confirmation — `manage-config-env` is advisory, not autonomous.
- Don't commit `.env`. Ever. If you see `.env` tracked in git, flag it immediately and hand off to `audit-security` for remediation.
- Don't store secrets in `.env.example`. That file is committable; real secrets go in `.env`.

## Hand-offs

- Secrets already committed to git → `audit-security` immediately, then rotate.
- Branch strategy conflict with existing maintainer convention → respect the maintainer; use `write-for-ai` to document the existing convention in `CLAUDE.md`.
- Dependency audit finds CVEs → `audit-security` for severity, `refactor-safely` for the upgrade diff.
- Config refactoring across many files → `refactor-safely` for the 1:1 preservation.

## References and templates

- `references/secrets-cli.md` — per-platform CLI walkthroughs (GitHub, Vercel, Netlify, Fly, Railway, Cloud Run, AWS)
- `references/startup-validation.md` — Python / Node / Go patterns for refusing to start on unfilled `__REPLACE_ME__`
- `references/branch-strategy.md` — when NOT to use GitHub Flow, inherited `dev` branches, release branches
- `references/directory-layout.md` — full naming table and structural-smell detection
- `references/path-portability.md` — pattern-and-fix table with language-specific equivalents
- `templates/.env.example.template` — starter `.env.example` with `__REPLACE_ME__` placeholders
- `templates/.gitignore.template` — comprehensive default `.gitignore`
- `templates/dependabot.yml.template` — starter dependency-update config
- `scripts/check-env-drift.sh` — CI script that fails if `.env` and `.env.example` key sets diverge
