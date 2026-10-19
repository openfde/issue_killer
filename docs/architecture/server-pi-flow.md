# Server、Pi 与 Skills 执行流程

```mermaid
flowchart TD
    A[Docker 扫描循环或 systemd timer] --> B[automation/openfde_ai_server.py scan]
    C[CLI: analyze --issue N] --> D[gh issue view N]
    D --> E[SQLite 入队指定 issue]
    B --> F[gh issue list: 发现 open issue]
    F --> G[SQLite: 新 issue 入队 / 已更新 issue 新 revision 入队]
    G --> H[领取一个 queued issue]
    E --> H

    H --> I{worker.execute 或 --execute?}
    I -- 否 --> J[保留 queued，等待下次扫描]
    I -- 是 --> K[process_claim: 最多 max_atomic_steps_per_issue 次]

    K --> L[启动 Pi 无会话]
    L --> M[pi --no-session --skill run-issue-workflow]
    M --> N[受信任提示词：仅当前 issue、只读源码、评论须经发布门槛、禁止构建]
    N --> O[初始化或读取 .fde-ai/issues/N/state.json]
    O --> P[恰好执行一个原子 skill]

    P --> P1[load profile / build context]
    P --> P2[fetch issue → 提取证据]
    P --> P3[解析 manifest → 只读源码缓存]
    P --> P4[源码追溯 → 分析校验 → 修复方案]
    P --> P5[可选 patch → patch 校验 → 评论草稿 → 归档]
    P --> P6[request-build → 受控构建 → collect-build-artifacts]

    P1 --> Q[Pi 退出；协调器保存 data/logs worker 输出]
    P2 --> Q
    P3 --> Q
    P4 --> Q
    P5 --> Q
    P6 --> Q

    Q --> R[协调器读取 state.json 的 state]
    R --> S{终态?}
    S -- archived / needs_information / blocked --> T[SQLite: completed]
    S -- build_requested / build_failed / component_review_requested --> U2[SQLite: queued，不启动 worker，等待人工动作]
    S -- 中间状态且未到上限 --> K
    S -- 到步骤上限 --> U[SQLite: queued，下一扫描继续]
    R -- state 缺失 / 非法 --> V[SQLite: retry 或 failed]
    R -- 原子步未推进状态 --> V2[SQLite: no progress，重试或 failed]

    T --> W[工件保留于 .fde-ai/issues/N]
    U --> W
    U2 --> W
    V2 --> W
    V --> W
```

## 关键约束

- `run-issue-workflow` 每次 Pi 调用只允许推进一个原子 skill；连续推进由协调器的 `process_claim` 循环负责。
- SQLite 只管理队列、revision、重试和 worker 日志路径；事实、证据和 patch 不在 SQLite，全部在 issue 工件目录。
- `state.json` 只能使用字段 `state`；`archived`、`needs_information`、`blocked` 才能使队列项完成。`build_requested`、`build_failed` 与 `component_review_requested` 是等待态：协调器只入队等待人工动作（构建或组件确认），不启动 worker。
- 同一状态连续出现两次视为无进展：协调器按失败重试计数，避免空转烧满步骤上限。
- patch 唯一位置是 `.fde-ai/issues/<issue号>/patch/0001-<名称>.patch`，未构建前永久是未应用、未测试的建议；构建只可经 profile `build.helper` 授权的助手执行，构建后必须回滚补丁。
- Docker 扫描循环与 systemd timer 都调用 `scan`；`worker.execute=true` 才会进入 Pi 循环。
