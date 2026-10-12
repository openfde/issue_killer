---
name: confirm-component-mapping
description: 当组件归属停在 component_review_requested 且开发人员给出确认或纠正时使用。
---

# 确认组件映射

仅接收 `component_review_requested`，且必须由人工显式给出结论：确认某个候选，或指定其他组件路径/项目。不得替人工推断，也不得再次检索猜测。

把确认结果写入 `.fde-ai/issues/<issue号>/analysis/components.json`（最终映射，标注依据 `human`；保留原候选记录），并把本次纠正追加到 `data/knowledge/component-map/entries.md`：选择最合适的 `kind`、`source: human`、`confidence: high`、`last_validated` 为当天、notes 记录来源 issue 与原因；同键旧条目保留优先级规则（学习条目优先）。

随后把根目录 `state.json` 推进到 `manifest_resolved`。人工表示“无法确认/需要更多信息”时，只在 `analysis/component-review.json` 记录结论并停止，不推进状态、不写知识库。不得在 `.fde-ai/runs/` 创建新产物。
