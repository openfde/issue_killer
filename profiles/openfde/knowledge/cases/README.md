# 版本化知识 case

本目录存放**已确认、可随源码发布**的 issue case 样本；运行时自动生成的 case 仍在 `data/knowledge/cases/`（Docker 持久卷，不进入 Git）。

## 目录约定

```text
profiles/openfde/knowledge/cases/
├── index.json              # 版本化 case 摘要索引
├── README.md
└── <issue>/
    ├── case.json           # 结构化 case（verified）
    └── case.md             # 人读摘要
```

- `index.json` 由人工维护或从运行时索引导出；`path` 相对本目录（`index.json` 所在目录）。
- `case.json` 必须来自已验证 case（`verification.verified=true` / `confirmed_fixed`），并保留 `provenance` 哈希。
- `case.json` 内的 `.fde-ai/...`、`data/...` 路径是生成时的运行时工件路径，不随仓库分发；以 `provenance` 哈希和 issue/证据链接追溯。
- 不提交 token、密码、完整 bugreport、原始日志或大附件；证据只放引用/哈希/URL。
- 运行时 `data/knowledge/index.json` 与同 issue 的版本化条目冲突时，以运行时为准。

## 当前条目

| issue | 状态 | 组件 | 备注 |
|---|---|---|---|
| 500 | confirmed_fixed / verified | `frameworks_base`、`systemuiplugin`、`packages_apps_launcher3`、`IntentResolver`（medium） | 2026-10-30 导出；PR #10 仍 open，issue 仍 open |

## 新增步骤

1. 在运行时生成并验证 case（`/skill:knowledge-case 采集问题 <编号>`）；
2. 人工确认 `case.json` 的 `knowledge_status=verified`、来源哈希和证据引用；
3. 复制到本目录 `<issue>/`；
4. 更新 `index.json` 的摘要（issue、title、status、revision、components、tags、path）；
5. 跑 `python -m unittest tests.test_versioned_knowledge_case`。

`retrieve-knowledge` 会先读本目录的 `index.json`，再读运行时 `data/knowledge/index.json`；版本化 case 是种子，运行时 case 优先。
