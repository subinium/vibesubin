---
name: manage-config-env
description: Opinionated defaults and full lifecycle playbook for config and secrets. Decides where a value lives (constant, .env, CI secret, env var), scaffolds .env.example and .gitignore, and manages the lifecycle end to end — add, update, rotate, remove, migrate between buckets, audit cross-environment drift, provision new environments. Also picks a branch strategy (GitHub Flow), enforces dependency pinning, and audits for hardcoded paths. Language-agnostic.
when_to_use: Trigger on "where should this config go", ".env", "environment variable", "rotate this secret", "remove unused env var", "migrate to env var", "add staging environment", "check env drift", "audit secrets across environments", "branch strategy", "main or dev", "gitignore", "dependency version", "pin this", "config management", or when onboarding a new project that needs a baseline layout.
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

The example file becomes useless the moment it drifts from the real `.env`. A ready-to-run drift check lives at `scripts/check-env-drift.sh` — wire it into a **pre-commit hook**, not CI. CI environments usually have no local `.env`, so the script would exit clean even when `.env.example` is out of date. Pre-commit catches it at the moment the operator adds a new variable.

### Build-time vs runtime env vars (Next.js, Vite, CRA)

Environment variables in frontend frameworks come in two flavors and the distinction causes the most common leak among non-developers.

