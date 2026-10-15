---
name: create-fix-pull-request
description: 当已校验的补丁建议需要以分支+PR 形式提交到 GitHub，供人工查看、修改与合入时使用。
---

# 创建修复 PR（只创建，不合入）

仅接收 `patch_validated`，且必须由调用方在关键节点显式选择“生成 PR”。全程在**独立工作区** `data/pr-work/issue-<编号>-<slug>/` 内操作；不得改动 `fde-sources` 只读树或 `fde-build` 构建树。

目标与默认值（可被 profile `pull_request` 覆盖）：

- provider：`github`（AOSP 定制项目已迁移至 GitHub org `openfde`）；
- 仓库：按清单项目名拼装 `https://github.com/openfde/<项目名>.git`（如 `packages_apps_TaskPlugin`）；
- base 分支：`fde_17`（主分支，仅作为 PR 目标，**不得合入**）；
- 分支名：`ai/issue-<编号>-<slug>`，已存在时追加 `-2`、`-3`，不强推、不覆盖。

步骤：

1. 浅克隆目标仓库到独立工作区并检出 base：`git clone --depth 1 --single-branch --branch <base> https://github.com/openfde/<项目名>.git <workdir>`（HTTPS 凭据由已配置的 `gh auth setup-git` 提供）。
2. 校验并应用补丁：先 `git apply --check <patch>`（失败即停止），再应用；用 `git status --porcelain` 核对仅补丁涉及文件变更，偏差即停止。
3. 提交（作者标注为助手）：`git -c user.name="pi-agent" -c user.email="pi-agent@openfde.local" commit -m "fix: <issue 标题> (openfde/openfde#<编号>)" -m "由 AI 修复助手生成的修复建议：未构建、未测试（not_run）；关联问题 openfde/openfde#<编号>。"`。
4. 推送分支：`git push origin HEAD:refs/heads/<分支>`。
5. 创建 PR（gh 已登录）：`gh pr create --repo openfde/<项目名> --base <base> --head <分支> --title "fix: <标题> (#<编号>)" --body-file <说明文件>`；说明文件由 `solution/solution.md` 摘要生成，开头与结尾均须注明“由 AI 修复助手生成、未构建未测试（not_run）、未合入”。从输出捕获 PR 链接；推送或创建失败时报告分支状态与 GitHub 页面链接后停止。
6. 记录 `patch/pull-request.json`：provider、repo、base、branch、commit、url、created_at、`merged: false`；`state.json` 增加 `pull_request` 引用，把 `state` 推进到 `pull_request_created`。
7. 关键节点汇报：PR 链接、分支、base、diff 摘要（`git show --stat`）、未验证声明，并明确“只创建、未合入”。

禁止：合入或关闭 PR、强推、向 base 直接推送、触碰只读源码树或构建树、在 `.fde-ai/runs/` 创建产物。人工要求修改时在同一分支追加提交并推送说明，不得改写历史。
