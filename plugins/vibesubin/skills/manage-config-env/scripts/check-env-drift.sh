#!/usr/bin/env bash
# scripts/check-env-drift.sh
# Fail CI if .env and .env.example have different key sets.
# Wire this into a pre-commit hook or the test workflow so a missing variable
# in the example gets caught before a collaborator clones and hits it.
set -euo pipefail

if [ ! -f .env.example ]; then
    echo ".env.example missing" >&2
    exit 1
fi

if [ ! -f .env ]; then
    # In CI where .env doesn't exist, only the example is checked.
    exit 0
fi

keys() { grep -E '^[A-Z_][A-Z0-9_]*=' "$1" | cut -d= -f1 | sort -u; }

only_in_example=$(comm -23 <(keys .env.example) <(keys .env))
only_in_real=$(comm -13 <(keys .env.example) <(keys .env))

if [ -n "$only_in_real" ]; then
    echo "Keys in .env but not in .env.example:" >&2
    echo "$only_in_real" | sed 's/^/  - /' >&2
    echo "Add them to .env.example (with __REPLACE_ME__ as the value)." >&2
    exit 1
fi

if [ -n "$only_in_example" ]; then
    echo "Note — keys in .env.example that your local .env doesn't set:" >&2
    echo "$only_in_example" | sed 's/^/  - /' >&2
    echo "Either add them to .env or remove them from .env.example." >&2
fi

echo "env drift check passed"
