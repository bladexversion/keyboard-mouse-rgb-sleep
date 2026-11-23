#!/bin/bash
# Removes everything rgb-sleep installed: the systemd service, the venv,
# the local config, and (optionally) the project folder itself.
set -u
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
cd "$DIR" || exit 1

# Get sudo up front, so it can't ask for a password while a device is asleep
sudo -v || exit 1

# 1. Put keyboard/mouse back in normal power mode so nothing stays suspended
if [ -f devices.conf ]; then
  ./lights.sh on || true
fi

# 2. Stop and remove the service
sudo systemctl disable --now wake-watch.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/wake-watch.service /etc/sudoers.d/rgb-sleep
sudo systemctl daemon-reload
sudo systemctl reset-failed wake-watch.service 2>/dev/null || true

# 3. Remove everything the install created or downloaded
rm -rf .venv __pycache__ devices.conf
rm -f "$HOME/.config/autostart/rgb-sleep-tray.desktop"
echo "Service, venv and local config removed."

# 4. Optionally delete the project folder itself (including .git)
read -r -p "Also delete this project folder ($DIR)? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  if [ -f "$DIR/lights.sh" ] && [ -f "$DIR/wake_watch.py" ] \
     && [ "$DIR" != "$HOME" ] && [ "$DIR" != "/" ]; then
    cd / && rm -rf -- "$DIR"
    echo "Deleted $DIR"
  else
    echo "Refusing to delete $DIR (doesn't look like the project folder)"
  fi
fi
