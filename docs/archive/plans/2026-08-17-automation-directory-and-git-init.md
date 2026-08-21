# 自动化目录合并与 Git 初始化实施计划

> **归档提示：** 仅供历史参考，不可作为当前操作依据。

> **供自动化执行者使用：** 按任务顺序执行；每个任务完成后运行其验证命令。

**目标：** 初始化当前工作区的 Git 仓库，并将 `server/`、`tools/` 合并为 `automation/`，同时更新全部项目自有引用。

**架构：** `automation/` 是确定性本地程序的唯一目录。Git 仅跟踪项目定义、技能、配置示例、文档和测试；本地源码检出、运行产物、数据和部署专用配置由根 `.gitignore` 排除。

**技术：** Git、Python 标准库、unittest、systemd 单元文件、Pi 技能。

## 全局约束

- 不移动、不删除或重写 `fde-manifests/`、`sources/`、`.fde-ai/`。
- 不修改 OpenFDE 源码、缓存或问题证据。
- 不创建初始提交、不推送、不创建 PR。
- `automation/openfde_ai_server.py` 是迁移后的唯一脚本入口；问题分析只通过 Pi 技能进行。

---

### 任务 1：初始化 Git 边界

**文件：**

- 创建：`.gitignore`
- 创建：`.git/`（由 `git init` 生成）

**产出：** 根工作区成为 Git 仓库；本地检出、产物、数据、Python 缓存和部署专用配置均不进入未跟踪列表。

- [ ] 创建 `.gitignore`，内容为：

  ```gitignore
  sources/
  fde-manifests/
  .fde-ai/
  data/
  config/openfde-ai-server.json
  __pycache__/
  *.py[cod]
  ```

- [ ] 在根目录运行：

  ```sh
  git init
  ```

- [ ] 验证忽略规则：

  ```sh
  git check-ignore -v sources .fde-ai server/__pycache__ config/openfde-ai-server.json
  git status --short
  ```

  预期：前一命令对四个目标均显示 `.gitignore` 规则；`sources/`、`.fde-ai/` 和 Python 缓存不出现在状态输出中。

### 任务 2：迁移自动化脚本与引用

**文件：**

- 创建：`automation/openfde_ai_server.py`（来自 `server/openfde_ai_server.py`）
- 删除：`tools/openfde_workflow.py`（旧产物工具）
- 修改：`profiles/openfde/profile.json`
- 修改：`deploy/systemd/openfde-ai-scan.service`
- 修改：`docs/**/*.md`、`tests/*.py` 中的路径引用
- 删除：已空的 `server/`、`tools/`

**产出：** 所有项目自有入口、配置和测试只使用 `automation/` 路径。

- [ ] 先在测试中将旧脚本路径断言改为不存在，并增加断言：`server/`、`tools/` 不再存在，`automation/` 只包含服务器协调器。
- [ ] 运行迁移相关测试，预期因脚本尚未移动而失败：

  ```sh
  python3 -m unittest tests.test_openfde_workflow tests.test_openfde_ai_server -v
  ```

- [ ] 创建 `automation/`，仅移动服务器协调器；删除旧产物工具，并更新项目配置、systemd 服务、文档、测试与代码字符串。
- [ ] 删除已空目录及其中的 Python 缓存。
- [ ] 验证无旧路径引用：

  ```sh
  ! rg -n 'server/openfde_ai_server\.py|tools/openfde_workflow\.py|automation/openfde_workflow\.py' \
    AGENTS.md config deploy docs profiles skills tests automation
  ```

### 任务 3：验证迁移结果

**文件：** 无新增文件。

**产出：** Git 边界、脚本入口和测试均有效。

- [ ] 运行完整测试：

  ```sh
  python3 -m unittest tests/test_openfde_workflow.py tests/test_openfde_ai_server.py -v
  ```

- [ ] 运行编译检查：

  ```sh
  python3 -m py_compile automation/openfde_ai_server.py
  ```

- [ ] 核验新的 CLI 入口：

  ```sh
  python3 automation/openfde_ai_server.py --help
  ```

- [ ] 检查状态，确认本地数据未被列为待提交文件：

  ```sh
  git status --short
  ```
