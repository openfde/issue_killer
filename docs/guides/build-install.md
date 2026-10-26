# 构建与安装助手

用于在 Docker AI 容器内完成一次「构建模块 -> 取回产物 -> 安装到 FDE -> 启动 OpenFDE」。支持 issue 最新 PR、显式 PR、当前分支或指定分支，支持多个模块。

## 环境准备

### 1. 角色与访问

| 角色 | 地址/路径 | 用户 | 需要 |
| --- | --- | --- | --- |
| AI 容器 | `openfde-ai` | `agent` | `ssh`/`scp`、`/workspace/data/ssh` |
| 构建机 | `10.31.62.29` | `huyang` | SSH key、`/aosp4/hy_fde17`、`build/envsetup.sh` |
| 安装机 | `10.31.62.247` | `huyang` | SSH key、`waydroid`、sudo 安装器 |
| FDE/设备 | `10.31.62.247:5555`（或 `:25555`） | — | adb 授权；用于采集/验证，不是 build-install 必需 |

build-install 的安装路径是：AI 容器 SSH 到 247，执行固定的 root 安装器；它**不依赖 adb**。adb 用于 L0 取证和后续人工验证。

### 2. 在 AI 容器生成 SSH key

```sh
docker exec -it -u agent openfde-ai bash
mkdir -p /workspace/data/ssh
chmod 700 /workspace/data/ssh
ssh-keygen -t ed25519 -N '' -f /workspace/data/ssh/id_ed25519
cat /workspace/data/ssh/id_ed25519.pub
```

`/workspace/data` 是持久卷，容器重建不会丢 key。私钥不要提交仓库、不要发到 issue。

### 3. 把公钥加入 29 和 247

在**能登录对应机器**的终端执行（每个用户一次）：

```sh
# 在 10.31.62.29 上以 huyang 登录
install -d -m 700 ~/.ssh
cat >> ~/.ssh/authorized_keys    # 粘贴上一步的 pubkey
chmod 600 ~/.ssh/authorized_keys

# 在 10.31.62.247 上以 huyang 登录
install -d -m 700 ~/.ssh
cat >> ~/.ssh/authorized_keys    # 同一把 pubkey
chmod 600 ~/.ssh/authorized_keys
```

如果使用非默认端口或用户名，在 `~/.ssh/config` 或 `FDE_SSH_KEY`/`FDE_INSTALL_USER` 中覆盖，不要写死到脚本。

### 4. 写入 known_hosts 并验证

在 AI 容器执行：

```sh
ssh-keyscan -H 10.31.62.29 10.31.62.247 >> /workspace/data/ssh/known_hosts

ssh -i /workspace/data/ssh/id_ed25519 \
  -o BatchMode=yes \
  -o UserKnownHostsFile=/workspace/data/ssh/known_hosts \
  huyang@10.31.62.29 'whoami; hostname'

ssh -i /workspace/data/ssh/id_ed25519 \
  -o BatchMode=yes \
  -o UserKnownHostsFile=/workspace/data/ssh/known_hosts \
  huyang@10.31.62.247 'whoami; hostname'
```

### 5. 247 安装 sudo 和固定安装器

`fde-install-module` 必须是 **root 所有、固定内容**的脚本；不要给 `NOPASSWD: ALL`。

```sh
# 在 10.31.62.247 上
sudo install -o root -g root -m 755 \
  /home/huyang/fde-install-module.sh /usr/local/sbin/fde-install-module

echo 'huyang ALL=(root) NOPASSWD: /usr/local/sbin/fde-install-module' \
  | sudo tee /etc/sudoers.d/fde-ai-install
sudo chmod 440 /etc/sudoers.d/fde-ai-install

# 从 AI 容器验证：--help 返回 usage 即说明免密规则生效
ssh -i /workspace/data/ssh/id_ed25519 \
  -o BatchMode=yes \
  -o UserKnownHostsFile=/workspace/data/ssh/known_hosts \
  huyang@10.31.62.247 \
  'sudo -n /usr/local/sbin/fde-install-module --help 2>&1 || true'
```

安装器只接受 manifest 中的 artifact/image/dest，并在内部停 waydroid、mount image、替换文件、umount、`waydroid init -f`。

### 6. adb（L0/验证，不是 build-install 必需）

AI 容器或本机连接 FDE：

```sh
adb connect 10.31.62.247:5555
# 如果 FDE 实际监听 25555：
adb connect 10.31.62.247:25555

adb devices
adb -s 10.31.62.247:5555 shell getprop ro.build.display.id
adb -s 10.31.62.247:5555 logcat -b crash -d
```

