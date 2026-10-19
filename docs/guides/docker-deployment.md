# Docker 容器运维（速查）

完整安装、Docker/Compose 安装、镜像加速、凭据/模型配置、首次启动与验证见 [README 4.3](../../README.md#43-docker-一键部署推荐)。本页只列日常容器运维，避免重复安装步骤。

## 日常命令

```sh
cd ~/fde-ai-assistant

# 启动/更新（带凭据；首次会自动生成 .env、同步源码、构建）
export GH_TOKEN='...'
export DEEPSEEK_API_KEY='...'
./deploy/docker/up.sh

# 容器内 Pi
docker exec -it openfde-ai bash
pi

# 或直接进入 Pi
docker exec -it openfde-ai pi
./deploy/docker/pi.sh

# 日志
docker logs -f openfde-ai-sources
docker logs -f openfde-ai
docker logs -f openfde-ai-poller
```

退出：`pi` 内 `/quit` 或 `/exit`（`Ctrl+D`）；容器 shell 内 `exit`（`Ctrl+D`）。退出 `exec` 不会停止服务。

## 服务与卷

| 服务/容器 | 说明 |
| --- | --- |
| `sources-sync` / `openfde-ai-sources` | 一次性：初始化/更新源码子集；完成后退出码 0 |
| `scanner` / `openfde-ai` | 定时扫描 + worker；`worker.execute` 控制是否自动分析 |
| `poller` / `openfde-ai-poller` | 回复轮询（默认 300 秒） |
| `shell` / `openfde-ai-shell` | 交互式 Pi（profile `tools`） |
| `openfde_ai_state` | `/workspace/.fde-ai`（issue 工件） |
| `openfde_ai_data` | `/workspace/data`（队列、日志、知识库） |
| `fde-sources` / `fde-manifests` | 源码与清单 bind mount；运行时只读 |

`scanner` 与 `poller` 共享 `.fde-ai/issues/<编号>/.workflow.lock`，避免同一 issue 并发执行；源码同步以 root 写入，运行服务以 UID 1000 只读访问。

## 停止与清理

```sh
cd ~/fde-ai-assistant

docker compose down          # 停止并删除容器；保留命名卷
docker compose down -v       # 同时删除容器内 .fde-ai/data 卷（不动 fde-sources/fde-manifests）
docker image prune -f        # 清理构建产生的 <none> 悬空镜像
docker rmi openfde-ai-assistant:pi   # 可选：删除镜像，下次 up 重新构建
```

`docker compose down` 必须在 `compose.yaml` 所在目录执行；在 `~` 下会报 `no configuration file provided`。不要直接 `docker compose up -d --force-recreate` 而不导出凭据，否则新容器会缺少 `GH_TOKEN`/模型 key；用 `up.sh` 重建。

## 容器侧排障

- `sources-sync` 失败：`docker logs openfde-ai-sources`；默认 GitHub 模式检查 GitHub 网络，repo 模式检查 `FDE_MANIFEST_URL`/`FDE_MANIFEST_BRANCH`；可用 `FDE_SOURCE_MODULES` 缩小范围，或 `FDE_SYNC_MODE=none` 使用已有源码；
- `gh` 未认证：确认 `GH_TOKEN` 非空并重建容器（见 [README 4.2](../../README.md#42-凭据与模型)）；
- `read:org` 告警：补经典 PAT 的 `read:org` 或 fine-grained Organization Members `Read`，重新授权后重建；
- 模型不可用：`pi auth check --provider <p> --model <m>`，检查对应 API key / `PI_BASE_URL`；
- 交互 Pi 仍是旧技能：退出并重新 `docker exec -it openfde-ai pi`（新进程）；
- 源码权限：确认 bind mount 对 UID 1000 可读，或重跑 `sources-sync` 的 `chmod -R a+rX`。

安装/镜像加速/首次验证等通用问题见 [README 4.3](../../README.md#43-docker-一键部署推荐)。
