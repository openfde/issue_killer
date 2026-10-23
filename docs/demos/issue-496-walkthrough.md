# 496 端到端 Demo：桌面点击文件图标打开两个窗口

> 本文按 issue #496 的实际产物整理：3 个 revision、2 个 PR、6 条 issue 评论、最终归档和知识候选。
> 496 的采集发生在“日志开关预检”和“标题 build 版本规则”强化之前；文中用“当前流程”标出后来新增的步骤。
> 用户输入用演示用的最短回复；Pi 输出取自实际分析、补丁、PR 和评论，关键节点格式按当前工作流。
>
> 最终结果：`confirmed_fixed → archived`（2026-10-21T08:56Z）；issue 仍 `OPEN`，PR #3 仍 `OPEN/unmerged`，合并和关闭由人工完成。

## 环境

```sh
docker exec -it openfde-ai bash
pi
```

以下 `/skill:...` 都在 Pi 会话内执行，不是 shell 命令。

## Step 0. 取证与建 issue

496 的输入是已有 bugreport + 截图（等价于“已有证据、不重新连设备”的 D 模式），issue 于 2026-10-21T02:18Z 创建。本轮没有重新执行现场采集，因此 Step 0 从 issue 正文开始；当前 A/B/C/D 采集菜单见[取证采集](../architecture/intake.md)。

当前流程在 A/C 现场采集前会检查日志开关：

```text
Pi> 采集前检查 log.tag=<TAG>
    - 已经是 V/VERBOSE：继续
    - 不是：执行 setprop log.tag.<TAG> V；失败则停止
```

496 发生时还没有这个预检；revision 3 依赖的是 `OpenFdeFix496` 的**无条件 `Log.i`**，所以不依赖 `log.tag`。当前流程仍会把日志开关作为采集前确认项。

标题规则：标题必须带 **build 版本号**，不能用“Android 17”这类 OS 版本代替。496 最初标题是“（Android 17）”，后来修正为“（CP2A.260605.016）”；当前 `collect-device-evidence` 和 `enrich-issue-intake` 已强制该规则。

实际 issue 正文（节选）：

```text
标题：桌面点击文件图标会打开两个文件窗口（CP2A.260605.016）

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
- 02:14:40.276 创建 com.android.documentsui/.LauncherActivity（task 875）
- 02:14:40.308 创建 .files.FilesActivity（task 876）
- 02:14:40.314 LauncherActivity 被 finish
- 02:14:40.353 再次创建 .files.FilesActivity（task 877）

两个 FilesActivity 的 Intent 相同
（dat=//com.android.documentsui.launchControl#1792548880300），
均处于可见 freeform 状态。

## 附件
- bugreport-fde_arm64-CP2A.260605.016-2026-10-21-02-14-57.zip
- screen.png
```

issue：https://github.com/openfde/openfde/issues/496

## Step 1. revision 1：根因、修复与 PR #2

```text
用户> /skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 496
```

Pi 内部连续执行：拉取 issue → 下载/解包 bugreport → 组件归属 → 源码追溯 → 分析校验 → 置信度分流。到关键节点停下：

```text
Pi> 【定位结论（revision 1）】
    问题落在 DocumentsUI：LauncherActivity 在单次点击中被系统重建，重建后的
    第二次 launch() 经 restoreTask() 再次启动 FilesActivity；叠加
    documentLaunchMode="always"，单次点击出现两个文件窗口。
    依据：E1 task dump（task 876/877 均 visible freeform）；
          E2 wm_relaunch_resume_activity reason=d00，同一 record 两次 performCreate；
          E3 Starting new task / Restoring existing task，伪 URI 相同。
    组件：packages/apps/DocumentsUI @ 79e0b906（fde_17）
    产物：analysis/analysis.md、analysis/analysis-validation.json

    修复置信度：72%（根因 high；重建触发点/documentLaunchMode 改动动机未证实）

    下一步（回复 A/B/C）：
    A. 进入修复方案评估
    B. 先展示 LauncherActivity 关键代码
    C. 暂停本轮
```

```text
用户> A
```

```text
Pi> 【修复方案（revision 1，后被证伪）】
    推荐 A：LauncherActivity.onCreate 增加重建幂等防护
    - 仅在 savedInstanceState == null 时 launch()
    - 配置变更重建时直接 finish()
    - 优点：最小改动；风险：依赖重建携带 savedInstanceState

    备选 B：恢复 AndroidManifest documentLaunchMode="intoExisting"
    备选 C：框架侧避免重建 NoDisplay LauncherActivity
```

