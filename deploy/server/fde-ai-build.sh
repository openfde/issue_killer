#!/bin/bash
# 受控构建助手（仅在 aosp17-ai 容器内运行）：
#   校验请求与锁 → 在受控构建树内临时应用 issue patch → 模块增量构建
#   → 记录产物哈希 → 回滚 patch → 更新 build/build-result.json 与 state.json
#
# 用法: deploy/server/fde-ai-build.sh --issue <issue_number>
# 约定:
#   - 构建树（profile build.tree）必须干净且 HEAD 等于请求的 base_commit。
#   - 与整体构建互斥：data/build.lock 与 <tree>/out/.siso_lock 任一被占用即退出 75（不改变状态）。
#   - 任何情况下都会在退出前回滚补丁。
set -uo pipefail

usage() { echo "usage: fde-ai-build.sh --issue <issue_number>" >&2; exit 2; }

ISSUE=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --issue) [ "$#" -ge 2 ] || usage; ISSUE="$2"; shift 2 ;;
        *) usage ;;
    esac
done
[ -n "$ISSUE" ] || usage

WORKSPACE="${WORKSPACE:-/workspace}"
ISSUE_DIR="$WORKSPACE/.fde-ai/issues/$ISSUE"
REQUEST="$ISSUE_DIR/build/build-request.json"
STATE="$ISSUE_DIR/state.json"
RESULT="$ISSUE_DIR/build/build-result.json"
LOG_DIR="$WORKSPACE/data/logs"
LOG="$LOG_DIR/build-issue-$ISSUE-$(date +%Y%m%d-%H%M%S).log"
LOCK_FILE="$WORKSPACE/data/build.lock"

mkdir -p "$LOG_DIR" "$ISSUE_DIR/build"
[ -f "$REQUEST" ] || { echo "缺少 $REQUEST：请先完成 request-build 步骤" >&2; exit 2; }
[ -f "$STATE" ] || { echo "缺少 $STATE" >&2; exit 2; }
: > "$LOG"

note() { echo "[fde-ai-build] $*" | tee -a "$LOG"; }
busy() { note "忙碌: $*"; exit 75; }

STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
FINISHED=""
ARTIFACT_JSON="[]"

write_result() {
    python3 - "$REQUEST" "$RESULT" "$STATE" "$LOG" "$1" "$2" "$STARTED" "$FINISHED" "${ARTIFACT_JSON:-[]}" <<'PY'
import json, os, sys
request_path, result_path, state_path, log, status, message, started, finished, artifacts_json = sys.argv[1:10]
request = json.load(open(request_path, encoding="utf-8"))
result = {
    "status": status,
    "message": message,
    "issue": request.get("issue"),
    "revision": request.get("revision"),
    "tree": request.get("tree"),
    "output": request.get("output", "out"),
    "target": request.get("target"),
    "modules": request.get("modules", []),
    "base_commit": request.get("base_commit"),
    "patch": request.get("patch"),
    "patch_sha256": request.get("patch_sha256"),
    "helper": request.get("helper"),
    "mode": request.get("mode"),
    "started_at": started,
    "finished_at": finished,
    "log": log,
    "artifacts": json.loads(artifacts_json.strip() or "[]"),
}
with open(result_path + ".tmp", "w", encoding="utf-8") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
os.replace(result_path + ".tmp", result_path)
state = json.load(open(state_path, encoding="utf-8"))
state["state"] = "build_done" if status == "done" else "build_failed"
state["updated_at"] = finished
state["build_result"] = "build/build-result.json"
with open(state_path + ".tmp", "w", encoding="utf-8") as handle:
    json.dump(state, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
os.replace(state_path + ".tmp", state_path)
PY
}

finish() { FINISHED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; write_result "$1" "$2"; }
fail() { note "失败: $*"; finish failed "$*"; exit 1; }

eval "$(python3 - "$REQUEST" <<'PY'
import json, shlex, sys
request = json.load(open(sys.argv[1], encoding="utf-8"))
for key in ("tree", "target", "patch", "patch_sha256", "base_commit", "output", "helper", "mode"):
    print("%s=%s" % (key.upper(), shlex.quote(str(request.get(key) or ""))))
print("JOBS=%s" % shlex.quote(str(request.get("max_jobs") or 12)))
print("MODULES=%s" % shlex.quote(" ".join(request.get("modules") or [])))
print("ARTIFACT_PATHS=%s" % shlex.quote("\n".join(request.get("artifacts") or [])))
PY
)"

