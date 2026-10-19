#!/bin/bash
# 首次启动时把 fde-sources 同步为“分析所需模块”的子集。
# 默认 github 模式：按 github-sources.tsv 克隆 OpenFDE GitHub 镜像（与当前
# fde-sources 树一致，无需访问内部 GitLab/repo）。也支持 repo 模式与 none。
#
# 环境变量：
#   FDE_SYNC_MODE=github|repo|none     默认 github
#   FDE_SOURCE_MODULES="art build ..." 默认当前 10 个顶层模块
#   FDE_SOURCE_BRANCH=fde_17           github 模式分支
#   FDE_MANIFEST_URL / FDE_MANIFEST_BRANCH
#   FDE_SOURCE_MAP                    默认 deploy/docker/github-sources.tsv
#   FDE_SYNC_JOBS=8                    并发克隆数
#   FORCE_SYNC=1                       忽略 marker，重新同步/重置
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCES="${FDE_SOURCES:-/workspace/fde-sources}"
MANIFESTS="${FDE_MANIFESTS:-/workspace/fde-manifests}"
SYNC_MODE="${FDE_SYNC_MODE:-github}"
MANIFEST_URL="${FDE_MANIFEST_URL:-https://github.com/openfde/fde-manifests.git}"
MANIFEST_BRANCH="${FDE_MANIFEST_BRANCH:-fde_17}"
SOURCE_BRANCH="${FDE_SOURCE_BRANCH:-fde_17}"
SOURCE_MAP="${FDE_SOURCE_MAP:-$SCRIPT_DIR/github-sources.tsv}"
MODULES="${FDE_SOURCE_MODULES:-art build device external frameworks hardware openfde-sdk packages prebuilts system}"
JOBS="${FDE_SYNC_JOBS:-8}"
MARKER="$SOURCES/.fde-ai-sync.json"
TMP_MANIFEST="/tmp/fde-manifest.xml"

log() { echo "[$(date -u +%FT%TZ)] $*"; }

write_marker() {
    local mode="$1"
    python3 - "$MARKER" "$mode" "$SYNC_MODE" "$MANIFEST_URL" "$MANIFEST_BRANCH" "$SOURCE_BRANCH" "$MODULES" <<'PY'
import datetime, json, sys

marker, mode, sync_mode, url, manifest_branch, source_branch, modules = sys.argv[1:8]
with open(marker, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "mode": mode,
            "sync_mode": sync_mode,
            "manifest_url": url,
            "manifest_branch": manifest_branch,
            "source_branch": source_branch,
            "modules": modules.split(),
            "synced_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        handle,
        ensure_ascii=False,
        indent=2,
    )
    handle.write("\n")
PY
}

marker_matches() {
    [ -f "$MARKER" ] || return 1
    python3 - "$MARKER" "$SYNC_MODE" "$MANIFEST_URL" "$MANIFEST_BRANCH" "$SOURCE_BRANCH" "$MODULES" <<'PY'
import json, sys

marker, sync_mode, url, manifest_branch, source_branch, modules = sys.argv[1:7]
try:
    data = json.load(open(marker, encoding="utf-8"))
except (OSError, ValueError):
    sys.exit(1)
sys.exit(0 if (
    data.get("sync_mode") == sync_mode
    and data.get("manifest_url") == url
    and data.get("manifest_branch") == manifest_branch
    and data.get("source_branch") == source_branch
    and data.get("modules") == modules.split()
) else 1)
PY
}

ensure_manifests() {
    if [ -f "$MANIFESTS/default.xml" ]; then
        return
    fi
    mkdir -p "$MANIFESTS"
    if [ -n "$(find "$MANIFESTS" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
        echo "fde-manifests 非空但缺少 default.xml：$MANIFESTS" >&2
        exit 1
    fi
    log "cloning manifests $MANIFEST_URL ($MANIFEST_BRANCH)"
    git clone --depth=1 -b "$MANIFEST_BRANCH" "$MANIFEST_URL" "$MANIFESTS"
}

select_github_rows() {
    python3 - "$SOURCE_MAP" "$MODULES" <<'PY'
import sys

source_map, modules = sys.argv[1], set(sys.argv[2].split())
for line in open(source_map, encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    parts = line.split("\t")
    if len(parts) < 2:
        continue
    path, url = parts[0], parts[1]
    if path.split("/", 1)[0] in modules:
        print(path, url)
PY
}

sync_one_github() {
    local path="$1" url="$2"
    local dest="$SOURCES/$path"
    if [ -d "$dest/.git" ]; then
        if [ "${FORCE_SYNC:-0}" = "1" ]; then
            git -C "$dest" fetch --depth=1 origin "$SOURCE_BRANCH"
            git -C "$dest" reset --hard FETCH_HEAD
        fi
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    git clone --depth=1 --branch "$SOURCE_BRANCH" "$url" "$dest"
}

sync_github() {
    [ -f "$SOURCE_MAP" ] || { echo "source map not found: $SOURCE_MAP" >&2; exit 1; }
    mapfile -t ROWS < <(select_github_rows)
    if [ "${#ROWS[@]}" -eq 0 ]; then
        echo "no source map rows matched modules: $MODULES" >&2
        exit 1
    fi
    log "github mirror sync: ${#ROWS[@]} projects (branch=$SOURCE_BRANCH, jobs=$JOBS)"
    export -f sync_one_github
    export SOURCES SOURCE_BRANCH FORCE_SYNC
    printf '%s\n' "${ROWS[@]}" | xargs -P "$JOBS" -n2 bash -c 'sync_one_github "$@"' _
}

sync_repo() {
    mkdir -p "$SOURCES"
    cd "$SOURCES"
    if [ ! -d .repo ]; then
        log "repo init $MANIFEST_URL ($MANIFEST_BRANCH)"
        repo init -u "$MANIFEST_URL" -b "$MANIFEST_BRANCH" --depth=1 --no-clone-bundle
    fi
    read -r -a MODULE_ARRAY <<< "$MODULES"
    log "resolving projects for modules: ${MODULE_ARRAY[*]}"
    repo manifest -o "$TMP_MANIFEST"
    mapfile -t PROJECTS < <(python3 "$SCRIPT_DIR/select-sources.py" "$TMP_MANIFEST" "${MODULE_ARRAY[@]}")
    if [ "${#PROJECTS[@]}" -eq 0 ]; then
        echo "no manifest projects matched modules: $MODULES" >&2
        exit 1
    fi
    log "repo sync ${#PROJECTS[@]} projects (jobs=$JOBS)"
    repo sync -c --no-tags -j"$JOBS" "${PROJECTS[@]}"
}

case "$SYNC_MODE" in
    github|repo|none) ;;
    *) echo "FDE_SYNC_MODE must be github, repo or none: $SYNC_MODE" >&2; exit 2 ;;
esac

umask 022
ensure_manifests

if [ "${FORCE_SYNC:-0}" != "1" ] && marker_matches; then
    log "sources marker matches; skip sync"
    chmod -R a+rX "$SOURCES" "$MANIFESTS" 2>/dev/null || true
    exit 0
fi

mkdir -p "$SOURCES"
case "$SYNC_MODE" in
    github) sync_github ;;
    repo) sync_repo ;;
    none) log "source sync disabled (FDE_SYNC_MODE=none)" ;;
esac

write_marker "$SYNC_MODE"
chmod -R a+rX "$SOURCES" "$MANIFESTS" 2>/dev/null || true
log "source sync complete"
