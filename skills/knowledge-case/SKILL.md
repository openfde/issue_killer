---
name: knowledge-case
description: 当需要把已归档 issue 采集为知识 case、重建 knowledge 索引或检查 case 状态时使用。
---

# 知识 case 采集与索引

把 `automation/capture_knowledge_case.py` 的采集/索引命令统一为 Pi skill。只操作 `data/knowledge/`，不改 issue 工件、不晋升 Wiki、不写 GitHub。

## 用法

```text
/skill:knowledge-case 采集问题 493
/skill:knowledge-case 归档问题 493
/skill:knowledge-case 重建索引
/skill:knowledge-case 查看问题 493
```

也接受自然语言：`把 493 做成知识 case`、`重建知识索引`、`看下 493 的知识状态`。

## 采集（capture）

1. 确认 workspace 根目录，且 `.fde-ai/issues/<编号>/state.json` 与 `.fde-ai/issues/<编号>/archive/case.json` 存在。
2. 执行：

   ```bash
   python3 automation/capture_knowledge_case.py --workspace . --issue <编号>
   ```

3. 校验以下文件存在且可读：

   - `data/knowledge/cases/<编号>/case.json`
   - `data/knowledge/cases/<编号>/case.md`
   - `data/knowledge/index.json`

4. 读取 `case.json`，报告 `knowledge_status`（`draft`/`verified`）、`verification.verified`、组件和证据来源。
5. 如果 `archive/case.json` 缺失或脚本非零退出，停止并报告；不要手工拼 case，不要伪造验证状态。

## 重建索引（rebuild）

```bash
python3 automation/capture_knowledge_case.py --workspace . --rebuild-index
```

完成后读取 `data/knowledge/index.json`，报告 case 数量、`verified`/`draft` 数量；索引为空是合法结果。

## 查看状态（status）

只读：

- 读 `data/knowledge/cases/<编号>/case.json`（存在时）；
- 读 `data/knowledge/index.json` 中对应条目；
- 报告 `knowledge_status`、`verification.verified`、来源哈希是否齐全；
- 不写文件、不重建索引。

## 边界

- 不把 `draft` 说成“已验证”；`verified` 只来自 `confirmed_fixed` 或人工确认。
- 不自动 `propose-knowledge` / `promote-knowledge`；晋升必须人工审核。
- 不修改源码、不关闭 issue、不发评论、不推送。
- 自动流程中由 `archive-case` 直接调用同一脚本；本 skill 是人工/交互入口。
