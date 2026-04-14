# Language-specific smoke-test chains

Each entry is the canonical "does it still work?" chain for one language. Run them in the listed order during step 5 of the verification procedure. Fail fast on the cheapest check first.

If you're using `git worktree` isolation, remember that local environments such as `.venv/`, `node_modules/`, `vendor/`, or generated code are often **not** copied into the new worktree. Bootstrap them first, or treat "tool not found / module not found" as an environment setup issue rather than refactor evidence.

## Python

```bash
python -c "import <pkg>"              # import smoke test
ruff check .                          # lint (fast)
mypy .                                # typecheck (or pyright, or ty if mature enough)
pytest -q --tb=short                  # tests
```

Notes:
- Prefer `ruff` over `flake8` / `pylint` / `black`. One tool, much faster.
- `mypy` is the safer default in 2026. `ty` (Astral) and `pyrefly` (Meta) are maturing but not yet drop-in.
- If the project uses `uv`, substitute `uv run pytest` and `uv run ruff`.

## Node / TypeScript

```bash
node -e "require('./')"               # CJS import smoke (or: node --input-type=module -e 'import("./")')
tsc --noEmit                          # typecheck (TS projects)
eslint .                              # lint
vitest run                            # tests (or: jest, or: node --test)
```

Notes:
- For ESM projects, use `node --input-type=module -e 'import("./index.js")'`.
- If the project uses `pnpm` / `yarn` / `bun`, prefix accordingly.
- `tsc --noEmit` is the single most effective guard for TS refactors.

## Rust

```bash
cargo check                           # compile check (fast, no codegen)
cargo clippy -- -D warnings           # lint
cargo test                            # tests (runs doctest too by default)
```

Notes:
- `cargo check` is the cheap path — always run it before `cargo test`.
- `clippy -D warnings` makes lint warnings fail the check. For an initial baseline, drop `-D warnings`.

## Go

```bash
go build ./...                        # build everything
go vet ./...                          # static analysis
golangci-lint run                     # lint (if installed)
go test ./...                         # tests
```

Notes:
- `go test` implicitly runs `go vet` as part of the test binary build, so `go vet` is slightly redundant but worth running for the earlier failure signal.

## Java / Kotlin (Maven)

```bash
mvn compile                           # compile
mvn verify                            # full verification including tests
```

For Gradle: `./gradlew build`.

Notes:
- For refactors, **OpenRewrite** is the safest industrial tool. If the project already uses it, delegate to its recipes rather than editing by hand.

## Ruby

```bash
bundle exec rubocop                   # lint
bundle exec rspec                     # tests
```

## PHP

```bash
composer validate
vendor/bin/phpstan analyse
vendor/bin/phpunit
```

## Elixir

```bash
mix compile                           # compile
mix credo                             # lint (if installed)
mix dialyzer                          # typecheck (if installed)
mix test                              # tests
```

## Swift (SPM)

```bash
swift build
swift test
```

## C / C++ (CMake)

```bash
cmake --build build
ctest --test-dir build
```

Notes:
- C/C++ refactors without a test suite are high risk. Do not proceed past step 1 without at least a build check.

---

## Language auto-detection (for scripts)

When a helper script needs to auto-detect the language, use file presence:

| File exists at repo root | Language |
|---|---|
| `pyproject.toml` or `setup.py` | Python |
| `package.json` | Node/TS (check `tsconfig.json` for TS) |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `pom.xml` | Java (Maven) |
| `build.gradle` / `build.gradle.kts` | Java / Kotlin (Gradle) |
| `Gemfile` | Ruby |
| `composer.json` | PHP |
| `mix.exs` | Elixir |
| `Package.swift` | Swift |
| `CMakeLists.txt` | C/C++ |

If multiple are present (polyglot repo), run each language's smoke chain for the files that language owns.

---

## Nothing above matches?

If the project is in a language not listed here, the pattern is universal:

1. **Parse / compile** — does the code still parse?
2. **Typecheck** — if the language has types, does it still typecheck?
3. **Lint** — is the code in a known-bad state?
4. **Test** — does the test suite still pass?
5. **Run** — can the artifact still start?

Find the language's canonical tool for each of those five and run them in order. If no tool exists for a step, skip it and document the gap.
