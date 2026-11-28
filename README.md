# rgb-sleep

Turn off keyboard/mouse RGB on Linux without suspending the PC, by putting the
USB devices into runtime suspend. Any key press or click wakes them and the
lights come back on.

## Architecture (v2)

- **D-Bus daemon** (`rgb-sleep-daemon.service`) runs as root at boot, holds permission to control USB power
- **CLI & Tray** are unprivileged clients that talk to the daemon via system D-Bus
- **No sudo/password prompts** — one-time install, then quiet forever
- **Event-driven** — daemon responds instantly, no polling loop

## Setup

1. `lsusb` and find your keyboard/mouse IDs (`vendor:product`).
2. `cp devices.conf.example devices.conf` and edit it (defaults: Semico keyboard & Fantech mouse).
3. `./install.py` — installs Python package, systemd daemon, D-Bus policy, config, and tray autostart.

## Use

- `rgb-sleep off` — Turn off RGB lights immediately
- `rgb-sleep on` — Turn on RGB lights
- `rgb-sleep status` — View live power status of devices & daemon
- `rgb-sleep-tray` — Launch/restart the taskbar tray indicator
- Check daemon logs: `journalctl -u rgb-sleep-daemon -n 20`

## Uninstall

`./uninstall.sh` restores lights, removes systemd service, D-Bus policy, config, Python package, and autostart.

## Warning

If your keyboard cannot wake itself from USB suspend, you can lock yourself out
until you replug it. Test with an auto-restore first:
`rgb-sleep off && sleep 20 && rgb-sleep on`