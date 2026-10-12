---
name: run-evidence-collection
description: 当取证采集方案已确认且设备已由人工连通时，通过授权环境执行只读采集并打包证据时使用。
---

# 执行取证采集

仅接收 `status: planned` 的 intake 目录，且必须由人工显式确认目标设备（序列号或 `IP:端口`）。默认 `server_adb` 通道：

- 先 `adb connect <地址>` 再列出 `adb devices` 展示给调用方并等待确认；多设备时必须使用显式 `-s <序列号>`，不得自动挑选设备；
- 严格按 `collection-plan.json` 的只读白名单逐条执行，输出写入 `data/intake/<slug>/capture/`，逐条记录命令、时间、输出大小与 SHA-256；
- 超出大小预算（默认 20MB）时先压缩，仍超则按时间窗/tag/pid 裁剪重抓，并在结果中记录裁剪策略；
- 打包 `evidence-<时间戳>.zip` 与 `package-manifest.json`（文件、大小、SHA-256、用途），写 `collection-result.json`（设备信息、执行时间、命令清单、失败项），`status` 推进到 `collected`。

连接失败或设备不可达时降级：保持 `planned` 不动，提示调用方改用已生成的 `collect_pc.sh` 或 `collect_on_device.sh`（人工执行后再运行 `validate-intake-package`）。

禁止 root、禁止写设备、禁止清日志缓冲、禁止安装/卸载/改设置；不得访问 GitHub 或发布任何内容；不得在 `.fde-ai/runs/` 创建新产物。
