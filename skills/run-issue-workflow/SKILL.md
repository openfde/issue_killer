---
name: run-issue-workflow
description: 当交互用户希望通过原子 skill 启动、恢复或检查一个已配置的 issue 分析 run 时使用。
---

# 运行单个 issue 工作流

这是一个薄编排器。开始前必须取得当前调用方显式指定的问题编号或完整 URL；人工 Pi 会话中必须来自当前用户请求，服务器模式中必须来自受信任的服务器队列。缺少指定时只返回“请选择问题”，不得创建运行目录、访问 GitHub 或下载任何内容。不得从问题列表、旧产物或上下文自行选择。

选择检查通过后，先初始化唯一目录 `.fde-ai/issues/<issue号>/` 及其 `input/`、`evidence/`、`analysis/`、`solution/`、`patch/`、`build/`、`comment/`、`archive/` 子目录，并在根目录**先写入** `state.json`：唯一状态字段名为 `state`，初始值为 `initialized`，同时记录 issue 编号、revision、profile SHA-256 与更新时间。不得使用 `status` 代替 `state`。然后加载项目配置、构建项目上下文、检查 `state.json`，恰好调用一个有效的原子 skill。该 skill 完成后重新读取并校验产物/状态；仅在调用方要求继续处理时重复。服务器协调器会对同一受信任 issue 自动发起后续调用，直到终态。任何后续技能都只可处理已明确选择的同一编号。唯一 patch 入口是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`；不得在 `.fde-ai/runs/` 创建新产物。

允许的顺序为 `load-project-profile` → `build-project-context` → `fetch-github-issue` → 一个证据分支 → `resolve-manifest-components`（低置信时经 `confirm-component-mapping` 人工确认）→ `cache-provenanced-sources` → `retrieve-knowledge` → `trace-evidence-to-source` → `verify-analysis` → `propose-fix` → 可选的 `draft-patch` / `validate-patch-artifact` → 配置了 `build` 时 `request-build` → `collect-build-artifacts` → `draft-issue-comment` → `archive-case`。

构建通道只允许通过 profile `build.helper` 声明的授权助手执行：`manual`（默认）只写 `build/build-request.json` 并停在 `build_requested`，等待人工运行助手；`auto` 才可调用助手。助手在受控构建树内临时应用 patch，构建后必须回滚，不得手工修改源码、应用 diff 或运行构建命令。`build_requested` 期间不得重复构建；`build_failed` 时记录失败并停止，交由人工处理。

组件归属低置信或存在并列候选时，`resolve-manifest-components` 停在 `component_review_requested` 并写 `analysis/component-review.json`；必须由开发人员给出结论，再由 `confirm-component-mapping` 写入最终映射并沉淀到组件映射知识，然后继续。评审前不得自行猜测归属或重复检索。

恰好选择一个证据分支：结构化日志使用 `extract-log-evidence`，否则使用 `extract-text-evidence`。`draft-issue-comment` 产生 `information_request_drafted` 时，下一次编排**只能**原子地将根目录 `state.json` 的 `state` 改为 `needs_information`，保留草稿和停止原因；不得再次读取 GitHub、源码或调用其他 skill。随后停止。不得把 `information_request_drafted` 当作可重复执行的工作态。

在 `needs_information`、`blocked`、任一校验失败，或发布策略不符合门槛时停止。编排器自身不分析源码、不创建 patch 或写入评论。除经 `request-build` 或人工调用的授权构建助手外，不得修改源码、应用 patch、构建、测试、提交、推送、创建 PR 或关闭 issue。
