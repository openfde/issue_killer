---
name: validate-knowledge
description: 当索引 Markdown 知识必须检查来源、schema 有效性、精确源码 revision 和过期条目时使用。
---

# 校验知识

读取每个选定的知识文档、索引项和 `data/knowledge/cases/<issue>/case.json`。校验必填字段、`case_id`、来源哈希、`verification.verified` 与 `knowledge_status` 一致性、源码 commits 和 manifest revisions。引用 revision 不再匹配当前映射时，将事实标记为 stale；写入 `knowledge-validation.json`。`draft` case 不得被当作已验证事实；缺少来源或哈希时报告并停止晋升，不静默修复。

不得使用向量搜索、静默重写 claim、晋升未经审核的内容、修改源码或发布评论。
