#!/bin/bash
set -euo pipefail

usage() {
    echo "usage: $0 --manifest <json> [--no-start] | --start-only" >&2
    exit 2
}

MANIFEST=""
START=1
START_ONLY=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        --manifest)
            [ "$#" -ge 2 ] || usage
            MANIFEST="$2"
            shift 2
            ;;
        --no-start)
            START=0
            shift
            ;;
        --start-only)
            START_ONLY=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

HOST="${FDE_INSTALL_HOST:-10.31.62.247}"
USER_NAME="${FDE_INSTALL_USER:-huyang}"
SSH_KEY="${FDE_SSH_KEY:-/workspace/data/ssh/id_ed25519}"
KNOWN_HOSTS="${FDE_KNOWN_HOSTS:-/workspace/data/ssh/known_hosts}"
INSTALLER="${FDE_INSTALLER:-/usr/local/sbin/fde-install-module}"
REMOTE_DIR="${FDE_REMOTE_MANIFEST_DIR:-/home/huyang/fde-install}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
START_HELPER_SOURCE="${FDE_START_HELPER_SOURCE:-$SCRIPT_DIR/fde-start.sh}"
START_HELPER_REMOTE="${FDE_START_HELPER:-/home/huyang/fde-start.sh}"
SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o UserKnownHostsFile="$KNOWN_HOSTS")
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o UserKnownHostsFile="$KNOWN_HOSTS")

if [ "$START_ONLY" -eq 0 ]; then
    [ -n "$MANIFEST" ] || usage
    [ -r "$MANIFEST" ] || { echo "manifest not readable: $MANIFEST" >&2; exit 2; }
    command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 2; }

    eval "$(python3 - "$MANIFEST" <<'PY'
import json
import shlex
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    data = json.load(handle)

def required(name):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("manifest missing %s" % name)
    return value.strip()

module = required("module")
source = required("source")
artifact = required("artifact")
if "/" in module:
    raise SystemExit("invalid module")
if not source.startswith("/"):
    raise SystemExit("source must be absolute")
if not artifact.startswith("/home/"):
    raise SystemExit("remote artifact must be under /home")
for key, value in (("MODULE", module), ("SOURCE", source), ("ARTIFACT", artifact)):
    print("%s=%s" % (key, shlex.quote(value)))
PY
)"

    [ -f "$SOURCE" ] || { echo "source artifact not found: $SOURCE" >&2; exit 2; }
    REMOTE_MANIFEST="$REMOTE_DIR/${MODULE}.json"
    "${SSH[@]}" "$USER_NAME@$HOST" "mkdir -p '$REMOTE_DIR' '$(dirname "$ARTIFACT")'"
    "${SCP[@]}" "$SOURCE" "$USER_NAME@$HOST:$ARTIFACT"
    "${SCP[@]}" "$MANIFEST" "$USER_NAME@$HOST:$REMOTE_MANIFEST"
    "${SSH[@]}" "$USER_NAME@$HOST" "sudo -n '$INSTALLER' --manifest '$REMOTE_MANIFEST'"
    echo "[fde-install] installed $MODULE on $HOST"
fi

if [ "$START_ONLY" -eq 1 ] || [ "$START" -eq 1 ]; then
    [ -f "$START_HELPER_SOURCE" ] || { echo "start helper not found: $START_HELPER_SOURCE" >&2; exit 2; }
    "${SCP[@]}" "$START_HELPER_SOURCE" "$USER_NAME@$HOST:$START_HELPER_REMOTE"
    "${SSH[@]}" "$USER_NAME@$HOST" "chmod 700 '$START_HELPER_REMOTE' && bash '$START_HELPER_REMOTE'"
    echo "[fde-install] started OpenFDE"
fi
