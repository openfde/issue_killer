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
        -h|--help) usage ;;
        *) usage ;;
    esac
done

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
STAMP="$(date +%Y%m%d-%H%M%S)"
TAG="${ISSUE:-local}"
WORK="${FDE_WORK_ROOT:-/workspace/data/assist/work}/${TAG}-${STAMP}"
mkdir -p "$WORK"

NPROC="$("${SSH[@]}" "$REMOTE_TARGET" "nproc 2>/dev/null || echo 8" | tr -dc '0-9')"
[ -n "$NPROC" ] || NPROC=8

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
    for _ in $(seq 1 360); do
        rc="$("${SSH[@]}" "$REMOTE_TARGET" "cat '$remote_exit' 2>/dev/null || true")"
        if [ -n "$rc" ]; then break; fi
        sleep 2
    done
    "${SSH[@]}" "$REMOTE_TARGET" "tail -20 '$remote_log' 2>/dev/null || true"
    if [ -z "$rc" ]; then
        echo "[build] timeout waiting for $name; inspect $remote_log" >&2
        exit 3
    fi
    if [ "$rc" -ne 0 ]; then
        echo "[build] $name failed with exit $rc; log: $remote_log" >&2
        exit "$rc"
    fi

    mkdir -p "$(dirname "$artifact_local")"
    "${SCP[@]}" "$REMOTE_TARGET:$TREE/out/target/product/$PRODUCT/$artifact_rel" "$artifact_local"
    echo "[build] $name artifact: $artifact_local"
    sha256sum "$artifact_local"

    if [ "$INSTALL" -eq 1 ]; then
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
        "$INSTALL_SCRIPT" --manifest "$manifest" --no-start
    fi
done

if [ "$INSTALL" -eq 1 ] && [ "$START" -eq 1 ]; then
    "$INSTALL_SCRIPT" --start-only
fi
echo "[build] done: ${M_NAME[*]}"
