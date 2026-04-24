# Layperson Translation — `explain=layperson`

## Purpose

Layperson mode is an opt-in output style for the vibesubin umbrella aimed at non-developer "vibe coders" — people who are shipping code with AI but do not read the technical findings fluently. Enable it with any of: `/vibesubin explain`, `/vibesubin easy`, `쉽게 설명해줘`, `일반인도 이해되게`, `initiate easy mode`, `非開発者でも分かるように`, `用通俗的话解释`. The marker becomes `explain=layperson` and is passed to every specialist alongside existing markers. It does NOT change findings, severity, evidence, file:line references, or counts — those stay identical to balanced mode. It only changes *how* each finding is presented: adds a 3-dimension human-impact block, wraps each finding in a box layout, and substitutes jargon with plain language. Balanced mode remains the default for technical operators.

## The 3-dimension block

Every finding gets three questions answered in plain language when `explain=layperson` is active:

1. **왜 이것을 해야 하나요? (Why should you do this?)** — One sentence, human-impact framing. Who gets hurt, when, and how. Example: *"이걸 안 고치면 공격자가 비밀번호 없이도 사용자 데이터를 열람할 수 있어요."*

2. **왜 중요한 작업인가요? (Why is this an important task?)** — Severity translation + consequence sketch. Concrete timeline, concrete outcome. Example: *"지금 이대로 두면 사용자가 배포 직후부터 로그인 정보가 섞이거나, 한 사용자의 데이터가 다른 사용자에게 노출될 수 있어요."*

3. **그래서 무엇을 하나요? (So what will be done?)** — Concrete action in plain language. No jargon. Any unavoidable term is defined in parens on first use. Example: *"이 파일의 특정 함수를 두 개로 나누고, 사용자 입력을 그대로 쿼리에 넣지 않고 먼저 검증하는 단계를 추가합니다 (검증 = 입력값이 안전한지 미리 확인하는 것)."*

## Severity translation table

| Technical severity | Plain-language urgency (Korean / English) |
|---|---|
| CRITICAL | 지금 당장 (ship하기 전에 필수) / Right now (must fix before shipping) |
| HIGH | 이번 주 안에 / This week |
| MEDIUM | 다음 릴리즈 전까지 / Before the next release |
| LOW | 시간 날 때 정리 / When you have time |

The plain-language phrase replaces the raw severity label in the finding header. The technical severity is still emitted for downstream tools but is shown in smaller framing. Never invent urgency that does not match the underlying severity.

## Pretty format — one finding, box layout

```
┌─ 발견 #3 — 지금 당장 (ship하기 전에 필수) ────────────────────┐
│ 파일: src/api/user.ts:187                                    │
│ 발견한 스킬: audit-security                                   │
├─ 왜 이것을 해야 하나요? ─────────────────────────────────────┤
│ 공격자가 비밀번호 없이도 사용자 데이터를 읽거나 지울 수 있어요.│
│ SQL 인젝션 취약점 (= 입력값을 검증 없이 DB 쿼리에 넣는 문제)   │
│ 이 있어요.                                                    │
├─ 왜 중요한 작업인가요? ──────────────────────────────────────┤
│ 배포 직후부터 노출됩니다. 로그인한 사용자 한 명이 다른 모든    │
│ 사용자의 이메일·비밀번호 해시·주문 내역을 가져갈 수 있어요.   │
│ 이런 버그는 보통 몇 시간 안에 공격 대상이 됩니다.             │
├─ 그래서 무엇을 하나요? ──────────────────────────────────────┤
│ user.ts의 getUserById 함수에서 사용자가 보낸 id 값을 쿼리에   │
│ 직접 넣는 부분을 없애고, 파라미터화된 쿼리 (= DB에 값을       │
│ 따로 전달하는 안전한 방식) 로 바꿉니다.                       │
├─ 어떤 스킬이 고치나요? ─────────────────────────────────────┤
│ refactor-verify 또는 codex-fix 로 수정할 수 있어요.           │
└───────────────────────────────────────────────────────────────┘
```

The box is a visual frame, not ornament. It makes the 3 dimensions scannable at a glance — the operator can skip the technical report and read only the boxes.

## Bilingual support

Layperson mode respects the operator's language. Detection is the same as balanced mode: operator's last user turn is checked; Korean turns produce Korean boxes, English turns produce English boxes, same for Japanese and Chinese. Box headers (`발견 #3`, `파일:`, etc.) stay in the operator's language. Tool-facing metadata (severity key, specialist name) stays in English for stability.

