# vibesubin

AI アシスタントに、リファクタリング・監査・デプロイを「本来こうあってほしい」やり方で仕込むための、ポータブルなスキルプラグインです。しかも `/vibesubin` ひとつで全部まとめて走らせられます。

開発者としての訓練は受けていないけれど、AI を使って実際にものを出荷している人のために作りました。自分が AI とコーディングするときに実践している習慣をスキルとしてパッケージしたものです。ルールをいちいち覚えなくても、アシスタントがそのまま従ってくれます。

同じ `SKILL.md` が **Claude Code**、**Codex CLI**、そして **[skills.sh](https://skills.sh) がサポートするあらゆるエージェント**(Cursor、Copilot、Cline など)で動きます。一度書けば、どのホストでも拾われます。

> [English](./README.md) · [한국어](./README.ko.md) · [中文](./README.zh.md)

---

## クイックスタート

[Claude Code](https://code.claude.com) をインストールして、次を実行:

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

リポジトリを開いて `/vibesubin` と打つだけ。全スキルが並列・読み取り専用でコードを走査し、優先順位付きのレポートひとつにまとめて返ってきます。リストから承認するまで、コードには一切触れません。スキルに実際に *作業* をさせたいときは、名前で直接呼び出してください(`/refactor-verify`、`/setup-ci` など)。そうすれば、ファイルを直接編集します。

Codex CLI、Cursor、Copilot、Cline を使っている場合は [Install](#install) セクションへどうぞ。

---

## vibesubin とは、そうでないもの

AI スキルの小さなバンドル — `SKILL.md` ファイル群 — を、エージェントがリクエストにマッチしたときに自動で拾います。普段の言葉で *「このファイル安全に分割して」*、*「なんか漏れてない?」*、*「デプロイ組んで」* と言えば、適切なスキルが走ります。

全スキル共通のルール: **証拠を見せられるまで「完了」とは言いません。** リファクタは AI がファイルを書き換えたから終わるのではなく、4 つの独立したチェックで「何も落ちていない・ずれていない・誤配線していない」が確認できて初めて終わります。セキュリティスイープは「vibe」で書いた段落ではなく、ファイル名と行番号付きの仕分け済みリストです。

SaaS ではなく(何もマシンから出ません)、コンプライアンスツールでもなく(SOC 2 / HIPAA は対象外)、コードジェネレータでもありません。すでにあるリポジトリを改善するためのものです。

### 使い方は 2 通り — スイープと直接呼び出し

- **スイープモード(`/vibesubin`)**。コード衛生系のスキルが全部並列で走りますが、すべて *読み取り専用* です。優先順位付きレポートがひとつ返り、項目を承認するまでリポジトリには何の変更も入りません。
- **直接呼び出し(`/refactor-verify`、`/setup-ci`、...)**。スキルが本来の仕事をフルで行います。ファイル編集も含みます。
- **プロセス系スキル(`/ship-cycle`)と、ホスト固有ラッパー(`/codex-fix`)** は直接呼び出し専用です。外部システム(GitHub、Codex)に変更を加えたりリリース状態を管理したりするので、sweep には入りません。

どちらの呼び方をしても絶対に編集しないスキルが 3 つあります:`fight-repo-rot`、`audit-security`、`manage-assets` — 純粋な診断専用です。

### 現在のラインナップ

**コード品質(5)**

| スキル | こう頼む | こう返ってくる |
|---|---|---|
| [`refactor-verify`](#refactor-verify) | *「このクラスの名前を変えて」*、*「このファイル分割して」*、*「このデッドコードを安全に消して」* | 計画されたリファクタを 4 つの検証パスで支え、全部通るまで「完了」と言いません |
| [`audit-security`](#audit-security) | *「シークレット漏れてない?」*、*「これ安全?」* | 500 行の PDF ではなく、ファイル名と行番号付きの、仕分け済みの短い本物リスト |
| [`fight-repo-rot`](#fight-repo-rot) | *「デッドコード探して」*、*「何消せる?」* | HIGH / MEDIUM / LOW の信頼度タグ付きデッドコード、神ファイル、ホットスポット。診断専用 |
| [`manage-assets`](#manage-assets) | *「リポが重すぎる」*、*「LFS 使うべき?」* | 肥大化レポート — 大きなファイル、git 履歴の巨大 blob、LFS 候補。履歴書き換えはしません |
| [`unify-design`](#unify-design) | *「ボタンを統一して」*、*「この色をトークンに抽出して」* | デザインシステム監査 — トークンを足場組み、ハードコード hex と魔法の px を特定、重複を統合 |

**ドキュメント & AI 親和性(2)**

| スキル | こう頼む | こう返ってくる |
|---|---|---|
| [`write-for-ai`](#write-for-ai) | *「README / コミット / PR 書いて」* | *次の* AI セッションが実際に読めるドキュメント — 根拠のないマーケ語なしで |
| [`project-conventions`](#project-conventions) | *「main と dev どっち?」*、*「この依存ピン留めする?」* | 決定ごとにデフォルトひとつ — GitHub Flow、ピン留め、ドメインファーストのレイアウト |

**インフラ & config(2)**

| スキル | こう頼む | こう返ってくる |
|---|---|---|
| [`setup-ci`](#setup-ci) | *「デプロイ組んで」*、*「push で deploy したい」* | テスト + デプロイ用の動く GitHub Actions と、平易な言葉での解説 |
| [`manage-secrets-env`](#manage-secrets-env) | *「このシークレットどこに置く?」*、*「`.env` 漏れてないよね?」* | 決定ごとに意見の強い答えひとつ + シークレットのライフサイクル全体 |

**リリースプロセス(1)**

| スキル | こう頼む | こう返ってくる |
|---|---|---|
| [`ship-cycle`](#ship-cycle) | *「リリース計画」*、*「이슈 드리븐」*、*「まとめてリリース切る」* | イシュー駆動リリースオーケストレーター — 多言語イシュー下書き、マイルストーン=バージョン、適切なワーカーへ委譲、changelog 集約、タグ + リリースまで。**2 トラック** — GitHub(デフォルト)と、他ホスト向けの PRD-on-disk |

**ホスト固有ラッパー(1)**

| スキル | こう頼む | こう返ってくる |
|---|---|---|
| [`codex-fix`](#codex-fix) | *「codex 돌려서 고쳐줘」*、*「Codex で最終チェック」* | 薄いラッパー:`/codex:rescue` → `refactor-verify` の review-driven fix mode。**Claude Code + Codex プラグイン専用**、他ホストでは一行の fallback |

新しいスキルは `plugins/vibesubin/skills/` に置けば `/vibesubin` が自動で拾います。

---

## `/vibesubin` コマンド

一語で、リポジトリに対してコード衛生系スキルを全部並列実行し、findings を優先順位付きレポートひとつにマージし、承認を待つ。

起動前にスコープを絞れます(*「src/api だけ」*、*「security と repo rot だけ」*)。sweep では全スキルが読み取り専用で、findings を出すだけで修正はしません。Critical はカテゴリ関係なく最上位に浮き、同じファイルを複数スキルが指摘したら優先度が跳ね上がります。返ってくるのは、vibe-check の段落、専門スキルごとの信号機一行、トップ 10 修正リスト、推奨順序、そして一文の総評。synthesis の完全ルールは [umbrella の `SKILL.md`](./plugins/vibesubin/skills/vibesubin/SKILL.md) にあります。

**スイープか単体か**。オープンエンドな質問にはスイープ(*「出荷していい?」*、*「セカンドオピニオンが欲しい」*)。やりたいことが決まっているなら単体呼び出し(*「このファイルリファクタして」* → `/refactor-verify`)。漏れたシークレットは sweep をスキップして `/audit-security` のインシデントパスへ直行。

**ハーシュモード**。オプトインで直接的なトーンに切り替え — `/vibesubin harsh`、*「容赦なくレビューして」*、*「オブラートに包まないで」*、*「매운 맛으로」*、*「厳しめで」*。読み取り専用のまま、根拠も同じ、ただ言葉を和らげません。勝手にハーシュにはなりません。

**Layperson モード**。オプトインで平易な言葉に翻訳 — `/vibesubin explain`、`/vibesubin easy`、*「非開発者でも分かるように」*、*「やさしい言葉で」*、*「쉽게 설명해줘」*、*「用通俗的话解释」*。各 finding が 3 次元ブロック(*なぜやるか / なぜ重要か / 何をするか*)にボックスで整形され、重大度は緊急度に翻訳(CRITICAL → *「今すぐ」*)。ハーシュモードとスタック可能。詳細は [`references/layperson-translation.md`](./plugins/vibesubin/skills/vibesubin/references/layperson-translation.md)。

**スキル間コンフリクト**。2 つの専門スキルが同じファイルで食い違ったとき(例:*refactor-verify* が「止めろ」と言い、*unify-design* が「統合しろ」と言う)、レポートは `⚠ Skill conflict` ブロックでギャップ・理由・各側の根拠を表示 — 判断はオペレータが下します。カタログは [`references/skill-conflicts.md`](./plugins/vibesubin/skills/vibesubin/references/skill-conflicts.md)。

---

## Install

| パス | 対象エージェント | 向いている場面 |
|---|---|---|
| **A. Claude Code marketplace** | Claude Code | 最もシンプル、自動更新 |
| **B. `skills.sh`** | Cursor、Copilot、Cline、Codex CLI、Claude Code | エージェント横断 |
| **C. 手動シンボリックリンク** | Claude Code / Codex CLI | プラグイン自体をいじるとき |

**A — Claude Code marketplace**(推奨)

```
/plugin marketplace add subinium/vibesubin
/plugin install vibesubin@vibesubin
```

更新は `/plugin marketplace update`、アンインストールは `/plugin uninstall vibesubin`。

**B — skills.sh**(エージェント横断、[skills.sh](https://skills.sh) 経由)

```bash
npx skills add subinium/vibesubin
```

同じコマンドを再実行すると更新されます。削除は `npx skills remove vibesubin`。対応ホストは `npx skills --help` で確認できます。

**C — 手動シンボリックリンク**(編集可能、オフライン、`git pull` でそのまま反映)

```bash
git clone https://github.com/subinium/vibesubin.git
cd vibesubin
bash install.sh                  # Claude Code(デフォルト)
bash install.sh --to codex       # Codex CLI
bash install.sh --to all         # 両方
bash install.sh --dry-run        # プレビュー
```

更新は `git pull`。アンインストールは `bash uninstall.sh [--to codex|all]` — スクリプトが作ったシンボリックリンクだけが削除されます。

インストールでつまずいたら、まずはエージェントのセッションを全部閉じて、新しいセッションを開き直してください(スキルはセッション単位でキャッシュされます)。それでもダメなら [issue を立ててください](https://github.com/subinium/vibesubin/issues)。

---

## スキル一覧

各スキルは [`plugins/vibesubin/skills/`](./plugins/vibesubin/skills/) にあります。以下はユーザー向けの説明で、完全な方法論は各スキルの `SKILL.md`、詳細な参考資料は同じ階層の `references/` フォルダにあります。

### コード品質

#### `refactor-verify`

一番強く擁護したいスキルです。AI がコードに触れるときの最大の失敗モードは、静かな失敗です。関数が移動されて、リネームも通って、テストも通って、3 週間後に誰かが古い名前を指したままのコードパスを踏んで全部落ちる。`refactor-verify` は、これを起こしようがなくするために存在します。

対象は構造的リファクタ(move / rename / split / merge / extract / inline)と、安全な削除(`fight-repo-rot` が dead と確認したコードの削除)。両方とも同じ 4 チェックの証明を使います:シンボル集合の保存、移動されたコードのバイト等価性、typecheck / lint / tests / smoke の再実行、import グラフ全体での呼び出し元監査。4 つのうち 1 つでも落ちたら先に進みません。頼んでいないファイルには触らず、チェックが 1 つでも落ちているのに「完了」とは言わず、`fight-repo-rot` が LOW 信頼度でフラグしたコードは人間レビュー無しでは削除しません。

#### `audit-security`

エンタープライズのスキャナは 500 件フラグを立てて 490 件が誤検知。`audit-security` はその逆 — 本物のミスを捕まえる、手作業で選ばれた短いパターン集で、各ヒットを「本物」「誤検知」「要人間確認」に仕分けし、一行の理由を添えます。

チェックするもの:明らかなもの(コミット入りシークレット、文字列連結の SQL、`eval` / `exec` / `pickle.loads`)、そこまで明らかでないもの(ユーザー入力で制御されるファイルパス、未エスケープ HTML、`httpOnly` / `Secure` のない Cookie、ワイルドカード CORS)、忘れがちなもの(git 履歴の `.env`、`.pem`、SSH 鍵)。重大度は平易な言葉で — *「見知らぬ他人が全ユーザーのデータを読める」* が *「CWE-89」* より伝わります。ペネトレーションテストではなく、静的スイープのみ、ネットワークは触りません。

#### `fight-repo-rot`

一にデッドコード検出、二に散らかり検出、常に純粋な診断。誰も呼んでいない関数、誰も import していないファイル、孤立モジュール、manifest にあるのに一度も import されていない依存。その上で神ファイル、ホットスポット(高頻度変更 × 高複雑度)、ハードコード絶対パス、リテラル IP、6 ヶ月以上古い `TODO` / `FIXME` もフラグします。

デッドコード候補には必ず信頼度タグが付きます:**HIGH**(どこからも参照なし — `refactor-verify` に削除を渡して安全)、**MEDIUM**(テストからしか参照なし、動的ディスパッチ絡み — オペレータ確認)、**LOW**(export されたシンボル、生成コード、リフレクション / DI — 人間レビュー必須)。編集せず、削除せず。削除は `refactor-verify`、ハードコードパス修正は `project-conventions`、CVE 級の依存腐敗は `audit-security` にハンドオフ。

#### `manage-assets`

肥大化検出器であって、コード分析器ではありません。バイナリの重さを浮かび上がらせます:ワーキングツリー内のファイルサイズ、git 履歴内の blob サイズ(見えない方)、LFS 移行候補、アセットディレクトリの増大、重複バイナリ。**診断専用** — ファイルを削除しない、履歴を書き換えない、`git filter-repo` や `git lfs migrate` を走らせません。承認された削除は `refactor-verify`(検証付き履歴書き換え)、`manage-secrets-env`(`.gitignore` 絡み)、`fight-repo-rot`(未参照アセット)にハンドオフ。

#### `unify-design`

フロントエンド向けのデザインシステム一貫性 — トークン + 重複の監査。ブランドアイデンティティ(色、間隔、タイポグラフィ、radius、shadow、breakpoint、中心コンポーネント)を単一の source of truth として扱い、ドリフトをトークン参照に書き戻します。フレームワークを自動検出(Tailwind v3 / v4、CSS Modules、styled-components、Emotion、MUI、Chakra、vanilla CSS)し、プロジェクト自身のイディオムを使い、外のパターンを持ち込みません。

3 つのことをします。トークンがなければ足場組み(primary color と display font だけオペレータに尋ねる)、ドリフト監査(ハードコード hex、`w-[432px]` のような Tailwind arbitrary value、インラインスタイルオブジェクト、重複した Button / Card / Nav)、ドリフト修正(小さな置換は直接、複数ファイルの統合は `refactor-verify` に)。ブランドを発明したり、フレームワークをまたいで書き換えたりはしません。

### ドキュメント & AI 親和性

#### `write-for-ai`

*次の* AI セッションにも人間にも向けて書かれたドキュメント。新鮮な AI セッションのつもりでリポジトリを冷たい状態から読み、不変条件を抽出し(プロジェクトが *何を* するかだけでなく、*どんなルールに従っているか* も)、関連するテンプレート(README、commit、PR description、architecture doc、`CLAUDE.md`、`AGENTS.md`)を埋め、書く前に各主張を検証します — README に `pnpm test` でテストが走ると書くなら、スキルは先に `pnpm test` を実行します。

古典的な失敗モードを防ぎます:AI に README を書き直させたら見事な仕事だったけれど、環境変数の段落がこっそり消えていた。気づかない。次のセッションは新しい README から始まって、env レイアウトがあることすら知らない。

#### `project-conventions`

賭け金が低めの構造的デフォルト:ブランチ戦略、依存のピン留め、ディレクトリレイアウト、絶対パスの衛生。デフォルトは GitHub Flow(`main` + 寿命の短い feature ブランチ、`dev` は無し)、本番依存は厳密ピン留めで lockfile をコミット、Dependabot / Renovate 月次、ドメインファーストのレイアウト、ソースに絶対パスを書かない。各ルールには一文の理由。

新規プロジェクトでは `dependabot.yml` とブランチ戦略メモを足場組み。既存プロジェクトでは逸脱を監査し、複数ファイルの修正は `refactor-verify` にハンドオフ。

### インフラ & config

#### `setup-ci`

CI はパックで最大の生産性向上です — 一度組めば、deploy は考えるものではなくなって `git push` そのものになります。まず概念を平易な言葉で説明(runner、Secrets、`concurrency` グループ、デプロイ後ヘルスチェック)、`package.json` / `requirements.txt` / `Cargo.toml` / `go.mod` からスタックを検出し、ワークフローを 2 本足場組み:`test.yml`(テスト + lint、タイムアウト付き)、`deploy.yml`(ホスト別のパターン — SSH、Vercel、Fly.io、Cloud Run、Netlify — concurrency ガード、SSH 鍵クリーンアップ、ヘルスチェック付き)。

意図的にやらないこと:Secrets を代わりに登録しません(GitHub UI に置くものです)、ホストを推測しません。

#### `manage-secrets-env`

「この値どこに置くべき?」の、一番賭け金が高い部分 — 置く場所を間違えるのはインシデントであって、スタイルの好みではありません。4 バケツの判定ツリー(ソース定数 / 環境変数 / ローカル `.env` / CI シークレットストア)、`.env.example` ↔ `.env` のドリフトチェック、デフォルトで安全な `.gitignore` テンプレート、シークレットのライフサイクル全体(追加 / 更新 / ローテーション / 削除 / バケツ間移行 / 監査 / 新環境プロビジョニング)。

デフォルト:ランタイム不変の定数はコード、ローカルのシークレットはコミット済み `.env.example` 付きの `.env`、本番は CI シークレットストア、環境差分のランタイム値は環境変数、`.gitignore` はシークレット形のエントリ事前埋め込み済み。既存プロジェクトでは tracked になったシークレットファイルをインシデント級でフラグ、漏洩進行中なら `audit-security` にハンドオフ。

### リリースプロセス

#### `ship-cycle`

パック唯一の **process カテゴリ** スキル。コードの *周辺のライフサイクル* に作用します — イシュー、マイルストーン、バージョン、タグ、リリース、changelog。ループはこう:intake → draft → cluster → confirm → create → branch → execute → release。多言語イシュー本文(日本語 / 英語 / 韓国語 / 中国語)、semver 判定ツリー(bug / perf / refactor → patch、追加 feat → minor、breaking → major)、patch は約 5 件キャップ。

**2 トラック**。**GitHub トラック**(デフォルト)は `gh` API を使います — イシュー、マイルストーン、PR、リリースは GitHub 上に存在し、`Closes #<N>` フッターで merge 時に自動クローズ。**PRD トラック**(他ホスト)は `docs/release-cycle/vX.Y.Z/` 配下のローカルマークダウンを使います — 方法論も規約も同じ、耐久性のある監査証跡の形だけが違います。オペレータが Step 1.5 で選びます。**規約は [`references/pr-branch-conventions.md`](./plugins/vibesubin/skills/ship-cycle/references/pr-branch-conventions.md) の通り強制されます**:GitHub Flow ブランチ(`<type>/<issue-N>-<slug>`)、Conventional Commits + 必須の `Closes #<N>` フッター、6 セクション必須の PR テンプレート(Context / What changed / Test plan / Docs plan / Risk / Handoff notes)、rebase-first merge + `--force-with-lease`、`main` / `master` / `release/*` への force-push 禁止。

意図的にやらない 3 つ:下書きイシューセットのオペレータ承認をスキップしない、main の CI が green でない状態でタグを push しない、関係ない項目を 1 つのマイルストーンに混ぜない。

### ホスト固有ラッパー

#### `codex-fix`

ひとつ特定のワークフローのための薄いラッパー(〜100 行):*「編集のひとまとまりを終えた。Codex でセカンドモデルのレビューを走らせる。Claude に検証付きで解決させる。」* 現在のブランチ diff に `/codex:rescue` を実行し、findings を `refactor-verify` の review-driven fix mode にハンドオフします。

**Claude Code + Codex プラグイン専用**。他のあらゆるホストでは *「Codex プラグインが検出されませんでした — 代わりに findings を `/refactor-verify` に直接渡してください。」* と出して、きれいに抜けます。

Claude Code + Codex 環境にいて、レビューソースが Codex であるときに `/codex-fix`。他のソース(人間の PR レビュー、Sentry、`gitleaks`、Semgrep、貼り付けたメモ)なら `/refactor-verify` を直接呼ぶ — エンジンは同じ、入力経路だけ違います。[`docs/PHILOSOPHY.md`](./docs/PHILOSOPHY.md) のルール 9「ポータブルエンジン + 薄いラッパー」のパターンでカバー。

---

## 日常の使い方

呼び出し方は 3 通り、知っている情報量の少ない順に。

どこから始めていいか分からない? `/vibesubin` と打てば全部走ります。何が気になっているか分かっている? 普段の言葉で言ってください — *「ここ整理して、ただし壊さないで」* で `refactor-verify`、*「シークレット漏れてない?」* で `audit-security`、*「何から直すべき?」* で `fight-repo-rot`。使いたいスキルが決まっている? 名前で呼んでください:`/refactor-verify`、`/audit-security` など。

全スキルは 4 部構成の出力に従います:何をしたか、何を見つけたか、何を検証したか、次に何をすべきか。この 4 つを含まない散文の壁が返ってきたら、それはバグです — [issue を立ててください](https://github.com/subinium/vibesubin/issues)。

### よくあるワークフロー

- **リポジトリの掃除**。`fight-repo-rot` が最悪の箇所を見つける → `refactor-verify` が検証付きで直す → `write-for-ai` がコミットと PR を書く。
- **リリース準備**。`audit-security` でシークレット確認 → critical なものは `refactor-verify` で対応 → `setup-ci` で次の退化を捕まえる体制に。
- **新しいリポジトリへのオンボーディング**。`/vibesubin` でフルスイープ → `write-for-ai` が欠けている `CLAUDE.md` を埋める → `manage-secrets-env` が `.gitignore` とシークレットを監査 → `project-conventions` がブランチ・依存・レイアウトを監査。
- **ゼロから始める**。`manage-secrets-env` が `.env.example` と `.gitignore` を足場組み → `project-conventions` が Dependabot とブランチメモを足場組み → `setup-ci` がワークフローを敷く → `write-for-ai` が README と `CLAUDE.md` を書く。
- **「なんでリポがこんなに重いの?」**。`manage-assets` が肥大化レポートを出す → `refactor-verify` が履歴書き換えや LFS 移行を検証付きで実行。
- **「ページごとに微妙に見た目が違う」**。`unify-design` がトークンファイルを足場組み(無ければ)してドリフトを監査し、コンポーネントをトークン参照に書き戻す → `refactor-verify` が複数ファイルの統合を処理。
- **「編集完了後の Codex ループ」(Claude Code + Codex プラグイン専用)**。編集のひとまとまりを終える → `codex-fix` が現在のブランチ diff に `/codex:rescue` を実行 → `refactor-verify` の review-driven fix mode にハンドオフ → トリアージ、検証、back-reference 付きコミット。他のホストや、Codex 以外のレビューソース(PR レビュー、Sentry、スキャナー、貼り付けたメモ)の場合は `/refactor-verify` を findings を直接渡して呼び出してください — エンジンは同じで、入力経路だけが違います。
- **リリース計画(Claude Code + GitHub + `gh` 限定)**。改善のバッチがたまった、または `/vibesubin` sweep が優先リストを出した後 → `ship-cycle` が一括で多言語イシューを下書き → 次の semver バージョンに対応するマイルストーンへクラスタリング → ラベルごとに適切なワーカーに委譲し検証つきで実行 → マイルストーンがクローズしたら、クローズ済みイシューから機能ベースの changelog を集約、両 manifest を bump、注釈付きタグを切って GitHub リリースを作成。非 GitHub ホストや `gh` 未認証時は `ship-cycle` が 1 行で fallback し終了 — その場合は下位のワーカーを直接呼ぶこと。

これを自分で計画する必要はありません。スキル側が次のハンドオフを提案します。

---

## 自分のスキルを追加する

新しいスキルは `plugins/vibesubin/skills/<skill-name>/` 配下の自己完結したディレクトリです。そこに置いてエージェントを再起動すれば、`/vibesubin` も補完メニューも自動で拾います。

```
plugins/vibesubin/skills/<skill-name>/
├── SKILL.md              # 必須、500 行以下、YAML frontmatter 付き
├── references/           # 任意、深掘り用のドキュメント
├── scripts/              # 任意、実行可能なヘルパー
└── templates/            # 任意、プロジェクトにコピーされるファイル
```

新しいスキルが継承するルール:*完了* とは検証済みのことで、主張ではない。`SKILL.md` は 500 行以下で、深い内容は `references/` に。出力は 4 部構成に従う。スイープ対象のスキルは read-only モードが必要。各スキルは自分の自信がどこで切れるかを明示する。

メインプラグインへの同梱を希望するスキルがある? トリガーフレーズ、やること、具体例を添えて [issue を立ててください](https://github.com/subinium/vibesubin/issues)。詳細は [`CONTRIBUTING.md`](./CONTRIBUTING.md) に。

---

## 哲学

全スキルが従うルールをいくつか。覚える必要はありません — 現在と未来のスキルの一貫性を保つためにあります。

**AI は善意のジュニア開発者です**。ジュニアは一生懸命働きますが、止まって聞くべきタイミングでも先に進んでしまうことがあります。このプラグインは、慎重な手なら差し込んだはずの *「一旦止まって聞く」* モーメントを差し込みます。

**Done は証明であって、主張ではありません**。タスクが complete と言うなら、その裏には実行結果があります — 通ったテスト、一致したハッシュ、生きた `200 OK`。証拠のない主張はバグです。

**ドキュメントは次の AI セッションのためのもので、人間のためだけではありません**。現在の会話はセッションが終われば蒸発します。README、コミット、PR 本文は、新鮮なセッションがコンテキストを再構築できるように書きます。

**既存の conventions がデフォルトです**。気まぐれであなたのブランチ戦略、ファイル配置、config を勝手に書き換えたりはしません。

このプラグインは [積極的にメンテナンスされています](./MAINTENANCE.md)。リファクタリングツールは進化し、スキルシステムは変わり、LLM の失敗モードはシフトします。各スキルは定期的にレビューされます。

---

## コントリビューション

オープンソースですが、PR は現在受け付けていません。バグを見つけた、新しい言語やランタイムをカバーしてほしい、ドキュメントが不明瞭だった、新しいスキルのアイデアがある? [issue を立ててください](https://github.com/subinium/vibesubin/issues)。メンテナーがレビューして直接反映します — そのほうが声のトーンが一貫するからです。詳細は [`CONTRIBUTING.md`](./CONTRIBUTING.md) に。

---

## ライセンス

MIT — [LICENSE](./LICENSE) を参照。

---

変更履歴は [`CHANGELOG.md`](./CHANGELOG.md) で追跡しています。プラグインのバージョンは [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json) にあります。
