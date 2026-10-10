# OpenFDE Issue AI Assistant

这是 OpenFDE 的 issue 分析自动化项目。它读取 `openfde/openfde` issue、评论、日志与截图附件，按 `fde-manifests` 定位源码，在本地只读树（`fde-sources/`）中分析，并输出根因、修复建议、未验证 patch 与 GitHub 评论草稿。需要编译验证时，可通过 profile `build` 配置的授权助手在受控构建树内临时应用 patch 进行受限构建并回滚。

它**不会**提交、推送、创建 PR、关闭 issue 或发布评论；除授权构建助手外，不修改源码、不构建、不安装、不测试。所有 patch 仅供 issue 用户自行审阅和验证，构建产物按构建证据登记、不等同于用户验证。

服务器上以 `aosp17-ai` 容器运行（含 Node/Pi/gh 与本地 AOSP 源码树的部署脚本），见 [服务器部署（aosp17-ai 容器）](deploy/server/README.md)。

## 从零开始：Docker 常驻扫描

### 1. 准备项目与凭据

项目根目录必须有 `fde-manifests/`。若不存在：

```sh
git clone https://src.ift.run/openfde17/fde-manifests fde-manifests
```

在启动 Docker 的同一 shell 或服务环境中提供凭据：

```sh
export GH_TOKEN='GitHub token'
export DEEPSEEK_API_KEY='DeepSeek token'
```

不要把 token 写入仓库、JSON 配置、日志或 issue 工件。`GH_TOKEN` 用于容器内 `gh`；宿主机 CLI 也可改用已登录的 `gh auth login`。

### 2. 启动

```sh
docker compose up -d --build --force-recreate scanner
```

首次立即扫描，之后每 30 分钟扫描一次。每轮使用 `scan.sync_page_size`（默认 100，最大 100）的 GitHub GraphQL 分页同步，并将游标保存在持久化数据卷；扫描器会跨轮继续，直到完整覆盖所有 open issue，再开始下一轮同步。`max_workers_per_run` 只限制每轮分析数，不会截断发现范围。`worker.execute=true` 使扫描器自动分析 issue；设为 `false` 时只发现和入队。

### 3. 查看与停止

```sh
docker compose logs -f scanner
docker compose down
```

`down` 保留 Docker 卷中的队列、日志、issue 工件和源码缓存；不要使用 `down -v`，除非确认要丢弃这些本地数据。

### 4. 代码或 skill 更新后

容器不会自动获得工作区的新代码。每次更新协调器、skills、profile 或 Dockerfile 后执行：

```sh
docker compose up -d --build --force-recreate scanner
```

所有 `docker compose` 命令都要求当前环境同时有 `GH_TOKEN` 和 `DEEPSEEK_API_KEY`。

## 直接分析一个 Issue

无需等待定时扫描：

```sh
docker compose exec scanner python automation/openfde_ai_server.py \
  --workspace /workspace \
  --config config/openfde-ai-server.json \
  analyze --issue 470
```

它使用与定时扫描完全相同的连续状态机。一个 issue 会连续推进原子 skill，直到 `archived`、`needs_information`、`blocked`，或到达 `max_atomic_steps_per_issue`；到达上限会重新入队，不会误标为完成。

宿主机直接运行、Pi 交互、systemd 部署、日志与排障见[使用指南](docs/guides/usage.md)。

## 结果在哪里

每个 issue 的工件只有一个固定目录：

```text
.fde-ai/issues/<issue号>/
├── state.json
├── input/      # issue、评论、附件（含截图）
├── evidence/   # 日志摘录与证据
├── analysis/   # 源码追溯与校验
├── solution/   # 修复方案
├── patch/      # 0001-<名称>.patch、元数据、校验
├── build/      # 受控构建请求、结果与产物登记
├── comment/    # 未发布的评论草稿
└── archive/    # 历史 revision 索引
```

唯一 patch 入口为 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`，并始终标注 `not_run` 与 `unverified_suggestion`（构建完成前）。

## 文档

- [使用指南](docs/guides/usage.md)：Docker、CLI、Pi、状态、日志、patch、停止与排障。
- [Docker 部署](docs/guides/docker-deployment.md)：容器运行细节。
- [服务器部署](docs/guides/server-deployment.md)：systemd 服务账户与定时器。
- [aosp17-ai 容器部署](deploy/server/README.md)：服务器构建/运行脚本与受控构建助手。
- [Pi 交互分析](docs/guides/pi-usage.md)：在 Pi 中使用 skills。
- [Issue 工件目录](docs/architecture/artifact-layout.md)：工件格式约束。
- [工作流架构](docs/architecture/workflow.md)：安全边界和步骤图。
