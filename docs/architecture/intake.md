# 取证采集（提 issue 前）

取证助手是提 issue 前的交互式人工辅助：**发现问题和决定提 issue 始终由人完成**，助手把"抓什么、怎么抓"变成几步对话，不做长篇规划。大多数问题只需要 **bugreport + 截屏**。

## 交互流程

1. 人工给出一句话现象（可选设备型号/版本、复现时刻）；
2. 助手简短评估并给出采集集请确认：默认 `bugreport` + 现象截图；录屏可选（复现/闪烁/动画类建议加）；仅当现象明确属于某子系统时追加单条额外项（蓝牙 HCI snoop、显示/音频/网络 dumpsys 头部、tombstone 摘要）；
3. 设备连接保持现状：服务器 `adb connect <IP>:5555` → 列 `adb devices` → 人工确认序列号（多设备显式 `-s`，不得自动挑选）；
4. 只读采集：`adb bugreport`、`adb exec-out screencap`、可选 `adb shell screenrecord` + `adb pull`；全程禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置；
5. 打包：`data/intake/<日期>-<slug>/` 内生成 zip（含简短 `summary.md`：现象、设备、时间、用途、SHA-256），总大小 ≤24MB（GitHub 附件上限 25MB），超限时把大文本成员 gzip 后重打包并说明；
6. 生成 issue 草稿：写 `issue-draft.md`（可整段复制的标题+正文+哈希，内网地址不写入）；人工在 GitHub 新建 issue——粘贴草稿、拖入 zip+截图；助手不代提、不发布。

## 降级

服务器连不上设备时，助手直接在对话里给出 PC 端命令（`adb bugreport`、`adb exec-out screencap`、`adb pull`）由测试人员执行，不生成脚本文件。

## 与 issue 分析衔接

取证包作为 issue 首版证据附件；分析阶段直接读取附件（截图由模型视觉识别）。组件映射与子系统经验沉淀在 `component-map` 知识库中，与取证互不耦合。
