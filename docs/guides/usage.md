# 使用指南

本系统分析 `openfde/openfde` issue，按证据下载必要附件、读取 manifest、缓存只读源码，并输出根因分析、修复建议、未验证 patch 和 GitHub 评论草稿。

它不修改 OpenFDE 源码或源码缓存，不创建 PR，也不发布 GitHub 评论。唯一例外是 profile `build` 配置声明的授权构建助手：它在受控构建树内临时应用 patch、完成受限构建并在退出前回滚补丁（默认人工触发）。patch 仍是给 issue 用户自行验证的建议。

## 准备

在运行用户身份下完成：

```sh
gh auth login -h github.com
export DEEPSEEK_API_KEY='...'
```

`GH_TOKEN` 仅供 Docker 使用；不要把任意 token 写入 JSON、日志或 issue 工件。确保 `fde-manifests/` 已位于项目根目录。

配置文件是 `config/openfde-ai-server.json`。关键项：

```json
"worker": {
  "execute": true,
  "timeout_seconds": 1800,
  "retry_limit": 2,
  "max_atomic_steps_per_issue": 16
}
```

一次 issue 会连续执行原子 skill，直到 `archived`、`needs_information`、`blocked`，或达到步骤上限。上限到达时会重新入队，下一次扫描继续；不会将中间步骤误标为完成。

## Docker 定时扫描

先验证镜像：

```sh
docker run --rm openfde-ai-assistant:pi pi --version
```

启动常驻任务：

```sh
docker compose up -d --build scanner
```

容器立即扫描一次，之后按 `SCAN_INTERVAL_SECONDS`（默认 1800 秒）重复扫描。停止但保留队列、日志和工件：

```sh
docker compose down
```

查看容器扫描日志：

```sh
docker compose logs -f scanner
```

## 直接分析一个 Issue

Docker 方式：

```sh
docker compose exec scanner python automation/openfde_ai_server.py \
  --workspace /workspace \
  --config config/openfde-ai-server.json \
  analyze --issue 470
```

宿主机方式：

```sh
python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json \
  analyze --issue 470
```

`analyze` 先用 `gh issue view` 获取该编号，再进入与定时扫描相同的状态机；不需要先运行 `scan`。队列汇总：

```sh
python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json status
```

只扫描/入队但不运行 Pi：将 `worker.execute` 临时改为 `false` 后运行 `scan`。一次性扫描并强制本轮执行 Pi：

```sh
python3 automation/openfde_ai_server.py \
  --workspace "$PWD" \
  --config config/openfde-ai-server.json scan --execute
```

## Pi 交互式分析

在项目根目录运行 `pi`，输入 `/reload`，再在 Pi 对话中使用：

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 470；只读分析，不发布、不改源码、不构建、不测试。
```

人工模式必须在当前请求明确给出 issue 编号或 URL；skill 每次只推进一个原子步骤。完整交互细节见 [Pi 交互分析](pi-usage.md)。

## 查看结果

每个 issue 的唯一目录是：

```text
.fde-ai/issues/<issue号>/
├── state.json
├── input/
├── evidence/
├── analysis/
├── solution/
├── patch/
├── build/
├── comment/
└── archive/
```

patch 的唯一入口：

```text
.fde-ai/issues/<issue号>/patch/0001-<名称>.patch
```

它配有 `patch.json`、`validation.json`，其中应明确写有 base commit、SHA-256、证据 claim 和所有 `not_run` 项。评论草稿位于 `comment/github-comment.md`，不会被自动发布。需要编译验证时，先由 `request-build` 写出 `build/build-request.json`，再运行受控构建助手（默认人工）：

```sh
deploy/server/fde-ai-build.sh --issue 470
```

构建结果与产物哈希记录在 `build/build-result.json`，`collect-build-artifacts` 校验后写入 `build/artifacts.json`；补丁在构建结束后被助手回滚。

协调器每步的 Pi 输出位于 `data/logs/`；Docker 中为 `/workspace/data/logs/`，可执行：

```sh
docker compose exec scanner sh -lc 'find /workspace/data/logs -type f -print'
```

## 宿主机 systemd 定时任务

按照 [服务器部署与运维](server-deployment.md) 安装 `openfde-ai-scan.timer`。timer 调用同一个 `scan` 命令，配置中 `worker.execute=true` 时会自动推进 issue。

查看或停止：

```sh
sudo systemctl status openfde-ai-scan.timer
sudo journalctl -u openfde-ai-scan.service -f
sudo systemctl disable --now openfde-ai-scan.timer
```
