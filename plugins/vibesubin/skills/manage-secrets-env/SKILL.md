---
name: manage-secrets-env
description: Opinionated defaults and full lifecycle playbook for secrets and environment variables. Decides where a secret or env-specific value lives (constant, .env, CI secret, env var), scaffolds .env.example and .gitignore, and manages the lifecycle end to end — add, update, rotate, remove, migrate between buckets, audit cross-environment drift, provision new environments. High-stakes companion to project-conventions. Language-agnostic.
when_to_use: Trigger on "where should this secret go", ".env", "environment variable", "rotate this secret", "remove unused env var", "migrate to env var", "add staging environment", "check env drift", "audit secrets across environments", ".gitignore" (for secret-shaped entries), "secret management", or when onboarding a new project that needs a baseline secrets layout.
allowed-tools: Read Write Edit Glob Grep Bash(grep *) Bash(git *) Bash(gh secret *) Bash(vercel env *) Bash(fly secrets *) Bash(netlify env *) Bash(railway variables *) Bash(gcloud *) Bash(aws *)
---

# manage-secrets-env

Every project has two kinds of structural decisions. Some are low-stakes — which branch naming, which directory layout — and a mistake costs a little friction. Some are high-stakes — where a database password lives, whether `.env` is tracked, whether a production token is in a build-time variable — and a mistake costs an incident.

This skill owns the high-stakes slice: **secrets, environment variables, and the gitignore that protects them**. The low-stakes conventions (branches, directories, dep pinning, path portability) live in `project-conventions`. Splitting them this way means the operator can trigger the right depth of care for the right question.

**The principle**: the safest default is the one the operator doesn't have to invent. When they ask *"where does my DB password go?"*, answer immediately, explain in one sentence, and offer to scaffold.

## State assumptions — before acting

Before starting the procedure, write an explicit Assumptions block. Don't pick silently between interpretations; surface the choice. If any assumption is wrong or ambiguous, pause and ask — do not proceed on a guess.

Required block:

```
Assumptions:
- Environment tier:  <dev | staging | prod — affects which bucket rules apply>
- .env.example:      <present | missing (drift check cannot run yet, operator must scaffold first)>
- Tracked secrets:   <none detected | FOUND — this is an incident; hand off to audit-security immediately, do not proceed with lifecycle workflows>
- Lifecycle action:  <audit only | add | update | rotate | remove | migrate | provision new env>
```

Typical items for this skill:

- Current environment tier (dev / staging / prod) — affects which bucket rules apply
- Whether `.env.example` exists — affects drift-check baseline
- Whether any secret-shaped value is tracked in git or git history (this is always an incident if true)

Stop-and-ask triggers:

- A tracked secret is detected — **immediate hand-off to audit-security incident mode**, do NOT proceed with normal lifecycle workflows
- Operator asks to "rotate" without naming which secret — list the candidates and ask

Silent picks are the most common failure mode: the skill runs, produces plausible output, and the operator doesn't notice the wrong interpretation was chosen. The Assumptions block is cheap insurance.

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

**Secret-shaped entries to verify on every audit**: `.env`, `.env.*` (except `.env.example` / `.env.*.template`), `*.pem`, `*.key`, `id_rsa*`, `id_ed25519*`, `credentials*`, `secrets*`, `*.p12`, `*.pfx`, service-account JSON keys (`*-sa.json`, `*.credentials.json`).

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

## Output format — when asked a structural question

Don't dump the entire skill. Answer the specific question in one paragraph and offer a concrete next step:

**Operator:** *"Where should my DB password go?"*
**You:** *"In `.env` for local dev, in your CI provider's secret store for production. Don't put it in source code or in `.env.example`. I can set up `.env.example` with `DATABASE_URL=__REPLACE_ME__` as a placeholder now — want me to?"*

**Operator:** *"Is my `.env` safe?"*
**You:** *"Checking. `.env` is gitignored ✅. `.env.example` has 8 keys, real `.env` has 10 — `STRIPE_KEY` and `SENTRY_DSN` are missing from the example. Want me to add them as `__REPLACE_ME__` placeholders?"*

## Things not to do

- Don't offer multiple options when one is clearly better. Pick the default.
- Don't silently change the existing layout. If the repo already has a specific structure, propose changes and wait for confirmation.
- Don't commit `.env`. Ever. If you see `.env` tracked in git, flag it immediately and hand off to `audit-security` for remediation.
- Don't store secrets in `.env.example`. That file is committable; real secrets go in `.env`.
- Don't touch non-secret conventions (branches, directory layout, dep pinning). Those live in `project-conventions`.
- **Don't add features the operator did not request.** If they asked to rotate one secret, don't also scaffold `.env.example` as a bonus, and don't add startup-validation to an app that didn't request it. Adjacent lifecycle gaps (`.env.example` missing, no startup validation, `.gitignore` incomplete) go in the final output as hand-off suggestions — each one is a decision the operator needs to make explicitly.

