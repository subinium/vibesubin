# Lifecycle workflows — deep dive

`SKILL.md`'s *Lifecycle workflows* section is the short playbook. This reference is the long version: edge cases, failure modes, and the full checklists. Read when the operator hits something the short version doesn't cover.

## Add — edge cases

**Adding a value that already exists in a parallel project.** Don't import values wholesale from another repo's `.env.example`. Each project's env surface is deliberate; copying in foreign variables introduces dead config. Ask the operator which specific values they want, explain why each one exists, skip the ones they don't need.

**Adding a client-visible constant that's really a public API URL.** If a value is "secret-adjacent" (a Stripe publishable key, a Mapbox token, a PostHog key), confirm it's actually meant to be public. Some providers call them "public" in the docs but still treat exposure as a rate-limiting risk. Tag the value with a comment: `# safe to expose: intentional public key`.

**Adding a feature flag.** Prefer a runtime config service (LaunchDarkly, Unleash, PostHog feature flags, a database row) over an env var when the flag needs to toggle without a redeploy. Env vars are fine for flags that change weekly or less.

## Update — failure modes

**The cache that forgot.** CDN edge config, Lambda warm containers, Next.js ISR pages that baked a value at build time, React Native apps with a value baked into a native build, SQL stored procedures that embed a credential. List these explicitly before the update; don't assume "deploy the app" refreshes everything.

**The worker that boots once and caches forever.** Long-running workers (Celery, BullMQ, Sidekiq) often read env vars at boot and never re-read them. Updating the env var does nothing until the worker restarts. Put this in the runbook: after updating, list every process that needs a restart.

**The integration test that runs against the old value.** Update test fixtures and CI-time secrets at the same time. Otherwise the next test run fails against the new DB password while using the old one from a fixture.

## Rotate — special cases beyond `secret-rotation.md`

**Rotating a secret that's referenced from a build-time env var.** (`NEXT_PUBLIC_STRIPE_KEY`, `VITE_API_KEY`.) These are baked into the client bundle at build time, so rotation requires a rebuild + redeploy, not just a secret update. Clients with the old bundle will keep using the old value until they reload.

**Rotating a secret that's embedded in mobile app binaries.** Same problem, worse: the old value lives on every installed device until the user updates the app. Treat the old value as "compromised but still valid" for weeks, not seconds.

**Rotating when you're not sure what's consuming the secret.** Before rotating, enable audit logging at the provider if it exists. Watch the logs for a week. Every IP / user-agent / service ID that touches the key is a consumer you'll need to update. Only then rotate.

## Remove — false-positive detection

The point of the `grep` phase in the *Remove* workflow is to catch non-obvious references. Patterns to grep for, beyond the literal key name:

- **String concatenation**: `"DATABASE_" + "URL"`, `` `DATABASE_${suffix}` ``, `f"{prefix}_URL"`.
- **Dictionary access**: `os.environ["DATABASE_URL"]`, `env["DATABASE_URL"]`, `process.env.DATABASE_URL`, `ENV.fetch("DATABASE_URL")`.
- **Case variations**: `DatabaseUrl`, `databaseUrl`, `database_url`, `db-url`. Some frameworks auto-convert between `SCREAMING_SNAKE` and `camelCase`.
- **Config file references**: `app.yaml`, `fly.toml`, `vercel.json`, `netlify.toml`, `docker-compose.yml`, `Dockerfile`.
- **CI workflow files**: `.github/workflows/*.yml` (including `env:` blocks and `${{ secrets.DATABASE_URL }}`), `.gitlab-ci.yml`, `circle.yml`.
- **Infrastructure as code**: `terraform/*.tf`, `pulumi/*.ts`, CloudFormation `*.yml`, Pulumi / CDK sources.
- **Shell scripts and Makefiles**: often embed credentials for dev workflows.
- **Secret references in other secrets**: a webhook URL might embed a token (`https://hooks.slack.com/services/T.../B.../...`).

If any of these match, the key is not safe to remove. Resolve the reference first.

