#!/bin/bash
# 在服务器上创建并启动 aosp17-ai 容器（rootless docker）。
# 依赖: /aosp/aosp17-ai/{workspace,pi-agent,.env} 与 aosp17-ai:latest 镜像。
# 用法: deploy/server/run-ai-container.sh
set -euo pipefail

DOCKER_HOST_SOCK="${DOCKER_HOST_SOCK:-unix:///aosp4/hy_docker_root/run/docker.sock}"
dk() { docker -H "$DOCKER_HOST_SOCK" "$@"; }

AI_ROOT="${AI_ROOT:-/aosp/aosp17-ai}"
WORKSPACE="$AI_ROOT/workspace"
PI_AGENT="$AI_ROOT/pi-agent"
ENV_FILE="$AI_ROOT/.env"
SOURCES_TREE="${SOURCES_TREE:-/aosp4/hy_fde17_docker}"
OUT_TREE="${OUT_TREE:-/aosp3/out_fde17}"

[ -f "$ENV_FILE" ] || { echo "缺少 $ENV_FILE（从 deploy/server/env.example 复制后填写）" >&2; exit 2; }
[ -d "$WORKSPACE" ] || { echo "缺少工作区 $WORKSPACE" >&2; exit 2; }
[ -d "$SOURCES_TREE" ] || { echo "缺少源码树 $SOURCES_TREE" >&2; exit 2; }
[ -d "$OUT_TREE" ] || { echo "缺少构建输出 $OUT_TREE" >&2; exit 2; }
mkdir -p "$PI_AGENT"

if dk inspect aosp17-ai >/dev/null 2>&1; then
    echo "aosp17-ai 容器已存在；使用 docker -H $DOCKER_HOST_SOCK start aosp17-ai 启动"
    exit 0
fi

dk run -d --name aosp17-ai --hostname aosp17-ai --restart unless-stopped \
    --env-file "$ENV_FILE" \
    -e PI_CODING_AGENT_DIR=/workspace/pi-agent \
    -v "$WORKSPACE":/workspace \
    -v "$SOURCES_TREE":/workspace/fde-sources:ro \
    -v "$SOURCES_TREE":/workspace/fde-build \
    -v "$OUT_TREE":/aosp3/out_fde17 \
    -v "$PI_AGENT":/workspace/pi-agent \
    aosp17-ai:latest

echo "已启动 aosp17-ai。首次使用请执行容器自检："
echo "  /aosp/aosp17-docker/dk exec aosp17-ai bash /workspace/deploy/server/ai-container-setup.sh"
