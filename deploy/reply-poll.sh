#!/bin/bash
# 等待态回复轮询（默认 3 分钟）：
#   - 扫描处于 awaiting_direction / awaiting_verification 的 issue；
#   - 仅当 GitHub 评论数增加时才调用 sync-github-replies 技能（空闲不消耗模型调用）。
# 用法：从已加载环境变量（GH_TOKEN 等）的登录 shell 启动：
#   cd ~/fde-ai-assistant && nohup bash deploy/reply-poll.sh >>/dev/null 2>&1 &
set -u
cd "$(dirname "$0")/.."

INTERVAL="${REPLY_POLL_SECONDS:-$(python3 -c "import json;print(json.load(open('profiles/openfde/profile.json')).get('replies',{}).get('poll_seconds',180))" 2>/dev/null || echo 180)}"
REPO="$(python3 -c "import json;print(json.load(open('profiles/openfde/profile.json'))['github']['repository'])" 2>/dev/null)"
LOG=data/logs/reply-poll.log
mkdir -p data/logs
echo "[$(date -u +%FT%TZ)] reply-poll started interval=${INTERVAL}s repo=${REPO}" >> "$LOG"

while :; do
    for st in .fde-ai/issues/*/state.json; do
        [ -f "$st" ] || continue
        issue="$(basename "$(dirname "$st")")"
        state="$(python3 -c "import json;print(json.load(open('$st')).get('state',''))" 2>/dev/null)"
        case "$state" in
            awaiting_direction|awaiting_verification) ;;
            *) continue ;;
        esac
        seen_file=".fde-ai/issues/$issue/input/replies-seen.json"
        seen="$(python3 -c "import json;print(json.load(open('$seen_file')).get('last_comment_count',0))" 2>/dev/null || echo 0)"
        current="$(gh api "repos/$REPO/issues/$issue" --jq .comments 2>/dev/null || echo "$seen")"
        if [ "${current:-0}" -gt "${seen:-0}" ] 2>/dev/null; then
            echo "[$(date -u +%FT%TZ)] issue=$issue state=$state new_comments=$((current-seen))" >> "$LOG"
            timeout 1200 pi --no-session --skill "$PWD/skills/sync-github-replies" \
                -p "同步问题 #$issue 的新回复（当前状态 $state），按技能规则继续。" >> "$LOG" 2>&1
        fi
    done
    sleep "$INTERVAL"
done
