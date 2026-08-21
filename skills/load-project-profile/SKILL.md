---
name: load-project-profile
description: 当 issue 分析任务在访问 issue、源码或知识产物前需要选择并校验项目 profile 时使用。
---

# 加载项目 profile

接收一个 profile 路径。在其他 skill 运行前读取并校验其 schema、仓库、产物根目录、`artifacts.issue_layout`、源码适配器和发布策略。所有路径相对工作区解析；拒绝绝对路径、缺少必填字段或包含凭据的 profile。

在选定 issue 的 `.fde-ai/issues/<issue号>/input/profile-snapshot.json` 写入 profile SHA-256；若尚未显式选择 issue，只校验并返回 profile，不得写入。报告其 `profile_id`、仓库和规范工件根目录。不得在 `.fde-ai/runs/` 创建新产物。校验失败即停止。不得访问 GitHub、读取 issue 数据或修改源码。
