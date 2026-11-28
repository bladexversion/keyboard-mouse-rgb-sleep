#!/bin/bash
# ==============================================================================
#  ⚡ RGB-SLEEP UNINSTALLER (D-Bus Architecture, venv)
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

# 1. Restore lights via D-Bus
echo -e "${BOLD}[1/7]${RESET} Restoring normal power mode to USB devices..."
dbus-send --system --dest=org.rgb_sleep.Control --print-reply=literal /org/rgb_sleep/Control org.rgb_sleep.Control.LightsOn >/dev/null 2>&1 || true
echo -e "      ${CHECK} Normal power restored"

# 2. Stop and remove daemon service
echo -e "${BOLD}[2/7]${RESET} Stopping and removing D-Bus daemon service..."
sudo systemctl disable --now rgb-sleep-daemon.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/rgb-sleep-daemon.service
sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl reset-failed rgb-sleep-daemon.service 2>/dev/null || true
echo -e "      ${CHECK} Daemon service removed"

# 3. Remove D-Bus policy
echo -e "${BOLD}[3/7]${RESET} Removing D-Bus policy..."
sudo rm -f /etc/dbus-1/system.d/org.rgb_sleep.Control.conf
echo -e "      ${CHECK} D-Bus policy removed"

# 4. Remove config
echo -e "${BOLD}[4/7]${RESET} Removing configuration..."
sudo rm -rf /etc/rgb-sleep
echo -e "      ${CHECK} Config removed"

# 5. Remove virtual environment
echo -e "${BOLD}[5/7]${RESET} Removing virtual environment..."
rm -rf .venv
echo -e "      ${CHECK} Virtual environment removed"

# 6. Clean local files
echo -e "${BOLD}[6/7]${RESET} Removing autostart and local files..."
rm -f "$HOME/.config/autostart/rgb-sleep-tray.desktop"
rm -rf __pycache__ devices.conf build dist *.egg-info

# Kill tray
for pid in $(pgrep -f "rgb-sleep-tray" 2>/dev/null); do
  [ "$pid" != "$$" ] && kill -9 "$pid" 2>/dev/null
done
echo -e "      ${CHECK} Local files removed"

# Optional directory deletion
echo -e "\n${BOLD}[7/7]${RESET} Cleanup project folder:"
read -r -p "Delete the entire project folder ($DIR)? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  if [ -f "$DIR/pyproject.toml" ] && [ -f "$DIR/rgb_sleep/daemon.py" ] \
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