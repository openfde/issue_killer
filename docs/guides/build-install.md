# 构建与安装助手

用于在 Docker AI 容器内完成一次「构建模块 -> 取回产物 -> 安装到 FDE -> 启动 OpenFDE」。支持 issue 最新 PR、显式 PR、当前分支或指定分支，支持多个模块。

## 前置

- `openfde-ai` 容器运行中
- 29 构建树可 SSH：`/aosp4/hy_fde17`
- 247 已安装 `/usr/local/sbin/fde-install-module`，并有 sudoers NOPASSWD
- 容器 key：`/workspace/data/ssh/id_ed25519`（29 和 247 已授权）
- 模块登记在 [`deploy/assist/modules.json`](../../deploy/assist/modules.json)

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

## 工作流

profile `build.install=true` 时，`run-issue-workflow` 在交付评论后停【构建+安装】节点：

- A：`--issue <编号>`，默认最新 PR + 自动模块
- B：自定义模块/PR/分支
- C：跳过

代理不自动合并 PR、不关闭 issue；构建/安装结果是验证证据，不等同于验证通过。
