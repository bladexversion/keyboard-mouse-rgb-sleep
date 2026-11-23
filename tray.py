#!/usr/bin/env python3
"""System tray indicator for rgb-sleep in XFCE and other desktop environments."""
import os
import signal
import subprocess
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, GLib, Gtk

DIR = os.path.dirname(os.path.realpath(__file__))
LIGHTS = os.path.join(DIR, "lights.sh")
SERVICE_NAME = "wake-watch.service"

ICON_ACTIVE = "input-keyboard-symbolic"
ICON_INACTIVE = "dialog-information-symbolic"


def is_service_active():
    try:
        res = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True,
            text=True,
            check=False,
        )
        return res.stdout.strip() == "active"
    except Exception:
        return False


def run_command_privileged(cmd):
    """Runs a command, using pkexec if sudo would prompt for a password."""
    try:
        if os.geteuid() == 0:
            full_cmd = cmd
        else:
            # Check if passwordless sudo is available
            test_sudo = subprocess.run(["sudo", "-n", "true"], capture_output=True)
            if test_sudo.returncode == 0:
                full_cmd = ["sudo"] + cmd
            else:
                full_cmd = ["pkexec"] + cmd
        subprocess.Popen(full_cmd)
    except Exception as e:
        subprocess.run(["notify-send", "RGB Sleep Error", str(e)])


class RgbSleepTray:
    def __init__(self):
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "rgb-sleep-indicator",
            ICON_ACTIVE,
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("RGB Sleep")

        self.menu = Gtk.Menu()

        # Status Header (non-clickable indicator)
        self.status_item = Gtk.MenuItem(label="Checking status...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # Action: Lights Off
        self.off_item = Gtk.MenuItem(label="💡 Turn Lights Off")
        self.off_item.connect("activate", self.on_lights_off)
        self.menu.append(self.off_item)

        # Action: Lights On
        self.on_item = Gtk.MenuItem(label="💡 Turn Lights On")
        self.on_item.connect("activate", self.on_lights_on)
        self.menu.append(self.on_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # Action: Toggle Watcher Service
        self.toggle_service_item = Gtk.MenuItem(label="Restart Watcher Service")
        self.toggle_service_item.connect("activate", self.on_restart_service)
        self.menu.append(self.toggle_service_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # Action: Quit
        self.quit_item = Gtk.MenuItem(label="Quit Tray Icon")
        self.quit_item.connect("activate", self.on_quit)
        self.menu.append(self.quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        # Initial check and periodic polling every 2 seconds
        self.update_status()
        GLib.timeout_add_seconds(2, self.update_status)

    def update_status(self):
        active = is_service_active()
        if active:
            self.indicator.set_icon_full(ICON_ACTIVE, "RGB Sleep Watcher Active")
            self.status_item.set_label("🟢 Watcher: Active")
        else:
            self.indicator.set_icon_full(ICON_INACTIVE, "RGB Sleep Watcher Stopped")
            self.status_item.set_label("🔴 Watcher: Inactive")
        return True

    def on_lights_off(self, _widget):
        run_command_privileged([LIGHTS, "off"])

    def on_lights_on(self, _widget):
        run_command_privileged([LIGHTS, "on"])

    def on_restart_service(self, _widget):
        run_command_privileged(["systemctl", "restart", SERVICE_NAME])
        GLib.timeout_add_seconds(1, self.update_status)

    def on_quit(self, _widget):
        Gtk.main_quit()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    RgbSleepTray()
    Gtk.main()


if __name__ == "__main__":
    main()
