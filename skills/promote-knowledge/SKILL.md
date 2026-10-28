---
name: promote-knowledge
description: 当已授权人工审核了带来源关联的项目事实，可以将其纳入索引知识 Wiki 时使用。
---

# 晋升已审核知识

接收人工批准记录和有效的提议事实。仅接受来源 case 为 `verification.verified=true` / `confirmed_fixed` 且带有 `case_id` 的提案。将已审核 Markdown 和元数据加入 `data/knowledge/wiki/`；`index.md` 不存在时用 `profiles/openfde/knowledge/wiki-index-template.md` 初始化，然后追加一行。并在 `data/knowledge/audits/promote.jsonl` 追加 `case_id`、`source_issue`、`verified_by`、`verified_at`、`stale_after` 和提案哈希。保留提议和批准引用；不得自动晋升 draft case。

没有批准或来源不完整时停止。不得推断批准、改动源码或发布到 GitHub。