[ -n "$TREE" ] || fail "build-request.json 缺少 tree"
[ -n "$TARGET" ] || fail "build-request.json 缺少 target"
[ -n "$PATCH" ] || fail "build-request.json 缺少 patch"
[ -n "$MODULES" ] || fail "build-request.json 缺少 modules"
OUTPUT="${OUTPUT:-out}"

exec 9>"$LOCK_FILE"
flock -n 9 || busy "另一个受控构建正在进行（$LOCK_FILE）"

SISO_LOCK="$WORKSPACE/$TREE/out/.siso_lock"
if [ -f "$SISO_LOCK" ] && ! flock -n "$SISO_LOCK" true 2>/dev/null; then
    busy "整体构建正在运行（.siso_lock 被占用），请稍后重试"
fi

TREE_DIR="$WORKSPACE/$TREE"
[ -d "$TREE_DIR/.git" ] || fail "构建树不存在: $TREE_DIR"
[ -z "$(git -C "$TREE_DIR" status --porcelain)" ] || fail "构建树不干净，拒绝构建"
if [ -n "$BASE_COMMIT" ]; then
    HEAD_COMMIT="$(git -C "$TREE_DIR" rev-parse HEAD)"
    [ "$HEAD_COMMIT" = "$BASE_COMMIT" ] || fail "base commit 不匹配: HEAD=$HEAD_COMMIT 期望=$BASE_COMMIT"
fi

PATCH_ABS="$ISSUE_DIR/$PATCH"
[ -f "$PATCH_ABS" ] || fail "patch 不存在: $PATCH_ABS"
if [ -n "$PATCH_SHA" ]; then
    ACTUAL_SHA="$(sha256sum "$PATCH_ABS" | awk '{print $1}')"
    [ "$ACTUAL_SHA" = "$PATCH_SHA" ] || fail "patch SHA-256 不匹配"
fi
PATCH_PATHS="$(git -C "$TREE_DIR" apply --numstat "$PATCH_ABS" 2>/dev/null | awk '{print $3}')"
[ -n "$PATCH_PATHS" ] || fail "patch 无法解析（git apply --numstat 无输出）"

REVERTED=0
revert_patch() {
    [ "$REVERTED" -eq 1 ] && return 0
    REVERTED=1
    if git -C "$TREE_DIR" apply -R "$PATCH_ABS" 2>>"$LOG"; then
        note "已回滚 patch"
    else
        for path in $PATCH_PATHS; do
            git -C "$TREE_DIR" checkout -- "$path" 2>>"$LOG" || true
        done
        note "git apply -R 失败，已按文件回滚"
    fi
}
trap revert_patch EXIT

note "临时应用 patch: $PATCH_ABS"
git -C "$TREE_DIR" apply "$PATCH_ABS" >>"$LOG" 2>&1 || fail "git apply 失败"

cd "$TREE_DIR" || fail "无法进入 $TREE_DIR"
set +u
export OUT_DIR="$OUTPUT"
source build/envsetup.sh >/dev/null 2>&1
lunch "$TARGET" >>"$LOG" 2>&1 || { set -u; fail "lunch $TARGET 失败"; }
set -u

note "执行: make -j$JOBS $MODULES"
make -j"$JOBS" $MODULES >>"$LOG" 2>&1
BUILD_RC=$?
[ "$BUILD_RC" -eq 0 ] || fail "构建失败（make 退出码 $BUILD_RC），日志: $LOG"

note "构建成功，收集产物"
OUTPUT_DIR="$TREE_DIR/$OUTPUT"
ARTIFACT_JSON="$(python3 - "$OUTPUT_DIR" "$ARTIFACT_PATHS" <<'PY'
import hashlib, json, os, sys
output_dir, raw = sys.argv[1:3]
items = []
for rel in raw.splitlines():
    rel = rel.strip()
    if not rel:
        continue
    path = os.path.join(output_dir, rel)
    if not os.path.isfile(path):
        print("missing artifact: " + rel, file=sys.stderr)
        sys.exit(3)
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    items.append({"name": os.path.basename(rel), "out_relative": rel, "path": path, "size": os.path.getsize(path), "sha256": digest.hexdigest()})
print(json.dumps(items, ensure_ascii=False))
PY
)" || fail "产物收集失败（见 $LOG）"

finish done "构建成功"
note "完成，构建结果: $RESULT"
exit 0
