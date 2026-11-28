#!/usr/bin/env python3
"""System tray indicator for rgb-sleep (D-Bus client)."""
import os
import signal
import sys

try:
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
except Exception:
    pass

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3, GLib, Gtk

import dbus
import dbus.mainloop.glib

DBUS_NAME = "org.rgb_sleep.Control"
DBUS_PATH = "/org/rgb_sleep/Control"

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

ICON_ACTIVE = "input-keyboard-symbolic"
ICON_INACTIVE = "dialog-information-symbolic"


def get_dbus_proxy():
    try:
        bus = dbus.SystemBus()
        obj = bus.get_object(DBUS_NAME, DBUS_PATH)
        return dbus.Interface(obj, DBUS_NAME)
    except Exception:
        return None


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

        self.status_item = Gtk.MenuItem(label="Connecting to daemon...")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        self.off_item = Gtk.MenuItem(label="💡 Turn Lights Off")
        self.off_item.connect("activate", self.on_lights_off)
        self.menu.append(self.off_item)

        self.on_item = Gtk.MenuItem(label="💡 Turn Lights On")
        self.on_item.connect("activate", self.on_lights_on)
        self.menu.append(self.on_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        # Device status submenu
        self.devices_item = Gtk.MenuItem(label="📱 Devices")
        self.devices_menu = Gtk.Menu()
        self.devices_item.set_submenu(self.devices_menu)
        self.menu.append(self.devices_item)

        self.menu.append(Gtk.SeparatorMenuItem())

        self.quit_item = Gtk.MenuItem(label="❌ Exit")
        self.quit_item.connect("activate", self.on_quit)
        self.menu.append(self.quit_item)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        self.proxy = None
        self.connect_dbus()
        GLib.timeout_add_seconds(2, self.update_status)

    def connect_dbus(self):
        self.proxy = get_dbus_proxy()
        if self.proxy:
            self.status_item.set_label("🟢 Daemon connected")
        else:
            self.status_item.set_label("🔴 Daemon not running")
        return True

    def update_status(self):
        if not self.proxy:
            self.connect_dbus()
            return True

        try:
            status = self.proxy.Status()
            devices = status.get("devices", [])
            watcher = status.get("watcher", "unknown")

            # Update main status
            if watcher == "active":
                self.indicator.set_icon_full(ICON_ACTIVE, "RGB Sleep Active")
                self.status_item.set_label("🟢 Daemon active")
            else:
                self.indicator.set_icon_full(ICON_INACTIVE, "RGB Sleep Inactive")
                self.status_item.set_label("🔴 Daemon inactive")

            # Update devices submenu
            self.devices_menu.foreach(lambda w: self.devices_menu.remove(w))
            for dev in devices:
                dev_id = dev.get("id", "unknown")
                product = dev.get("product", "unknown")
                status = dev.get("status", "unknown")
                if status == "active":
                    label = f"🟢 {product} ({dev_id})"
                elif status == "suspended":
                    label = f"🟡 {product} ({dev_id}) - suspended"
                else:
                    label = f"⚪ {product} ({dev_id}) - {status}"
                item = Gtk.MenuItem(label=label)
                item.set_sensitive(False)
                self.devices_menu.append(item)
            self.devices_menu.show_all()

        except Exception as e:
            self.status_item.set_label(f"🔴 Error: {e}")

        return True

    def on_lights_off(self, _widget):
        if self.proxy:
            try:
                self.proxy.LightsOff()
                self.status_item.set_label("🟢 Lights OFF")
            except Exception as e:
                self.status_item.set_label(f"🔴 Error: {e}")

    def on_lights_on(self, _widget):
        if self.proxy:
            try:
                self.proxy.LightsOn()
                self.status_item.set_label("🟢 Lights ON")
            except Exception as e:
                self.status_item.set_label(f"🔴 Error: {e}")

    def on_quit(self, _widget):
        if self.proxy:
            try:
                self.proxy.LightsOn()
            except Exception:
                pass
        Gtk.main_quit()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    RgbSleepTray()
    Gtk.main()


if __name__ == "__main__":
    main()