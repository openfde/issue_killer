# 取证采集模板库

本目录是“取证助手”的命令模板来源：`plan-evidence-collection` 按现象匹配子系统模板，生成采集方案与三通道脚本；`run-evidence-collection` 只按方案白名单执行；`validate-intake-package` 按方案的预期标记校验完整包。

## 通道

| 通道 | 适用 | 执行者 |
| --- | --- | --- |
| `server_adb`（默认） | 设备与服务器网络可达、已开 adb tcp | 助手在容器内只读执行 |
| `pc`（降级） | 服务器不可达，但测试人员 PC 可连设备 | 测试人员运行 `collect_pc.sh` |
| `on_device`（降级） | 不便接 adb 的现场 | 推送 `collect_on_device.sh` 后在设备执行 |

## 约束

- 全部命令只读：`logcat -d`、`dumpsys`、`getprop`、`screencap`、白名单路径 `pull`；**禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置**。
- 默认大小预算 20MB（GitHub 附件上限 25MB）：日志必须带时间窗与 tag 过滤；超限先压缩再裁剪重抓。
- 每个子系统文件包含：关键词/现象、必采、选采（允许失败）、预期标记、常见坑。
- 新增子系统：复制现有文件结构，补充 `##` 小节并在本文件登记。

## 目录约定

采集产物固定写入 `data/intake/<日期>-<slug>/`：

```text
collection-plan.json      方案与白名单（status: planned/collected/validated/failed）
collect_pc.sh             PC 通道脚本
collect_on_device.sh      设备侧脚本
capture/                  原始采集输出（含逐条命令记录）
evidence-<ts>.zip         打包证据（<= 预算）
package-manifest.json     文件、大小、SHA-256、用途
collection-result.json    设备信息、命令清单、失败项、裁剪策略
intake-validation.json    校验结果与补充采集请求
```
