---
name: validate-intake-package
description: 当取证包已采集或由人工回传后需要校验完整性与最小数据集并生成补充采集请求时使用。
---

# 校验取证包

接收 `data/intake/<slug>/`（服务器采集产物）或人工提供的取证包解压目录。对照 `collection-plan.json` 校验：清单与哈希完整、必需 evidence item 齐全、文件非空且大小合理、版本与机型信息存在、预期关键标记（tag/关键字）在文本中出现。

写 `data/intake/<slug>/intake-validation.json`：通过项、缺项、异常项，以及逐条“精确到命令”的补充采集请求。全部必需项通过时把 `status` 推进到 `validated`（可整体附加到 issue 作为首版证据）；存在缺项时保持 `collected`，只读校验、不推断原因、不修改采集包原始内容。

不得访问 GitHub、发布评论、连接设备或执行新的采集；不得在 `.fde-ai/runs/` 创建新产物。
