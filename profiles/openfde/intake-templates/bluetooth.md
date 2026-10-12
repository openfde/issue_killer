# 子系统：蓝牙（bluetooth）

## 关键词/现象

蓝牙打不开/自动关闭、配对或连接失败、音频断续、设备列表为空、蓝牙图标消失。

## 必采

- 服务状态：`adb shell dumpsys bluetooth_manager`
- 相关日志（时间窗 + tag）：`adb logcat -d -T '<复现前1分钟>' -v threadtime -s BluetoothManagerService BluetoothAdapter BluetoothDevice BluetoothA2dp BluetoothGatt BluetoothHeadset StateMachine bt_stack`
- 属性：`adb shell getprop | grep -iE "bluetooth|bt_"`
- 连接态快照：`adb shell dumpsys connectivity | grep -iE "bluetooth|bt-" | head -40`

## 选采（允许失败）

- HCI snoop（需已在开发者选项开启；无 root 可能不可读）：`adb pull /data/misc/bluetooth/logs/btsnoop_hci.log capture/ 2>/dev/null`
- 固件与控制器信息：`adb shell dumpsys bluetooth_manager | grep -iE "firmware|controller|version" | head -20`

## 预期标记

- `BluetoothManagerService` 或 `bt_stack` 至少 1 行状态迁移（`enable`/`disable`/`adapter`）
- 复现步骤中的目标设备 MAC 或名称出现在日志或 dumpsys 中

## 常见坑

- 复现后立刻抓取，蓝牙状态日志刷屏快。
- 开/关蓝牙的复现请记录准确时刻，用 `-T` 收窄。
- A2DP/LE 问题需同时采 `BluetoothA2dp`/`BluetoothGatt` tag。
