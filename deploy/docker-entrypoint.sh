#!/bin/sh
set -eu

pi_runtime_dir="${PI_CODING_AGENT_DIR:-/tmp/pi-agent}"

mkdir -p "$pi_runtime_dir"

if [ -d /run/secrets/pi-agent ]; then
    cp -a /run/secrets/pi-agent/. "$pi_runtime_dir/"
fi

export PI_CODING_AGENT_DIR="$pi_runtime_dir"

exec "$@"
