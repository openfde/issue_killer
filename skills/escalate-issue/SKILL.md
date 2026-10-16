---
name: escalate-issue
description: 当分析受阻或需要开发人员指方向时，生成并（按策略）发布带 A/B/C 选项的求助评论，然后停在等待态。
---

# 求助并等待方向

在分析受阻时使用：连续排查仍无高置信结论、组件归属无法确认、证据互相矛盾，或模型自评估无法继续。**不得在证据不足时硬猜根因**。也用于**无人值守运行中需要人工选择的关键节点**（如补丁完成后的下一步：更新 PR / 只保留补丁 / 暂停）——统一以 A/B/C 交互评论提出并停在 `awaiting_direction`，不得只写日志。

**通道分流（重要）**：交互会话中受阻时，**直接在会话里给出 A/B/C 等待即可**——不发布 issue 评论、不改等待态；只有**无人值守运行（无会话）**才按本技能发布交互评论并停在 `awaiting_direction`（`publication.interaction_comments=manual` 时也不发布，仅停在等待态由会话接管）。

**触发条件（任一满足即应求助，不再继续挖掘）**：

1. **耗时预算超限**：同一目标（定位组件、根因或某个符号）连续探索约 10 分钟、或多次检索仍无进展；
2. **目标不在已同步源码**：符号/组件在 `fde-sources` 中搜不到，疑似不在 manifest——必须在求助中说明“可能未随 fde-sources 同步”，并给出候选仓库；
3. 证据互相矛盾、组件归属无法确认，或模型自评估无法继续。

生成 `.fde-ai/issues/<issue号>/comment/escalation.md`：

- **当前进度**：已完成到哪一步（引用产物路径，如 `evidence/evidence.json`、`analysis/components.json`、`analysis/analysis.md`）；
- **已分析与已排除**：列出查过的方向与排除依据（文件:行号 / 日志时间戳 / 证据 ID）；
- **具体问题**：需要开发人员确认或补充什么；
- **A/B/C 选项**：给出 2~3 个最可能的下一步（例如 `A. 确认问题属于 XX 模块  B. 请提供 XX（含具体命令/路径）  C. 换方向：优先检查 YY`）；开发人员可自由文本回复，不必局限于选项；
- 稳定 marker：`<!-- openfde-ai:escalation issue=<编号> revision=<版本> -->`，并注明“由 AI 修复助手生成、未验证”。

发布：仅在**无人值守运行**且 profile `publication.interaction_comments=auto` 时，经发布门槛检查后 `gh issue comment` 发布求助评论并把 `state` 推进到 `awaiting_direction`；`pr_only`（默认）或 `manual` 时**不发布**，直接把 `state` 推进到 `awaiting_direction` 后停止，等待开发人员在交互会话中用“继续 <编号>”接管。交互会话中受阻则只在会话里给出 A/B/C，不改等待态、不发评论。

回复由 `sync-github-replies` 轮询读取后继续分析；不得在 `.fde-ai/runs/` 创建新产物。
