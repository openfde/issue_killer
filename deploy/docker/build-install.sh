#!/bin/bash
set -euo pipefail

CONTAINER="${FDE_CONTAINER:-openfde-ai}"
if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "container not found: $CONTAINER" >&2
    exit 2
fi
if [ "$(docker inspect -f '{{.State.Status}}' "$CONTAINER")" != "running" ]; then
    echo "container is not running: $CONTAINER" >&2
    exit 2
fi

exec docker exec -u agent "$CONTAINER" bash /workspace/deploy/assist/build-install.sh "$@"
