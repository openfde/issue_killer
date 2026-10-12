# 子系统：相机（camera）

## 关键词/现象

预览黑屏/卡死、拍照失败、切换镜头异常、闪光灯错误、录像失败、相机服务崩溃。

## 必采

- 相机服务：`adb shell dumpsys media.camera | head -250`
- 相关日志（时间窗 + tag）：`adb logcat -d -T '<复现前1分钟>' -v threadtime -s CameraService Camera2Client CameraProviderManager CameraHal Camera3Device Camera2CameraImpl`
- 进程状态：`adb shell ps -A | grep -iE "camera|provider" | head -20`
- 截图（预览状态）：`adb exec-out screencap -p > capture/screen.png`

## 选采（允许失败）

- 相机属性：`adb shell getprop | grep -iE "camera|vendor.camera" | head -30`
- HAL 崩溃记录：`adb shell ls -la /data/tombstones/ 2>/dev/null | tail -10`

## 预期标记

- `CameraService` 至少 1 行打开/关闭/错误记录
- 目标相机 ID（0/1/2…）与现象步骤对应

## 常见坑

- 先复现再抓，相机服务重启会冲掉旧日志。
- 预览黑屏需同时截图与录像各有其一更佳（截图可能捕捉不到瞬时黑屏）。
