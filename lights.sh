#!/bin/bash
# usage: lights.sh on|off
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
CONF="${RGB_SLEEP_CONF:-$DIR/devices.conf}"
[ "$1" = on ] || [ "$1" = off ] || { echo "usage: $0 on|off" >&2; exit 1; }
[ -f "$CONF" ] || { echo "missing $CONF (copy devices.conf.example)" >&2; exit 1; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO=sudo

declare -A WAKE
while read -r id wake _; do
  case "$id" in ""|\#*) continue;; esac
  WAKE[$id]="${wake:-disabled}"
done < "$CONF"

for d in /sys/bus/usb/devices/*; do
  [ -f "$d/idVendor" ] || continue
  id="$(cat "$d/idVendor"):$(cat "$d/idProduct")"
  [ -n "${WAKE[$id]}" ] || continue
  if [ "$1" = off ]; then
    echo 1            | $SUDO tee "$d/authorized" >/dev/null
    echo "${WAKE[$id]}" | $SUDO tee "$d/power/wakeup" >/dev/null
    echo 0            | $SUDO tee "$d/power/autosuspend_delay_ms" >/dev/null
    echo auto         | $SUDO tee "$d/power/control" >/dev/null
  else
    echo on      | $SUDO tee "$d/power/control" >/dev/null
    echo 1       | $SUDO tee "$d/authorized" >/dev/null
    echo enabled | $SUDO tee "$d/power/wakeup" >/dev/null
  fi
done
