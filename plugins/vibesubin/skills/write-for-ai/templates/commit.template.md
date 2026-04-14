<type>(<scope>): <subject — imperative mood, lowercase, no trailing period>

<One paragraph explaining *why* this change needed to happen. What problem
does it solve or what capability does it add? A reviewer reading `git blame`
in six months should understand the motivation without opening an issue tracker.>

<Optional second paragraph covering the *what* and the *how*. Which files
were touched and which functions were changed. Any non-obvious decisions
belong here. Skip this paragraph for trivial changes.>

## Verification
- <command run, result> e.g. `pytest -q` → 142 passed
- <command run, result> e.g. `ruff check .` → clean
- <command run, result> e.g. `tsc --noEmit` → clean

## Risks
- <One risk the reviewer should watch for. Omit the section if there is no risk.>

---
Notes:
- <type> is one of: feat, fix, refactor, chore, docs, test, ci, perf, style, build
- <scope> is the module or feature affected, in kebab-case, e.g. `auth`, `billing-api`
- <subject> must be ≤ 72 characters, imperative (`add`, `fix`, `move` — not `added`, `fixes`)
- Delete this Notes block before committing.
