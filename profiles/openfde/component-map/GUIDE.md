# OpenFDE 模块分流指南

> 用途：把 issue 的现象、日志、包名、窗口和 UI 文案，快速映射到 FDE/AOSP 组件，减少每次从零检索源码。
>
> 状态：**已由开发人员确认（2026-10-28）**。确认的是组件归属，不是问题已修复；设备现象见案例索引备注。
>
> 维护：新增或纠正条目时，同时更新 `entries.md`、本文件的案例索引和 `last_validated`；人工确认的条目使用 `source: human`。

## 0. 30 秒决策

1. 先提取信号：包名/Activity、窗口名、日志 tag、UI 文案、文件路径、构建模块。
2. 有**精确包名/Activity**：直接查本指南“组件目录”和 `entries.md`。
3. 只有**UI 文案**：先看“决策树”，再看 `entries.md` 的 `keyword`。
4. 命中 `high`：直接采用，记录 `matched_by: guide/entries`。
5. 命中 `medium` 或多个候选：列 2 个候选，问开发人员一个最小问题。
6. 无命中或 `low`：停 `component_review_requested`，不要猜。

## 1. 信号字典

| 信号 | 从哪里取 | 例子 | 用途 |
|---|---|---|---|
| `package` | `dumpsys window`、`dumpsys activity`、logcat | `com.android.documentsui` | 最可靠，优先 |
| `activity` | `dumpsys activity activities`、窗口栈 | `com.android.documentsui/.files.FilesActivity` | 定位页面 |
| `window` | `dumpsys window` | `NotificationShade`、`TopBarLayout` | 区分状态栏/通知/桌面 |
| `log-tag` | logcat | `SHADE_EXPAND` | 定位系统 UI 路径 |
| `ui-text` | 截图、UI 树 | “应用列表”“搜索全部应用”“清空” | 只有界面文案时使用 |
| `path` | 源码/产物路径 | `packages/apps/TaskPlugin` | 构建/安装定位 |
| `property-prefix` | `getprop`、配置 | `persist.fde.` | 设备树/产品配置 |
| `module` | `out/target/product/...` | `FdeSystemUI`、`DocumentsUI` | 编译模块 |

## 2. 组件目录

> `project` 使用 `fde-manifests` 里的 **manifest 项目名**；括号内是历史别名。旧种子里的别名会在后续 revision 逐步纠正。

| 组件/职责 | manifest project | 本地路径 | 构建/安装 | 备注 |
|---|---|---|---|---|
| FDE 应用列表/应用抽屉（TaskPlugin 插件窗口） | `taskplugin`（旧：`packages_apps_TaskPlugin`） | `packages/apps/TaskPlugin` | `TaskPlugin` / FDE 模块 | 491 已确认；宿主进程是 `com.android.launcher3` |
| FDE 桌面顶栏/任务栏/窗口装饰 | `systemuiplugin`（旧：`boringdroidsystemui`） | `packages/apps/BoringdroidSystemUI` | `FdeSystemUI` | 只替换状态栏内容，不等于原生 NotificationShade |
| Launcher3 宿主/标准 Launcher 行为 | `packages_apps_launcher3` | `packages/apps/Launcher3` | `Launcher3` | 仅标准 Launcher 行为；FDE 应用列表 UI 在 TaskPlugin |
| 文件管理器/文件选择器 | `packages_apps_documentsui` | `packages/apps/DocumentsUI` | `DocumentsUI` | 492/496 相关；freeform 窗口 |
| 设置 | `packages_apps_Settings` | `packages/apps/Settings` | `Settings` | FDE 定制 |
| 日历应用 | `platform/packages/apps/Calendar` | `packages/apps/Calendar` | `Calendar` | 498 待核实；provider 另算 |
| 日历 Provider | `platform/packages/providers/CalendarProvider` | `packages/providers/CalendarProvider` | `CalendarProvider` | 498 的 authority `com.android.calendar` |
| 原生 NotificationShade/SystemUI | `frameworks_base` | `frameworks/base` | `SystemUI` | 493 原生 shade；与 FDE 顶栏分层 |
| FDE 设备树/产品配置 | `device_fde` | `device/openfde/fde` | `fde_arm64` | 权限、privapp、产品配置 |
| 窗口管理/WMS | `frameworks_base` | `frameworks/base` | `services` | 窗口 bounds/freeform |
| 图形/渲染 | `waydroid_android_external_mesa3d` | `external/mesa` | — | 花屏/GPU |
| 音频 | `external_pulseaudio` | `external/pulseaudio` | — | 声音/录音 |
| 蓝牙 | `packages_modules_Bluetooth` | `packages/modules/Bluetooth` | — | BLE/蓝牙 |

## 3. 决策树

### 3.1 桌面、任务栏、应用列表

```text
现象在桌面/任务栏/窗口装饰
  ├─ 应用列表页、应用抽屉、搜索全部应用、AppOverviewWindow → taskplugin
  ├─ 标准 Launcher 桌面/图标/workspace → packages_apps_launcher3
  ├─ 顶栏、状态栏内容、任务栏、窗口按钮 → systemuiplugin
  └─ 窗口拖动/缩放/bounds/多窗口 → frameworks_base (WMS) + systemuiplugin
```

### 3.2 状态栏、通知、控制中心

```text
状态栏下拉/通知面板/快捷设置
  ├─ 原生 NotificationShade、SHADE_EXPAND、legacy_window_root → frameworks_base (SystemUI)
  ├─ FDE 顶栏内容、TopBarLayout、通知卡片样式 → systemuiplugin
  └─ 通知清空/常驻通知 → systemuiplugin + frameworks_base (NotificationService)
```