- 设备显示 `offline` 时，先确认 adb 授权/端口，再 `adb kill-server && adb connect ...`。
- 现场采集前按 intake 流程检查 `log.tag`；`setprop log.tag V` 是唯一允许的设备写操作。
- 498 当时 adb 25555 曾离线；现场采集失败时用 D 模式（已有 bugreport）不阻塞分析。
- 安装后的 FDE 启动由 `fde-start.sh` 通过 SSH 完成，不走 adb。

### 7. 构建机与安装机自检

```sh
# 29 构建树
ssh -i /workspace/data/ssh/id_ed25519 \
  -o BatchMode=yes \
  -o UserKnownHostsFile=/workspace/data/ssh/known_hosts \
  huyang@10.31.62.29 \
  'cd /aosp4/hy_fde17 && test -f build/envsetup.sh && echo tree_ok; nproc; df -h .; git -C packages/apps/DocumentsUI status --short'

# 247 waydroid / sudo / adb
ssh -i /workspace/data/ssh/id_ed25519 \
  -o BatchMode=yes \
  -o UserKnownHostsFile=/workspace/data/ssh/known_hosts \
  huyang@10.31.62.247 \
  'systemctl is-active waydroid-container.service; waydroid status; adb devices; sudo -n /usr/local/sbin/fde-install-module --help 2>&1 || true'
```

FDE 启动环境默认是 Kylin/UKUI X11：

```text
XDG_SESSION_TYPE=x11
DISPLAY=:0
XAUTHORITY=/home/huyang/.Xauthority
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
XDG_RUNTIME_DIR=/run/user/1000
```

`fde-start.sh` 按 `fde_ctrl` → `waydroid session start` → `fde_shortcut` 顺序启动；Wayland 会话需要相应调整。

### 8. 配置分层、初始配置与更新

