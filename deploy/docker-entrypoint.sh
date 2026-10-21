#!/bin/sh
set -eu

pi_runtime_dir="${PI_CODING_AGENT_DIR:-/tmp/pi-agent}"

mkdir -p "$pi_runtime_dir"

if [ -d /run/secrets/pi-agent ]; then
    cp -a /run/secrets/pi-agent/. "$pi_runtime_dir/"
fi

if [ ! -f "$pi_runtime_dir/settings.json" ]; then
    if python3 -c 'import json, os, sys; enabled=[m.strip() for m in os.environ.get("PI_ENABLED_MODELS", "deepseek/deepseek-flash").split(",") if m.strip()]; json.dump({"defaultProvider": os.environ.get("PI_PROVIDER", "deepseek"), "defaultModel": os.environ.get("PI_MODEL", "deepseek-flash"), "enabledModels": enabled}, sys.stdout, indent=2)' > "$pi_runtime_dir/settings.json" 2>/dev/null; then
        :
    elif [ -f /opt/pi-agent-template/settings.json ]; then
        cp /opt/pi-agent-template/settings.json "$pi_runtime_dir/settings.json"
    fi
fi

if [ ! -f "$pi_runtime_dir/models-store.json" ] && [ -f /opt/pi-agent-template/models-store.json ]; then
    cp /opt/pi-agent-template/models-store.json "$pi_runtime_dir/models-store.json"
fi

export PI_CODING_AGENT_DIR="$pi_runtime_dir"

# 容器内以 agent 读取只读源码树；允许与宿主/同步阶段不同属主的仓库。
git config --global --add safe.directory '*' >/dev/null 2>&1 || true
if [ -n "${GH_TOKEN:-}" ]; then
    gh auth setup-git >/dev/null 2>&1 || true
fi

exec "$@"
