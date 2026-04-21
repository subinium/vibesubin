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

## Implementation notes
- Hand-off: `/<skill-name>` (exact vibesubin skill that owns the fix)
- Scope: <files/areas — concrete paths>
- Out of scope: <explicit list of what will NOT be touched>

## Linked
- Depends on: #<N>
- Blocked by: #<N>
- Supersedes: #<N>
- From: `/vibesubin` sweep <YYYY-MM-DD> (if the item came from a sweep report)
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

## Implementation notes
- Hand-off: `/refactor-verify` (perf focus)
- Scope: `src/api/users.ts`, `src/api/users.test.ts`
- Out of scope: schema changes, pagination contract, caching layer

## Linked
- From: `/vibesubin` sweep 2026-04-21
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

## Implementation notes
- Hand-off: `/refactor-verify`
- Scope: `src/auth/session.ts`, `src/components/SessionWarning.tsx`, `src/hooks/useFormDraft.ts`
- Out of scope: 세션 만료 시간 자체 변경, 서버 측 세션 저장소 교체

## Linked
- Depends on: #42
```

## When fields don't apply

- No dependencies → omit `Depends on` / `Blocked by` / `Supersedes` lines (keep the `Linked` heading only if one of them is filled).
- Not from a sweep → omit the `From:` line.
- Problem is trivial (typo, single-line fix) → the `Problem` section is still required; one sentence is acceptable, zero sentences is not.
- No clear out-of-scope → write `none` explicitly. Silence is ambiguous.
