---
name: list-github-issues
description: 当用户或调度器需要获取项目 profile 指定仓库的完整 GitHub issue 索引时使用。
---

# 列出 GitHub issue

接收已校验的 profile。运行 `gh auth status`，再以足够大的限制执行 `gh issue list --repo <profile.repository> --state <open|closed|all> --limit <N>`。仅在 `issue-index.json` 中保存编号、状态、标题、标签、更新时间和 URL；排除 pull request。

校验索引仓库与项目配置一致，并展示摘要供交互选择。列出后必须等待用户在新的请求中显式给出问题编号或完整 URL；不得将列表首项、最近更新项或旧选择传给获取技能。认证或读取失败即停止。不得获取正文、克隆源码、替用户选择问题或写入评论。
