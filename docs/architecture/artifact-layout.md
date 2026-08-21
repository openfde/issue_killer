# Issue 工件目录

每个 issue 的活动工件只能写入 `.fde-ai/issues/<issue号>/`。目录由 profile 的 `artifacts.issue_layout` 定义；任何 skill 在写入前都必须校验 issue 编号、根目录和相对路径。

```text
.fde-ai/issues/<issue号>/
├── state.json
├── input/       issue、评论、附件元数据与原始附件
├── evidence/    受限摘录与 evidence.json
├── analysis/    组件映射、来源、知识选择、分析与校验
├── solution/    修复建议
├── patch/       0001-<名称>.patch、patch.json、validation.json
├── comment/     GitHub 评论草稿
└── archive/     本 issue revision 的 case 索引
```

唯一 patch 入口是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`。`state.json` 必须引用该文件、其 SHA-256、基准提交和 `unverified_suggestion` 状态；没有 patch 时明确写为 `null`，不得猜测路径。

`.fde-ai/sources/` 是唯一的本地源码缓存位置；`data/knowledge/` 是知识库和长期 case 索引。不得在 `.fde-ai/runs/` 创建新产物、在 issue 目录复制源码 checkout，或覆盖旧 revision；新回复需在同一目录的 `archive/` 下保留可追溯 revision 索引。
