---
name: request-build
description: 当已校验的 patch 建议需要按项目构建配置请求一次受限构建并记录请求或结果时使用。
---

# 请求受限构建

仅接收 `patch_validated`，且**仅当 profile `build.enabled=true` 时使用**（构建通道默认关闭；L0-L2 调试期间不得进入）。只读取 profile 的 `build` 配置和唯一补丁入口 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch` 及其 `patch.json`；不得手工修改源码、手工应用 diff 或手工运行构建命令。不得在 `.fde-ai/runs/` 创建新产物。

先写 `.fde-ai/issues/<issue号>/build/build-request.json`：issue 编号、revision、patch 路径与 SHA-256、base commit、`target`、`modules`、构建树与输出目录逻辑路径、`artifacts` 列表、助手命令和触发模式。随后按 `build.mode` 分支：

- `manual`（默认）：将 `state.json` 推进到 `build_requested` 后停止，并告知调用方运行 profile `build.helper` 声明的授权助手（`deploy/server/fde-ai-build.sh --issue <issue号>`）完成构建。不得自行执行构建。
- `auto`：仅允许通过授权助手执行一次构建；助手内部负责加锁（`build.lock` 与 `.siso_lock` 检查）、临时应用 patch、构建、收集结果、回滚 patch 并写出 `build/build-result.json`。按结果推进到 `build_done` 或 `build_failed`。

任何情况下都不得把补丁留在构建树中；`build_failed` 时记录原因并停止，不自动重试。不得在 `.fde-ai/runs/` 创建新产物。
