#!/usr/bin/env python3
"""D-Bus daemon for rgb-sleep: runs as root, controls USB power."""
import os
import sys
import glob
import subprocess
from gi.repository import GLib
import dbus
import dbus.service
import dbus.mainloop.glib

DBUS_NAME = "org.rgb_sleep.Control"
DBUS_PATH = "/org/rgb_sleep/Control"
CONF_PATH = os.environ.get("RGB_SLEEP_CONF", "/etc/rgb-sleep/devices.conf")

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


def load_ids(path):
    ids = set()
    try:
        with open(path) as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    ids.add(line.split()[0])
    except FileNotFoundError:
        pass
    return ids


def find_devices(ids):
    devices = []
    for d in glob.glob("/sys/bus/usb/devices/*"):
        try:
            vid = open(d + "/idVendor").read().strip()
            pid = open(d + "/idProduct").read().strip()
        except OSError:
            continue
        if f"{vid}:{pid}" in ids:
            devices.append(d)
    return devices


def set_power(dev_path, on):
    ctrl = dev_path + "/power/control"
    wake = dev_path + "/power/wakeup"
    auth = dev_path + "/authorized"
    try:
        if on:
            open(ctrl, "w").write("on\n")
            open(auth, "w").write("1\n")
            open(wake, "w").write("enabled\n")
        else:
            open(ctrl, "w").write("auto\n")
            open(auth, "w").write("1\n")
            open(wake, "w").write("enabled\n")
        return True
    except OSError:
        return False


def get_status(dev_path):
    try:
        status = open(dev_path + "/power/runtime_status").read().strip()
        return status
    except OSError:
        return "unknown"


class RgbSleepDaemon(dbus.service.Object):
    def __init__(self):
        bus = dbus.SystemBus()
        name = dbus.service.BusName(DBUS_NAME, bus)
        super().__init__(name, DBUS_PATH)
        self.ids = load_ids(CONF_PATH)

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="b")
    def LightsOff(self):
        ok = True
        for d in find_devices(self.ids):
            if not set_power(d, False):
                ok = False
        return ok

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="b")
    def LightsOn(self):
        ok = True
        for d in find_devices(self.ids):
            if not set_power(d, True):
                ok = False
        return ok

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="a{sv}")
    def Status(self):
        result = {"devices": [], "watcher": "active"}
        for d in find_devices(self.ids):
            try:
                vid = open(d + "/idVendor").read().strip()
                pid = open(d + "/idProduct").read().strip()
                prod = open(d + "/product").read().strip()
            except OSError:
                continue
            result["devices"].append({
                "id": f"{vid}:{pid}",
                "product": prod,
                "path": d,
                "status": get_status(d),
            })
        return result


def main():
    if os.geteuid() != 0:
        print("Must run as root", file=sys.stderr)
        sys.exit(1)

    daemon = RgbSleepDaemon()
    print("rgb-sleep daemon started", flush=True)
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()