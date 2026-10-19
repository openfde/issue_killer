#!/bin/bash
# 首次启动时把 fde-sources 同步为“分析所需模块”的子集。
# 在容器内运行（compose sources-sync），也可在装有 repo 的宿主机运行。
# 默认模块与当前部署一致：art build device external frameworks hardware
# openfde-sdk packages prebuilts system。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCES="${FDE_SOURCES:-/workspace/fde-sources}"
MANIFESTS="${FDE_MANIFESTS:-/workspace/fde-manifests}"
MANIFEST_URL="${FDE_MANIFEST_URL:-https://src.ift.run/openfde17/fde-manifests}"
MANIFEST_BRANCH="${FDE_MANIFEST_BRANCH:-fde_17}"
MODULES="${FDE_SOURCE_MODULES:-art build device external frameworks hardware openfde-sdk packages prebuilts system}"
JOBS="${FDE_SYNC_JOBS:-8}"
MARKER="$SOURCES/.fde-ai-sync.json"
TMP_MANIFEST="/tmp/fde-manifest.xml"

log() { echo "[$(date -u +%FT%TZ)] $*"; }

write_marker() {
    local mode="$1"
    python3 - "$MARKER" "$MANIFEST_URL" "$MANIFEST_BRANCH" "$MODULES" "$mode" <<'PY'
import datetime, json, sys

marker, url, branch, modules, mode = sys.argv[1:6]
with open(marker, "w", encoding="utf-8") as handle:
    json.dump(
        {
            "mode": mode,
            "manifest_url": url,
            "manifest_branch": branch,
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
    python3 - "$MARKER" "$MANIFEST_URL" "$MANIFEST_BRANCH" "$MODULES" <<'PY'
import json, sys

marker, url, branch, modules = sys.argv[1:5]
try:
    data = json.load(open(marker, encoding="utf-8"))
except (OSError, ValueError):
    sys.exit(1)
sys.exit(0 if (
    data.get("manifest_url") == url
    and data.get("manifest_branch") == branch
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

umask 022
ensure_manifests

if [ "${FORCE_SYNC:-0}" != "1" ] && marker_matches; then
    log "sources marker matches; skip sync"
    chmod -R a+rX "$SOURCES" "$MANIFESTS" 2>/dev/null || true
    exit 0
fi

if [ -d "$SOURCES" ] && [ -n "$(find "$SOURCES" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ] && [ ! -d "$SOURCES/.repo" ]; then
    log "existing prepared source tree without .repo; keep it and skip repo sync"
    write_marker external
    chmod -R a+rX "$SOURCES" "$MANIFESTS" 2>/dev/null || true
    exit 0
fi

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

log "syncing ${#PROJECTS[@]} projects (jobs=$JOBS)"
repo sync -c --no-tags -j"$JOBS" "${PROJECTS[@]}"

write_marker repo
chmod -R a+rX "$SOURCES" "$MANIFESTS" 2>/dev/null || true
log "source sync complete"
