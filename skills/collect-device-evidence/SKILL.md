---
name: collect-device-evidence
description: 当测试人员发现现象、需要在提 issue 前交互式采集设备证据（bugreport、截屏、可选录屏）时使用。
---

# 采集设备证据（交互式）

人工给出现象描述后，用一次简短确认决定采集项，然后引导并执行采集；默认只读、最小集，不做长篇规划。

1. **简短评估**：问清一句话现象、设备型号/版本、复现时刻；随后提出采集集并请调用方确认：
   - 默认必选：`bugreport` + 现象截图；
   - 录屏（可选）：复现过程/闪烁/动画类问题建议加；
   - 额外项：仅当现象明确属于某子系统时追加一条，保持最小——蓝牙加 HCI snoop（开发者选项里已开启时）、显示加 `dumpsys SurfaceFlinger` 头部、音频加 `dumpsys media.audio_flinger` 头部、网络加 `dumpsys connectivity` 头部、崩溃加 `ls /data/tombstones` 与 `dumpsys dropbox` 摘要。不要扩成套件。
2. **设备连接（保持现状）**：`adb connect <IP>:5555` 后列出 `adb devices`，人工确认目标序列号；多设备必须显式 `-s`，不得自动挑选。
3. **采集（服务器 adb 通道；全部只读命令）**：
   - `adb -s <序列号> bugreport <输出目录>`（主证据）
   - `adb -s <序列号> exec-out screencap -p > <输出目录>/screen.png`
   - 可选录屏：`adb -s <序列号> shell screenrecord --time-limit 180 /sdcard/record.mp4`，提示调用方复现后 `adb pull` 取回；设备不支持时引导用自带录屏。
   - 可选子系统项按第 1 步结论执行。
4. **打包与自检**：产物写入 `data/intake/<日期>-<slug>/`；附一份简短 `summary.md`（现象、设备、复现时刻、每项用途与 SHA-256）；打成 zip，总大小 ≤24MB（GitHub 附件上限 25MB），超限时把大文本成员 gzip 后重打包并说明；自检 zip 存在、含 bugreport 文本与截图。
5. **输出**：给出 zip 路径与文件清单，提示人工新建 issue 并附 zip+截图；不代提 issue、不发布任何内容。

边界：只读（bugreport/screencap/screenrecord/白名单 pull）；禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置。服务器连不上设备时，直接在对话里给出 PC 端命令（`adb bugreport`、`adb exec-out screencap`、`adb pull`）让测试人员自行执行，不生成脚本文件。不得在 `.fde-ai/runs/` 创建新产物。
