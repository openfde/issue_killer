# 取证采集（提 issue 前）

取证助手是提 issue 之前的人工辅助：**发现问题和决定提 issue 始终由人完成**，助手只负责把"该采什么、怎么采、是否采全"变成可执行、可校验的步骤。

## 三个通道

| 通道 | 适用 | 执行者 |
| --- | --- | --- |
| `server_adb`（默认） | 设备与服务器网络可达、已开 adb tcp | 助手在容器内只读执行 |
| `pc`（降级） | 服务器不可达，测试人员 PC 可连设备 | 测试人员运行 `collect_pc.sh` |
| `on_device`（降级） | 不便接 adb 的现场 | 推送 `collect_on_device.sh` 后在设备执行 |

## 流程

1. `plan-evidence-collection`：人工给出现象描述（可选设备信息、时间点），助手匹配 `profiles/openfde/intake-templates/` 子系统模板，在 `data/intake/<日期>-<slug>/` 生成 `collection-plan.json`、三通道脚本与说明；
2. `run-evidence-collection`：仅当人工确认设备序列号后，按只读白名单在服务器 adb 上执行，产出 `evidence-<ts>.zip`、`package-manifest.json` 与 `collection-result.json`；连接失败则保持 planned，改用脚本通道；
3. `validate-intake-package`：对照方案校验完整性与最小数据集，缺项输出“精确到命令”的补充采集请求，通过后 `status: validated`；
4. 人工决定提 issue 并附上取证包（GitHub 附件单文件 ≤ 25MB，默认预算 20MB）。

## 安全与体积约束

- 只读：`logcat -d`、`dumpsys`、`getprop`、`screencap`、白名单路径 `pull`；**禁止 root、禁止 `logcat -c`、禁止安装/卸载/改设置**。
- 日志必须带时间窗与 tag 过滤；超预算先压缩再按时间窗/tag/pid 裁剪重抓，并把裁剪策略写入 `collection-result.json`。
- 设备连接必须先列出 `adb devices` 由人工确认；多设备必须显式 `-s`，不得自动挑选。
- 助手不访问 GitHub、不代提 issue、不发布任何内容；产物只写 `data/intake/`。

## 与 issue 分析衔接

取证包作为 issue 首版证据附件；分析流程在证据阶段按最小数据集校验，缺失时生成同样格式的补充采集请求。子系统模板与后续组件映射知识（component-map）共用同一套治理：人工纠正与新模板都先评审、再沉淀。
