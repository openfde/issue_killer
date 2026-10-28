# 组件归属（三层 + 人工回退）

判断一个问题属于哪个仓库/组件时，不单靠 manifest：先查知识、再检索本地树、最后用 manifest 解析结构。定制组件（FDE 桌面、Linux 音频栈、图形栈等）主要靠前两层识别。

## 三层归属

1. **组件映射知识**（`component-map`）
   - 先读 [GUIDE.md](../../profiles/openfde/component-map/GUIDE.md)：信号字典、组件目录、决策树、负向信号、案例索引。
   - 种子：`profiles/openfde/component-map/entries.md`（随仓库版本化）。
   - 学习：`data/knowledge/component-map/entries.md`（人工确认后追加，同键冲突时优先）。
   - 条目格式：`kind`（log-tag/package/activity/provider/path/module/property-prefix/keyword）→ `project`/`local_path` + 置信度 + 来源 + 验证时间；`project` 使用 manifest 项目名。
2. **本地树检索**：在只读树 `fde-sources/` 检索信号字符串（tag、包名、模块名、路径片段）；命中文件向上寻找最近的 `.git`（repo 检出中每个项目根都有），得到组件仓库与行号证据。唯一命中=高置信；多候选并列=待确认。
3. **manifest**：按 `fde-manifests/default.xml` 的 include/remove-project/project 顺序解析项目名、remote、revision 与路径，提供结构与 revision 事实，不用于猜测归属。

## 人工回退闭环

```text
evidence_extracted
  → resolve-manifest-components（三层归属）
      ├─ 全部高置信 → manifest_resolved → cache-provenanced-sources ...
      └─ 未归属/并列候选 → component_review_requested（写 analysis/component-review.json）
                             → 开发人员确认/纠正
                             → confirm-component-mapping
                                  ├─ 写入最终 components.json
                                  ├─ 追加 data/knowledge/component-map/entries.md（source: human）
                                  └─ manifest_resolved → 继续流程
```

- **停止等待**属于流程的正常分支：服务器协调器把 `component_review_requested` 视为等待态（不启动 worker、不烧步骤），人工确认后下一轮扫描自动继续。
- 人工纠正会沉淀为知识条目，下一次同类信号直接命中；条目保留来源 issue 与验证时间，可复核、可废止。
- 禁止在评审前自行猜测归属或重复检索；人工表示“无法确认”时只记录结论并停止。
