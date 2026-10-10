---
name: collect-build-artifacts
description: 当受限构建已完成并需要校验构建结果、登记产物哈希并推进到产物归档时使用。
---

# 收集构建产物

仅接收 `build_done`。读取 `.fde-ai/issues/<issue号>/build/build-result.json`，校验 profile `build.artifacts` 列出的每个输出都存在且哈希与构建记录一致，把产物引用与 `artifacts.json`（产物名称、大小、SHA-256、构建时间戳、target、modules、base commit、patch SHA-256 与日志路径）登记到 `.fde-ai/issues/<issue号>/build/`。唯一 patch 入口仍是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`，本步骤不得修改它。产物只读引用或复制均可，不得修改构建树、源码或补丁。

全部产物校验通过后推进到 `artifacts_collected`。产物缺失或哈希不匹配时停止并记录差异，不得重试构建。不得在 `.fde-ai/runs/` 创建新产物。
