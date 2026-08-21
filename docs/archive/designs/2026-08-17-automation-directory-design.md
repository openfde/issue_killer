# 自动化目录合并设计

> **归档提示：** 仅供历史参考，不可作为当前操作依据。

## 目标

将根目录的 `server/` 与 `tools/` 合并为 `automation/`，减少顶层职责分散，同时保留现有脚本文件名和运行行为。

## 目标目录

```text
automation/
  openfde_ai_server.py   # 原 server/openfde_ai_server.py；调度 Pi 技能
```

`automation/` 只存放服务器协调器。它负责队列和 Pi 工作进程调度，不包含问题分析逻辑、技能说明、配置、源码、问题证据或下载缓存。问题分析只由 `skills/run-issue-workflow` 及其原子技能完成。

## 不变项

- `skills/` 仍是 Pi 可发现的通用技能目录，`.pi/skills/` 的链接不变。
- `profiles/`、`config/`、`deploy/`、`tests/`、`docs/` 保持原位置和职责。
- `fde-manifests/`、`sources/`、`.fde-ai/` 是清单、源码/缓存或审计数据，不移动、不删除、不重写。
- 所有安全边界不变：不得修改源码、应用补丁、构建、测试、提交、推送或创建 PR。

## Git 忽略规则

根目录当前尚未初始化为 Git 仓库；迁移时仍创建 `.gitignore`，以便后续初始化或被纳入上级仓库时立即生效。它必须忽略本地、可再生或可能含敏感信息的数据：

- `sources/`：本地源码检出副本；
- `fde-manifests/`：独立克隆的 OpenFDE 清单仓库；
- `.fde-ai/`：问题证据、运行产物、缓存和本地 SQLite 数据；
- `data/`：服务器运行时队列、日志和锁；
- `config/openfde-ai-server.json`：部署专用配置；
- `__pycache__/`、`*.py[cod]`：Python 字节码缓存。

不得忽略 `config/openfde-ai-server.example.json`、`profiles/`、`skills/`、`automation/`、`deploy/`、`tests/` 或 `docs/`。`fde-manifests/` 保持其独立来源和本地路径；本次不会将它作为嵌套仓库加入主仓库。

## 路径迁移

将所有项目自有引用同步为新路径：

| 旧路径 | 新路径 | 受影响位置 |
| --- | --- | --- |
| `server/openfde_ai_server.py` | `automation/openfde_ai_server.py` | systemd 服务、部署/使用文档、测试命令 |
| `tools/openfde_workflow.py` | 删除 | 旧产物工具、配置、文档和测试 |

不保留旧路径兼容包装器，避免出现两个看似可用的入口。CLI 的正式入口改为：

```sh
python3 automation/openfde_ai_server.py --help
```

## 清理与验证

迁移后删除已空的 `server/`、`tools/` 目录以及其中/测试目录下可再生的 `__pycache__/`。随后执行：

```sh
python3 -m unittest tests/test_openfde_workflow.py tests/test_openfde_ai_server.py -v
python3 -m py_compile automation/openfde_ai_server.py
rg -n 'automation/openfde_workflow\.py|tools/openfde_workflow\.py' \
  AGENTS.md config deploy docs profiles skills tests automation
```

最后一条检索应无结果；测试与编译检查必须成功。

## 回滚

这是纯路径迁移，没有改变队列或工作流数据格式。若验证失败，只需将两个脚本移回原目录并还原引用；`fde-manifests/`、`sources/` 和 `.fde-ai/` 不受影响。