493 的根因是原生 shade 仍可展开，不是 FDE 顶栏本身；不要把 493 直接归到 `systemuiplugin` 就结束。

### 3.3 文件、文档、文件选择

```text
文件管理器/文件选择/文档
  ├─ FilesActivity、DocumentsUI、文件列表 → packages_apps_documentsui
  ├─ 窗口标题栏拖动/freeform → packages_apps_documentsui + frameworks_base
  └─ 文件类型/缩略图/权限 → DocumentsUI 或对应 provider
```

### 3.4 日历、Provider

```text
日历启动/日程/Provider
  ├─ AllInOneActivity、日历 UI → platform/packages/apps/Calendar
  ├─ authority com.android.calendar、provider 注册 → platform/packages/providers/CalendarProvider
  └─ 产品镜像是否包含 provider → device_fde + 构建产物
```

498 的“启动即退出”既有应用侧，也可能是产品镜像缺 provider；分流时必须同时看应用和 provider，不能只看 `packages/apps/Calendar`。

### 3.5 应用自身/账号/网络

```text
王者荣耀、微信扫码、第三方账号
  └─ 应用自身/网络/账号；不是 FDE 模块
```

499 的扫码回调属于应用/账号链路，不应硬分到 FDE 组件；除非有窗口/输入法/网络栈证据。

## 4. 负向信号

- 看到 `com.android.launcher3` 不一定是 Launcher3 仓库：FDE 应用列表是 TaskPlugin 插件，宿主进程仍是 launcher3。
- 看到 `com.boringdroid.systemui` 不要只归 `systemuiplugin`：493 的 NativeShade 在 `frameworks_base`。
- 看到“状态栏”不要直接归 SystemUI：FDE 顶栏是插件，原生 shade 是 AOSP。
- 看到“文件”不要直接归 Launcher：FilesActivity 在 DocumentsUI。
- 看到“日历”不要只归 Calendar：provider/authority 可能在 CalendarProvider 或产品镜像。
- 看到第三方游戏/微信，不要硬分 FDE 组件。

## 5. 案例索引

| issue | 现象摘要 | 组件候选 | 状态 | 备注 |
|---|---|---|---|---|
| 491 | 应用列表文本筛选退出重开不复位 | `taskplugin` | 已确认（映射 + 设备截图） | 搜索框空但列表仍过滤 |
| 492 | 文件窗口标题栏按住停顿后拖动失效 | `packages_apps_documentsui` + `frameworks_base` | 已确认（映射） | freeform 输入/窗口；设备复现未完成 |
| 493 | 状态栏下拉仍出原生控制中心 | `frameworks_base` + `systemuiplugin` | 已确认（映射 + 设备 + log） | `SHADE_EXPAND`、`NotificationShade` |
| 494 | 应用列表滚轮一格翻两页 | `taskplugin` | 已确认（映射） | 滚轮输入链路仍建议按输入层排查 |
| 496 | 点击文件图标开两个文件窗口 | `packages_apps_documentsui` | 已确认（映射） | 当前设备双击只开 1 个窗口；单击只选中图标 |
| 497 | 通知“清空”后残留常驻通知 | `systemuiplugin` + `frameworks_base` | 已确认（映射） | 常驻通知为 NO_CLEAR；设备复现未完成 |
| 498 | 启动日历异常退出 | `platform/packages/apps/Calendar` + `CalendarProvider` | 已确认（映射） | 设备启动失败，crash 日志未捕获；provider 已注册 |
| 499 | 王者微信扫码后未进游戏 | 应用自身/账号/网络 | 已确认（不归 FDE 组件） | 需手机微信扫码，非模块分流问题 |

> 确认的是“问题归哪个组件”，不代表该 issue 已修复或已复现。设备侧结论仍以 issue 的证据和最新验证为准。

## 6. 维护流程

1. 新增条目：优先使用 `package`/`activity`/`log-tag` 精确信号；只有文案时才用 `keyword`。
2. 人工确认后写 `data/knowledge/component-map/entries.md`，`source: human`、`confidence: high`、`last_validated` 当天、`notes` 写来源 issue。
3. 同一个 `kind`+`value` 只保留一条有效映射；冲突以学习条目为准，保留历史备注。
4. 项目迁移/重构后更新 `local_path` 和 `last_validated`；过期条目标 `low` 或删除。
5. 每次确认后跑 `python -m unittest tests.test_component_map`。

## 7. 已确认后的观察项

以下组件归属已确认；后续只需按新证据更新“设备现象”，不要再把它们当成未归属候选：

- 498：`platform/packages/apps/Calendar` 与 `CalendarProvider`。设备当前启动失败、crash 日志未捕获；若后续有崩溃栈，优先核对 provider/产品镜像。
- 494：应用列表滚轮归 `taskplugin`；若修复仍无效，再沿输入层查 `packages_apps_launcher3` / `frameworks_base`。
- 492：freeform 标题栏拖动归 `packages_apps_documentsui` + `frameworks_base`；设备复现未完成，后续按窗口/输入层取证。
- 496：文件窗口归 `packages_apps_documentsui`；当前设备双击只开 1 个窗口，单击只选中图标，手势差异需在复现时注明。
- 499：应用自身/账号/网络，不归 FDE 组件；除非出现窗口/输入法/网络栈证据。
- `entries.md` 的 `taskplugin` / `systemuiplugin` 已切换到 manifest 名；旧别名只保留在 `notes` 中。
