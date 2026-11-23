#!/bin/bash
# usage: lights.sh on|off
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
CONF="${RGB_SLEEP_CONF:-$DIR/devices.conf}"
[ "$1" = on ] || [ "$1" = off ] || { echo "usage: $0 on|off" >&2; exit 1; }
[ -f "$CONF" ] || { echo "missing $CONF (copy devices.conf.example)" >&2; exit 1; }

# Re-exec as root with sudo if not already root
if [ "$(id -u)" -ne 0 ]; then
  exec sudo "$0" "$@"
fi

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
    echo 1              > "$d/authorized"
    echo "${WAKE[$id]}" > "$d/power/wakeup"
    echo 0              > "$d/power/autosuspend_delay_ms"
    echo auto           > "$d/power/control"
  else
    echo on             > "$d/power/control"
    echo 1              > "$d/authorized"
    echo enabled        > "$d/power/wakeup"
  fi
done
