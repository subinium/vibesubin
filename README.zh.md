# vibesubin

一套便携的 skill 插件,教你的 AI 助手按我期待的方式重构、审计和部署代码 —— 还能用一句 `/vibesubin` 把所有 skill 一次跑完。

它是给那些用 AI 做真东西、但没受过开发训练的人准备的。这些是我自己带着 AI 写代码时的习惯,打包成 skill,让你的助手不用你唠叨就能照着做。

同一份 `SKILL.md` 可以在 **Claude Code**、**Codex CLI**,以及 **[skills.sh](https://skills.sh) 支持的任何 agent** 里直接用 —— Cursor、Copilot、Cline 等等。写一次,所有宿主都能识别。

> [English](./README.md) · [한국어](./README.ko.md) · [日本語](./README.ja.md)

---

## 快速开始

装好 [Claude Code](https://code.claude.com),然后运行:

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

打开一个仓库,输入 `/vibesubin`。所有 skill 会并行地扫一遍你的代码,只读,最后合成一份带优先级的报告 —— 你不点头,什么都不会改。想让某个 skill 真的*动手*干活?直接点名调用(`/refactor-verify`、`/setup-ci` 等等),它就会直接改你的文件。

用 Codex CLI、Cursor、Copilot 或 Cline?跳到 [安装](#安装)。

---

## vibesubin 是什么,不是什么

一小束 AI skill —— 也就是 `SKILL.md` 文件 —— 只要你的请求对上了,agent 会自动拾起对应的那个。直接用大白话说你想干嘛(*"把这个文件安全地拆了"*、*"有没有东西在漏"*、*"给我配个 deploy"*),对的 skill 会自己跑起来。

所有 skill 共享同一条规矩:**拿不出证据,就不许说"完成"。** 重构得四轮独立检查都确认没漏、没串、没接错,才算完 —— 不是 AI 重写完文件就算完。安全扫描是一份带文件路径和行号的分类清单,不是凭感觉写的一段话。

它不是 SaaS(没有任何东西离开你的机器)、不是合规工具(不管 SOC 2 / HIPAA)、也不是代码生成器。它只改善你已经有的那个仓库。

### 两种用法 —— sweep vs. 直接点名

- **Sweep 模式(`/vibesubin`)。** 所有代码卫生 skill 并行跑,*只读*。你拿到一份带优先级的报告;不点头,什么都不会动。
- **直接点名(`/refactor-verify`、`/setup-ci`……)。** skill 把它的完整活干完,包括直接改文件。
- **流程 skill(`/ship-cycle`)** 和 **特定宿主 wrapper(`/codex-fix`)** 只能直接点名 —— 它们不参与 sweep,因为它们会动外部系统(GitHub、Codex)或管发布状态。

有三个 skill(`fight-repo-rot`、`audit-security`、`manage-assets`)不管你怎么调都是**纯诊断**,永远不会编辑文件。

### 按领域分的阵容

**代码质量(5 个)**

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`refactor-verify`](#refactor-verify) | *"给这个类改名"*、*"拆掉这个文件"*、*"安全地删掉这段死代码"* | 一次带计划的重构,四轮验证通过之后才敢说完成 |
| [`audit-security`](#audit-security) | *"有没有密钥泄露"*、*"这样安全吗"* | 一份筛过的真实问题清单,带文件和行号 —— 不是 500 页 PDF |
| [`fight-repo-rot`](#fight-repo-rot) | *"找出死代码"*、*"哪些可以删"* | 死代码标 HIGH / MEDIUM / LOW 置信度,加上巨型文件和热点。纯诊断 |
| [`manage-assets`](#manage-assets) | *"我的 repo 太大了"*、*"要不要用 LFS"* | 臃肿报告 —— 大文件、git 历史里的大 blob、LFS 候选。从不重写历史 |
| [`unify-design`](#unify-design) | *"把按钮统一一下"*、*"把这些颜色抽成 token"* | 设计系统审计 —— 搭 tokens、找出硬编码的 hex 和魔法 px、合并重复组件 |

**文档与 AI 友好(2 个)**

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`write-for-ai`](#write-for-ai) | *"写个 README / commit / PR"* | 能让*下一个* AI session 真正读懂的文档 —— 没有没根据的夸张形容词 |
| [`project-conventions`](#project-conventions) | *"main 还是 dev 分支"*、*"这个依赖要不要锁"* | 每个决定一个默认值 —— GitHub Flow、锁版本的依赖、按领域划分目录 |

**基础设施与配置(2 个)**

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`setup-ci`](#setup-ci) | *"配个 deploy"*、*"push 就上线"* | 能跑的 GitHub Actions workflow,外加一份人话解说 |
| [`manage-secrets-env`](#manage-secrets-env) | *"这个密钥应该放哪"*、*"`.env` 是不是在漏"* | 一个有主见的答案加完整的密钥生命周期 |

**发布流程(1 个)**

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`ship-cycle`](#ship-cycle) | *"规划发布"*、*"用 issue 驱动开发"*、*"打个版本"* | 以 issue 驱动的发布编排器 —— 起草多语言 issue、聚合成与版本对应的 milestone、分派给对应 worker、聚合 CHANGELOG、打 tag 创建 release。**两条轨道** —— GitHub(默认)或非 GitHub 宿主上的 PRD on disk |

**特定宿主 wrapper(1 个)**

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`codex-fix`](#codex-fix) | *"用 codex 跑一遍再修"*、*"run codex and fix"* | 薄壳:`/codex:rescue` → `refactor-verify` 的 review-driven fix mode。**只在 Claude Code 加 Codex 插件**;其他宿主下一行 fallback |

新 skill 扔进 `plugins/vibesubin/skills/`,`/vibesubin` 就会自动捡起来。

---

## `/vibesubin` 命令

一个词,把所有代码卫生 skill 并行扫一遍你的仓库,合成一份带优先级的报告,动手之前先等你点头。

出发前可以缩小范围(*"只看 src/api"*、*"只跑 security 和 repo rot"*)。sweep 模式下所有专项都是只读的 —— 它们产出发现,不产出修复。critical 不管属于哪个类别都会浮到最上面;如果多个专项独立地标了同一个文件,这个文件的优先级会往上跳。你最后拿到一段 vibe check 开场、每个专项一行红绿灯、一份 top 10 修复清单、一个推荐顺序,和一句结论。完整合成规则在 [umbrella 的 `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md) 里。

**全扫 vs 单 skill。** 面对开放性问题就全扫(*"能上线了吗"*、*"给我个第二意见"*)。已经知道要什么就直接点名(*"重构这个文件"* → `/refactor-verify`)。密钥已经泄露就直接走 `/audit-security` 的事件路径,跳过 sweep。

**严厉模式。** 可选的直白语气 —— `/vibesubin harsh`、*"严厉模式"*、*"说狠一点"*、*"别嘴软"*、*"매운 맛으로"*、*"厳しめで"*。还是只读,证据还是那些证据,把含糊其辞都扔掉。永远不会默认严厉。

**外行模式。** 可选的大白话翻译 —— `/vibesubin explain`、`/vibesubin easy`、*"用通俗的话解释"*、*"给外行看的版本"*、*"쉽게 설명해줘"*、*"non-technical"*。每条 finding 都会给出一个三维度小框:**为什么要做 / 为什么重要 / 具体做什么**,严重程度会翻译成紧迫感(CRITICAL → *"现在立刻"*)。能叠加严厉模式。详见 [`references/layperson-translation.md`](./plugins/vibesubin/skills/vibesubin/references/layperson-translation.md)。

**Skill 冲突。** 当两个专项对同一个文件给出相反建议(比如 *refactor-verify* 说"先停一下",而 *unify-design* 说"该合并了"),报告里会浮出一个 `⚠ Skill conflict` 块,列出分歧点、原因,以及双方各自的依据 —— 由操作者来决定。目录放在 [`references/skill-conflicts.md`](./plugins/vibesubin/skills/vibesubin/references/skill-conflicts.md)。

---

## 安装

| 路径 | Agent | 适合场景 |
|---|---|---|
| **A. Claude Code marketplace** | Claude Code | 最简单,自动更新 |
| **B. `skills.sh`** | Cursor、Copilot、Cline、Codex CLI、Claude Code | 跨 agent |
| **C. 手动 symlink** | Claude Code 和/或 Codex CLI | 想改插件本身 |

**A —— Claude Code marketplace**(推荐)

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

用 `/plugin marketplace update` 更新。用 `/plugin uninstall vibesubin` 卸载。

**B —— skills.sh**(跨 agent,由 [skills.sh](https://skills.sh) 驱动)

```bash
npx skills add subinium/vibesubin
```

重跑同样的命令就能更新。用 `npx skills remove vibesubin` 移除。支持的宿主列表见 `npx skills --help`。

**C —— 手动 symlink**(可编辑、离线、`git pull` 立刻生效)

```bash
git clone https://github.com/subinium/vibesubin.git
cd vibesubin
bash install.sh                  # Claude Code(默认)
bash install.sh --to codex       # Codex CLI
bash install.sh --to all         # 两个都装
bash install.sh --dry-run        # 预览
```

`git pull` 就是更新。用 `bash uninstall.sh [--to codex|all]` 卸载 —— 只会移除脚本自己建的 symlink。

装不上?把所有 agent session 关掉再开一个新的(skill 是按 session 缓存的)。其他问题,[开 issue](https://github.com/subinium/vibesubin/issues)。

---

## Skill 列表

每个 skill 都在 [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/) 下。下面是面向用户的说明;完整的方法论在每个 skill 的 `SKILL.md` 里,更深入的参考放在同级的 `references/` 目录。

### 代码质量

#### `refactor-verify`

这是我最愿意拼命为它辩护的一个 skill。AI 改代码最大的失败模式是"沉默型"的 —— 重命名成功、测试通过,三周后有人碰到一处还指向老名字的代码路径,整个东西就炸了。`refactor-verify` 就是专门让这种沉默失败变得不可能。

管两类改动 —— 结构性重构(move、rename、split、merge、extract、inline)和安全删除(删 `fight-repo-rot` 确认过的死代码)。两者走同一套四重验证:符号集保持不变、被移代码逐字节等价、typecheck / lint / 测试 / 冒烟通通重跑、沿着整个 import graph 对所有受影响符号做调用方审计。四个里任何一个挂了,skill 都不会往下走。它不会碰你没让它碰的文件、不会在有检查失败时说"完成"、也不会在没经过人工复核的情况下删掉 LOW 置信度的死代码。

#### `audit-security`

企业级扫描器一口气标出 500 条,其中 490 条是误报。`audit-security` 是反过来的形状:一份短的、手工筛选过的模式集合,专门抓人会真犯的错;每一条命中都被分类 —— 真问题、误报、需人工复核 —— 并附一句话理由。

查明显的(commit 里的密钥、字符串拼接的 SQL、`eval` / `exec` / `pickle.loads`),也查不那么明显的(用户可控路径、HTML 里未转义的输入、缺 `httpOnly` / `Secure` 的 cookie、通配符 CORS),还有那些总被忘掉的(git 历史里的 `.env`、`.pem`、SSH key)。严重程度用大白话描述 —— *"陌生人能读到每个用户的数据"* 比 *"CWE-89"* 好用得多。不是渗透测试,只做静态扫描,不联网。

#### `fight-repo-rot`

首先是死代码检测器,其次是杂物扫描器,始终是纯诊断。没人调用的函数、没人 import 的文件、孤儿模块、manifest 里声明却从未被 import 的依赖。在此之上也标巨型文件、热点(改得多*又*复杂的)、硬编码的绝对路径、字面 IP、超过半年的 `TODO` / `FIXME`。

每一条死代码候选都带置信度:**HIGH**(哪里都查不到引用 —— 可以安全交给 `refactor-verify` 删除)、**MEDIUM**(只被测试引用或涉及动态派发 —— 需要你确认)、**LOW**(导出符号、生成代码、反射 / DI —— 必须人工复核)。从不编辑、从不删除。删除交给 `refactor-verify`,硬编码路径修复交给 `project-conventions`,依赖 CVE 类问题交给 `audit-security`。

#### `manage-assets`

臃肿检测器,不是代码分析器。把二进制重量摆到台面上来:工作区文件大小、git 历史 blob 大小(看不见的那部分)、LFS 迁移候选、资源目录增长、重复的二进制文件。**只诊断** —— 从不删除、从不重写历史、从不跑 `git filter-repo` 或 `git lfs migrate`。批准的移除交给 `refactor-verify`(负责带验证的历史重写)、`manage-secrets-env`(如果跟 `.gitignore` 相关),或 `fight-repo-rot`(如果资源也没人引用)。

#### `unify-design`

前端的设计系统一致性 —— tokens 加重复审计。把品牌标识(颜色、间距、排版、radius、阴影、断点、核心组件)当作唯一 source of truth,把所有漂移都重写成引用 token。自动识别框架(Tailwind v3 / v4、CSS Modules、styled-components、Emotion、MUI、Chakra、vanilla CSS),用项目本来的习惯写法,而不是从外面搬新模式。

做三件事:如果没有 tokens 文件就搭一个(会问你主色和展示字体),审计漂移(硬编码 hex、像 `w-[432px]` 的 Tailwind arbitrary value、内联 style 对象、重复的 Button / Card / Nav),修掉漂移(小改动直接应用,跨多文件的合并交给 `refactor-verify`)。不会凭空编品牌,也不会跨框架迁移。

### 文档与 AI 友好

#### `write-for-ai`

文档同时写给*下一个* AI session 和人类。像一个全新的 AI session 那样冷读仓库,抽出不变量(不只是项目做什么,还有它遵守哪些规矩),套进对应模板(README、commit、PR description、架构文档、`CLAUDE.md`、`AGENTS.md`),在写下去之前核对每一条声明 —— 如果 README 说 `pnpm test` 能跑测试,skill 会先去跑一遍 `pnpm test`。

防住这种经典失败:你让 AI 重写 README,它写得挺好,只是关于环境变量的那一段悄悄消失了。你没发现,下一个 session 从新的 README 开始,对你的 env 布局一无所知。

#### `project-conventions`

低赌注的结构性默认:分支策略、依赖锁版本、目录布局、绝对路径卫生。默认值 —— GitHub Flow(`main` 加短寿命 feature 分支,不要 `dev`)、生产依赖严格锁版本加提交的 lockfile、Dependabot / Renovate 按月跑、按领域划分目录、源码里不留绝对路径。每条规则都配一句理由。

新项目里搭 `dependabot.yml` 和分支策略说明。已有项目里审计偏离,把跨文件的修复交给 `refactor-verify`。

### 基础设施与配置

#### `setup-ci`

CI 是这个 pack 里最大的生产力解锁 —— 一旦配好,deploy 就不再是一件要"想"的事,它就是 `git push`。先用大白话解释概念(runner、Secrets、`concurrency` 组、部署后健康检查),从 `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` 识别你的技术栈,搭出两个 workflow:`test.yml`(测试加 lint,带明确超时)和 `deploy.yml`(按宿主匹配 —— SSH、Vercel、Fly.io、Cloud Run、Netlify —— 带并发保护、SSH key 清理、健康检查)。

不替你添加 Secrets(Secrets 活在 GitHub UI 里),不会猜你的宿主。

#### `manage-secrets-env`

"这个值该放哪" 里赌注最大的那一片 —— 放错地方不是风格偏好,是事故。四桶决策树(源代码常量 / 环境变量 / 本地 `.env` / CI 密钥仓库)、`.env.example` ↔ `.env` 漂移检查、默认安全的 `.gitignore` 模板、完整生命周期(添加 / 更新 / 轮换 / 移除 / 迁移 / 审计 / 新环境配置)。

默认值:运行时永远不变的常量放在代码里;本地密钥放 `.env`,配一个提交进库的 `.env.example`;生产密钥放 CI 密钥仓库;随环境变化的运行时值用环境变量;`.gitignore` 开箱就带好所有密钥形状的条目。已有项目里审计现状,把已被 track 的密钥文件标为事件级 finding,已经在漏就交给 `audit-security`。

### 发布流程

#### `ship-cycle`

pack 里唯一的 **流程分类** skill。作用于代码外围的生命周期 —— issue、milestone、version、tag、release、changelog。跑的循环是:intake → draft → cluster → confirm → create → branch → execute → release。issue 正文双语(韩 / 英 / 日 / 中),semver 决策树(bug / perf / refactor → patch,新增 feat → minor,破坏性 → major),每个 patch 上限约 5 条。

**两条轨道。** **GitHub 轨道**(默认)走 `gh` API —— issue、milestone、PR、release 都活在 GitHub 上;`Closes #<N>` footer 合并时自动关 issue。**PRD 轨道**(任意其他宿主)走 `docs/release-cycle/vX.Y.Z/` 下的本地 markdown 文件 —— 同一套方法论、同一套规范,只是换了个持久的审计载体。操作者在 Step 1.5 挑。**规范是强制的**,见 [`references/pr-branch-conventions.md`](./plugins/vibesubin/skills/ship-cycle/references/pr-branch-conventions.md):GitHub Flow 分支命名(`<type>/<issue-N>-<slug>`)、Conventional Commits 加必填的 `Closes #<N>` footer、含六个必填章节(Context / What changed / Test plan / Docs plan / Risk / Handoff notes)的 PR 模板、rebase-first 合并加 `--force-with-lease`、禁止向 `main` / `master` / `release/*` 强推。

不会跳过你对起草 issue 的审批,不会在 main 上 CI 没绿的情况下 push tag,不会把不相关的 item 塞进同一个 milestone。

### 特定宿主 wrapper

#### `codex-fix`

为一个特定工作流服务的薄壳(约 100 行):*"我这一轮编辑结束了。用 Codex 跑一遍 second-model review。让 Claude 带验证地解决。"* 在当前分支 diff 上跑 `/codex:rescue`,把 findings 交给 `refactor-verify` 的 review-driven fix mode。

**只在 Claude Code 加 Codex 插件** 下运行。其他宿主下只输出一行 *"未检测到 Codex 插件 —— 请直接把 findings 交给 `/refactor-verify`。"* 然后干净退出。

Claude Code 加 Codex *且* review 来源就是 Codex 的时候用 `/codex-fix`。其他任何来源(人工 PR review、Sentry、`gitleaks`、Semgrep、粘贴的笔记)直接调 `/refactor-verify` —— 引擎一样,只是输入路径不同。符合 [`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md) 第 9 条的 "可移植引擎加薄壳" 模式。

---

## 日常怎么用

三种调用方式,按你知道的程度排序。

不知道从哪下手?敲 `/vibesubin`,它把所有东西都跑一遍。知道哪里不对劲?用大白话说出来 —— *"清一下,别搞坏"* 会触发 `refactor-verify`,*"有没有密钥泄露"* 触发 `audit-security`,*"我应该先修什么"* 触发 `fight-repo-rot`,诸如此类。已经明确知道要哪个 skill?直接点名:`/refactor-verify`、`/audit-security` 等等。

每个 skill 都遵循同一个四段式输出:做了什么、发现了什么、验证了什么、你接下来该做什么。如果某个 skill 回给你一大段没这四段的散文,那是 bug,[开 issue](https://github.com/subinium/vibesubin/issues)。

### 常见组合

- **清理一个仓库。** `fight-repo-rot` 找出最大的祸害 → `refactor-verify` 带验证修掉 → `write-for-ai` 写 commit 和 PR。
- **准备发版。** `audit-security` 查密钥 → `refactor-verify` 修关键问题 → `setup-ci` 下次自动拦住回归。
- **上手一个陌生仓库。** `/vibesubin` 全扫一遍 → `write-for-ai` 补上缺失的 `CLAUDE.md` → `manage-secrets-env` 审计 `.gitignore` 和密钥 → `project-conventions` 审计分支、依赖和目录。
- **从零开始。** `manage-secrets-env` 搭 `.env.example` 和 `.gitignore` → `project-conventions` 搭 Dependabot 和分支说明 → `setup-ci` 铺 workflow → `write-for-ai` 写 README 和 `CLAUDE.md`。
- **"我的 repo 怎么这么大?"** `manage-assets` 出臃肿报告 → `refactor-verify` 带验证执行历史重写或 LFS 迁移。
- **"每一页看起来都有点不一样。"** `unify-design` 搭 tokens(如果没有)、审计漂移、把组件改写成引用 token → `refactor-verify` 处理跨多文件的合并。
- **"编辑都结束了,用 Codex 跑一遍收尾"(只限 Claude Code 加 Codex 插件)。** `codex-fix` 在当前分支跑 `/codex:rescue` → 把 findings 交给 `refactor-verify` 的 review-driven fix mode → 分类、验证、带 back-reference 的 commit。在其他宿主,或 review 来源不是 Codex(PR review、Sentry、扫描器、粘贴的笔记),直接把 findings 交给 `/refactor-verify` —— 引擎一样,只是输入路径不同。
- **规划一个发布(Claude Code + GitHub + `gh` 专属)。** 一批改动累积好了,或 `/vibesubin` sweep 给出了优先修复列表 → `ship-cycle` 从列表起草多语言 issue → 聚合成对应下一个 semver 版本的 milestone → 按 label 把每个 issue 分派给对应 worker,带验证执行 → milestone 关闭时,从已关闭 issue 聚合出功能型 changelog,bump 两个 manifest,打 annotated tag,创建 GitHub release。非 GitHub 宿主或 `gh` 未认证时 `ship-cycle` 以一行 fallback 退出 —— 此时直接调下层 worker。

这些组合你自己不用规划 —— 合适的时候 skill 会主动建议下一步交给谁。

---

## 加一个你自己的 skill

一个新 skill 就是 `plugins/vibesubin/skills/<skill-name>/` 下的一个自包含目录。扔进去,重启 agent,`/vibesubin` 和自动补全菜单都会自动认出它。

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # 必需,500 行以内,带 YAML frontmatter
├── references/           # 可选,深入参考文档
├── scripts/              # 可选,可执行的辅助脚本
└── templates/            # 可选,skill 往项目里复制的文件
```

新 skill 继承的规矩:*完成*意味着已验证(不是嘴上说的);`SKILL.md` 保持在 500 行以内,深度内容写进 `references/`;输出遵循四段式;任何可参与 sweep 的 skill 都要有只读模式;每个 skill 都得清楚声明自己的置信度边界在哪。

想让某个 skill 进主插件?[开 issue](https://github.com/subinium/vibesubin/issues),附上触发词、它会做什么,和一个具体的例子。见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

---

## 哲学

所有 skill 都绕着几条规矩打转。你不用背下来 —— 它们存在的意义是让现在和未来的 skill 保持一致。

**你的 AI 是一个用心的初级工程师。** 初级工程师很努力,但有时候本该停下来问一句却一股脑往前冲了。这个插件在一个更老练的手会停下来的地方插入*"停一下、问一句"*的节点。

**完成是证出来的,不是说出来的。** 如果某件事说是完成,背后就有执行结果撑着 —— 一个通过的测试、一个对上的 hash、一个真实的 `200 OK`。没证据的断言就是 bug。

**文档是写给下一个 AI session 的,不只是写给人的。** 当前的对话在 session 结束时就蒸发了;README、commit、PR body 的写法要让一个全新的 session 能把上下文重建出来。

**既有约定就是默认。** 这个插件不会心血来潮地悄悄改掉你的分支策略、文件布局或配置。

插件在[持续维护中](./MAINTENANCE.md)。重构工具会演进,skill 系统会变,LLM 的失败模式也会变 —— 每个 skill 都按一个时间表定期复审。

---

## 贡献

开源,但目前不接受 PR。发现 bug、想加一门新语言或 runtime、觉得文档写得不清楚、有新 skill 的点子?[开 issue](https://github.com/subinium/vibesubin/issues)。维护者会直接复核并整合进来,这样语气能保持一致。详见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

---

## 许可证

MIT —— 见 [LICENSE](./LICENSE)。

---

历次改动记录在 [`CHANGELOG.md`](./CHANGELOG.md) 里。插件版本号在 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) 里。
