---
name: escalate-issue
description: 当分析受阻或需要开发人员指方向时，生成并（按策略）发布带 A/B/C 选项的求助评论，然后停在等待态。
---

# 求助并等待方向

在分析受阻时使用：连续排查仍无高置信结论、组件归属无法确认、证据互相矛盾，或模型自评估无法继续。**不得在证据不足时硬猜根因**。

生成 `.fde-ai/issues/<issue号>/comment/escalation.md`：

- **当前进度**：已完成到哪一步（引用产物路径，如 `evidence/evidence.json`、`analysis/components.json`、`analysis/analysis.md`）；
- **已分析与已排除**：列出查过的方向与排除依据（文件:行号 / 日志时间戳 / 证据 ID）；
- **具体问题**：需要开发人员确认或补充什么；
- **A/B/C 选项**：给出 2~3 个最可能的下一步（例如 `A. 确认问题属于 XX 模块  B. 请提供 XX（含具体命令/路径）  C. 换方向：优先检查 YY`）；开发人员可自由文本回复，不必局限于选项；
- 稳定 marker：`<!-- openfde-ai:escalation issue=<编号> revision=<版本> -->`，并注明“由 AI 修复助手生成、未验证”。

发布：按 profile `publication.interaction_comments`——`auto` 且通过 `publish-policy-comment` 的去重/脱敏/认证门槛时直接 `gh issue comment` 发布；`manual` 时只保留草稿并提示人工发布。发布完成后把 `state.json` 的 `state` 推进到 `awaiting_direction` 并停止。

回复由 `sync-github-replies` 轮询读取后继续分析；不得在 `.fde-ai/runs/` 创建新产物。
