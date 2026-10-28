# OpenFDE Issue AI Assistant

面向 OpenFDE 的 issue 分析与修复工作流助手：从 GitHub 读取 issue、评论与附件，基于 `fde-manifests` 和只读源码树做源码级因果分析，按修复置信度分流——高置信直接产出修复 PR，中低置信先产出“原因链 + 修复选项”的 issue 回复，必要时提供复现方案或调试插桩 PR。

##### 全流程以“未验证建议”为边界：不修改只读源码树、不自动合入 PR、不关闭 issue；所有补丁、PR 与结论均标注 `not_run` / 未验证，由开发人员审阅与验证。

## 快速开始

**交互式（推荐，本机/已有源码树）**

```sh
git clone git@src.ift.run:ai-apps/fde-ai-assistant.git
cd fde-ai-assistant
# 准备 fde-manifests/ 与 fde-sources/（见第 3 节）
gh auth login -h github.com
export DEEPSEEK_API_KEY='...'
# 其他模型：export PI_PROVIDER=... PI_MODEL=... 及对应 *_API_KEY
pi
```

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 <编号>
```

**Docker 一键（Linux + Docker Compose，不需要 AOSP 构建）**

```sh
export GH_TOKEN='...'
export DEEPSEEK_API_KEY='...'        # 默认 deepseek/deepseek-flash
./deploy/docker/up.sh                # 自动生成 .env；首次同步源码模块
docker exec -it openfde-ai bash      # 进入容器后运行 pi
```

完整安装（含 Docker/Compose 安装、镜像加速、验证、停止与排障）见 [4.3 Docker 一键部署](#43-docker-一键部署推荐)。

## 目录

- [1. 能力与边界](#1-能力与边界)
- [2. 工作流一览](#2-工作流一览)
- [3. 从代码获取](#3-从代码获取)
- [4. 安装与凭据](#4-安装与凭据)
  - [4.5 配置分层：初始配置与更新](#45-配置分层初始配置与更新)
- [5. 使用配置](#5-使用配置)
- [6. 各环节任务命令](#6-各环节任务命令)
- [7. 执行过程](#7-执行过程)
- [8. 目录结构](#8-目录结构)
- [9. 常见问题](#9-常见问题)
- [10. 文档索引](#10-文档索引)

## 1. 能力与边界

**做什么**

- 拉取 issue、评论与附件元数据，按证据条件提取日志/文本证据；
- 按三层归属定位组件（组件映射知识 → 本地源码树信号 → manifest 结构）；
- 在只读 `fde-sources/` 中追溯源码，输出可审计的原因链、修复选项与验证判据；
- 修复置信度 ≥70 时生成未验证补丁与 GitHub PR（只创建、不合入）；
- 置信度不足时生成 `analysis-options` issue 回复（原因链 + 修复选项 + 复现方案/调试 PR/深入分析选项）；
- 轮询 issue 回复，按开发选择继续修复、展开复现方案、创建调试插桩 PR 或重新分析。

**不做什么**

- 不修改 `fde-sources/` 只读树；不在设备上执行写操作（root、清日志、改设置、输入注入）；
- 不自动合入/关闭 PR，不关闭 issue；
- 不把补丁、PR 或 AI 分析声称为“已验证”；
- 不在 issue、JSON、日志或代码中写入任何凭据；
- 构建+安装由 profile `build.enabled`/`build.install` 控制；Docker 推荐使用 `deploy/docker/build-install.sh`（支持 PR/无 PR），详见 [构建与安装助手](docs/guides/build-install.md)。

## 2. 工作流一览

```
flowchart TD
    L0[采集设备证据 / 已有 bugreport<br/>issue 草稿] --> A[fetch issue]
    A --> B[证据提取]
    B --> C[组件归属 + 只读源码]
    C --> D[源码因果分析 + 校验]
    D --> E[propose-fix + fix_confidence]
    E -->|>= 70| F[补丁 → PR（人工确认）]
    E -->|50–69| G[analysis-options 草案<br/>原因链 + A/B/C + D/E/F]
    E -->|< 50| H[深度分析（最多 2 轮）]
    H --> G
    G --> GP[会话展示草案<br/>A/B/C=修复路线；P=发布；Q=暂停]
    GP -->|A/B/C| F
    GP -->|P + 用户批准| PUB[发布 analysis-options]
    GP -->|D| K[复现与验证方案（人工批准）]
    GP -->|E| L[调试插桩 PR（人工选择）]
    GP -->|F| H
    PUB --> J[awaiting_direction]
    K --> J
    L --> J
    J -->|开发回复 A/B/C| F
    F --> FC[交付评论草稿<br/>manual / approval]
    FC -->|build.install=true| BI{构建+安装 A/B/C}
    FC -->|build.install=false| I[awaiting_verification]
    BI -->|A 最新 PR| BLD[build-install --issue n]
    BI -->|B 自定义| BLD2[指定模块/PR/分支]
    BI -->|C 跳过| I
    BLD --> INST[安装到 FDE + 启动]
    BLD2 --> INST
    INST --> I
    I -->|验证通过| M[confirmed_fixed → archived]
    I -->|仍有问题 + 新日志| A
