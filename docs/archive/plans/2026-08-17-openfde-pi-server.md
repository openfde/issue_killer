# OpenFDE Pi 服务器实施计划

> **归档提示：** 仅供历史参考，不可作为当前操作依据。

> **面向 agent 工作进程：** 必须使用 `superpowers:executing-plans` 或 `superpowers:subagent-driven-development` 逐任务执行本计划；步骤使用复选框语法记录。

**目标：** 增加一个由 systemd 监管的单主机 issue 扫描器，将队列状态保存到 SQLite 并运行有边界的非交互 Pi worker。

**架构：** Python 标准库协调器负责 `gh` 发现、SQLite 队列转换、进程超时和审计日志。Pi 接收单一 issue 及选定 profile 的简短明确提示词；Pi 不承担调度器或持久状态存储职责。

**技术栈：** Python 3 标准库、SQLite、`gh`、Pi CLI、systemd、unittest。

## 全局约束

- 不得修改源码/checkout、应用 patch、构建、测试、提交、推送、创建 PR 或关闭 issue。
- 仅使用 `gh` 访问 GitHub；协调器不执行 GitHub 写入。
- 队列项以 issue 编号和 `updatedAt` 去重，且可原子领取、可重试。
- 所有配置路径相对部署根目录；凭据仅存在于环境文件或密钥管理器。

---

### 任务 1：队列与扫描测试

**文件：**
- 创建：`tests/test_openfde_ai_server.py`

- [ ] 为 SQLite schema 创建、变更 issue 重新入队、原子领取、worker 提示词安全边界和 dry-run 扫描编写失败测试。
- [ ] 运行 `python3 -m unittest tests/test_openfde_ai_server.py -v`；预期因模块未实现而失败。

### 任务 2：确定性服务器协调器

**文件：**
- 创建：`automation/openfde_ai_server.py`
- 创建：`config/openfde-ai-server.example.json`

- [ ] 以可注入命令 runner 的方式实现 `QueueStore`、`discover_issues`、`build_worker_prompt`、`run_worker`、`scan`、`worker` 和 `status`。
- [ ] worker 命令为 `pi --no-session --skill <项目 skill 目录> -p <提示词>`；在 `data/logs/` 记录 stdout/stderr 并执行超时限制。
- [ ] 运行聚焦测试；预期通过。

### 任务 3：部署资源和文档

**文件：**
- 创建：`deploy/systemd/openfde-ai-scan.service`
- 创建：`deploy/systemd/openfde-ai-scan.timer`
- 创建：`deploy/systemd/openfde-ai.env.example`
- 创建：`docs/openfde-pi-server-deployment.md`

- [ ] 添加非 root service、`flock`、systemd 沙箱、相对部署路径、timer 周期和安装/回滚步骤。
- [ ] 记录先以 `dry_run` 部署，再显式启用 worker 执行的步骤。

### 任务 4：移除过时兼容 skill

**文件：**
- 删除：旧 `openfde_workflow.py` 产物工具；分析统一由 Pi 技能执行
- 删除：`skills/legacy/`
- 修改：`profiles/openfde/profile.json`、`tests/test_openfde_workflow.py` 以及引用兼容路径的文档

- [ ] 删除过时的产物工具配置和全部引用；服务器仅调用 Pi 的 `run-issue-workflow` 技能。
- [ ] 删除精确的 legacy 目录。

### 任务 5：验证

- [ ] 运行 `python3 -m unittest tests/test_openfde_workflow.py tests/test_openfde_ai_server.py -v`。
- [ ] 运行 `python3 -m py_compile automation/openfde_ai_server.py`。
- [ ] 校验全部 Pi 链接可解析且 `skills/legacy` 不存在。
