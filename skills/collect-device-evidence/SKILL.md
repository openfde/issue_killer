---
name: collect-device-evidence
description: 当测试人员发现现象、需要在提 issue 前交互式采集设备证据（bugreport、截屏、可选录屏）时使用。
---

# 采集设备证据（交互式）

调用方只需一句话现象；设备与复现时间都可省略。默认只读、最小集，不做长篇规划。**采集前必须经过确认门。**

1. **简短评估与采集方式选项**：先问清一句话现象、设备型号/版本、复现时刻，并给出采集方式选项（回复 A/B/C）：
   - **A. 按最小集采集（默认）**：`bugreport` + 现象截图；录屏问一句要不要（复现/闪烁/动画类建议要）；仅当现象明确属于某子系统时追加单条额外项（蓝牙 HCI snoop、显示/音频/网络 dumpsys 头部、tombstone 摘要）。不要扩成套件。
   - **B. 不采集**：仅按一句话描述生成 issue 草稿（正文无附件段落，标注“未采集证据”）。
   - **C. 先现场复现**，再决定是否采集。
   - 设备：未提供时先看 `adb devices`——恰好 1 台在用就直接用它（把序列号报给调用方）；多台时不得自动挑选，必须问清并由调用方指定；一台都没有时提示 `adb connect <IP>:5555`。
   - 复现时间：可模糊（“刚才”“十分钟前”均可）；调用方准备现场复现时，引导“先复现、复现完再说”。
2. **确认门（硬性，必须停住等待）**：一次性交给调用方确认——①目标设备序列号 ②将要执行的采集命令清单 ③开始时机：
   - 现场复现：请调用方先复现，收到“复现完成”（或“开始采集”）后才执行；
   - 已经复现过：确认时间点后执行。
   在收到明确确认前，只允许 `adb devices` 之类的枚举检查，**不得执行 bugreport/screencap/screenrecord 等任何采集命令**。
3. **连接确认**：目标设备不在线时 `adb connect <IP>:5555`；执行命令必须带显式 `-s <序列号>` 或确保仅一台设备在线。
4. **采集（服务器 adb 通道；全部只读命令）**：
   - `adb -s <序列号> bugreport <输出目录>`（主证据）
   - `adb -s <序列号> exec-out screencap -p > <输出目录>/screen.png`
   - 可选录屏：`adb -s <序列号> shell screenrecord --time-limit 180 /sdcard/record.mp4`，提示调用方复现后 `adb pull` 取回；设备不支持时引导用自带录屏。
5. **打包与自检**：产物写入 `data/intake/<日期>-<slug>/`；附简短 `summary.md`（现象、设备、时间可为模糊描述、每项用途与 SHA-256）；打成 zip，总大小 ≤24MB（GitHub 附件上限 25MB），超限时把大文本成员 gzip 后重打包并说明；自检 zip 与截图存在。
6. **生成 issue 草稿**：写 `data/intake/<日期>-<slug>/issue-draft.md`，标题固定为 `<现象摘要>（<系统版本号>）`——版本号取 bugreport 文件名中的版本段（如 `CP2A.260605.016`）或 `getprop ro.build.display.id`；正文包含现象、环境（设备/版本/时间）、复现步骤、预期与实际、附件清单（只列文件名与用途，**不写 SHA-256**；哈希保留在本地 `summary.md`；**选择“不采集”时无附件段落并标注“未采集证据”**），并注明“由 AI 取证助手辅助生成、未验证”；内网地址等敏感信息不写入草稿。
7. **输出（标准格式）**：对话中按固定格式给出——① 打包文件路径与大小；② 文件清单（每项用途）；③ issue 草稿全文（标题含系统版本号）；④ 提 issue 提醒（粘贴正文、拖入 zip 与截图）；⑤ 最后附**本机拉取附件的 scp 命令**（服务器绝对路径），便于马上下载后提交 issue：
   `scp huyang@10.31.62.29:/aosp/aosp17-ai/workspace/data/intake/<slug>.zip <本机目录>`
   `scp huyang@10.31.62.29:/aosp/aosp17-ai/workspace/data/intake/<slug>/screen.png <本机目录>`
   不代提 issue、不发布任何内容。

边界：只读（bugreport/screencap/screenrecord/白名单 pull）；禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置。服务器连不上设备时，直接在对话里给出 PC 端命令（`adb bugreport`、`adb exec-out screencap`、`adb pull`）让测试人员自行执行，不生成脚本文件。不得在 `.fde-ai/runs/` 创建新产物。
