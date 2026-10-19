# Docker 部署（无需 AOSP 构建）

本页是完整的 Docker 部署步骤，与 [README 6.9](../../README.md#69-docker-一键部署无-aosp-构建推荐) 保持一致；通用配置（profile、skills、工作流）见 README。

适用：Linux 服务器 + Docker Compose v2；不需要 AOSP 构建工具链。首次默认从 GitHub 镜像同步分析所需源码，之后启动 `scanner` + `poller`，可用容器内 `pi` 交互。

## 1. 安装 Docker 与 Compose v2

优先使用官方脚本：

```sh
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version && docker compose version
```

如果 `download.docker.com` 被网络阻断，改用 Ubuntu 源：

```sh
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
docker --version && docker compose version
```

其他发行版安装 Docker Engine + Compose v2 插件即可，最终确认 `docker compose version` 可用。

## 2. Docker Hub 被阻断时配置镜像加速

```sh
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{
  "registry-mirrors": ["https://docker.m.daocloud.io", "https://docker.1ms.run"]
}
EOF
sudo systemctl restart docker
docker pull node:24-bookworm-slim
```

镜像源由第三方提供，仅在 Docker Hub 不可达时使用。

## 3. 获取代码

```sh
git clone git@src.ift.run:ai-apps/fde-ai-assistant.git
cd fde-ai-assistant
```

无法访问内网 Git 时，可从已有环境同步代码（不拷贝 11G 源码）：

```sh
mkdir -p ~/fde-ai-assistant && cd ~/fde-ai-assistant
rsync -a --exclude fde-sources --exclude fde-manifests --exclude .fde-ai --exclude data \
  huyang@192.168.227.129:~/fde-ai-assistant/ ./
```

## 4. 配置凭据

```sh
export GH_TOKEN='...'                 # issue 读取、评论、创建 PR
export DEEPSEEK_API_KEY='...'         # 默认模型
# 其他模型示例：
# export PI_PROVIDER=openai PI_MODEL=<model> OPENAI_API_KEY='...'
# export PI_BASE_URL=https://...      # OpenAI 兼容网关
```

`GH_TOKEN` 的创建与权限（经典 PAT `repo` + `read:org`，或 fine-grained Issues/Contents/PR 读写 + Metadata 读取）见 [README 4.4](../../README.md#44-github-token-配置ghtoken)。容器不共享宿主机 `gh` 登录态，必须显式传入；更换 token 后重新 `up.sh`。

`up.sh` 首次运行会自动生成 `.env`；已 export 的变量优先，不会被 `.env` 覆盖。也可以直接编辑 `.env`。`.env` 已被 `.gitignore` 忽略。

## 5. 一键启动

```sh
./deploy/docker/up.sh
```

脚本会：自动生成 `.env` → 检查 Docker/Compose 与凭据 → 生成 `config/openfde-ai-server.json` → 缺失时克隆 `fde-manifests` → 构建镜像 → 启动 `sources-sync`、`scanner`、`poller`。

首次启动时 `sources-sync` 默认按 `deploy/docker/github-sources.tsv` 同步 GitHub 镜像（48 个仓库，分支 `fde_17`），并按 `FDE_SOURCE_MODULES`（默认 `art build device external frameworks hardware openfde-sdk packages prebuilts system`）过滤模块；`scanner`/`poller` 会等它完成后才启动。

```sh
docker logs -f openfde-ai-sources    # 首次源码同步；完成后退出码 0
docker compose ps -a
docker logs -f openfde-ai            # scanner
docker logs -f openfde-ai-poller     # 回复轮询
```

已有仓库会被复用；`FDE_SYNC_MODE=repo` 可改用 Android `repo init/sync`（内部 GitLab 可达时），`FDE_SYNC_MODE=none` 可完全跳过同步。国内网络可在 `.env` 设置 `NPM_REGISTRY` / `REPO_URL` 覆盖镜像构建源。

## 6. 验证安装

```sh
docker exec -it openfde-ai bash
pi --version
rg --version
gh auth status
pi auth check --provider deepseek --model deepseek-flash
ls .pi/skills | wc -l                 # 34
git -C fde-sources/frameworks/base rev-parse --short HEAD
pi --no-session -p "回复 OK"
pi
```

- `gh auth status` 提示缺少 `read:org` 不影响 issue 读取；补 scope 后重建容器即可。
- 模型调用返回 `OK` 表示 provider/key 正常；其他模型替换 `--provider/--model`。

容器内跑一条只读 skill 验证：

```text
/skill:list-github-issues 使用 profiles/openfde/profile.json 列出全部问题的编号、状态、标题、标签和更新时间；不要下载详情或写入 GitHub。
```

## 7. 交互式 Pi（短命令）

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

独立 shell（不影响 scanner/poller；启动前先 export 凭据，或把凭据写入 `.env`）：

```sh
docker compose --profile tools up -d shell
docker exec -it openfde-ai-shell pi
```

容器内 Pi 的会话保存在 `/tmp/pi-agent`（临时）；技能更新后退出并重新进入即可。

## 8. 模型配置

| 变量 | 说明 |
| --- | --- |
| `PI_PROVIDER` | Pi 提供方，默认 `deepseek` |
| `PI_MODEL` | 模型，默认 `deepseek-flash` |
| `PI_BASE_URL` | OpenAI 兼容网关地址（可选） |
| `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `GOOGLE_API_KEY` | 对应提供方凭据 |

entrypoint 会根据 `PI_PROVIDER`/`PI_MODEL` 生成 `settings.json`；用 `pi auth check --provider <p> --model <m>` 检查提供方就绪状态。

## 9. scanner 工作模式

`config/openfde-ai-server.json` 的 `worker.execute`：

- `true`：扫描并自动分析 issue（会产生模型调用）；
- `false`：只发现/入队，不自动分析（验证安装时建议）。

修改后执行：

```sh
docker restart openfde-ai
```

## 10. 服务与卷

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

## 11. 更新、停止与清理

```sh
cd ~/fde-ai-assistant

# 代码/skill 更新后：带凭据重建（推荐 up.sh，避免新容器丢失 token）
export GH_TOKEN=...
export DEEPSEEK_API_KEY=...
./deploy/docker/up.sh

# 只停止并删除容器；保留命名卷
docker compose down

# 同时删除容器内 .fde-ai/data 卷（不动 fde-sources/fde-manifests）
docker compose down -v

# 清理构建产生的 <none> 悬空镜像
docker image prune -f

# 可选：删除应用镜像，下次 up 重新构建
docker rmi openfde-ai-assistant:pi

# 强制重新同步源码子集
FORCE_SYNC=1 ./deploy/docker/up.sh
```

`docker compose down` 必须在 `compose.yaml` 所在目录执行；在 `~` 下会报 `no configuration file provided`。不要用 `docker compose up -d --force-recreate` 直接重建而不导出凭据，否则新容器会缺少 `GH_TOKEN`/模型 key。

## 12. 排障

- **Docker Hub i/o timeout**：配置第 2 步的 `registry-mirrors` 并重启 Docker；
- **`download.docker.com` 连接重置**：改用第 1 步的 `docker.io` + `docker-compose-v2`；
- **`docker compose` 不存在**：安装 Compose v2 插件（`docker-compose-v2` 或 Docker 官方 repo）；
- **`.bashrc` 里 source 不生效**：Ubuntu `.bashrc` 对非交互 shell 会提前 `return`；直接 `export` 或写入 `.env`；
- **`docker compose down` 报找不到配置**：先 `cd ~/fde-ai-assistant`；
- **`sources-sync` 失败**：查看 `docker logs openfde-ai-sources`；默认 GitHub 模式检查 GitHub 网络，repo 模式检查 `FDE_MANIFEST_URL`/`FDE_MANIFEST_BRANCH`；可用 `FDE_SOURCE_MODULES` 缩小范围，或 `FDE_SYNC_MODE=none` 使用已有源码；
- **容器内 `gh` 未认证**：确认 `GH_TOKEN` 非空并重建容器（`./deploy/docker/up.sh`）；
- **`gh auth status` 提示缺少 `read:org`**：补经典 PAT 的 `read:org`（或 fine-grained 的 Organization Members `Read`），重新授权后重建；
- **交互 Pi 仍是旧技能**：退出 Pi 进程并重新 `docker exec -it openfde-ai pi`（新进程）；
- **模型不可用**：`pi auth check --provider <p> --model <m>`，检查对应 API key / `PI_BASE_URL`；
- **token 更新不生效**：容器环境变量在创建时固定；重新运行 `./deploy/docker/up.sh`；
- **源码权限**：确认 bind mount 目录对 UID 1000 可读，或重新运行 `sources-sync` 的 `chmod -R a+rX`。
