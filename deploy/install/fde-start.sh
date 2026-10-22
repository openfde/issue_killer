#!/bin/bash
set -u

export XDG_SESSION_TYPE=x11
export XDG_CURRENT_DESKTOP=UKUI
export XDG_SESSION_ID="${XDG_SESSION_ID:-4}"
export XDG_SEAT="${XDG_SEAT:-seat0}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/huyang/.Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"

if ! pgrep -f '[f]de_ctrl' >/dev/null 2>&1; then
    nohup fde_ctrl -m shell -n -a openfde >/tmp/fde-ctrl.log 2>&1 &
    sleep 2
fi

status="$(waydroid status 2>/dev/null || true)"
if printf '%s' "$status" | grep -q 'Session:.*STOPPED'; then
    nohup waydroid session start >/tmp/waydroid-session.log 2>&1 &
    for _ in $(seq 1 20); do
        status="$(waydroid status 2>/dev/null || true)"
        if printf '%s' "$status" | grep -q 'Session:.*RUNNING'; then
            break
        fi
        sleep 1
    done
fi

if pgrep -f '[f]de_ctrl' >/dev/null 2>&1; then
    nohup /usr/bin/fde_shortcut >/tmp/fde-start.log 2>&1 &
fi

sleep 1
echo "[fde-start] waydroid status:"
waydroid status 2>&1 || true
echo "[fde-start] fde_ctrl:"
pgrep -a -f '[f]de_ctrl' | head -3 || true
