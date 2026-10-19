# Docker 部署（无需 AOSP 构建）

根目录 [README](../../README.md) 是完整入口；**安装 Docker/Compose、Docker Hub 镜像加速、首次源码同步、验证与排障见 [README 6.9](../../README.md#69-docker-一键部署无-aosp-构建推荐)**。本页只补充容器运行细节。

适用：Linux 服务器 + Docker Compose v2；不需要 AOSP 构建工具链，只需要 `fde-manifests` 与 `fde-sources`（首次默认从 GitHub 镜像同步模块子集）。

## 前置：export 凭据（`.env` 会自动生成）

```sh
export GH_TOKEN='...'                 # issue 读取、评论、创建 PR
export DEEPSEEK_API_KEY='...'         # 默认模型
# 其他模型示例：
# export PI_PROVIDER=openai PI_MODEL=<model> OPENAI_API_KEY='...'
# export PI_BASE_URL=https://...      # OpenAI 兼容网关
```

`GH_TOKEN` 的创建与权限（经典 PAT `repo`+`read:org`，或 fine-grained Issues/Contents/PR 读写 + Metadata 读取）见 [README 4.4](../../README.md#44-github-token-配置ghtoken)。容器不共享宿主机 `gh` 登录态，必须显式传入；更换 token 后重新 `up.sh`。

`up.sh` 首次运行会自动生成 `.env`；已 export 的变量优先，不会被 `.env` 覆盖。也可以直接编辑 `.env`。`.env` 已被 `.gitignore` 忽略。

## 一键启动

```sh
./deploy/docker/up.sh
```

脚本会：自动生成 `.env` → 检查 Docker/Compose 与凭据 → 生成 `config/openfde-ai-server.json` → 缺失时克隆 `fde-manifests` → 构建镜像 → 启动 `sources-sync`、`scanner`、`poller`。

首次启动时 `sources-sync` 默认按 `deploy/docker/github-sources.tsv` 同步 GitHub 镜像（48 个仓库，分支 `fde_17`），并按 `FDE_SOURCE_MODULES`（默认 `art build device external frameworks hardware openfde-sdk packages prebuilts system`）过滤模块；`scanner`/`poller` 会等它完成后才启动。

```sh
docker logs -f openfde-ai-sources    # 首次源码同步
docker logs -f openfde-ai            # scanner
docker logs -f openfde-ai-poller     # 回复轮询
```

已有仓库会被复用；`FDE_SYNC_MODE=repo` 可改用 Android `repo init/sync`（内部 GitLab 可达时），`FDE_SYNC_MODE=none` 可完全跳过同步。

## 交互式 Pi（短命令）

进入运行中的容器，然后直接运行 `pi`：

```sh
docker exec -it openfde-ai bash
pi
```

或直接进入 Pi：

```sh
docker exec -it openfde-ai pi
./deploy/docker/pi.sh        # 等价
```

退出：

- `pi` 内输入 `/quit` 或 `/exit`（也可 `Ctrl+D`）；
- 回到容器 shell 后输入 `exit`（或 `Ctrl+D`）返回宿主机；
- 直接 `docker exec -it openfde-ai pi` 时，退出 Pi 即回到宿主机；
- 退出 `exec` 不会停止 scanner/poller；停止服务用 `docker compose down`。

独立 shell（不影响 scanner/poller）：

```sh
docker compose --profile tools up -d shell
docker exec -it openfde-ai-shell pi
```

容器内 Pi 的会话保存在 `/tmp/pi-agent`（临时）；技能更新后退出并重新进入即可。

## 模型配置

| 变量 | 说明 |
| --- | --- |
| `PI_PROVIDER` | Pi 提供方，默认 `deepseek` |
| `PI_MODEL` | 模型，默认 `deepseek-flash` |
| `PI_BASE_URL` | OpenAI 兼容网关地址（可选） |
| `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `GOOGLE_API_KEY` | 对应提供方凭据 |

entrypoint 会根据 `PI_PROVIDER`/`PI_MODEL` 生成 `settings.json`；`pi auth` 可检查提供方就绪状态。

## 服务与卷

| 服务/容器 | 说明 |
| --- | --- |
| `sources-sync` / `openfde-ai-sources` | 一次性：初始化/更新源码子集（默认 GitHub 镜像，可切换 repo 模式）；以 root 写入并 `chmod -R a+rX` |
| `scanner` / `openfde-ai` | 定时扫描 + worker，按 `SCAN_INTERVAL_SECONDS`（默认 1800）循环 |
| `poller` / `openfde-ai-poller` | 回复轮询，`REPLY_POLL_SECONDS`（默认 300） |
| `shell` / `openfde-ai-shell` | 交互式 Pi（profile `tools`） |
| `openfde_ai_state` | `/workspace/.fde-ai`（issue 工件） |
| `openfde_ai_data` | `/workspace/data`（队列、日志、知识库） |
| `fde-sources` / `fde-manifests` | 源码与清单 bind mount；运行时只读 |

`scanner` 与 `poller` 共享 `.fde-ai/issues/<编号>/.workflow.lock`，避免同一 issue 并发执行。`sources-sync` 与其余服务以不同属主访问源码（同步 root、运行 agent/UID 1000）。

## 更新与停止

```sh
# 代码/skill 更新后重建
docker compose build
docker compose up -d --force-recreate

# 强制重新同步源码子集
FORCE_SYNC=1 ./deploy/docker/up.sh

# 停止但保留队列/工件
docker compose down
```

不要使用 `docker compose down -v`，除非确认要丢弃命名卷中的队列、日志与 issue 工件。

## 排障

- `sources-sync` 失败：查看 `docker logs openfde-ai-sources`；默认 GitHub 模式检查 GitHub 网络，repo 模式检查 `FDE_MANIFEST_URL`/`FDE_MANIFEST_BRANCH`；可用 `FDE_SOURCE_MODULES` 缩小范围，或 `FDE_SYNC_MODE=none` 使用已有源码；
- 容器内 `gh` 未认证：确认 `.env` 的 `GH_TOKEN` 非空并重建容器；
- 交互 Pi 仍是旧技能：退出 Pi 进程并重新 `docker exec -it openfde-ai pi`（新进程）；
- 模型不可用：检查 `PI_PROVIDER`/`PI_MODEL` 与对应 API key（`pi auth`）；
- 源码权限：确认 bind mount 目录对 UID 1000 可读，或重新运行 `sources-sync` 的 `chmod -R a+rX`。
