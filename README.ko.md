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

AI skill들 — `SKILL.md` 파일들 — 의 작은 묶음입니다. 요청이 맞는 상황이 오면 agent가 알아서 집어서 씁니다. trigger 문구를 외울 필요 없이 그냥 평소처럼 말하면 돼요. *"이 파일 안전하게 쪼개줘"*, *"뭐 새는 거 없어?"*, *"deploy 세팅해줘"* 같은 식으로요.

모든 skill이 공유하는 단 하나의 원칙: **증거를 보여줄 수 있을 때만 *완료*라고 말한다.** 리팩토링은 AI가 파일을 다시 썼다고 끝난 게 아니라, 네 가지 독립적인 check가 "누락도 이동도 연결 실수도 없음"을 확인했을 때 끝납니다. 보안 점검은 "괜찮아 보이네요" 같은 감성 문단이 아니라, 각 항목이 진짜 / 오탐 / 사람이 봐야 함으로 분류된 리스트입니다. 파일명과 라인 번호까지 붙어서요.

**아닌 것**: SaaS 아니고 (데이터는 로컬에서만 돕니다), 컴플라이언스 도구 아니고 (SOC 2 / HIPAA 같은 거 없음), 코드 생성기 아닙니다. 이미 있는 repo를 개선합니다.

### Read-only sweep vs. 진짜로 수정하는 skill

이거 먼저 확실히 해두는 게 좋습니다. plugin을 쓰는 방법이 두 가지인데, 동작이 완전히 다릅니다.

- **Sweep 모드 (`/vibesubin`).** 모든 skill이 병렬로, *read-only*로 돕니다. findings만 내놓고 fix는 안 합니다. 리포트에서 항목을 승인하기 전엔 repo가 하나도 안 바뀝니다. "솔직한 second opinion 한 번 받고 싶다" 싶을 때 쓰는 모드예요.
- **직접 호출 (`/refactor-verify`, `/setup-ci`, `/write-for-ai`, `/manage-secrets-env`, `/project-conventions`, `/unify-design`).** skill이 본업을 다 합니다. 파일 수정까지 포함해서요. `refactor-verify`는 의존성 트리 전체에 걸쳐 코드를 고쳐 씁니다. `setup-ci`는 돌아가는 YAML을 `.github/workflows/`에 떨굽니다. `write-for-ai`는 README를 고칩니다. `manage-secrets-env`는 `.env.example`, `.gitignore`을 scaffold하고 secret 전체 lifecycle을 돌립니다. `project-conventions`는 Dependabot을 scaffold하고 dep pinning을 강제하고 hardcode된 경로를 고칩니다. `unify-design`은 tokens 파일을 scaffold하고 component를 token 참조 형태로 다시 씁니다. "진짜 일 좀 해줘" 모드입니다.

어떻게 부르든 절대 수정 안 하는 skill 세 개: **`fight-repo-rot`** (순수 진단 — dead code와 smell을 찾고, 삭제는 `refactor-verify`에 넘김), **`audit-security`** (static triage 리포트만), **`manage-assets`** (bloat 리포트만 — history 다시 쓰는 일도, 파일 지우는 일도 없음). 나머지 — `refactor-verify`, `setup-ci`, `write-for-ai`, `manage-secrets-env`, `project-conventions`, `unify-design` — 은 직접 호출하면 진짜 worker skill이고, sweep에서 불리면 read-only reporter입니다.

### 지금 들어 있는 skill

