#!/bin/bash
# 在服务器上构建 aosp17-ai:latest（rootless docker）。
# 用法: deploy/server/build-ai-image.sh
set -euo pipefail

DOCKER_HOST_SOCK="${DOCKER_HOST_SOCK:-unix:///aosp4/hy_docker_root/run/docker.sock}"
dk() { docker -H "$DOCKER_HOST_SOCK" "$@"; }

SERVER_DIR="$(cd "$(dirname "$0")" && pwd)"
CONTEXT="${AI_BUILD_CONTEXT:-/aosp/aosp17-ai/build-context}"

GH_BIN="${GH_BIN:-/usr/bin/gh}"
GLSLANG_BIN="${GLSLANG_BIN:-/usr/local/bin/glslang}"

[ -x "$GH_BIN" ] || { echo "缺少 gh 二进制: $GH_BIN" >&2; exit 2; }
[ -x "$GLSLANG_BIN" ] || { echo "缺少 glslang 二进制: $GLSLANG_BIN" >&2; exit 2; }

mkdir -p "$CONTEXT"
install -m 0755 "$GH_BIN" "$CONTEXT/gh"
install -m 0755 "$GLSLANG_BIN" "$CONTEXT/glslang"
cp "$SERVER_DIR/Dockerfile.ai" "$CONTEXT/Dockerfile.ai"

dk build -f "$CONTEXT/Dockerfile.ai" -t aosp17-ai:latest "$CONTEXT"
echo "镜像 aosp17-ai:latest 构建完成"