- **Build-time / public** (`NEXT_PUBLIC_*` in Next.js, `VITE_*` in Vite, `REACT_APP_*` in CRA): baked into the client JavaScript bundle at build time. Anyone who views page source sees them. **Never put a secret in a build-time variable.** Safe uses: public API URLs, feature flags, non-secret configuration, analytics IDs.
- **Runtime / server-only** (anything without the framework's public prefix): only available to server-side code. Safe for database URLs, API keys, session secrets, signing keys.

If a value is secret and also needs to be visible in the browser, it does not belong in env vars — it belongs behind an API route that reads the server-side secret and returns only the derived data the client actually needs.

### Precedence when multiple `.env` files exist

Most frameworks load several `.env` files in a defined order. Later files override earlier ones. When debugging *"why is this env var wrong?"*, always confirm which file the framework actually loaded — a value in `.env` can be silently overridden by `.env.local`.

- **Next.js / Vite**: `.env` → `.env.<environment>` → `.env.local` → `.env.<environment>.local`. The `.local` variants are gitignored by convention; `.env.development` / `.env.production` are committed only if they contain non-secret defaults.
- **Node `dotenv`**: one file by default. Use `dotenv-flow` or an explicit chain for multi-file support.
- **Python `python-dotenv`**: one file by default; use `dotenv_values()` merging for explicit multi-file chains.
- **Ruby / Rails**: reads `.env.<environment>` through `dotenv-rails`, with `.env.local` as an override.

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

Core patterns to grep for: `C:\\`, `/Users/<name>`, `/home/<name>`, literal IPv4 addresses, `\\` in string literals, `/tmp/<specific>`. The full pattern-and-fix table with language-specific equivalents is in `references/path-portability.md`. When the audit finds more than a couple of files, hand off to `refactor-verify` for the 1:1 preservation work.

## Lifecycle workflows — the "manage" part

Placing a value in the right bucket is the first decision. Everything after is lifecycle: values get added, updated, rotated, removed, migrated between buckets, and audited across environments. This section is the opinionated playbook for each operation. Full per-step detail and edge cases live in `references/lifecycle-workflows.md`.

### Add a new value

Use the four-bucket tree to decide where it goes, then run this checklist:

1. Add to the chosen bucket (source constant, `.env` + `.env.example`, CI/platform secret store, or environment variable).
2. If it's in `.env`, add the same key to `.env.example` with `__REPLACE_ME__` as the value.
3. Add a startup validation check so the app refuses to boot without it. See `references/startup-validation.md`.
4. Document the variable in the env-var table in README or `CLAUDE.md`. Hand off to `write-for-ai` if the table is stale or missing.
5. Notify collaborators — if the app is deployed, the CI/platform secret must exist before the next deploy or startup validation will fail the rollout.

### Update an existing value

The trap is forgetting one environment. A password changed in local `.env` but not in GitHub Secrets breaks the next deploy. Update in this order:

1. Local `.env` first (fastest feedback).
2. Run the app locally against the new value; confirm it works before touching anything remote.
3. Update every remote secret store that references the key. List them explicitly — `gh secret list`, `vercel env ls`, `fly secrets list`, etc. Don't assume one store is the only one.
4. Trigger any cache that holds the value: edge config, CDN env, Lambda warmup, long-running workers that cache at boot.
5. Deploy and hit a health probe to confirm the new value is in effect.

### Rotate a secret

The most important lifecycle operation and the one most frequently skipped. Triggers: a collaborator leaves, a laptop is lost, a secret appears in logs, a scheduled rotation window, or a suspected leak. Incident rotation is the urgent path — scheduled rotation is the preventive one. Incident rotations hand off to `audit-security` first to assess blast radius.

**Zero-downtime rotation** (when the provider supports dual-valid credentials — most API keys, some JWT signing setups, IAM access keys):

1. Generate the new secret at the provider.
2. Add the new value alongside the old in every environment. Both are valid during the overlap window.
3. Roll the application once so every instance picks up the new value.
4. Remove the old value at the provider.
5. Verify the old value now fails authentication.
6. Append an entry to `ROTATION_LOG.md` at the repo root (date, key name, trigger, actor).

**Downtime rotation** (when dual-valid is not supported — database passwords, single-value signing secrets):

1. Schedule and announce a maintenance window.
2. Generate the new secret.
3. Put the app in maintenance mode (stop traffic or return 503 from a health gate).
4. Update every environment in a coordinated burst, starting from the authoritative store.
5. Roll the application.
6. Verify startup and a critical path, then re-open traffic.
7. Log the rotation.

Provider-specific rotation recipes (AWS IAM, GCP service account keys, Stripe, OpenAI, database users, JWT signing keys, OAuth client secrets) live in `references/secret-rotation.md`. Always prefer OIDC over rotatable secrets when the platform supports it — a credential that doesn't exist cannot be rotated or leaked.

### Remove an unused value

The trap is leaving orphan secrets in CI that nobody owns. Steps:

1. Grep the codebase for the key, including dynamic forms: string concatenation (`"DATABASE_" + "URL"`), template rendering, YAML/TOML/JSON config files, shell scripts, Dockerfiles, CI workflow files.
2. If any reference is found, decide whether it's dead code (hand off to `fight-repo-rot` to confirm, then to `refactor-verify` to delete) or legitimate usage (the value is not removable yet; stop).
3. Remove from `.env` and `.env.example` simultaneously so the drift check stays green.
4. Remove from every CI / platform secret store. Keep the list from the *Update* workflow above.
5. Remove from the env-var table in docs.
6. Deploy and monitor startup validation — if any environment silently depended on the key, you'll see it here, not in production traffic.

### Migrate between buckets

Triggers: a compile-time constant needs to vary per environment (source constant → env var), a local-only value becomes a shared secret (`.env` → CI secret store), a feature flag graduates from env var to a runtime config service. Steps:

1. Add the value to the new bucket without removing it from the old yet.
2. Update every call site to read from the new location.
3. Run the app and confirm it actually reads from the new location (log the source once at boot, or add a temporary assertion).
4. Remove from the old bucket.
5. Grep with a zero-match assertion that nothing still references the old location.
6. Hand off to `refactor-verify` for symbol-level validation that no caller was missed.

### Audit drift across environments

`.env` vs `.env.example` is the minimum check. The full audit compares every environment: local `.env`, staging, production, and each CI / platform secret store. Drift modes to detect:

- **Missing in target**: key present in source but absent in target. Deploy will fail on startup validation.
- **Extra in target**: key present in target but nowhere else. Orphan — candidate for the *Remove* workflow.
- **Same key, divergent value shape**: e.g., `DATABASE_URL` is a Postgres URL in prod but a SQLite path in staging. Runtime type mismatch.
- **Placeholder in a non-local environment**: any `__REPLACE_ME__` still present in staging or production.

The skill produces a table: key, value-shape fingerprint per environment (length, prefix, suffix — never the real value), drift verdict. **Never print real secret values** — fingerprints are the primitive for diffing secrets safely.

### Provision a new environment

Triggers: adding staging, spinning up a preview environment, onboarding a new deploy target, handing off a region. Steps:

1. Read `.env.example` as the canonical required-keys list.
2. Generate environment-specific values for every required key (a new database URL, a new domain, API keys scoped to the new environment, new OAuth client).
3. Set them in the new environment's secret store via the CLI in one scripted pass. The script lives in `scripts/` so the operator can re-run or inspect it.
4. Boot the app against the new environment. Startup validation is the test — missing keys fail loud.
5. Document the new environment in `CLAUDE.md` via `write-for-ai`: name, purpose, URL, who owns it, what it's safe to break.

---

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

- Secrets already committed to git → `audit-security` immediately for blast-radius assessment, then run the *Rotate a secret* workflow above as the incident path.
- Branch strategy conflict with existing maintainer convention → respect the maintainer; use `write-for-ai` to document the existing convention in `CLAUDE.md`.
- Dependency audit finds CVEs → `audit-security` for severity, `refactor-verify` for the upgrade diff.
- Config refactoring across many files (e.g., *Migrate between buckets* touching dozens of call sites) → `refactor-verify` for the 1:1 preservation and symbol-level proof.
- A new env var needs to appear in README / `CLAUDE.md` env-var table → `write-for-ai` with the key, one-line purpose, and default or placeholder value.
- Dead code found during the *Remove* workflow → `fight-repo-rot` to confirm, then `refactor-verify` to delete safely.

## References and templates

- `references/secrets-cli.md` — per-platform CLI walkthroughs (GitHub, Vercel, Netlify, Fly, Railway, Cloud Run, AWS)
- `references/startup-validation.md` — Python / Node / Go patterns for refusing to start on unfilled `__REPLACE_ME__`
- `references/secret-rotation.md` — provider-specific rotation recipes (AWS IAM, GCP SA keys, Stripe, OpenAI, DB users, JWT signing, OAuth)
- `references/lifecycle-workflows.md` — deep dive on add / update / rotate / remove / migrate / audit / provision with edge cases
- `references/branch-strategy.md` — when NOT to use GitHub Flow, inherited `dev` branches, release branches
- `references/directory-layout.md` — full naming table and structural-smell detection
- `references/path-portability.md` — pattern-and-fix table with language-specific equivalents
- `templates/.env.example.template` — starter `.env.example` with `__REPLACE_ME__` placeholders
- `templates/.gitignore.template` — comprehensive default `.gitignore`
- `templates/dependabot.yml.template` — starter dependency-update config
- `scripts/check-env-drift.sh` — pre-commit-friendly script that fails if `.env` and `.env.example` key sets diverge
