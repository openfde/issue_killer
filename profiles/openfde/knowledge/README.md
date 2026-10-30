# 知识沉淀（knowledge）

本目录是**版本化的知识规则/模板，以及人工导出的已验证 case**；运行时数据在 `data/knowledge/`（Docker 持久卷，不进入 Git）。

## 目标

每个 issue 处理结束后，自动留下可检索、可追溯、可复核的 case；经人工审核后再晋升为 Wiki 事实。知识只用于加速定位和提供候选，**任何结论仍必须引用原始证据和源码**。

## 两层结构

### 运行时（Docker 持久卷，不进入 Git）

```text
data/knowledge/
├── index.json                  # 所有 case 的摘要索引（脚本重建）
├── cases/
│   └── <issue>/
│       ├── case.json           # 结构化 case（draft / verified）
│       └── case.md             # 人读摘要
├── wiki/
│   ├── index.md                # 已审核事实索引
│   └── <topic>.md              # 已审核事实
├── component-map/
│   └── entries.md              # 人工确认的组件映射（运行时学习）
└── audits/
    └── promote.jsonl           # 知识晋升审计
```

### 版本化 case（进入 Git，随源码发布）

```text
profiles/openfde/knowledge/cases/
├── index.json                  # 版本化已验证 case 摘要
├── README.md
└── <issue>/
    ├── case.json               # 结构化 case（必须 verified）
    └── case.md                 # 人读摘要
```

- 只存放人工确认的 `verified` / `confirmed_fixed` case；自动采集不会直接写入本目录。
- 运行时 `data/knowledge/index.json` 与同 issue 的版本化条目冲突时，以运行时为准；版本化 case 作为新环境种子和可审计样本。
- `retrieve-knowledge` 先读版本化索引，再读运行时索引；选择记录必须标明 `source: versioned|runtime`。
- 新增/导出步骤见 [cases/README.md](cases/README.md)；不提交 token、密码、完整 bugreport 或大附件。

### Case（自动、全量）

- 每个 `archived` / `confirmed_fixed` / `blocked` / `needs_information` 的 revision 都生成一份 case。
- 默认 `knowledge_status: draft`，不改 Wiki，不代表已验证。
- `verified: true` 只来自人工确认或 `confirmed_fixed` 状态。
- 只有 verified case 才能导出到 `profiles/openfde/knowledge/cases/`；运行时仍可保留 draft 供检索线索。
- 同一 issue 的最新 revision 覆盖 `case.json`；历史通过 issue 的 `archive/` 和 case 内的 `revision` 追溯。

### Wiki（人工审核后）

- 只有 `verified` case 才能由 `propose-knowledge` 生成候选、由 `promote-knowledge` 写入 `wiki/`。
- Wiki 条目必须有：`source_case`、`source_issue`、`verified_by`、`verified_at`、`applies_to`、`stale_after`。
- `data/knowledge/wiki/index.md` 缺失时用 [wiki-index-template.md](wiki-index-template.md) 初始化。
- 冲突事实不覆盖；保留 `differential` 和适用条件。

## Case 字段

完整 schema 见 [case-schema.json](case-schema.json)，模板见 [case-template.md](case-template.md)。核心字段：

| 字段 | 说明 |
|---|---|
| `case_id` | `issue-<编号>` |
| `issue` / `repo` / `title` / `url` | issue 元数据 |
| `status` | issue 工件状态（`archived` 等） |
| `revision` | 分析 revision |
| `device` | 设备/构建/Android 版本（有则记录） |
| `components` | 组件、路径、置信度、来源 |
| `signals` | package/activity/log-tag/UI 文案等 |
| `symptom` | 现象摘要 |
| `root_cause` | 根因（未验证则标注） |
| `fix` | patch/PR/commit/摘要 |
| `verification` | 验证状态、证据、验证人、时间 |
| `knowledge_status` | `draft` / `verified` / `rejected` |
| `provenance` | 来源文件、哈希、时间 |
| `tags` | 检索标签 |

## 自动采集

`archive-case` 归档后调用：

```bash
python3 automation/capture_knowledge_case.py --workspace . --issue <编号>
```

脚本只读 issue 工件，写：

- `data/knowledge/cases/<issue>/case.json`
- `data/knowledge/cases/<issue>/case.md`
- `data/knowledge/index.json`

脚本是幂等的；只生成 `draft`，不写 Wiki、不改 GitHub、不晋升知识。缺少 `archive/case.json` 时以非零退出，避免把空 case 写入知识库。

人工确认后，把已验证 case 从运行时导出到版本化目录（步骤见 [cases/README.md](cases/README.md)）：

```text
data/knowledge/cases/<issue>/case.json  ->  profiles/openfde/knowledge/cases/<issue>/case.json
data/knowledge/cases/<issue>/case.md    ->  profiles/openfde/knowledge/cases/<issue>/case.md
data/knowledge/index.json               ->  profiles/openfde/knowledge/cases/index.json（只保留已验证条目）
```

版本化导出是人工动作，不由 `archive-case` 自动执行。

重建索引：

```bash
python3 automation/capture_knowledge_case.py --workspace . --rebuild-index
```

## 检索

`retrieve-knowledge` 的优先级：

1. 先读版本化 `profiles/openfde/knowledge/cases/index.json`，再读运行时 `data/knowledge/index.json`；
2. 按组件/包名/Activity/log tag 做结构化过滤；
3. 按标签、版本、时间做过滤；同一 issue 运行时条目覆盖版本化条目；
4. 读取命中的 `case.json` 和 `wiki/*.md`；
5. 只把 `verified` 或 `confirmed_fixed` 的 case 作为“已确认知识”，`draft` 只作为线索；
6. 写入 `analysis/knowledge-selection.json`，带来源（`versioned`/`runtime`）、哈希、置信度、过期状态；无命中是合法结果。

## 质量规则

- 不把“相似”当证据；检索结果必须能回到 case/issue/证据。
- 不保存 token、密码、私钥、完整 bugreport；只存引用和哈希，文本按需截断。
- 同一信号多个根因时，保留 differential，不合并成单一事实。
- 版本化 case 必须 `verified`，并能追溯到原始 issue/证据/源码；不得把 draft 导出。
- 版本/构建变化后，旧事实标记 `stale`，重新验证后再用。
- 人工审核是晋升的唯一入口；agent 不自动晋升、不自动关闭 issue。
