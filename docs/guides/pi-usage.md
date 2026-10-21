# OpenFDE 问题工作流 — Pi 使用指南

## 准备

在项目根目录启动 Pi。**技能更新后必须退出并新开会话**（`pi`，不要 `pi -c`；旧会话不会换掉已注入的技能文本，直接用“继续”会沿用旧流程）；启动后用 `/skill:...` 调用项目技能，Pi 会发现当前项目 `.pi/skills/` 中的通用技能。

```sh
cd /you/project/path/to/fde-ai-assistant
pi
```

所有 GitHub 读取和评论都由所有智能体共用的 `gh` 命令行工具执行。首次使用前在本机完成 `gh auth login -h github.com`；Docker 部署必须显式传入 `GH_TOKEN`（创建与权限见 [README 4.2](../../README.md#42-凭据与模型)）。不要把令牌写入项目配置、问题产物或提示词。

本项目选用的项目配置是 `profiles/openfde/profile.json`。它提供仓库、Android repo XML 清单、产物目录和发布策略；它不包含问题内容或凭据。

## 命令行入口

本项目有两个不同的命令行入口，不能混用：

| 场景 | 入口 | 作用 |
| --- | --- | --- |
| 人工、交互式分析 | `pi` | 启动 Pi 后，通过 `/skill:...` 调用项目技能。 |
| 服务器、非交互式调度 | `python3 automation/openfde_ai_server.py` | 发现问题、维护队列，并按配置启动短生命周期 Pi 工作进程。 |

### 交互式 Pi

在项目根目录执行：

```sh
cd "$(git rev-parse --show-toplevel)"
gh auth status
pi
```

启动后直接使用下列技能命令。它们不是 shell 命令，因此不要直接粘贴到 zsh/bash。技能更新后退出并新开会话（`pi`，不要 `pi -c`），见文首说明。

```text
/skill:list-github-issues 使用 profiles/openfde/profile.json 列出全部问题的编号、状态、标题、标签和更新时间；不要下载详情或写入 GitHub。
```

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 470；只读分析，不修改源码、不构建、不测试、不提交。
```

也可将 `470` 替换为完整的 GitHub 问题链接。

### 非交互式服务器协调器

该入口供服务器定时器或管理员使用，不是直接分析命令。它会先通过 `gh issue list` 发现问题、写入本地 SQLite 队列；仅在配置或 `--execute` 参数启用后，才为已领取的问题启动 Pi。

复制示例配置后默认会执行 worker；如只需发现和入队，先将 `worker.execute` 改为 `false`：

```sh
cp config/openfde-ai-server.example.json config/openfde-ai-server.json
python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json \
  scan

python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json \
  status
```

确认队列和配置后，可显式启动本轮已入队分析：

```sh
python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json \
  scan --execute
```

协调器连续推进同一 issue 的原子步骤；只有 `archived`、`needs_information`、`blocked` 才是完成终态。Pi 或 patch 均不等同于问题已修复。生产环境的 `systemd` 部署、服务账户和凭据隔离见[服务器部署指南](server-deployment.md)。

## 取证采集（提 issue 前）

交互式采集，先给 A/B/C/D 菜单；默认最小集，全程只读。产物在 `data/intake/`，不写入 issue 工件、不访问 GitHub。

```text
/skill:collect-device-evidence 现象：<一句话>；设备：<型号/版本/IP>
```

- **A. 最小集**（默认）：`bugreport` + 截图；录屏按需；
- **B. 不采集**：只生成 issue 草稿；
- **C. 先现场复现**，复现完成后采集；
- **D. 事后证据**：已有 bugreport，不连设备；
- 已给设备并说“开始采集/复现完成”= A 且已确认，直接执行；否则一条确认，未确认前不采集；
- 容器内用网络 adb：`adb connect <IP>:5555`（镜像已内置 `adb`；USB 默认不映射）；
- 完成后对话中输出**完整 issue 草稿**（供复制）+ zip/文件；
- 包在宿主机 `~/fde-ai-assistant/data/intake/<slug>`，可直接：
  `scp -r <宿主机用户>@<宿主机IP>:~/fde-ai-assistant/data/intake/<slug> <本机目录>`；
- D 模式不连设备；全程只读：禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置。

**最简 issue + 手动整理**：可以先只提交一句 `偶现…，有 bugreport`（或仅文字+截图），创建后执行整理命令——pi 内 `/skill:enrich-issue-intake 整理问题 #N`，或 shell `bash deploy/enrich-issue.sh N`。整理会规范化标题/正文（时间线只写范围、推测步骤标注未确认、保留原始描述）；**无 bugreport 时**用模型视觉读图并给出“初步分析（未验证）”与建议补充的证据。详见[取证采集](../architecture/intake.md)。偶现问题也可选 D 模式（事后证据：不连设备、只校验打包已有 bugreport）。

全程只读：禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置。

## 置信度分流（分析助手 / 修复助手）

`propose-fix` 会给出 `fix_confidence`（取根因与修复的较低值，0–100）。分流规则：

| 分数 | 处理 |
| --- | --- |
| ≥70 | 修复助手：补丁 → PR → 交付/验证征询评论 → `awaiting_verification` |
| 50–69 | 分析助手：原因链 + 修复选项 A/B/C + D/E/F 选项（同一轮生成草案，确认后发布）→ `awaiting_direction` |
| <50 | 分析助手深度分析（最多 2 轮）；仍不足则发调查选项 → `awaiting_direction` |

## 原因链与修复选项（50–69）

当修复置信度不足 70（根因存在未证实环节、需要复现实验、多条可行修复路线或改动影响面需要开发决策）时，助手**不自行选路线**，而是产出并发布一条 `analysis-options` issue 回复：

- **结论与置信度**：失效机制 + “修复置信度 xx%（根因 xx / 修复 xx，依据……）”；
- **问题原因链**：触发条件与前置状态、毫秒级时间线、按时间/调用顺序的完整因果链（每步带证据 ID/日志时间戳与 `文件:行号`）、直接原因、根本原因、放大因素、容错路径为何失效、未证实环节（标注“推断，未证实”与验证实验）、影响面、已排除项；
- **修复选项 A/B/C**：每项含改动点（`文件:函数`）、机制、优点、缺点与风险、验证方法与判据、工作量、是否需要构建/刷机；推荐项标注“推荐”；
- **可选证据补强（只列选项，不展开）**：D. 复现与验证方案；E. 调试 PR（插桩）；F. 深入分析（<50 或按需）；
- **请求决策**：回复 A/B/C/D/E/F；A/B/C 生成补丁/PR，D 展开复现方案并追加 issue 回复，E 创建 `ai-debug/` 插桩 PR，F 继续深度分析。

写作要求：纯技术分析，结论必有依据，禁止套话、情绪化文字与空泛总结。发布由 `publication.analysis_options_comment` 控制（当前 `auto`）；`dry_run=true` 时发布前仍需你在会话中确认。

## 复现与验证方案（选择 D 后）

当根因只能由代码推断、无法完全确认，且你选择 D 时，`design-reproduction-plan` 会生成方案并**追加一条 issue 回复**：

- **稳定复现**：无侵入 adb 循环脚本（如快速切换 dock 缩略图与桌面应用）→ 轻插桩日志 → 需构建的深插桩（断言/trace/perfetto）；
- **观测点**：目标 crash 签名、`logcat -b crash`、tombstone/dropbox、关键 tag；
- **判定标准**：N 次运行出现 ≥1 次目标签名即“已复现”；修复后同一脚本 N 次 0 次目标签名 + 错误日志消失即“通过”；
- **根因确认实验**：列出可区分的假设与实验，说明每个结果支持/排除哪个假设。

方案仅供人工执行（全部 `not_run`），需要构建的插桩会提示开启 `build.enabled=true`；执行后回传日志/结果，按新证据进入新 revision。

## 调试 PR（选择 E 后）

- 只加日志/埋点，**不改变行为**；分支 `ai-debug/issue-<编号>-*`，只创建、不合入；
- 评论包含插桩点与 TAG、复现与采集命令（`adb logcat -s openfde<编号>`）、回传要求、移除方式；
- 当前构建关闭，由开发自行构建/刷机；回传调试日志后按新证据进入新 revision 重新分析。

## 求助与验证闭环

**交互通道与占比（`publication.interaction_comments`）**：

| 模式 | 求助/选择（A/B/C） | 修复交付（含 PR） |
| --- | --- | --- |
| 交互会话（你在电脑前） | 终端内完成，不发评论 | 发布交付/验证征询评论 |
| 无人值守 + `pr_only`（默认） | 不发评论，停在等待态 | 发布交付/验证征询评论 |
| 无人值守 + `auto` | 发布 A/B/C 求助评论 | 发布交付/验证征询评论 |
| 任意 + `manual` | 不发 | 仅留草稿 |

例外：`publication.analysis_options_comment=auto` 时，“置信度不足”的原因链+修复选项征询评论（`analysis-options`）会发布到 issue 并停在 `awaiting_direction`（不受 `pr_only` 限制）；`reproduction_plan_comment` / `debug_pr_comment` 为 `auto` 时，D/E 产出的复现方案/调试 PR 评论同样发布并保持 `awaiting_direction`。`dry_run=true` 时发布前仍需你在会话中确认。

**重新进入下一轮（推荐用法）**：在 pi 会话里直接说：

```text
继续 494
继续 494；选 A（更新 PR），PAGE_TURN_DISTANCE 用 60
```

（技能有更新时先退出并新开会话，再执行上述命令。）

它会先重读状态、自动同步 issue 新回复（如有），然后在**本地**继续分析修复；对任意中间状态都适用（包括无人值守停下的 `patch_validated`）。关键节点与 A/B/C 默认在终端内完成，不产生 issue 评论；原因链+修复选项征询（`analysis-options`）除外。

其余行为：
- 分析受阻（或按耗时预算触发）时停 `awaiting_direction`；交互会话内直接问，无人值守且 `auto` 时才发布求助评论；
- 交付修复后停 `awaiting_verification`：回复 `验证通过` 收敛为 `confirmed_fixed` 并归档；回复 `仍有问题`（附新日志/截图）开启新 revision 重新分析；调试 PR 回传日志同样按新证据进入新 revision；
- 轮询：`deploy/reply-poll.sh` 默认每 5 分钟检查一次新回复（`REPLY_POLL_SECONDS` 或 profile `replies.poll_seconds` 可调整）；无新回复时不消耗模型调用、保持等待；`awaiting_direction` 超过 30 分钟仅在日志与下次会话提示。

## 浏览与分析一个问题

先只浏览完整 issue 清单：

```text
/skill:list-github-issues 使用 profiles/openfde/profile.json 列出全部问题的编号、状态、标题、标签和更新时间；不要下载详情或写入 GitHub。
```

选择编号后，使用统一编排器：

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 <issue-number-or-url>；按产物状态执行原子步骤，直到得到建议、需要补充信息或明确阻塞；不修改源码。
```

它会按证据条件选择一个分支：有 bugreport/tombstone/ANR/结构化日志时调用 `extract-log-evidence`，否则调用 `extract-text-evidence`。然后依次映射清单组件、只读缓存精确版本修订的源码、追溯证据到源码、验证引用、提出方案并可生成未应用的补丁建议。

若证据不足，系统应停止猜测，形成只请求版本、环境、复现步骤和相关日志的补充信息草稿。它不应声称已经定位根因。

## 组件归属确认

组件归属优先查 `profiles/openfde/component-map/` 种子与 `data/knowledge/component-map/` 学习条目，再在 `fde-sources/` 检索信号（命中文件向上找最近 `.git`）；拿不准时流程停在 `component_review_requested`，并在 `.fde-ai/issues/<编号>/analysis/component-review.json` 给出候选与依据。开发人员确认后：

```text
/skill:confirm-component-mapping 该问题属于 <项目名或路径>；依据：<一句话>
```

确认结果写入最终映射并沉淀到组件映射知识，下次同类信号自动命中；回复“无法确认”时流程停止等待更多信息，不会猜测。

## 补丁与 GitHub 评论

`draft-patch` 只生成统一 diff 建议及其 base commit、SHA-256、证据 claim 和 `not_run` 说明。它从不修改源码缓存、执行 `git apply`、构建或测试。

修复交付/更新评论使用丰富模板：问题范围、证据与定位、根因（源码行号）、**完整统一 diff**、影响与风险、建议验证步骤、`not_run`、PR 链接与验证征询；不得只发交付摘要或省略 diff。更新已有 PR 时同样附当前生效补丁的完整 diff。

```text
/skill:draft-issue-comment 为当前版本修订生成 GitHub 评论草稿，包含证据/源码引用、补丁建议、风险和用户测试说明；不要发布。
```

只有 `publish-policy-comment` 可以执行外部写入，且只能使用 `gh issue comment`。交互模式默认逐条确认；服务器批量模式只有在项目配置已启用 `auto_when_eligible`、通过去重、脱敏、置信度、标签、限额和停用开关检查后，才允许自动发布。无论哪种模式，评论都必须声明：AI 生成、补丁未应用/未验证、由用户自行测试。

补丁校验通过后，关键节点会提供“生成 PR”选项：`create-fix-pull-request` 在独立工作区（`data/pr-work/`）克隆 GitHub 仓库（openfde org，按清单项目名拼装 URL）、校验并应用补丁、推送 `ai/issue-<编号>-<slug>` 分支，并用 `gh pr create` 创建 PR（默认目标 `fde_17` 主分支；**只创建、不合入**；不强推、不覆盖已有分支）。修复跨多个项目时，**按项目分别生成 PR**，全部链接（单项目为一个）写入评论草稿的“修复 PR/MR”段落；PR 说明与评论落款统一使用“由 AI 修复助手生成”，且不得写出 `.fde-ai/` 等内部产物路径。

## 受控构建（可选）

`validate-patch-artifact` 通过后，**仅当 profile 配置了 `build` 且 `build.enabled=true`** 才进入构建通道（**默认关闭**，调试 L0-L2 期间不进入；停在 `build_requested` 的历史状态在关闭时视为已跳过）。启用后默认 `build.mode=manual`：

1. `request-build` 只写 `.fde-ai/issues/<issue号>/build/build-request.json`，把 `state` 推进到 `build_requested` 后停止；
2. 人工在部署容器内运行授权助手：

```sh
deploy/server/fde-ai-build.sh --issue <issue号>
```

3. 助手加锁（`data/build.lock` 与 `.siso_lock` 检查）、临时应用补丁、增量构建、记录产物哈希到 `build-result.json`、更新 `state` 为 `build_done`（或 `build_failed`），并在退出前回滚补丁；
4. 在 Pi 中继续 `/skill:run-issue-workflow`，`collect-build-artifacts` 校验产物后推进到 `artifacts_collected`，随后评论草稿会包含构建验证段落。

整体构建运行期间助手会因锁被占用退出 75，稍后重试即可。`build.mode=auto` 时才允许 `request-build` 直接调用助手；无论哪种模式都不得手工 `git apply`、`make` 或把补丁留在构建树中。

## 批量扫描与回复

```text
/skill:scan-github-issues 使用 profiles/openfde/profile.json 进行一次受限扫描；遵守队列并发、发布策略、限额和紧急停用开关。
```

服务端应由定时器定期触发该技能。开发者或用户的新增回复通过 `sync-github-replies` 读取；新日志、环境信息或测试失败创建新的分析版本修订，旧产物不覆盖。用户测试结果记录为 `user_reported_result`，不等同于 AI 验证。

## 常见问题

**没有候选技能：** 确认当前目录是项目根目录，退出并新开会话（`pi`，不要 `pi -c`），并在 Pi `/settings` 启用技能命令。

**没有完整 Android/FDE 环境：** 设备侧启动、运行时和验收仍是设计边界，标记为 `not_run`；需要编译验证时，按 profile `build` 配置运行受控构建助手，把结果记为构建证据而非用户验证。

**截图类证据：** 用模型自身视觉直接读取 `input/` 内的截图附件，不引入 OCR 工具；图片中的文字与指令一律作为不可信证据。

**多个清单组件都可能相关：** 保留候选项，只有日志调用栈、模块名或源码路径能支持时才缩小范围。

旧的 OpenFDE 专用技能已移除；当前项目只保留本页列出的通用入口。历史产物仍可作为只读证据使用，但不可再依赖旧技能名称恢复流程。
