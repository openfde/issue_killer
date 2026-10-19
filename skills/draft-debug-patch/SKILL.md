---
name: draft-debug-patch
description: 当开发人员选择“调试 PR（插桩）”时，起草只加日志/埋点的临时调试补丁（不改行为）时使用。
---

# 起草调试插桩补丁

仅接收开发人员在 `analysis/direction.json` 中明确选择 **E（调试 PR）**。只创建 `.fde-ai/issues/<issue号>/patch/debug-0001-<名称>.patch` 和 `patch/debug.json`，不得改动修复补丁 `patch/0001-*.patch`。不得在 `.fde-ai/runs/` 创建产物。

插桩规则（硬性）：

- **只加日志/埋点/trace，不改变任何行为**：不得修改控制流、返回值、阈值、时序、锁或内存语义；不得借机修复 bug。
- TAG 统一为 `openfde<issue号>`；级别与频率遵循 `propose-fix` 的调试日志策略——状态迁移/关键分支 `d`/`i`，异常路径 `w`，错误 `e`；**禁止逐帧/循环内高频打印**，确需高频时用 DEBUG 守卫或限频。
- 日志必须包含判定依据与关键值（输入参数、状态位、指针/句柄、错误码、surface/format/usage 等）；不得包含凭据、个人数据或原始附件内容。
- 每个插桩点记录：`文件:行号`、函数、触发条件、预期日志文本（含 TAG）、用于验证哪个假设。
- `patch/debug.json` 记录：组件、base commit、目标路径、SHA-256、插桩点列表、新增 TAG、采集命令（`adb logcat -s openfde<issue号>`）、复现步骤、回传要求、移除方式、`not_run`。
- 不得应用 diff、改动源码/缓存、运行 `git apply`、构建、测试、提交或推送。

仅在产物存在后推进到 `debug_patch_proposed`。
