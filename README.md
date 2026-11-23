# rgb-sleep

Turn off keyboard/mouse RGB on Linux without suspending the PC, by putting the
USB devices into runtime suspend. Any key press or click wakes them and the
lights come back on.

## Setup
1. `lsusb` and find your keyboard/mouse IDs (`vendor:product`).
2. `cp devices.conf.example devices.conf` and edit it (defaults already matchSemico keyboard & Fantech mouse).
3. `./install.py` (or `./install.sh`): Sets up background watcher, taskbar tray icon, and passwordless execution.

## Use
- `./lights.sh off`: Turn off RGB lights immediately
- `./lights.sh on`: Turn on RGB lights
- `./lights.sh status`: View live power status of devices, watcher daemon, and tray icon
- `./lights.sh tray`: Launch or restart the taskbar tray indicator
- Check the watcher logs: `journalctl -u wake-watch -n 20`

## Uninstall
`./uninstall.sh` restores the devices to normal power mode, removes the systemd
service, the venv and your local config, then asks whether to delete the whole
project folder.

## Warning
If your keyboard cannot wake itself from USB suspend, you can lock yourself out
until you replug it. Test with an auto-restore first, for example:
`./lights.sh off; sleep 20; ./lights.sh on`
