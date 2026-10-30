# 知识沉淀与组件导引

本文说明 issue 处理后的知识如何落库、如何检索、如何晋升，以及模块分流指南如何使用。规则/模板和人工导出的已验证 case 在仓库内，运行时数据在 `data/knowledge/`（Docker 持久卷，不进入 Git）。

## 1. 三条知识线

| 知识线 | 位置 | 产生方式 | 可信度 |
|---|---|---|---|
| Case（自动、全量） | `data/knowledge/cases/<issue>/` | `archive-case` 归档时调用 `automation/capture_knowledge_case.py` | `draft`；只有 `confirmed_fixed` 才 `verified` |
| 版本化 Case（源码种子） | `profiles/openfde/knowledge/cases/` | 人工从 verified 运行时 case 导出 | 随源码发布，可审计；同 issue 以运行时为准 |
| Wiki（人工审核） | `data/knowledge/wiki/` | `propose-knowledge` 生成候选 → `promote-knowledge` 人工批准 | 已审核事实，带来源/验证人/过期时间 |

运行时 Case 是“发生过什么”，版本化 Case 是已验证的可审计种子，Wiki 是“可以复用的项目事实”。它们都不替代原始证据和源码。

## 2. Case 自动采集

交互式使用 Pi skill：

```text
/skill:knowledge-case 采集问题 <编号>
/skill:knowledge-case 重建索引
/skill:knowledge-case 查看问题 <编号>
```

自动流程由 `archive-case` 直接调用脚本；手动调试才使用底层命令：

```bash
python3 automation/capture_knowledge_case.py --workspace . --issue <编号>
```

读取：

- `.fde-ai/issues/<编号>/state.json`
- `.fde-ai/issues/<编号>/archive/case.json`（必需）
- `analysis/components.json`、`evidence/evidence.json`、`input/issue.json`（可选）
- `patch/*.patch`（只记录路径/哈希，不复制内容）

写入：

```text
data/knowledge/
├── index.json
└── cases/<编号>/
    ├── case.json
    └── case.md
```

脚本是幂等的，只生成 `draft`，不写 Wiki、不改 GitHub、不晋升知识。缺少 `archive/case.json` 时会失败，避免把空 case 写进知识库。

人工确认后，可把 verified case 导出为随源码发布的版本化种子：

```text
profiles/openfde/knowledge/cases/
├── index.json
└── <编号>/{case.json,case.md}
```

只导出 `verified` case；同 issue 的运行时条目优先。维护规则见 [cases/README.md](../../profiles/openfde/knowledge/cases/README.md)。

重建索引：

```bash
python3 automation/capture_knowledge_case.py --workspace . --rebuild-index
```

字段定义见 [case-schema.json](../../profiles/openfde/knowledge/case-schema.json)，模板见 [case-template.md](../../profiles/openfde/knowledge/case-template.md)，完整规则见 [knowledge/README.md](../../profiles/openfde/knowledge/README.md)。

## 3. 检索与使用

`retrieve-knowledge` 的流程：

1. 先读版本化 `profiles/openfde/knowledge/cases/index.json`，再读运行时 `data/knowledge/index.json`；同一 issue 以运行时为准；
2. 按组件、包名/Activity/log tag、标签、版本、时间做结构化过滤；
3. 读取匹配的版本化/运行时 `case.json` 和 `wiki/*.md`；
4. 写入 `analysis/knowledge-selection.json`，带路径、哈希、`verified`/`draft`、来源（`versioned`/`runtime`）、置信度、过期状态。

规则：

- `verification.verified=true` 或 `confirmed_fixed` 的 case 可以作为“已确认知识”；
- `draft` case 只作为线索，必须标 `trust: draft`，不能据此下结论；
- 版本化 case 只能是 verified 种子；不得把 draft 或含敏感信息的 case 导出到仓库；
- 相似度只用于排序，不能当证据；每个结论仍引用证据/源码；
- 没有命中是合法结果，记录空选择后继续。

## 4. 晋升为 Wiki

1. `propose-knowledge` 只接受已验证 case，生成候选（带 `case_id`、来源 issue、`verified_by`、`stale_after`）；
2. 人工审核候选；
3. `promote-knowledge` 写入 `data/knowledge/wiki/`，更新 `wiki/index.md`，并在 `data/knowledge/audits/promote.jsonl` 追加审计；
4. 版本/构建变化后标记过期，重新验证后再用。

Agent 不自动晋升、不自动关闭 issue、不自动合并 PR。

## 5. 模块分流指南

先读 [component-map/GUIDE.md](../../profiles/openfde/component-map/GUIDE.md)：

- 信号字典：package / activity / log tag / window / UI 文案 / path / module；
- 组件目录：manifest 项目名与本地路径；
- 决策树：桌面/任务栏、状态栏/通知、文件、日历、第三方应用；
- 负向信号：避免把 launcher 宿主、FDE 顶栏、原生 shade、Calendar provider 混在一起；
- 案例索引：491、492、493、494、496、497、498、499 的当前判断与待核实项。

`resolve-manifest-components` 会先读 GUIDE，再查 `entries.md`；高置信命中直接采用，中置信列候选并问开发人员，低置信停 `component_review_requested`。人工确认后用 `confirm-component-mapping` 写回 `data/knowledge/component-map/entries.md`。

## 6. 质量与安全

- 不保存 token、密码、私钥、完整 bugreport；只存引用/哈希，文本按需截断。
- 同一信号多个根因时保留 differential，不合并成单一事实。
- 过期 case/事实标 `stale`，重新验证后再用。
- 人工审核是晋升的唯一入口；agent 只生成 draft/候选。
