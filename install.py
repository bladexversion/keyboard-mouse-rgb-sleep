#!/usr/bin/env python3
"""
⚡ RGB-SLEEP INSTALLER
Installs systemd background watcher, passwordless sudo rules, and taskbar tray icon.
"""
import os
import shutil
import subprocess
import sys
import time

DIR = os.path.dirname(os.path.realpath(__file__))
CONF = os.path.join(DIR, "devices.conf")
CONF_EX = os.path.join(DIR, "devices.conf.example")
LIGHTS = os.path.join(DIR, "lights.sh")
TRAY = os.path.join(DIR, "tray.py")
DESKTOP_SRC = os.path.join(DIR, "rgb-sleep-tray.desktop")

# Terminal Styling
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
MAGENTA = "\033[0;35m"
RESET = "\033[0m"

CHECK = f"{GREEN}✔{RESET}"
CROSS = f"{RED}✖{RESET}"
BULLET = f"{CYAN}●{RESET}"


def print_banner():
    print(f"\n{CYAN}{BOLD}╔═══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║               ⚡ RGB-SLEEP INSTALLER ⚡                   ║{RESET}")
    print(f"{CYAN}{BOLD}║       Turn off USB RGB lights without PC suspend          ║{RESET}")
    print(f"{CYAN}{BOLD}╚═══════════════════════════════════════════════════════════╝{RESET}\n")


def get_real_user():
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    return os.environ.get("USER", "aravsun")


