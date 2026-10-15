---
name: publish-policy-comment
description: 当 GitHub issue 评论草稿符合策略门槛可以发布，或配置的交互评论策略允许自动发布时使用。
---

# 按策略发布评论

仅接收评论草稿和 profile 发布策略。任何写入前，校验目标仓库、marker 去重、脱敏结果、标签、限额、停用文件、认证和所需置信度。patch 建议必须包含明确的未验证声明和 `not_run` 列表。

**交互评论自动发布**：草稿带 `openfde-ai:escalation` marker（求助），或属于“修复交付/验证征询”（含 PR/MR 链接或验证征询段落）时，若 profile `publication.interaction_comments=auto` 且全部门槛通过，可直接发布；其余评论仍遵循 `dry_run`/人工确认路径。

仅使用 `gh issue comment <number> --repo <repository> --body-file <草稿路径>`。在 `publication.json` 中保存命令结果、URL、marker 和哈希；重新读取 marker。发布成功后按草稿类型推进状态：求助 → `awaiting_direction`；修复交付/验证征询 → `awaiting_verification`；缺失信息请求 → `needs_information`。任一门槛失败时保留草稿并停止。不得修改源码、推送、创建 PR 或关闭 issue。
