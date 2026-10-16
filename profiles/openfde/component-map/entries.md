# 组件映射条目（种子）

来源：fde-manifests（openfde.xml）与项目命名事实，`2026-10-12` 由部署流程写入；`keyword` 类为定制经验，复核后调整置信度。

| kind | value | project | local_path | confidence | source | last_validated | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| path | device/openfde/fde | device_fde | device/openfde/fde | high | seed-manifest | 2026-10-12 | FDE 设备树与产品配置 |
| path | hardware/openfde | hardware_openfde | hardware/openfde | high | seed-manifest | 2026-10-12 | FDE 硬件抽象实现 |
| keyword | 应用列表,应用抽屉,全部应用,AppOverviewWindow,LoadedViewPager,AllApps | packages_apps_TaskPlugin | packages/apps/TaskPlugin | high | seed | 2026-10-16 | FDE 桌面应用列表页（TaskPlugin 插件窗口，宿主进程为 com.android.launcher3） |
| keyword | launcher,Launcher3,宿主进程,launcher host | packages_apps_launcher3 | packages/apps/Launcher3 | medium | seed | 2026-10-16 | 仅标准 Launcher3 行为或宿主进程问题映射本仓库；FDE 应用列表 UI 实为 TaskPlugin 插件 |
| keyword | 桌面,窗口,任务栏,任务,desktop,taskbar,window | boringdroidsystemui | packages/apps/BoringdroidSystemUI | medium | seed | 2026-10-12 | FDE 桌面系统 UI（任务栏/窗口装饰） |
| keyword | 任务管理,任务切换,TaskManager | packages_apps_TaskManager | packages/apps/TaskManager | high | seed | 2026-10-12 | 桌面任务管理组件 |
| keyword | TaskPlugin | packages_apps_TaskPlugin | packages/apps/TaskPlugin | high | seed | 2026-10-12 | 桌面任务插件 |
| keyword | 文件,文件管理,文件选择,DocumentsUI | packages_apps_documentsui | packages/apps/DocumentsUI | high | seed | 2026-10-12 | 文件管理器/文件选择器 |
| keyword | 图库,相册,gallery | packages_apps_fdegallery | packages/apps/FdeGallery | high | seed | 2026-10-12 | FDE 图库 |
| keyword | Linux应用,Linux 应用,应用启动,FDELinuxAppLauncher | android_packages_apps_FDELinuxAppLauncher | packages/apps/FDELinuxAppLauncher | high | seed | 2026-10-12 | Linux 应用启动器 |
| keyword | 精选应用,应用商城,上架,CuratedApps | packages_apps_FDECuratedApps | packages/apps/FDECuratedApps | high | seed | 2026-10-12 | 精选应用控制 |
| keyword | SDK,openfde-sdk | openfde-sdk | openfde-sdk | high | seed | 2026-10-12 | FDE SDK |
| keyword | 声音,音频,无声,破音,录音,播放,audio,pulseaudio,alsa | external_pulseaudio | external/pulseaudio | medium | seed | 2026-10-12 | FDE Linux 音频栈（配合 alsa-lib/alsa-plugins/libsndfile） |
| keyword | 蓝牙,蓝芽,bluetooth,BLE | packages_modules_Bluetooth | packages/modules/Bluetooth | high | seed | 2026-10-12 | 蓝牙模块（AOSP 模块路径） |
| keyword | 设置,Settings | packages_apps_Settings | packages/apps/Settings | high | seed | 2026-10-12 | 系统设置（fde-main 定制） |
| keyword | 相机,拍照,预览,camera | packages_apps_Camera2 | packages/apps/Camera2 | medium | seed | 2026-10-12 | 相机应用；HAL 问题看 hardware_interfaces |
| keyword | 合成,图形,渲染,花屏,mesa,OpenGL,GPU | waydroid_android_external_mesa3d | external/mesa | high | seed | 2026-10-12 | Waydroid Mesa 分支（FDE 图形栈） |
| keyword | skia,绘制 | lineageos_android_external_skia | external/skia | high | seed | 2026-10-12 | Skia 分支 |
| keyword | llvm,LLVM | waydroid_android_external_llvm_project | external/llvm-project | high | seed | 2026-10-12 | LLVM 分支 |
| keyword | HAL,hwcomposer,HWC,composer,硬件抽象 | hardware_interfaces | hardware/interfaces | medium | seed | 2026-10-12 | HAL 接口；实现可能在 hardware/openfde |
| keyword | 窗口管理,WMS,WindowManager,窗口异常 | frameworks_base | frameworks/base | medium | seed | 2026-10-12 | fde-main 定制分支 |
| package | com.boringdroid.systemui | boringdroidsystemui | packages/apps/BoringdroidSystemUI | medium | seed | 2026-10-12 | 待运行时校验包名 |
