# Secret rotation — provider-specific recipes

Rotation is the lifecycle operation most non-developers skip because it feels scary. This reference is the playbook: for each provider, the steps for scheduled rotation and for incident rotation. All examples assume the CLI is authenticated.

## Before you start

- **Always log rotations.** Append to `ROTATION_LOG.md` at the repo root: date, key name, trigger (scheduled / departure / leak / scheduled audit), actor, downtime window if any.
- **Never rotate during a deploy.** Let the currently-rolling deploy finish first. Rotating mid-deploy means half your fleet has the old key and half has the new.
- **Pre-rotation check:** confirm where the secret is used. Run the audit from the *Audit drift across environments* workflow in `SKILL.md` so you don't miss a store.
- **Prefer OIDC where supported.** AWS, GCP, Azure, and Vault support federated identity from GitHub Actions. A credential that doesn't exist cannot be rotated.

## Dual-valid vs single-valid providers

| Provider / key type | Supports dual-valid? | Rotation mode |
|---|---|---|
| AWS IAM access keys | Yes (up to 2 active keys per user) | Zero-downtime |
| GCP service account keys | Yes (multiple keys per SA) | Zero-downtime |
| Stripe secret keys (live + restricted) | Yes | Zero-downtime |
| OpenAI API keys | Yes (multiple keys per org) | Zero-downtime |
| Anthropic API keys | Yes | Zero-downtime |
| OAuth client secrets (most providers) | Yes (secondary secret supported) | Zero-downtime |
| GitHub personal access tokens | No (one per scope per user) | Cut-over |
| Database user passwords (Postgres / MySQL) | No (single password per user) | Downtime OR create new user |
| JWT signing keys (HS256) | Depends on app (needs `kid` header) | Downtime unless `kid` rotation is in place |
| Session cookies / CSRF tokens | No | Forces user re-login |

For single-valid cases, the usual workaround is *create a new user / new key and migrate traffic to it*, then retire the old one. That's a dual-valid pattern at the application layer.

## AWS IAM access keys

Scheduled rotation:

```bash
# 1. Create the second key
aws iam create-access-key --user-name deploy-bot
# Capture AccessKeyId + SecretAccessKey in a secure scratch space

# 2. Update every consumer (CI, servers, local .env) to the new pair
gh secret set AWS_ACCESS_KEY_ID --body "<new>"
gh secret set AWS_SECRET_ACCESS_KEY --body "<new>"
# repeat for Vercel / Fly / etc.

# 3. Roll the app and confirm the new key works

# 4. Deactivate the old key (soft-delete window)
aws iam update-access-key --user-name deploy-bot \
    --access-key-id AKIA... --status Inactive

# 5. After 24 hours of no failures, delete it
aws iam delete-access-key --user-name deploy-bot --access-key-id AKIA...
```

Incident rotation: skip step 4's soft-delete window and go straight to delete.

## GCP service account keys

```bash
# 1. Create new key
gcloud iam service-accounts keys create ./new-key.json \
    --iam-account=deploy-bot@project.iam.gserviceaccount.com

# 2. Distribute and roll the app

# 3. List existing keys and delete the old one
gcloud iam service-accounts keys list \
    --iam-account=deploy-bot@project.iam.gserviceaccount.com

gcloud iam service-accounts keys delete <KEY_ID> \
    --iam-account=deploy-bot@project.iam.gserviceaccount.com
```

