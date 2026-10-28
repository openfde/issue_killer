# 组件映射知识（component-map）

先读 [GUIDE.md](GUIDE.md)：它是面向人的分流指南（信号字典、组件目录、决策树、负向信号和案例索引）。`entries.md` 是机器/人工共用的精确映射条目。

用于把问题信号（日志 tag、进程/包名、文件路径、模块名、属性前缀、中英文关键词）映射到源码组件仓库。`resolve-manifest-components` 按三层归属：

1. **本知识库**（本目录种子 + 运行时学习）；
2. **本地树检索**：在只读树 `fde-sources/` 检索信号，命中文件向上寻找最近的 `.git`（repo 检出中每个项目根有 `.git`）；
3. **manifest**：按 `fde-manifests/default.xml` 解析项目名、remote、revision 与路径，作为结构与 revision 的事实来源，不用于猜测归属。

拿不准时流程停在 `component_review_requested`，由开发人员用 `confirm-component-mapping` 确认/纠正；确认结果追加为 `source: human` 条目。

## 文件与优先级

- 本目录 `GUIDE.md`：人读的分流指南（信号、决策树、负向信号、案例索引）。
- 本目录 `entries.md`：随仓库发布的种子条目（可评审、可版本化）。
- `data/knowledge/component-map/entries.md`：运行时学习条目；与种子同键冲突时以学习条目为准。
- 种子条目不会自动被覆盖；复核后由人工修改。

## 条目格式

Markdown 表格，列固定：

| 列 | 说明 |
| --- | --- |
| `kind` | `log-tag` / `package` / `activity` / `provider` / `path` / `module` / `property-prefix` / `keyword` |
| `value` | 匹配值；`keyword` 可用逗号分隔多个中英文关键词 |
| `project` | manifest 项目名（name 属性） |
| `local_path` | repo 检出中的本地路径 |
| `confidence` | `high` / `medium` / `low`（低置信命中不单独定案） |
| `source` | `seed` / `seed-manifest` / `human` / `case` |
| `last_validated` | 最后验证日期（YYYY-MM-DD） |
| `notes` | 备注：定制说明、来源 issue、限制 |

`project` 必须是 `fde-manifests` 里的 manifest 项目名；历史别名（如 `packages_apps_TaskPlugin`、`boringdroidsystemui`）在 `notes` 中保留，新增条目使用 `taskplugin`、`systemuiplugin`。

## 维护规则

- 人工确认（`confirm-component-mapping`）追加 `source: human`、`confidence: high`；不得编造。
- 定期复核：项目迁移或重构后更新 `local_path` 与 `last_validated`；过期条目标记 `low` 或删除。
- 同一 `kind`+`value` 只保留一条有效映射，冲突以学习条目为准并保留历史备注。
