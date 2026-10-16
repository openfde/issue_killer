---
name: run-issue-workflow
description: 当交互用户希望通过原子 skill 启动、恢复或检查一个已配置的 issue 分析 run 时使用。
---

# 运行单个 issue 工作流

这是一个薄编排器。开始前必须取得当前调用方显式指定的问题编号或完整 URL；人工 Pi 会话中必须来自当前用户请求，服务器模式中必须来自受信任的服务器队列。缺少指定时只返回“请选择问题”，不得创建运行目录、访问 GitHub 或下载任何内容。不得从问题列表、旧产物或上下文自行选择。

选择检查通过后，先初始化唯一目录 `.fde-ai/issues/<issue号>/` 及其 `input/`、`evidence/`、`analysis/`、`solution/`、`patch/`、`build/`、`comment/`、`archive/` 子目录，并在根目录**先写入** `state.json`：唯一状态字段名为 `state`，初始值为 `initialized`，同时记录 issue 编号、revision、profile SHA-256 与更新时间。不得使用 `status` 代替 `state`。然后加载项目配置、构建项目上下文、检查 `state.json`，恰好调用一个有效的原子 skill。该 skill 完成后重新读取并校验产物/状态；仅在调用方要求继续处理时重复。服务器协调器会对同一受信任 issue 自动发起后续调用，直到终态。任何后续技能都只可处理已明确选择的同一编号。唯一 patch 入口是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`；不得在 `.fde-ai/runs/` 创建新产物。

允许的顺序为 `load-project-profile` → `build-project-context` → `fetch-github-issue` → 一个证据分支 → `resolve-manifest-components`（低置信时经 `confirm-component-mapping` 人工确认）→ `cache-provenanced-sources` → `retrieve-knowledge` → `trace-evidence-to-source` → `verify-analysis` → `propose-fix` → 可选的 `draft-patch` / `validate-patch-artifact` → 可选 `create-fix-pull-request`（人工确认；只创建/更新 PR、不合入主分支）→ `draft-issue-comment` → `publish-policy-comment`（**交付/验证征询评论必须立即发布到 issue**，不得因等待构建而延迟）→ 配置了 `build` 时 `request-build` → `collect-build-artifacts`（构建结果后到时追加一条简短更新评论）→ `awaiting_verification` →（回复轮询）→ `confirmed_fixed` → `archive-case`。任意阶段受阻时可先走 `escalate-issue`。

**汇报与交互规范（人工交互模式）**：不逐步汇报所有原子步骤——加载配置、构建上下文、拉取 issue、证据提取、知识检索、引用校验等机械步骤内部连续执行，最多一句话带过（服务器队列模式仍按其提示词每次只推进一个原子步骤）。源码检索**一律使用 `rg`** 并限制范围与上限（`timeout`/`head`），禁止 `grep -r` 全树遍历。只在以下**关键节点**停下汇报，并给出 A/B/C 选项等待选择：

1. **定位结论**：证据提取与组件归属完成——问题落在哪个组件的哪个功能；
2. **根因结论**：分析校验通过——一句话根因 + 因果链要点；
3. **修复方案**：推荐改法与替代方案、风险（`not_run`）；
4. **求助（任意阶段受阻时）**：当前进度、已排除方向、具体问题与 A/B/C 选项（`escalate-issue`）；
5. **代码修改**：**用统一 diff 直接展示修改**（引用 patch 文件的关键 hunk，不得只给路径），并逐处说明修改目的；该节点的 A/B/C 应包含“生成 PR（只创建、不合入主分支；跨多个项目时按项目分别生成并附全部链接）”“只保留补丁文件”“暂停”等选项；
6. **校验结果**：补丁结构与来源校验的通过项/问题项；
7. **评论草稿与验证征询**：草稿路径与要点；交付后请开发人员回复 `验证通过` 或 `仍有问题`（附新日志/截图）。

关键节点汇报格式（结论在前、简洁）：

```text
【<节点名>】<一句话结论，直白说明问题/结果>
依据：<1~3 条，含 文件:行号 或日志时间戳或证据 ID>
产物：<产物相对路径>

下一步（回复 A/B/C）：
A. <动作>
B. <动作>
C. <动作>
```

示例：

```text
【根因结论】筛选条件在窗口退出时没有被清空：provider 忽略了 name==null 的复位请求。
依据：AllAppsProvider.kt:40-42（仅 name!=null 时覆盖 filter）；AppOverviewWindow.kt:417（退出时传 null）；日志 02:17:05.902 仍按旧关键字过滤
产物：.fde-ai/issues/491/analysis/analysis.md

