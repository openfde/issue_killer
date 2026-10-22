# 真实 Bug L0–L3 验证 Runbook

> 用于一次真实 bug 的端到端验证：日志采集（L0）→ 分析（L1）→ 修复（L2）→ 编译安装（L3）。
> 验证助手尚未设计；L3 安装完成后由人工验证，流程停在 `awaiting_verification`。

## 环境就绪

- Docker：`openfde-ai`、`openfde-ai-poller` 运行中
- Pi：`/skill:build-install` 可用
- 构建：29 `/aosp4/hy_fde17` 可 SSH；`build-install.sh` 可执行
- 安装：247 `fde-install-module` + sudoers 已配置
- FDE：`Session RUNNING`，`fde_ctrl` 运行
- 测试：VM 上 91 项通过
- 采集：FDE adb 端口为 **25555**，但当前连接为 `offline`；`waydroid shell` 需要 root
- 验证助手：空位，人工验证

## L0：日志采集与建 issue

使用 `/skill:collect-device-evidence`。

- 设备：`10.31.62.247`（FDE，adb 端口 25555）
- 当前 adb 不可用时的首选：**D 模式**（已有 bugreport，不连设备）
- 现场 A/C 模式需先恢复 adb 授权；不要用 `waydroid shell` 代替（需要 root）
- 采集前按当前流程检查 `log.tag`；复现前设置必要的日志级别
- issue 标题必须带 build 版本（如 `CP2A.260605.016`），不能用 “Android 17” 代替
- 产出：`issue-draft.md` 全文、bugreport、截图、`data/intake/<slug>` 路径
- 人工创建 issue 后，记录 issue 编号/URL

## L1：分析

```text
/skill:run-issue-workflow 使用 profiles/openfde/profile.json 分析问题 <编号>
```

- 证据：bugreport / logcat / 截图 / 复现时间线
- 组件归属；源码追溯；知识检索；分析校验
- 输出 `fix_confidence` 和原因链
- 分流：
  - ≥70：修复流程
  - 50–69：analysis-options + A/B/C/D/E/F，等待开发选择
  - <50：深度分析最多 2 轮
- 关键节点 A/B/C 在会话内确认；issue 评论按 `pr_only`/dry-run 策略

## L2：修复与 PR

- 生成/校验 patch；创建 PR（只创建，不合入）
- 交付评论必须包含：范围、证据、根因、完整 unified diff、风险、验证步骤、not_run、PR、验证征询
- 代理不合并 PR、不关闭 issue
- 记录 PR 编号和模块（用于 L3）

## L3：编译安装

```sh
# issue 最新 PR + 自动模块
sg docker -c './deploy/docker/build-install.sh --issue <编号>'

# 多模块
sg docker -c './deploy/docker/build-install.sh --issue <编号> --module A --module B'

# 指定分支
sg docker -c './deploy/docker/build-install.sh --module <模块> --no-pr --branch <分支>'

# Pi 内
/skill:build-install --issue <编号>
```

- 模块必须先登记在 `deploy/assist/modules.json`
- 线程默认 `--jobs auto`：模块映射优先，缺失按 APK/JAR/native/image 和 `nproc` 估算
- 产物路径：29 → 容器 → 247；SHA-256 校验
- 247 完成安装后启动 FDE；多模块只在最后启动一次
- 代理不自动验证；人工在 FDE 中复测

## 人工验证

- 复测原始 bug 的复现路径
- 采集验证截图/日志（验证助手未设计）
- 回复 `验证通过` 或 `仍有问题`；后者附带新证据进入新 revision

## 这次需要提供

1. 真实 bug 的 issue 编号/URL，或现象描述
2. 设备/日志：现有 bugreport 路径，或恢复 adb 后的设备连接方式
3. L1 期望模块/项目；L3 需要编译安装的模块（可多个）
4. 是否需要指定分支/PR；默认用 issue 最新 PR
5. 人工验证步骤和期望结果

## 当前阻塞

- FDE adb 25555 `offline`：现场采集需修复授权；否则用 D 模式
- `waydroid shell` 需要 root，不能作为 AI 采集通道
- 真实 bug 的模块可能尚未在 `modules.json` 中，需要按 L1 结论补充
- 验证助手未实现，L3 后只能人工验证
