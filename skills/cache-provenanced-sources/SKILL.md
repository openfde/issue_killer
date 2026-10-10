---
name: cache-provenanced-sources
description: 当已解析 manifest 组件需要在只读本地源码树或离线缓存中生成精确 revision 来源记录以供离线分析时使用。
---

# 缓存带来源记录的源码

仅接收 `manifest_resolved`。按 profile `sources.mode` 选择来源方式：

- `local_tree`：不克隆、不拉取。在 profile `sources.path` 指向的只读本地树中，为每个已映射组件定位本地路径，并使用 `git -C <组件路径> rev-parse HEAD` 与 `git -C <组件路径> status --porcelain` 校验：工作区必须干净，且解析出的 commit 与 manifest 请求的 revision 一致；revision 为分支或标签时记录其解析到的 commit。AOSP repo 检出中每个组件目录自身即 git 仓库，不得假设树根是单一仓库。
- 其他模式：复用干净且兼容的 checkout，或仅获取已映射组件的精确 manifest revision。

只写入 `.fde-ai/issues/<issue号>/analysis/sources.json`，逐组件记录 remote、请求 revision、解析后的 commit、本地路径（逻辑路径与容器内绝对路径）和内容哈希。不得在 `.fde-ai/runs/` 创建新产物或复制源码到 issue 目录。

验证每个来源对分析 agent 均为干净只读，然后推进到 `sources_fetched`。本地树缺失、工作区脏、revision 不匹配或来源不一致时停止。不得改动 checkout、应用 diff、构建、测试、提交或推送。
