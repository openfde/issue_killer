#!/bin/bash
# 手动整理最简 issue 为标准取证格式（调用方显式指定编号，无自动扫描）。
# 用法（从已加载 GH_TOKEN/模型环境的登录 shell 执行）:
#   bash deploy/enrich-issue.sh <issue_number>
set -u
cd "$(dirname "$0")/.."

ISSUE="${1:-}"
[ -n "$ISSUE" ] || { echo "usage: bash deploy/enrich-issue.sh <issue_number>" >&2; exit 2; }

mkdir -p data/logs
LOG="data/logs/enrich-issue-$ISSUE.log"
echo "[$(date -u +%FT%TZ)] enrich issue #$ISSUE" | tee -a "$LOG"
timeout 1200 pi --no-session --skill "$PWD/skills/enrich-issue-intake" \
    -p "整理问题 #$ISSUE 为标准取证 issue 格式（调用方显式指定；保留原始描述；有 bugreport 走标准取证格式；无 bugreport 时基于文字与截图做初步分析并标注未验证）。" 2>&1 | tee -a "$LOG"
