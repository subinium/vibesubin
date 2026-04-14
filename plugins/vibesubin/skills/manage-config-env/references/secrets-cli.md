# Secrets management per platform — CLI cheatsheet

Short cheat sheets for the common hosting providers. Before running any of these, load the secret into a shell variable first (see `SKILL.md` → *"Secrets management — CLI over dashboards"*), then reference `"$VAR"` in the commands below. Never paste a literal secret value into a command.

## GitHub Secrets (for GitHub Actions)

```bash
# One-time: gh auth login
gh secret set DEPLOY_SSH_KEY < ~/.ssh/id_ed25519      # from a file
gh secret set DEPLOY_HOST --body "192.0.2.10"         # literal value
gh secret set DATABASE_URL                            # prompts for value
gh secret list                                        # show what's set
gh secret delete OLD_TOKEN                            # remove
```

Environment-scoped secrets (attached to a specific deploy environment):

```bash
gh secret set PROD_DB_URL --env production
gh secret list --env production
```

## Vercel

```bash
vercel env add DATABASE_URL production                # prompts for value
vercel env ls                                          # list
vercel env rm OLD_KEY production
vercel env pull .env.local                             # sync to local
```

## Netlify

```bash
netlify env:set DATABASE_URL "$DATABASE_URL"
netlify env:list
netlify env:unset OLD_KEY
netlify env:import .env                                # bulk import from file
```

## Fly.io

```bash
fly secrets set DATABASE_URL="$DATABASE_URL" SESSION_SECRET="$SESSION_SECRET"
fly secrets list
fly secrets unset OLD_KEY
# All secrets are exposed as env vars inside the deployed machine.
```

## Railway

```bash
railway variables set DATABASE_URL="$DATABASE_URL"
railway variables
railway variables delete OLD_KEY
```

## Cloud Run (GCP)

```bash
gcloud run services update <service-name> \
  --update-env-vars DATABASE_URL="$DATABASE_URL" \
  --region <region>

# For real secrets, store in Secret Manager and mount them:
printf '%s' "$DATABASE_URL" | gcloud secrets create database-url --data-file=-
gcloud run services update <service-name> \
  --update-secrets DATABASE_URL=database-url:latest \
  --region <region>
```

## AWS (Parameter Store / Secrets Manager)

```bash
# SSM Parameter Store — for config-like values
aws ssm put-parameter --name /myapp/database_url --type SecureString --value "$DATABASE_URL" --overwrite
aws ssm get-parameter --name /myapp/database_url --query 'Parameter.Name' --output text

# Secrets Manager — for high-value secrets with rotation
aws secretsmanager create-secret --name myapp/database --secret-string "{\"url\":\"$DATABASE_URL\"}"
aws secretsmanager describe-secret --secret-id myapp/database
```
