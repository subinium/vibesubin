# vibesubin

AI 어시스턴트가 리팩토링, 감사, 배포를 "원래 이렇게 해줬으면" 하는 방식으로 하게 만드는, 이식 가능한 skill plugin입니다. `/vibesubin` 한 단어로 전부 한 번에 돌릴 수 있습니다.

개발자 출신은 아니지만 AI로 실제 서비스를 굴리는 사람들을 위해 만들었습니다. 제가 AI랑 코딩할 때 쓰는 습관들을 skill로 묶어둔 거라, 모든 규칙을 외우지 않아도 어시스턴트가 알아서 따라갑니다.

같은 `SKILL.md`가 **Claude Code**, **Codex CLI**, 그리고 **[skills.sh](https://skills.sh)가 지원하는 모든 agent** — Cursor, Copilot, Cline 등 — 에서 그대로 돌아갑니다. 한 번 써두면 어느 host에서나 집어갑니다.

> [English](./README.md) · [中文](./README.zh.md) · [日本語](./README.ja.md)

---

## Quick start

[Claude Code](https://code.claude.com) 설치 후:

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

아무 repo나 열고 `/vibesubin`. 모든 skill이 코드 전체에 병렬로 퍼져 read-only로 돌고, 우선순위가 매겨진 리포트 하나로 돌아옵니다. 리포트에서 항목을 승인하기 전까진 아무것도 안 건드립니다. skill한테 진짜로 *일*을 시키고 싶으면 이름으로 직접 부르세요 (`/refactor-verify`, `/setup-ci` 등). 이쪽은 파일을 바로 수정합니다.

Codex CLI, Cursor, Copilot, Cline 쓰시면 [Install](#install) 섹션으로.

---

## vibesubin이 뭐고 뭐가 아닌지

AI skill들 — `SKILL.md` 파일들 — 의 작은 묶음입니다. 요청이 맞는 상황이 오면 agent가 알아서 집어서 씁니다. trigger 문구 외울 필요 없이 평소처럼 말하면 돼요 — *"이 파일 안전하게 쪼개줘"*, *"뭐 새는 거 없어?"*, *"deploy 세팅해줘"* 같은 식으로요.

모든 skill이 공유하는 원칙: **증거를 보여줄 수 있을 때만 *완료*라고 말한다.** 리팩토링은 AI가 파일을 다시 썼다고 끝나는 게 아니라, 네 개의 독립 check가 "누락도 이동도 연결 실수도 없음"을 확인했을 때 끝납니다. 보안 점검은 감성 문단이 아니라 파일·라인 붙은 triage 리스트입니다.

**아닌 것**: SaaS 아니고 (데이터는 로컬에서만 돕니다), 컴플라이언스 도구 아니고 (SOC 2 / HIPAA 같은 거 없음), 코드 생성기 아닙니다. 이미 있는 repo를 개선합니다.

### 두 가지 쓰는 법 — sweep vs. 직접 호출

- **Sweep 모드 (`/vibesubin`).** 모든 코드 위생 skill이 병렬로, *read-only*로 돕니다. 우선순위 리포트 한 장만 나오고, 리포트에서 항목을 승인하기 전엔 아무것도 안 바뀝니다.
- **직접 호출 (`/refactor-verify`, `/setup-ci`, ...).** skill이 본업을 다 합니다. 파일 수정까지 포함해서요.
- **프로세스 skill (`/ship-cycle`)과 host 전용 wrapper (`/codex-fix`)** 는 직접 호출 전용입니다 — 외부 시스템 (GitHub, Codex) 을 건드리거나 릴리즈 상태를 관리하기 때문에 sweep에는 안 들어갑니다.

어떻게 부르든 절대 수정 안 하는 skill 세 개: `fight-repo-rot`, `audit-security`, `manage-assets` — 진단 전용입니다.

### 영역별 skill 라인업

**코드 품질 (5)**

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`refactor-verify`](#refactor-verify) | *"이 클래스 이름 바꿔줘"*, *"이 파일 쪼개줘"*, *"이 죽은 코드 안전하게 지워줘"* | 네 개의 verification pass로 "완료"를 스스로 증명하는 리팩토링 |
| [`audit-security`](#audit-security) | *"secret 샌 거 있어?"*, *"이거 안전해?"* | 500페이지 PDF 대신, 파일·라인 붙은 실제 findings 짧은 리스트 |
| [`fight-repo-rot`](#fight-repo-rot) | *"dead code 찾아줘"*, *"뭘 지워도 돼?"* | HIGH / MEDIUM / LOW confidence로 태깅된 dead code + god file, hotspot까지. 진단 전용 |
| [`manage-assets`](#manage-assets) | *"내 repo 너무 커"*, *"LFS 써야 해?"* | Bloat 리포트 — 큰 파일, git history의 big blob, LFS 후보. history 다시 안 씀 |
| [`unify-design`](#unify-design) | *"버튼들 통일해줘"*, *"이 색깔들 토큰으로 뽑아줘"* | 디자인 시스템 audit — tokens scaffold, hardcode된 hex와 magic px, 중복 component 통합 |

**문서 & AI 친화성 (2)**

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`write-for-ai`](#write-for-ai) | *"README / commit / PR 써줘"* | *다음* AI session이 실제로 읽을 수 있는 문서 — 근거 없는 과장 형용사 없이 |
| [`project-conventions`](#project-conventions) | *"main? dev? 어느 branch?"*, *"이 dep pin 해야 해?"* | 결정마다 기본값 하나 — GitHub Flow, 고정된 dep, 도메인 중심 레이아웃 |

**인프라 & 설정 (2)**

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`setup-ci`](#setup-ci) | *"deploy 세팅해줘"*, *"push로 배포되게"* | 돌아가는 GitHub Actions workflow + 말로 풀어쓴 walkthrough |
| [`manage-secrets-env`](#manage-secrets-env) | *"이 secret 어디에 둬야 돼?"*, *"`.env` 새고 있는 거 아니지?"* | 결정마다 주장 있는 답 하나 + secret 전체 lifecycle |

**릴리즈 프로세스 (1)**

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`ship-cycle`](#ship-cycle) | *"릴리즈 계획 짜자"*, *"이슈 드리븐"*, *"버전 컷"* | 이슈 드리븐 릴리즈 오케스트레이터 — 이중 언어 이슈 초안, 마일스톤=버전 클러스터링, 라벨별 워커 위임, changelog 집계, 태그 + 릴리즈 컷. **두 트랙** — GitHub (기본) 또는 다른 host용 PRD-on-disk |

**Host 전용 wrapper (1)**

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`codex-fix`](#codex-fix) | *"codex 돌려서 고쳐줘"*, *"run codex and fix"* | 얇은 wrapper: `/codex:rescue` → `refactor-verify`의 review-driven fix mode. **Claude Code + Codex 플러그인 전용**; 다른 host에선 한 줄 fallback |

새 skill은 `plugins/vibesubin/skills/`에 넣으면 `/vibesubin`이 알아서 집어갑니다.

---

## `/vibesubin` 커맨드

모든 코드 위생 skill을 repo에 병렬로 돌리고, findings를 우선순위 리포트 한 장으로 합치고, 승인 전까진 아무것도 안 건드리는 한 단어짜리 명령입니다.

시작 전에 범위를 좁힐 수 있습니다 (*"src/api만"*, *"security랑 repo rot만"*). sweep 모드의 specialist는 전부 read-only — findings만 내고 fix는 안 합니다. critical은 카테고리 상관없이 맨 위로 올라가고, 여러 specialist가 같은 파일을 지목하면 그 파일 우선순위가 뜁니다. 결과물은 vibe check 문단, specialist별 신호등 한 줄, top 10 고칠 것, 권장 순서, 한 문장 판정. synthesis 규칙 전체는 [umbrella `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md)에 있습니다.

**Sweep vs. 단일 skill.** 열린 질문엔 sweep (*"배포해도 되나?"*, *"second opinion"*). 원하는 게 분명하면 skill 직접 호출 (*"이 파일 리팩토링"* → `/refactor-verify`). 샌 secret은 sweep 건너뛰고 `/audit-security` 긴급 모드로 바로.

**Harsh mode.** opt-in 직설 버전 — `/vibesubin harsh`, *"brutal review"*, *"돌려 말하지 말고"*, *"매운 맛으로"*, *"厳しめで"*. read-only 유지, 근거도 동일, 완곡어만 걷어냄. 기본값은 언제나 balanced.

**Layperson mode.** opt-in 평문 모드 — `/vibesubin explain`, `/vibesubin easy`, *"쉽게 설명해줘"*, *"일반인도 이해되게"*, *"用通俗的话解释"*. 모든 finding에 3차원 박스 — *왜 해야 / 왜 중요 / 무엇을 할지* — 가 붙고, 심각도는 긴급도로 번역됩니다 (CRITICAL → *"지금 당장"*). harsh와 같이 쓸 수 있습니다. 자세한 건 [`references/layperson-translation.md`](./plugins/vibesubin/skills/vibesubin/references/layperson-translation.md).

**Skill 충돌.** 두 specialist가 같은 파일에서 의견이 엇갈릴 때 (예: *refactor-verify*는 "잠깐"을, *unify-design*은 "통합해"를 말할 때), 리포트에 `⚠ Skill conflict` 박스가 뜹니다 — 차이, 이유, 각 쪽의 근거가 붙고 선택은 operator가. 카탈로그는 [`references/skill-conflicts.md`](./plugins/vibesubin/skills/vibesubin/references/skill-conflicts.md).

---

## Install

| 경로 | Agent | 적합한 상황 |
|---|---|---|
| **A. Claude Code marketplace** | Claude Code | 가장 간단, 자동 업데이트 |
| **B. `skills.sh`** | Cursor, Copilot, Cline, Codex CLI, Claude Code | 여러 agent 동시 사용 |
| **C. 수동 symlink** | Claude Code 또는 Codex CLI | plugin을 직접 고치면서 쓸 때 |

**A — Claude Code marketplace** (추천)

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

업데이트는 `/plugin marketplace update`. 삭제는 `/plugin uninstall vibesubin`.

**B — skills.sh** (cross-agent, [skills.sh](https://skills.sh) 기반)

```bash
npx skills add subinium/vibesubin
```

같은 명령을 다시 돌리면 업데이트. 제거는 `npx skills remove vibesubin`. 지원 host는 `npx skills --help`에서 확인.

**C — 수동 symlink** (수정 가능, 오프라인, `git pull`로 즉시 반영)

```bash
git clone https://github.com/subinium/vibesubin.git
cd vibesubin
bash install.sh                  # Claude Code (기본)
bash install.sh --to codex       # Codex CLI
bash install.sh --to all         # 둘 다
bash install.sh --dry-run        # 미리보기
```

업데이트는 `git pull`. 삭제는 `bash uninstall.sh [--to codex|all]` — 스크립트가 만든 symlink만 지웁니다.

설치 문제 있으면 agent session 전부 닫고 새로 여세요 (skill이 session 단위로 cache됩니다). 그래도 안 되면 [issue](https://github.com/subinium/vibesubin/issues) 열어주세요.

---

## 스킬들

모든 skill은 [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/) 아래 있습니다. 아래는 사용자용 버전이고, 자세한 방법론은 각 skill의 `SKILL.md`와 옆의 `references/`에 있습니다.

### 코드 품질

#### `refactor-verify`

제가 제일 애착 가지는 skill입니다. AI가 코드를 건드릴 때 가장 무서운 실패는 조용한 실패입니다 — rename 됐고, 테스트도 통과했고, 3주 뒤에 누군가 옛날 이름을 가리키는 code path를 밟고 전체가 터지는 거요. `refactor-verify`는 딱 그 실패를 불가능하게 만들려고 있습니다.

구조적 refactor (move, rename, split, merge, extract, inline)와 안전한 삭제 (`fight-repo-rot`이 dead라고 확인한 코드 제거)를 다룹니다. 둘 다 같은 네 개 check를 씁니다: symbol set 보존, 옮긴 코드의 바이트 동일성, typecheck/lint/test/smoke 재실행, 그리고 import graph 전체의 caller 감사. 네 개 중 하나라도 실패하면 다음 step으로 안 넘어갑니다. 요청 안 한 파일은 안 건드리고, check 깨진 상태로 *완료* 말하지 않고, `fight-repo-rot`이 LOW로 태깅한 코드를 사람 확인 없이 지우지 않습니다.

#### `audit-security`

엔터프라이즈 스캐너는 500개 잡고 490개가 오탐입니다. `audit-security`는 정반대 — 사람이 실제로 저지르는 실수를 잡는 짧고 수제 패턴 리스트이고, 모든 hit이 진짜 / 오탐 / 사람 확인 필요로 분류되고 한 줄 이유가 붙습니다.

뻔한 것들 (commit에 박힌 secret, SQL concatenation, `eval` / `exec` / `pickle.loads`), 덜 뻔한 것들 (user-controlled 파일 path, escape 안 된 HTML, `httpOnly` / `Secure` 빠진 cookie, wildcard CORS), 잊어버리는 것들 (git history의 `.env`, `.pem`, SSH key)을 봅니다. 심각도는 평범한 말로 — "CWE-89"보다 *"모르는 사람이 모든 유저 데이터를 읽을 수 있음"* 쪽입니다. penetration test 아닙니다 — static만, network 안 봅니다.

#### `fight-repo-rot`

먼저 dead-code detector, 두 번째로 잡동사니 탐지기, 항상 순수 진단. 아무도 부르지 않는 함수, import 안 되는 파일, 고아 module, manifest에만 있는 의존성을 찾습니다. 그 위에 god file, hotspot (자주 바뀌고 동시에 복잡한 것들), hardcode된 절대경로, IP 리터럴, 6개월 넘은 `TODO` / `FIXME`를 플래그합니다.

dead-code 후보는 전부 confidence 태그가 붙습니다: **HIGH** (어디서도 참조 없음 — `refactor-verify`에 넘기면 안전), **MEDIUM** (test에서만 참조, 혹은 dynamic dispatch — operator 확인), **LOW** (export된 symbol, 생성 코드, reflection / DI — 반드시 사람이 봄). 수정도 삭제도 안 합니다. 삭제는 `refactor-verify`, hardcode된 경로는 `project-conventions`, CVE 의존성은 `audit-security`로 hand-off.

#### `manage-assets`

bloat 탐지기지, 코드 분석기가 아닙니다. binary 무게를 드러냅니다 — working tree 파일 크기, git history의 blob 크기 (안 보이는 쪽), LFS 마이그레이션 후보, 자산 디렉터리 증가, 중복 binary. **진단 전용** — 파일 안 지우고, history 안 다시 쓰고, `git filter-repo`나 `git lfs migrate` 안 돌립니다. 승인된 제거는 `refactor-verify`에 (검증된 history 재작성), `.gitignore` 모양이면 `manage-secrets-env`에, 참조도 없으면 `fight-repo-rot`에 넘깁니다.

#### `unify-design`

프론트엔드용 디자인 시스템 일관성 — tokens + 중복 audit. 프로젝트 BI (색상, 간격, 타이포그래피, radius, shadow, breakpoint, 핵심 component) 를 단일 source of truth로 취급하고, 거기서 벗어난 것들을 token 참조로 다시 씁니다. 프레임워크를 자동 감지합니다 (Tailwind v3/v4, CSS Modules, styled-components, Emotion, MUI, Chakra, vanilla CSS) — 프로젝트 관용구를 그대로 씁니다. 외래 패턴 안 끌고 옵니다.

세 가지를 합니다. tokens 파일 없으면 scaffold (primary color와 display font는 사용자에게 물음), drift audit (hardcode된 hex, `w-[432px]` 같은 Tailwind arbitrary value, inline style 객체, 중복 Button/Card/Nav), drift 수정 (작은 교체는 바로, 여러 파일 통합은 `refactor-verify`). 브랜드를 지어내지 않고, 프레임워크를 바꿔 쓰지 않습니다.

### 문서 & AI 친화성

#### `write-for-ai`

사람뿐 아니라 *다음* AI session을 위한 문서. 새 AI session이 그러듯 repo를 처음부터 읽고, invariant를 뽑고 (프로젝트가 *뭘* 하는지만이 아니라 어떤 규칙을 따르는지), 해당 템플릿을 채웁니다 (README, commit, PR description, architecture doc, `CLAUDE.md`, `AGENTS.md`). 쓰기 전에 모든 주장을 검증합니다 — README에 `pnpm test`가 suite를 돌린다고 쓰려면, skill이 먼저 `pnpm test`를 돌려봅니다.

이게 막는 시나리오: AI한테 README를 다시 써달라고 했더니 잘 썼어요. 근데 환경변수 얘기하던 문단이 조용히 사라져 있습니다. 알아채지 못 해요. 다음 AI session은 새 README에서 시작하니까 env 구조가 있는 줄도 모릅니다.

#### `project-conventions`

낮은 판돈 쪽 구조적 기본값: branch 전략, dep 고정, 디렉터리 레이아웃, 절대경로 위생. 기본값 — GitHub Flow (`main` + 단기 feature 브랜치, `dev` 없음), production dep 정확히 pin + lockfile commit, Dependabot / Renovate 월 단위, 도메인 중심 레이아웃, 소스에 절대경로 없음. 모든 규칙에 한 문장 이유.

새 프로젝트면 `dependabot.yml`과 브랜치 전략 노트를 scaffold합니다. 기존 프로젝트면 일탈을 audit하고, 여러 파일 건드리는 수정은 `refactor-verify`에 넘깁니다.

### 인프라 & 설정

#### `setup-ci`

Pack에서 가장 큰 생산성 잠금해제 — 제대로 세팅되면 deploy는 그냥 `git push`가 됩니다. 먼저 개념을 말로 풀어주고 (runner, Secrets, `concurrency` group, 배포 후 health check), `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod`에서 stack을 감지하고, workflow 두 개를 생성합니다: `test.yml` (timeout 있는 test + lint), `deploy.yml` (host별 패턴 — SSH, Vercel, Fly.io, Cloud Run, Netlify — concurrency guard와 SSH key 정리, health check 포함).

Secrets를 대신 추가하지 않습니다 (GitHub UI에 두는 거). host도 추측 안 합니다.

#### `manage-secrets-env`

"이 값 어디에 둬야 하지?"의 판돈 큰 조각 — 잘못 두면 사건이지, 스타일 선호가 아닙니다. 네 개 bucket 결정 트리 (소스 상수 / env var / 로컬 `.env` / CI secret store), `.env.example` ↔ `.env` drift check, 기본 안전한 `.gitignore` 템플릿, 그리고 secret의 전체 lifecycle (추가 / 업데이트 / 로테이션 / 제거 / 마이그레이션 / audit / provision).

기본값: 런타임 불변 상수는 코드에, 로컬 secret은 committed `.env.example`과 함께 `.env`에, production secret은 CI secret store에, 환경별 runtime 값은 환경변수로, `.gitignore`는 secret 모양 항목이 전부 미리 채워진 채로 출발. 기존 프로젝트면 audit하고, 이미 tracked된 secret 파일은 사건급 finding으로 플래그 — 이미 새면 `audit-security`에 넘깁니다.

### 릴리즈 프로세스

#### `ship-cycle`

팩의 유일한 **process-카테고리** 스킬. 코드를 *둘러싼 라이프사이클* — 이슈, 마일스톤, 버전, 태그, 릴리즈, changelog — 을 다룹니다. 루프: intake → draft → cluster → confirm → create → branch → execute → release. 이중 언어 이슈 본문 (한/영/일/중), semver 결정 트리 (bug/perf/refactor → patch; additive feat → minor; breaking → major), 패치당 ~5개 상한.

**두 트랙.** **GitHub 트랙** (기본) 은 `gh` API 사용 — 이슈, 마일스톤, PR, 릴리즈가 GitHub에 살고, `Closes #<N>` footer로 merge 시 자동 close. **PRD 트랙** (다른 host) 은 `docs/release-cycle/vX.Y.Z/` 아래 로컬 markdown 파일 사용 — 같은 방법론, 같은 컨벤션, 다른 감사 추적. Step 1.5에서 operator가 선택. **컨벤션은 [`references/pr-branch-conventions.md`](./plugins/vibesubin/skills/ship-cycle/references/pr-branch-conventions.md) 대로 강제됩니다**: GitHub Flow 브랜치 (`<type>/<issue-N>-<slug>`), Conventional Commits + 필수 `Closes #<N>` footer, 6개 섹션 PR 템플릿 (Context / What changed / Test plan / Docs plan / Risk / Handoff notes), `--force-with-lease`를 쓰는 rebase-first merge, `main` / `master` / `release/*`에는 force-push 금지.

초안 승인 게이트 안 건너뜀, main에 CI 그린 없이 태그 안 푸시, 관계없는 항목을 한 마일스톤에 안 섞습니다.

### Host 전용 wrapper

#### `codex-fix`

한 가지 워크플로우를 위한 얇은 wrapper (~100줄): *"편집 한 묶음 끝내고, Codex로 second-model 리뷰 돌리고, Claude가 검증과 함께 해결하게 한다."* 현재 branch diff에 `/codex:rescue`를 invoke하고, findings를 `refactor-verify`의 review-driven fix mode에 넘깁니다.

**Claude Code + Codex 플러그인 전용.** 다른 host에서는 *"Codex 플러그인이 감지되지 않았습니다 — findings를 `/refactor-verify`에 직접 넘겨주세요."* 출력 후 깔끔히 종료.

Claude Code + Codex에 있고 리뷰 소스가 Codex면 `/codex-fix`. 다른 소스면 (사람 PR 리뷰, Sentry, `gitleaks`, Semgrep, 붙여넣은 메모) `/refactor-verify` 직접 호출 — 엔진은 같고, 입력 경로만 다릅니다. [`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md) 규칙 9번의 포터블-엔진-+-얇은-wrapper 패턴.

---

## 실전 사용

호출 방식은 세 가지, 아는 만큼 골라쓰면 됩니다.

어디서부터 시작할지 모르겠으면 `/vibesubin` 쳐서 전부 돌리세요. 뭐가 문제인지는 알면 평소 말로 하시면 됩니다 — *"이거 정리해줘, 아무것도 깨지 말고"*는 `refactor-verify`, *"secret 샌 거 있어?"*는 `audit-security`, *"제일 먼저 뭘 고쳐야 돼?"*는 `fight-repo-rot`. 어느 skill인지 정확히 알면 이름으로 부르세요: `/refactor-verify`, `/audit-security` 등.

모든 skill은 같은 4-part 출력 모양을 따릅니다: 뭘 했는지, 뭘 찾았는지, 뭘 검증했는지, 다음에 뭘 해야 하는지. 이 네 부분 없이 산문 덩어리만 돌아오면 버그입니다 — [issue](https://github.com/subinium/vibesubin/issues) 열어주세요.

### 자주 나오는 흐름

- **Repo 청소.** `fight-repo-rot`이 최악 지점 찾기 → `refactor-verify`가 검증과 함께 수정 → `write-for-ai`가 commit과 PR 작성.
- **Release 준비.** `audit-security`로 secret 점검 → critical은 `refactor-verify`로 → `setup-ci`로 다음부터 회귀 자동 감지.
- **새 repo 인계 받음.** `/vibesubin` 전체 sweep → `write-for-ai`가 빠진 `CLAUDE.md` 채움 → `manage-secrets-env`가 `.gitignore`·secret 점검 → `project-conventions`가 branch·dep·레이아웃 점검.
- **처음부터 시작.** `manage-secrets-env`가 `.env.example`·`.gitignore` scaffold → `project-conventions`가 Dependabot·branch 노트 scaffold → `setup-ci`가 workflow 깔기 → `write-for-ai`가 README·`CLAUDE.md` 작성.
- **"내 repo 왜 이렇게 커?"** `manage-assets`가 bloat 리포트 → `refactor-verify`가 history rewrite나 LFS 마이그레이션을 검증과 함께 실행.
- **"페이지마다 모양이 조금씩 달라."** `unify-design`이 tokens 파일을 scaffold (없으면), drift audit, component를 token 참조로 다시 씀 → `refactor-verify`가 여러 파일 통합을 처리.
- **"편집 끝났고 Codex 한번 돌려서 정리하자" (Claude Code + Codex plugin 전용).** `codex-fix`가 `/codex:rescue`를 현재 branch에 돌림 → findings를 `refactor-verify`의 review-driven fix mode에 넘김 → triage, 검증, back-reference commit. 다른 host나 다른 리뷰 소스 (PR 리뷰, Sentry, 스캐너, 붙여넣은 메모) 라면 findings를 `/refactor-verify`에 직접 넘겨주세요 — 엔진은 같고, 입력 경로만 다릅니다.
- **릴리즈 계획 (Claude Code + GitHub + `gh` 한정).** 일련의 개선이 쌓였거나 `/vibesubin` sweep이 우선순위 리스트를 내놓은 상황 → `ship-cycle`이 리스트에서 이중 언어 이슈 초안 작성 → 다음 semver 버전에 매핑되는 마일스톤으로 클러스터링 → 각 이슈를 올바른 워커에 위임해서 검증된 실행 → 마일스톤 닫히면 닫힌 이슈들에서 기능 중심 체인지로그 항목 집계, 두 매니페스트 버전 올림, 어노테이션 태그 컷, GitHub 릴리즈 생성. 비-GitHub 호스트나 `gh` 미인증 시 `ship-cycle`은 한 줄 폴백 후 종료 — 그 경우 하위 워커를 직접 호출하세요.

이런 flow를 직접 짤 필요는 없습니다. skill이 다음 hand-off가 필요한 시점을 알려줍니다.

---

## 내 skill 추가하기

새 skill은 `plugins/vibesubin/skills/<skill-name>/` 아래의 self-contained 디렉토리입니다. 넣고 agent 재시작하면 `/vibesubin`과 autocomplete 메뉴가 바로 집어갑니다.

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # 필수, 500줄 이하, YAML frontmatter 포함
├── references/           # 선택, 자세한 문서
├── scripts/              # 선택, 실행 가능한 helper
└── templates/            # 선택, 프로젝트에 복사되는 파일
```

새 skill이 따라야 할 규칙: *완료*는 주장이 아니라 검증, `SKILL.md`는 500줄 이하이고 깊이는 `references/`에, 출력은 4-part 모양, sweep에 들어갈 skill은 read-only 모드 필수, 모든 skill은 자기 confidence의 한계를 명시.

메인 plugin에 포함시키고 싶으면 trigger 문구, 하는 일, 구체적 예시를 적어서 [issue](https://github.com/subinium/vibesubin/issues)로 주세요. [`CONTRIBUTING.md`](./CONTRIBUTING.md) 참고.

---

## 철학

모든 skill이 공유하는 규칙 몇 개입니다. 외울 필요는 없고 — 지금과 앞으로의 skill이 일관되게 유지되라고 있는 겁니다.

**AI는 성실한 주니어 개발자입니다.** 주니어는 열심히 일하고, 가끔은 멈춰서 물어봐야 할 때 그냥 밀고 나갑니다. 이 plugin은 더 신중한 손이라면 멈췄을 지점에 *"멈추고 물어보기"* 순간을 꽂아 넣습니다.

**완료는 증명된 거지 주장한 게 아닙니다.** 어떤 task가 complete라고 쓰여 있다면 그 뒤엔 실행 결과가 있습니다 — 통과한 test, 일치하는 hash, 살아있는 `200 OK`. 증거 없는 단언은 버그입니다.

**문서는 사람용만큼이나 다음 AI session용입니다.** 지금 대화는 session이 끝나면 사라집니다. README, commit, PR body는 새로운 session이 맥락을 다시 쌓을 수 있게 쓰여야 합니다.

**기존 컨벤션이 기본값입니다.** plugin이 브랜치 전략이나 파일 레이아웃, config를 기분 따라 몰래 덮어쓰지 않습니다.

**문서는 과장 없이 객관적으로.** 벤치마크나 실제 사용 사례 없이 *"빠르다"*, *"production-ready"*, *"best-in-class"* 같은 단어를 쓰지 않습니다. 능력 주장에는 검증 명령어가 함께 붙어야 합니다. 안 그러면 지웁니다.

이 plugin은 [현재도 유지보수 중](./MAINTENANCE.md)입니다. 리팩토링 도구는 계속 진화하고, skill system은 바뀌고, LLM 실패 양상도 달라지니까요 — 각 skill은 정기적으로 리뷰됩니다.

---

## 기여

오픈소스지만 PR은 지금 안 받고 있습니다. 버그, 새 언어·런타임 지원 요청, 애매한 문서, 새 skill 아이디어 있으면 [issue](https://github.com/subinium/vibesubin/issues)로 주세요. 메인테이너가 직접 보고 반영합니다. 목소리 일관성을 위해서요. 자세한 건 [`CONTRIBUTING.md`](./CONTRIBUTING.md).

---

## 라이선스

MIT — [LICENSE](./LICENSE) 참고.

---

변경 내역은 [`CHANGELOG.md`](./CHANGELOG.md)에서 추적합니다. Plugin 버전은 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json)에 있습니다.
