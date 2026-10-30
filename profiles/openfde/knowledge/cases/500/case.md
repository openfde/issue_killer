# Issue #500 · 通过 Launcher 启动应用选择器时页面全屏并隐藏 Dock 与状态栏（CP2A.260605.016）

- 状态：`confirmed_fixed`
- revision：`2`
- 知识状态：`verified`
- 设备/构建：model=tangorpro, build=CP2A.260605.016, android=17
- 标签：auto-hide, chooser, desktop-mode, display-policy, frameworks_base, resolver, window-manager, windowIsFloating
- 更新时间：2026-10-30T06:31:01Z

## 现象

FDE 桌面点击无默认打开者的文件图标（Desktop/get-openfde.sh.1）后，系统选择器 ResolverActivity 以整页全屏出现：弹窗只占屏幕下部（截图白色区域 x=720..1199、y=574..1078），其余区域为空白 + 70% dim，同时 FDE 状态栏与 Dock 被隐藏（E1/E5/E7/E8）。

## 组件

- frameworks_base | fde-sources/frameworks/base | high | tree+guide
- platform/packages/modules/IntentResolver | medium | manifest+tree_absence
- systemuiplugin | fde-sources/packages/apps/BoringdroidSystemUI | high | guide
- packages_apps_launcher3 | fde-sources/packages/apps/Launcher3 | high | tree

## 信号

- （无）

## 根因

选择器窗口是非浮动全屏窗口：Theme.DeviceDefault.Resolver 继承非浮动的 Theme.DeviceDefault.DayNight，且未设置 windowIsFloating（core/res/res/values/themes_device_defaults.xml:2597-2624，C10/E11），窗口尺寸恒等于任务 bounds（实测 mAttrs (0,0)(fillxfill)、frame=[0,0][1920,1080]，E6）；而工作表由 ResolverDrawerLayout 在窗口内自下而上绘制，宽度受 resolver_max_width=480dp、折叠高度受 192dp 限制（resolver_list.xml:16-30、dimens.xml:793,1090，C11/C14），窗口高度与弹窗高度无关，多出的区域表现为空白 + 70% dim（E7/E8）。同一窗口因 occludesParent=false 但 auto-hide 判据只用 !mInFreeformMode + 焦点窗口 ACTIVITY_TYPE_STANDARD（DisplayPolicy.java:2989-3013，C1/C5），3000ms 后被当作沉浸式 App 隐藏 statusBars+navigationBars（InsetsPolicy.java:745-748,797，C3/E5），Dock（Taskbar，导航栏 insets provider）随之消失。

## 修复

- summary: route A：Theme.DeviceDefault.Resolver 增加 windowIsFloating=true 让窗口按内容测量（高度=弹窗高度），并在 DisplayPolicy.updateAutoHideState() 追加 occludesParent() 条件使对话框不再触发桌面 auto-hide；同时撤回 rev1 的 freeform 豁免。
- pr: https://github.com/openfde/frameworks_base/pull/10
- pull_request: 10
- commit: 6306ef6bd16e58c8dc4cd9f7bebfbec5428226f1
- branch: ai/issue-500-chooser-desktop-window
- status: OPEN/unmerged
- patch: .fde-ai/issues/500/patch/0001-chooser-dialog-sized-window.patch
- patch_sha256: 9904ea220bf0edfa10addf21bcc3b2117cd3e8b6b88f23c85e5573788c4617bc

## 验证

- status: confirmed_fixed
- verified: true
- verified_by: foryoung2018
- verified_at: 2026-10-30T06:23:12Z
- evidence: ["https://github.com/openfde/openfde/issues/500#issuecomment-6516432134（原文“验证通过”，无附件/日志，scope=revision 2 补丁 PR #10 commit 6306ef6bd1 开发人员自测）"]

## 来源

- issue_dir: .fde-ai/issues/500
- hashes: {"archive_case": "8be7d7fcd28c2cc1f89b7290686479e96ffb47d9d99bf36fdb77e471a6a7cb7b", "components": "26f980ff1a9633e064ef3ca42278200e6f5de9d51ab5f285388cf7fdc9a98514", "evidence": "c0f5c724f4114418fa12ce759d77654bb28be034930bef9233756fead0d179b8", "issue_snapshot": "1a02e4e3cd190ebe55becf4d747ef164d2f0518000790bd919da084b72500f4b", "state": "235a2369e846ec2ea0fa41cc05507ff7eedc985842f1c96bc8cea7435b2718bd"}
- state: .fde-ai/issues/500/state.json
- archive_case: .fde-ai/issues/500/archive/case.json
- components: .fde-ai/issues/500/analysis/components.json
- issue_snapshot: .fde-ai/issues/500/input/issue.json
- evidence: .fde-ai/issues/500/evidence/evidence.json

> 本 case 由自动化脚本生成；`draft` 不代表已验证，晋升 Wiki 需要人工审核。
