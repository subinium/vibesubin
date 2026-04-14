# Directory layout and naming — the full table

`SKILL.md` states the three quiet rules:

1. **Domain-first, type-second** — group by feature, not by file type.
2. **No flat directory above ~15 files** — sub-group at the threshold.
3. **Names are predictions** — a directory name should predict what's inside.

This reference covers the full naming table and the list of structural smells.

## Naming table — what to call each directory

| What it contains | Name it |
|---|---|
| Feature / domain code | Singular noun (`auth`, `billing`, `cart`), lowercase, hyphens if multi-word |
| Stateless helpers | `utils/`, `helpers/`, or `lib/` — pick one per repo and stick to it |
| Top-level config | `config/` (not both `settings/` and `config/`) |
| Data model definitions | `models/` or `schemas/` — pick one |
| API route handlers | `handlers/`, `routes/`, or `controllers/` — pick one |
| Tests for feature X | `tests/<same-name-as-feature>/` |
| Scripts you run by hand | `scripts/` with clear categories underneath |
| Generated output | `dist/`, `build/`, `target/` — never commit |
| Cached or temporary | `tmp/`, `.cache/` — always gitignore |
| Static assets | `assets/` or `public/` — pick one |

## Naming inside a file

- **Functions / methods** are verbs (`fetch_user`, `calculate_total`, `handle_login`).
- **Classes / types** are nouns (`User`, `OrderTotal`, `LoginHandler`).
- **Booleans** start with `is_`, `has_`, `can_`, `should_`.
- **Constants** are `UPPER_SNAKE_CASE`.
- **Private members** have a leading underscore in languages without a private keyword (`_helper`, `_cache`).

Apply these quietly. When the operator asks to add a new file, pick a name that follows the rule and note the reason in one sentence (*"I'm naming this `auth/session_store.py` — singular domain, snake_case, type name in the module path"*). No lecture.

## Domain-first example

```
# Good
src/
├── auth/
│   ├── handlers.py
│   ├── service.py
│   └── queries.py
├── billing/
│   ├── handlers.py
│   ├── service.py
│   └── queries.py

# Bad
src/
├── handlers/
│   ├── auth.py
│   └── billing.py
├── services/
│   ├── auth.py
│   └── billing.py
├── queries/
│   ├── auth.py
│   └── billing.py
```

The "bad" version becomes unbearable around 20 domains. Split by domain early.

## Structural smells — detection list

Smells that should trigger a `fight-repo-rot` hand-off:

- A directory with more than 30 flat files.
- A file named `utils.py` / `helpers.py` / `misc.py` over 500 lines — always a god-module.
- Two directories doing the same thing (`config/` and `settings/`, `utils/` and `helpers/`).
- A `common/` or `shared/` directory that everything imports from — coupling magnet.
- Deep nesting greater than 5 levels — indicates over-organization.
- Files named after people (`alice_helper.py`) or dates (`old_version_2024.py`) — local context leaking into shared code.
