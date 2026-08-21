---
name: propose-fix
description: 当已验证的源码分析在起草任何 patch 产物前需要形成受证据约束的修复建议时使用。
---

# 提出修复建议

仅接收 `analysis_verified`。只创建 `.fde-ai/issues/<issue号>/solution/solution.md` 和 `solution.json`，包含推荐与替代方案、关联 claim ID、受影响组件/文件、风险、预期行为，以及标记为 `not_run` 的用户/CI 验证建议。不得在 `.fde-ai/runs/` 创建新产物。

推进到 `solution_proposed`。建议无法关联已验证 claim 时停止。不得编辑工作副本、声称已修复或运行验证命令。
