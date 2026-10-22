#!/bin/bash
set -euo pipefail

usage() {
    echo "usage: $0 --manifest <module-manifest.json>" >&2
    exit 2
}

MANIFEST=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --manifest)
            [ "$#" -ge 2 ] || usage
            MANIFEST="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            usage
            ;;
    esac
done

[ -n "$MANIFEST" ] || usage
[ -r "$MANIFEST" ] || { echo "manifest not readable: $MANIFEST" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required to parse the manifest" >&2; exit 2; }

eval "$(python3 - "$MANIFEST" <<'PY'
import json
import shlex
import sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
except Exception as exc:
    raise SystemExit("invalid manifest: %s" % exc)

if not isinstance(data, dict):
    raise SystemExit("manifest must be a JSON object")

def required(name):
    value = data.get(name)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit("manifest missing %s" % name)
    return value.strip()

module = required("module")
artifact = required("artifact")
image = required("image")
dest = required("dest")

if "/" in module or module in (".", ".."):
    raise SystemExit("invalid module name")
if not artifact.startswith("/"):
    raise SystemExit("artifact must be an absolute path")
if image not in ("system", "vendor"):
    raise SystemExit("image must be system or vendor")
if ".." in dest.split("/"):
    raise SystemExit("destination must not contain ..")
if not dest.startswith(("/system/", "/system_ext/", "/product/", "/vendor/")):
    raise SystemExit("destination must be under /system, /system_ext, /product or /vendor")
if dest.endswith("/"):
    raise SystemExit("destination must be a file path, not a directory")

for key, value in (("MODULE", module), ("ARTIFACT", artifact), ("IMAGE", image), ("DEST", dest)):
    print("%s=%s" % (key, shlex.quote(value)))
PY
)"

IMAGE_PATH="/usr/share/waydroid-extra/images/${IMAGE}.img"
[ -f "$IMAGE_PATH" ] || { echo "image not found: $IMAGE_PATH" >&2; exit 2; }
[ -f "$ARTIFACT" ] || { echo "artifact not found: $ARTIFACT" >&2; exit 2; }
command -v mountpoint >/dev/null 2>&1 || { echo "mountpoint is required" >&2; exit 2; }
if mountpoint -q /mnt; then
    echo "/mnt is already mounted" >&2
    exit 2
fi

cleanup() {
    if mountpoint -q /mnt; then
        umount /mnt || true
    fi
}
trap cleanup EXIT

echo "[fde-install] module=$MODULE image=$IMAGE"
echo "[fde-install] artifact=$ARTIFACT"
echo "[fde-install] dest=$DEST"
systemctl stop waydroid-container.service
mount "$IMAGE_PATH" /mnt
mkdir -p "$(dirname "/mnt$DEST")"
cp -f "$ARTIFACT" "/mnt$DEST"
sync
umount /mnt
trap - EXIT
waydroid init -f
echo "[fde-install] complete: $MODULE -> $DEST"
