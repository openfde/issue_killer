#!/bin/bash
# 最简 issue 自动整理（单次扫描）：
#   - 由 reply-poll.sh 每轮调用一次（默认 3 分钟节奏）；
#   - 只处理基线之后**新建**的 issue：正文很短、含附件链接、无 openfde-ai:intake marker；
#   - 调用 enrich-issue-intake 技能把标题/正文整理为标准取证格式（保留原始描述）。
# 可由 profile publication.issue_enrichment=manual 关闭自动整理。
set -u
cd "$(dirname "$0")/.."

REPO="$(python3 -c "import json;print(json.load(open('profiles/openfde/profile.json'))['github']['repository'])" 2>/dev/null)"
STATE=data/intake/watch-state.json
LOG=data/logs/intake-watch.log
mkdir -p data/intake data/logs

enabled="$(python3 -c "import json;print(json.load(open('profiles/openfde/profile.json')).get('publication',{}).get('issue_enrichment','auto'))" 2>/dev/null)"
[ "$enabled" = "auto" ] || exit 0

if [ ! -f "$STATE" ]; then
    now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '{"schema_version": 1, "last_created_at": "%s", "baseline": true}\n' "$now" > "$STATE"
    echo "[$now] intake-watch baseline (no old issues processed)" >> "$LOG"
    exit 0
fi

gh api "repos/$REPO/issues?state=open&sort=created&direction=desc&per_page=20" > /tmp/intake-issues.json 2>/dev/null || exit 0

cands="$(python3 - "$STATE" <<'PY'
import json, sys
state = json.load(open(sys.argv[1]))
last = state.get("last_created_at", "")
data = json.load(open("/tmp/intake-issues.json"))
blocked = {"no-ai-reply"}
for issue in sorted(data, key=lambda x: x["created_at"]):
    if issue.get("pull_request"):
        continue
    body = issue.get("body") or ""
    if issue["created_at"] <= last:
        continue
    if len(body) >= 600:
        continue
    if "user-attachments" not in body:
        continue
    if "openfde-ai:intake" in body:
        continue
    if any(label.get("name") in blocked for label in (issue.get("labels") or [])):
        continue
    print(f"{issue['number']}\t{issue['created_at']}")
PY
)"

[ -z "$cands" ] && exit 0

while IFS=$'\t' read -r num created; do
    [ -z "$num" ] && continue
    echo "[$(date -u +%FT%TZ)] enrich issue #$num (created $created)" >> "$LOG"
    timeout 1200 pi --no-session --skill "$PWD/skills/enrich-issue-intake" \
        -p "整理问题 #$num 为标准取证 issue 格式（最简 issue 自动整理；保留原始描述与附件；发生时间只能是范围时按范围记录）。" >> "$LOG" 2>&1
    python3 - "$STATE" "$created" <<'PY'
import json, sys
path, created = sys.argv[1], sys.argv[2]
state = json.load(open(path))
state["last_created_at"] = created
state.pop("baseline", None)
json.dump(state, open(path, "w"), ensure_ascii=False, indent=1)
PY
done <<< "$cands"
