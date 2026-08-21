# OpenFDE 缺陷工作流设计（归档）

> **归档提示：** 仅供历史参考，不可作为当前操作依据。

本文件记录的是早期 OpenFDE 专用技能设计，涉及的 `setup-openfde-analysis`、`openfde-bug-workflow` 等旧技能已删除，不得再作为执行依据。

当前权威设计与使用入口如下：

- [当前工作流架构](../../architecture/workflow.md)
- [Pi 交互分析](../../guides/pi-usage.md)
- [服务器部署与运维](../../guides/server-deployment.md)
- [服务器工作进程](../../architecture/server-worker.md)

当前流程仅使用项目根目录 `skills/` 下的通用技能、`profiles/openfde/profile.json` 和 `automation/openfde_ai_server.py`。服务器协调器只负责调度 Pi；源码与缓存保持只读，补丁仅为未经验证的建议。