```

验证助手尚未实现；`I` 的验证由人工完成。`M` 只归档，PR 合并和 issue 关闭仍由人工操作；产品配置类修复还应完成 `systemimage` + PR 构建或 A/B 验证。

**置信度分流**

| `fix_confidence` | 处理 |
| --- | --- |
| ≥ 70 | 修复助手：补丁 → PR（人工确认）→ 交付评论草稿（manual/approval）→ 构建+安装 A/B/C → `awaiting_verification` |
| 50–69 | 分析助手：生成 `analysis-options` 草案（原因链 + A/B/C + D/E/F），会话展示；A/B/C=修复路线，P=发布（approval）→ `awaiting_direction` |
| < 50 | 分析助手深度分析（最多 2 轮）；仍不足则发调查选项 → `awaiting_direction` |

`fix_confidence = min(根因置信度, 修复置信度)`，记录在 `solution/solution.json`；分层锚点见 [Pi 使用指南](docs/guides/pi-usage.md#置信度分流分析助手--修复助手)。

## 3. 从代码获取

### 3.1 助手仓库

```sh
git clone git@src.ift.run:ai-apps/fde-ai-assistant.git
cd fde-ai-assistant
```

主仓库只包含工作流代码、skills、profile、部署脚本与测试；以下目录通过 `.gitignore` 排除，需要单独准备：

```text
fde-manifests/   # Android repo 清单（必需）
fde-sources/     # 只读源码树（必需）
fde-build/       # 可写构建树（仅构建通道需要）
data/            # 运行数据、知识库、日志（自动生成）
.fde-ai/         # issue 工件（自动生成）
```

### 3.2 清单：fde-manifests

```sh
git clone https://src.ift.run/openfde17/fde-manifests fde-manifests
```

确认 `fde-manifests/default.xml` 与 `fde-manifests/openfde.xml` 存在。工作流按 include、`remove-project`、`project` 的声明顺序解析，不以仓库名猜归属。

### 3.3 源码：fde-sources（只读）

`sources.mode=local_tree`，工作流只读取 `fde-sources/` 中每个项目的 `.git` 提交与文件，**不克隆、不拉取**。任选一种方式准备：

```sh
# 方式 A：用 Android repo 工具同步（按实际 manifest 分支）
mkdir -p fde-sources && cd fde-sources
repo init -u https://src.ift.run/openfde17/fde-manifests -b fde_17
repo sync -c -j8
cd ..
```

```text
# 方式 B：复制已准备好的只读源码树（离线/内网镜像）
把与 manifest revision 一致的树放到项目根目录的 fde-sources/
要求：每个项目保留自己的 .git；提交与 fde-manifests 中的 revision 对应
```

源码树必须保持只读。工作流会在 `analysis/sources.json` 记录每个组件的精确 commit 与哈希。

Docker 一键部署时无需手工准备：首次启动的 `sources-sync` 默认按 `github-sources.tsv` 同步 GitHub 镜像（48 个仓库，分支 `fde_17`），并按 `FDE_SOURCE_MODULES`（默认 `art build device external frameworks hardware openfde-sdk packages prebuilts system`）过滤模块；已有仓库会被复用。若内部 GitLab 可达，可设 `FDE_SYNC_MODE=repo` 改用 `repo init/sync`。

### 3.4 构建树：fde-build（可选）

仅当需要受控构建（`build.enabled=true`）时准备，通常是 `fde-sources` 的可写副本或挂载视图；构建树必须干净，且 HEAD 与补丁的 base commit 一致。构建助手会临时应用补丁、构建、记录产物并在退出前回滚补丁。

## 4. 安装与凭据

> 使用 Docker：按 **4.2 → 4.3**；本机交互式分析：按 **4.2 → 4.4**。两者都需要 4.2 的 GitHub token 与模型凭据。

### 4.1 运行方式

| 方式 | 适用场景 | 安装 |
| --- | --- | --- |
| Docker（推荐） | Linux 服务器、长期运行、scanner + poller | [4.3](#43-docker-一键部署推荐) |
| 本机交互式 | 已有源码树、临时分析/开发、VM | [4.4](#44-本机交互式安装可选) |

### 4.2 凭据与模型

**环境变量**

```sh
export GH_TOKEN='<GitHub token>'                 # 无人值守/容器必需；交互式也可用 gh auth login
export DEEPSEEK_API_KEY='<DeepSeek token>'        # 默认模型；其他模型见下
export PI_PROVIDER='deepseek'
export PI_MODEL='deepseek-flash'
export PI_ENABLED_MODELS='deepseek/deepseek-flash'  # 只允许 flash，避免误用 pro
# export PI_BASE_URL='https://...'                # OpenAI 兼容网关
# export OPENAI_API_KEY='...'                     # 按 PI_PROVIDER 选择
# export ANTHROPIC_API_KEY='...'
# export GEMINI_API_KEY='...'                     # 或 GOOGLE_API_KEY
export PI_CODING_AGENT_DIR="$HOME/pi-agent"
export PI_TELEMETRY=0
```

建议写入 `~/.bashrc`，**不要**写入仓库、profile、日志或 issue 工件。

> Docker 部署可把变量写入 `.env`，见 [4.3](#43-docker-一键部署推荐)；容器内使用 `/tmp/pi-agent`，无需设置 `PI_CODING_AGENT_DIR`。

**GitHub Token**

工作流用 `gh` 读取 issue/评论/附件、发布评论、创建 PR；`create-fix-pull-request` 还会通过 `gh auth setup-git` 用同一个 token 推送 `ai/` 分支。**Docker 容器不共享宿主机的 `gh` 登录态，必须显式提供 `GH_TOKEN`。**

**创建（二选一）**

- **经典 PAT**：<https://github.com/settings/tokens> → Generate new token (classic)
  - 勾选 `repo`（读写仓库/issue/PR；仅公开仓库可用 `public_repo`）
  - 勾选 `read:org`（读取组织信息；避免 `gh auth status` 的 `read:org` 告警）
  - 若组织启用 SAML SSO：在该 token 页面点 `Configure SSO` → 授权 `openfde`
- **Fine-grained PAT**：<https://github.com/settings/personal-access-tokens/new>
  - Resource owner：`openfde`（或你的账号）
  - Repository access：`openfde/openfde` + 需要分析的源码仓库（建议 All repositories）
  - Repository permissions：Issues `Read and write`、Contents `Read and write`、Pull requests `Read and write`、Metadata `Read`（必选）
  - Organization permissions（可选）：Members `Read`（减少 `read:org` 告警）

**配置**

宿主机交互式：`export GH_TOKEN='ghp_...'`（或 `gh auth login`）。Docker：在 `up.sh` 前 export 或写入 `.env`，见 [4.3](#43-docker-一键部署推荐)。

**验证**

```sh
gh auth status
```

Docker 内的验证命令见 [4.3](#43-docker-一键部署推荐)。token 只放环境变量或 `.env`，不要提交到仓库；建议专用账号/最小权限并定期轮换。

### 4.3 Docker 一键部署（推荐）

适用于 Linux 服务器；**不需要 AOSP 构建工具链**。已在 Ubuntu 20.04 + Docker 26.1.3 + Compose v2.27.1 实测：安装 → 配置 → 首次同步 48 个源码仓库 → 启动 scanner/poller → 容器内 Pi 验证。

#### 1) 安装 Docker 与 Compose v2

优先使用 Docker 官方脚本：

```sh
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
newgrp docker
docker --version && docker compose version
```

如果 `download.docker.com` 被网络阻断（本机实测），改用 Ubuntu 源：

```sh
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
newgrp docker
docker --version && docker compose version
```

其他发行版安装 Docker Engine + Compose v2 插件即可，最终确认 `docker compose version` 可用。

#### 2) Docker Hub 被阻断时配置镜像加速

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

镜像源由第三方提供，仅在 Docker Hub 不可达时使用；能直连时不要配置。

#### 3) 获取代码

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

#### 4) 配置凭据

按 [4.2](#42-凭据与模型) 创建 `GH_TOKEN`；模型默认 `deepseek/deepseek-flash`，其他模型见 [4.2](#42-凭据与模型)。Docker 容器不共享宿主 `gh` 登录态：

```sh
export GH_TOKEN='...'
export DEEPSEEK_API_KEY='...'
# 其他模型：export PI_PROVIDER=... PI_MODEL=... <PROVIDER>_API_KEY=...
```

`up.sh` 会自动生成 `.env`；已 export 的变量优先，也可以编辑 `.env`。构建/安装主机、`FDE_BUILD_*`、`FDE_INSTALL_*`、SSH key 也在这里配置；四层配置、初始配置和后续更新见 [4.5](#45-配置分层初始配置与更新)。

#### 5) 一键启动

```sh
./deploy/docker/up.sh
```

脚本会：自动生成 `.env` → 检查凭据 → 生成 `config/openfde-ai-server.json` → 缺失时克隆 `fde-manifests` → 构建镜像 → 启动 `sources-sync`、`scanner`、`poller`。

首次 `sources-sync` 默认按 `deploy/docker/github-sources.tsv` 同步 GitHub 镜像（48 个仓库，分支 `fde_17`），并按 `FDE_SOURCE_MODULES`（默认 `art build device external frameworks hardware openfde-sdk packages prebuilts system`）过滤；已有仓库复用。内部 GitLab 可达时可 `FDE_SYNC_MODE=repo`；已有完整源码树可 `FDE_SYNC_MODE=none`。

```sh
docker logs -f openfde-ai-sources     # 首次同步；完成后退出码 0
docker compose ps -a
docker logs -f openfde-ai            # scanner
docker logs -f openfde-ai-poller     # 回复轮询
```

国内网络可在 `.env` 设置 `NPM_REGISTRY=https://registry.npmmirror.com` 与 `REPO_URL` 覆盖镜像构建源。

