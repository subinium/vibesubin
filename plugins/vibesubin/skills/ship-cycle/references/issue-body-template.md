# Issue body template

Every issue ship-cycle creates uses the structure below. Title and body adapt to the chosen language (Korean / English / Japanese / Chinese) but the section headings and checkboxes stay in English so `gh issue view` parsing and cross-repo grep remain stable.

## Structure

```
<body in the operator's chosen language>

## Problem
<what's wrong, with concrete evidence — file:line, metric, grep count, log excerpt>

## Acceptance criteria
- [ ] <verifiable criterion 1>
- [ ] <verifiable criterion 2>
- [ ] <verifiable criterion 3>

## Test plan (required — scoped by label)

Pick the row matching this issue's `type:` label. Every PR that closes this issue must demonstrate the corresponding test before merge.

| Label | Required test |
|---|---|
| `bug` | A regression test that reproduces the failure on `main`, then passes after the fix. Add to `tests/` and reference the test name here. |
| `feat` | A new test (unit or integration) covering the added behavior. Include the fixture path. |
| `perf` | A benchmark with before/after numbers. Measurement command + expected improvement threshold. |
| `refactor` | Before/after equivalence — AST-diff, `git diff` byte-identical for renamed symbols, OR a grep-count assertion that public signatures are preserved. `refactor-verify`'s 4-check is the authoritative mechanism. |
| `docs` / `chore` | `python3 scripts/validate_skills.py` passes + a grep assertion showing the documented change landed (e.g., `git grep <new-term>` returns expected count). |
| `security` | Pairs of tests — one demonstrates the vulnerability on `main`, one confirms the fix blocks it. |
| `ci` | A PR that would previously fail the new check is rejected; a passing PR is accepted. Cover both paths. |

Fill in for this issue:

```
Test: <concrete command or file path>
Assertion: <exact grep count, exit code, or test-name>
```

## Implementation notes
- Hand-off: `/<skill-name>` (exact vibesubin skill that owns the fix)
- Scope: <files/areas — concrete paths>
- Out of scope: <explicit list of what will NOT be touched>

## Docs plan (required — lands in same PR as the code fix)

Every doc that must update in the same PR as this issue's resolution. No follow-up PRs for docs.

| File | What changes |
|---|---|
| `CHANGELOG.md` | `### Added` / `### Changed` / `### Fixed` / `### Security` / `### Removed` bullet under `[Unreleased]`. Functional-only style per `CLAUDE.md` always-do #2. |
| `README.md` / `README.ko.md` / `README.ja.md` / `README.zh.md` | Skill-table row, workflow bullet, § section — whichever applies. Surgical edits per `CLAUDE.md` never-do #1. All four in the same PR. |
| `plugins/vibesubin/skills/<skill>/SKILL.md` | Skill-file edits, with validator passing. |
| `CLAUDE.md` | Change-type matrix row, load-bearing invariant update, Recently-decided entry — whichever applies. |
| `docs/PHILOSOPHY.md` | Invariant addition/amendment — only for major-version scope changes. |

Fill in for this issue:

```
- <file> — <what changes, one line>
- <file> — <what changes, one line>
```

If no docs need to change, state `- None — this is an internal-only change (explain why).`

## Linked
- Depends on: #<N>
- Blocked by: #<N>
- Supersedes: #<N>
- From: `/vibesubin` sweep <YYYY-MM-DD> (if the item came from a sweep report)

## Handoff notes (required — for the next AI session)

Two subsections. Both are load-bearing for avoiding duplicate work across sessions.

**What the next session needs to know.** Context that would take 20 minutes to reconstruct from a cold read — e.g., *"the 4-check verification is mandatory before closing; skipping it has historically caused silent regressions."*

**Already-done-at.** Links to commits, PRs, issues, or file paths where adjacent work has been done. Format: `- <scope> — done at #<issue> / <commit-sha> / <file:line>`. Prevents a fresh session from redoing work.

Fill in for this issue:

```
What next session needs:
- <one- or two-sentence context>

Already done at:
- <scope>: #<issue or sha or path>
```
```

## Title rules

- Under 72 characters. If longer, compress — full context lives in the body.
- Imperative mood: `Fix N+1 query in /api/users`, not `N+1 query in /api/users is slow`.
- Domain prefix when helpful: `auth:`, `api:`, `ui:`, `ci:`, `docs:`. Match the repo's commit-scope conventions.
- No trailing period. No emoji. No version numbers in the title (the milestone carries the version).

## Labels

Three axes, one label each:

| Axis | Values | Drives |
|---|---|---|
| **type** | `bug`, `feat`, `refactor`, `perf`, `docs`, `chore`, `security`, `test` | Milestone classification (see `milestone-rules.md`) |
| **priority** | `p0`, `p1`, `p2`, `p3` | Order inside the milestone |
| **area** | repo-specific (`auth`, `api`, `ui`, `db`, `ci`, ...) | Routing and assignment |

Optional single-use labels when applicable: `breaking`, `good-first-issue`, `needs-design`, `needs-data`.

## English example

```
Title: api: fix N+1 query in /users endpoint

