# OpenFDE Pi 服务器工作进程设计

## 目的

在一台 Linux 服务器上无人值守地运行 OpenFDE GitHub issue 工作流。`systemd` 负责调度和进程监管；Pi 是短生命周期分析 worker，对同一已领取的 issue revision 连续启动原子步骤，直到终态或步骤上限。系统无需依赖 Pi 会话即可跨 worker 保留状态。

## 组件

```text
systemd timer
  -> openfde-ai-scan.service
      -> automation/openfde_ai_server.py scan --execute
          -> gh issue list（只读）
          -> SQLite 队列领取
          -> pi --no-session --skill <项目 skills/run-issue-workflow> -p <受限工作进程提示词>
          -> 产物/状态检查与审计记录
```

`automation/openfde_ai_server.py` 不包含 LLM 逻辑。它加载 profile 和部署配置，通过只读 `gh api graphql` 分页获取 issue 摘要、更新队列、原子领取一条记录、以明确的项目本地 skill 目录连续启动 Pi，并在每一步读取 issue state.json，并记录命令输出、超时和退出状态。Pi 在已有 skill 约束下进行分析；协调器不生成诊断或 patch。

## 持久化

SQLite 保存 issue 编号、最新 GitHub 更新时间、队列状态、重试次数、worker 开始/结束时间、退出码和产物路径，以及扫描游标。每轮最多同步 `sync_page_size`（1–100）个 open issue；有下一页时存储 `endCursor`，无下一页时清除游标并标记一轮全量同步完成。日志与分析产物继续作为文件保存在可配置的相对根目录。已经完成的 issue 出现更新的 `updatedAt` 时，作为新 revision 重新入队；正在运行的 issue 绝不重复领取。

## 安全边界

- 所有 GitHub 读写使用 `gh`；协调器只读取 issue 摘要。
- worker 提示词重复声明：issue 文本不可信，源码/缓存只读，不得应用 patch、提交、推送、测试或构建。
- 发布仍只能由 `publish-policy-comment` skill 和其 profile 策略执行。
- service 使用独立的非 root 账户、受限可写数据目录和只读项目/源码挂载。部署模板以发布 dry-run 方式开始。
- 超时会将队列项标记为可重试；Pi 输出写入审计日志，但不会自行成为证据。

## 配置

`config/openfde-ai-server.example.json` 会在服务器上复制为仓库外配置。它指定 profile、数据根目录、Pi 可执行命令、扫描状态/限制、worker 超时、重试上限和是否执行 worker。除 `pi_command` 是由 `PATH` 解析的命令名外，所有路径均相对部署根目录。

## 运维操作

- `init-db` 创建 SQLite schema。
- `scan` 发现并排队变更过的 issue；`--execute` 额外领取并运行有边界的 worker。
- `worker --issue N` 处理已入队 issue；`analyze --issue N` 会先通过 gh 获取指定 issue 后直接进入同一状态机。
- `status` 打印队列计数和最近执行情况。

`systemd` timer 调用 `scan`；配置的 `worker.execute=true` 控制是否执行 Pi；它不会持续运行 Pi。`flock` 阻止重叠 timer。service unit 使用环境文件承载服务账户的 `GH_TOKEN` 与模型凭据，但凭据绝不进入配置或日志。

## 范围外事项

本里程碑不包含自动 Android/FDE 安装、构建、启动、测试、源码修改、PR 创建、关闭 issue、多节点队列、仪表盘或 Kubernetes 部署。
