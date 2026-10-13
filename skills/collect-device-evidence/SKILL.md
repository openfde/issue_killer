---
name: collect-device-evidence
description: 当测试人员发现现象、需要在提 issue 前交互式采集设备证据（bugreport、截屏、可选录屏）时使用。
---

# 采集设备证据（交互式）

调用方只需一句话现象；设备与复现时间都可省略。默认只读、最小集，不做长篇规划。

1. **简短评估**：
   - 设备：未提供时先看 `adb devices`——恰好 1 台在用就直接用它（把序列号报给调用方）；多台时不得自动挑选，必须问清并由调用方指定；一台都没有时提示 `adb connect <IP>:5555`。
   - 复现时间：可模糊（“刚才”“十分钟前”均可）；调用方准备现场复现时，直接引导“先复现、复现后立即采集”，不必强求时间——bugreport 自带最近日志。
   - 采集集：默认 `bugreport` + 现象截图；录屏问一句要不要（复现/闪烁/动画类建议要）；仅当现象明确属于某子系统时追加单条额外项（蓝牙 HCI snoop、显示/音频/网络 dumpsys 头部、tombstone 摘要）。不要扩成套件。
2. **连接确认**：目标设备不在线时 `adb connect <IP>:5555`；执行命令必须带显式 `-s <序列号>` 或确保仅一台设备在线。
3. **采集（服务器 adb 通道；全部只读命令）**：
   - `adb -s <序列号> bugreport <输出目录>`（主证据）
   - `adb -s <序列号> exec-out screencap -p > <输出目录>/screen.png`
   - 可选录屏：`adb -s <序列号> shell screenrecord --time-limit 180 /sdcard/record.mp4`，提示调用方复现后 `adb pull` 取回；设备不支持时引导用自带录屏。
4. **打包与自检**：产物写入 `data/intake/<日期>-<slug>/`；附简短 `summary.md`（现象、设备、时间可为模糊描述、每项用途与 SHA-256）；打成 zip，总大小 ≤24MB（GitHub 附件上限 25MB），超限时把大文本成员 gzip 后重打包并说明；自检 zip 与截图存在。
5. **生成 issue 草稿（A 方案）**：写 `data/intake/<日期>-<slug>/issue-draft.md`，包含可整段复制的标题与正文——现象、环境（设备/版本/时间）、复现步骤、预期与实际、附件清单与 SHA-256，并注明“由 AI 取证助手辅助生成、未验证”；内网地址等敏感信息不写入草稿。
6. **输出**：在对话中给出 zip/截图路径与 issue 草稿全文，提示人工在 GitHub 新建 issue——粘贴草稿正文、拖入 zip 与截图；不代提 issue、不发布任何内容。

边界：只读（bugreport/screencap/screenrecord/白名单 pull）；禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置。服务器连不上设备时，直接在对话里给出 PC 端命令（`adb bugreport`、`adb exec-out screencap`、`adb pull`）让测试人员自行执行，不生成脚本文件。不得在 `.fde-ai/runs/` 创建新产物。
