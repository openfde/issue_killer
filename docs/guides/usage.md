# 使用指南（服务器 CLI / 队列）

当前推荐流程：

- Docker 一键部署：见 [README 4.3](../../README.md#43-docker-一键部署推荐)；
- 本机交互式 Pi：见 [Pi 使用指南](pi-usage.md)；
- 工作流、状态与置信度分流：见 [工作流架构](../architecture/workflow.md)。

本页只列服务器 CLI、队列、日志和结果查看，避免与 README 重复。

配置分层（profile / `.env` / CLI / `data/assist`）、优先级和初始/更新方式见 [README 4.5](../../README.md#45-配置分层初始配置与更新)。profile 改后需重建镜像并新开 Pi；`.env` 改后需重建/重启容器；build-install 的 `profile.build.*` 不会自动生效。

## 准备

```sh
gh auth status
export DEEPSEEK_API_KEY='...'        # 或其他 provider 的 key
# fde-manifests/ 必须在项目根目录
cp config/openfde-ai-server.example.json config/openfde-ai-server.json
```

`config/openfde-ai-server.json` 的关键项：

| 字段 | 说明 |
| --- | --- |
| `profile` | 使用的 profile |
| `scan.sync_page_size` / `max_issues_per_run` | 扫描分页与每轮 issue 上限 |
| `scan.max_workers_per_run` | 每轮并发 worker 数 |
| `worker.execute` | `true` 启动 Pi 分析；`false` 只发现/入队 |
| `worker.timeout_seconds` / `retry_limit` | 单 issue 超时与重试 |
| `worker.max_atomic_steps_per_issue` | 单 issue 每轮最多推进的原子步数 |
| `worker.stream_logs` | 是否写 `data/logs/` |

## 队列与扫描

```sh
# 状态
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json status

# 扫描并入队（worker.execute=false 时只入队）
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json scan

# 扫描并执行本轮 worker
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json scan --execute

# 直接分析 / 单步 worker / 重新入队
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json analyze --issue <编号>
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json worker --issue <编号>
python3 automation/openfde_ai_server.py --workspace "$PWD" \
  --config config/openfde-ai-server.json requeue --issue <编号>
```

`scan` 会连续推进同一 issue 的原子步骤，直到终态或达到 `max_atomic_steps_per_issue`。`awaiting_direction`/`awaiting_verification` 是等待态：需要人工回复，Docker 部署由 `poller` 负责轮询，本机可运行 `deploy/reply-poll.sh`。

## 日志

```sh
find data/logs -type f -print
tail -f data/logs/reply-poll.log
```

## 查看结果

每个 issue 的工件在 `.fde-ai/issues/<编号>/`；格式见 [Issue 工件目录](../architecture/artifact-layout.md)。

- 修复补丁：`patch/0001-<名称>.patch`；
- 调试插桩补丁（选择 E 时）：`patch/debug-0001-<名称>.patch` + `patch/debug.json`；
- 评论草稿与发布记录：`comment/`；
- 构建：默认关闭（`build.enabled=false`），启用后由授权助手在受控构建树内临时应用补丁并回滚。

## systemd

宿主机定时运行 `scan` 的安装与运维见 [服务器部署与运维](server-deployment.md)。

## 发布与边界

- `publication.interaction_comments=pr_only`：修复交付/验证征询与 `analysis-options` 等明确类型可按策略发布；
- PR 只创建、不合入；issue 关闭始终人工；
- 无人值守遇到需人工选择的节点会停在 `awaiting_direction`/`awaiting_verification`，不会自行猜修复路线；
- 不修改只读源码树；补丁、PR 与结论均标注 `not_run`/未验证。