下一步（回复 A/B/C）：
A. 继续生成修复方案
B. 先展示该窗口相关代码片段
C. 暂停本轮
```

到达等待态（`component_review_requested`/`build_requested`/`build_failed`/`awaiting_direction`/`awaiting_verification`）或终态（`archived`/`needs_information`/`blocked`）时，同样给出 A/B/C 选项（含继续方式/恢复命令）并说明原因，不得沉默结束需要人工决策的步骤。

**会话恢复规则**：任何会话（含被轮询/服务器唤醒的无人值守运行）继续处理时，必须先重读 `.fde-ai/issues/<issue号>/state.json` 与最新产物，从**当前实际状态**继续；不得依赖旧会话上下文，也不得因上下文与文件不一致而停止。

**继续命令（交互会话，优先使用）**：在会话中说“继续 <编号>”时——先重读 `state.json`；若处于 `awaiting_direction`/`awaiting_verification`，先执行一次 `sync-github-replies` 检查 issue 新回复并据此更新状态；若开发人员在会话中直接给出选择/方向，则将其写入 `analysis/direction.json`（来源标注 `session`）后继续。然后按最新状态继续；该命令对**任意中间状态**都适用（包括无人值守停下的 `patch_validated` 等）。关键节点的 A/B/C **直接在本会话内询问并等待**，不在 issue 发交互评论（issue 评论仅用于无人值守的 PR 交付场景）。

**无人值守运行的收尾规则**：非交互运行（无会话）中遇到任何需要人工选择的节点——求助、补丁完成后的下一步、验证征询等——**必须停在受监控的等待态**（`awaiting_direction`/`awaiting_verification`），不得只把问题写进日志后停在无监控的中间态（如 `patch_validated`），否则无人能接手。发布规则：默认 `pr_only`——**只有包含 PR 的交付/验证征询评论会发布到 issue**，其他决策不发布、等待开发者回到会话用“继续 <编号>”接管；`auto` 时求助评论（A/B/C）也发布；`manual` 时任何交互评论都不发布。日志只作为审计记录。

**PR 与 issue 的同步规则（硬性）**：`create-fix-pull-request` 创建或更新 PR 后，编排**必须立即执行 `draft-issue-comment` → `publish-policy-comment`**，把该 revision 的交付/验证征询评论发布到 issue（`pr_only` 下这是唯一必发的过程评论）；不得因等待构建、等待人工或其他步骤而延迟。更新已有 PR 时，评论中注明更新后的分支/提交。构建结果若后到，追加一条简短更新评论。

**人机闭环**：分析受阻（连续排查无高置信结论、证据矛盾、模型自评估无法继续）时调用 `escalate-issue` 生成带 A/B/C 的求助评论（按 `publication.interaction_comments` 可自动发布）并停在 `awaiting_direction`；开发人员的回复（选项、方向或自由文本）由 `sync-github-replies` 轮询读取，写入 `analysis/direction.json` 后带着该方向继续（`direction_received`）。交付修复后进入 `awaiting_verification`（评论含“验证征询”段落）：回复“验证通过”→ `confirmed_fixed` → `archive-case`；回复“仍有问题（附新日志/截图）”→ 归档旧 revision、`revision+1`、从 `issue_fetched` 重新分析。issue 关闭始终由人工完成。

**耗时预算（求助触发）**：同一目标（定位组件、根因或某个符号）连续探索约 **10 分钟**、或多次检索仍无进展时，必须停下调用 `escalate-issue`：列出已掌握线索、已排除项与候选方向（A/B/C），请开发人员指方向；不得无限期硬耗。外部/搜索命令一律带 `timeout`（建议 ≤300 秒）与结果上限。

构建通道只允许通过 profile `build.helper` 声明的授权助手执行：`manual`（默认）只写 `build/build-request.json` 并停在 `build_requested`，等待人工运行助手；`auto` 才可调用助手。助手在受控构建树内临时应用 patch，构建后必须回滚，不得手工修改源码、应用 diff 或运行构建命令。`build_requested` 期间不得重复构建；`build_failed` 时记录失败并停止，交由人工处理。

组件归属低置信或存在并列候选时，`resolve-manifest-components` 停在 `component_review_requested` 并写 `analysis/component-review.json`；必须由开发人员给出结论，再由 `confirm-component-mapping` 写入最终映射并沉淀到组件映射知识，然后继续。评审前不得自行猜测归属或重复检索。

恰好选择一个证据分支：结构化日志使用 `extract-log-evidence`，否则使用 `extract-text-evidence`。`draft-issue-comment` 产生 `information_request_drafted` 时，下一次编排**只能**原子地将根目录 `state.json` 的 `state` 改为 `needs_information`，保留草稿和停止原因；不得再次读取 GitHub、源码或调用其他 skill。随后停止。不得把 `information_request_drafted` 当作可重复执行的工作态。

在 `needs_information`、`blocked`、任一校验失败，或发布策略不符合门槛时停止。编排器自身不分析源码、不创建 patch 或写入评论。除经 `request-build` 或人工调用的授权构建助手外，不得修改源码、应用 patch、构建、测试、提交、推送、创建 PR 或关闭 issue。
