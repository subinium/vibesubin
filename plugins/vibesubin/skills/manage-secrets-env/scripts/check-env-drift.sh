#!/usr/bin/env bash
# scripts/check-env-drift.sh
# Fail if .env and .env.example have different key sets.
#
# Intended for a pre-commit hook (git hook or lefthook/husky entry), NOT CI —
# CI environments usually have no local .env, so the script would exit clean
# even when .env.example is out of date. Pre-commit catches drift at the
# moment a new variable is added.
#
# Correctly handles:
#   - comments (#-prefixed lines)
#   - blank lines
#   - spaces around the first `=`  (e.g. `KEY = value`)
#   - values that contain `=`      (e.g. `API_KEY=k=v`)
#   - quoted values                (e.g. `TOKEN="a b c"`)
#   - `export ` prefix              (e.g. `export KEY=value`)
#
# Does NOT handle:
#   - multi-line values spanning lines (PEM blocks etc). Put those in a file
#     reference instead (KEY_FILE=./secrets/foo.pem), which keeps drift-check
#     sound and doesn't leak the key into .env.example.

set -euo pipefail

if [ ! -f .env.example ]; then
    echo ".env.example missing" >&2
    exit 1
fi

if [ ! -f .env ]; then
    # Pre-commit may run in a fresh clone. Nothing to compare against.
    exit 0
fi

# Extract the key portion of KEY=VALUE / KEY = VALUE / export KEY=...
# 1. strip `export ` prefix if present
# 2. skip comments and blank lines
# 3. grab the identifier before the first `=`, trimming trailing spaces
# 4. require the identifier to match [A-Z_][A-Z0-9_]*
keys() {
    sed -E \
        -e 's/^[[:space:]]*export[[:space:]]+//' \
        -e '/^[[:space:]]*#/d' \
        -e '/^[[:space:]]*$/d' \
        "$1" \
    | awk -F= '{
        key = $1
        sub(/[[:space:]]+$/, "", key)
        if (key ~ /^[A-Z_][A-Z0-9_]*$/) print key
    }' \
    | sort -u
}

only_in_example=$(comm -23 <(keys .env.example) <(keys .env))
only_in_real=$(comm -13 <(keys .env.example) <(keys .env))

status=0

if [ -n "$only_in_real" ]; then
    echo "Keys in .env but not in .env.example:" >&2
    echo "$only_in_real" | sed 's/^/  - /' >&2
    echo "Add them to .env.example (with __REPLACE_ME__ as the value)." >&2
    status=1
fi

if [ -n "$only_in_example" ]; then
    echo "Note — keys in .env.example that your local .env doesn't set:" >&2
    echo "$only_in_example" | sed 's/^/  - /' >&2
    echo "Either add them to .env or remove them from .env.example." >&2
fi

if [ "$status" -eq 0 ]; then
    echo "env drift check passed"
fi

exit "$status"
