# <PROJECT_NAME> — AI operator guide

Read this file first in every new session. It encodes the invariants that matter for this project.

> This file works as `CLAUDE.md` for Claude Code, and as `AGENTS.md` for agent frameworks that use that convention. The content is identical; only the filename changes. Copy to the other name if both are needed.

---

## 🛑 Never do

1. **Never commit `.env` or any secret file.** If you see one in `git status`, stop and alert the operator.
2. **Never force-push `main` or the default branch** unless the operator has explicitly authorized it in this session.
3. **Never run destructive commands** (`rm -rf`, `DROP TABLE`, `git reset --hard`, `git clean -fdx`) without asking first.
4. **Never skip verification.** Any task that says "done" must have produced a passing test, a clean typecheck, or an execution result.
5. **Never add a hardcoded absolute path** (`/Users/...`, `C:\Users\...`, `/home/...`) or a literal IP address to committed code.

---

## ✅ Always do

| Ritual | Verification command |
|---|---|
| Typecheck after any change | `<typecheck command>` |
| Run tests after any change | `<test command>` |
| Lint after any change | `<lint command>` |
| Smoke test the app still starts | `<smoke command>` |

---

## 📋 Change type → file matrix

| What you want to change | Files to touch (in order) | Verification |
|---|---|---|
| Add an API route | `<routes dir>` → `<handler dir>` → tests | `<command>` |
| Add a database table | `<migrations dir>` → `<models dir>` → tests | `<command>` |
| Add an env var | `.env.example` → `<config file>` → README §env | `<smoke test>` |
| Add a page (frontend) | `<pages dir>` → `<components dir>` → tests | `<command>` |
| Add a new dependency | `<manifest file>` → lockfile → smoke test | `<install command>` |

---

## 🔒 Invariants

| Invariant | What breaks if you violate it |
|---|---|
| Secrets live only in `.env` (local) and <CI secret store> (remote) | Credentials in git, rotation pain |
| All datetimes are <UTC or specific timezone> | Scheduled jobs drift, users see wrong times |
| Database queries use parameter binding, never string interpolation | SQL injection |
| Every route that takes user input validates it at entry | Path traversal, XSS, type errors |
| Tests must pass before push | CI red, rollback pain |

Add project-specific invariants here.

---

## 🗺️ Repo map

```
<PROJECT_DIR>/
├── <dir>                  # <one-line purpose>
├── <dir>                  # <one-line purpose>
└── ...
```

---

## 🚀 Deployment

<One paragraph describing how the project deploys. Which branch triggers a deploy?
Which environment? Is it automatic or manual? Where are the logs?>

Link to a deeper runbook if one exists.

---

## 🎭 Recently decided — do not re-litigate

Decisions already made in this project. Future sessions should not re-propose these as open questions.

- **<Decision>.** Reason: <one sentence>. Date: <YYYY-MM-DD>.
- **<Decision>.** Reason: <one sentence>. Date: <YYYY-MM-DD>.

Add new entries here whenever a non-obvious architectural choice is made.

---

## More docs

- [`README.md`](./README.md) — project overview and quick start
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute (if applicable)
- [`docs/`](./docs/) — deeper documentation
