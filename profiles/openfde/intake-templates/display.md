# 子系统：显示与合成（display）

## 关键词/现象

黑屏/花屏/闪烁、窗口错位、拖影、旋转异常、外接显示器无输出、缩放不生效。

## 必采

- 合成器状态：`adb shell dumpsys SurfaceFlinger | head -200`
- 层与刷新：`adb shell dumpsys SurfaceFlinger --list | head -50`
- 显示设备：`adb shell dumpsys display | head -150`
- 窗口状态：`adb shell dumpsys window displays | head -100`
- 相关日志（时间窗 + tag）：`adb logcat -d -T '<复现前1分钟>' -v threadtime -s SurfaceFlinger HWComposer hwc-display display BufferQueueProducer OpenGLRenderer renderengine`
- 截图（现象屏）：`adb exec-out screencap -p > capture/screen.png`

## 选采（允许失败）

- 刷新率/模式：`adb shell dumpsys SurfaceFlinger | grep -iE "refresh|mode|activeMode" | head -30`
- GPU 信息：`adb shell dumpsys gpu | head -40`

## 预期标记

- 截图与现象描述一致（人工确认后再提交）
- 日志含 `SurfaceFlinger` 或 `hwc` 的 `E/`/`W/` 行，或 dumpsys 中目标 layer 存在

## 常见坑

- 截图可能拍不到花屏/闪烁等瞬时问题，需同时录像或多张连拍。
- 外接显示器问题要记录接口与分辨率配置。
