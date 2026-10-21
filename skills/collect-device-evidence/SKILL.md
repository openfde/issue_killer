---
name: collect-device-evidence
description: 当测试人员发现现象、需要在提 issue 前交互式采集设备证据（bugreport、截屏、可选录屏）时使用。
---

# 采集设备证据（交互式）

调用方只需一句话现象；设备与时间可省略。默认只读（唯一例外：确认门中列出的日志开关 `setprop`）。**采集前必须确认**；对话保持简短，完成后在对话中输出完整 issue 草稿供复制。

1. **选择方式（未明确时只给这一小段，等回复）**
   ```text
   采集方式：
   A. 最小集：bugreport + 截图（默认；录屏按需）
   B. 不采集，只生成 issue 草稿
   C. 先现场复现，复现完成后再采集
   D. 事后证据：已有 bugreport，不连设备
   回复 A/B/C/D；A/C 请给设备（IP/序列号）。
   ```
   - 调用方已给设备并说“开始采集/复现完成” → 视为 A 且已确认，直接执行，不再问菜单；
   - 已说“不采集” → B；已说“已有 bugreport/不在现场” → D；已说“先复现” → C。
2. **设备确认与日志开关（A/C）**
   - 设备未给：`adb devices`；恰好 1 台直接用；多台必须问清，**不得自动挑选**；一台都没有且给了 IP 时 `adb connect <IP>:5555`。
   - 设备确认后读取日志开关：`adb -s <序列号> shell getprop log.tag`；若值不是 `V`/`VERBOSE`，在确认门中列入 `setprop log.tag V`。
   - 未确认时只回一行：`设备：<序列号>；日志开关：log.tag=<当前值>（非 V 将 setprop log.tag V）；采集：setprop log.tag V（如需）+ bugreport + 截图；现在开始？（现场复现请回复“复现完成”）`。
   - 未确认前只允许 `adb devices` 和 `getprop log.tag` 枚举；**不得执行 `setprop` 或任何采集命令**。
   - 调用方已给设备并说“开始采集/复现完成” → 视为已确认（含日志开关 `setprop log.tag V`），直接执行。
3. **日志开关预检（A/C，抓日志前）**
   - 若 `getprop log.tag` 已是 `V`/`VERBOSE`，跳过。
   - 否则执行 `adb -s <序列号> shell setprop log.tag V`，再 `getprop log.tag` 复核；仍不是 V 时停止并报告（可改用相关 TAG：`getprop log.tag.<TAG>`、`setprop log.tag.<TAG> V`，如 `DocumentsUI`、`ActivityTaskManager`、`WindowManager`；不要设置无关属性）。
   - `setprop` 失败时停止报告，不得声称已设置。
   - 在 `summary.md` 记录原值/新值；这是本流程唯一允许的写操作。
4. **采集（A/C；除日志开关外只读；全部带 `-s` 或确保仅一台在线）**
   - `adb -s <序列号> bugreport <输出目录>`
   - `adb -s <序列号> exec-out screencap -p > <输出目录>/screen.png`
   - 录屏默认不做；调用方明确要求，或现象为闪烁/动画/卡顿时才可选 `screenrecord` + `adb pull`。
   - 仅当现象明确属于某子系统时追加单条额外项（蓝牙 HCI snoop、显示/音频/网络 dumpsys 头部、tombstone 摘要）；不要扩成套件。
   - 设备不在线时 `adb connect <IP>:5555`。
5. **B：不采集**：只生成 issue 草稿，标注“未采集证据”；不走设备确认/采集。
6. **D：事后证据**：不连接设备、不执行任何设备命令；只校验并打包已有 bugreport；发生时间只写范围（未知写“待补充”）；超 24MB 生成时间窗摘录包。
7. **打包与草稿**
   - 产物写 `data/intake/<日期>-<slug>/`；`summary.md` 含现象、设备、时间（可范围/模糊）、日志开关原值/新值、每项用途与 SHA-256；zip ≤24MB；超限生成时间窗摘录包并说明。
   - 生成 `issue-draft.md`：标题 `<现象摘要>（<build 版本号>）`——版本号只取 bugreport 文件名中的版本段（如 `CP2A.260605.016`）或 `getprop ro.build.display.id`；**不得用 `Android 17` 等 OS 版本代替**；无法取得时写“版本待补充”并询问调用方；正文含现象、时间线、环境、复现步骤（推测，未确认）、预期/实际、附件清单（只列文件名与用途，**不写 SHA-256**）、下次偶现采集建议、AI 取证声明；不写内网地址。
8. **输出（必须包含 issue 草稿全文）**
   ```text
   完成：<zip 路径>（<大小>）
   文件：bugreport.zip、screen.png
   日志开关：log.tag=<原值> → V
   ---- issue-draft.md ----
   <在此输出 issue-draft.md 全文，供直接复制>
   ---- end ----
   提交：新建 issue，粘贴上述正文，拖入 zip 与截图。
   取回：宿主机路径 ~/fde-ai-assistant/data/intake/<slug>
   scp：scp -r <宿主机用户>@<宿主机IP>:~/fde-ai-assistant/data/intake/<slug> <本机目录>
   ```
   - **不要只给草稿路径**；草稿全文必须出现在对话里。
   - 不输出哈希表、命令清单、长解释或其他内容。
   - 宿主/VM 直接运行时，路径改为对应工作区的 `data/intake/<slug>`；没有 bind mount 时可用 `docker cp openfde-ai:/workspace/data/intake/<slug> .` 作为兜底。

边界：除确认门中列出的日志开关 `setprop log.tag...`（及必要的 per-tag `setprop log.tag.<TAG>`）外，全程只读（bugreport/screencap/screenrecord/白名单 pull）；禁止 root、禁止 `logcat -c`、禁止安装/卸载/其他改设置；不得自动挑选设备；不得在 `.fde-ai/runs/` 创建产物；不代提 issue、不发布任何内容。
