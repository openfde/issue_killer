# 子系统：音频（audio）

## 关键词/现象

无声/破音/断续、音量调节无效、耳机/扬声器切换异常、录音失败、通话无声。

## 必采

- AudioFlinger：`adb shell dumpsys media.audio_flinger | head -250`
- AudioPolicy：`adb shell dumpsys media.audio_policy | head -200`
- AudioService：`adb shell dumpsys audio | head -150`
- 相关日志（时间窗 + tag）：`adb logcat -d -T '<复现前1分钟>' -v threadtime -s AudioFlinger AudioPolicyManager AudioService AudioTrack AudioRecord audio_hw_primary`
- 播放态：`adb shell dumpsys media.audio_flinger | grep -iE "active|track" | head -40`

## 选采（允许失败）

- 设备路由：`adb shell dumpsys audio | grep -iE "device|route" | head -40`
- 内核声音日志：`adb shell dmesg | grep -iE "asoc|codec|snd" | tail -100`

## 预期标记

- dumpsys 中存在输出/输入设备与音量条目
- 日志含 `AudioFlinger`/`AudioPolicyManager` 的 `E/` 行或路由切换记录

## 常见坑

- 复现“无声”前先确认系统音量与静音状态并截图。
- 通话/蓝牙问题同时启用蓝牙或通话模板采集。
