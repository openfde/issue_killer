---
name: publish-policy-comment
description: 当 GitHub issue 评论草稿符合策略门槛可以发布，或配置的交互评论策略允许自动发布时使用。
---

# 按策略发布评论

仅接收评论草稿和 profile 发布策略。任何写入前，校验目标仓库、marker 去重、脱敏结果、标签、限额、停用文件、认证、所需置信度和 `no_internal_paths`（正文与落款不含 `.fde-ai/`、`data/` 等内部产物路径及“分析产物”字样，marker 除外，落款为固定文案）。patch 建议必须包含明确的未验证声明和 `not_run` 列表。

**交互评论发布策略（`publication.interaction_comments`）**：

- `auto`：求助（`openfde-ai:escalation` marker）与交付/验证征询评论都可自动发布；
- `pr_only`（默认）：**只有包含 PR/MR 链接的修复交付/验证征询评论**可自动发布；求助类交互评论**不发布**（只停在等待态，由交互会话接管）；
- `manual`：全部不自动发布，仅保留草稿。

**分析选项征询评论（`analysis-options`）**：用于“无法立即修复”的 issue——正文含完整原因链与修复选项 A/B/C，请开发人员选择。当 `publication.analysis_options_comment="auto"` 时允许发布（不受 `pr_only` 限制），发布后把状态推进到 `awaiting_direction`；`manual` 时只保留草稿。`dry_run=true` 时仍须人工确认后才发布。该评论允许包含 medium 置信的推断，但必须逐项标注置信度与“推断，未证实”及验证方法，不得把推断写成结论。

其余评论仍遵循 `dry_run`/人工确认路径。发布成功后按草稿类型推进状态：交付/验证征询 → `awaiting_verification`；求助（仅 `auto`）→ `awaiting_direction`；分析选项征询 → `awaiting_direction`；缺失信息请求 → `needs_information`。

仅使用 `gh issue comment <number> --repo <repository> --body-file <草稿路径>`。在 `publication.json` 中保存命令结果、URL、marker 和哈希；重新读取 marker。发布成功后按草稿类型推进状态：求助 → `awaiting_direction`；修复交付/验证征询 → `awaiting_verification`；缺失信息请求 → `needs_information`。任一门槛失败时保留草稿并停止。不得修改源码、推送、创建 PR 或关闭 issue。
