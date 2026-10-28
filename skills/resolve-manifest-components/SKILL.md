---
name: resolve-manifest-components
description: 当已提取证据需要映射到仓库组件时使用：优先查组件映射知识，其次检索本地只读源码树，最后用 manifest 解析仓库结构与 revision。
---

# 解析 manifest 组件

仅接收 `evidence_extracted`。对每个候选信号（日志 tag、进程/包名、Activity/窗口、provider/authority、文件路径、模块名、属性前缀、中英文关键词/UI 文案）按三层归属：

1. **组件映射知识**：先读 `profiles/openfde/component-map/GUIDE.md`，用其中的信号字典、决策树和负向信号选候选；再读 `profiles/openfde/component-map/entries.md`（种子）与 `data/knowledge/component-map/entries.md`（运行时学习，同键冲突以其为准）做精确匹配。精确命中的高置信条目可直接采用，并在 `components.json` 记录 `matched_by: guide` 或 `matched_by: entries`。
2. **本地树检索**：在只读树 `fde-sources/` 中按固定字符串检索（`rg -lF --max-count 1 -g '!prebuilts' -g '!out' -g '!.repo' <信号>`），一次一个信号；先搜 `frameworks/ packages/ system/ hardware/ device/ vendor/`，未命中再放宽全树。命中文件向上寻找最近的 `.git`（repo 检出中每个项目根有 `.git`）得到组件仓库；唯一命中记为高置信，多命中并列列为候选。
3. **manifest 结构与 revision**：按 `fde-manifests/default.xml` 的 include/remove-project/project 顺序解析项目名、remote、revision 与本地路径；不用于猜测归属。

只写 `.fde-ai/issues/<issue号>/analysis/components.json`：每个组件带匹配依据（knowledge/tree/manifest）、信号、置信度与证据（条目引用或文件行号）。所有必需信号均高置信归属时推进到 `manifest_resolved`。

存在未归属信号或并列候选时，写 `.fde-ai/issues/<issue号>/analysis/component-review.json`（候选排序、依据、向开发人员提问的最小问题），并把根目录 `state.json` 推进到 `component_review_requested` 后停止，等待人工用 `confirm-component-mapping` 二次确认；不得在评审前自行猜测归属或重复检索。不得在 `.fde-ai/runs/` 创建新产物。
