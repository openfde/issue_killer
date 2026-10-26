#!/bin/bash
set -euo pipefail

usage() {
    cat >&2 <<'EOF'
usage: build-install.sh [options]

  --issue <n>             issue number; without --module/--pr/--branch it uses
                          the issue's latest PR and matching module(s)
  --module <name>         repeatable/comma-separated module(s) from modules.json
  --pr <n>                explicit PR (all modules must use the same repository)
  --latest-pr             use the latest PR for --issue (default for issue)
  --no-pr                 do not apply a PR
  --branch <name>         build a named branch (no PR); restored after build
  --keep-branch           do not restore the original branch
  --jobs <auto|n>         default auto: module jobs from map, capped by host nproc
  --target <lunch>        default fde_arm64-cp2a-user
  --product <name>        default fde_arm64
  --host <host>           default 10.31.62.29
  --tree <path>           default /aosp4/hy_fde17
  --no-install            build/fetch only
  --no-start              install but do not start OpenFDE
  --install-only          install an existing artifact; skip build
  --artifact <path>       local artifact for --install-only
  --wait-seconds <n>      remote build wait budget (default FDE_BUILD_WAIT_SECONDS=3600)
  --poll-seconds <n>      remote build poll interval (default FDE_BUILD_POLL_SECONDS=5)
  -h, --help
EOF
    exit 2
}

ISSUE=""
MODULES=()
PR=""
PR_MODE=""
BRANCH=""
KEEP_BRANCH=0
INSTALL=1
START=1
INSTALL_ONLY=0
ARTIFACT_OVERRIDE=""
BUILD_WAIT_SECONDS="${FDE_BUILD_WAIT_SECONDS:-3600}"
BUILD_POLL_SECONDS="${FDE_BUILD_POLL_SECONDS:-5}"
TARGET="${FDE_BUILD_TARGET:-fde_arm64-cp2a-user}"
JOBS="${FDE_BUILD_JOBS:-auto}"
PRODUCT="${FDE_BUILD_PRODUCT:-fde_arm64}"
HOST="${FDE_BUILD_HOST:-10.31.62.29}"
TREE="${FDE_BUILD_TREE:-/aosp4/hy_fde17}"
SSH_KEY="${FDE_SSH_KEY:-/workspace/data/ssh/id_ed25519}"
KNOWN_HOSTS="${FDE_KNOWN_HOSTS:-/workspace/data/ssh/known_hosts}"
MODULE_MAP="${FDE_MODULE_MAP:-/workspace/deploy/assist/modules.json}"
INSTALL_SCRIPT="${FDE_INSTALL_SCRIPT:-/workspace/deploy/install/fde-install.sh}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_BUILD_SOURCE="$SCRIPT_DIR/build-remote.sh"
REMOTE_USER="${FDE_BUILD_USER:-huyang}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --issue) [ "$#" -ge 2 ] || usage; ISSUE="$2"; shift 2 ;;
        --module)
            [ "$#" -ge 2 ] || usage
            IFS=',' read -ra _mods <<< "$2"
            for _m in "${_mods[@]}"; do [ -n "$_m" ] && MODULES+=("$_m"); done
            shift 2
            ;;
        --pr) [ "$#" -ge 2 ] || usage; PR="$2"; PR_MODE="explicit"; shift 2 ;;
        --latest-pr) PR_MODE="latest"; shift ;;
        --no-pr) PR_MODE="none"; shift ;;
        --branch) [ "$#" -ge 2 ] || usage; BRANCH="$2"; PR_MODE="none"; shift 2 ;;
        --keep-branch) KEEP_BRANCH=1; shift ;;
        --jobs) [ "$#" -ge 2 ] || usage; JOBS="$2"; shift 2 ;;
        --target) [ "$#" -ge 2 ] || usage; TARGET="$2"; shift 2 ;;
        --product) [ "$#" -ge 2 ] || usage; PRODUCT="$2"; shift 2 ;;
        --host) [ "$#" -ge 2 ] || usage; HOST="$2"; shift 2 ;;
        --tree) [ "$#" -ge 2 ] || usage; TREE="$2"; shift 2 ;;
        --no-install) INSTALL=0; shift ;;
        --no-start) START=0; shift ;;
        --install-only) INSTALL_ONLY=1; shift ;;
        --artifact) [ "$#" -ge 2 ] || usage; ARTIFACT_OVERRIDE="$2"; shift 2 ;;
        --wait-seconds) [ "$#" -ge 2 ] || usage; BUILD_WAIT_SECONDS="$2"; shift 2 ;;
        --poll-seconds) [ "$#" -ge 2 ] || usage; BUILD_POLL_SECONDS="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) usage ;;
    esac
