---
name: create-fix-pull-request
description: 当已校验的补丁建议需要以分支+合并请求（PR/MR）形式提交，供人工查看、修改与合入时使用。
---

# 创建修复 PR/MR（只创建，不合入）

仅接收 `patch_validated`，且必须由调用方在关键节点显式选择“生成 PR/MR”。全程在**独立工作区** `data/pr-work/issue-<编号>-<slug>/` 内操作；不得改动 `fde-sources` 只读树或 `fde-build` 构建树。

目标与默认值（可被 profile `pull_request` 覆盖）：

- provider：`gitlab`（默认；组件 remote 含 `src.ift.run` 等 GitLab 主机时），`github.com` 才用 `github`；
- base 分支：`fde_17`（主分支，仅作为 PR 目标，**不得合入**）；
- 分支名：`ai/issue-<编号>-<slug>`，已存在时追加 `-2`、`-3`；
- 仓库：`analysis/sources.json` 中该组件的 remote（GitLab 用 SSH 形式）。

步骤：

1. 浅克隆目标仓库到独立工作区并检出 base 分支：`git clone --depth 1 --single-branch --branch <base> <remote> <workdir>`。
2. 校验并应用补丁：先 `git apply --check <patch>`（失败即停止），再应用；用 `git status --porcelain` 核对仅补丁涉及文件变更，偏差即停止。
3. 提交（作者标注为助手）：`git -c user.name="pi-agent" -c user.email="pi-agent@openfde.local" commit -m "fix: <issue 标题> (openfde/openfde#<编号>)" -m "由 AI 助手生成的修复建议：未构建、未测试（not_run）；关联问题 openfde/openfde#<编号>。"`。
4. 推送并创建 MR（GitLab push options，不直接调用 API）：
   `git push -o merge_request.create -o merge_request.target=<base> -o merge_request.title="fix: <标题> (#<编号>)" -o merge_request.description="AI 生成的修复建议（未构建未测试），关联 openfde/openfde#<编号>；改动与验证说明见提交信息。" -o merge_request.remove_source_branch origin HEAD:refs/heads/<分支>`
   从推送输出捕获 MR 链接；无权限或服务不支持 push options 时，报告分支推送状态与 GitLab 页面链接后停止。
5. 记录 `patch/pull-request.json`：provider、project、base、branch、commit、url、created_at、`merged: false`；`state.json` 增加 `pull_request` 引用，把 `state` 推进到 `pull_request_created`。
6. 关键节点汇报：MR 链接、分支、base、diff 摘要（`git show --stat`）、未验证声明，并明确“只创建、未合入”。

禁止：合入或关闭 MR、强推、向 base 直接推送、触碰只读源码树或构建树、在 `.fde-ai/runs/` 创建产物。人工要求修改时在同一分支追加提交并说明，不得改写历史。
