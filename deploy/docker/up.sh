#!/bin/bash
# Docker 一键安装/启动：检查依赖与凭据 → 初始化配置 → 构建 → 启动 scanner + poller。
# 用法: ./deploy/docker/up.sh [--force-sync]
set -euo pipefail

cd "$(dirname "$0")/../.."
ROOT="$PWD"

FORCE_SYNC=0
case "${1:-}" in
    "") ;;
    --force-sync) FORCE_SYNC=1 ;;
    *) echo "usage: $0 [--force-sync]" >&2; exit 2 ;;
esac

if [ -f "$ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$ROOT/.env"
    set +a
elif [ -z "${GH_TOKEN:-}" ] || [ -z "${DEEPSEEK_API_KEY:-}" ]; then
    cp "$ROOT/deploy/server/env.example" "$ROOT/.env"
    echo "已生成 .env；请填写 GH_TOKEN 与 DEEPSEEK_API_KEY 后重新运行。" >&2
    exit 2
fi

: "${GH_TOKEN:?GH_TOKEN 未设置（环境变量或 .env）}"
: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY 未设置（环境变量或 .env）}"

command -v docker >/dev/null 2>&1 || { echo "未找到 docker" >&2; exit 2; }
docker compose version >/dev/null 2>&1 || { echo "未找到 docker compose v2" >&2; exit 2; }

MANIFEST_URL="${FDE_MANIFEST_URL:-https://github.com/openfde/fde-manifests.git}"
MANIFEST_BRANCH="${FDE_MANIFEST_BRANCH:-fde_17}"

if [ ! -f "$ROOT/config/openfde-ai-server.json" ]; then
    cp "$ROOT/config/openfde-ai-server.example.json" "$ROOT/config/openfde-ai-server.json"
    echo "已生成 config/openfde-ai-server.json（可按需调整 scan/worker）。"
fi

if [ ! -f "$ROOT/fde-manifests/default.xml" ]; then
    if [ -d "$ROOT/fde-manifests" ] && [ -n "$(find "$ROOT/fde-manifests" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]; then
        echo "fde-manifests 非空但缺少 default.xml：$ROOT/fde-manifests" >&2
        exit 2
    fi
    git clone --depth=1 -b "$MANIFEST_BRANCH" "$MANIFEST_URL" "$ROOT/fde-manifests"
fi

mkdir -p "$ROOT/fde-sources"
if [ "$(id -u)" -eq 0 ]; then
    # 同步服务以 root 运行，这里只保证容器可创建；读取由 agent(1000) 完成。
    chmod 0755 "$ROOT/fde-sources" "$ROOT/fde-manifests" 2>/dev/null || true
fi

if [ "$FORCE_SYNC" -eq 1 ]; then
    export FORCE_SYNC
fi

echo "构建镜像..."
docker compose build

echo "启动服务（首次会按模块子集同步 fde-sources，可能耗时较长）..."
docker compose up -d --force-recreate

docker compose ps
cat <<'EOF'

常用命令：
  docker compose logs -f sources-sync     # 首次源码同步进度
  docker compose logs -f scanner poller
  docker compose exec scanner pi          # 交互式 Pi（也可用 shell 服务）
  docker compose --profile tools up -d shell
  docker compose exec shell pi
  FORCE_SYNC=1 ./deploy/docker/up.sh      # 重新同步源码子集

首次同步的模块由 FDE_SOURCE_MODULES 控制，默认：
  art build device external frameworks hardware openfde-sdk packages prebuilts system
EOF
