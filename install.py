#!/usr/bin/env python3
"""
⚡ RGB-SLEEP INSTALLER (D-Bus Architecture)
Installs Python package in venv, systemd D-Bus daemon, D-Bus policy, config, and tray.
No sudoers needed — daemon runs as root, clients talk via D-Bus.
"""
import os
import shutil
import subprocess
import sys
import time

DIR = os.path.dirname(os.path.realpath(__file__))
CONF = os.path.join(DIR, "devices.conf")
CONF_EX = os.path.join(DIR, "devices.conf.example")
DESKTOP_SRC = os.path.join(DIR, "rgb-sleep-tray.desktop")
DBUS_POLICY = os.path.join(DIR, "org.rgb_sleep.Control.conf")
DAEMON_SERVICE = os.path.join(DIR, "rgb-sleep-daemon.service")

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
    print(f"{CYAN}{BOLD}║       D-Bus daemon architecture — no sudo required        ║{RESET}")
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
    if os.geteuid() != 0:
        print(f"{YELLOW}{BOLD}⚡ Administrator privileges required for installation.{RESET}")
        print(f"{DIM}Re-running with sudo...{RESET}\n")
        args = ["sudo", sys.executable] + sys.argv
        os.execvp("sudo", args)

    print_banner()

    user = get_real_user()
    home = os.path.expanduser(f"~{user}")
    venv_dir = os.path.join(DIR, ".venv")
    venv_python = os.path.join(venv_dir, "bin", "python")
    venv_bin = os.path.join(venv_dir, "bin")

    # 0. Install system dependencies
    print(f"{BOLD}[0/7]{RESET} Installing system dependencies...")
    subprocess.run(["apt-get", "update"], check=False)
    subprocess.run(["apt-get", "install", "-y", "python3-dbus", "python3-gi", "gir1.2-ayatanaappindicator3-0.1"], check=True)
    print(f"      {CHECK} System dependencies installed")

