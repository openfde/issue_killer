---
name: extract-log-evidence
description: 当已获取 issue 包含 bugreport、tombstone、ANR、压缩包或结构化诊断日志附件，需要受限提取证据时使用。
---

# 提取结构化日志证据

仅接收带有结构化日志附件的 `issue_fetched`。通过 profile 批准的路径安全下载，执行压缩包、文件数和大小限制，只写入 `.fde-ai/issues/<issue号>/input/attachments/` 的原始附件与 `evidence/` 的受限摘录和 `evidence.json`。每项都需要来源附件、字节或行范围、SHA-256 和提取规则。不得在 `.fde-ai/runs/` 创建新产物。

校验公共证据 schema 并推进到 `evidence_extracted`。压缩包不安全、哈希缺失或没有技术证据时停止。同一 revision 不得同时运行本 skill 和正文证据 skill；不得诊断根因。