没有单一“总配置文件”。构建/安装相关的参数分四层；总览和更新矩阵见 [README 4.5](../../README.md#45-配置分层初始配置与更新)。

| 层 | 位置 | 管什么 | 生效方式 |
| --- | --- | --- | --- |
| 1. 工作流策略 | `profiles/openfde/profile.json` | 分析阈值、发布策略、`build.enabled`/`build.install`、模块列表 | 改后 `./deploy/docker/up.sh` 重建镜像并新开 Pi；已运行 issue 不会自动变更 |
| 2. 环境变量 | `.env`/已 export 变量 | 模型、token、构建/安装主机、SSH key、等待时间 | `up.sh` 读取 `.env`；scanner/poller/shell 的 `env_file` 注入；容器重建后生效 |
| 3. CLI | `build-install.sh` 参数 | 单次模块、PR/分支、jobs、target/product、wait、安装/启动 | 只影响本次命令 |
| 4. 模块映射/安装脚本 | `data/assist/` 持久卷 | 自定义 `module-map.json`、`fde-install.sh` | 用 `FDE_MODULE_MAP`/`FDE_INSTALL_SCRIPT` 指向；无需重建 |

**优先级**：CLI > `.env`/容器环境变量 > 脚本默认值。`profile.json` 只控制 issue 工作流，**不会自动传给 `build-install.sh`**。

#### 初始配置

1. 首次使用 Docker 时运行 `./deploy/docker/up.sh`：它会从 `deploy/server/env.example` 生成 `.env`，读取后检查 `GH_TOKEN` 和模型 key；已 export 的同名变量优先。
2. 编辑 `.env`（或 export）以下构建/安装参数：

```sh
GH_TOKEN=...
PI_PROVIDER=deepseek
PI_MODEL=deepseek-flash
DEEPSEEK_API_KEY=...

FDE_BUILD_HOST=10.31.62.29
FDE_BUILD_USER=huyang
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

3. 按本文第 2–7 节配置容器 SSH key、29/247 公钥、247 sudo 安装器和 known_hosts；这些不走 `.env` 的私钥内容。
4. `profiles/openfde/profile.json` 使用默认分析/发布/构建策略；需要改阈值、`build.install` 或模块列表时再改，改后运行 `./deploy/docker/up.sh`。`state.json` 的 `profile_sha256` 不会自动更新，建议新 issue 或新 revision 验证新策略。
5. 需要自定义模块映射/安装脚本时，复制到持久卷 `data/assist/`，运行时指定：

```sh
FDE_MODULE_MAP=/workspace/data/assist/module-map.json \
FDE_INSTALL_SCRIPT=/workspace/data/assist/fde-install.sh \
bash deploy/assist/build-install.sh --issue 498 --module CalendarProvider --no-pr
```

镜像内 `/workspace` 是只读的；不要改 `/workspace/deploy/assist/modules.json`，否则重建容器会丢失。498 现场就是用 `data/assist/` 覆盖模块/安装脚本；后续可固化进镜像。

#### 更新配置

| 要改什么 | 操作 | 重建/重启 | 注意 |
| --- | --- | --- | --- |
| 模型、token、构建/安装主机、wait | 编辑 `.env`，运行 `./deploy/docker/up.sh`（或 `docker compose up -d --force-recreate`） | 重建/重启容器 | 容器环境变量创建时固定，`docker restart` 不会重新读取 |
| 单次构建参数 | `--module/--pr/--branch/--jobs/--target/--product/--wait-seconds/--install-only` | 不需要 | CLI 覆盖 `.env` 和默认值 |
| 工作流 profile | 编辑 `profiles/openfde/profile.json`，运行 `./deploy/docker/up.sh` | 重建镜像，新开 Pi | 已运行 issue 的 `profile_sha256` 仍是旧的；新 issue/revision 生效 |
| 模块映射/安装脚本 | 编辑 `data/assist/module-map.json` 或 `data/assist/fde-install.sh` | 不需要 | 运行时设置 `FDE_MODULE_MAP`/`FDE_INSTALL_SCRIPT` |
| SSH/sudo/adb | 更新 authorized_keys、sudoers、设备连接 | 不需要 | build-install 走 SSH；adb 只做采集/验证 |

如果绕过 `up.sh` 直接 `docker compose`，`env_file` 仍会注入 `.env`；需要在当前 shell 做变量替换/检查时执行 `set -a; . ./.env; set +a`。`.env` 不提交，token 定期轮换。

**重要限制**：`profile.build.target/host/tree` 目前不会自动传给 `build-install.sh`。只改 profile、不改 `.env`/CLI 时，构建仍使用脚本默认值。要“单一配置源”，需要后续给 `build-install.sh` 增加读取 `data/assist/build.env` 或 profile 的逻辑；当前优先改 `.env` 或 CLI。

## 单命令

在 VM 上执行：

```sh
cd ~/fde-ai-assistant

# issue 默认使用最新 PR，并自动匹配模块
./deploy/docker/build-install.sh --issue 496

# 显式模块 + 指定 PR
./deploy/docker/build-install.sh --issue 496 --module DocumentsUI --pr 3

# 多个模块（逐个构建/安装，最后只启动一次 FDE）
./deploy/docker/build-install.sh --issue 496 --module DocumentsUI --module libinput --no-pr

# 指定分支（不应用 PR，构建后恢复原分支）
./deploy/docker/build-install.sh --module DocumentsUI --no-pr \
  --branch issue-496-documentsui-documentlaunchmode-intoexisting

# 只构建并取回产物
./deploy/docker/build-install.sh --issue 496 --no-install

# 安装但不启动 FDE
./deploy/docker/build-install.sh --issue 496 --no-start

# 已有产物只安装，不重新构建/不重新应用 PR
./deploy/docker/build-install.sh --issue 499 --module SystemUI \
  --install-only --artifact /workspace/data/artifacts/499/SystemUI.apk

# 覆盖构建等待时间（默认 3600 秒）
./deploy/docker/build-install.sh --issue 499 --wait-seconds 5400
```

如果当前 shell 尚未激活 `docker` 组：

```sh
sg docker -c './deploy/docker/build-install.sh --issue 496'
```

也可以进入容器执行：

```sh
docker exec -u agent openfde-ai bash /workspace/deploy/assist/build-install.sh \
  --issue 496
```

在交互式 Pi 中使用：

```text
/skill:build-install --issue 496
/skill:build-install --issue 496 --module DocumentsUI --module libinput --no-pr
/skill:build-install --module DocumentsUI --no-pr --branch <branch>
```

Pi 也支持自然语言，不需要记参数：

```text
/skill:build-install 编译安装BoringdroidSystemUI
/skill:build-install 编译安装 DocumentsUI 和 BoringdroidSystemUI
/skill:build-install 只编译 BoringdroidSystemUI，不安装
/skill:build-install 按分支 fde_17 编译安装 BoringdroidSystemUI
/skill:build-install 用 issue 496 的最新 PR 编译安装
```

`BoringdroidSystemUI` 是别名，实际构建模块是 `FdeSystemUI`，源码在 `packages/apps/BoringdroidSystemUI`，产物安装到 `/system/system_ext/priv-app/FdeSystemUI/FdeSystemUI.apk`。

## 超时、结果和续跑

默认等待远端构建 `FDE_BUILD_WAIT_SECONDS=3600` 秒（可用 `--wait-seconds` 覆盖），每 `FDE_BUILD_POLL_SECONDS=5` 秒检查一次远端 `.exit`。不要再使用 600 秒级短超时，也不要用 `sleep`/`tail build.log` 轮询本地日志。

构建/安装结果写入 issue 目录：

- `build/build-result.json`：`running`/`success`/`failed`/`timeout`、模块、PR、产物路径和 SHA-256、远端日志、退出码、起止时间。
- `install/install-result.json`：安装状态、A/B 主机、模块、源/远端产物、目标路径和日志。

构建脚本返回 `3`/`timeout` 时：

1. 先读 `build/build-result.json` 和远端 `remote_log`/`.exit`；
2. 远端 `exit 0` → 用 `--install-only --artifact <产物>` 继续安装；
3. 远端仍在运行 → 记录 `build_running`、远端 pid/log，等待或暂停；
4. 不要重复启动构建，也不要把旧 `build.log` 当成当前构建状态。

2026-10-23 的 499 就是反例：SystemUI 实际编译 19:56，但旧脚本固定等待约 12 分钟就返回 timeout；远端构建继续并成功，workflow 却停在旧日志和旧失败结果上。现在超时结果与远端日志分开记录，且可用 install-only 接回安装。

## issue 与 PR

- 只给 `--issue` 时：
  1. 读取 `.fde-ai/issues/<issue>/state.json` 的 `pull_request`；
  2. 没有则用 `gh pr list --search "#<issue>"` 在模块仓库中找最新 PR；
  3. 用 PR 所属仓库自动匹配 `modules.json` 中的模块。
- 找不到 PR 时不会猜测：提示使用 `--pr`、`--no-pr` 或 `--branch`。
- `--pr` 只适用于所有模块属于同一仓库；跨仓库请用 `--latest-pr`、`--no-pr` 或 `--branch`。

## 模块映射

```json
{
  "DocumentsUI": {
    "project": "packages/apps/DocumentsUI",
    "repository": "openfde/packages_apps_documentsui",
    "artifact": "system/priv-app/DocumentsUI/DocumentsUI.apk",
    "image": "system",
    "dest": "/system/priv-app/DocumentsUI/DocumentsUI.apk",
    "kind": "apk",
    "jobs": 4
  }
}
```

`jobs` 可由模块显式指定；缺省时按 `kind` 估算（apk=4、jar/native=8、image=12），并用构建机 `nproc` 封顶。`--jobs N` 强制覆盖所有模块。

## 流程

1. 解析 issue/模块/PR/分支。
2. 指定分支时检查工作区干净并切换；构建结束恢复原分支（`--keep-branch` 可保留）。
3. `--pr`/最新 PR：通过 `gh pr diff` 获取 diff；在 29 上临时应用，构建后回滚。若当前分支已包含该 PR，`git apply --reverse --check` 识别为已应用，不重复打补丁。
4. `lunch fde_arm64-cp2a-user`，`make <module> -j<auto>`。
5. 产物：29 -> 容器 `/workspace/data/artifacts/<issue>/` -> 247；SHA-256 校验。
6. 每个模块生成 manifest，调用 247 通用安装器：停 waydroid、mount image、替换产物、umount、`waydroid init -f`。
7. 所有模块安装完后调用 `fde-start.sh` 一次：`fde_ctrl` -> `waydroid session start` -> `fde_shortcut`。

构建日志和临时文件在 `/workspace/data/assist/work/<issue>-<时间>/`；29 上日志在 `/aosp4/hy_fde17/out/assist-build-*.log`。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| `Permission denied (publickey)` | 公钥未加入目标机 `authorized_keys`；检查 `~/.ssh` 700、`authorized_keys` 600、home 权限 |
| `Host key verification failed` | 重新 `ssh-keyscan -H <host> >> /workspace/data/ssh/known_hosts` |
| `sudo: a password is required` | 247 的 sudoers 规则未生效；重新安装 `/etc/sudoers.d/fde-ai-install` |
| adb `offline` | `adb kill-server; adb connect ...`；确认端口/授权；build-install 本身不依赖 adb |
| `module not found` | 模块不在 `modules.json`；补映射或用 `FDE_MODULE_MAP` 覆盖 |
| `fde-install.sh: Permission denied` | 使用 `FDE_INSTALL_SCRIPT` 指向可执行包装，或 `bash fde-install.sh` |
| `artifact missing` | 检查模块产物路径；`--no-pr` 与 PR 构建的产物可能不同 |
| PR patch 不适用 | 检查分支/base；用 `--branch` 或 `--no-pr` 重试 |
| `system.img` 接近上限 | 498 已达到 2668994560/2668996864 量级；新增包需关注空间 |

## 工作流

profile `build.install=true` 时，`run-issue-workflow` 在交付评论后停【构建+安装】节点：

- A：`--issue <编号>`，默认最新 PR + 自动模块
- B：自定义模块/PR/分支
- C：跳过

代理不自动合并 PR、不关闭 issue；构建/安装结果是验证证据，不等同于验证通过。
