#!/bin/sh
set -u

scan_interval="${SCAN_INTERVAL_SECONDS:-1800}"

case "$scan_interval" in
    ''|*[!0-9]*)
        echo "SCAN_INTERVAL_SECONDS must be a positive integer" >&2
        exit 64
        ;;
esac

if [ "$scan_interval" -eq 0 ]; then
    echo "SCAN_INTERVAL_SECONDS must be greater than zero" >&2
    exit 64
fi

child_pid=""

stop() {
    if [ -n "$child_pid" ]; then
        kill "$child_pid" 2>/dev/null || true
    fi
    exit 0
}

trap stop INT TERM

while :; do
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) starting OpenFDE issue scan"
    python automation/openfde_ai_server.py --workspace /workspace --config config/openfde-ai-server.json scan &
    child_pid=$!
    if wait "$child_pid"; then
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) OpenFDE issue scan completed"
    else
        echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) OpenFDE issue scan failed; retrying after interval" >&2
    fi
    child_pid=""
    sleep "$scan_interval"
done
