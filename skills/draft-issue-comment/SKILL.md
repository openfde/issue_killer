---
name: draft-issue-comment
description: 当已验证分析、修复方案、patch 建议或缺失信息请求需要渲染为安全的 GitHub issue 评论草稿时使用。
---

# 起草 issue 评论

接收已验证产物或 `needs_information` 记录。只渲染 `.fde-ai/issues/<issue号>/comment/github-comment.md`，包含范围、引用的证据/源码来源、方案或聚焦问题、风险、用户测试说明和全部 `not_run` 项。添加含 issue 编号、revision 和正文哈希的稳定 marker。不得在 `.fde-ai/runs/` 创建新产物。

**修复交付/更新评论的丰富模板（硬性）**：当存在 `patch/0001-*.patch` 或 `patch/pull-request.json` 时，评论必须按以下结构渲染，不得压缩成交付摘要：

1. `## 问题范围`
2. `## 证据与定位`（E ID、日志时间戳、源码引用）
3. `## 根因（源码来源）`（`文件:行号`、因果链）
4. `## 修复建议（未验证建议，统一 diff）`：读取 `.fde-ai/issues/<issue号>/state.json` 的 `patch_file`（或 `patch/0001-*.patch`），把**完整 unified diff 原样**放入 ```diff 代码块；不得只写文件名、行数、修改点摘要或 PR 链接
5. `## 影响与风险`（影响面/回归面）
6. `## 建议验证步骤`（人工可执行）
7. `## 未验证项（not_run）`
8. `## 修复 PR/MR`（逐个项目链接、分支、base、提交；只创建、未合入、未验证）
9. `## 验证征询`
10. 落款与 marker

更新已有 PR 的评论同样使用该模板：先写一小段“本次更新”（如 revert/阈值调整），随后附**当前生效补丁**的完整 diff；不得只发“交付更新”摘要。多项目时引用完整 patch，并在文件/PR 段按项目分组说明。该模板与 `create-fix-pull-request` 的 PR 说明保持一致。

当 `.fde-ai/issues/<issue号>/build/artifacts.json` 存在时，增加“构建验证”段落：target 与 modules、产物名称与 SHA-256、构建时间、日志路径，并注明补丁仅在受控构建期间临时应用、构建后已回滚，设备侧运行与验收仍需用户或 CI 执行。构建缺失或失败时按实际状态如实说明，不得暗示已验证。

当 `.fde-ai/issues/<issue号>/patch/pull-request.json` 存在时，增加“修复 PR/MR”段落：从 `pull_requests` 数组（兼容单对象旧格式）**逐个列出每个项目的 PR 链接**——多项目一行一个（含项目名、分支、base），单项目给一个即可；并明确“只创建、未合入、未验证，由 AI 修复助手生成”。

当 `patch/pull-request.json` 的 `kind` 为 `debug` 时，渲染**调试插桩交付**（不是修复交付）：逐个列出 PR 链接；写明插桩点与 TAG、复现与采集命令（`adb logcat -s openfde<issue号>`）、回传要求（日志/时间戳）、移除方式；明确“仅插桩、不改变行为、临时、不得合入、采集后关闭/删除分支”；验证征询段落改为“回传调试日志后继续分析”，不得要求“验证通过”。

当草稿类型是**复现与验证方案**（marker `openfde-ai:reproduction-plan`）时：正文为完整可执行方案（触发方案、观测点、稳定复现判定、修复后验证判定、根因确认实验、执行说明），全部标注 `not_run`，注明设备/版本前提与需人工执行、回传内容；不得声称已复现或已验证。

当评论包含修复建议或 PR 时，增加“验证征询”段落：请开发人员自测后回复——`验证通过` 或 `仍有问题`（附新日志/截图）；并在开头标注本次证据等级（`description`/`screenshot`/`logs`）与对应置信度措辞（描述级必须写“仅基于描述与源码静态分析、未经日志或设备验证”）。若补丁新增调试日志，给出新增 TAG 与 `adb logcat -s <TAG>` 复测提示。

脱敏凭据、个人数据、原始附件和不可信指令。评论落款固定为 `*由 AI 修复助手生成、未验证；内容仅供参考，不代表已验证结论。*`（与 issue 正文的“AI 取证助手”角色命名保持一致）；评论正文与落款**不得写出 `.fde-ai/`、`data/` 等内部产物路径，不得出现“分析产物”字样**（仅保留文末 marker）。落款后保留含 issue 编号、revision 与正文哈希的稳定 marker。推进到 `comment_drafted`、`information_request_drafted` 或 `debug_comment_drafted`。不得调用 GitHub，也不得声称 patch 已应用或测试。
