# 子系统：网络（network）

## 关键词/现象

无法上网、Wi-Fi 连不上/掉线、以太网异常、DNS 失败、网速异常、AP 模式异常。

## 必采

- 连接状态：`adb shell dumpsys connectivity | head -200`
- Wi-Fi 状态：`adb shell dumpsys wifi | head -200`
- 网络接口：`adb shell getprop | grep -iE "net\.|wifi|dhcp" | head -40`
- 相关日志（时间窗 + tag）：`adb logcat -d -T '<复现前1分钟>' -v threadtime -s ConnectivityService WifiService WifiStateMachine DhcpClient NetworkMonitor netd WifiHAL wpa_supplicant`
- 接口地址：`adb shell ip -4 addr show | head -40`

## 选采（允许失败）

- 路由表：`adb shell ip route | head -30`
- DNS：`adb shell getprop | grep -iE "dns" | head -10`

## 预期标记

- dumpsys 中含目标网络（SSID/接口名）的状态条目
- 日志含 `ConnectivityService`/`WifiService` 的状态变更或错误行

## 常见坑

- 记录复现时的 SSID/AP/网关信息与时间点。
- “时断时续”类问题建议复现 2-3 次并分别标注时刻。
