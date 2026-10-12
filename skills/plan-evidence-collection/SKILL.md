---
name: plan-evidence-collection
description: 当测试人员发现现象并需要在提交 issue 前生成受限取证采集方案与采集脚本时使用。
---

# 规划取证采集

仅在人工明确给出问题时使用：调用方必须显式提供现象描述（一句话），可选设备型号/版本、设备网络地址、复现时间点；不得自行选择现象或替调用方定性问题。

读取 profile `intake` 配置与 `profiles/openfde/intake-templates/` 模板，匹配最接近的子系统模板（无法匹配时用 `common.md` 并明确标注不确定性），在 `data/intake/<日期>-<slug>/` 生成：

- `collection-plan.json`：现象、子系统、疑似信号、设备信息、时间窗、通道（默认 `server_adb`，降级 `pc`/`on_device`）、只读命令白名单、逐条 evidence item（用途、三种通道的命令变体、预期标记、大小估计、是否必需）、大小预算与 `status: planned`、`allow_root: false`；
- `collect_pc.sh` 与 `collect_on_device.sh`：按模板组装、可直接执行的只读采集脚本（含大小上限与打包步骤）；
- `README.md`：执行说明、预期目录结构、注意事项（不清理日志缓冲，按时间窗与 tag 过滤控制体积）。

命令只允许模板中的只读模式（`logcat -d`、`dumpsys`、`getprop`、`screencap`、白名单路径 `pull`）；禁止 root、禁止清日志缓冲、禁止安装/卸载/改设置。不连接设备、不访问 GitHub、不提出或发布 issue；产物只写 `data/intake/`。不得在 `.fde-ai/runs/` 创建新产物。
