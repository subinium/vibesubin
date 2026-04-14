# vibesubin

一个为 **vibe coders** 设计的温和关怀型技能包 — 面向那些用 AI 运行真实生产代码仓库、但没有受过系统开发训练的人。

> [English](./README.md) · [한국어](./README.ko.md) · [日本語](./README.ja.md)

> **权威版本是英文版**。本中文版目前为概要翻译，完整的触发场景、方法论细节、故障排查和贡献指南请参见 [English README](./README.md)。全文翻译将在英文版稳定后进行。

---

## 它解决什么问题

当非开发者让 AI 重构、审计、部署代码时，常见的失败模式往往是**静默的**：

- AI 说"完成了"，但并没有真正验证 — 一个类被移动了，但三处调用仍然指向旧路径
- 一份 3000 行的文档被重写，过程中 12 个关键事实悄悄消失了
- 一次安全"审计"报告了 30 个问题，全部都是误报，而真正的漏洞被漏掉了
- 硬编码的 `C:\Users\alice\...` 路径从队友电脑上被提交
- "有帮助的"重构引入了一个幻觉 import，没人注意到
- 仓库开始腐烂：死代码、巨型文件、高变动热点，但没人追踪
- CI/CD 是手动 SSH，没有回滚计划，操作者从没听说过 `workflow_run`
- 提交消息只写"update"，下一个 AI 会话必须重读整个 diff 才能理解改了什么

**这不是你的错。** 工具假设你懂一些从没人教过你的东西。这个技能包尝试把其中一些缺失的部分打包成技能，让你的 AI 能代表你使用。

---

## 包含的六个技能

每个技能都是一个独立的目录，位于 [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/)。你不需要记住它们 — AI 会根据你的问题自动挑选合适的技能。

| 技能 | 核心作用 |
|---|---|
| **`refactor-safely`** | 将任何重构规划为 Mikado 风格的依赖树，从叶节点向上执行，并通过**六步递归验证**（符号集 diff、AST 节点 diff、行为测试、调用点闭包检查）证明 1:1 语义等价性。触发于 "重构这个"、"这个还能正常工作吗"、"拆分这个文件" 等 |
| **`audit-security`** | 故意保持小巧、人工挑选的安全扫描。硬编码密钥、SQL/shell 注入、XSS、路径穿越、危险反序列化、缺失的 Cookie 标志、通配符 CORS、追踪中的密钥文件。每条发现都被分类为"真实"、"误报"或"需要确认"。触发于 "这安全吗"、"有漏洞吗"、"审计" |
| **`fight-repo-rot`** | 计算**变动频率 × 复杂度热点**，揪出最该重构的文件。同时发现巨型文件、死代码、硬编码路径、陈旧 TODO、失衡的依赖图。触发于 "清理这个"、"什么烂掉了"、"哪里是死代码" |
| **`write-for-ai`** | 为**下一个 AI 会话**优化的文档、提交消息、PR 描述写作。包括 README、`CLAUDE.md`/`AGENTS.md`、conventional commit、PR 正文模板。原则：表格和清单胜过散文；绝对路径始终用反引号；不变量单独成章 |
| **`setup-ci`** | 从零讲解 CI/CD 给非开发者听，然后生成可用的 GitHub Actions `test.yml` + `deploy.yml`。内置并发组、超时、密钥清理、部署后健康检查。按**必需 / 推荐 / 可选 / 有则更好 / 昂贵**五级决策树提供组件选择 |
| **`manage-config-env`** | 对结构性决策给出有主见的默认值：`.env` 布局、`.gitignore` 模板、依赖固定策略、分支策略（默认 GitHub Flow）、目录结构与命名规范、路径可移植性审计 |

此外还有一个总入口技能 **`vibesubin`**：当你不知道从哪开始时，输入 `/vibesubin` 会触发它，它会问一个简短的问题并把你路由到合适的专门技能。

---

## 三个贯穿全包的价值

每一个设计决策都在为这三件事服务。冲突时，按此顺序取舍：

1. **可维护性** — 仓库六个月后仍应对一个**陌生人**（通常是新的 AI 会话，也可能是六个月后的你）可读
2. **安全** — 假设每一次 diff 都有对手在看
3. **生产力** — 一条命令应该完成一件无聊的事情。操作者的注意力是最稀缺的资源

---

## 安装

### 通过 Claude Code 插件市场（推荐）

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
/plugin marketplace update    # 之后拉取更新
```

这是唯一能获得**自动更新**的路径。

### 手动安装（回退方案）

```bash
git clone https://github.com/subinium/vibesubin.git
cd vibesubin
bash install.sh         # 为每个技能创建 ~/.claude/skills/ 的软链接
```

卸载：`bash uninstall.sh`。

### 关于便携性

虽然本包目前按 Claude Code 的技能格式编写，但**结构本身是便携的**。每个技能都是一个自包含的目录（Markdown + 脚本 + 模板），可以较低成本移植到其他 skill marketplace 或 agent 框架。未来支持其他平台时会在这里添加安装说明。

---

## 日常使用方式

安装后，你大多数时候不需要按名字调用技能。用自然语言描述你想做的事，AI 会自动挑选合适的技能：

| 你说... | 会触发 |
|---|---|
| "清理这里，别把东西搞坏了" | `refactor-safely` |
| "我刚才改了，还能正常工作吗" | `refactor-safely` |
| "有什么泄漏？有漏洞吗？" | `audit-security` |
| "我的仓库还好吗？最该修什么？" | `fight-repo-rot` |
| "帮我写 README / commit / PR" | `write-for-ai` |
| "帮我设置自动部署" | `setup-ci` |
| "这个密钥该放哪里？" / "main 还是 dev？" | `manage-config-env` |

如果不确定，输入 `/vibesubin` 打开总入口并获得一次引导。

---

## 仅接受 Issue，不接受 PR

本包开源但**目前不接受 Pull Request**。如果你发现：

- 某个技能在实际任务中失败了
- 不支持你用的语言或运行时
- 有重构或安全模式被漏掉了
- 文档对非开发者不清晰

请[提 issue](https://github.com/subinium/vibesubin/issues)。维护者会审阅并直接修复，以保持本包语调的一致性。

---

## 许可证

MIT — 见 [LICENSE](./LICENSE)。

---

*本包由一位 vibe coder 为 vibe coders 打造。作者亲身经历了它所防范的每一种失败模式。如果其中一个技能为你省下一个下午，那它就已经回本了。*
