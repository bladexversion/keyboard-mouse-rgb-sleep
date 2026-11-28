#!/usr/bin/env python3
"""CLI entry point for rgb-sleep."""
import subprocess
import sys

DBUS_NAME = "org.rgb_sleep.Control"
DBUS_PATH = "/org/rgb_sleep/Control"


def dbus_call(method):
    cmd = f"dbus-send --system --dest={DBUS_NAME} --print-reply=literal {DBUS_PATH} {DBUS_NAME}.{method}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def dbus_call_bool(method):
    result = dbus_call(method)
    return "true" in result.lower()


def main():
    if len(sys.argv) < 2:
        print("Usage: rgb-sleep <on|off|status>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "off":
        print("Turning OFF RGB lights...")
        if dbus_call_bool("LightsOff"):
            print("Lights OFF. Press any key or click mouse to wake.")
        else:
            print("Failed to contact daemon")
            sys.exit(1)

    elif cmd == "on":
        print("Turning ON RGB lights...")
        if dbus_call_bool("LightsOn"):
            print("Lights ON. Normal power restored.")
        else:
            print("Failed to contact daemon")
            sys.exit(1)

    elif cmd == "status":
        result = dbus_call("Status")
        if result and "Error" not in result:
            print("Daemon connected")
            print(result)
        else:
            print("Daemon not running")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()