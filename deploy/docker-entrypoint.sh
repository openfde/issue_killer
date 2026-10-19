#!/bin/sh
set -eu

pi_runtime_dir="${PI_CODING_AGENT_DIR:-/tmp/pi-agent}"

mkdir -p "$pi_runtime_dir"

if [ -d /run/secrets/pi-agent ]; then
    cp -a /run/secrets/pi-agent/. "$pi_runtime_dir/"
fi

if [ ! -f "$pi_runtime_dir/settings.json" ] && [ -f /opt/pi-agent-template/settings.json ]; then
    cp /opt/pi-agent-template/settings.json "$pi_runtime_dir/settings.json"
fi

export PI_CODING_AGENT_DIR="$pi_runtime_dir"

# 容器内以 agent 读取只读源码树；允许与宿主/同步阶段不同属主的仓库。
git config --global --add safe.directory '*' >/dev/null 2>&1 || true
if [ -n "${GH_TOKEN:-}" ]; then
    gh auth setup-git >/dev/null 2>&1 || true
fi

exec "$@"
