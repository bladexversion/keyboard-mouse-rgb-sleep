#!/bin/bash
# ==============================================================================
#  ⚡ RGB-SLEEP UNINSTALLER
# ==============================================================================
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$DIR" || exit 1

# Terminal Colors & Styling
if [ -t 1 ]; then
  BOLD="\033[1m"
  DIM="\033[2m"
  CYAN="\033[0;36m"
  GREEN="\033[0;32m"
  YELLOW="\033[0;33m"
  RED="\033[0;31m"
  RESET="\033[0m"
else
  BOLD=""
  DIM=""
  CYAN=""
  GREEN=""
  YELLOW=""
  RED=""
  RESET=""
fi

CHECK="${GREEN}✔${RESET}"
CROSS="${RED}✖${RESET}"
BULLET="${CYAN}●${RESET}"

echo -e "\n${RED}${BOLD}╔═══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${RED}${BOLD}║              ⚡ RGB-SLEEP UNINSTALLER ⚡                  ║${RESET}"
echo -e "${RED}${BOLD}╚═══════════════════════════════════════════════════════════╝${RESET}\n"

# 1. Restore lights
echo -e "${BOLD}[1/4]${RESET} Restoring normal power mode to USB devices..."
if [ -f devices.conf ]; then
  ./lights.sh on >/dev/null 2>&1 || true
fi
echo -e "      ${CHECK} Normal power restored"

# 2. Stop and remove services
echo -e "${BOLD}[2/4]${RESET} Stopping and removing background service & tray..."
sudo systemctl disable --now wake-watch.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/wake-watch.service /etc/sudoers.d/rgb-sleep
sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl reset-failed wake-watch.service 2>/dev/null || true

for pid in $(pgrep -f "python.*tray\.py" 2>/dev/null); do
  [ "$pid" != "$$" ] && kill -9 "$pid" 2>/dev/null
done
echo -e "      ${CHECK} Services and sudoers rule removed"

# 3. Clean files
echo -e "${BOLD}[3/4]${RESET} Removing virtual environment and autostart files..."
rm -rf .venv __pycache__ devices.conf
rm -f "$HOME/.config/autostart/rgb-sleep-tray.desktop"
echo -e "      ${CHECK} Local environment and autostart removed"

# 4. Optional directory deletion
echo -e "\n${BOLD}[4/4]${RESET} Cleanup project folder:"
read -r -p "Delete the entire project folder ($DIR)? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  if [ -f "$DIR/lights.sh" ] && [ -f "$DIR/wake_watch.py" ] \
     && [ "$DIR" != "$HOME" ] && [ "$DIR" != "/" ]; then
    cd / && rm -rf -- "$DIR"
    echo -e "      ${CHECK} ${GREEN}Deleted $DIR${RESET}"
  else
    echo -e "      ${CROSS} ${RED}Refusing to delete $DIR (safety check failed)${RESET}"
  fi
else
  echo -e "      ${CHECK} Project folder kept at $DIR"
fi

echo -e "\n${GREEN}${BOLD}RGB-Sleep has been completely uninstalled.${RESET}\n"
