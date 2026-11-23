#!/bin/bash
# ==============================================================================
#  ⚡ RGB-SLEEP CLI CONTROLLER
# ==============================================================================

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
CONF="${RGB_SLEEP_CONF:-$DIR/devices.conf}"

# Terminal Colors & Styling
if [ -t 1 ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  CYAN="\033[0;36m"
  GREEN="\033[0;32m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  MAGENTA="\033[0;35m"
  BLUE="\033[0;34m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  CYAN=""
  GREEN=""
  YELLOW=""
  RED=""
  MAGENTA=""
  BLUE=""
  RESET=""
fi

CHECK="${GREEN}✔${RESET}"
CROSS="${RED}✖${RESET}"
BULLET="${CYAN}●${RESET}"
STAR="${YELLOW}★${RESET}"
ARROW="${CYAN}➜${RESET}"

show_banner() {
  echo -e "${CYAN}${BOLD}╔═══════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${CYAN}${BOLD}║                ⚡ RGB-SLEEP CONTROLLER ⚡                 ║${RESET}"
  echo -e "${CYAN}${BOLD}╚═══════════════════════════════════════════════════════════╝${RESET}"
}

show_help() {
  show_banner
  echo -e "${BOLD}USAGE:${RESET}"
  echo -e "  ${CYAN}./lights.sh${RESET} ${YELLOW}<command>${RESET}\n"
  echo -e "${BOLD}COMMANDS:${RESET}"
  echo -e "  ${GREEN}off${RESET}      Turn off RGB on configured USB peripherals"
  echo -e "  ${GREEN}on${RESET}       Turn on RGB and restore normal power"
  echo -e "  ${GREEN}status${RESET}   Show power state of devices, service, and tray"
  echo -e "  ${GREEN}tray${RESET}     Launch or restart the taskbar tray indicator"
  echo -e "  ${GREEN}help${RESET}     Show this help manual\n"
  echo -e "${BOLD}EXAMPLES:${RESET}"
  echo -e "  ${DIM}# Turn lights off:${RESET}"
  echo -e "  ./lights.sh off\n"
  echo -e "  ${DIM}# Check live status:${RESET}"
  echo -e "  ./lights.sh status\n"
  echo -e "  ${DIM}# Test turning off for 15 seconds, then auto-restore:${RESET}"
  echo -e "  ./lights.sh off && sleep 15 && ./lights.sh on\n"
}

# Auto-elevate with sudo for hardware power control
elevate_if_needed() {
  if [ "$(id -u)" -ne 0 ]; then
    exec sudo "$0" "$@"
  fi
}

show_status() {
  show_banner
  echo -e "\n${BOLD}${MAGENTA}▶ SYSTEM SERVICES${RESET}"
  
  # Watcher Service
  if systemctl is-active --quiet wake-watch.service; then
    echo -e "  ${BULLET} Watcher Daemon (systemd):  ${GREEN}${BOLD}ACTIVE (RUNNING)${RESET} ${DIM}[wake-watch.service]${RESET}"
  else
    echo -e "  ${BULLET} Watcher Daemon (systemd):  ${RED}${BOLD}STOPPED${RESET} ${DIM}[wake-watch.service]${RESET}"
  fi

  # Tray Indicator
  TRAY_PID=$(pgrep -f "python.*tray\.py" 2>/dev/null | head -n 1)
  if [ -n "$TRAY_PID" ]; then
    echo -e "  ${BULLET} Taskbar Tray Indicator:   ${GREEN}${BOLD}ACTIVE${RESET} ${DIM}(PID: $TRAY_PID)${RESET}"
  else
    echo -e "  ${BULLET} Taskbar Tray Indicator:   ${YELLOW}${BOLD}NOT RUNNING${RESET} ${DIM}(run: ./lights.sh tray)${RESET}"
  fi

  echo -e "\n${BOLD}${MAGENTA}▶ CONFIGURED USB DEVICES${RESET} ${DIM}($CONF)${RESET}"

  if [ ! -f "$CONF" ]; then
    echo -e "  ${CROSS} ${RED}Missing configuration file: $CONF${RESET}"
    return
  fi

  declare -A WAKE
  while read -r id wake _; do
    case "$id" in ""|\#*) continue;; esac
    WAKE[$id]="${wake:-disabled}"
  done < "$CONF"

  printf "  ${BOLD}%-12s %-12s %-24s %-16s %-10s${RESET}\n" "TYPE" "ID" "PRODUCT" "POWER STATUS" "WAKEUP"
  echo -e "  ${DIM}-------------------------------------------------------------------------${RESET}"

  FOUND=0
  for d in /sys/bus/usb/devices/*; do
    [ -f "$d/idVendor" ] || continue
    id="$(cat "$d/idVendor"):$(cat "$d/idProduct")"
    [ -n "${WAKE[$id]}" ] || continue
    FOUND=1

    prod="$(cat "$d/product" 2>/dev/null || echo "USB Device")"
    [ ${#prod} -gt 23 ] && prod="${prod:0:20}..."
    
    status="$(cat "$d/power/runtime_status" 2>/dev/null || echo "unknown")"
    wake="$(cat "$d/power/wakeup" 2>/dev/null || echo "unknown")"

    if [ "$status" = "active" ]; then
      STATUS_STR="${GREEN}● active${RESET}"
    elif [ "$status" = "suspended" ]; then
      STATUS_STR="${YELLOW}○ suspended (RGB OFF)${RESET}"
    else
      STATUS_STR="${DIM}$status${RESET}"
    fi

    dev_type="Device"
    case "$id" in
      *8c02*) dev_type="Keyboard";;
      *1440*) dev_type="Mouse";;
    esac

    printf "  %-12s ${CYAN}%-12s${RESET} %-24s %-25b %-10s\n" "$dev_type" "$id" "$prod" "$STATUS_STR" "$wake"
  done

  if [ "$FOUND" -eq 0 ]; then
    echo -e "  ${YELLOW}No configured devices currently connected.${RESET}"
  fi
  echo ""
}

start_tray() {
  echo -e "${CYAN}${BOLD}[●] Launching Taskbar Tray Indicator...${RESET}"
  for pid in $(pgrep -f "python.*tray\.py" 2>/dev/null); do
    [ "$pid" != "$$" ] && kill -9 "$pid" 2>/dev/null
  done
  setsid nohup python3 "$DIR/tray.py" </dev/null >/dev/null 2>&1 &
  sleep 1
  if pgrep -f "python.*tray\.py" >/dev/null; then
    echo -e "  ${CHECK} ${GREEN}Tray indicator is now active on your taskbar!${RESET}"
  else
    echo -e "  ${CROSS} ${RED}Failed to launch tray indicator. Check Python dependencies.${RESET}"
  fi
}

toggle_lights() {
  elevate_if_needed "$@"

  [ -f "$CONF" ] || { 
    echo -e "${CROSS} ${RED}Missing configuration file: $CONF (copy devices.conf.example)${RESET}" >&2
    exit 1
  }

  declare -A WAKE
  while read -r id wake _; do
    case "$id" in ""|\#*) continue;; esac
    WAKE[$id]="${wake:-disabled}"
  done < "$CONF"

  ACTION="$1"
  if [ "$ACTION" = "off" ]; then
    echo -e "${YELLOW}${BOLD}[●] Turning OFF RGB lights (entering runtime suspend)...${RESET}"
  else
    echo -e "${GREEN}${BOLD}[●] Turning ON RGB lights (restoring normal power)...${RESET}"
  fi

  COUNT=0
  for d in /sys/bus/usb/devices/*; do
    [ -f "$d/idVendor" ] || continue
    id="$(cat "$d/idVendor"):$(cat "$d/idProduct")"
    [ -n "${WAKE[$id]}" ] || continue

    prod="$(cat "$d/product" 2>/dev/null || echo "USB Device")"

    if [ "$ACTION" = "off" ]; then
      echo 1              > "$d/authorized"
      echo "${WAKE[$id]}" > "$d/power/wakeup"
      echo 0              > "$d/power/autosuspend_delay_ms"
      echo auto           > "$d/power/control"
      echo -e "  ${CHECK} ${CYAN}$prod${RESET} ${DIM}($id)${RESET} ${ARROW} ${YELLOW}Suspended (RGB OFF)${RESET}"
    else
      echo on             > "$d/power/control"
      echo 1              > "$d/authorized"
      echo enabled        > "$d/power/wakeup"
      echo -e "  ${CHECK} ${CYAN}$prod${RESET} ${DIM}($id)${RESET} ${ARROW} ${GREEN}Active (RGB ON)${RESET}"
    fi
    ((COUNT++))
  done

  if [ "$COUNT" -eq 0 ]; then
    echo -e "  ${CROSS} ${YELLOW}No matching devices found from $CONF.${RESET}"
  else
    if [ "$ACTION" = "off" ]; then
      echo -e "${STAR} ${GREEN}${BOLD}Lights OFF.${RESET} ${DIM}Press any key or click mouse to wake them back up.${RESET}"
    else
      echo -e "${STAR} ${GREEN}${BOLD}Lights ON.${RESET} ${DIM}Normal power restored.${RESET}"
    fi
  fi
}

# Main Command Dispatcher
case "$1" in
  on|off)
    toggle_lights "$@"
    ;;
  status)
    show_status
    ;;
  tray)
    start_tray
    ;;
  help|--help|-h)
    show_help
    ;;
  "")
    show_help
    ;;
  *)
    echo -e "${RED}${BOLD}Unknown command: $1${RESET}\n"
    show_help
    exit 1
    ;;
esac
