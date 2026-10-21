#!/bin/bash
# Docker 一键安装/启动：自动生成 .env → 检查凭据 → 构建 → 启动 scanner + poller。
# 用法:
#   export GH_TOKEN=...
#   export DEEPSEEK_API_KEY=...            # 或 OPENAI_API_KEY/ANTHROPIC_API_KEY/...
#   export PI_PROVIDER=deepseek PI_MODEL=deepseek-flash
#   ./deploy/docker/up.sh [--force-sync]
set -euo pipefail

cd "$(dirname "$0")/../.."
ROOT="$PWD"

FORCE_SYNC=0
case "${1:-}" in
    "") ;;
    --force-sync) FORCE_SYNC=1 ;;
    *) echo "usage: $0 [--force-sync]" >&2; exit 2 ;;
esac

load_env() {
    [ -f "$ROOT/.env" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        case "$line" in ''|'#'*) continue ;; esac
        local key="${line%%=*}"
        local value="${line#*=}"
        case "$key" in ''|*[!A-Za-z0-9_]*) continue ;; esac
        # 已 export 的变量优先，不被 .env 覆盖。
        if [ -z "${!key+x}" ]; then
            export "$key=$value"
        fi
    done < "$ROOT/.env"
}

if [ ! -f "$ROOT/.env" ]; then
    cp "$ROOT/deploy/server/env.example" "$ROOT/.env"
    echo "已自动生成 .env；可直接 export 变量后重新运行，或编辑 .env。"
fi
load_env

if [ -z "${GH_TOKEN:-}" ]; then
    echo "缺少 GH_TOKEN：请先 export GH_TOKEN=... 或写入 .env（创建与权限见 README 4.4）。" >&2
    exit 2
fi

provider="${PI_PROVIDER:-deepseek}"
case "$provider" in
    deepseek)
        if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
            echo "provider=deepseek 需要 DEEPSEEK_API_KEY（export 或 .env）。" >&2
            exit 2
        fi
        ;;
    openai)
        if [ -z "${OPENAI_API_KEY:-}" ]; then
            echo "provider=openai 需要 OPENAI_API_KEY（export 或 .env）。" >&2
            exit 2
        fi
        ;;
    anthropic)
        if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
            echo "provider=anthropic 需要 ANTHROPIC_API_KEY（export 或 .env）。" >&2
            exit 2
        fi
        ;;
    gemini|google)
        if [ -z "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}" ]; then
            echo "provider=$provider 需要 GEMINI_API_KEY 或 GOOGLE_API_KEY（export 或 .env）。" >&2
            exit 2
        fi
        ;;
    *)
        echo "提示：未识别的 PI_PROVIDER=$provider；请确认 .env/环境变量中已有对应凭据（会通过 env_file 传入容器）。" >&2
        ;;
esac

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

mkdir -p "$ROOT/fde-sources" "$ROOT/data/intake"
chmod 0777 "$ROOT/data/intake" 2>/dev/null || true
if [ "$(id -u)" -eq 0 ]; then
    chmod 0755 "$ROOT/fde-sources" "$ROOT/fde-manifests" 2>/dev/null || true
fi

if [ "$FORCE_SYNC" -eq 1 ]; then
    export FORCE_SYNC
fi

echo "构建镜像..."
docker compose build

echo "启动服务（首次会同步源码模块，可能耗时较长）..."
docker compose up -d --force-recreate

docker compose ps
cat <<'EOF'

进入容器后运行 pi：
  docker exec -it openfde-ai bash
  pi

或直接进入 Pi：
  docker exec -it openfde-ai pi
  # 等价：./deploy/docker/pi.sh

日志：
  docker logs -f openfde-ai-sources    # 首次源码同步
  docker logs -f openfde-ai            # scanner
  docker logs -f openfde-ai-poller     # 回复轮询

重新同步源码：
  FORCE_SYNC=1 ./deploy/docker/up.sh
EOF
