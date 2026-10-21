# 496 端到端 Demo：桌面点击文件图标打开两个窗口

> 本文按 issue #496 的实际产物（issue 正文、analysis、solution、patch、PR、交付评论）整理。
> 496 的实际采集发生在“日志开关预检”加入前；下方按当前流程展示该步骤。
> 用户输入使用演示用的最短回复；Pi 输出取自实际分析/方案/补丁/评论，关键节点格式按当前工作流。

## 环境

```sh
docker exec -it openfde-ai bash
pi
```

以下 `/skill:...` 都在 Pi 会话内执行，不是 shell 命令。

## Step 0. 取证采集（提 issue 前，可选）

```text
用户> /skill:collect-device-evidence 现象：桌面点击文件图标会打开两个文件窗口；设备：fde_arm64；复现时间：02:14
```

```text
Pi> 采集方式：
    A. 最小集：bugreport + 截图（默认；录屏按需）
    B. 不采集，只生成 issue 草稿
    C. 先现场复现，复现完成后再采集
    D. 事后证据：已有 bugreport，不连设备
    回复 A/B/C/D；A/C 请给设备（IP/序列号）。
```

```text
用户> A

Pi> 设备：<序列号>；日志开关：log.tag=<当前值>（非 V 将 setprop log.tag V）；
    采集：setprop log.tag V + bugreport + 截图；现在开始？
    回复“开始采集”（现场复现请回复“复现完成”）。
```

```text
用户> 开始采集

Pi> 日志开关：log.tag=<原值> → V；正在采集...
    完成：data/intake/2026-10-21-documentsui-duplicate-window/bugreport-...zip
    文件：bugreport-...zip、screen.png
    日志开关：log.tag=<原值> → V
    ---- issue-draft.md ----
    ## 现象
    在桌面点击文件图标，会同时打开两个文件窗口，必现。
    ...
    ## 附件
    - bugreport-...zip
    - screen.png
    ---- end ----
    提交：新建 issue，粘贴上述正文，拖入 zip 与截图。
    取回：宿主机路径 ~/fde-ai-assistant/data/intake/<slug>
    scp：scp -r <宿主机用户>@<宿主机IP>:~/fde-ai-assistant/data/intake/<slug> <本机目录>
```

用户在 GitHub 新建 issue。实际 #496 正文：

```text
标题：桌面点击文件图标会打开两个文件窗口（Android 17）

## 现象
在桌面点击文件图标，会同时打开两个文件窗口，必现。

## 时间线
- 发生时间：约 2026-10-21 02:14（现场复现后立即采集）

## 环境
- 设备：fde_arm64（OpenFDE）
- 系统版本：Android 17（Build CP2A.260605.016 release-keys）
- 分辨率：1920x1080
- 桌面：com.android.launcher3（QuickstepLauncher）
- 文件管理器：com.android.documentsui

## 复现步骤（推测，未确认）
1. 在桌面点击任意文件图标。
2. 观察：会同时弹出两个文件管理器窗口（DocumentsUI 的 FilesActivity）。

## 预期结果
点击一次只打开一个文件窗口。

## 实际结果
点击一次同时打开两个文件窗口。

## 日志线索（bugreport）
单次点击后 activity 创建时间线（02:14:40）：
- .276 创建 .LauncherActivity（task 875）
- .308 创建 .files.FilesActivity（task 876）
- .314 LauncherActivity 被 finish
- .353 再次创建 .files.FilesActivity（task 877）

两个 FilesActivity 的 Intent 相同（dat=//com.android.documentsui.launchControl#1792548880300），均处于可见 freeform 状态。

## 附件
- bugreport-fde_arm64-CP2A.260605.016-2026-10-21-02-14-57.zip
- screen.png

## AI 取证声明
本文由 AI 取证助手根据现场只读采集（bugreport + 截图）生成，仅供开发定位参考；复现步骤与根因尚未经人工确认。
```

## Step 1. 启动分析

```text
用户> /skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 496
```

Pi 内部连续执行：拉取 issue → 解包 bugreport → 组件归属 → 源码追溯 → 分析校验。到关键节点停下：

```text
Pi> 【定位结论】
    问题落在 DocumentsUI：LauncherActivity 在单次点击中被系统重建，重建后的
    第二次 launch() 经 restoreTask() 再次启动 FilesActivity；叠加
    documentLaunchMode="always"，单次点击出现两个文件窗口。
    依据：E2（wm_relaunch reason=d00，同一 record 两次 performCreate）；
          E3（Starting new task / Restoring existing task，伪 URI 相同）；
          task dump（task 876、877 均 visible=true mode=freeform）。
    产物：analysis/analysis.md、analysis/analysis-validation.json

    下一步（回复 A/B/C）：
    A. 继续做根因解析与修复评估
    B. 先展示 LauncherActivity 关键代码
    C. 暂停本轮
```

```text
用户> A
```

## Step 2. 根因重点解析与置信度分流

