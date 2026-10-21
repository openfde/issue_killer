# 文档索引

本目录分为当前文档与历史归档。日常使用只阅读“指南”和“架构”；`archive/` 中的内容仅用于追溯，不可作为当前操作依据。

## 按角色阅读

| 角色 | 先读 | 再读 |
| --- | --- | --- |
| 演示/培训 | [496 端到端 Demo](demos/issue-496-walkthrough.md) | [Pi 交互分析](guides/pi-usage.md) |
| 日常运行、CLI、查看 patch | [服务器 CLI 使用指南](guides/usage.md) | [Issue 工件目录](architecture/artifact-layout.md) |
| 使用 Pi 分析单个问题 | [Pi 交互分析](guides/pi-usage.md) | [工作流架构](architecture/workflow.md) |
| Docker 部署/维护服务器 | [README 4.3 Docker 一键部署](../README.md#43-docker-一键部署推荐) | [Docker 容器运维](guides/docker-deployment.md) |
| 部署/维护宿主服务 | [服务器部署与运维](guides/server-deployment.md) | [服务器工作进程](architecture/server-worker.md) |
| 查阅历史决策 | [历史设计](archive/designs/README.md) | [历史实施计划](archive/plans/README.md) |

## 当前文档

- [496 端到端 Demo](demos/issue-496-walkthrough.md)：从取证采集、分析、修复方案、PR 到验证的完整对话示例。
- [服务器 CLI 使用指南](guides/usage.md)：队列、扫描、日志与 patch（安装/Pi/Docker 见 README）。
- [Docker 容器运维](guides/docker-deployment.md)：日常命令、服务与卷、停止清理；完整安装见 README 4.3。
- [Pi 交互分析](guides/pi-usage.md)：Pi 的 skill 调用细节。
- [服务器部署与运维](guides/server-deployment.md)：宿主机 systemd 部署。
- [工作流架构](architecture/workflow.md)：当前流程、证据/源码边界、补丁与知识沉淀。
- [取证采集](architecture/intake.md)：提 issue 前的三通道采集、体积与安全约束。
- [组件归属](architecture/component-attribution.md)：三层归属（知识/本地树/manifest）与人工回退闭环。
- [Issue 工件目录](architecture/artifact-layout.md)：每个 issue 的固定产物位置与 patch 入口。
- [服务器工作进程](architecture/server-worker.md)：队列、Pi 进程和并发语义。
- [Server、Pi 与 Skills 执行流程](architecture/server-pi-flow.md)：定时扫描、CLI、Pi 原子 skill 与状态机循环图。

## 历史归档

- [历史设计](archive/designs/README.md)：早期方案与目录迁移记录。
- [历史实施计划](archive/plans/README.md)：已完成或已替代的实施计划。