修复 diff（revision 1）：

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

```text
用户> A

Pi> 【修复 PR（revision 1）】
    项目：packages_apps_documentsui
    链接：https://github.com/openfde/packages_apps_documentsui/pull/2
    分支：ai/issue-496-documentsui-avoid-duplicate-filesactivity
    提交：f33d76db95a309f27f8803cfa43adbd81796e128
    只创建、未合入、未验证。

    【交付评论】
    https://github.com/openfde/openfde/issues/496#issuecomment-6306868107
    包含：范围 / 证据 / 根因 / 完整 unified diff / 风险 /
          验证步骤 / not_run / PR / 验证征询
    状态：awaiting_verification
```

revision 1 的结论后来被证伪：`LauncherActivity` 在 `finish()` 之后，`ActivityThread` 不会保存实例状态，重建时 `savedInstanceState` 恒为 `null`，所以这个守卫不会生效。PR #2 仍 `OPEN`，已被 revision 3 的 PR #3 取代；两个 PR 都未合入。

## Step 2. 回归 1 → revision 2：清单改回 intoExisting

开发人员在 issue 回复新 bugreport（03:39）：

```text
开发> 仍有问题
      [bugreport-fde_arm64-CP2A.260605.016-2026-10-21-03-39-20.zip]
      评论：https://github.com/openfde/openfde/issues/496#issuecomment-6307464280
```

```text
Pi> 归档 revision 1（outcome: regression）→ revision 2。
    新证据：回归 bugreport 的 logcat 已滚动，无法重建完整时间线；
    可见成对 taskId（888/887、891/890、894/893），现象与原始一致。
    当时可选“重新定位根因”或“调试 PR”，开发选择重新定位。

    【根因（revision 2）】
    1. AndroidManifest.xml:212 把 FilesActivity 设为 documentLaunchMode="always"
       （AOSP 上游为 intoExisting）。
    2. ActivityStarter 在 always 下追加 FLAG_ACTIVITY_MULTIPLE_TASK，
       使启动不复用既有任务。
    3. LauncherActivity.finish() 使 relaunch 时 savedInstanceState 恒为 null，
       revision 1 的守卫无效。
    4. freeform 配置变化使 onCreate 执行两次，第二次 restoreTask() 再次启动，
       又新建一个 FilesActivity 任务。
    修复置信度：80%
```

revision 2 的修复：

```diff
--- a/AndroidManifest.xml
+++ b/AndroidManifest.xml
@@ -209,7 +209,7 @@
             android:name=".files.FilesActivity"
             android:taskAffinity=""
             android:launchMode="standard"
-            android:documentLaunchMode="always"
+            android:documentLaunchMode="intoExisting"
             android:exported="true"
             android:theme="@style/LauncherTheme"
             android:configChanges="locale|layoutDirection">
```

同时加入诊断 TAG `OpenFdeFix496`（无条件 `Log.i`），用于确认运行构建包含补丁，并记录 `findTask()` / `restoreTask()` / `FilesActivity` 的 taskId 与 flags。

```text
Pi> 【修复 PR（revision 2）】
    项目：packages_apps_documentsui
    链接：https://github.com/openfde/packages_apps_documentsui/pull/3
    分支：ai/issue-496-documentsui-documentlaunchmode-intoexisting
    提交：6f2e67efe54c60c89b617987b7d0b0e7d7485d41
    只创建、未合入、未验证。

    【交付评论】
    https://github.com/openfde/openfde/issues/496#issuecomment-6309188622
    状态：awaiting_verification
```

## Step 3. 回归 2 → revision 3：清理持久化的 MULTIPLE_TASK

开发人员再次回复“仍有问题”，这次带 bugreport 和 `OpenFdeFix496` 日志：

```text
开发> 仍有问题
      [bugreport-fde_arm64-CP2A.260605.016-2026-10-21-08-08-30.zip]
      OpenFdeFix496 日志显示：
      08:08:05.400 LauncherActivity.onCreate taskId=919
                    issue496-fix-applied documentLaunchMode=intoExisting
      08:08:05.406 findTask(): selected taskId=901
                    data=//...launchControl#1792552976384 flags=0x18080000
      08:08:05.406 restoreTask(): startActivity flags=0x18080000
      08:08:05.422 START .files.FilesActivity flg=0x18080000 → task 920
      08:08:05.442 同一 ActivityRecord 再次 onCreate
      08:08:05.444 findTask(): selected taskId=920
      08:08:05.457 START .files.FilesActivity flg=0x18080000 → task 921
      08:08:05.476 / 05.655 FilesActivity.onCreate t920 / t921
      评论：https://github.com/openfde/openfde/issues/496#issuecomment-6311272934
```