| Skill | 이럴 때 | 이렇게 돌려줌 |
|---|---|---|
| [`refactor-verify`](#1-refactor-verify) | *"이 클래스 이름 바꿔줘"*, *"이 파일 쪼개줘"*, *"이 죽은 코드 안전하게 지워줘"* | refactor, rename, split, 삭제 — 의존성 트리 leaf부터 올라가며 실행, 완료 직전에 네 가지 verification pass |
| [`audit-security`](#2-audit-security) | *"secret 샌 거 있어?"*, *"이거 안전해?"* | 500페이지 PDF 대신, 파일·라인 붙은 실제 findings 짧은 리스트 |
| [`fight-repo-rot`](#3-fight-repo-rot) | *"dead code 찾아줘"*, *"뭘 지워도 돼?"* | HIGH / MEDIUM / LOW confidence로 태깅된 dead code + god file, hotspot, hardcode된 경로, 테스트 rot까지. 진단만 — 절대 수정 안 함 |
| [`write-for-ai`](#4-write-for-ai) | *"README / commit / PR 써줘"* | *다음* AI session이 실제로 읽을 수 있는 문서 — 근거 없는 과장 형용사 없이 |
| [`setup-ci`](#5-setup-ci) | *"deploy 세팅해줘"*, *"push로 배포되게"* | 돌아가는 GitHub Actions workflow + 말로 풀어쓴 walkthrough |
| [`manage-secrets-env`](#6-manage-secrets-env) | *"이 secret 어디에 둬야 돼?"*, *"`.env` 새고 있는 거 아니지?"* | 한 줄 이유가 붙은 주장 있는 답 + secret 전체 lifecycle |
| [`project-conventions`](#7-project-conventions) | *"main? dev? 어느 branch?"*, *"이 dep pin 해야 해?"*, *"hardcode된 경로?"* | 결정마다 기본값 하나 — GitHub Flow, 고정된 dep, 도메인 중심 레이아웃, 소스에 home-dir 없음 |
| [`manage-assets`](#8-manage-assets) | *"내 repo 너무 커"*, *"LFS 써야 해?"* | Bloat 리포트 — 큰 파일, git history의 big blob, LFS 후보. 순수 진단 — history 다시 안 씀 |
| [`unify-design`](#9-unify-design) | *"버튼들 통일해줘"*, *"페이지마다 모양이 다 달라"*, *"이 색깔들 토큰으로 뽑아줘"* | 디자인 시스템 audit — tokens 파일 없으면 scaffold, hardcode된 hex와 magic px 전부 찾아냄, 중복 component 통합 |

새 skill은 `plugins/vibesubin/skills/`에 넣으면 `/vibesubin`이 알아서 집어갑니다.

---

## `/vibesubin` 커맨드

plugin의 모든 skill을 repo에 병렬로 돌리고, findings를 리포트 하나로 합치고, 승인 전까진 아무것도 안 건드리는 한 단어짜리 명령입니다.

돌아가는 방식은 이렇습니다. 먼저 skill이 한 문장으로 "이거 할 거예요"라고 말하고, 범위 좁힐 기회를 줍니다 (*"src/api만"*, *"security랑 repo rot만"*). 그다음 각 specialist를 isolated task agent로 뿌립니다. 실행이 서로 격리되니까 agent 간 간섭이 없습니다. 이 pass에서 모든 specialist는 read-only입니다 — findings만 내고 fix는 안 합니다. 테스트 suite가 아예 안 뜨는 것처럼 돌릴 수 없는 상황이면, 그 사실 자체를 finding으로 돌려주고 빠집니다. specialist 하나가 죽어도 전체 sweep이 막히진 않아요.

돌아온 결과는 synthesis 규칙으로 병합됩니다. critical은 카테고리 상관없이 맨 위로 올라갑니다 (샌 secret > hotspot > 누락된 docstring). 여러 specialist가 같은 파일을 독립적으로 지목하면 그 파일 우선순위가 뜁니다. findings는 카테고리가 아니라 파일 기준으로 묶입니다 — 실제로 고칠 땐 파일 단위로 고치니까요. 모든 항목에 구체적 권장 조치가 한 개씩 붙습니다.

결과물은 markdown 리포트 한 장: vibe check 문단, specialist별 신호등 한 줄, top 10 고칠 것, 권장 순서, 한 문장 판정. 다 괜찮으면 괜찮다고 말합니다. 승인 전까진 repo가 안 바뀝니다.

리포트 템플릿과 synthesis 규칙 전체는 [umbrella `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md)에 있습니다.

**Sweep vs. 단일 skill.** 열린 질문엔 sweep: *"방금 이 repo 물려받음"*, *"배포해도 되나?"*, *"second opinion"*. 원하는 게 분명하면 skill 직접 호출: *"이 파일 리팩토링"* → `/refactor-verify`. *"`.env` push해버림"* → `/audit-security`, 긴급 모드. *"README 써줘"* → `/write-for-ai`.

**Harsh mode.** sweep은 기본적으로 balanced 톤으로 돕니다 — 솔직하지만 너무 차갑진 않게. 매운 버전을 원하면 그렇게 시키세요: *"`/vibesubin harsh`"*, *"brutal review"*, *"돌려 말하지 말고"*, *"매운 맛으로"*, *"厳しめで"*. 리포트는 여전히 read-only고 근거도 똑같이 붙지만, 완곡한 표현을 걷어내고 제일 나쁜 finding부터 꺼내고, 실제 문제가 있는데 *"괜찮아 보여요"*로 덮고 끝내는 걸 거부합니다. opt-in 전용 — 자동으로 harsh로 가는 일은 없습니다.

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

## Skill 각각

모든 skill은 [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/) 아래 있습니다. 아래 설명은 사용자용 버전이고, 자세한 방법론은 각 skill의 `SKILL.md`와 옆의 `references/` 폴더에 있습니다. 이 파일들을 직접 읽을 필요는 없습니다 — AI가 읽으니까요 — 궁금하시면 열어보셔도 됩니다.

### 1. `refactor-verify`

제가 제일 애착 가지는 skill입니다. AI가 코드를 건드릴 때 가장 무서운 실패는 조용한 실패입니다 — 함수가 어디로 옮겨졌고, rename도 됐고, 테스트도 통과했는데, 3주 뒤에 누군가 옛날 이름을 가리키는 code path를 밟고 전체가 터지는 거요. `refactor-verify`는 딱 그 실패 유형을 불가능하게 만들려고 있습니다.

두 종류의 변경을 다룹니다 — 구조적 refactor (move, rename, split, merge, extract, inline)와 안전한 삭제 (`fight-repo-rot`이 dead라고 확인한 코드 제거). 둘 다 같은 네 가지 check를 씁니다.

손 대기 전에 현재 상태를 snapshot합니다: 어떤 함수가 어디 있는지, 지금 테스트가 통과하는지, linter 결과는 어떤지. 이게 *before* 그림입니다. 그다음 변경을 의존성 트리로 쪼개서 leaf부터 올라갑니다. 덕분에 실행 중간에 반쪽짜리 상태에 빠지는 일이 없어요.

매 스텝 끝나면 독립적인 check 네 개가 돕니다. 첫 번째는 symbol set을 훑어서 이전에 있던 public name이 전부 여전히 있거나 의도적으로 지워진 건지 확인합니다. 두 번째는 옮기거나 남긴 코드가 whitespace 빼고 비트 단위로 동일한지 봅니다. 세 번째는 typecheck, lint, test, smoke run을 다시 돌립니다. 네 번째 — 실전 버그를 제일 많이 잡는 check — 는 영향받은 모든 symbol의 caller를 전부 순회하면서 올바른 곳을 가리키는지, 지워진 symbol이면 아무 곳도 안 가리키는지 확인합니다. 네 개 중 하나라도 실패하면 skill이 다음 step으로 안 넘어갑니다.

안 하는 것들: 요청 안 한 파일 건드리기, check 깨진 상태로 *완료* 말하기, suite가 안 뜰 때 테스트 결과 지어내기, move 중에 함수 body 고치기, `fight-repo-rot`이 LOW라고 태깅한 코드를 사람 확인 없이 지우기.

### 2. `audit-security`

엔터프라이즈 보안 스캐너들은 노이즈 문제가 있습니다. 500개 잡고 그중 490개가 오탐이라, 일주일쯤 지나면 사람들이 다 무시합니다. 진짜 critical이 파묻히죠. `audit-security`는 정반대 모양입니다 — 사람이 실제로 저지르는 실수를 잡는 짧고 수제 패턴 리스트이고, 모든 hit이 진짜 / 오탐 / 사람 확인 필요로 분류되고 한 줄 이유가 붙습니다.

뻔한 것들 (commit에 박힌 secret, 문자열 concatenation으로 만든 SQL, 신뢰 못 할 input에 `eval` / `exec` / `pickle.loads`), 덜 뻔한 것들 (파일 read에 user-controlled path, HTML에 escape 안 된 input, `httpOnly` / `Secure` 빠진 cookie, wildcard CORS), 사람들이 잊어버리는 것들 (git history에 남은 `.env`, `.pem`, SSH key)을 봅니다. 심각도는 평범한 말로 표시합니다 — "CWE-89"보다 *"모르는 사람이 모든 유저 데이터를 읽을 수 있음"* 쪽입니다.

penetration test를 대체하진 않습니다. static sweep이에요 — network도, 실행 중인 system도 안 봅니다. 그리고 부끄러운 걸 *"괜찮아 보이네요"* 뒤에 숨기지 않습니다.

### 3. `fight-repo-rot`

먼저 dead-code detector, 두 번째로 잡동사니 탐지기, 그리고 항상 순수 진단입니다. 아무도 부르지 않는 함수, 아무도 import 안 하는 파일, 고아 module, consumer 없는 export, manifest엔 있지만 import 안 되는 의존성 — 이것들이 본래 잡으려고 만든 것들입니다. 그 위에 흔한 악취들도 플래그합니다: god file, god function, hardcode된 절대경로, IP 리터럴, 6개월 넘은 `TODO` / `FIXME` / `HACK`, *"다음에 가장 물릴 가능성 높은"* 파일들 (자주 바뀌고 *동시에* 복잡한 것들), 그리고 테스트 rot (죽은 테스트, 낡은 fixture, 고아 snapshot).

dead-code 후보는 모두 confidence 태그가 붙어서 돌아옵니다:

- **HIGH** — 어디서도 참조 없음 (grep, LSP, import graph, test, config 파일). 삭제는 `refactor-verify`에 넘기면 안전.
- **MEDIUM** — test에서만 참조되거나, 언어가 dynamic dispatch (Python, Ruby, 느슨한 JS)를 씀. 삭제 전 사용자 확인.
- **LOW** — export된 symbol, 생성 코드, reflection / DI / annotation 엮임. 반드시 사람이 봐야 함 — 자동 hand-off 금지.

이 skill은 일부러 손이 없습니다: 수정도, 삭제도, verification도 안 합니다. 각 항목 옆에 증거를 붙여 문제를 드러내고, 삭제와 split은 `refactor-verify`로, hardcode된 경로는 `project-conventions`로, CVE 의존성은 `audit-security`로 hand-off합니다. 리스트를 승인하기 전까진 아무것도 안 건드립니다.

### 4. `write-for-ai`

대부분의 문서는 한 번 훑고 지나가는 사람 독자를 위해 쓰여 있습니다. AI는 다르게 읽습니다: 매 session마다 새로 parse하고, 산문보다 표를 선호하고, backtick으로 감싼 명시적 파일 경로를 따라가고, *"절대 X 하지 마라"*가 스토리에 묻히는 대신 선언적으로 적혀 있어야 합니다. `write-for-ai`는 그 독자를 위해 씁니다 — 그리고 이렇게 쓴 문서는 사람한테도 더 잘 먹힙니다. 구조는 구조니까요.

쓸 대상을 주면 — README, commit, PR description, architecture doc, `CLAUDE.md`, `AGENTS.md` — 새 AI session이 그러듯 repo를 처음부터 읽습니다. 그다음 invariant를 뽑습니다: 이 프로젝트가 *뭘* 하는지만이 아니라, 어떤 규칙을 따르는지. 해당 템플릿을 채우고, 중요하게는 쓰기 전에 모든 주장을 검증합니다. README에 `pnpm test`가 suite를 돌린다고 쓰려면, skill이 먼저 `pnpm test`를 돌려봅니다.

그리고 한 가지 더 — 이번 버전에서 새로 들어간 원칙: **과장하지 않기, 근거 없이 팔지 않기**. *"fast"*, *"robust"*, *"production-ready"*, *"best-in-class"* 같은 마케팅 단어는 벤치마크나 실제 사례가 붙어 있을 때만 쓰고, 없으면 지웁니다. 능력 주장에는 검증 명령어가 함께 따라갑니다. 모호한 수치("대략 몇백 명")는 정확한 숫자로 바꾸거나 지웁니다.

이게 막는 시나리오: AI한테 README를 다시 써달라고 했더니 잘 썼어요. 근데 환경변수 얘기하던 문단이 조용히 사라져 있습니다. 원래 뭐가 있었는지 기억 못 하니까 알아채지 못 해요. 다음 AI session은 새 README에서 시작하니까 env 구조가 있는 줄도 모릅니다.

### 5. `setup-ci`

CI는 이 plugin에서 가장 큰 생산성 잠금해제입니다 — 제대로 세팅되면 *deploy*는 더 이상 생각할 일이 아니라 그냥 `git push`가 됩니다. 문제는 *제대로 세팅*하는 데서 개발자 아닌 분들이 대부분 포기한다는 거예요.

이 skill은 개념부터 말로 풀어줍니다 — runner가 뭔지, Secrets가 뭔지, `concurrency` group이 왜 필요한지, deploy 후 health check이 왜 필요한지. 그다음 `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod`에서 stack을 감지하고, 맞는 test·lint 명령을 고르고, 동작하는 workflow 두 개를 생성합니다. `test.yml`은 모든 push와 PR에서 test와 lint를 timeout 명시해서 돌리고, `deploy.yml`은 성공 시 host에 맞는 패턴 — SSH, Vercel, Fly.io, Cloud Run, Netlify — 으로 deploy합니다. concurrency guard, SSH key 정리, deploy 후 health check 포함해서요.

의도적으로 안 하는 두 가지: Secrets를 대신 추가하지 않습니다 (Secrets는 GitHub UI에 두는 거고, skill은 어떤 이름·어떤 값이 필요한지만 알려주지 credential 자체를 만지지 않습니다). 그리고 host를 추측하지 않습니다.

### 6. `manage-secrets-env`

secret은 "이 값 어디에 둬야 하지?"라는 질문 중에서 판돈이 제일 큰 조각입니다 — 잘못 두면 사건이 되지, 스타일 선호의 문제가 아닙니다. `manage-secrets-env`는 그 조각을 전담합니다: 네 개의 bucket 결정 트리 (소스 상수 / env var / 로컬 `.env` / CI secret store), `.env.example` ↔ `.env` drift check, 기본 안전한 `.gitignore` 템플릿, 그리고 secret의 전체 lifecycle (추가 / 업데이트 / 로테이션 / 제거 / bucket 간 이동 / drift audit / 새 환경 provision).

기본값 짧은 버전: 런타임에 안 바뀌는 상수는 코드에, 로컬 전용 secret은 committed `.env.example`과 함께 `.env`에, production secret은 CI provider의 secret store에, 환경별 runtime 값은 환경변수로, `.gitignore`는 secret 모양의 항목이 전부 미리 채워진 채로 출발합니다.

새 프로젝트면 `.env.example`, `.gitignore`, startup validation을 scaffold합니다. 기존 프로젝트면 현재 상태를 audit하고, 이미 tracked된 secret 파일은 사건급 finding으로 플래그하고, 이미 새는 상황이면 `audit-security`에 넘깁니다.

### 7. `project-conventions`

`manage-secrets-env`의 낮은 판돈 쪽 파트너입니다. 모든 프로젝트에는 secret과 무관한 구조적 결정들이 있습니다: main이냐 dev 브랜치냐, dep을 pin할 거냐 떠 있는 채로 둘 거냐, domain 기준 폴더 레이아웃이냐 type 기준이냐, 소스에 절대경로 버그가 슬쩍 들어가는 걸 어떻게 막을 거냐. 대부분은 95% 프로젝트에 맞는 답이 하나씩 있고, 그걸 고르는 데 한 session을 쓰는 건 낭비입니다.

기본값: GitHub Flow (`main` + 단기 feature 브랜치, `dev` 없음), production dep은 정확히 pin하고 lockfile commit, Dependabot 또는 Renovate를 월 단위 주기로, domain 중심 디렉터리 레이아웃, 소스에 절대경로 없음. 모든 규칙에 한 문장 이유가 붙어 있습니다.

새 프로젝트면 `dependabot.yml`과 브랜치 전략 노트를 scaffold합니다. 기존 프로젝트면 브랜치 일탈, unpinned dependency, 디렉터리 냄새, hardcode된 경로를 audit하고, 여러 파일 건드리는 수정은 `refactor-verify`에 넘겨서 verification pass 없이는 아무것도 다시 안 써지게 합니다.

### 8. `manage-assets`

bloat 탐지기지, 코드 분석기가 아닙니다. repo가 느려지는 이유는 코드가 아니라 binary입니다 — 작년에 누가 올린 300 MB SQLite, `.gitignore` 피해서 들어온 `dist/` 디렉터리, LFS에 들어갔어야 할 `.psd` 파일. `manage-assets`는 그 무게를 드러냅니다: working tree 파일 크기, git history의 blob 크기 (안 보이는 쪽), LFS 마이그레이션 후보, 자산 디렉터리 증가, 중복 binary.

이 skill은 **진단 전용**입니다. 파일을 지우지도, history를 다시 쓰지도, `git filter-repo`나 `git lfs migrate`를 돌리지도 않습니다. 사용자가 제거를 승인하면, 파괴적인 작업은 `refactor-verify`에 넘어가고 (history 다시 쓰기 같은 destructive op의 verification을 담당), `.gitignore` 문제는 `manage-secrets-env`로, 참조도 없는 자산은 `fight-repo-rot`로 갑니다.

오픈소스 공개 직전에 특히 궁합이 좋습니다 — 느린 연결에서의 첫 clone은 repo가 얼마나 무거워졌는지 솔직하게 말해주는 측정기입니다.

### 9. `unify-design`

모든 vibe-coding 프로젝트가 결국 필요해지지만 매번 나중으로 미뤄지는 그거에 대한 웹 스킬: 디자인 시스템 하나, 일관된 참조, drift 없음. 대부분 프로젝트는 primary blue가 세 개, Button 구현이 두 개, padding이 조금씩 다른 게 다섯 개, 로고가 여섯 개 파일에 raw `<img>`로 붙어 있고, 두 페이지의 네비게이션이 서로 다릅니다. 하나씩 보면 눈에 안 띄는데, 처음 방문한 사람 눈에는 즉시 보입니다.

`unify-design`은 프로젝트의 BI (브랜드 아이덴티티) — 색상, 간격, 타이포그래피, radius, shadow, breakpoint, 그리고 모든 페이지에 나오는 핵심 component들 — 을 단일 source of truth로 취급하고, 거기서 벗어난 것들을 찾아서 token 참조로 다시 씁니다. 프레임워크를 자동으로 감지합니다 (Tailwind v3와 v4, CSS Modules, styled-components, Emotion, Material UI, Chakra UI, custom property 쓰는 vanilla CSS) — 프로젝트가 쓰는 관용구를 그대로 씁니다. 외래 패턴을 끌고 오지 않아요.

세 가지를 합니다. 첫째, source of truth를 만듭니다: tokens 파일이 없으면 opinionated 기본값 (spacing scale, typography scale, radius scale)과 함께 scaffold하고, 짐작할 수 없는 두 값 — primary color와 display font — 만 사용자에게 물어봅니다. 둘째, drift를 audit합니다 — tokens 파일 밖의 hardcode된 hex, `w-[432px]` 같은 Tailwind arbitrary value, inline style 객체, 중복 Button/Card/Nav/Logo component, 명백히 복사·붙여넣기 실수로 생긴 near-match 색상. 셋째, drift를 고칩니다: 작은 교체는 바로 적용하고, 여러 파일 건드리는 refactor는 `refactor-verify`에 넘겨서 token rename이나 component 통합이 call-site 검증을 거치게 합니다.

의도적으로 안 하는 두 가지: 프로젝트에 BI 자체가 없을 때 브랜드를 지어내지 않습니다 (묻습니다). 그리고 프레임워크를 바꿔 쓰지 않습니다 — styled-components 프로젝트면 theme 객체를 쓰고, Tailwind로 이사시키지 않습니다.

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
