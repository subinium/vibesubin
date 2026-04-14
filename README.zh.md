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

打开一个仓库,输入 `/vibesubin`。所有 skill 会并行地扫一遍你的代码,只读,最后合成一份带优先级的报告。你不点头,什么都不会改。想让某个 skill 真的*动手*干活?直接点名调用(`/refactor-verify`、`/setup-ci` 等等),它就会直接改你的文件。

用 Codex CLI、Cursor、Copilot 或 Cline?跳到 [安装](#安装)。

---

## vibesubin 是什么,不是什么

一小束 AI skill —— 也就是 `SKILL.md` 文件 —— 只要你的请求对上了,agent 会自动拾起对应的那个。你不用背触发词。直接用大白话说你想干嘛 —— *"把这个文件安全地拆了"*、*"有没有东西在漏"*、*"给我配个 deploy"* —— 对的 skill 会自己跑起来。

所有 skill 共享同一条规矩:**拿不出证据,就不许说"完成"。** 重构不是 AI 重写完文件就算完 —— 得四轮独立检查都确认没漏、没串、没接错,才算完。安全扫描也不是靠感觉写一段话,而是一份分类过的清单:每一条要么是真问题、要么是误报、要么标上"需要人工复核",每条都带文件路径和行号。

它**不是**:不是 SaaS(没有任何东西离开你的机器)、不是合规工具(不管 SOC 2 / HIPAA)、也不是代码生成器。它只改善你已经有的那个仓库。

### 只读扫描 vs. 真正会编辑文件的 skill

这件事得早点搞清楚。这个插件有两种用法,行为完全不一样。

- **Sweep 模式(`/vibesubin`)。** 所有 skill 并行跑,*只读*。它们产出的是发现,不是修复。你不从报告里批准,仓库里一个字都不会动。这是"我想要一个诚实的第二意见"的模式。
- **直接点名(`/refactor-verify`、`/setup-ci`、`/write-for-ai`、`/manage-secrets-env`、`/project-conventions`、`/unify-design`)。** skill 把它的完整活干完,包括直接改文件。`refactor-verify` 会沿着依赖树重写你的代码。`setup-ci` 会把能跑的 YAML 扔进 `.github/workflows/`。`write-for-ai` 会动你的 README。`manage-secrets-env` 会搭出 `.env.example`、`.gitignore`,并跑完密钥的完整生命周期。`project-conventions` 会搭出 Dependabot、强制依赖锁版本、修掉硬编码路径。`unify-design` 会搭出 tokens 文件,把组件改写成引用 token 的形式。这些是"真的动手干"的模式。

有三个 skill 不管你怎么调都不会编辑文件:**`fight-repo-rot`**(纯诊断 —— 找死代码和气味,删除交给 `refactor-verify`)、**`audit-security`**(只产出静态筛选报告)和 **`manage-assets`**(只出臃肿报告 —— 从不重写历史、从不删文件)。其他的 —— `refactor-verify`、`setup-ci`、`write-for-ai`、`manage-secrets-env`、`project-conventions`、`unify-design` —— 直接点名调用时就是真正动手的 worker,被 sweep 拉进去时就切换成只读的汇报者。

### 当前阵容

| Skill | 你会说什么 | 你会拿到什么 |
|---|---|---|
| [`refactor-verify`](#1-refactor-verify) | *"给这个类改名"*、*"拆掉这个文件"*、*"安全地删掉这段死代码"* | 一次有计划的改动 —— 重构、重命名、拆分或删除 —— 自底向上执行,四轮验证通过之后才敢说完成 |
| [`audit-security`](#2-audit-security) | *"有没有密钥泄露"*、*"这样安全吗"* | 一份筛过的真实问题清单,带文件和行号 —— 而不是 500 页的 PDF |
| [`fight-repo-rot`](#3-fight-repo-rot) | *"找出死代码"*、*"哪些可以删"* | 死代码标 HIGH / MEDIUM / LOW 置信度,再附上巨型文件、热点、硬编码路径和测试腐败。纯诊断 —— 绝不动手改 |
| [`write-for-ai`](#4-write-for-ai) | *"写个 README / commit / PR"* | 能让*下一个* AI session 真正读懂的文档 —— 没有没根据的夸张形容词 |
| [`setup-ci`](#5-setup-ci) | *"配个 deploy"*、*"push 就上线"* | 能跑的 GitHub Actions workflow,外加一份人话解说 |
| [`manage-secrets-env`](#6-manage-secrets-env) | *"这个密钥应该放哪"*、*"`.env` 是不是在漏"* | 一个有主见的答案,附一句话的理由 + 密钥的完整生命周期 |
| [`project-conventions`](#7-project-conventions) | *"main 还是 dev 分支"*、*"这个依赖要不要锁"*、*"硬编码路径"* | 每个决定一个默认值 —— GitHub Flow、锁版本的依赖、按领域划分的目录、源码里不留家目录 |
| [`manage-assets`](#8-manage-assets) | *"我的 repo 太大了"*、*"要不要用 LFS"* | 臃肿报告 —— 大文件、git 历史里的大 blob、LFS 候选。纯诊断 —— 不重写历史 |
| [`unify-design`](#9-unify-design) | *"把按钮统一一下"*、*"这两页看起来不一样"*、*"把这些颜色抽成 token"* | 设计系统审计 —— 没有 tokens 文件就搭一个,把所有硬编码的 hex 和魔法 px 都找出来,合并重复组件 |

新 skill 扔进 `plugins/vibesubin/skills/`,`/vibesubin` 就会自动捡起来。

---

## `/vibesubin` 命令

一个词,把插件里所有 skill 并行扫一遍你的仓库,把结果合成一份报告,动手之前先等你点头。

流程是这样。skill 会一句话告诉你它打算干啥,给你一个缩小范围的机会(*"只看 src/api"*、*"只跑 security 和 repo rot"*),然后再出发。之后它把每个专项作为独立的 task agent 分发出去 —— 每次运行都是隔离的,agent 之间不会互相污染。这一轮所有专项都是只读的:它们产出发现,不产出修复。如果某个专项跑不起来 —— 比如测试套件根本起不来 —— 它会把这件事本身作为"发现"汇报,然后让开。一个挂掉的专项绝不会卡住整轮扫描。

结果回来以后,按合成规则合并。Critical 不管属于哪个类别都会浮到最上面(泄露的密钥 > 热点 > 缺文档字符串)。如果多个专项独立地标了同一个文件,这个文件的优先级会往上跳。发现按文件分组 —— 因为你是按文件修代码,不是按类别。每一条都带一个具体的建议动作。

你最后拿到一份 markdown 报告:一段 vibe check 开场、每个专项一行红绿灯、一份 top 10 修复清单、一个推荐的处理顺序,以及一句结论。如果一切正常,结论就直接说正常。你不批准,仓库里一个字都不会改。

完整的报告模板和合成规则在 [umbrella 的 `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md) 里。

**全扫 vs 单 skill。** 面对开放性问题就全扫:*"我刚接手这个仓库"*、*"这玩意能上线了吗"*、*"给我个第二意见"*。已经知道自己要什么就直接点名:*"重构这个文件"* → `/refactor-verify`。*"我把 `.env` push 上去了"* → `/audit-security`,紧急优先。*"写 README"* → `/write-for-ai`。

**严厉模式。** 默认情况下 sweep 的语气是平衡的 —— 诚实但不扎人。想让它严厉一点就明说:*"`/vibesubin harsh`"*、*"严厉模式"*、*"说狠一点"*、*"别嘴软"*、*"매운 맛으로"*、*"厳しめで"*。报告还是只读的,证据还是那些证据,但它会把含糊其辞的话都扔掉,把最糟的那条放到最前面,也不会在真问题还堆着的时候用一句 *"看起来还行"* 收尾。只在你主动要的时候才开 —— 永远不会默认严厉。

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

每个 skill 都在 [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/) 下。下面是面向用户的说明;完整的方法论在每个 skill 的 `SKILL.md` 里,更深入的参考放在同级的 `references/` 目录。你其实不用去读这些文件 —— AI 会读 —— 但它们都是开源的,好奇的话可以看看。

### 1. `refactor-verify`

这是我最愿意拼命为它辩护的一个 skill。AI 改代码最大的失败模式是"沉默型"的 —— 一个函数被挪了位置、重命名成功、测试通过,结果三周后有人碰到一处还指向老名字的代码路径,整个东西就炸了。`refactor-verify` 就是专门让这种沉默失败变得不可能。

它管两类改动 —— 结构性重构(move、rename、split、merge、extract、inline)和安全删除(删除 `fight-repo-rot` 确认过是死代码的部分)。两者走的是同一套四重验证。

动手之前,它先把当前状态拍个快照:有哪些函数、每个函数在哪个文件、此刻测试过不过、lint 怎么说。这就是*之前*的样子。然后它把整个改动拆成一棵依赖树,从叶子节点往上做,让你永远不会卡在半成品状态。

每一步之后,四个独立检查同时跑。一个走一遍符号集,确认所有原本存在的公共名称现在都还在(或者是被明确删掉的)。一个确认被移动或保留的代码逐字节还是原来的样子,忽略空白。一个重跑 typecheck、lint、测试和冒烟运行。第四个 —— 抓到最多真实 bug 的那个 —— 走一遍所有受影响符号的调用方,确认它们指向了正确的地方,或者在符号被删的情况下什么都不指。四个里任何一个挂了,skill 都不会往下走。

它绝不会做的一些事:碰你没让它碰的文件;在有检查失败的情况下说"完成";在测试套件根本起不来时编造一个结果;在 move 的过程中顺手重写函数体;在未经人工复核的情况下删掉 `fight-repo-rot` 标为 LOW 置信度的代码。

### 2. `audit-security`

企业级安全扫描器都有噪声问题。一口气标出五百条,其中四百九十条是误报 —— 一周之后大家就整个忽略掉了。真正的 critical 被淹没。`audit-security` 是反过来的形状:一份短的、手工筛选过的模式集合,专门抓人会真犯的错;每一条命中都被分类 —— 真问题、误报、还是需要人工复核 —— 并附一句话理由。

它查明显的(commit 里的密钥、字符串拼接的 SQL、用户输入喂给 `eval` / `exec` / `pickle.loads`),也查不那么明显的(用户可控路径的文件读取、HTML 里未转义的输入、缺 `httpOnly` / `Secure` 的 cookie、通配符 CORS),还有那些总被忘掉的(git 历史里的 `.env`、`.pem` 和 SSH key)。严重程度用大白话描述 —— *"陌生人能读到每个用户的数据"* 比 *"CWE-89"* 好用得多。

它不能代替渗透测试。它是静态扫描 —— 不联网、不跑系统。它也绝不会用一句 *"看起来没事"* 的总结把什么尴尬的东西藏起来。

### 3. `fight-repo-rot`

首先是一个死代码检测器,其次是杂物扫描器,始终是纯诊断。没人调用的函数、没人 import 的文件、孤儿模块、没有消费者的 export、manifest 里声明却从未被 import 的依赖 —— 这些才是它真正要找的。在此之上,它顺便也标出老一套气味:god file、god function、硬编码的绝对路径、字面 IP、超过半年的 `TODO` / `FIXME` / `HACK`,以及那些"最可能下次咬你一口"的文件(改得多*又*复杂的),还有测试腐败(死测试、过时的 fixture、孤儿快照)。

每一条死代码候选都带一个置信度标签:

- **HIGH** —— 各种手段都查不到引用(grep、LSP、import graph、测试、配置文件)。可以安全交给 `refactor-verify` 删除。
- **MEDIUM** —— 只被测试引用,或者语言本身动态派发(Python、Ruby、松散的 JS)。删之前得你确认。
- **LOW** —— 导出符号、生成代码、涉及反射 / DI / 注解。必须人工复核,永远不自动交接。

这个 skill 故意不动手:它从不编辑、从不删除、从不跑验证。它只把问题连证据一起摆出来,然后把删除和拆分交给 `refactor-verify`,把硬编码路径的修复交给 `project-conventions`,把依赖 CVE 类的问题交给 `audit-security`。清单你不批准,一个字都不会碰。

### 4. `write-for-ai`

大多数文档是写给人读的 —— 而人只会扫一眼。AI 的读法不一样:每个 session 它都从头 parse 一遍,更吃表格不是长段落,更吃 backtick 里显式的文件路径,更需要 *"不要做 X"* 被直接声明出来而不是埋在故事里。`write-for-ai` 就是写给那个读者的 —— 顺便出来的东西对人也更好用,因为结构就是结构。

你丢给它一个要写的东西 —— README、commit、PR description、架构文档、`CLAUDE.md`、`AGENTS.md` —— 它会先像一个全新的 AI session 那样把仓库从头读一遍。然后它抽出"不变量":不只是*这个项目做什么*,还有*它遵守哪些规矩*。它套进合适的模板,然后 —— 这是关键 —— 在写下去之前核对每一个声明。如果 README 说 `pnpm test` 能跑测试,它会先去跑一遍 `pnpm test`。

还多了一条 —— 这个版本新加的原则: **不夸大,不凭空推销**。像 *"fast"*、*"robust"*、*"production-ready"*、*"best-in-class"* 这种营销词,要么有基准测试或真实案例撑着,要么就删掉。能力声明得配一个验证命令。模糊数字("大概几百用户")要么换成具体数,要么删掉。

它防住的是这种情况:你让 AI 重写 README,它写得挺好,只是关于环境变量的那一段悄悄消失了。你也没发现,因为你不记得原来写了什么。下一个 AI session 从新的 README 开始,对你的 env 布局一无所知。

### 5. `setup-ci`

CI 是这个插件里最大的生产力解锁 —— 一旦配好,*deploy* 这件事就不再是一件你需要"想"的事,它就是 `git push`。问题是,"正确地配好" 是大多数非开发者放弃的地方。

这个 skill 先用大白话解释概念 —— 什么是 runner、Secrets 是什么、为什么需要 `concurrency` 组、为什么每次 deploy 之后要加一次健康检查。然后它从 `package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` 识别你的技术栈,挑对测试和 lint 命令,搭出两个能跑的 workflow。`test.yml` 在每次 push 和 PR 上跑测试和 lint,带明确的超时。`deploy.yml` 在测试通过时部署,用的是适配你宿主的模式 —— SSH、Vercel、Fly.io、Cloud Run、Netlify —— 加上并发保护、SSH key 清理,以及部署后的健康检查。

两件它故意不做的事:它不会替你添加 Secrets(Secrets 活在 GitHub UI 里 —— 它会告诉你需要哪些、每个装什么,但自己绝不碰凭证);它也不会猜你的宿主。

### 6. `manage-secrets-env`

密钥是"这个值该放哪"这类问题里赌注最大的那一片 —— 放错地方不是风格偏好,是事故。`manage-secrets-env` 专门负责这一片:四桶决策树(源代码常量 / 环境变量 / 本地 `.env` / CI 密钥仓库)、`.env.example` ↔ `.env` 漂移检查、默认安全的 `.gitignore` 模板,以及密钥的完整生命周期(添加 / 更新 / 轮换 / 移除 / 桶间迁移 / 跨环境漂移审计 / 新环境配置)。

最短版默认值:运行时永远不变的常量放在代码里;只在本地用的密钥放在 `.env`,配一个提交进库的 `.env.example`;生产密钥放在 CI 提供方的密钥仓库里;随环境变化的运行时值用环境变量;`.gitignore` 开箱就带好所有密钥形状的条目。

新项目里,它搭 `.env.example`、`.gitignore` 和启动时校验。已有项目里,它审计现状,把已被 track 的密钥文件标为事件级 finding,如果已经在漏,就交给 `audit-security`。

### 7. `project-conventions`

`manage-secrets-env` 的"低赌注"搭档。每个项目都有一些跟密钥无关的结构性决定:main 还是 dev 分支、依赖锁不锁版本、按领域还是按类型分目录、怎么阻止绝对路径偷偷混进源码。这些问题里绝大多数都有一个适合 95% 项目的答案,选它不值得耗掉一整个 session。

默认值:GitHub Flow(`main` 加短寿命 feature 分支,不要 `dev`),生产依赖严格锁版本,lockfile 提交进库,Dependabot 或 Renovate 按月跑,按领域划分目录,源码里不留绝对路径。每条规则都配一句理由。

新项目里,它搭 `dependabot.yml` 和一份分支策略说明。已有项目里,它审计偏离的分支策略、没锁的依赖、目录气味、硬编码路径,再把跨文件的修复交给 `refactor-verify`,保证没经过 verification pass,一个字都不会被重写。

### 8. `manage-assets`

臃肿检测器,不是代码分析器。仓库变慢的原因不是代码,是二进制 —— 去年某人 check-in 的 300 MB SQLite、溜进来没被 `.gitignore` 拦住的 `dist/` 目录、本来该进 LFS 的 `.psd`。`manage-assets` 把这些重量摆到台面上来:工作区内的文件大小、git 历史里的 blob 大小(看不见的那部分)、LFS 迁移候选、资源目录的增长、重复的二进制文件。

这个 skill 是**只诊断**的。它从不删除文件、从不重写历史、从不跑 `git filter-repo` 或 `git lfs migrate`。当你批准一个移除,破坏性操作会交给 `refactor-verify`(它负责像历史重写这类 destructive 操作的验证),`.gitignore` 相关的发现会交给 `manage-secrets-env`,如果资源同时也没人引用,会交给 `fight-repo-rot`。

它跟开源之前的准备特别搭 —— 慢网络下的第一次 clone 是一把诚实的尺子,量出你的仓库到底有多重。

### 9. `unify-design`

每个 vibe-coding 项目最后都需要、而每次都被搁到后面的一件事,给它一个专门的 Web skill:一个设计系统,被一致地引用,没有漂移。大多数项目出厂时带着三种略微不同的主蓝色、两种 Button 实现、五种微调过的 padding,logo 以原生 `<img>` 的形式粘在六个文件里,两个页面的导航栏对不上。单独看每个都不明显,第一次访问的人一眼就看出来了。

`unify-design` 把项目的 BI(品牌标识)—— 颜色、间距、排版、radius、阴影、断点,以及出现在每一页上的那些核心组件 —— 当作唯一的 source of truth,把所有漂移都重写成引用 token 的形式。它会自动识别框架(Tailwind v3 和 v4、CSS Modules、styled-components、Emotion、Material UI、Chakra UI、用自定义属性的 vanilla CSS),用项目本来的习惯写法,而不是从外面搬新的模式过来。

它做三件事。第一,确立 source of truth:如果没有 tokens 文件,就用一套有主见的默认值(spacing scale、typography scale、radius scale)搭一个,只把它猜不到的两个值 —— 主色和展示字体 —— 留给你来填。第二,审计漂移 —— tokens 文件之外硬编码的 hex、像 `w-[432px]` 这样的 Tailwind arbitrary value、内联 style 对象、重复的 Button / Card / Nav / Logo 组件、明显是复制粘贴失误才出现的 near-match 颜色。第三,修掉漂移:小改动直接应用,跨多文件的重构交给 `refactor-verify`,让 token 重命名或组件合并经过 call-site 验证。

它故意不做的两件事:当项目根本没有 BI 的时候,它不会凭空编一个(它会问你)。也不会跨框架迁移 —— 如果你在用 styled-components,它就用 theme 对象,而不是劝你换到 Tailwind。

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
- **"每一页看起来都有点不一样。"** `unify-design` 搭 tokens 文件(如果没有)、审计漂移、把组件改写成引用 token → `refactor-verify` 处理跨多文件的合并。

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

**文档要客观,不夸张。** 没有基准测试或真实案例就不写 *"fast"*、*"production-ready"*、*"best-in-class"* 这种词。能力声明得配一个验证命令,否则整句话删掉。

插件在[持续维护中](./MAINTENANCE.md)。重构工具会演进,skill 系统会变,LLM 的失败模式也会变 —— 每个 skill 都按一个时间表定期复审。

---

## 贡献

开源,但目前不接受 PR。发现 bug、想加一门新语言或 runtime、觉得文档写得不清楚、有新 skill 的点子?[开 issue](https://github.com/subinium/vibesubin/issues)。维护者会直接复核并整合进来,这样语气能保持一致。详见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

---

## 许可证

MIT —— 见 [LICENSE](./LICENSE)。

---

历次改动记录在 [`CHANGELOG.md`](./CHANGELOG.md) 里。插件版本号在 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) 里。
