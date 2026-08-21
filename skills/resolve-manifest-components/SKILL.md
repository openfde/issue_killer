---
name: resolve-manifest-components
description: 当已提取证据必须通过项目 profile 声明的 manifest 适配器映射到仓库组件时使用。
---

# 解析 manifest 组件

仅接收 `evidence_extracted`。使用 profile 的 manifest 路径调用选定适配器。只写入 `.fde-ai/issues/<issue号>/analysis/components.json`；每个候选项必须包含匹配依据、manifest 项目名、获取 URL、revision 和本地路径。不得在 `.fde-ai/runs/` 创建新产物。

依据有效 manifest 校验映射并推进到 `manifest_resolved`。证据无法映射到组件时停止；创建缺失信息记录，而不是猜测仓库。
