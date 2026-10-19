# Docker 部署（无需 AOSP 构建）

根目录 [README](../../README.md) 是完整入口。本页只补充容器部署细节。

适用：Linux 服务器 + Docker Compose v2；不需要 AOSP 构建工具链，只需要 `fde-manifests` 与 `fde-sources`（首次可自动同步模块子集）。

## 前置

```sh
cp deploy/server/env.example .env
# 编辑 .env：GH_TOKEN、DEEPSEEK_API_KEY（可选 PI_BASE_URL）
```

`GH_TOKEN` 需要 issue 读取、评论、创建 PR 的权限；`.env` 已被 `.gitignore` 忽略。

## 一键启动

```sh
./deploy/docker/up.sh
```

脚本会：检查 Docker/Compose 与凭据 → 生成 `config/openfde-ai-server.json` → 缺失时克隆 `fde-manifests` → 构建镜像 → 启动 `sources-sync`、`scanner`、`poller`。

首次启动时 `sources-sync` 会按 `FDE_SOURCE_MODULES`（默认 `art build device external frameworks hardware openfde-sdk packages prebuilts system`）执行 `repo init/sync`；`scanner`/`poller` 会等它完成后才启动。

```sh
docker compose logs -f sources-sync
docker compose logs -f scanner poller
docker compose ps
```

已有源码树（非空且无 `.repo`）会被原样复用，不会覆盖。

## 交互式 Pi

```sh
docker compose exec scanner pi
```

或在独立 shell 中运行（不影响 scanner/poller）：

```sh
docker compose --profile tools up -d shell
docker compose exec shell pi
```

## 服务与卷

| 服务/卷 | 说明 |
| --- | --- |
| `sources-sync` | 一次性：初始化/更新源码子集；以 root 写入并 `chmod -R a+rX` |
| `scanner` | 定时扫描 + worker，按 `SCAN_INTERVAL_SECONDS`（默认 1800）循环 |
| `poller` | 回复轮询，`REPLY_POLL_SECONDS`（默认 300） |
| `shell` | 交互式 Pi（profile `tools`） |
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

- `sources-sync` 失败：查看日志；检查 `FDE_MANIFEST_URL`/`FDE_MANIFEST_BRANCH` 网络可达性；可用 `FDE_SOURCE_MODULES` 缩小范围；
- 容器内 `gh` 未认证：确认 `.env` 的 `GH_TOKEN` 非空并重建容器；
- 交互 Pi 仍是旧技能：退出 Pi 进程并重新 `docker compose exec`（新进程）；
- 源码权限：确认 bind mount 目录对 UID 1000 可读，或重新运行 `sources-sync` 的 `chmod -R a+rX`。
