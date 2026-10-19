---
name: design-reproduction-plan
description: 当问题偶现、仅凭代码逻辑无法确认根因时，需要设计可稳定复现与修复后验证的方案（含根因确认实验）时使用。
---

# 设计复现与验证方案

用于偶现/难以从代码确认的问题。**只产出方案与脚本，不自行在设备上执行交互操作**（输入注入、改设置等属写操作，需人工执行；只读采集仍走 `collect-device-evidence` 的通道与确认门）。

产物：`.fde-ai/issues/<issue号>/analysis/reproduction-plan.md`（可附 `scripts/` 下可复制脚本，放在 issue 目录内并说明用途）。不得在 `.fde-ai/runs/` 创建产物。

方案必须包含：

1. **触发方案（按侵入程度分档）**
   - **无侵入**：`adb shell input tap/swipe/keyevent` 循环脚本 + 并发/时序压力（例如快速切换 dock 缩略图与桌面应用、重复 N 次），脚本注明设备与版本前提；
   - **轻插桩**：在关键路径加调试日志（tag、DEBUG 开关；级别/频率遵循 `propose-fix` 的日志规则）、放宽阈值/缩短超时以提高复现率；
   - **深插桩（需构建）**：断言/trace、perfetto/systrace、关键状态快照；注明需要人工开启构建通道（`build.enabled=true`）。
2. **观测点**：目标 crash 签名（引用 issue 中的原始签名，如 `drawRenderNode called on a context with no surface!`）、`logcat -b crash`、tombstone/dropbox、关键 tag（如 `openfde<issue号>`）、SurfaceFlinger/hwcomposer 相关日志。
3. **稳定复现判定**：脚本命令、次数 N（按偶现率估算并给出依据）、判定标准“N 次内出现 ≥1 次目标签名”，并记录每次时间戳。
4. **修复后验证判定**：同一脚本 N 次运行 0 次目标签名 + 相关错误日志消失；给出通过/不通过标准与记录方式。
5. **根因确认实验（关键）**：列出 2~3 个可区分的假设与对应实验（如“仅当 X 条件成立才复现”“禁用 Y 后不复现”），逐条说明实验结果对假设的支持/排除关系，确保代码逻辑无法完全确认时仍能通过实验定位根因。
6. **执行说明**：哪些步骤需人工/测试人员执行、预计耗时、设备与版本要求、风险（可能触发更多 crash，但只读日志采集不受影响）。

推进：完成后把 `state` 推进到 `reproduction_plan_ready`；该方案供人工执行，后续 `propose-fix` 应引用其中的验证判定。

边界：不得声称已复现或已验证（全部 `not_run`）；不得改源码；不得在设备上执行交互命令；需要构建时只提示开启构建通道；不得发布评论。
