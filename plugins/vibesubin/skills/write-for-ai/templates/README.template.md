# <PROJECT_NAME>

<One-sentence description. Noun phrase. Tells a cold reader what this is.>

> Status: <early | stable | deprecated>. Last updated: <YYYY-MM-DD>.

---

## What this is

<One paragraph. Why it exists, who uses it, what problem it solves.
Three sentences max. If you need more, you're writing for the wrong audience.>

---

## Quick start

```bash
git clone <REPO_URL>
cd <PROJECT_DIR>

# Install dependencies
<install command>

# Copy the env template
cp .env.example .env
# Edit .env and replace every __REPLACE_ME__ with a real value

# Run
<run command>
```

You should see <what the operator should see if it worked>.

---

## Repo map

```
<PROJECT_DIR>/
├── <dir or file>          # <one-line purpose>
├── <dir or file>          # <one-line purpose>
└── ...
```

---

## Environment variables

| Name | Required? | Example | What it's for |
|---|---|---|---|
| `DATABASE_URL` | yes | `__REPLACE_ME__` | Primary database connection string |
| `SESSION_SECRET` | yes | `__REPLACE_ME__` | Signs auth tokens and session cookies |
| `LOG_LEVEL` | no | `info` | Logging verbosity: `debug`, `info`, `warning`, `error` |
| `PORT` | no | `8080` | HTTP port the server binds to |

See [`.env.example`](./.env.example) for the full list.

---

## Common tasks

| Task | Command |
|---|---|
| Run tests | `<test command>` |
| Run linter | `<lint command>` |
| Run type check | `<typecheck command>` |
| Start dev server | `<dev command>` |
| Build for production | `<build command>` |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `<error message>` | <cause> | `<fix command>` |
| `<error message>` | <cause> | `<fix command>` |

---

## More docs

- [`CLAUDE.md`](./CLAUDE.md) / [`AGENTS.md`](./AGENTS.md) — AI-facing invariants and conventions
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute (if applicable)
- [`docs/`](./docs/) — deeper documentation (if applicable)

---

## License

<LICENSE_NAME> — see [LICENSE](./LICENSE).
