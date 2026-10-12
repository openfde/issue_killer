---
name: trace-evidence-to-source
description: 当证据、组件映射和只读缓存源码已具备，可以进行源码级因果分析时使用。
---

# 将证据追溯到源码

仅接收 `sources_fetched` 或 `knowledge_retrieved`（编排顺序为 cache-provenanced-sources → retrieve-knowledge → 本步骤）。只写入 `.fde-ai/issues/<issue号>/analysis/analysis.md` 与 `analysis.json`。每个 claim 必须关联证据 ID、组件路径、精确源码 commit、源码文件、行号、支撑陈述和置信度。将未证明的替代解释标记为假设。不得在 `.fde-ai/runs/` 创建新产物。

仅在全部 claim 引用都能在本地解析时推进到 `root_cause_traced`。不存在证据到源码链时停止并请求信息。不得修改源码，也不得将未经验证的假设称为修复。