done

case "$BUILD_WAIT_SECONDS" in
    ''|*[!0-9]*) echo "--wait-seconds must be a positive integer" >&2; exit 2 ;;
esac
case "$BUILD_POLL_SECONDS" in
    ''|*[!0-9]*) echo "--poll-seconds must be a positive integer" >&2; exit 2 ;;
esac
[ "$BUILD_WAIT_SECONDS" -gt 0 ] || { echo "--wait-seconds must be greater than 0" >&2; exit 2; }
[ "$BUILD_POLL_SECONDS" -gt 0 ] || { echo "--poll-seconds must be greater than 0" >&2; exit 2; }
if [ "$INSTALL_ONLY" -eq 1 ]; then
    [ "$INSTALL" -eq 1 ] || { echo "--install-only cannot be combined with --no-install" >&2; exit 2; }
    [ -z "$PR" ] || { echo "--install-only cannot be combined with --pr" >&2; exit 2; }
    [ -z "$BRANCH" ] || { echo "--install-only cannot be combined with --branch" >&2; exit 2; }
elif [ -n "$ARTIFACT_OVERRIDE" ]; then
    echo "--artifact requires --install-only" >&2
    exit 2
fi

[ -f "$MODULE_MAP" ] || { echo "module map not found: $MODULE_MAP" >&2; exit 2; }
[ -f "$REMOTE_BUILD_SOURCE" ] || { echo "remote build script not found: $REMOTE_BUILD_SOURCE" >&2; exit 2; }

STATE="/workspace/.fde-ai/issues/${ISSUE}/state.json"

if [ -z "$PR_MODE" ]; then
    if [ -n "$PR" ]; then
        PR_MODE="explicit"
    elif [ -n "$BRANCH" ]; then
        PR_MODE="none"
    elif [ -n "$ISSUE" ]; then
        PR_MODE="latest"
    else
        PR_MODE="none"
    fi
fi
if [ "$PR_MODE" = "explicit" ] && [ -z "$PR" ]; then
    usage
fi
if [ "$PR_MODE" = "explicit" ] && [ -n "$BRANCH" ]; then
    echo "--pr and --branch are mutually exclusive" >&2
    exit 2
fi