```text
Pi> 【根因重点解析与分流】
    单次点击 → 启动无界面的 LauncherActivity（task 875）→ 首次 launch() 走
    startTask() 创建 FilesActivity（task 876）→ LauncherActivity 被系统重建
    （wm_relaunch_resume_activity reason=d00）→ 重建后的 onCreate 再次无条件
    launch() → findTask() 找到 task 876 → restoreTask() 再 startActivity →
    因 FilesActivity 的 documentLaunchMode="always"（OpenFDE 由 intoExisting
    改来），这次 startActivity 新建 task 877 而不是复用 task 876。
    直接原因：launch() 没有重建幂等防护。
    根本原因：documentLaunchMode=always 与 freeform 重建叠加，使
    restoreTask() 的去重契约失效。
    未证实：LauncherActivity 重建的精确框架触发点；always 的改动动机。
    修复置信度：72%（根因 high / 修复 72%；≥70，进入修复方案）。
    依据：LauncherActivity.java:62-68、70-120；AndroidManifest.xml:212；
          logcat 02:14:40.267→.364。
    产物：analysis/analysis.md

    下一步（回复 A/B/C）：
    A. 进入修复方案评估
    B. 展示关键代码
    C. 暂停本轮
```

```text
用户> A
```

## Step 3. 修复方案

```text
Pi> 【修复方案】
    推荐 A：LauncherActivity.onCreate 增加重建幂等防护
    - 改动点：src/com/android/documentsui/files/LauncherActivity.java:62-68
    - 机制：仅在 savedInstanceState == null 时 launch()；配置变更重建直接 finish()
    - 优点：最小改动，精准命中直接原因；不改 documentLaunchMode 语义
    - 风险：依赖重建携带 savedInstanceState（标准行为）；低

    备选 B：恢复 documentLaunchMode="intoExisting"
    - 改动点：AndroidManifest.xml:212
    - 优点：一行改动，恢复 AOSP 去重契约
    - 风险：可能影响 OpenFDE 有意引入的多实例/parallel world 附加窗口

    备选 C：框架侧避免重建 NoDisplay LauncherActivity
    - 缺点：触发点未定位、影响面大；不推荐

    下一步（回复 A/B/C）：
    A. 按推荐方案 A 生成补丁并创建 PR
    B. 只保留补丁文件
    C. 暂停
```

```text
用户> A
```

## Step 4. 代码修改（Pi 展示统一 diff）

````text
Pi> 【代码修改（未验证）】
    src/com/android/documentsui/files/LauncherActivity.java

```diff
@@ -61,8 +61,13 @@
     @Override
     protected void onCreate(Bundle savedInstanceState) {
         super.onCreate(savedInstanceState);
 
-        launch();
+        // Only launch on the initial creation. On a configuration-change
+        // recreation (e.g. freeform windowing resize) the task was already
+        // launched; re-running launch() would open a duplicate FilesActivity.
+        if (savedInstanceState == null) {
+            launch();
+        }
 
         finish();
     }
```

    下一步（回复 A/B/C）：
    A. 生成 PR（只创建、不合入）
    B. 只保留补丁文件
    C. 暂停
````

```text
用户> A
```

## Step 5. 创建 PR 并发布交付评论

```text
Pi> 【修复 PR】
    项目：packages_apps_documentsui
    链接：https://github.com/openfde/packages_apps_documentsui/pull/2
    分支：ai/issue-496-documentsui-avoid-duplicate-filesactivity
    base：fde_17（仅作目标，未合入）
    提交：f33d76db95a309f27f8803cfa43adbd81796e128
    只创建、未合入、未验证。

    【交付评论】
    已发布到 issue：
    https://github.com/openfde/openfde/issues/496#issuecomment-6306868107

    评论包含：问题范围 / 证据与定位 / 根因 / 完整 unified diff /
    影响与风险 / 建议验证步骤 / not_run / 修复 PR / 验证征询。

    状态：awaiting_verification（等待开发回复验证结果）
```

实际交付评论：https://github.com/openfde/openfde/issues/496#issuecomment-6306868107

实际 PR：https://github.com/openfde/packages_apps_documentsui/pull/2

## Step 6. 验证闭环（当前停在这里）

开发人员自测后，在 issue 回复：

```text
开发> 验证通过
```

```text
Pi> 已收到“验证通过”，状态 → confirmed_fixed，归档 case。
    issue 关闭仍由人工完成。
```

或者：

```text
开发> 仍有问题（附新 logcat/bugreport）
```

```text
Pi> 归档当前 revision → revision 2，重新提取证据并分析；
    新评论同样包含完整 diff 与验证征询。
```

## 最短输入序列（演示用）

```text
/skill:collect-device-evidence 现象：桌面点击文件图标会打开两个文件窗口；设备：fde_arm64；复现时间：02:14
A
开始采集
（在 GitHub 创建 issue #496）
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 496
A
A
A
A
（等待开发回复：验证通过 / 仍有问题）
```
