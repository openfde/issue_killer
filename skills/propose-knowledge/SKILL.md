---
name: propose-knowledge
description: 当已归档 case 包含可复用且适用范围明确的项目事实，需要准备给人工审核知识库时使用。
---

# 提议知识条目

接收已归档 case（优先 `data/knowledge/cases/<issue号>/case.json`）。仅接受 `verification.verified=true` 或状态 `confirmed_fixed` 的 case；`draft` case 只能提示补充验证，不能生成候选事实。创建候选 Markdown 事实，YAML 元数据包含组件路径、manifest revision、源码 commits、`case_id`、来源 issue、标签、状态、验证时间、`verified_by` 和 `stale_after`。将每条陈述关联到其证据/源码/case 来源，并说明适用范围。

将候选项标记为 `proposed`；不得加入活动 Wiki 索引，也不得将其表示为当前项目事实。