### English mirror of the same finding

```
┌─ Finding #3 — Right now (must fix before shipping) ──────────┐
│ File: src/api/user.ts:187                                     │
│ Found by: audit-security                                       │
├─ Why should you do this? ────────────────────────────────────┤
│ An attacker can read or delete user data without a password.  │
│ This is a SQL injection bug (= the code puts user input       │
│ straight into a database query without checking it).          │
├─ Why is this an important task? ─────────────────────────────┤
│ Exposed from the moment you ship. One logged-in user can       │
│ pull every other user's email, password hash, and order        │
│ history. Bugs like this are usually attacked within hours.    │
├─ So what will be done? ──────────────────────────────────────┤
│ In user.ts, the getUserById function stops inserting the      │
│ user's id directly into the query. It switches to a           │
│ parameterized query (= a safer style that sends the value     │
│ to the database separately).                                  │
├─ Which skill will fix this? ─────────────────────────────────┤
│ refactor-verify or codex-fix can apply the fix.                │
└───────────────────────────────────────────────────────────────┘
```

### Japanese / Chinese — same shape, localized headers

Japanese uses `発見 #N — 今すぐ (出荷前に必須)` for the CRITICAL header and localizes the four section labels (`なぜこれをやるべきですか?` / `なぜ重要なタスクですか?` / `では何をしますか?` / `どのスキルが修正しますか?`). Chinese uses `发现 #N — 立刻 (上线前必须修复)` and `为什么要做这件事?` / `为什么是重要的任务?` / `那么要做什么?` / `哪个技能来修复?`. Box structure and content are identical to the Korean and English examples above.

## What changes vs. balanced mode

- Each finding gets the 3-dimension block.
- Each finding is wrapped in the box layout.
- Technical jargon is replaced by plain equivalents. Short glossary:
  - **SQL injection** → "공격자가 입력값을 악용해 DB에서 원하는 것을 꺼내가는 버그"
  - **dependency** → "이 프로젝트가 쓰는 외부 코드 조각"
  - **lint** → "코드 스타일·흔한 실수 자동 점검"
  - **hotspot** → "여러 번 고쳐지고 있는 불안정한 파일"
  - **CI** → "깃 푸시할 때마다 자동으로 돌아가는 검사"
  - **rebase** → "커밋 내역을 깔끔하게 재배열하는 작업"
  - **force push** → "원격 커밋 내역을 덮어쓰기 (위험)"
  - **semver** → "버전 번호 규칙 (1.2.3 형식)"
  - **lockfile** → "설치한 외부 코드의 정확한 버전을 고정해 두는 파일"
- The severity line uses the plain-language urgency phrase from the table above.
- Everything else — findings, counts, file:line references, confidence tags, evidence quotes — is identical to balanced mode.

## What does NOT change

- Findings themselves. Same files, same line numbers, same counts, same categories.
- Evidence. Same grep hits, same metrics, same before/after snippets.
- Read-only behavior in sweep mode. Layperson mode is presentation-only; it never changes what the specialists do.
- Accuracy. Plain language is never imprecise. "SQL injection" becomes "공격자가 비밀번호 없이도 사용자 데이터를 읽을 수 있는 버그" — not "a little security thing", not "maybe a bug". If a finding is CRITICAL, the plain-language phrase is "지금 당장" — never softer.

## Combination with harsh mode

`tone=harsh` and `explain=layperson` stack. Harsh-layperson output is direct, no hedging, plain language. The 3-dimension block uses the same sentences harsh mode would use, just without jargon.

Example harsh-layperson Dimension 1:
*"지금 이 상태로 배포하면 고객 데이터가 유출됩니다. 버그가 아니라 공격 경로입니다. 지금 당장 막아야 합니다."*

Not softened, not hedged, still plain-language. The rule from harsh mode holds: never inflates severity beyond the underlying finding, never invents findings, cites the same evidence balanced mode would.

## When NOT to use layperson mode

- The operator is a developer and explicitly asked for the technical report.
- The repo is already clean and every specialist returned zero findings. Wrapping "nothing to fix" in plain-language framing reads condescending; emit a one-line clean result instead.
- The operator explicitly asked for jargon or technical detail ("I'm a dev, give me the CVEs", "show me the raw findings"). Respect the override — do not force layperson framing on a technical audience.
- The finding is already plain-language native (e.g., "README is missing"). Box wrapping is still fine; synthetic jargon translation is not needed.