#### 6) 验证安装

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

#### 7) scanner 工作模式

`config/openfde-ai-server.json` 的 `worker.execute`：

- `true`：扫描并自动分析 issue（会产生模型调用，暂未调试）；
- `false`：只发现/入队，不自动分析（验证安装时建议）。

修改后执行：

```sh
docker restart openfde-ai
```

#### 8) 停止与清理

```sh
cd ~/fde-ai-assistant
docker compose down          # 停止并删除容器；保留命名卷
docker compose down -v       # 同时删除容器内 .fde-ai/data 卷（不动 fde-sources/fde-manifests）
docker image prune -f        # 清理构建产生的 <none> 悬空镜像
docker rmi openfde-ai-assistant:pi   # 可选：删除镜像，下次 up 重新构建
```

`docker compose down` 必须在 `compose.yaml` 所在目录执行；在 `~` 下会报 `no configuration file provided`。

#### 9) 常见问题

- **Docker Hub i/o timeout**：配置第 2 步的 `registry-mirrors` 并重启 Docker；
- **`download.docker.com` 连接重置**：改用第 1 步的 `docker.io` + `docker-compose-v2`；
- **`docker compose` 不存在**：安装 Compose v2 插件（`docker-compose-v2` 或 Docker 官方 repo）；
- **`.bashrc` 里 source 不生效**：Ubuntu `.bashrc` 对非交互 shell 会提前 `return`；直接 `export` 或写入 `.env`；
- **`docker compose down` 报找不到配置**：先 `cd ~/fde-ai-assistant`；
- **`sources-sync` 失败**：`docker logs openfde-ai-sources`；检查 GitHub 网络/模块列表；必要时 `FDE_SYNC_MODE=none` 使用已有源码；
- **模型不可用**：`pi auth check --provider <p> --model <m>`，检查对应 API key / `PI_BASE_URL`；
- **token 更新不生效**：容器环境变量在创建时固定；重新运行 `./deploy/docker/up.sh`（或 `docker compose up -d --force-recreate`）；
- **权限**：`sudo usermod -aG docker "$USER"` 后重新登录或 `newgrp docker`；源码同步以 root 写入并 `chmod -R a+rX`，运行服务以镜像内 `agent`（非 root）只读访问源码；`data/intake` 为 0777 宿主目录，采集包可直接 scp；
- **退出不要用 `Ctrl+C` 停服务**：`Ctrl+C` 通常只中断当前操作；停服务用 `docker compose down`。

### 4.4 本机交互式安装（可选）

> 需要先完成 4.2 的凭据配置。使用 Docker 时不需要本节。

#### 系统依赖

推荐 Linux（Ubuntu 20.04+，或同等的 WSL2/虚拟机）：

