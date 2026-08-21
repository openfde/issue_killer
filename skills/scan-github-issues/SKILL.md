---
name: scan-github-issues
description: 当定时或批量 worker 需要发现并排队已配置的 GitHub issue，以进行受限且受策略控制的分析时使用。
---

# 扫描 GitHub issue

加载 profile，检查紧急停用文件并运行 `list-github-issues`。按 issue 编号与最新快照/评论游标去重，执行配置的 run/并发预算，再将符合条件的 revision 入队。每个入队项都通过 `run-issue-workflow` 调度，不得绕过其产物门槛。

仅当 profile 启用且全部门槛通过时，才通过 `publish-policy-comment` 发布。认证失败、停用文件存在、预算耗尽或队列锁竞争时停止。不得修改源码、运行验证命令、推送或创建 pull request。
