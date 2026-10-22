---
name: build-install
description: 当用户要求在容器内构建模块、使用 issue 最新 PR、指定 PR/分支、安装到 FDE 并启动 OpenFDE 时使用。
---

# 构建并安装模块

解析用户输入，只通过容器内的单命令执行；不要手工 `git apply`、`make`、`mount` 或 `waydroid init`。

```sh
bash /workspace/deploy/assist/build-install.sh [--issue <编号>] [--module <模块> ...] [--pr <PR编号> | --no-pr | --branch <分支>] [--jobs auto|N] [--no-install] [--no-start]
```

## 自然语言

用户不需要记参数；从描述中提取模块、PR/分支和安装意图：

- `编译安装 BoringdroidSystemUI` → `--module BoringdroidSystemUI`（别名解析到实际模块 `FdeSystemUI`）
- `编译安装 DocumentsUI 和 BoringdroidSystemUI` → 两个 `--module`
- `只编译不安装` → `--no-install`
- `用 issue 496 的最新 PR 编译安装` → `--issue 496`
- `按分支 fde_17 编译安装 BoringdroidSystemUI` → `--module BoringdroidSystemUI --no-pr --branch fde_17`
- `线程用 8` → `--jobs 8`；未指定则自动

模块、PR/分支或安装意图不明确时先询问，不要猜。

## 规则

- 模块映射：`deploy/assist/modules.json`。
- 只给 `--issue`：默认取该 issue 最新的 PR，并从 PR 所属仓库自动匹配模块。
- 多个模块：重复 `--module` 或逗号分隔；逐个构建、逐个安装，最后只启动一次 FDE。
- 指定分支：`--no-pr --branch <分支>`；构建后恢复原分支（`--keep-branch` 可保留）。
- PR：`--pr <编号>` 只适用于所有模块同仓库；否则用 `--latest-pr`、`--no-pr` 或 `--branch`。
- 线程：`--jobs auto`（默认）按模块映射的 `jobs`，缺失时按 APK/JAR/native/image 选 4/8/12，并以构建机 `nproc` 封顶；`--jobs N` 强制覆盖。
- 用户未给模块且无法从 issue 推断、或 PR/分支意图不明确时，先询问，不猜。
- 示例：
  - `/skill:build-install --issue 496`
  - `/skill:build-install --issue 496 --module DocumentsUI --module libinput --no-pr`
  - `/skill:build-install --module DocumentsUI --no-pr --branch issue-496-documentsui-documentlaunchmode-intoexisting`
  - `/skill:build-install --issue 496 --module DocumentsUI --pr 3 --jobs 4`
- 执行后报告构建结果、产物路径与 SHA-256、安装结果和 FDE 状态；失败停止，不自动重试。
- 不自动合并 PR、不关闭 issue、不修改源码或补丁文件。
