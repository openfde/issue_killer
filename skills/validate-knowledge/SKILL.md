---
name: validate-knowledge
description: 当索引 Markdown 知识必须检查来源、schema 有效性、精确源码 revision 和过期条目时使用。
---

# 校验知识

读取每个选定的知识文档和索引项。校验必填 YAML 字段、引用的 case ID、源码 commits 和 manifest revisions。引用 revision 不再匹配当前映射时，将事实标记为 stale；写入 `knowledge-validation.json`。

不得使用向量搜索、静默重写 claim、晋升未经审核的内容、修改源码或发布评论。
