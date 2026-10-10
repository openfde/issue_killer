---
name: validate-patch-artifact
description: 当拟议的统一 diff 产物在展示给 issue 报告者前需要进行不执行代码的结构与来源校验时使用。
---

# 校验 patch 产物

仅接收 `patch_proposed`。只校验 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch` 的统一 diff 头、路径是否属于已映射组件、base commit、SHA-256 和关联的已验证 claim。写入同目录 `validation.json`；将运行时、构建、测试和应用检查记为 `not_run`。不得在 `.fde-ai/runs/` 创建新产物。

结构、路径与来源全部校验通过后推进到 `patch_validated`；这也是构建通道（`request-build`）的唯一入口状态。不得调用 `git apply`、`git diff --check`、构建、安装或测试。diff 格式错误或来源缺失时停止；即使产物结构有效也仍是未经验证的建议。
