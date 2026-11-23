#!/usr/bin/env python3
"""Turn RGB back on when the keyboard or mouse wakes from suspend."""
import glob, os, subprocess, sys, time

DIR = os.path.dirname(os.path.realpath(__file__))
CONF = os.environ.get("RGB_SLEEP_CONF", os.path.join(DIR, "devices.conf"))
LIGHTS = os.path.join(DIR, "lights.sh")

def load_ids(path):
    ids = set()
    with open(path) as f:
        for line in f:
            line = line.split("#", 1)[0].strip()
            if line:
                ids.add(line.split()[0])
    return ids

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None

def snapshot(ids):
    snap = {}
    for d in glob.glob("/sys/bus/usb/devices/*"):
        vid, pid = read(d + "/idVendor"), read(d + "/idProduct")
        if vid is None or pid is None or f"{vid}:{pid}" not in ids:
            continue
        status = read(d + "/power/runtime_status")
        t = read(d + "/power/runtime_active_time")
        if status is None or t is None:
            continue
        snap[d] = (status, int(t))
    return snap

def main():
    ids = load_ids(CONF)
    prev = snapshot(ids)
    if not prev:
        sys.exit("no configured devices found, or runtime_active_time is missing")
    print("watching:", sorted(os.path.basename(d) for d in prev), flush=True)
    while True:
        time.sleep(0.2)
        cur = snapshot(ids)
        woke = [d for d, (s, t) in cur.items()
                if d in prev and prev[d][0] == "suspended" and t > prev[d][1]]
        if woke:
            print("woke:", [os.path.basename(d) for d in woke], flush=True)
            subprocess.run([LIGHTS, "on"])
            time.sleep(1)
            cur = snapshot(ids)
        prev = cur

if __name__ == "__main__":
    main()
