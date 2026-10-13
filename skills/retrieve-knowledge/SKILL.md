---
name: retrieve-knowledge
description: 当源码分析 run 需要从版本化、可索引的 Markdown Wiki 获取项目知识，且不能将语义相似度当作证据时使用。
---

# 检索索引知识

接收 profile 快照、组件映射和证据词。按组件路径、manifest revision、源码 commit、状态和标签过滤 Wiki 索引，再使用 `rg` 读取匹配的 Markdown 文档。只写入 `.fde-ai/issues/<issue号>/analysis/knowledge-selection.json`，其中带文档路径、哈希和过期状态。不得在 `.fde-ai/runs/` 创建新产物。

无论是否有匹配文档，都要写入选择记录并把根目录 `state.json` 的 `state` 推进到 `knowledge_retrieved`：**没有匹配文档（知识库为空或索引不存在）是合法结果**——记录空选择与原因后继续，不得因“无知识”停止流程。仅在索引结构损坏或产物无法写入时停止。仅将检索材料作为上下文；每个结论仍须引用原始证据和源码。不得向量化、晋升事实或重写 Wiki 文件。