if [ ${#MODULES[@]} -eq 0 ]; then
    [ -n "$ISSUE" ] && [ -f "$STATE" ] || {
        echo "no --module and no issue state to infer modules from" >&2
        exit 2
    }
    mapfile -t MODULES < <(python3 - "$MODULE_MAP" "$STATE" <<'PY'
import json
import re
import sys

map_path, state_path = sys.argv[1:3]
with open(map_path, encoding="utf-8") as handle:
    modules = json.load(handle)
with open(state_path, encoding="utf-8") as handle:
    state = json.load(handle)
pr = state.get("pull_request") or {}
repo = pr.get("repo") or ""
url = pr.get("url") or ""
if not repo and url:
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/", url)
    if match:
        repo = match.group(1)
for name, entry in modules.items():
    if entry.get("repository") == repo:
        print(name)
PY
    )
fi
if [ ${#MODULES[@]} -eq 0 ]; then
    echo "could not infer modules; pass --module" >&2
    exit 2
fi

mapfile -t MODULE_ROWS < <(python3 - "$MODULE_MAP" "${MODULES[@]}" <<'PY'
import json
import sys

map_path = sys.argv[1]
names = sys.argv[2:]
with open(map_path, encoding="utf-8") as handle:
    modules = json.load(handle)
for name in names:
    entry = modules.get(name)
    actual = name
    if not isinstance(entry, dict):
        matches = [key for key, value in modules.items() if name in (value.get("aliases") or [])]
        if len(matches) != 1:
            raise SystemExit("module not found in map: %s" % name)
        actual = matches[0]
        entry = modules[actual]
    fields = ["project", "repository", "artifact", "image", "dest"]
    values = []
    for field in fields:
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            raise SystemExit("module %s missing %s" % (actual, field))
        values.append(value)
    values.append(str(entry.get("kind") or ""))
    values.append(str(entry.get("jobs") or 0))
    print("|".join([actual] + values))
PY
)
if [ ${#MODULE_ROWS[@]} -eq 0 ]; then
    echo "module map returned no rows" >&2
    exit 2
fi

declare -a M_NAME M_PROJECT M_REPO M_ART M_IMAGE M_DEST M_KIND M_MAPJOBS
for row in "${MODULE_ROWS[@]}"; do
    IFS='|' read -r name project repo artifact image dest kind mapjobs <<< "$row"
    M_NAME+=("$name"); M_PROJECT+=("$project"); M_REPO+=("$repo")
    M_ART+=("$artifact"); M_IMAGE+=("$image"); M_DEST+=("$dest")
    M_KIND+=("$kind"); M_MAPJOBS+=("$mapjobs")
done

declare -A PR_BY_REPO=()
declare -A BRANCH_ORIG=()

STAMP="$(date +%Y%m%d-%H%M%S)"
TAG="${ISSUE:-local}"
WORK="${FDE_WORK_ROOT:-/workspace/data/assist/work}/${TAG}-${STAMP}"
mkdir -p "$WORK"
RESULT_ROWS="$WORK/results.tsv"
: > "$RESULT_ROWS"
RESULT_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ISSUE_DIR=""
BUILD_RESULT=""
INSTALL_RESULT=""
INSTALL_LOG=""
if [ -n "$ISSUE" ] && [ -d "/workspace/.fde-ai/issues/$ISSUE" ]; then
    ISSUE_DIR="/workspace/.fde-ai/issues/$ISSUE"
    mkdir -p "$ISSUE_DIR/build" "$ISSUE_DIR/install"
    BUILD_RESULT="$ISSUE_DIR/build/build-result.json"
    INSTALL_RESULT="$ISSUE_DIR/install/install-result.json"
    INSTALL_LOG="$ISSUE_DIR/install/install.log"
fi

write_build_result() {
    local status="$1" stage="$2" code="${3:-}" reason="${4:-}"
    [ -n "$ISSUE_DIR" ] || return 0
    RESULT_STATUS="$status" RESULT_STAGE="$stage" RESULT_CODE="$code" RESULT_REASON="$reason" \
    RESULT_ISSUE="$ISSUE" RESULT_PR="${RESULT_PR_OVERRIDE:-$PR}" RESULT_TREE="$TREE" RESULT_STARTED_AT="$RESULT_STARTED_AT" \
    RESULT_ROWS="$RESULT_ROWS" python3 - "$BUILD_RESULT" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

rows = []
path = os.environ.get("RESULT_ROWS", "")
if path and os.path.exists(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                continue
            module, artifact, sha, remote_log, image, dest = fields
            rows.append({
                "module": module,
                "artifact": artifact,
                "sha256": sha,
                "remote_log": remote_log,
                "image": image,
                "dest": dest,
            })
pr = os.environ.get("RESULT_PR", "")
code = os.environ.get("RESULT_CODE", "")
issue = os.environ.get("RESULT_ISSUE", "")
data = {
    "issue": int(issue) if issue.isdigit() else issue or None,
    "status": os.environ.get("RESULT_STATUS", ""),
    "stage": os.environ.get("RESULT_STAGE", ""),
    "exit_code": int(code) if code.isdigit() else None,
    "pr": int(pr) if pr.isdigit() else None,
    "tree": os.environ.get("RESULT_TREE", ""),
    "started_at": os.environ.get("RESULT_STARTED_AT", ""),
    "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "reason": os.environ.get("RESULT_REASON", ""),
    "modules": [row["module"] for row in rows],
    "artifacts": rows,
}
if len(rows) == 1:
    data.update({
        "module": rows[0]["module"],
        "artifact": rows[0]["artifact"],
        "artifact_sha256": rows[0]["sha256"],
        "remote_log": rows[0]["remote_log"],
    })
target = sys.argv[1]
tmp = target + ".tmp"
with open(tmp, "w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
os.replace(tmp, target)
PY
}

write_install_result() {
    local status="$1" code="${2:-}" reason="${3:-}"
    [ -n "$ISSUE_DIR" ] || return 0
    RESULT_STATUS="$status" RESULT_CODE="$code" RESULT_REASON="$reason" RESULT_TAG="$TAG" \
    RESULT_ISSUE="$ISSUE" RESULT_STARTED_AT="$RESULT_STARTED_AT" RESULT_ROWS="$RESULT_ROWS" RESULT_LOG="$INSTALL_LOG" \
    RESULT_HOST="${FDE_INSTALL_HOST:-10.31.62.247}" python3 - "$INSTALL_RESULT" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

rows = []
path = os.environ.get("RESULT_ROWS", "")
if path and os.path.exists(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 6:
                continue
            module, source, sha, remote_log, image, dest = fields
            rows.append({
                "module": module,
                "source": source,
                "artifact": "/home/huyang/fde-artifacts/%s/%s" % (os.environ.get("RESULT_TAG", ""), os.path.basename(source)),
                "sha256": sha,
                "dest": dest,
            })
code = os.environ.get("RESULT_CODE", "")
issue = os.environ.get("RESULT_ISSUE", "")
data = {
    "issue": int(issue) if issue.isdigit() else issue or None,
    "status": os.environ.get("RESULT_STATUS", ""),
    "exit_code": int(code) if code.isdigit() else None,
    "host": os.environ.get("RESULT_HOST", ""),
    "started_at": os.environ.get("RESULT_STARTED_AT", ""),
    "completed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "reason": os.environ.get("RESULT_REASON", ""),
    "log": os.environ.get("RESULT_LOG", ""),
    "modules": [row["module"] for row in rows],
    "artifacts": rows,
}
target = sys.argv[1]
tmp = target + ".tmp"
with open(tmp, "w", encoding="utf-8") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
os.replace(tmp, target)
PY
}

install_existing_artifact() {
    local name="$1" source="$2" image="$3" dest="$4"
    [ -f "$source" ] || { echo "artifact not found: $source" >&2; return 2; }
    local sha remote_artifact manifest rc
    sha="$(sha256sum "$source" | awk '{print $1}')"
    remote_artifact="/home/huyang/fde-artifacts/${TAG}/$(basename "$source")"
    manifest="$WORK/manifest-${name}.json"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$source" "$sha" "-" "$image" "$dest" >> "$RESULT_ROWS"
    python3 - "$manifest" "$name" "$source" "$remote_artifact" "$image" "$dest" <<'PY'
import json
import sys
manifest, module, source, artifact, image, dest = sys.argv[1:7]
with open(manifest, "w", encoding="utf-8") as handle:
    json.dump({
        "module": module,
        "source": source,
        "artifact": artifact,
        "image": image,
        "dest": dest,
    }, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
    write_install_result running
    set +e
    if [ -n "$INSTALL_LOG" ]; then
        "$INSTALL_SCRIPT" --manifest "$manifest" --no-start 2>&1 | tee -a "$INSTALL_LOG"
        rc=${PIPESTATUS[0]}
    else
        "$INSTALL_SCRIPT" --manifest "$manifest" --no-start
        rc=$?
    fi
    set -e
    if [ "$rc" -ne 0 ]; then
        write_install_result failed "$rc" "install failed for $name; log: $INSTALL_LOG"
        return "$rc"
    fi
    if [ "$START" -eq 1 ]; then
        set +e
        if [ -n "$INSTALL_LOG" ]; then
            "$INSTALL_SCRIPT" --start-only 2>&1 | tee -a "$INSTALL_LOG"
            rc=${PIPESTATUS[0]}
        else
            "$INSTALL_SCRIPT" --start-only
            rc=$?
        fi
        set -e
        if [ "$rc" -ne 0 ]; then
            write_install_result failed "$rc" "start failed; log: $INSTALL_LOG"
            return "$rc"
        fi
    fi
    write_install_result success 0
    echo "[build] installed $name from $source"
}

if [ "$INSTALL_ONLY" -eq 1 ]; then
    [ ${#M_NAME[@]} -eq 1 ] || { echo "--install-only requires exactly one --module" >&2; exit 2; }
    name="${M_NAME[0]}"
    source="$ARTIFACT_OVERRIDE"
    if [ -z "$source" ] && [ -n "$BUILD_RESULT" ] && [ -f "$BUILD_RESULT" ]; then
        source="$(python3 - "$BUILD_RESULT" "$name" <<'PY'
import json
import sys
path, module = sys.argv[1:3]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
if data.get("module") == module and data.get("artifact"):
    print(data["artifact"])
else:
    for item in data.get("artifacts") or []:
        if item.get("module") == module:
            print(item.get("artifact") or item.get("path") or "")
            break
PY
)"
    fi
    install_existing_artifact "$name" "$source" "${M_IMAGE[0]}" "${M_DEST[0]}"
    exit 0
fi

latest_pr_for_repo() {
    local repo="$1" state_pr="" state_url="" state_num=""
    if [ -f "$STATE" ]; then
        read -r state_pr state_url state_num < <(python3 - "$STATE" "$repo" <<'PY'
import json
import re
import sys
state_path, repo = sys.argv[1:3]
try:
    with open(state_path, encoding="utf-8") as handle:
        state = json.load(handle)
except Exception:
    raise SystemExit(0)
pr = state.get("pull_request") or {}
pr_repo = pr.get("repo") or ""
url = pr.get("url") or ""
if not pr_repo and url:
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/", url)
    if match:
        pr_repo = match.group(1)
number = pr.get("number")
if not number and url:
    match = re.search(r"/pull/(\d+)", url)
    if match:
        number = match.group(1)
if pr_repo == repo and number:
    print(pr_repo, url, number)
PY
        ) || true
    fi
    if [ -n "$state_num" ]; then
        PR_BY_REPO["$repo"]="$state_num"
        echo "[build] latest PR for $repo: #$state_num (issue state)"
        return 0
    fi
    local number
    number="$(gh pr list --repo "$repo" --state all --search "#$ISSUE" --limit 10 --json number,updatedAt \
        --jq 'sort_by(.updatedAt) | reverse | .[0].number' 2>/dev/null || true)"
    if [ -n "$number" ] && [ "$number" != "null" ]; then
        PR_BY_REPO["$repo"]="$number"
        echo "[build] latest PR for $repo: #$number (gh search)"
        return 0
    fi
    return 1
}

if [ "$PR_MODE" = "explicit" ]; then
    unique_repos="$(printf '%s\n' "${M_REPO[@]}" | sort -u)"
    if [ "$(printf '%s\n' "$unique_repos" | wc -l)" -ne 1 ]; then
        echo "--pr requires all modules to use one repository; use --latest-pr, --no-pr or --branch" >&2
        exit 2
    fi
fi

if [ "$PR_MODE" = "latest" ]; then
    for repo in $(printf '%s\n' "${M_REPO[@]}" | sort -u); do
        latest_pr_for_repo "$repo" || {
            echo "no PR found for issue #$ISSUE in $repo; use --pr, --no-pr or --branch" >&2
            exit 2
        }
    done
fi

SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o UserKnownHostsFile="$KNOWN_HOSTS")
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o UserKnownHostsFile="$KNOWN_HOSTS")
REMOTE_TARGET="$REMOTE_USER@$HOST"

NPROC="$("${SSH[@]}" "$REMOTE_TARGET" "nproc 2>/dev/null || echo 8" | tr -dc '0-9')"
[ -n "$NPROC" ] || NPROC=8
write_build_result running build "" ""

restore_branches() {
    [ "$KEEP_BRANCH" -eq 1 ] && return 0
    for project in "${!BRANCH_ORIG[@]}"; do
        "${SSH[@]}" "$REMOTE_TARGET" "git -C '$TREE/$project' checkout '${BRANCH_ORIG[$project]}'" >/dev/null 2>&1 || true
    done
}
trap restore_branches EXIT

if [ -n "$BRANCH" ]; then
    for project in $(printf '%s\n' "${M_PROJECT[@]}" | sort -u); do
        dirty="$("${SSH[@]}" "$REMOTE_TARGET" "git -C '$TREE/$project' status --porcelain")"
        if [ -n "$dirty" ]; then
            echo "dirty worktree: $TREE/$project" >&2
            write_build_result failed build 7 "dirty worktree: $TREE/$project"
            exit 7
        fi
        orig="$("${SSH[@]}" "$REMOTE_TARGET" "git -C '$TREE/$project' branch --show-current")"
        [ -n "$orig" ] || { echo "cannot determine branch: $TREE/$project" >&2; exit 2; }
        BRANCH_ORIG["$project"]="$orig"
        "${SSH[@]}" "$REMOTE_TARGET" "git -C '$TREE/$project' checkout '$BRANCH'"
        echo "[build] $project: $orig -> $BRANCH"
    done
fi

echo "[build] issue=$ISSUE modules=${M_NAME[*]} target=$TARGET jobs=$JOBS product=$PRODUCT"
echo "[build] tree=$TREE work=$WORK"

last_index=$((${#M_NAME[@]} - 1))
for i in "${!M_NAME[@]}"; do
    name="${M_NAME[$i]}"; project="${M_PROJECT[$i]}"; repo="${M_REPO[$i]}"
    artifact_rel="${M_ART[$i]}"; image="${M_IMAGE[$i]}"; dest="${M_DEST[$i]}"
    kind="${M_KIND[$i]}"; mapjobs="${M_MAPJOBS[$i]}"

    if [ "$JOBS" = "auto" ]; then
        jobs="$mapjobs"
        if [ -z "$jobs" ] || [ "$jobs" -le 0 ]; then
            case "$kind" in
                image) jobs=12 ;;
                jar) jobs=8 ;;
                apk) jobs=4 ;;
                native) jobs=4 ;;
                *) jobs=4 ;;
            esac
        fi
        if [ "$jobs" -gt "$NPROC" ]; then jobs="$NPROC"; fi
    else
        jobs="$JOBS"
    fi
    echo "[build] module=$name project=$project jobs=$jobs"

    patch=""
    pr=""
    if [ "$PR_MODE" = "explicit" ]; then
        pr="$PR"
    elif [ "$PR_MODE" = "latest" ]; then
        pr="${PR_BY_REPO[$repo]:-}"
    fi
    if [ -n "$pr" ]; then
        diff="$WORK/pr-${repo//\//_}-${pr}.diff"
        if [ ! -f "$diff" ]; then
            echo "[build] fetching PR #$pr from $repo"
            gh pr diff "$pr" --repo "$repo" > "$diff"
        fi
        remote_patch="/tmp/fde-pr-${TAG}-${name}-${STAMP}.diff"
        "${SCP[@]}" "$diff" "$REMOTE_TARGET:$remote_patch"
        patch="$remote_patch"
    elif [ -n "$BRANCH" ]; then
        echo "[build] no PR; branch $BRANCH"
    else
        echo "[build] no PR; current branch"
    fi

    remote_script="/tmp/fde-build-${TAG}-${name}-${STAMP}.sh"
    remote_log="$TREE/out/assist-build-${TAG}-${name}-${STAMP}.log"
    remote_exit="$TREE/out/assist-build-${TAG}-${name}-${STAMP}.exit"
    remote_pid="$TREE/out/assist-build-${TAG}-${name}-${STAMP}.pid"
    artifact_local="/workspace/data/artifacts/${TAG}/$(basename "$artifact_rel")"

    "${SCP[@]}" "$REMOTE_BUILD_SOURCE" "$REMOTE_TARGET:$remote_script"
    "${SSH[@]}" "$REMOTE_TARGET" "chmod 700 '$remote_script'; cd '$TREE' && git -C '$project' branch --show-current && git -C '$project' rev-parse HEAD && git -C '$project' status --porcelain"
    "${SSH[@]}" "$REMOTE_TARGET" "rm -f '$remote_log' '$remote_exit' '$remote_pid'; nohup bash '$remote_script' '$TREE' '$project' '$TARGET' '$name' '$jobs' '$patch' '$artifact_rel' '$PRODUCT' '$remote_log' '$remote_exit' > '$remote_log' 2>&1 & echo \$! > '$remote_pid'; cat '$remote_pid'"

    rc=""
    deadline=$((SECONDS + BUILD_WAIT_SECONDS))
    while [ "$SECONDS" -lt "$deadline" ]; do
        rc="$("${SSH[@]}" "$REMOTE_TARGET" "cat '$remote_exit' 2>/dev/null || true")"
        if [ -n "$rc" ]; then break; fi
        sleep "$BUILD_POLL_SECONDS"
    done
    "${SSH[@]}" "$REMOTE_TARGET" "tail -20 '$remote_log' 2>/dev/null || true"
    if [ -z "$rc" ]; then
        remote_pid_value="$("${SSH[@]}" "$REMOTE_TARGET" "cat '$remote_pid' 2>/dev/null || true")"
        echo "[build] timeout after ${BUILD_WAIT_SECONDS}s waiting for $name; remote build may still be running (pid ${remote_pid_value:-unknown}); log: $remote_log" >&2
        RESULT_PR_OVERRIDE="$pr" write_build_result timeout build 3 "timeout after ${BUILD_WAIT_SECONDS}s waiting for $name; remote log: $remote_log; remote pid: ${remote_pid_value:-unknown}"
        exit 3
    fi
    if [ "$rc" -ne 0 ]; then
        echo "[build] $name failed with exit $rc; log: $remote_log" >&2
        RESULT_PR_OVERRIDE="$pr" write_build_result failed build "$rc" "$name failed with exit $rc; log: $remote_log"
        exit "$rc"
    fi

    mkdir -p "$(dirname "$artifact_local")"
    "${SCP[@]}" "$REMOTE_TARGET:$TREE/out/target/product/$PRODUCT/$artifact_rel" "$artifact_local"
    sha="$(sha256sum "$artifact_local" | awk '{print $1}')"
    echo "[build] $name artifact: $artifact_local"
    echo "$sha  $artifact_local"
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$name" "$artifact_local" "$sha" "$remote_log" "$image" "$dest" >> "$RESULT_ROWS"
    RESULT_PR_OVERRIDE="$pr" write_build_result success build 0

    if [ "$INSTALL" -eq 1 ]; then
        write_install_result running
        manifest="$WORK/manifest-${name}.json"
        MODULE_NAME="$name" SOURCE_PATH="$artifact_local" REMOTE_ARTIFACT="/home/huyang/fde-artifacts/${TAG}/$(basename "$artifact_rel")" IMAGE_NAME="$image" DEST_PATH="$dest" \
        python3 - "$manifest" <<'PY'
import json
import os
import sys
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump({
        "module": os.environ["MODULE_NAME"],
        "source": os.environ["SOURCE_PATH"],
        "artifact": os.environ["REMOTE_ARTIFACT"],
        "image": os.environ["IMAGE_NAME"],
        "dest": os.environ["DEST_PATH"],
    }, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
        if [ -n "$INSTALL_LOG" ]; then
            set +e
            "$INSTALL_SCRIPT" --manifest "$manifest" --no-start 2>&1 | tee -a "$INSTALL_LOG"
            rc=${PIPESTATUS[0]}
            set -e
            if [ "$rc" -ne 0 ]; then
                write_install_result failed "$rc" "install failed for $name; log: $INSTALL_LOG"
                exit "$rc"
            fi
        else
            "$INSTALL_SCRIPT" --manifest "$manifest" --no-start
        fi
    fi
done

RESULT_PR_OVERRIDE="$pr" write_build_result success build 0

if [ "$INSTALL" -eq 1 ]; then
    if [ "$START" -eq 1 ]; then
        if [ -n "$INSTALL_LOG" ]; then
            set +e
            "$INSTALL_SCRIPT" --start-only 2>&1 | tee -a "$INSTALL_LOG"
            rc=${PIPESTATUS[0]}
            set -e
            if [ "$rc" -ne 0 ]; then
                write_install_result failed "$rc" "start failed; log: $INSTALL_LOG"
                exit "$rc"
            fi
        else
            "$INSTALL_SCRIPT" --start-only
        fi
    fi
    write_install_result success 0
fi
echo "[build] done: ${M_NAME[*]}"
