#!/usr/bin/env python3
"""D-Bus daemon for rgb-sleep: USB suspend + HID RGB control + wake monitor."""
import os
import sys
import glob
import fcntl
from gi.repository import GLib
import dbus
import dbus.service
import dbus.mainloop.glib

DBUS_NAME = "org.rgb_sleep.Control"
DBUS_PATH = "/org/rgb_sleep/Control"
CONF_PATH = os.environ.get("RGB_SLEEP_CONF", "/etc/rgb-sleep/devices.conf")

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)


def load_ids(path):
    ids = {}
    try:
        with open(path) as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    ids[parts[0]] = parts[1] == "enabled"
                else:
                    ids[parts[0]] = True
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
        key = f"{vid}:{pid}"
        if key in ids:
            devices.append((d, key, ids[key]))
    return devices


def get_hidraw_for_device(dev_path):
    try:
        for i in range(20):
            uevent_path = f"/sys/class/hidraw/hidraw{i}/device/uevent"
            if not os.path.exists(uevent_path):
                continue
            with open(uevent_path) as f:
                content = f.read()
            vid_line = [l for l in content.split('\n') if l.startswith('HID_ID=')]
            if vid_line:
                hid_id = vid_line[0].split('=')[1]
                if len(hid_id) >= 10:
                    hid_vid = hid_id[5:9]
                    hid_pid = hid_id[10:14]
                    try:
                        our_vid = open(dev_path + "/idVendor").read().strip()
                        our_pid = open(dev_path + "/idProduct").read().strip()
                        if hid_vid == our_vid.lower() and hid_pid == our_pid.lower():
                            return f"/dev/hidraw{i}"
                    except:
                        pass
    except Exception:
        pass
    return None


def hid_send_feature_report(hidraw_path, report):
    try:
        fd = os.open(hidraw_path, os.O_RDWR)
        fcntl.ioctl(fd, 0x40044806, bytearray(report))
        os.close(fd)
        return True
    except Exception:
        return False


def keyboard_rgb_off(hidraw_path):
    """Try common RGB-off report IDs for gaming keyboards."""
    if not hidraw_path:
        return False
    # Common report IDs for RGB control (SEMICO/OEM keyboards)
    attempts = [
        # Report 0x09 - common for RGB mode/brightness
        [0x09, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x09, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x09, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x09, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x0A
        [0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x0B - brightness
        [0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x0B, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x08
        [0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x07
        [0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x06
        [0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x05
        [0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x04
        [0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x03
        [0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x02
        [0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        # Report 0x01
        [0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    ]
    for report in attempts:
        if hid_send_feature_report(hidraw_path, report):
            return True
    return False


def keyboard_rgb_on(hidraw_path):
    """Try common RGB-on report IDs."""
    if not hidraw_path:
        return False
    attempts = [
        [0x09, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x09, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x0A, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x0B, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x0B, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x08, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        [0x07, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    ]
    for report in attempts:
        if hid_send_feature_report(hidraw_path, report):
            return True
    return False


def set_power(dev_path, on):
    ctrl = dev_path + "/power/control"
    wake = dev_path + "/power/wakeup"
    auth = dev_path + "/authorized"
    autosuspend = dev_path + "/power/autosuspend_delay_ms"
    try:
        if on:
            open(ctrl, "w").write("on\n")
            open(auth, "w").write("1\n")
            open(wake, "w").write("enabled\n")
        else:
            open(ctrl, "w").write("auto\n")
            open(auth, "w").write("1\n")
            open(wake, "w").write("enabled\n")
            open(autosuspend, "w").write("0\n")
        return True
    except OSError:
        return False


def get_status(dev_path):
    try:
        status = open(dev_path + "/power/runtime_status").read().strip()
        return status
    except OSError:
        return "unknown"


def get_active_time(dev_path):
    try:
        t = open(dev_path + "/power/runtime_active_time").read().strip()
        return int(t)
    except OSError:
        return 0


def snapshot_active_times(devices):
    snap = {}
    for d, key, can_wake in devices:
        status = get_status(d)
        if status == "suspended":
            snap[d] = get_active_time(d)
    return snap


class RgbSleepDaemon(dbus.service.Object):
    def __init__(self):
        bus = dbus.SystemBus()
        name = dbus.service.BusName(DBUS_NAME, bus)
        super().__init__(name, DBUS_PATH)
        self.ids = load_ids(CONF_PATH)
        self.keyboard_hidraw = None
        for d, key, _ in find_devices(self.ids):
            if key == "1a2c:8c02":
                self.keyboard_hidraw = get_hidraw_for_device(d)
                if self.keyboard_hidraw:
                    print(f"Keyboard hidraw: {self.keyboard_hidraw}", flush=True)

        self.prev_suspended = {}
        self.start_wake_monitor()

    def start_wake_monitor(self):
        def check_wake():
            devices = find_devices(self.ids)
            cur_suspended = snapshot_active_times(devices)
            for d, prev_time in self.prev_suspended.items():
                cur_time = cur_suspended.get(d)
                if cur_time is not None and cur_time > prev_time:
                    print(f"Wake detected on {os.path.basename(d)}", flush=True)
                    self.wake_all()
                    break
            self.prev_suspended = cur_suspended
            return True
        GLib.timeout_add(200, check_wake)

    def wake_all(self):
        for dev_path, key, _ in find_devices(self.ids):
            if key == "1a2c:8c02":
                if self.keyboard_hidraw:
                    keyboard_rgb_on(self.keyboard_hidraw)
                set_power(dev_path, True)
            else:
                set_power(dev_path, True)

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="b")
    def LightsOff(self):
        ok = True
        for dev_path, key, can_wake in find_devices(self.ids):
            if key == "1a2c:8c02":
                if self.keyboard_hidraw:
                    hid_ok = keyboard_rgb_off(self.keyboard_hidraw)
                    if hid_ok:
                        print("Keyboard RGB off via HID", flush=True)
                    else:
                        print("Keyboard HID RGB off failed, trying USB suspend", flush=True)
                        if not set_power(dev_path, False):
                            ok = False
                else:
                    if not set_power(dev_path, False):
                        ok = False
            elif key == "30fa:1440":
                if not set_power(dev_path, False):
                    ok = False
            else:
                if not set_power(dev_path, False):
                    ok = False
        return ok

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="b")
    def LightsOn(self):
        ok = True
        for dev_path, key, _ in find_devices(self.ids):
            if key == "1a2c:8c02":
                if self.keyboard_hidraw:
                    keyboard_rgb_on(self.keyboard_hidraw)
                set_power(dev_path, True)
            elif key == "30fa:1440":
                if not set_power(dev_path, True):
                    ok = False
            else:
                if not set_power(dev_path, True):
                    ok = False
        return ok

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="a{sv}")
    def Status(self):
        result = {"devices": [], "watcher": "active"}
        for d, key, _ in find_devices(self.ids):
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
    print("rgb-sleep daemon started (USB suspend + HID RGB + wake monitor)", flush=True)
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()