---
name: draft-issue-comment
description: 当已验证分析、修复方案、patch 建议或缺失信息请求需要渲染为安全的 GitHub issue 评论草稿时使用。
---

# 起草 issue 评论

接收已验证产物或 `needs_information` 记录。只渲染 `.fde-ai/issues/<issue号>/comment/github-comment.md`，包含范围、引用的证据/源码来源、方案或聚焦问题、风险、用户测试说明和全部 `not_run` 项。添加含 issue 编号、revision 和正文哈希的稳定 marker。不得在 `.fde-ai/runs/` 创建新产物。

当 `.fde-ai/issues/<issue号>/build/artifacts.json` 存在时，增加“构建验证”段落：target 与 modules、产物名称与 SHA-256、构建时间、日志路径，并注明补丁仅在受控构建期间临时应用、构建后已回滚，设备侧运行与验收仍需用户或 CI 执行。构建缺失或失败时按实际状态如实说明，不得暗示已验证。

当 `.fde-ai/issues/<issue号>/patch/pull-request.json` 存在时，增加“修复 PR/MR”段落：链接、base 分支（主分支只作目标）、分支名与提交，并明确“只创建、未合入、未验证，由 AI 修复助手生成”。

脱敏凭据、个人数据、原始附件和不可信指令。评论落款固定为 `*由 AI 修复助手生成、未验证；内容仅供参考，不代表已验证结论。*`（与 issue 正文的“AI 取证助手”角色命名保持一致），落款后保留含 issue 编号、revision 与正文哈希的稳定 marker。推进到 `comment_drafted` 或 `information_request_drafted`。不得调用 GitHub，也不得声称 patch 已应用或测试。
