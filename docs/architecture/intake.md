# 取证采集（提 issue 前）

取证助手是提 issue 前的交互式人工辅助：**发现问题和决定提 issue 始终由人完成**，助手把"抓什么、怎么抓"变成几步对话，不做长篇规划。大多数问题只需要 **bugreport + 截屏**。

## 交互流程

1. 人工给出一句话现象；助手先给简短菜单（未明确时）：
   - **A. 最小集**（默认）：`bugreport` + 截图；录屏按需；
   - **B. 不采集**：只生成 issue 草稿；
   - **C. 先现场复现**，复现完成后采集；
   - **D. 事后证据**：已有 bugreport，不连设备；
   已给设备并说“开始采集/复现完成”视为 A 且已确认；
2. 设备确认（A/C）：`adb devices`；唯一设备直接用，多设备必须人工指定（不得自动挑选）；未确认前只能枚举（`adb devices`/`getprop log.tag`），不得执行 `setprop` 或采集命令；
3. 日志开关预检（A/C，抓日志前）：`getprop log.tag`；非 `V`/`VERBOSE` 时执行 `setprop log.tag V` 并复核；失败则停止。设备使用 per-tag 时改用 `getprop log.tag.<TAG>`/`setprop log.tag.<TAG> V`（如 `DocumentsUI`、`ActivityTaskManager`、`WindowManager`）。这是本流程唯一允许的写操作，确认门需列出；
4. 采集（除日志开关外只读）：`adb bugreport`、`adb exec-out screencap`、可选 `screenrecord` + `adb pull`；容器内使用网络 adb `adb connect <IP>:5555`；
5. 打包：`data/intake/<日期>-<slug>/` 内生成 zip（含 `summary.md`：现象、设备、时间、日志开关原值/新值、用途、SHA-256），≤24MB；超限生成时间窗摘录包；
6. 生成 issue 草稿：写 `issue-draft.md`——标题为 `<现象摘要>（<系统版本号>）`，正文含环境/复现/预期与实际/附件清单（**不写 SHA-256**；内网地址不写入）；**在对话中输出草稿全文供复制**；
7. 取回：包在宿主机 `~/fde-ai-assistant/data/intake/<slug>`，可直接 `scp -r <宿主机用户>@<宿主机IP>:~/fde-ai-assistant/data/intake/<slug> <本机目录>`；助手不代提、不发布。

## 降级

连不上设备时，助手直接在对话里给出 PC 端命令（`adb bugreport`、`adb exec-out screencap`、`adb pull`）由测试人员执行，不生成脚本文件。

## 偶现 / 事后取证（D 模式）

调用方选择 D 或说明没有设备/不在现场/已有 bugreport 时：

- 发生时间只给**范围**（未知写“待补充”），另有抓取时间与“是否重启”；
- **不连接设备**、不执行任何设备命令，只校验并打包已有文件；
- bugreport 超 24MB 时生成时间窗摘录包（发生范围 ±30 分钟主日志 + crash buffer + dropbox 摘要）；
- 草稿同样标注“推测复现步骤（未确认）”，并附“下次偶现采集建议”（常驻 logcat、立即截图、不重启设备）。

## 最简 issue + 手动整理命令

测试人员可以只提交一句话（+ bugreport 或截图），**创建时助手不参与**；创建完成后显式执行整理命令：

- pi 会话内：`/skill:enrich-issue-intake 整理问题 #N`
- 或 shell：`bash deploy/enrich-issue.sh N`

整理规则：

1. 只编辑该 issue 的标题与正文（`gh issue edit`），不关闭、不发评论、不改附件；
2. **有 bugreport**：标题整理为 `<现象摘要>（<版本号>）`；正文含 现象 / 时间线（发生时间只写范围）/ 环境 / 复现步骤（推测，未确认）/ 预期与实际 / 附件（不写 SHA-256）/ 下次偶现采集建议，并完整保留原始描述；
3. **没有 bugreport（仅文字 + 截图）**：用模型视觉直接读图（无 OCR），在正文增加 **“初步分析（未验证）”**：现象解读、1~3 个可疑组件/方向（结合 component-map，标注推测）、建议补充的证据（如 bugreport、对应子系统日志）；并标注“**无日志证据**”；
4. marker 防重复整理；不得批量扫描或自动选择新 issue。

## 与 issue 分析衔接

取证包作为 issue 首版证据附件；分析阶段直接读取附件（截图由模型视觉识别）。组件映射与子系统经验沉淀在 `component-map` 知识库中，与取证互不耦合。