| 依赖 | 用途 |
| --- | --- |
| Python 3.8+ | 编排器、测试（仅标准库，无额外 pip 依赖） |
| Git | 仓库与源码树 |
| Node.js 24 | 运行 Pi |
| [Pi](https://www.npmjs.com/package/@earendil-works/pi-coding-agent) | 交互式分析与 skill 执行 |
| [GitHub CLI `gh`](https://cli.github.com/) | 读取 issue、下载附件、发布评论、创建 PR |
| `ripgrep`（`rg`） | 源码检索（工作流强制使用） |
| `adb`（可选） | 取证采集（只读） |

```sh
sudo apt update
sudo apt install -y git python3 ripgrep adb
# Node 24（按官方源安装）
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g @earendil-works/pi-coding-agent@0.84.2
```

`gh` 请按官方文档安装；安装后执行：

```sh
gh auth login -h github.com
gh auth status
```

#### 模型配置

默认使用 DeepSeek（`deepseek/deepseek-flash`，支持图片输入，用于截图证据）。Pi 的运行目录建议固定到用户目录：

```sh
export PI_CODING_AGENT_DIR="$HOME/pi-agent"
mkdir -p "$PI_CODING_AGENT_DIR"
cp deploy/server/pi-agent-template/settings.json "$PI_CODING_AGENT_DIR/" 2>/dev/null || true
```

如需刷新模型目录：

```sh
pi update --models
```

Node 24 + Pi 0.84.2 已验证；其他版本请先运行 `pi --version` 与一次最小对话自检。

> Docker 用户不执行本节；容器会根据 `PI_PROVIDER`/`PI_MODEL` 生成 settings，见 [4.3](#43-docker-一键部署推荐)。

#### 验证

```sh
cd fde-ai-assistant
chmod +x deploy/*.sh deploy/server/*.sh deploy/docker/*.sh
python3 -m unittest discover -s tests -p "test_*.py"   # 当前应为 87 个测试全部通过
pi --version
gh auth status
ls .pi/skills | head                                # 34 个 skill 符号链接
```

Docker 安装验证见 [4.3](#43-docker-一键部署推荐)。

### 4.5 配置分层：初始配置与更新

没有单一“总配置文件”。参数分成四层，先看清位置再改，避免改了 profile 却以为 build-install 会使用它。

| 层 | 位置 | 管什么 | 生效方式 |
| --- | --- | --- | --- |
| 1. 工作流策略 | `profiles/openfde/profile.json` | triage 阈值、深度分析轮数、回复轮询、publication 策略、`build.enabled`/`build.install`、模块列表等 | 改后 `./deploy/docker/up.sh`（重建镜像/重启服务）；已运行 issue 不会自动变更，新 issue 或新 revision 才使用新策略 |
| 2. 模型/令牌/构建/安装环境 | `.env`（或已 export 的环境变量） | `PI_*`、`DEEPSEEK_API_KEY`/`OPENAI_API_KEY` 等、`GH_TOKEN`、`FDE_BUILD_*`、`FDE_INSTALL_*`、`FDE_SSH_KEY` 等 | `up.sh` 读取 `.env` 并导出；scanner/poller/shell 的 `env_file` 也会注入；重建容器后生效 |
| 3. 一次性 CLI | `deploy/docker/build-install.sh` 参数 | 单次构建的模块、PR/分支、jobs、target、product、等待时间、是否安装/启动 | 只影响本次命令，不需要重建镜像 |
| 4. 模块映射/安装脚本 | `data/assist/`（持久卷） | 自定义 `module-map.json`、`fde-install.sh` | 运行时用 `FDE_MODULE_MAP`/`FDE_INSTALL_SCRIPT` 指向文件；不重建镜像 |

**优先级**：构建 CLI > 容器环境变量（`.env`/`env_file`）> `build-install.sh` 脚本默认值。`profile.json` 只控制 issue 工作流策略，**不是 build-install 的参数来源**。

#### 初始配置

1. 首次运行 `./deploy/docker/up.sh` 会从 `deploy/server/env.example` 生成 `.env`，并检查 `GH_TOKEN` 和模型 key；`up.sh` 会读取 `.env`，已 export 的同名变量优先。
2. 编辑 `.env`，至少配置：

```sh
GH_TOKEN=...
PI_PROVIDER=deepseek
PI_MODEL=deepseek-flash
PI_ENABLED_MODELS=deepseek/deepseek-flash
DEEPSEEK_API_KEY=...

FDE_BUILD_HOST=10.31.62.29
FDE_BUILD_TREE=/aosp4/hy_fde17
FDE_BUILD_TARGET=fde_arm64-cp2a-user
FDE_BUILD_PRODUCT=fde_arm64
FDE_BUILD_JOBS=auto
FDE_BUILD_WAIT_SECONDS=3600
FDE_BUILD_POLL_SECONDS=5

FDE_INSTALL_HOST=10.31.62.247
FDE_INSTALL_USER=huyang
FDE_INSTALLER=/usr/local/sbin/fde-install-module
FDE_SSH_KEY=/workspace/data/ssh/id_ed25519
FDE_KNOWN_HOSTS=/workspace/data/ssh/known_hosts
```

3. 工作流默认值已在 `profiles/openfde/profile.json`；需要调整阈值/发布策略时再改，改后重新运行 `up.sh`。
4. 构建机的 SSH key、247 的 sudo 安装器、adb 按 [构建与安装助手](docs/guides/build-install.md) 的“环境准备”配置；它们不使用 `.env` 里的私钥内容。
5. 自定义模块映射/安装脚本放到 `data/assist/`，运行时指定 `FDE_MODULE_MAP`/`FDE_INSTALL_SCRIPT`；不要改只读的 `/workspace/deploy`。

#### 更新配置

| 要改什么 | 怎么做 | 需要重建/重启 | 注意 |
| --- | --- | --- | --- |
| 模型、token、构建/安装主机 | 编辑 `.env`，再运行 `./deploy/docker/up.sh`（或 `docker compose up -d --force-recreate`） | 重建/重启容器 | 容器环境变量在创建时固定；改完不要只 `docker restart` |
| 单次构建参数 | 直接给 `build-install.sh --module/--pr/--branch/--jobs/--target/--product/--wait-seconds` | 不需要 | CLI 覆盖 `.env` 和默认值 |
| 工作流策略 | 编辑 `profiles/openfde/profile.json`，运行 `./deploy/docker/up.sh` | 重建镜像，新开 Pi | 已运行 issue 的 `profile_sha256` 是旧的；用新 issue 或新 revision 验证新策略 |
| 模块映射/安装脚本 | 编辑 `data/assist/module-map.json` 或 `data/assist/fde-install.sh` | 不需要 | 运行时设置 `FDE_MODULE_MAP`/`FDE_INSTALL_SCRIPT` |
| SSH/sudo/adb | 更新 `~/.ssh/authorized_keys`、sudoers 或设备连接 | 不需要 | build-install 走 SSH；adb 只用于采集/验证 |

绕过 `up.sh` 直接使用 `docker compose` 时，`env_file` 仍会把 `.env` 注入 scanner/poller/shell；如果要在当前 shell 里先做替换或检查，可执行 `set -a; . ./.env; set +a`。`.env` 不要提交，token 只放环境变量并定期轮换。

**重要限制**：`profile.build.target/host/tree` 目前不会自动传给 `build-install.sh`。如果你改了 profile 里的这些字段但没有改 `.env` 或 CLI，构建仍使用脚本默认值。当前请优先改 `.env` 或命令行；要做“单一配置源”，需要后续给 `build-install.sh` 增加读取 `data/assist/build.env` 或 profile 的逻辑。

完整构建参数、超时/续跑和安装细节见 [构建与安装助手](docs/guides/build-install.md)。

## 5. 使用配置

### 5.1 Profile：`profiles/openfde/profile.json`

Profile 只控制工作流策略，不是构建/安装的总配置。完整分层、初始配置和更新方式见 [4.5](#45-配置分层初始配置与更新)；`profile.build.*` 目前不会自动传给 `build-install.sh`，构建/安装主机和参数请改 `.env` 或 CLI。修改 profile 后需重新运行 `./deploy/docker/up.sh` 并新开 Pi；已运行 issue 保留旧 `profile_sha256`。

| 字段 | 当前值 | 说明 |
| --- | --- | --- |
| `github.repository` | `openfde/openfde` | issue 仓库 |
| `sources.mode` / `path` | `local_tree` / `fde-sources` | 只读源码树 |
| `build.enabled` | `true` | 启用构建+安装通道 |
| `build.install` | `true` | 构建后安装并启动 FDE |
| `intake.size_budget_mb` | `24` | 附件预算（GitHub 25MB 限制） |
| `publication.interaction_comments` | `pr_only` | 过程评论仅限 PR / 分析选项等明确类型 |
| `publication.analysis_options_comment` | `auto` | 原因链+修复选项回复 |
| `publication.reproduction_plan_comment` | `auto` | D 选项展开回复 |
| `publication.debug_pr_comment` | `auto` | E 选项调试 PR 评论 |
| `publication.dry_run` | `true` | 发布前仍需会话内人工确认 |
| `triage.analysis_reply_min_confidence` | `50` | 低于 50 先深度分析 |
| `triage.auto_pr_min_confidence` | `70` | ≥70 才允许直接出修复 PR |
| `triage.max_deep_analysis_rounds` | `2` | 深度分析轮次上限 |
| `replies.poll_seconds` | `300` | 回复轮询间隔（5 分钟） |
| `pull_request.base_branch` | `fde_17` | 修复 PR 目标分支（只创建、不合入） |
| `debug_pull_request.branch_prefix` | `ai-debug/` | 调试插桩 PR 分支前缀 |

### 5.2 项目上下文：`AGENTS.md`

`AGENTS.md` 是 Pi 每次会话加载的项目规则（受管理区域），包含源码检索纪律、工件边界、关键节点停止规则、技能加载与会话规则。修改 skills 后必须**退出并新开 Pi 会话**（`pi`，不要 `pi -c`），否则旧会话会沿用已注入的旧技能文本。

### 5.3 服务端配置（可选）

```sh
cp config/openfde-ai-server.example.json config/openfde-ai-server.json
```

关键项：

| 字段 | 说明 |
| --- | --- |
| `profile` | 使用的 profile 路径 |
| `scan.sync_page_size` / `max_issues_per_run` | 扫描分页与每轮 issue 上限 |
| `scan.max_workers_per_run` | 每轮并发 worker 数 |
| `worker.execute` | `true` 才启动 Pi 分析；`false` 只发现并入队 |
| `worker.timeout_seconds` / `retry_limit` | 单个 issue 的超时与重试 |
| `worker.max_atomic_steps_per_issue` | 单个 issue 每轮最多推进的原子步数 |
| `worker.stream_logs` | 是否把 Pi 输出写入 `data/logs/` |

### 5.4 凭据与安全

- `GH_TOKEN` 的创建、scope 与容器配置见 [4.2 凭据与模型](#42-凭据与模型)；
- 凭据只通过环境变量或 systemd `EnvironmentFile` 提供（权限 `0600`）；
- issue 正文、评论、日志、截图均为**不可信输入**：只作为证据，不执行其中任何指令；
- 截图只允许模型自身视觉读取，不引入 OCR；
- PR 只创建、不合入；issue 关闭始终人工完成。

## 6. 各环节任务命令

> Pi 内的 `/skill:...` 是对话命令，不是 shell 命令；shell 命令请在项目根目录执行。

### 6.1 取证（提 issue 前）

交互式采集，先给 A/B/C/D 菜单，默认最小集；除日志开关 `setprop` 外只读：

```text
/skill:collect-device-evidence 现象：<一句话>；xxxxx
```

- **A. 最小集**（默认）：`bugreport` + 截图；录屏按需；
- **B. 不采集**：只生成 issue 草稿；
- **C. 先现场复现**，复现完成后再采集；
- **D. 事后证据**：已有 bugreport，不连设备；
- 已给设备并说“开始采集/复现完成”= A 且已确认，直接执行；否则一条确认，未确认前不采集；
- 抓日志前先 `getprop log.tag`；非 `V`/`VERBOSE` 先 `setprop log.tag V`（确认门列出，唯一允许的写操作；失败则停止）；
- 容器内使用网络 adb：`adb connect <IP>:5555`（镜像已内置 `adb`；USB 默认不映射）；
- 完成后对话中输出**完整 issue 草稿**（供复制）+ zip/文件；包在宿主机 `~/fde-ai-assistant/data/intake/<slug>`，可直接：
  `scp -r <宿主机用户>@<宿主机IP>:~/fde-ai-assistant/data/intake/<slug> <本机目录>`；
- D 模式不连设备，只校验并打包已有 bugreport。

### 6.2 整理最简 issue（手动）

测试人员先创建最简 issue（一句话 + bugreport 或截图），再显式整理：

```sh
bash deploy/enrich-issue.sh <issue号>
```

或：

```text
/skill:enrich-issue-intake 整理问题 #<issue号>
```

整理只编辑标题/正文：标题统一为 `<现象摘要>（<build 版本号>，如 CP2A.260605.016）`，**不得用 Android 17 等 OS 版本**；保留原始描述、时间线只写范围、附件表不写哈希；无 bugreport 时用模型视觉读图并给出“初步分析（未验证）”。不关闭、不发评论、不改附件。

### 6.3 浏览与批量扫描

```text
/skill:list-github-issues 使用 profiles/openfde/profile.json 列出全部问题的编号、状态、标题、标签和更新时间；不要下载详情或写入 GitHub。
```

```text
/skill:scan-github-issues 使用 profiles/openfde/profile.json 进行一次受限扫描；遵守队列并发、发布策略、限额和紧急停用开关。
```

### 6.4 分析一个问题（交互式主用法）

先启动**新会话**：

```sh
cd fde-ai-assistant
pi
```

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 <编号或 URL>
```

恢复任意中间状态：

```text
继续 <编号>
继续分析 <编号>；选 A（生成 PR）
继续分析 <编号>；选 D（先给复现与验证方案）
```

- `继续 <编号>` 默认只读状态；只有 `继续分析 <编号>` 或显式 `/skill:run-issue-workflow` 才推进到**下一个关键节点**并停下；
- 关键节点默认在终端内给 A/B/C，不刷 issue 评论；
- 分析选项、复现方案、调试 PR 评论默认 `manual`，必须有人工 `approval.json`；修复交付评论先生成草稿。

### 6.5 分流与回复选项

分析校验后自动计算 `fix_confidence`：

- **≥70**：展示修复方案与 A/B/C（生成 PR / 只留补丁 / 暂停）；
- **50–69**：生成分析回复草案（原因链 + 修复选项 A/B/C + D/E/F），会话展示；P/明确确认并写入 approval 后发布到 issue；
- **<50**：先深度分析（最多 2 轮），仍不足则发调查选项。

`analysis-options` 回复中的 D/E/F：

| 选项 | 行为 |
| --- | --- |
| D. 复现与验证方案 | 生成稳定复现脚本、观测点、修复后判据与根因确认实验，**追加一条 issue 回复** |
| E. 调试 PR（插桩） | 创建 `ai-debug/` 分支 PR：只加日志/埋点、不改行为、不合入，由开发构建刷机 |
| F. 深入分析 | 分析助手继续排查（<50 或按需） |

### 6.6 修复 PR（≥70，人工确认后）

- 补丁：`patch/0001-<名称>.patch` + `patch.json` + `validation.json`；
- `create-fix-pull-request` 在独立工作区应用补丁，推送 `ai/issue-<编号>-<slug>` 分支并创建 PR；
- base 分支 `fde_17`，**只创建、不合入**；多项目修复按项目分别创建 PR；
- PR 创建/更新后**立即**发布交付/验证征询评论，然后停在 `awaiting_verification`；
- 交付评论使用丰富模板，必须包含：问题范围、证据与定位、根因、**完整统一 diff**、影响与风险、验证步骤、`not_run`、PR 链接与验证征询；不得只发交付摘要或省略 diff。

### 6.7 调试 PR（选择 E 后）

- 补丁：`patch/debug-0001-<名称>.patch`，只加日志/埋点，不改控制流；
- 分支 `ai-debug/issue-<编号>-<slug>`，PR 标题 `[debug] issue #N: ...`；
- 评论包含插桩点、TAG、复现与采集命令（`adb logcat -s openfde<编号>`）、回传要求与移除方式；
- 当前构建关闭时由开发自行构建/刷机；回传日志按新证据进入新 revision。

### 6.8 回复轮询与验证闭环（可选）

启动轮询（每 5 分钟；无新评论不启动模型）：

```sh
source ~/.bashrc
nohup bash deploy/reply-poll.sh >>/dev/null 2>&1 &
```

```sh
tail -f data/logs/reply-poll.log
pkill -f reply-poll.sh      # 停止
REPLY_POLL_SECONDS=600 nohup bash deploy/reply-poll.sh >>/dev/null 2>&1 &   # 临时改间隔
```

手动同步一次回复：

```text
/skill:sync-github-replies 同步问题 #<编号> 的新回复（当前状态 <state>），按技能规则处理。
```

- 开发选择 A/B/C → 按路线继续修复；
- 选择 D → 展开复现方案并追加回复；选择 E → 调试 PR；选择 F → 深度分析；
- 回传调试日志/复现结果 → 新 revision 重新分析；
- 回复“验证通过” → `confirmed_fixed` → `archived`（issue 关闭仍人工）；
- `awaiting_direction` 超过 30 分钟仅写日志/下次会话提示，不自动深挖。

### 6.9 Docker 日常命令（可选）

安装、配置、首次启动、验证与清理见 [4.3 Docker 一键部署](#43-docker-一键部署推荐)；容器运维速查见 [Docker 容器运维](docs/guides/docker-deployment.md)。

```sh
docker exec -it openfde-ai bash   # 进入后运行 pi
docker exec -it openfde-ai pi
./deploy/docker/pi.sh
docker logs -f openfde-ai
docker logs -f openfde-ai-poller
```

退出：`pi` 内 `/quit` 或 `/exit`（`Ctrl+D`）；容器 shell 内 `exit`（`Ctrl+D`）。退出 `exec` 不会停止服务；停止/清理见 4.3。

### 6.10 无人值守 / 服务端（可选）

服务器 CLI、队列、日志与 systemd 的完整命令见 [服务器 CLI 使用指南](docs/guides/usage.md) 与 [服务器部署](docs/guides/server-deployment.md)。Docker 用户直接使用 4.3 的 `scanner`/`poller`，不需要本节。

### 6.11 构建+安装（Docker 单命令）

Docker 用户可直接构建并安装到 FDE。issue 模式默认读取最新 PR 并自动匹配模块。构建/安装参数属于 [4.5 配置分层](#45-配置分层初始配置与更新) 的第 2/3 层：`.env` 的 `FDE_*` 或本次 CLI；profile 的 `build.*` 不会自动传入。

```sh
cd ~/fde-ai-assistant

# issue 最新 PR + 自动模块
./deploy/docker/build-install.sh --issue 496

# 多模块（逐个构建/安装，最后只启动一次 FDE）
./deploy/docker/build-install.sh --issue 496 --module DocumentsUI --module libinput --no-pr

# 指定分支（不应用 PR，构建后恢复原分支）
./deploy/docker/build-install.sh --module DocumentsUI --no-pr --branch <branch>

# 显式 PR
./deploy/docker/build-install.sh --issue 496 --module DocumentsUI --pr 3

# 已有产物只安装，不重新构建/不重新应用 PR
./deploy/docker/build-install.sh --issue 499 --module SystemUI \
  --install-only --artifact /workspace/data/artifacts/499/SystemUI.apk

# 覆盖远端构建等待（默认 3600 秒）
./deploy/docker/build-install.sh --issue 499 --wait-seconds 5400
```

- `--jobs auto`（默认）按模块映射的 `jobs` 选线程，`--jobs N` 强制覆盖
- `--no-pr` / `--branch`：不应用 PR；`--branch` 构建后恢复原分支
- `--no-install`：只构建并取回产物；`--no-start`：安装但不启动 FDE
- `--install-only --artifact <path>`：已有产物只安装，用于构建晚到/超时后接回安装
- `--wait-seconds` / `--poll-seconds`：远端构建等待与轮询；默认 3600/5 秒
- 构建/安装结果写入 `build/build-result.json` / `install/install-result.json`
- 多模块逐个构建/安装，最后只启动一次 FDE
- 当前 shell 未激活 docker 组时使用 `sg docker -c '...'`

完整参数、模块映射、超时/续跑和配置更新见 [构建与安装助手](docs/guides/build-install.md)。

Pi 内：

```text
/skill:build-install --issue 496
/skill:build-install --issue 496 --module DocumentsUI --module libinput --no-pr
/skill:build-install 编译安装BoringdroidSystemUI
```

`BoringdroidSystemUI` 是 `FdeSystemUI` 的别名；自然语言会映射到对应模块和参数。

工作流：`build.install=true` 时在交付评论后停【构建+安装】，A=最新 PR/默认模块，B=已有产物只安装（`--install-only`）或自定义模块/PR/分支，C=跳过。构建超时先查 `build/build-result.json` 和远端日志/exit；远端已成功就用 install-only 接回安装，仍在运行则记录 `build_running`，不要 sleep/tail 本地日志死循环或重复起构建。

### 6.11.1 旧手工构建（build.install=false，兼容）

仅当 profile `build.enabled=true` 时进入构建通道：

1. 工作流 `request-build` 写 `build/build-request.json` 并停在 `build_requested`；
2. 人工运行授权助手：

```sh
deploy/server/fde-ai-build.sh --issue <编号>
```

3. 助手加锁（`data/build.lock` / `.siso_lock`）、临时应用补丁、增量构建、记录产物哈希、回滚补丁；锁被占用时退出 75，稍后重试；
4. 继续工作流，`collect-build-artifacts` 校验产物并进入评论流程。

构建结果只是构建证据，不等同于用户验证；构建树不得残留补丁。

### 6.12 测试（未确认）

```sh
python3 -m unittest discover -s tests -p "test_*.py"
```

当前基线以 VM 上全量测试输出为准；Windows 本机受 `.pi/skills` junction 与 `fcntl` 限制，部分测试不适用。

### 6.13 知识沉淀

`archive-case` 归档时会自动生成一个 **draft case**（不自动进 Wiki）：

```sh
python3 automation/capture_knowledge_case.py --workspace . --issue <编号>
```

产物：`data/knowledge/cases/<编号>/case.json`、`case.md`、`data/knowledge/index.json`。

`retrieve-knowledge` 会先按组件/包名/log tag 检索 case 和 Wiki；`draft` 只作线索，已确认 case 才能作为知识引用。人工审核后：

```text
/skill:propose-knowledge ...
/skill:promote-knowledge ...
/skill:validate-knowledge ...
```

完整规则见 [知识沉淀与组件导引](docs/guides/knowledge-base.md)。

组件归属确认使用：

```text
/skill:confirm-component-mapping 该问题属于 <项目名或路径>；依据：<一句话>
```

### 6.14 异常恢复（未确认）

用于监督流程执行和环境保持

1.bot方案

2.自动重入

3.状态维护

### 6.15 并发执行（未确认）

各个助手都可以并行处理多个任务

## 7. 执行过程

### 7.1 状态与阶段

| 阶段 | 状态 |
| --- | --- |
| 初始化 | `initialized` → `profile_loaded` → `context_built` |
| 拉取与证据 | `issue_fetched` → `evidence_extracted` |
| 归属与源码 | `manifest_resolved` → `sources_fetched` → `knowledge_retrieved` |
| 分析与校验 | `root_cause_traced` → `analysis_verified` |
| 方案与分流 | `solution_proposed` → `analysis_options_drafted` / `patch_proposed` |
| 修复交付 | `patch_validated` → `pull_request_created` → `comment_drafted` → `awaiting_verification` |
| 收敛 | `confirmed_fixed` → `archived` |
| 等待人工 | `awaiting_direction` / `direction_received`、`component_review_requested`、`build_requested` / `build_running` / `build_failed` |
| 调试插桩 | `debug_patch_proposed` → `debug_pull_request_created` |
| 构建 | `build_requested` → `build_running` → `build_done` → `artifacts_collected` |
| 终止/阻塞 | `archived`、`needs_information`、`blocked` |

`state.json` 使用唯一状态字段 `state`，并记录 `revision`、`phase`（analysis/fix）、`fix_confidence`、`deep_analysis_rounds`、`direction_wait_since` 等。

### 7.2 关键节点（交互会话）

1. **定位结论**：问题落在哪个组件的哪个功能；
2. **根因重点解析与置信度分流**：完整原因链 + `fix_confidence` + 交付物选项；
3. **修复方案**（≥70）：A/B/C；
4. **分析回复草案**（50–69）：发布 / 修改 / 暂停；
5. **复现与验证方案**（D）/ **调试 PR**（E）；
6. **求助**（受阻）；
7. **代码修改**（diff 展示）/ **校验结果** / **评论与验证征询**。

硬性规则：`继续 <编号>` 默认只读；明确“继续分析/推进”或显式 `/skill:run-issue-workflow` 才推进到下一个关键节点；`analysis_verified` 后同一轮完成 `propose-fix` 与分流；`<70` 不得自行选择修复路线或生成补丁/PR；深度分析最多 2 轮。

### 7.3 评论类型

| 类型 | marker | 发布策略 |
| --- | --- | --- |
| 分析选项征询 | `openfde-ai:analysis-options` | `analysis_options_comment=manual`；必须有人工 `publication/approval.json` |
| 复现与验证方案 | `openfde-ai:reproduction-plan` | 选择 D 后生成草稿；必须有人工批准 |
| 调试 PR | `openfde-ai:debug-pr` | 选择 E 后生成草稿；必须有人工批准 |
| 求助 | `openfde-ai:escalation` | `manual` 默认；`auto` 时仍需会话确认 |
| 修复交付/验证征询 | 含 PR 链接与 issue/revision/正文哈希 | 先生成草稿；`manual` 默认，批准后发布 |

### 7.4 产物目录

```text
.fde-ai/issues/<issue号>/
├── state.json
├── input/      # issue、评论、附件（含截图）
├── evidence/   # 日志摘录与 evidence.json
├── analysis/   # 组件、来源、知识、原因链与校验
├── solution/   # 修复建议与 fix_confidence
├── patch/      # 0001-*.patch、debug-0001-*.patch、元数据与校验
├── build/      # 构建请求、结果与产物登记
├── comment/    # 评论草稿与发布记录
└── archive/    # 历史 revision
```

## 8. 目录结构

```text
.
├── AGENTS.md                     # Pi 项目上下文与硬规则
├── automation/openfde_ai_server.py
├── compose.yaml / Dockerfile
├── config/openfde-ai-server.example.json
├── deploy/
│   ├── enrich-issue.sh           # 手动整理 issue
│   ├── reply-poll.sh             # 等待态回复轮询
│   ├── run-scan-loop.sh          # 容器扫描循环
│   ├── docker/                   # 一键启动与源码子集同步
│   ├── server/                   # 容器与受控构建助手
│   └── systemd/                  # 宿主机定时器
├── docs/                         # 指南与架构文档
├── profiles/openfde/             # profile 与组件映射种子
├── skills/                       # 原子技能（34 个）
├── tests/                        # unittest
├── .pi/skills/                   # 指向 skills/ 的符号链接
├── fde-manifests/                # 清单（不入库）
├── fde-sources/                  # 只读源码树（不入库）
└── fde-build/                    # 可写构建树（可选，不入库）
```

## 9. 常见问题

**技能更新后行为没变**

退出 Pi 并**新开会话**（`pi`，不要 `pi -c`），再从 `/skill:run-issue-workflow` 开始。旧会话会沿用已注入的旧技能文本。

**`gh` 未认证 / 读不到 issue**

```sh
gh auth status
gh auth login -h github.com
```

无人值守环境使用 `GH_TOKEN`，创建与 scope 见 [4.2 凭据与模型](#42-凭据与模型)。Docker 容器不共享宿主 `gh` 登录态，必须显式传入 `GH_TOKEN`；更换 token 后重新运行 `./deploy/docker/up.sh`。

**`gh auth status` 提示缺少 `read:org`**

issue 读取/列表/评论通常不受影响；补经典 PAT 的 `read:org`（或 fine-grained 的 Organization Members `Read`），重新授权后重建容器。

**组件归属失败或停在 `component_review_requested`**

确认 `fde-sources/` 已准备且每个项目保留 `.git`；按 `analysis/component-review.json` 的候选人工确认：

```text
/skill:confirm-component-mapping 该问题属于 <项目名或路径>；依据：<一句话>
```

**附件超过 24MB**

GitHub 单附件限制 25MB；工作流会生成时间窗摘录包，原始大文件需人工补充到 issue。

**评论没有自动发布**

`publication.dry_run=true` 时发布前必须在会话中确认；`pr_only` 下求助类评论不发布，只停在等待态。

**构建停在 `build_requested`**

构建通道默认关闭；确认 `build.enabled=true` 后人工运行 `deploy/server/fde-ai-build.sh --issue <编号>`。退出 75 表示构建锁被占用，稍后重试。

**轮询没有运行**

```sh
pgrep -af reply-poll.sh
nohup bash deploy/reply-poll.sh >>/dev/null 2>&1 &
tail -f data/logs/reply-poll.log
```

**Docker 首次启动长时间停在 `sources-sync`**

首次需要同步源码模块（默认 GitHub 镜像 48 个仓库），耗时取决于网络与磁盘：

```sh
docker compose logs -f sources-sync
# 调整镜像/分支/模块
FDE_SYNC_MODE=repo FDE_MANIFEST_URL=... FDE_SOURCE_MODULES="..." ./deploy/docker/up.sh
FORCE_SYNC=1 ./deploy/docker/up.sh     # 忽略已有 marker，强制重同步
```

已有源码（每个项目保留 `.git`）会被复用；`FDE_SYNC_MODE=none` 可完全跳过同步。

**Docker 内交互 Pi**

```sh
docker logs -f openfde-ai-sources
docker exec -it openfde-ai bash   # 然后运行 pi
# 或：docker exec -it openfde-ai pi
# 或：./deploy/docker/pi.sh

# 独立 shell（不影响 scanner/poller）：
docker compose --profile tools up -d shell
docker exec -it openfde-ai-shell pi
```

技能更新后必须退出容器内 Pi 并重新进入（新进程），不要依赖旧会话。退出方式：`pi` 内 `/quit` 或 `/exit`（`Ctrl+D`）；容器 shell 内 `exit`（`Ctrl+D`）；`docker exec -it openfde-ai pi` 退出 Pi 即回到宿主机。

**Docker 源码/清单权限**

`sources-sync` 以 root 写入并执行 `chmod -R a+rX`；`scanner`/`poller`/`shell` 以镜像内 `agent`（非 root）只读访问源码。`data/intake` 额外挂载到宿主机 `~/fde-ai-assistant/data/intake`（权限 0777）并直接用于 scp 取回。若宿主目录由其他属主创建且不可读，请调整目录权限后重新 `up.sh`。

**退出PI后怎么继续与原issue交互**

```
继续 496
```

**模型/图片能力异常**

```sh
pi update --models
pi --version
```

确认默认模型为支持图片输入的 `deepseek/deepseek-flash`。

## 10. 文档索引

### 安装使用
- [Pi 使用指南](docs/guides/pi-usage.md)：交互命令、分流、回复闭环；
- [Docker 容器运维](docs/guides/docker-deployment.md)：日常命令、服务与卷、停止清理（完整安装见 4.3）；
- [构建与安装助手](docs/guides/build-install.md)：issue 最新 PR、多模块、分支、自动线程、FDE 启动；

### 工作流详解
- [服务器 CLI 使用指南](docs/guides/usage.md)：队列、扫描、日志与 patch；
- [工作流架构](docs/architecture/workflow.md)：状态机、置信度分流、安全边界；
- [取证采集](docs/architecture/intake.md)：A/B/C/D 采集模式与体积约束；
- [组件归属](docs/architecture/component-attribution.md)：三层归属与人工回退；
- [组件分流指南](profiles/openfde/component-map/GUIDE.md)：信号字典、组件目录、决策树、负向信号与案例索引；
- [知识沉淀与组件导引](docs/guides/knowledge-base.md)：case 自动采集、Wiki 晋升与检索规则；
- [Issue 工件目录](docs/architecture/artifact-layout.md)：产物格式与 patch 入口；
- [服务器部署](docs/guides/server-deployment.md)：systemd 服务账户与定时器；
- [aosp17-ai 容器部署](deploy/server/README.md)：容器与受控构建助手；
- [服务器工作进程](docs/architecture/server-worker.md)：队列、并发与 Pi 进程语义。
- [496 端到端 Demo](docs/demos/issue-496-walkthrough.md)：从取证到修复 PR 与验证的完整对话示例；
- [498 端到端 Demo](docs/demos/issue-498-walkthrough.md)：从取证到修复 PR 到自动编译安装、人工验证的完整对话示例；



