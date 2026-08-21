---
name: draft-patch
description: 当受证据约束的修复方案需要针对已知只读源码 commit 起草统一 diff 建议时使用。
---

# 起草未应用 patch

仅接收 `solution_proposed`。只创建唯一补丁 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch` 和同目录 `patch.json`，包含组件、base commit、目标路径、SHA-256、关联 claim、预期行为和 `not_run` 验证说明；`state.json` 必须引用该路径。从只读源码上下文生成建议。不得在 `.fde-ai/runs/` 创建新产物。

仅在产物存在后推进到 `patch_proposed`。不得应用 diff、改动源码/缓存、运行 `git apply`、构建、测试、提交或推送。
