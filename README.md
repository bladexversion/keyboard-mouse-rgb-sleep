# rgb-sleep

Turn off keyboard/mouse RGB on Linux without suspending the PC, by putting the
USB devices into runtime suspend. Any key press or click wakes them and the
lights come back on.

## Setup
1. `lsusb` and find your keyboard/mouse IDs (`vendor:product`).
2. `cp devices.conf.example devices.conf` and edit it.
3. `./install.sh` (creates a venv and a systemd service that runs the watcher).

## Use
- `./lights.sh off`: lights off
- `./lights.sh on`: lights on
- `./tray.py`: run the system tray indicator in your taskbar
- Check the watcher: `journalctl -u wake-watch -n 20`

## Uninstall
`./uninstall.sh` restores the devices to normal power mode, removes the systemd
service, the venv and your local config, then asks whether to delete the whole
project folder.

## Warning
If your keyboard cannot wake itself from USB suspend, you can lock yourself out
until you replug it. Test with an auto-restore first, for example:
`./lights.sh off; sleep 20; ./lights.sh on`
