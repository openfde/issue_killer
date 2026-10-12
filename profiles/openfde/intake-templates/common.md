# 通用采集（common）

## 关键词/现象

任意现象都先采集本节；无法匹配子系统时以本节为主并标注不确定性。

## 必采

- 版本与机型：`adb shell getprop | grep -E "ro\.(build|product|boot)\."`（或逐项 `getprop ro.build.fingerprint` 等）
- 时间与运行时长：`adb shell date; adb shell uptime`
- 内存与存储：`adb shell cat /proc/meminfo | head -5; adb shell df -h /data`
- 复现时间窗日志（不清理缓冲，用起始时间过滤）：`adb logcat -d -T '<复现前1分钟>' -v threadtime | head -c 2000000`（超过 2MB 时按 tag 收窄）
- 崩溃缓冲：`adb logcat -d -b crash -T '<复现前1分钟>' -v threadtime`
- 截图：`adb exec-out screencap -p > capture/screen.png`
- 前台界面：`adb shell dumpsys activity activities | grep -E "mResumedActivity|topResumedActivity" | head -5`

## 选采（允许失败）

- 内核最近日志：`adb shell dmesg | tail -300`（部分设备限制）
- 电源状态：`adb shell dumpsys battery`

## 预期标记

- `ro.build.fingerprint=`、`ro.product.model=` 存在且非空
- logcat 时间窗内至少 1 行 `E/` 或 `W/` 级别输出

## 常见坑

- 先复现再抓、不要重启设备；日志缓冲被覆盖是缺证主因。
- `-T` 的时钟取设备时间（`adb shell date` 为准）。
- 截图只拍“问题现象可见的那一屏”，不要用桌面代替。
