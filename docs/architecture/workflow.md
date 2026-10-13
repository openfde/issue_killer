# OpenFDE 问题分析工作流架构

## 目标与安全边界

系统持续分析 `openfde/openfde` 的 GitHub 问题：收集问题、评论、日志和附件元数据；将证据映射到 OpenFDE 清单组件与精确版本源码；形成可审计的根因判断、补丁建议与评论草稿。

问题正文、评论、日志和附件都是不可信证据，不能充当指令。系统不得修改源码或缓存，不得应用补丁、构建、安装、测试、提交、推送、创建 PR 或关闭问题。唯一例外是 profile `build` 配置声明的授权构建助手：它在受控构建树内临时应用 patch、完成受限构建、记录产物并回滚补丁；默认人工触发。补丁永远只是统一 diff 形式的未验证建议。

## 组件与数据流

```text
GitHub（只读 gh）
  → 问题列表、详情、评论、附件元数据
  → Pi：run-issue-workflow
      → 证据提取（含截图附件：模型视觉直读）
      → 清单组件解析
      → 只读源码缓存（local_tree：本地只读树 + 精确 commit）
      → 证据到源码追溯与分析校验
      → 修复建议、补丁建议
      → 受控构建（manual 默认；授权助手临时应用 patch 并回滚）
      → 构建产物登记
      → 评论草稿、知识候选
  → .fde-ai/issues/<issue号>/：问题版本、证据、构建与审计产物
  → data/knowledge/：经审核的 Wiki 知识库
```

`automation/openfde_ai_server.py` 只负责发现问题、维护 SQLite 队列并启动短生命周期 Pi 进程。它不分析问题，也不生成补丁。详细调度语义见[服务器工作进程](server-worker.md)。

## 两种运行方式

| 方式 | 入口 | 选择规则 |
| --- | --- | --- |
| 人工交互 | Pi 的 `/skill:run-issue-workflow` | 当前用户必须明确提供问题编号或完整 URL。 |
| 服务器扫描 | `automation/openfde_ai_server.py scan --execute` | 仅接受受信任队列领取的编号。 |

无论哪种方式，都不得从列表首项、最近问题、旧产物或对话上下文自行选择问题。缺少明确选择时停止并请求选择。

提 issue 之前还有独立的取证通道（`collect-device-evidence`，交互式）：人工给出现象，助手简短评估后引导采集 bugreport/截屏（录屏可选，按需加子系统项），只读执行，产物只写 `data/intake/`，不访问 GitHub。详见[取证采集](intake.md)。

## 工件位置

所有原子 skill 共享一个规范 issue 目录，目录约束见 [Issue 工件目录](artifact-layout.md)。唯一 patch 入口是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`；不得在 `.fde-ai/runs/` 创建新产物。

## 原子技能顺序

`run-issue-workflow` 是薄编排器。它按以下顺序调用项目本地通用技能，并在每个原子步骤后校验产物状态：

```text
load-project-profile
→ build-project-context
→ fetch-github-issue
→ extract-log-evidence 或 extract-text-evidence
→ resolve-manifest-components（低置信时经 confirm-component-mapping 人工确认）
→ cache-provenanced-sources
→ retrieve-knowledge
→ trace-evidence-to-source
→ verify-analysis
→ propose-fix
→ 可选 draft-patch / validate-patch-artifact
→ 可选 create-fix-pull-request（人工确认；只创建 MR/PR，不合入）
→ 配置了 build 时 request-build（manual 等待人工 / auto 经授权助手）
→ collect-build-artifacts
→ draft-issue-comment
→ archive-case
```

证据不足、状态校验失败或需要人工信息时，流程进入 `needs_information` 或 `blocked`，而不是猜测根因。开发者新增回复、新日志或用户测试失败会创建新的分析版本，不覆盖旧证据。

## 源码、补丁与验证

`resolve-manifest-components` 按三层归属：组件映射知识（种子 + 运行时学习）、本地树信号检索（`fde-sources/` 中命中文件向上寻找最近 `.git`）、`fde-manifests/default.xml` 的 include/remove-project/project 顺序（结构与 revision 事实来源）。低置信或并列候选时停在 `component_review_requested`，由开发人员确认/纠正后经 `confirm-component-mapping` 落库并继续；详见[组件归属](component-attribution.md)。

`sources.mode=local_tree` 时，`cache-provenanced-sources` 在只读本地树中按组件记录精确 commit 与哈希，不克隆、不拉取；其他模式仅获取匹配组件的精确版本，并保持本地副本只读。

补丁建议必须关联已验证的证据、组件、文件、行号和基准提交，且标记为 `not_run`。安装、启动和设备侧测试由用户或 CI 执行；其结果可作为下一版本的证据。补丁经人工在关键节点确认后，可由 `create-fix-pull-request` 在独立工作区应用、推送 `ai/` 分支并以 MR/PR 形式提交（**只创建、不合入主分支**），供开发人员查看、修改与合入。构建通道是补丁的受限验证手段而非修复声明：`manual`（默认）下 `request-build` 只写 `build/build-request.json` 并停在 `build_requested`，人工运行 `deploy/server/fde-ai-build.sh --issue <编号>`；`auto` 下由授权助手执行。助手加锁（`data/build.lock` 与 `.siso_lock` 检查）、临时应用 patch、模块增量构建、记录产物哈希到 `build/build-result.json`，并在任何退出路径回滚补丁；`collect-build-artifacts` 校验后推进到 `artifacts_collected`。

## GitHub 读取与发布

GitHub 访问统一使用 `gh`。读取使用 `gh issue` 或只读 `gh api`；唯一允许的外部写入是经过 `publish-policy-comment` 策略检查后的 `gh issue comment`。

交互模式默认逐条确认。服务器批量模式只有在项目配置显式启用自动发布、完成去重/脱敏/置信度/标签/限额/停用开关检查后才可评论。评论必须说明：由 AI 生成、补丁未应用且未验证、需要用户自行测试。

## 知识沉淀

知识库是可索引的 Markdown Wiki，不使用向量化作为事实来源。知识条目记录组件路径、清单版本、源码提交、问题版本、状态、标签和最后验证时间。模型先按这些字段过滤，再用全文检索读取候选文档；所有结论必须回链到原始证据、源码和问题版本。
