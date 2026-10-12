# 服务器部署（aosp17-ai 容器）

本目录提供在服务器（rootless docker）上构建并运行 `aosp17-ai` 容器的脚本。该容器把本仓库与本地 AOSP 源码树、构建输出组合在一起，负责 Issue 分析、受控构建与产物收集。

## 组成

| 文件 | 运行位置 | 作用 |
| --- | --- | --- |
| `Dockerfile.ai` | 服务器 | `FROM aosp17-builder:latest`，叠加 Node、Pi、gh、adb、glslang。 |
| `build-ai-image.sh` | 服务器 | 收集 `gh`/`glslang` 到构建上下文并构建 `aosp17-ai:latest`。 |
| `run-ai-container.sh` | 服务器 | 创建并启动 `aosp17-ai` 容器（挂载工作区、源码树、构建输出）。 |
| `ai-container-setup.sh` | 容器内 | 建立 mesa-tools 软链接并自检 python 模块与工具版本。 |
| `fde-ai-build.sh` | 容器内 | 受控构建助手：加锁、临时应用 patch、构建、记录产物、回滚 patch、推进状态。 |
| `env.example` | 服务器 | 复制为 `/aosp/aosp17-ai/.env` 后填写令牌。 |
| `pi-agent-template/` | 服务器 | `PI_CODING_AGENT_DIR` 持久目录模板。 |

## 顺序

1. 部署工作区到 `/aosp/aosp17-ai/workspace`（见仓库 deploy 说明或服务器 README），并准备 `fde-manifests/`。
2. `cp env.example /aosp/aosp17-ai/.env` 并填写令牌；复制 `pi-agent-template/` 到 `/aosp/aosp17-ai/pi-agent/`。
3. 运行 `build-ai-image.sh` 构建镜像。
4. 运行 `run-ai-container.sh` 启动容器。
5. 容器内执行 `ai-container-setup.sh` 自检。
6. 在容器内启动扫描循环：`deploy/run-scan-loop.sh`（或按需运行 `automation/openfde_ai_server.py`）。

构建默认人工触发：`request-build` 只写 `build/build-request.json` 并停在 `build_requested`；人工在容器内运行
`deploy/server/fde-ai-build.sh --issue <编号>` 完成构建。整体构建运行期间助手会因 `.siso_lock` 被占用而退出 75，稍后重试即可。
