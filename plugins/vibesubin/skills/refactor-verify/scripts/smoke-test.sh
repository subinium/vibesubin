#!/usr/bin/env bash
#
# smoke-test.sh — auto-detect language and run the canonical "does it still
# work?" chain. Fail fast on the cheapest check first.
#
# Usage:
#   scripts/smoke-test.sh          # run in current directory
#   scripts/smoke-test.sh /path    # run in another directory
#
# Detection is by file presence at the target root:
#   pyproject.toml | setup.py         → Python
#   package.json                      → Node / TypeScript
#   Cargo.toml                        → Rust
#   go.mod                            → Go
#   Gemfile                           → Ruby
#   composer.json                     → PHP
#   mix.exs                           → Elixir
#
# If multiple are present (polyglot repo), every detected language's chain runs.
#
# Exit code:
#   0 — every step passed
#   1 — at least one step failed
#   2 — no supported language detected
#   3 — supported language detected, but the isolated workspace does not look bootstrapped enough to trust the result yet

set -euo pipefail

TARGET="${1:-.}"
cd "$TARGET"

[ -d .venv/bin ] && PATH="$(pwd)/.venv/bin:$PATH"
[ -d node_modules/.bin ] && PATH="$(pwd)/node_modules/.bin:$PATH"
[ -d vendor/bin ] && PATH="$(pwd)/vendor/bin:$PATH"

fail=0
ran_any=0
checks_run=0
bootstrap_hint=0

run_step() {
    local label="$1"
    shift
    echo "  → $label"
    checks_run=$((checks_run + 1))
    if "$@"; then
        echo "    ok"
    else
        echo "    FAIL"
        fail=1
    fi
}

maybe() {
    # Run a command only if the binary exists. No-op otherwise.
    if command -v "$1" >/dev/null 2>&1; then
        run_step "$1 $2" "$@"
    else
        echo "  ~ $1 not installed — skipping"
    fi
}

hint_bootstrap() {
    bootstrap_hint=1
    echo "  ! $1"
}

# --- Python ---
if [ -f pyproject.toml ] || [ -f setup.py ] || [ -f requirements.txt ]; then
    echo "== Python =="
    ran_any=1
    if [ ! -d .venv ] && ! command -v ruff >/dev/null 2>&1 && ! command -v mypy >/dev/null 2>&1 && ! command -v pytest >/dev/null 2>&1; then
        hint_bootstrap "No Python toolchain found here. If this is a fresh git worktree, recreate the virtualenv before trusting failures."
    fi
    maybe ruff check .
    maybe mypy .
    if [ -d tests ]; then
        maybe pytest -q --tb=short
    fi
fi

# --- Node / TypeScript ---
if [ -f package.json ]; then
    echo "== Node / TypeScript =="
    ran_any=1
    if [ ! -d node_modules ]; then
        hint_bootstrap "node_modules is missing in this checkout. If tests fail with module-not-found, install dependencies in this worktree first."
    fi
    if [ -f tsconfig.json ]; then
        maybe tsc --noEmit
    fi
    # Prefer the package manager in use
    if [ -f pnpm-lock.yaml ] && command -v pnpm >/dev/null 2>&1; then
        run_step "pnpm test --if-present" pnpm test --if-present
        run_step "pnpm lint --if-present" pnpm lint --if-present
    elif [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then
        run_step "yarn test" yarn test
        run_step "yarn lint" yarn lint
    elif [ -f bun.lockb ] && command -v bun >/dev/null 2>&1; then
        run_step "bun test" bun test
    elif command -v npm >/dev/null 2>&1; then
        run_step "npm test --if-present" npm test --if-present
        run_step "npm run lint --if-present" npm run lint --if-present
    fi
fi

# --- Rust ---
if [ -f Cargo.toml ]; then
    echo "== Rust =="
    ran_any=1
    maybe cargo check
    maybe cargo clippy --quiet
    maybe cargo test --quiet
fi

# --- Go ---
if [ -f go.mod ]; then
    echo "== Go =="
    ran_any=1
    run_step "go build ./..." go build ./...
    run_step "go vet ./..."   go vet ./...
    maybe golangci-lint run --timeout 2m
    run_step "go test ./..." go test ./...
fi

# --- Ruby ---
if [ -f Gemfile ]; then
    echo "== Ruby =="
    ran_any=1
    if [ ! -d vendor ] && ! command -v bundle >/dev/null 2>&1; then
        hint_bootstrap "Bundler is not available here. If this is an isolated worktree, bootstrap Ruby deps before trusting failures."
    fi
    maybe bundle exec rubocop
    maybe bundle exec rspec
fi

# --- PHP ---
if [ -f composer.json ]; then
    echo "== PHP =="
    ran_any=1
    if [ ! -d vendor ]; then
        hint_bootstrap "vendor/ is missing in this checkout. Run composer install in this worktree before trusting failures."
    fi
    maybe composer validate
    if [ -x vendor/bin/phpstan ]; then
        run_step "phpstan analyse" vendor/bin/phpstan analyse
    fi
    if [ -x vendor/bin/phpunit ]; then
        run_step "phpunit" vendor/bin/phpunit
    fi
fi

# --- Elixir ---
if [ -f mix.exs ]; then
    echo "== Elixir =="
    ran_any=1
    maybe mix compile
    maybe mix test
fi

echo
if [ $ran_any -eq 0 ]; then
    echo "no supported language detected at $TARGET"
    echo "supported: Python, Node/TS, Rust, Go, Ruby, PHP, Elixir"
    exit 2
fi

if [ $checks_run -eq 0 ]; then
    echo "no verification commands ran"
    echo "This usually means the repo was detected, but the isolated checkout is not bootstrapped yet."
    exit 3
fi

if [ $fail -ne 0 ]; then
    echo "FAIL — at least one step failed"
    exit 1
fi

if [ $bootstrap_hint -ne 0 ]; then
    echo "OK — checks passed, but this checkout showed signs of missing local bootstrap state"
    echo "If this was a fresh git worktree, re-run after recreating project-local deps for higher confidence."
    exit 0
fi

echo "OK — smoke test passed"
exit 0
