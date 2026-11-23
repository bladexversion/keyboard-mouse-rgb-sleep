#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
[ -d .venv ] || python3 -m venv .venv
[ -f devices.conf ] || cp devices.conf.example devices.conf
chmod +x lights.sh wake_watch.py uninstall.sh tray.py
sudo tee /etc/systemd/system/wake-watch.service >/dev/null << UNIT
[Unit]
Description=Turn keyboard/mouse RGB back on when they wake

[Service]
ExecStart=$DIR/.venv/bin/python $DIR/wake_watch.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now wake-watch.service
sudo systemctl restart wake-watch.service

mkdir -p "$HOME/.config/autostart"
cp "$DIR/rgb-sleep-tray.desktop" "$HOME/.config/autostart/rgb-sleep-tray.desktop" 2>/dev/null || true

# Start or restart tray icon in background
pkill -f "$DIR/tray.py" 2>/dev/null || true
if [ -n "$DISPLAY" ]; then
  nohup python3 "$DIR/tray.py" >/dev/null 2>&1 &
fi

echo "installed. try: $DIR/lights.sh off"