# 1. Create virtual environment
    print(f"{BOLD}[1/7]{RESET} Creating virtual environment...")
    if not os.path.isdir(venv_dir):
        subprocess.run([sys.executable, "-m", "venv", venv_dir, "--system-site-packages"], check=True)
        subprocess.run(["chown", "-R", f"{user}:{user}", venv_dir], check=False)
        print(f"      {CHECK} Created {CYAN}.venv/{RESET} (with system site packages)")
    else:
        print(f"      {CHECK} Virtual environment exists")

    # Install package in venv
    print(f"      {BOLD}Installing package in venv...{RESET}")
    subprocess.run([venv_python, "-m", "pip", "install", "-e", DIR], check=True)
    print(f"      {CHECK} Package installed in venv")

    # 2. Configuration directory & file
    print(f"{BOLD}[2/7]{RESET} Setting up configuration...")
    etc_conf_dir = "/etc/rgb-sleep"
    os.makedirs(etc_conf_dir, exist_ok=True)
    target_conf = os.path.join(etc_conf_dir, "devices.conf")
    if not os.path.exists(target_conf):
        if os.path.exists(CONF):
            shutil.copyfile(CONF, target_conf)
        elif os.path.exists(CONF_EX):
            shutil.copyfile(CONF_EX, target_conf)
        print(f"      {CHECK} Created {CYAN}{target_conf}{RESET}")
    else:
        print(f"      {CHECK} Configuration {CYAN}{target_conf}{RESET} exists")

    # 3. D-Bus policy
    print(f"{BOLD}[3/7]{RESET} Installing D-Bus policy...")
    dbus_dir = "/etc/dbus-1/system.d"
    os.makedirs(dbus_dir, exist_ok=True)
    shutil.copyfile(DBUS_POLICY, os.path.join(dbus_dir, "org.rgb_sleep.Control.conf"))
    print(f"      {CHECK} Installed policy to {CYAN}{dbus_dir}/org.rgb_sleep.Control.conf{RESET}")

    # 4. Systemd service for daemon (uses venv python)
    print(f"{BOLD}[4/7]{RESET} Configuring systemd daemon service...")
    service_content = f"""[Unit]
Description=RGB Sleep Daemon (D-Bus)
After=network.target

[Service]
ExecStart={venv_python} -m rgb_sleep.daemon
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    service_path = "/etc/systemd/system/rgb-sleep-daemon.service"
    with open(service_path, "w") as f:
        f.write(service_content)
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "--now", "rgb-sleep-daemon.service"], check=True)
    subprocess.run(["systemctl", "restart", "rgb-sleep-daemon.service"], check=True)
    print(f"      {CHECK} Enabled & started {GREEN}rgb-sleep-daemon.service{RESET}")

    # 5. Desktop autostart file (uses venv)
    print(f"{BOLD}[5/7]{RESET} Installing desktop autostart...")
    autostart_dir = os.path.join(home, ".config", "autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    target_desktop = os.path.join(autostart_dir, "rgb-sleep-tray.desktop")
    if os.path.exists(DESKTOP_SRC):
        # Update desktop file to use venv
        with open(DESKTOP_SRC) as f:
            desktop_content = f.read()
        desktop_content = desktop_content.replace(
            "Exec=rgb-sleep-tray",
            f"Exec={venv_bin}/rgb-sleep-tray"
        )
        with open(target_desktop, "w") as f:
            f.write(desktop_content)
        subprocess.run(["chown", f"{user}:{user}", target_desktop], check=False)
        print(f"      {CHECK} Added to login autostart ({CYAN}~/.config/autostart/{RESET})")

    # XFCE tray whitelist
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

    # 6. Launch tray
    print(f"{BOLD}[6/7]{RESET} Starting Taskbar Tray Indicator...")
    try:
        res = subprocess.run(["pgrep", "-f", "rgb-sleep-tray"], capture_output=True, text=True)
        for pid_str in res.stdout.split():
            try:
                pid = int(pid_str)
                if pid != os.getpid():
                    os.kill(pid, 9)
            except Exception:
                pass

        display = os.environ.get("DISPLAY", ":0.0")
        env = {"DISPLAY": display, "PATH": f"{venv_bin}:/usr/local/bin:/usr/bin:/bin", "HOME": home, "USER": user}
        cmd = ["sudo", "-u", user, "-E", "setsid", f"{venv_bin}/rgb-sleep-tray"]
        subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        time.sleep(1)
        print(f"      {CHECK} Taskbar tray icon started {GREEN}(⌨ visible in system tray){RESET}")
    except Exception as e:
        print(f"      {YELLOW}Note starting tray: {e}{RESET}")

# 7. Finalize
    print(f"{BOLD}[7/7]{RESET} Finalizing...")
    print(f"      {CHECK} Installation complete")

    # Success Card
    print(f"\n{GREEN}{BOLD}════════════════════════════════════════════════════════════{RESET}")
    print(f"  {CHECK} {GREEN}{BOLD}Installation successfully completed!{RESET}")
    print(f"{GREEN}{BOLD}════════════════════════════════════════════════════════════{RESET}\n")

    print(f"{BOLD}Quick Commands:{RESET}")
    print(f"  {CYAN}{venv_bin}/rgb-sleep off{RESET}     Turn off keyboard/mouse RGB lights")
    print(f"  {CYAN}{venv_bin}/rgb-sleep on{RESET}      Turn on RGB lights")
    print(f"  {CYAN}{venv_bin}/rgb-sleep status{RESET}  View live status of devices & daemon")
    print(f"  {CYAN}{venv_bin}/rgb-sleep-tray{RESET}    Launch or reload taskbar tray icon")
    print(f"\n{DIM}Commands use venv Python. No sudo needed — talk to root daemon via D-Bus.{RESET}\n")


if __name__ == "__main__":
    main()