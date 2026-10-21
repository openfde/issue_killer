---
name: create-fix-pull-request
description: 当已校验的补丁建议需要以分支+PR 形式提交到 GitHub，供人工查看、修改与合入时使用。
---

# 创建修复 PR（只创建，不合入）

仅接收 `patch_validated`，且必须由调用方在关键节点显式选择“生成 PR”。先按组件映射把补丁的目标文件归入项目：**只有一个项目时生成一个 PR；涉及多个项目时，按项目分别生成 PR（每个项目一个），并在汇报与评论中附上全部 PR 链接**。每个项目在独立工作区 `data/pr-work/issue-<编号>-<项目名>-<slug>/` 内操作；不得改动 `fde-sources` 只读树或 `fde-build` 构建树。

目标与默认值（可被 profile `pull_request` 覆盖）：

- provider：`github`（AOSP 定制项目已迁移至 GitHub org `openfde`）；
- 仓库：按清单项目名拼装 `https://github.com/openfde/<项目名>.git`（如 `packages_apps_TaskPlugin`）；
- base 分支：`fde_17`（主分支，仅作为 PR 目标，**不得合入**）；
- 分支名：`ai/issue-<编号>-<slug>`，已存在时追加 `-2`、`-3`，不强推、不覆盖。

步骤（多项目时对每个项目各执行一遍）：

1. 浅克隆目标仓库到独立工作区并检出 base：`git clone --depth 1 --single-branch --branch <base> https://github.com/openfde/<项目名>.git <workdir>`（HTTPS 凭据由已配置的 `gh auth setup-git` 提供）。
2. 生成该项目补丁片段：单项目即规范 patch 本身，多项目时从规范 patch 中拆分出仅属于该项目的文件/hunk；片段只作工作区中间文件。先 `git apply --check <片段>`（失败即停止），再应用；用 `git status --porcelain` 核对仅片段涉及文件变更，偏差即停止。
3. 提交（作者标注为助手）：`git -c user.name="pi-agent" -c user.email="pi-agent@openfde.local" commit -m "fix: <issue 标题> (openfde/openfde#<编号>)" -m "由 AI 修复助手生成的修复建议：未构建、未测试（not_run）；关联问题 openfde/openfde#<编号>。"`。
4. 推送分支：`git push origin HEAD:refs/heads/<分支>`。
5. 创建 PR（gh 已登录）：`gh pr create --repo openfde/<项目名> --base <base> --head <分支> --title "fix: <标题> (#<编号>)" --body-file <说明文件>`；说明文件由 `solution/solution.md` + 当前补丁生成，必须包含：根因（证据/源码行号）、修改（至少当前 patch 的关键 hunk，使用统一 diff（```diff）代码块；不得只给摘要或文件名）、预期行为、风险、`not_run`、验证建议；多项目时每个 PR 只放该项目片段。开头与结尾均须注明“由 AI 修复助手生成、未构建未测试（not_run）、未合入”，结尾固定为 `*由 AI 修复助手生成、未构建未测试（not_run）、未合入；内容仅供参考。*`；**PR 说明不得写出 `.fde-ai/`、`data/` 等内部产物路径，不得出现“分析产物”字样**；若补丁新增调试日志，列出新增 TAG 与复测用 `adb logcat -s <TAG>` 过滤命令。从输出捕获 PR 链接；推送或创建失败时报告已处理项目的分支状态与页面链接，并停止剩余项目。
6. 全部项目完成后记录 `patch/pull-request.json`：`pull_requests` 数组，每项含 provider、repo、base、branch、commit、url、created_at、`merged: false` 与该项目补丁片段引用；单项目时数组也恰好一项。`state.json` 增加 `pull_request` 引用（单项目为对象、多项目为数组），把 `state` 推进到 `pull_request_created`。
7. 关键节点汇报：**逐行列出全部 PR 链接（项目 → 链接、分支、base）**；单项目只给一个链接。附各项目 diff 摘要（`git show --stat`）与未验证声明，并明确“只创建、未合入”。

禁止：合入或关闭 PR、强推、向 base 直接推送、触碰只读源码树或构建树、在 `.fde-ai/runs/` 创建产物、在 PR 说明中暴露内部产物路径或写出“分析产物”。人工要求修改时在同一分支追加提交并推送说明，不得改写历史。

**与 issue 的同步（硬性）**：PR 创建或更新完成后，必须立即继续 `draft-issue-comment` → `publish-policy-comment`，把该 revision 的交付/验证征询评论发布到 issue（`pr_only` 下这是唯一必发的过程评论；交互会话模式同样必须发布）；不得因等待构建或其他步骤而延迟。更新已有 PR 时，评论注明更新后的分支/提交；构建结果若后到，另行追加简短更新评论。
