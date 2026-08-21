---
name: cache-provenanced-sources
description: 当已解析 manifest 组件需要带精确 revision 来源记录的本地只读源码副本以供离线分析时使用。
---

# 缓存带来源记录的源码

仅接收 `manifest_resolved`。复用干净且兼容的 checkout，或仅获取已映射组件的精确 manifest revision。源码只可位于 `.fde-ai/sources/`；在 `.fde-ai/issues/<issue号>/analysis/sources.json` 中记录 remote、请求 revision、解析后的 commit、缓存路径和内容哈希。不得在 `.fde-ai/runs/` 创建新产物或复制源码到 issue 目录。

验证每个缓存对分析 agent 均为干净只读，然后推进到 `sources_fetched`。克隆、revision 或来源不匹配时停止。不得改动 checkout、应用 diff、构建、测试、提交或推送。
