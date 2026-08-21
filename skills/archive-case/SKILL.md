---
name: archive-case
description: 当 issue 分析 revision 需要不可变且关联来源的归档，以供后续审查和重建回复闭环时使用。
---

# 归档 case revision

接收已完成或已阻塞的 revision。将产物引用复制或链接到 profile 的 case archive，并在 `.fde-ai/issues/<issue号>/archive/case.json` 写入本 issue 的索引，包含 issue 快照哈希、证据、manifest/源码来源、结论、patch 建议、发布记录和用户报告的结果。唯一 patch 入口仍是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`；不得在 `.fde-ai/runs/` 创建新产物。

校验全部引用并保留旧 revision。产物缺失时停止。不得晋升知识、修改源码或写入 GitHub。