## Sweep mode — read-only audit

When invoked from `/vibesubin` (the umbrella skill's parallel sweep), this skill runs in **read-only audit mode**. Do not scaffold `.env.example`, do not edit `.gitignore`, do not touch any config files. Do not run lifecycle workflows (no rotate, no remove, no migrate, no provision).

Instead, produce a findings-only report:

- Four-bucket audit: are values in the right place? Any secrets in source, any constants in env vars that should be in code, any production secrets sitting in `.env`?
- `.env.example` drift: does every key in `.env` have a matching entry in `.env.example`? Any `__REPLACE_ME__` placeholders still live in a real environment?
- `.gitignore` coverage: is `.env` actually ignored? Any `*.pem`, `id_rsa`, `credentials*` files missing?
- Tracked secrets: any secret-shaped files already in `git ls-files`? (These are incident-class — flag immediately and hand off to `audit-security`.)
- Stoplight verdict: 🟢 secrets layout is clean / 🟡 drift or minor hygiene gaps / 🔴 committed secrets, missing `.gitignore` entries, or other incident-class findings.
- A one-line "fix with" pointer indicating `/manage-secrets-env` will apply the scaffolds or run the lifecycle workflow when invoked directly.

The operator reviews the sweep report and, if they want the fixes applied, invokes `/manage-secrets-env` directly — which then runs the full opinionated procedure.

How to tell: the task context from the umbrella will include a `sweep=read-only` marker or an explicit "produce findings only, do not edit" instruction. Obey it. If the operator invokes this skill by name, the full procedure applies and editing is expected.

## Harsh mode — no hedging

When the task context contains the `tone=harsh` marker (usually set by the `/vibesubin harsh` umbrella invocation, but can also come from direct requests like *"don't sugarcoat"* / *"brutal review"* / *"매운 맛"* / *"厳しめ"*), switch output rules:

- **Lead with the worst finding**, not the four-bucket audit. If `.env` is tracked in git or a secret is in source, that's the first line of the report with file and line.
- **No softening words.** Drop *"could be"*, *"might"*, *"consider"*, *"you may want to"*, *"probably fine"*. Replace with blast-radius framing: *"your Stripe key is in `src/config.ts:14` and is readable by anyone who clones this repo"*, not *"potential secret exposure in config.ts"*.
- **Tracked secrets get incident language.** If `git ls-files` returns a secret-shaped file, the first line is *"Stop. Rotate the credential now. Handing off to `audit-security` incident runbook."* No preamble.
- **Drift findings get action verbs.** Balanced mode says *"`STRIPE_KEY` is missing from `.env.example`"*. Harsh mode says *"add `STRIPE_KEY=__REPLACE_ME__` to `.env.example` now — the next collaborator will clone a broken app."*
- **No *"mostly fine"* closures** when any finding is HIGH or CRITICAL. *"Don't ship until `.env` is untracked and `.gitignore` covers `*.pem`"*, not *"a couple of hygiene items to watch"*.
- **Stoplight stays literal.** Harsh mode does not inflate 🟡 to 🔴 — it tightens framing, not severity.

Harsh mode does not invent findings, fabricate severities, or become rude. Every harsh statement must still cite the same file, line, or `git ls-files` match the balanced version would cite. The change is framing, not substance.

## Hand-offs

- Secrets already committed to git → `audit-security` immediately for blast-radius assessment, then run the *Rotate a secret* workflow above as the incident path.
- Dependency audit finds CVEs → `audit-security` for severity, `refactor-verify` for the upgrade diff.
- Config refactoring across many files (e.g., *Migrate between buckets* touching dozens of call sites) → `refactor-verify` for the 1:1 preservation and symbol-level proof.
- A new env var needs to appear in README / `CLAUDE.md` env-var table → `write-for-ai` with the key, one-line purpose, and default or placeholder value.
- Dead code found during the *Remove* workflow → `fight-repo-rot` to confirm, then `refactor-verify` to delete safely.
- Branch strategy, directory layout, dep pinning, hardcoded path audits → `project-conventions`, which owns those lower-stakes conventions.

## References and templates

- `references/secrets-cli.md` — per-platform CLI walkthroughs (GitHub, Vercel, Netlify, Fly, Railway, Cloud Run, AWS)
- `references/startup-validation.md` — Python / Node / Go patterns for refusing to start on unfilled `__REPLACE_ME__`
- `references/secret-rotation.md` — provider-specific rotation recipes (AWS IAM, GCP SA keys, Stripe, OpenAI, DB users, JWT signing, OAuth)
- `references/lifecycle-workflows.md` — deep dive on add / update / rotate / remove / migrate / audit / provision with edge cases
- `templates/.env.example.template` — starter `.env.example` with `__REPLACE_ME__` placeholders
- `templates/.gitignore.template` — comprehensive default `.gitignore`
- `scripts/check-env-drift.sh` — pre-commit-friendly script that fails if `.env` and `.env.example` key sets diverge
