# 子系统：启动与崩溃（boot-crash）

## 关键词/现象

开机卡住/反复重启、开机后无桌面、应用崩溃（FC）、系统服务崩溃（system_server）、ANR、native crash。

## 必采

- 崩溃缓冲：`adb logcat -d -b crash -T '<复现前1分钟>' -v threadtime | head -c 1000000`
- 主日志错误行：`adb logcat -d -T '<复现前1分钟>' -v threadtime | grep -E "FATAL|AndroidRuntime|system_server|SIGSEGV|SIGABRT" | head -c 800000`
- 启动属性：`adb shell getprop | grep -E "ro.boot|sys.boot|ro.build.fingerprint"`
- 开机耗时：`adb shell getprop sys.boot_completed; adb shell uptime`
- 进程快照：`adb shell ps -A | head -60`

## 选采（允许失败）

- tombstone 列表与内容（无 root 可能不可读）：`adb shell ls -la /data/tombstones/ 2>/dev/null | tail -10`
- dropbox 摘要：`adb shell dumpsys dropbox --print | grep -E "entry|Tombstone|ANR" | head -40`
- ANR traces 列表：`adb shell ls -la /data/anr/ 2>/dev/null | tail -10`

## 预期标记

- 日志含 `FATAL EXCEPTION`、`SIGSEGV`、`system_server` 重启或 `boot_completed` 异常
- 目标应用/进程名与现象一致

## 常见坑

- 崩溃日志滚动极快，复现后立即采集。
- 开机问题需记录“第几次开机/是否必现/上电时长”。