```text
Pi> 归档 revision 2（outcome: regression）→ revision 3。
    intoExisting 已生效，但问题仍在：不是清单没生效，而是历史任务
    baseIntent 里持久化了 FLAG_ACTIVITY_MULTIPLE_TASK。

    【根因（revision 3）】
    1. 0x18080000 = NEW_TASK | MULTIPLE_TASK | NEW_DOCUMENT。
       残留任务 901 是 always 时期创建的，baseIntent 已带 MULTIPLE_TASK。
    2. restoreTask() 原样重放该 intent，没有清理 flag。
    3. 框架 resolveReusableTask() 只有在 NEW_TASK 且 MULTIPLE_TASK == 0
       时才复用既有任务；intoExisting 本身不会剥离调用方显式携带的 flag，
       只有 DOCUMENT_LAUNCH_NEVER 会剥离。
    4. freeform relaunch 让 onCreate 执行两次，第二次本可复用刚建的 920，
       却因 MULTIPLE_TASK 又新建 921。

    修复置信度：80%
    依据：E5（SYSTEM LOG 时间线）、E6（wm_relaunch reason=d80）、
          E7（task 920/921 同时 visible freeform）、ActivityStarter 3236-3238 /
          3645-3648 / 3595-3621 / 2986-2993、LauncherActivity 114-121
```

开发选择 A：把 revision 3 追加到已有 PR #3 分支：

```text
用户> A

Pi> 【修复 PR（revision 3）】
    项目：packages_apps_documentsui
    链接：https://github.com/openfde/packages_apps_documentsui/pull/3
    分支：ai/issue-496-documentsui-documentlaunchmode-intoexisting
    追加提交：dc224fd5c7cb59f5cf610b986e5d28fe21abb1ec
    上一提交：6f2e67e（清单 intoExisting + 诊断日志）
    只创建/更新、未合入、未验证。

    【交付评论】
    https://github.com/openfde/openfde/issues/496#issuecomment-6311706649
    状态：awaiting_verification
```

最终生效的两处修复：

```diff
--- a/AndroidManifest.xml
+++ b/AndroidManifest.xml
@@ -209,7 +209,7 @@
-            android:documentLaunchMode="always"
+            android:documentLaunchMode="intoExisting"
```

```diff
--- a/src/com/android/documentsui/files/LauncherActivity.java
+++ b/src/com/android/documentsui/files/LauncherActivity.java
@@ -147,6 +147,9 @@
         try {
+            // Drop MULTIPLE_TASK persisted by an older "always" build.
+            intent.setFlags(intent.getFlags() & ~Intent.FLAG_ACTIVITY_MULTIPLE_TASK);
             // TODO: This doesn't appear to restore a task once it has stopped running.
             startActivity(intent);
```

两处必须同时存在：只改清单对已有残留任务无效；只清 flag 时 `always` 仍会让框架重新追加 `MULTIPLE_TASK`。完整 diff、判读方法和回归项见 revision 3 评论和 PR #3。

## Step 4. 验证通过与归档

```text
开发> 验证通过
      评论：https://github.com/openfde/openfde/issues/496#issuecomment-6311930786
      时间：2026-10-21T08:48:45Z（revision 3 / commit dc224fd）
```

轮询器在 08:55:11Z 读取验证评论，状态自动推进：

```text
awaiting_verification
  → confirmed_fixed
  → archived（2026-10-21T08:56:00Z）

verification:
  result=passed
  verified_revision=3
  verified_commit=dc224fd5c7cb59f5cf610b986e5d28fe21abb1ec
  source_comment=6311930786
  note=closure is human-only; agent must not close the issue or merge PR #3
```

归档产物：

```text
.fde-ai/issues/496/
  archive/case.json
  archive/revision-1/{state,attachments,replies-seen}.revision-1.json
  archive/revision-2/{state,attachments,replies-seen}.revision-2.json
  archive/revision-3/{state,attachments,replies-seen,fetch-meta}.revision-3.json
  input/、evidence/、analysis/、solution/、patch/、comment/
```

`archive/case.json` 记录 issue 快照哈希、证据、源码 commits（DocumentsUI `79e0b90`、framework `ab9ac37`）、结论、补丁、PR、验证结果和归档时间。

收尾状态：