Prefer Workload Identity Federation over long-lived SA keys. Setup reference: [Google's WIF docs](https://cloud.google.com/iam/docs/workload-identity-federation).

## Stripe secret keys

```bash
# 1. Create a new restricted key in the Stripe dashboard
#    (Stripe CLI doesn't expose key creation, use the dashboard once)

# 2. Update the webhook endpoint's signing secret if rotating that too
stripe listen --print-secret   # if using the CLI's webhook forwarding

# 3. Distribute the new STRIPE_SECRET_KEY
gh secret set STRIPE_SECRET_KEY --body "sk_live_..."

# 4. Roll the app, confirm a test charge or webhook delivery

# 5. Revoke the old key from the dashboard
```

Stripe supports multiple live keys, so there's no forced downtime. Always use restricted keys scoped to the minimum required resources.

## OpenAI / Anthropic API keys

```bash
# 1. Create a new key via the web dashboard
# 2. gh secret set OPENAI_API_KEY --body "sk-..."
# 3. Roll the app
# 4. Delete the old key from the dashboard
```

Anthropic workspaces and OpenAI projects both support multiple keys per workspace / project, so cut-over has no downtime.

## Database user passwords (Postgres)

Single-valid, so choose one of two strategies.

**Strategy A — downtime rotation (simple, short window):**

```sql
-- Maintenance mode on the app first
ALTER USER appuser WITH PASSWORD 'new-strong-password';
```

Then update every consumer of `DATABASE_URL` and restart.

**Strategy B — zero-downtime via a new user:**

```sql
-- 1. Create a new user with the same privileges
CREATE USER appuser_v2 WITH ENCRYPTED PASSWORD 'new-strong-password';
GRANT ALL PRIVILEGES ON DATABASE myapp TO appuser_v2;
-- Match grants exactly — the drift matters here

-- 2. Update every consumer to the new user
-- 3. Roll the app
-- 4. After confirming success:
DROP USER appuser;
```

Strategy B is safer for production but requires careful grant matching. Most managed Postgres (Supabase, RDS, Cloud SQL) provide a rotate-password flow that handles this for you — use it when available.

## JWT signing keys

The correct pattern for zero-downtime JWT rotation uses a `kid` (key ID) header and a key ring.

1. Add the new key to the ring under a new `kid`.
2. Start signing new tokens with the new `kid`.
3. Keep verifying tokens signed with the old `kid` until they naturally expire.
4. After the longest token lifetime has passed, remove the old key from the ring.

Without `kid` rotation support, rotating a JWT signing key invalidates every active session. Warn the operator explicitly — this is a forced-logout event.

## OAuth client secrets

Most OAuth providers (Google, GitHub, Azure AD) support a secondary secret during rotation.

1. Add a secondary secret at the provider.
2. Distribute the secondary secret to the app via `gh secret set` or equivalent.
3. Roll the app and confirm sign-ins work.
4. Promote the secondary to primary, remove the old primary.

If the provider doesn't support dual secrets, treat it like a database user rotation: brief downtime window.

## GitHub personal access tokens (PATs) and fine-grained tokens

PATs are single-valid and short-lived by design. Rotation is just issuing a new one, updating every consumer (including local git credential helpers), and revoking the old one from `https://github.com/settings/tokens`.

Prefer **GitHub App installations** over PATs for anything that runs unattended. GitHub Apps have finer-grained permissions, installation-scoped tokens, and clean rotation.

## Incident rotation — the urgent path

When a secret appears in logs, a laptop is lost, or a collaborator leaves under contention, the incident path skips the soft-delete windows:

1. **Immediately revoke** the compromised secret at the provider. Don't wait for the new one to be distributed — you're racing an attacker.
2. Put the app in maintenance mode if revocation will take it down.
3. Generate the new secret and distribute to every store.
4. Bring the app back up.
5. Hand off to `audit-security` for blast-radius assessment: what did the secret have access to, what logs should be checked, what data might have been exfiltrated.
6. Log the incident fully — not just in `ROTATION_LOG.md` but in an incident tracker if one exists.
7. After the incident, review: why did the secret leak, and what workflow change prevents the next one (usually: move to OIDC, tighten scope, move to a vault).

## When to hand off to other skills

- **Suspected leak or historical commit** → `audit-security` for git-history scanning before/after rotation.
- **Rotation requires code changes** (e.g., adding `kid` support for JWT rotation) → `refactor-verify` for the 1:1 behavior preservation.
- **Documenting the new rotation procedure** → `write-for-ai` to add a `ROTATION.md` or update `CLAUDE.md`.