def run_as_user(user, cmd):
    if os.geteuid() == 0 and user != "root":
        return subprocess.run(["sudo", "-u", user] + cmd, capture_output=True, text=True)
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    # Require root for installing systemd and sudoers configuration
    if os.geteuid() != 0:
        print(f"{YELLOW}{BOLD}⚡ Administrator privileges required for installation.{RESET}")
        print(f"{DIM}Re-running with sudo...{RESET}\n")
        args = ["sudo", sys.executable] + sys.argv
        os.execvp("sudo", args)

    print_banner()

    user = get_real_user()
    home = os.path.expanduser(f"~{user}")

    # 1. Virtual Environment
    print(f"{BOLD}[1/6]{RESET} Setting up Python virtual environment...")
    venv_dir = os.path.join(DIR, ".venv")
    if not os.path.isdir(venv_dir):
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        # Ensure correct ownership
        subprocess.run(["chown", "-R", f"{user}:{user}", venv_dir], check=False)
        print(f"      {CHECK} Created {CYAN}.venv/{RESET}")
    else:
        print(f"      {CHECK} Virtual environment already exists")

    # 2. Configuration file
    print(f"{BOLD}[2/6]{RESET} Checking device configuration...")
    if not os.path.exists(CONF):
        if os.path.exists(CONF_EX):
            shutil.copyfile(CONF_EX, CONF)
            subprocess.run(["chown", f"{user}:{user}", CONF], check=False)
            print(f"      {CHECK} Created {CYAN}devices.conf{RESET} (from template)")
        else:
            print(f"      {CROSS} {RED}Template devices.conf.example missing!{RESET}")
    else:
        print(f"      {CHECK} Configuration {CYAN}devices.conf{RESET} found")

    # 3. Executable permissions
    print(f"{BOLD}[3/6]{RESET} Setting executable permissions on scripts...")
    for script in ["lights.sh", "wake_watch.py", "uninstall.sh", "tray.py", "install.py", "install.sh"]:
        p = os.path.join(DIR, script)
        if os.path.exists(p):
            os.chmod(p, 0o755)
    print(f"      {CHECK} Permissions set (755)")

    # 4. Systemd Background Watcher
    print(f"{BOLD}[4/6]{RESET} Configuring background watcher service (systemd)...")
    service_content = f"""[Unit]
Description=Turn keyboard/mouse RGB back on when they wake

[Service]
ExecStart={venv_dir}/bin/python {DIR}/wake_watch.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
"""
    service_path = "/etc/systemd/system/wake-watch.service"
    with open(service_path, "w") as f:
        f.write(service_content)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "--now", "wake-watch.service"], check=True)
    subprocess.run(["systemctl", "restart", "wake-watch.service"], check=True)
    print(f"      {CHECK} Enabled & started {GREEN}wake-watch.service{RESET}")

    # 5. Sudoers rule for passwordless execution
    print(f"{BOLD}[5/6]{RESET} Setting up passwordless rule for lights toggle...")
    sudoers_rule = (
        f"{user} ALL=(ALL) NOPASSWD: {LIGHTS}, "
        f"/bin/systemctl restart wake-watch.service, /usr/bin/systemctl restart wake-watch.service\n"
    )
    sudoers_path = "/etc/sudoers.d/rgb-sleep"
    with open(sudoers_path, "w") as f:
        f.write(sudoers_rule)
    os.chmod(sudoers_path, 0o440)
    print(f"      {CHECK} Configured {CYAN}/etc/sudoers.d/rgb-sleep{RESET}")

    # 6. Taskbar Tray Indicator & Autostart
    print(f"{BOLD}[6/6]{RESET} Setting up Taskbar Tray Indicator...")
    autostart_dir = os.path.join(home, ".config", "autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    target_desktop = os.path.join(autostart_dir, "rgb-sleep-tray.desktop")
    if os.path.exists(DESKTOP_SRC):
        shutil.copyfile(DESKTOP_SRC, target_desktop)
        subprocess.run(["chown", f"{user}:{user}", target_desktop], check=False)
        print(f"      {CHECK} Added to login autostart ({CYAN}~/.config/autostart/{RESET})")

    # Ensure XFCE tray whitelist allows rgb-sleep-indicator
    try:
        visible_res = run_as_user(user, ["xfconf-query", "-c", "xfce4-panel", "-p", "/plugins/plugin-8/names-visible", "-a"])
        items = [line.strip() for line in visible_res.stdout.splitlines() if line.strip() and not line.startswith("Value")]
        if "rgb-sleep-indicator" not in items:
            items.append("rgb-sleep-indicator")
            args = ["xfconf-query", "-c", "xfce4-panel", "-p", "/plugins/plugin-8/names-visible", "-a"]
            for item in items:
                args.extend(["-t", "string", "-s", item])
            run_as_user(user, args)
            run_as_user(user, ["xfce4-panel", "-r"])
    except Exception:
        pass

    # Launch tray process as the desktop user
    try:
        # Kill any old instances
        res = subprocess.run(["pgrep", "-f", "python.*tray\\.py"], capture_output=True, text=True)
        for pid_str in res.stdout.split():
            try:
                pid = int(pid_str)
                if pid != os.getpid():
                    os.kill(pid, 9)
            except Exception:
                pass

        display = os.environ.get("DISPLAY", ":0.0")
        env = {
            "DISPLAY": display,
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": home,
            "USER": user,
        }
        cmd = ["sudo", "-u", user, "-E", "setsid", "python3", TRAY]
        subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        time.sleep(1)
        print(f"      {CHECK} Taskbar tray icon started {GREEN}(⌨ visible in system tray){RESET}")
    except Exception as e:
        print(f"      {YELLOW}Note starting tray: {e}{RESET}")

    # Success Card
    print(f"\n{GREEN}{BOLD}═══════════════════════════════════════════════════════════{RESET}")
    print(f"  {CHECK} {GREEN}{BOLD}Installation successfully completed!{RESET}")
    print(f"{GREEN}{BOLD}═══════════════════════════════════════════════════════════{RESET}\n")

    print(f"{BOLD}Quick Commands:{RESET}")
    print(f"  {CYAN}./lights.sh off{RESET}     Turn off keyboard/mouse RGB lights")
    print(f"  {CYAN}./lights.sh on{RESET}      Turn on RGB lights")
    print(f"  {CYAN}./lights.sh status{RESET}  View live status of devices & services")
    print(f"  {CYAN}./lights.sh tray{RESET}    Launch or reload taskbar tray icon\n")


if __name__ == "__main__":
    main()
