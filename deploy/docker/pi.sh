#!/bin/bash
# 直接进入运行中容器的 Pi；等价于 docker exec -it openfde-ai pi。
set -euo pipefail

if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -qx 'openfde-ai'; then
    echo "容器 openfde-ai 未运行；先执行 ./deploy/docker/up.sh" >&2
    exit 2
fi

exec docker exec -it openfde-ai pi