## Problem
`src/api/users.ts:47` issues one query per user in the loop.
Measured: 120ms for 50 users on staging (trace id abc123).
`git grep -n 'User.findOne' src/api/ | wc -l` returns 14 — most in hot paths.

## Acceptance criteria
- [ ] Replace the N+1 loop with a single `User.findMany({ where: { id: { in: ids } } })`
- [ ] p95 on `/users?limit=50` drops below 50ms on staging
- [ ] Add a regression test that fails on the old pattern

## Test plan (required — scoped by label)

Label: `perf` → benchmark before/after.

Test: `node --experimental-vm-modules scripts/bench-users-endpoint.mjs --n=50 --runs=20`
Assertion: p95 drops from 120ms → <50ms; `tests/api/users.bench.test.ts:t_n_plus_one_fixed` passes.

## Implementation notes
- Hand-off: `/refactor-verify` (perf focus)
- Scope: `src/api/users.ts`, `src/api/users.test.ts`
- Out of scope: schema changes, pagination contract, caching layer

## Docs plan (required — lands in same PR as the code fix)

- `CHANGELOG.md` — `### Fixed` bullet under `[Unreleased]`: "Fix N+1 query in /users endpoint (#<N>)".
- `README.md` — no change (internal perf fix, not user-facing API).
- Other docs — None — endpoint contract unchanged.

## Linked
- From: `/vibesubin` sweep 2026-04-21

## Handoff notes (required — for the next AI session)

What next session needs:
- The existing `User.findMany` helper at `src/api/_shared/batch.ts:22` already batches correctly — reuse it rather than writing a new batch utility. Previous attempt #38 was reverted for skipping that helper.

Already done at:
- batch helper: `src/api/_shared/batch.ts:22`
- trace evidence: Sentry trace id abc123 (linked in #38's thread)
```

## Korean example

```
Title: auth: 세션 만료 시 조용히 로그인으로 리디렉트되는 문제 수정

## Problem
`src/auth/session.ts:91`에서 만료된 세션을 감지하면 에러 없이 `/login`으로 리디렉트한다.
사용자는 작업 중이던 폼 데이터를 잃는다. Sentry issue-4821: 지난 7일간 142건.

## Acceptance criteria
- [ ] 만료 직전 60초 구간에 토스트로 경고 표시
- [ ] 리디렉트 전 폼 데이터를 `sessionStorage`에 저장
- [ ] 재로그인 후 저장된 데이터로 폼 복구
- [ ] Sentry issue-4821이 1주일간 신규 이벤트 0건

## Test plan (required — scoped by label)

Label: `bug` → regression test required.

Test: `pnpm test src/auth/session.test.ts -t "session expiry preserves form draft"`
Assertion: 기존 `main`에서 실패(폼 데이터 유실) → 수정 후 통과. Sentry issue-4821 이벤트 카운트 1주 관찰.

## Implementation notes
- Hand-off: `/refactor-verify`
- Scope: `src/auth/session.ts`, `src/components/SessionWarning.tsx`, `src/hooks/useFormDraft.ts`
- Out of scope: 세션 만료 시간 자체 변경, 서버 측 세션 저장소 교체

## Docs plan (required — lands in same PR as the code fix)

- `CHANGELOG.md` — `### Fixed` 아래 `[Unreleased]` 항목: "세션 만료 시 폼 데이터 유실 문제 수정 (#<N>)".
- `README.md` / `README.ko.md` / `README.ja.md` / `README.zh.md` — 변경 없음(내부 버그 수정, 공개 API 무변경).
- `docs/auth/session.md` — `useFormDraft` 훅 사용 예시 1줄 추가.

## Linked
- Depends on: #42

## Handoff notes (required — for the next AI session)

What next session needs:
- `sessionStorage` 폴백은 Safari private 모드에서 예외를 던진다. #42에서 `try/catch` 래퍼 패턴을 이미 도입했으니 그대로 재사용. 새 래퍼를 만들지 말 것.

Already done at:
- storage wrapper: `src/lib/safe-storage.ts:14` (#42에서 추가)
- Sentry 연동: `src/lib/telemetry.ts:88`
```

## When fields don't apply

- No dependencies → omit `Depends on` / `Blocked by` / `Supersedes` lines (keep the `Linked` heading only if one of them is filled).
- Not from a sweep → omit the `From:` line.
- Problem is trivial (typo, single-line fix) → the `Problem` section is still required; one sentence is acceptable, zero sentences is not.
- No clear out-of-scope → write `none` explicitly. Silence is ambiguous.