## Migrate between buckets — worked examples

**Source constant → env var** (most common):

```python
# before: hard-coded
MAX_REQUESTS_PER_MINUTE = 100
```

Steps:

1. Add `MAX_REQUESTS_PER_MINUTE=100` to `.env.example` (with the default as the value, since it's non-secret).
2. Add `MAX_REQUESTS_PER_MINUTE=100` to `.env`.
3. Replace the constant:
   ```python
   MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "100"))
   ```
4. Run the app; confirm it reads from the env var.
5. Hand off to `refactor-verify` to walk the symbol table and confirm every caller now reads the env-backed value.

**`.env` (local dev) → CI secret (shared production)**:

This happens when a value previously only needed locally starts being needed in production. Steps:

1. Add the value to the CI / platform secret store under the same name.
2. Deploy a canary and confirm startup validation passes.
3. Leave the value in local `.env` — local dev still needs it.
4. Update the env-var documentation to reflect that the value is now required in production.

**Env var → runtime config service** (e.g., LaunchDarkly):

The trickier migration. The env var was static; the runtime config service is dynamic. Callers need to switch from "read once at boot" to "read per request / with cache".

1. Keep the env var as a fallback.
2. Add the runtime config SDK. Wire it up to read the value.
3. Switch call sites to read from the SDK, falling back to the env var if the SDK is unavailable.
4. Deploy and confirm the SDK path is live.
5. After a stable week, remove the env var and the fallback path.

## Audit drift — fingerprint comparison

Real values never leave the tool. The audit compares fingerprints:

| Value type | Fingerprint |
|---|---|
| Random tokens | length, first 4 chars, last 4 chars |
| URLs | scheme, host, port, path shape (not query string) |
| JSON blobs | top-level key set (not values) |
| Numeric | exact value (unless it looks secret) |
| Booleans | exact value |
| `__REPLACE_ME__` | literal match — always flag |

Fingerprints are safe to log, safe to include in audit reports, safe to share across environments. Real values are not.

## Provision — the scripted path

Manual environment provisioning is an error source (typos in env var names, forgotten keys, inconsistent values). Script it:

```bash
#!/usr/bin/env bash
# scripts/provision-staging.sh
# Provision staging secrets from .env.example as the source of truth.

set -euo pipefail

ENV_NAME="staging"
EXAMPLE_FILE=".env.example"

if [ ! -f "$EXAMPLE_FILE" ]; then
    echo "missing $EXAMPLE_FILE" >&2
    exit 1
fi

# Derive keys from the example file, skip placeholders and commented lines
while IFS= read -r key; do
    # Prompt securely for each value
    read -srp "Value for $key (staging): " value
    echo
    gh secret set "$key" --env "$ENV_NAME" --body "$value"
done < <(grep -E '^[A-Z_][A-Z0-9_]*=' "$EXAMPLE_FILE" | cut -d= -f1 | sort -u)

echo "staging provisioned ($(grep -cE '^[A-Z_][A-Z0-9_]*=' "$EXAMPLE_FILE") keys)"
```

The script is idempotent — re-running it overwrites the same keys with the same values. Keep the script in `scripts/` so it's reviewable.

## Common mistakes

- **Rotating before auditing consumers.** You'll break a consumer you didn't know about.
- **Updating `.env.example` without updating `.env`.** The next developer to clone hits a missing variable.
- **Deleting a secret from CI without deleting it from code.** The code still tries to read it and fails at startup.
- **Using the same secret across environments.** A staging leak becomes a production leak.
- **Keeping old rotated secrets "just in case".** They're a compliance liability and an exfiltration target.
- **Provisioning by web UI.** Not reproducible, not auditable, slow.

## Observability

For any lifecycle operation in production, log three things:

1. **What changed** (key name, not value).
2. **When** (timestamp).
3. **Who** (actor, ideally a named human or a service account with a traceable identity).

Put this in `ROTATION_LOG.md` for rotations and an equivalent for other operations. A lifecycle log is the difference between "we know what happened" and "we think nothing changed".
