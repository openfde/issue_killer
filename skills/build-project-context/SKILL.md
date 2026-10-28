---
name: build-project-context
description: 当已选择的项目 profile 在 issue 分析前需要生成受限且可持久化的 AGENTS.md 上下文段落时使用。
---

# 构建项目上下文

接收已校验的 profile 快照。仅将稳定项目事实、规范 issue 工件布局、manifest 规则、源码适配器、构建通道边界、`gh` 边界和安全策略渲染到根目录 `AGENTS.md` 的标记包围区；保留标记外文本。必须声明唯一 patch 入口 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch` 和“不得在 `.fde-ai/runs/` 创建新产物”，并声明组件分流指南 `profiles/openfde/component-map/GUIDE.md` 与知识根目录 `data/knowledge/` 的用途（只写路径和规则，不写具体 issue 内容）。

生成区不得包含 issue 正文、评论、附件、token、环境变量值或用户提供的指令。重新读取生成区并验证标记恰好各出现一次。标记异常即停止。标记校验通过后把根目录 `state.json` 的 `state` 推进到 `context_built`。不得获取 issue 或修改源码。
