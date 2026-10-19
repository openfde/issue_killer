---
name: create-debug-pull-request
description: 当调试插桩补丁已起草且开发人员选择创建调试 PR 时，把它以 ai-debug/ 分支和 PR 形式提交（只创建、不合入）时使用。
---

# 创建调试 PR（只创建，不合入）

仅接收 `debug_patch_proposed`，且开发人员已在 `analysis/direction.json` 明确选择 **E（调试 PR）**。沿用 `create-fix-pull-request` 的工作区与安全规则：每个项目在独立工作区 `data/pr-work/issue-<编号>-debug-<项目名>-<slug>/` 内操作；不得改动 `fde-sources` 只读树或 `fde-build` 构建树。

目标与默认值（可被 profile `debug_pull_request` 覆盖）：

- provider：`github`；仓库按清单项目名拼装 `https://github.com/openfde/<项目名>.git`；
- base 分支：`fde_17`（**不得合入**）；
- 分支名：`ai-debug/issue-<编号>-<slug>`，已存在时追加 `-2`、`-3`，不强推、不覆盖；
- 多项目时按项目分别创建 PR，每个项目一个，并附全部链接。

步骤（多项目时逐个项目执行）：

1. 浅克隆目标仓库并检出 base；从 `debug-0001-*.patch` 拆分出该项目片段，`git apply --check` 通过后应用，核对仅插桩文件变更。
2. 提交：`git -c user.name="pi-agent" -c user.email="pi-agent@openfde.local" commit -m "[debug] issue #<编号>: <标题>" -m "仅插桩日志/埋点，不改变行为；临时调试用途，不得合入；采集证据后移除。"`。
3. 推送分支并创建 PR：`gh pr create --repo openfde/<项目名> --base fde_17 --head <分支> --title "[debug] issue #<编号>: <标题>" --body-file <说明文件>`。PR 说明必须包含：**仅插桩、不改行为、临时、不得合入、采集后关闭/删除分支**、插桩点与 TAG、复现与采集命令、回传要求、`not_run`；不得写出 `.fde-ai/`、`data/` 等内部产物路径或“分析产物”字样。
4. 记录 `patch/pull-request.json`：`kind: "debug"`、`instrumentation_only: true`、`pull_requests` 数组（repo/base/branch/commit/url/created_at/`merged: false`）、插桩点与 TAG；`state.json` 引用并推进到 `debug_pull_request_created`。

**与 issue 的同步（硬性）**：调试 PR 创建或更新完成后，必须立即继续 `draft-issue-comment` → `publish-policy-comment`，发布调试说明评论（marker `openfde-ai:debug-pr`），包含全部 PR 链接、插桩点/TAG、复现与采集命令（`adb logcat -s openfde<编号>`）、回传要求、移除方式；该评论**不是**修复交付，不得要求“验证通过”。发布后停在 `awaiting_direction` 等待调试日志。

禁止：合入或关闭 PR、强推、向 base 直接推送、触碰只读源码树或构建树、在 `.fde-ai/runs/` 创建产物、把调试插桩伪装成修复。当前 `build.enabled=false` 时不得调用构建助手，调试镜像由开发自行构建/刷机。
