---
name: verify-analysis
description: 当源码追溯分析在提出修复方案前需要确定性校验证据、组件、路径、行号、commit 与产物引用时使用。
---

# 校验分析

仅接收 `root_cause_traced`。校验每个 claim 引用的哈希、证据 ID、组件来源、精确 commit、源码路径和行范围。只写入 `.fde-ai/issues/<issue号>/analysis/analysis-validation.json`，包含失败项和过期依赖。不得在 `.fde-ai/runs/` 创建新产物。

仅在所有必需引用均校验通过时推进到 `analysis_verified`。引用缺失、过期或矛盾时停止。此步骤校验产物完整性，不校验运行时行为。