- issue 仍 `OPEN`，PR #3 仍 `OPEN/unmerged`；代理按策略不合并、不关闭，需人工处理。
- PR #2（revision 1）也仍 `OPEN`，已被 PR #3 取代。
- 496 的归档 issue 快照仍保留当时的“（Android 17）”标题；实际 issue 标题已修正为“（CP2A.260605.016）”，当前 intake 技能强制 build 版本。
- 496 的状态和产物在容器卷 `/workspace/.fde-ai`；宿主机 `~/fde-ai-assistant/.fde-ai` 不包含 496。

## Step 5. 知识候选（归档后）

归档后生成了候选事实：

```text
/workspace/data/knowledge/proposed/issue-496-documentsui-launch-task-reuse.md
status: proposed
review: pending
case_id: issue-496-revision-3
```

候选包含 5 条事实：

- F1 `LauncherActivity` 的任务去重契约；
- F2 框架复用任务要求 `MULTIPLE_TASK == 0`；
- F3 `intoExisting` 不剥离调用方显式 `MULTIPLE_TASK`；
- F4 FDE freeform 下 `LauncherActivity.onCreate` 执行两次；
- F5 生效修复：清单改 `intoExisting` + `restoreTask()` 清 flag。

下一步三选一：

```text
A. 审核后 promote-knowledge：把候选纳入活动知识 Wiki 索引，
   保留 case 引用和晋升审计；不改代码、不合并/关闭 PR/issue。
B. 保持现状：人工合入 PR #3 并关闭 issue #496；
   代理不合入、不关闭、不再发评论。
C. 转到其他问题：继续 <编号>，#496 不再迭代。
```

候选当前不在活动索引中；`retrieve-knowledge` 暂时检索不到。晋升流程和 `parallel-world-design.md` 这类设计文档的纳入方式，见知识沉淀相关文档。

## 产物与链接

| revision | 触发 | 修复 | PR / commit | 交付评论 | 结果 |
| --- | --- | --- | --- | --- | --- |
| 1 | 初始 issue | `onCreate` 的 `savedInstanceState` 守卫 | PR #2 / `f33d76d` | [6306868107](https://github.com/openfde/openfde/issues/496#issuecomment-6306868107) | 回归：6307464280 |
| 2 | 03:39 bugreport | 清单 `always → intoExisting` + `OpenFdeFix496` 诊断 | PR #3 / `6f2e67e` | [6309188622](https://github.com/openfde/openfde/issues/496#issuecomment-6309188622) | 回归：6311272934 |
| 3 | 08:08 bugreport + 日志 | 追加 `restoreTask()` 清 `MULTIPLE_TASK` | PR #3 / `dc224fd` | [6311706649](https://github.com/openfde/openfde/issues/496#issuecomment-6311706649) | 验证通过：6311930786 → archived |

- issue：https://github.com/openfde/openfde/issues/496
- PR #2（revision 1，已取代，仍 open）：https://github.com/openfde/packages_apps_documentsui/pull/2
- PR #3（revision 2/3，当前修复，仍 open）：https://github.com/openfde/packages_apps_documentsui/pull/3
- 回归 1：https://github.com/openfde/openfde/issues/496#issuecomment-6307464280
- 回归 2：https://github.com/openfde/openfde/issues/496#issuecomment-6311272934
- 验证通过：https://github.com/openfde/openfde/issues/496#issuecomment-6311930786

## 最短演示输入

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 496
A
（GitHub：仍有问题 + bugreport 03:39）
（GitHub：仍有问题 + bugreport 08:08 + OpenFdeFix496 日志）
（GitHub：验证通过）
（可选：审核知识候选后回复 A/B/C）
```

## 这条 case 暴露的流程问题

- **不能只看第一个 patch 就结束**：revision 1 的 `savedInstanceState` 守卫看似合理，但 `finish()` 让该值恒为 `null`；必须用新日志证伪。
- **清单修复不等于清理历史状态**：`intoExisting` 只影响新启动；已有任务 baseIntent 中的 `MULTIPLE_TASK` 必须在 `restoreTask()` 清理。
- **完整 diff 和 marker 很重要**：revision 2/3 都附完整 diff、诊断 TAG 和判读方法，才能让开发快速确认“补丁是否在运行构建里”以及“是否真的复用 task”。
- **标题必须带 build 版本**：496 最初用了“Android 17”，后续修正为 `CP2A.260605.016`；当前 intake 技能已强制 build 版本，避免同类问题。
- **验证通过后的边界**：轮询器可以自动归档，但按策略不合并 PR、不关闭 issue；人工完成合入/关闭。
- **状态目录要分清**：容器运行时的 `.fde-ai` 在命名卷中，和宿主仓库目录不是同一份；排查 496 要到容器卷里看。
