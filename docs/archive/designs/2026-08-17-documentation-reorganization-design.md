# 文档体系重组设计

> **归档提示：** 仅供历史参考，不可作为当前操作依据。

## 目标

将当前操作文档、架构说明与历史记录分离。用户和运维人员只需阅读 `README.md`、`docs/README.md`、`docs/guides/` 与 `docs/architecture/`；历史设计和计划不得再被当作操作指南。

## 目标结构

```text
README.md
docs/
  README.md
  guides/
    pi-usage.md
    server-deployment.md
  architecture/
    workflow.md
    server-worker.md
  archive/
    designs/
    plans/
```

## 内容边界

- `README.md`：项目用途、目录职责、快速入口与文档导航。
- `docs/README.md`：按角色列出阅读顺序和链接。
- `docs/guides/`：只写可直接执行的 Pi、CLI、部署和运维步骤。
- `docs/architecture/`：只描述当前系统：`automation/openfde_ai_server.py` 调度 Pi 的 `run-issue-workflow` 技能；补丁只作为未验证建议。
- `docs/archive/`：保存历史设计和计划，每个文件都声明“仅供历史参考，不可作为当前操作依据”。

## 迁移规则

| 当前文件 | 目标文件 | 处理方式 |
| --- | --- | --- |
| `docs/openfde-bug-workflow-usage.md` | `docs/guides/pi-usage.md` | 移动并更新链接与当前入口。 |
| `docs/openfde-pi-server-deployment.md` | `docs/guides/server-deployment.md` | 移动并更新链接与当前入口。 |
| `docs/openfde-ai-server-workflow-design.md` | `docs/architecture/workflow.md` | 精简为当前架构，删除旧工具/测试引用。 |
| `docs/superpowers/specs/2026-08-17-openfde-pi-server-design.md` | `docs/architecture/server-worker.md` | 移动并更新当前路径。 |
| 其余 `docs/superpowers/specs/` | `docs/archive/designs/` | 移动，并在首部加入归档提示。 |
| `docs/superpowers/plans/` | `docs/archive/plans/` | 移动，并在首部加入归档提示。 |

## 一致性要求

- 当前文档不得出现 `automation/openfde_workflow.py`、`tools/openfde_workflow.py`、`server/openfde_ai_server.py`、已删除技能名或已删除测试文件。
- 当前文档中的服务器入口只能是 `python3 automation/openfde_ai_server.py`。
- 所有内部 Markdown 链接必须解析到存在的文件。
- 文档保持中文；命令、路径、技能名与状态值保留其机器可读拼写。

## 验证

运行技能与服务器测试；扫描当前文档中的旧路径；逐一验证 `README.md` 与 `docs/README.md` 的内部链接。归档文档可提及历史名称，但必须带有不可执行提示。
