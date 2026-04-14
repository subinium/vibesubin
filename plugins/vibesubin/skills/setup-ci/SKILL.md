---
name: setup-ci
description: Teaches CI/CD from first principles to a non-developer, then scaffolds a working test + deploy pipeline. Handles the common hosts (GitHub Actions, GitLab CI, CircleCI, Travis, Jenkins) and common deploy targets (SSH to VM, Vercel, Netlify, Fly.io, Cloud Run, Docker registries). Asks what the operator has before generating anything — never assumes.
when_to_use: Trigger on "set up CI", "auto deploy", "GitHub Actions", "I want to push and have it deploy", "what is CI", "how does deployment work", or when the operator wants any automated testing or deployment on a new or existing project.
allowed-tools: Read Write Edit Glob Bash(ls .github/*) Bash(gh *) Bash(vercel *) Bash(fly *) Bash(netlify *) Bash(railway *) Bash(gcloud *) Bash(aws *) Bash(act *)
---

# setup-ci

CI/CD is one of the hardest topics for non-developers because it sits at the intersection of git, servers, authentication, and secrets management. Most tutorials jump straight to YAML. This skill starts earlier.

**Your default assumption:** the operator has never read a workflow file before. Don't patronize them, but don't skip concepts either.

## Step 1 — Figure out what the operator actually wants

Before generating any YAML, ask the operator **two questions, one at a time**. Don't ask all at once.

**Question 1:** *"What happens when you push code today? Do you deploy manually, or is something already automated?"*

Their answer tells you:

- "I SSH in and run `git pull`" → They have a server and a manual deploy. You're replacing the manual step.
- "I use Vercel / Netlify / Fly.io" → They have a managed platform. CI is about **tests before deploy**, the deploy is already automatic.
- "Nothing, it's only on my laptop" → They need a host choice first. Suggest the simplest option for their stack (Vercel for web frontends, Fly.io for full apps, a VM for anything complicated).
- "What's a deploy?" → Start from the very beginning. Go to the concepts section below.

**Question 2:** *"Which git host are you on? GitHub, GitLab, Bitbucket, self-hosted?"*

Their answer tells you which CI system you're writing for:

- GitHub → GitHub Actions
- GitLab → GitLab CI (`.gitlab-ci.yml`)
- Bitbucket → Bitbucket Pipelines (`bitbucket-pipelines.yml`)
- Self-hosted / "I don't know" → Default to GitHub Actions since the operator almost certainly knows GitHub

**Do not generate YAML until both questions are answered.** The #1 failure mode here is producing a GitHub Actions workflow for someone who's actually on GitLab.

If the operator says "just pick whatever's easiest," pick: **GitHub + GitHub Actions + their current deploy target**. Tell them explicitly that you picked that and why.

## CI pipeline components — required, recommended, optional

CI/CD is modular. Not every project needs every component. Use this tree to decide what to scaffold for a given repo.

```
CI Pipeline
│
├── REQUIRED (always scaffold)
│   ├── Checkout                 # git clone into the runner
│   ├── Runtime install          # the language (Python/Node/Rust/Go/...)
│   ├── Dependency install       # pip/npm/cargo/go mod
│   ├── Test execution           # whatever test command the project has
│   └── Status reporting         # pass/fail to the PR or commit
│
├── RECOMMENDED (scaffold unless operator declines)
│   ├── Lint                     # ruff/eslint/clippy/golangci-lint
│   ├── Typecheck                # mypy/tsc --noEmit/cargo check/go vet
│   ├── Dependency caching       # skip re-downloading node_modules every run
│   ├── Concurrency group        # cancel old runs when a new commit lands
│   └── Branch / PR filter       # only run on main + PRs, not every branch
│
├── OPTIONAL — auto deploy (only if operator asked)
│   ├── Deploy trigger           # workflow_run on success, or direct push
│   ├── Deploy step              # SSH / Vercel / Fly / Cloud Run / Docker push
│   ├── Post-deploy health check # curl -f /health, fail loudly
│   ├── Rollback path            # revert to previous SHA on health fail
│   └── Notification             # Slack/Telegram/email on success or fail
│
├── NICE TO HAVE (suggest, don't auto-add)
│   ├── Coverage report          # pytest-cov, c8, tarpaulin
│   ├── Security scan            # pip-audit, npm audit, cargo audit (see audit-security)
│   ├── Container build + push   # if the deploy is container-based
│   ├── Integration tests        # separate from unit, usually against a real DB
│   ├── Matrix builds            # multiple OSes or language versions
│   ├── Scheduled runs           # nightly cron for dependency updates or flake detection
│   └── Release automation       # semantic-release, changesets, goreleaser
│
└── EXPENSIVE — offer only if operator asks
    ├── E2E browser tests        # Playwright, Cypress (slow, flaky)
    ├── Visual regression        # screenshot diffing
    ├── Load / stress tests      # k6, Locust
    ├── Mutation testing         # Stryker, PIT
    └── Fuzzing                  # per-language fuzzer
```

**How to use this tree with the operator:**

1. Start by scaffolding **REQUIRED + RECOMMENDED**. That's the default.
2. Ask: *"Do you also want automatic deployment, or just tests for now?"* If yes → add OPTIONAL. If no → stop here.
3. Mention **NICE TO HAVE** as a one-sentence menu: *"You can also add coverage, a security scan, or scheduled runs later. Want any of those now?"*
4. Never silently scaffold EXPENSIVE items. They slow every run down and flake on new projects.

Every added component costs something (runner minutes, maintenance, false-positive noise). Bias toward the minimal working pipeline. It's easier to add later than to remove.

## Step 2 — Concepts, if the operator wants them

If the operator said "what's a deploy?" or "what is CI?", pause and explain. Short, concrete, concrete, concrete. One analogy per concept.

**CI (Continuous Integration)** — "Every time you push code, a computer somewhere else runs your tests and tells you if anything broke. If the tests break, you find out in a minute instead of when a user hits the bug."

**CD (Continuous Delivery / Deployment)** — "If the tests pass, that same computer also deploys your code to production automatically. No more SSH."

**Runner** — "The computer that does the work. It's not your laptop and it's not your production server. Think of it as a rented robot that runs for 30 seconds and then disappears."

**Workflow** — "The recipe you give the runner. It's a YAML file that says: install these dependencies, run these tests, if they pass, deploy to this place."

**Trigger** — "The event that wakes the runner up. Usually 'someone pushed code to the main branch.' Can also be 'someone opened a pull request' or 'every Monday at 9am.'"

**Secrets** — "Passwords and API keys that the runner needs but that cannot be visible in the YAML (because YAML is in git and git is public). They live in a separate encrypted store on the CI platform and are injected into the runner at runtime."

**Artifact** — "The thing you built. A zip, a container image, a directory of static HTML. CI produces it; CD ships it."

**Environment** — "Where the artifact ends up. 'staging' is the pre-production test site; 'production' is what real users see."

After this one-page explanation, ask: *"Does that make sense? Should I keep going, or do you want to pause and ask anything?"*

## Step 3 — Pick the right CI host

The host you generate for depends on:

1. **Their git host** (from Step 1, question 2)
2. **Where they want to deploy** (SSH VM? Managed platform?)
3. **Whether they already have something working** (don't replace it unless asked)

### Host-to-file mapping

| Git host | CI file |
|---|---|
| GitHub | `.github/workflows/*.yml` |
| GitLab | `.gitlab-ci.yml` at repo root |
| Bitbucket | `bitbucket-pipelines.yml` at repo root |
| Gitea / Forgejo | `.gitea/workflows/*.yml` (uses GitHub Actions syntax) |
| CircleCI (add-on) | `.circleci/config.yml` |
| Travis (add-on) | `.travis.yml` |

Skill scaffolds for GitHub Actions by default. For others, state clearly: *"I'll write this as GitHub Actions first, then point out the pieces that change for <your host>."* The core logic is portable even if the YAML syntax differs.

## Step 4 — Scaffold the files

Generate **two workflows** at minimum:

### `test.yml` — runs on every push and PR

Contents:

1. Checkout the repo
2. Install language runtime (Python, Node, Rust, etc. — auto-detect from repo files)
3. Install dependencies
4. Run lint
5. Run typecheck
6. Run tests

Commented inline for the non-developer reader. Every step has a comment explaining what it does.

### `deploy.yml` — runs on success of `test.yml`

Triggered by `workflow_run` (GitHub Actions) or equivalent. Only fires if `test.yml` passed.

Contents depend on the deploy target (see Step 5). The invariant: **deploy the exact revision that passed** in `test.yml`, not whatever `main` happens to point to when the deploy job starts.

Built-in safety (every workflow this skill scaffolds enforces all of these):

- **Top-level `permissions: contents: read`** — start from zero and only grant what the job actually needs. Default-broad token permissions are the #1 GitHub Actions supply-chain risk. Elevate per-job (e.g., `id-token: write` for OIDC) only where required.
- **Third-party actions pinned to a full commit SHA**, never a tag. A tag can be moved; a SHA cannot. Every `uses:` line looks like `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683   # v4.2.2`.
- **Carry the tested SHA through to deploy.** For `workflow_run`, use the successful run's `head_sha` and deploy that exact commit. Never `git pull origin main` blindly on the server — that is how commit A's passing tests deploy commit B by accident.
- **OIDC over long-lived secrets** for cloud deploys. Target platforms that support it (AWS, GCP, Azure, Vault, Cloudflare) should use federated tokens instead of storing static keys in GitHub Secrets. SSH to a VM is the one legitimate case for a static `DEPLOY_SSH_KEY` — there is no OIDC equivalent for arbitrary SSH.
- **Protected `production` environment** with required reviewers for any job that deploys to production. `environment: name: production` in the job turns on the approval gate. Pair with branch protection.
- **`CODEOWNERS` covers `.github/workflows/`** so a random contributor can't silently change a workflow. Add `/.github/workflows/ @maintainer` at minimum.
- **Self-hosted runners are opt-in and isolated.** Never run self-hosted runners on a forked PR without explicit allowlisting. Prefer GitHub-hosted runners for anything that touches secrets. If self-hosted is unavoidable, use ephemeral runners and isolate by repository.
- **Log redaction** — GitHub masks registered secrets automatically, but `echo $SECRET` still risks leaking through errors, stack traces, or timing. Never echo a secret. If a command's output might contain one, pipe through a redaction filter.
- **`concurrency` group** so two deploys don't race each other.
- **Job-level `timeout-minutes`** so a hung deploy eventually fails.
- **Secrets cleanup** — any temp SSH key or credential file is deleted in an `always()` step.
- **Post-deploy health check** — `curl -f <url>/health` or equivalent. If the health check fails, the deploy job fails loudly.

Working templates in this skill's `templates/` directory:

- `templates/github-actions-test.yml` — language-aware test workflow, permissions-hardened, SHA-pinned
- `templates/github-actions-deploy-ssh.yml` — deploy to a VM over SSH, with post-deploy health check and cleanup

Templates for Vercel, Fly.io, Cloud Run, and Docker registries follow the same pattern — the skill can emit them on demand, but the canonical reference implementations are the two above.

## Repo-aware generation rule

Do not emit generic YAML just because it is the easiest thing to write. Before scaffolding, inspect the repo and tailor the workflow to the actual stack:

- `pnpm-lock.yaml` → use `pnpm`, not `npm`
- `yarn.lock` → use `yarn`
- `bun.lockb` → use `bun`
- `uv.lock` → use `uv run`
- `poetry.lock` → use `poetry run`
- `Cargo.toml` → `cargo check` / `cargo test`
- `go.mod` → `go test ./...`
- `Gemfile` → `bundle exec ...`
- `composer.json` → `composer` / `phpunit`
- `mix.exs` → `mix test`

Framework markers matter too:

- Next.js / Vercel / Netlify style app → usually generate **test-only CI** and let the platform handle deploys
- Django / Rails / Laravel → include migration step explicitly if the app already does it manually
- Multi-service monorepo → ask which service(s) the workflow should cover, or generate one workflow per service path

The operator should feel like the workflow was written for **their** repo, not copied from a blog post.

## Step 5 — Deploy target specifics

### SSH to a VM

Needs:

- SSH private key as a GitHub Secret (`DEPLOY_SSH_KEY`)
- VM host as a Secret or repository variable (`DEPLOY_HOST`)
- VM user as a Secret or variable (`DEPLOY_USER`)
- The target already has the repo cloned and a runtime installed
- The `sudo` commands the deploy needs have NOPASSWD rules set up (`sudoers.d`)

**Common failure:** sudo prompts for a password and the CI job hangs. Always verify NOPASSWD is set up or use a user that doesn't need sudo.

**Reproduce locally first.** If the operator has never done a remote deploy, tell them: *"Before we automate this, we should do it manually from your laptop once to make sure it works. Can you SSH in and run the deploy commands by hand?"* Automating a broken manual process leads to hours of debugging.

### Managed platform (Vercel / Netlify / Railway / Render)

Most managed platforms already auto-deploy on push. CI's job here is only **testing before deploy**, not deploying itself. The skill should:

1. Confirm the platform is already connected to the repo
2. Generate a `test.yml` that runs on push and PR
3. **Not** generate a `deploy.yml` unless the operator wants a staging/production gate
4. Explain that "deploy" happens automatically because the platform is listening for pushes

### Fly.io / Cloud Run / Kubernetes

These typically use an image push + a deploy command:

1. Build the container (`docker build` or `flyctl deploy`)
2. Push the image or deploy directly
3. The platform rolls out the new version

Needs the platform's API token as a Secret (`FLY_API_TOKEN`, `GCP_CREDENTIALS`, etc.).

### "I don't have a target yet"

If the operator doesn't have somewhere to deploy, **don't try to set up a full pipeline in one go**. Suggest the simplest-possible target for their project:

- Static site / frontend → Vercel or Netlify
- Full-stack web app, want managed → Fly.io or Railway
- Full-stack web app, want control → Hetzner / DO / Oracle Cloud VM + SSH
- Container workload → Fly.io or Cloud Run
- Discord bot / Telegram bot / any long-running process → Fly.io with `fly.toml`, or a VM

After they pick, come back and run Step 4 / Step 5.

## Step 6 — Secrets checklist

Every workflow that uses secrets needs a checklist handed to the operator. The skill produces this as a comment block in the generated YAML and also as a separate message:

```markdown
## Secrets this workflow needs

Set these in your GitHub repo: Settings → Secrets and variables → Actions → New repository secret

- [ ] `DEPLOY_SSH_KEY` — contents of your SSH private key (e.g., `cat ~/.ssh/my_key`)
- [ ] `DEPLOY_HOST` — IP or hostname of your server (e.g., `192.0.2.1`)
- [ ] `DEPLOY_USER` — username on the server (e.g., `ubuntu`)

After you set all three, re-run the workflow. First run will usually fail on the SSH step if any secret is wrong — the log will tell you which one.
```

Never print the secret values themselves, and never store them in YAML.

## Step 7 — First run = manual dispatch

Always recommend that the first run of a deploy workflow be **manual**, via `workflow_dispatch`. Reasons:

1. The operator can watch the log in real time and catch errors at their source
2. Secrets missing / wrong will fail fast instead of on every push
3. If the VM prereq is off, they find out now instead of tomorrow

Tell the operator: *"After I generate the files, go to Actions → Deploy → Run workflow. Watch the output. If it passes, you're set up. If it fails, paste me the error and I'll fix it."*

Manual dispatch is for **a reviewed re-deploy** or first-run proof. Make the generated comments explicit about this. In normal operation, `workflow_run` should be the path that moves tested code to production.

## Things not to do

- **Don't write YAML blind.** Always ask the two Step 1 questions first
- **Don't invent secret names.** If you reference `DEPLOY_HOST` in the YAML, the same name has to be in the checklist
- **Don't use third-party actions unnecessarily.** `actions/checkout` and `actions/setup-*` are fine; random actions from marketplace are a supply-chain risk. If you reference one, pin to a commit SHA
- **Don't copy an outdated template.** CI/CD conventions move fast. Check that the syntax matches the current docs before emitting
- **Don't auto-deploy to production from the first run.** Require `workflow_dispatch` manually for the first run, then switch to `workflow_run` for subsequent automated runs
- **Don't leave framework mismatch in place.** A Python workflow in a pnpm repo is not a starting point, it's a bug. Detect the repo and emit the right commands the first time.

## Common failure modes

Things to watch for in your own output:

- **Deploy fix loops** — iterating on the YAML remotely when the problem is actually that the manual deploy doesn't work yet. Always have the operator prove the manual path works before automating
- **Platform env var confusion** — Vercel, Netlify, and similar have their own secrets UI, separate from git host secrets. If the deploy uses env vars on the platform, tell the operator to set them there, not in GitHub Secrets
- **Assumption that `git pull` is enough** — if the project has migrations, native dependencies, cache warming, or a restart step, `git pull` alone will silently produce a broken deployment. Enumerate every step
- **Secrets in logs** — `echo $DEPLOY_KEY` in a step leaks the key to the public log. Never echo secrets
- **Long-running runners forgotten** — if the workflow starts a server and doesn't stop it, the runner eventually times out. Scope runners to single commands

## Hand-offs

- Deploy touches config files → `manage-config-env` for the `.env` pattern
- Deploy leaks secrets → `audit-security` immediately
- Deploy breaks and touches production code → `refactor-verify` for the fix

## Details

Canonical working templates live in `templates/`:

- `templates/github-actions-test.yml` — test workflow with permissions hardening and SHA-pinned actions
- `templates/github-actions-deploy-ssh.yml` — deploy to a VM over SSH with post-deploy health check and secret cleanup

The CI/CD concept explainer (runners, triggers, environments, OIDC, secrets, concurrency) is embedded in the "Step 2 — Concepts" section of this SKILL.md rather than split into a reference file. Per-platform deploy gotchas live in the "Step 5 — Deploy target specifics" section.
