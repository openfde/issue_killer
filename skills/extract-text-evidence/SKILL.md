---
name: extract-text-evidence
description: 当已获取 issue 没有结构化诊断日志附件，但正文或评论可能包含技术故障证据时使用。
---

# 提取讨论证据

仅接收无结构化日志附件的 `issue_fetched`。从 `input/issue.json` 与 `input/comments.json` 提取受限技术陈述，只写入 `.fde-ai/issues/<issue号>/evidence/` 的摘录和共享 `evidence.json` schema。保留来源 `issue` 或 `comment:<id>`、行范围与 SHA-256。不得在 `.fde-ai/runs/` 创建新产物。

仅在存在技术证据时推进到 `evidence_extracted`。否则创建缺失信息记录，只请求版本、宿主机/设备上下文、复现步骤和相关日志。不得推断原因或执行源码工作。
