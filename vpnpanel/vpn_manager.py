"""Взаимодействие с WireGuard и получение внешнего IP-адреса.

Никакого кеширования состояния: каждый вызов читает реальное состояние
системы. Благодаря этому переключение через `vpn` в терминале сразу видно
на странице после обновления.
"""

import ipaddress
import os
import subprocess
from urllib.request import Request, urlopen

IFACE = "wg0"
CONFIG_PATH = "/etc/wireguard/wg0.conf"

SUDO = "/usr/bin/sudo"
WG = "/usr/bin/wg"
WG_QUICK = "/usr/bin/wg-quick"

IP_SERVICES = (
    "https://api.ipify.org",
    "https://ifconfig.me/ip",
    "https://icanhazip.com",
)


def config_exists() -> bool:
    """Есть ли конфиг ProtonVPN по ожидаемому пути.

    /etc/wireguard часто имеет права 700, поэтому из-под обычного
    пользователя файл не виден — тогда смотрим по поднятому интерфейсу.
    """
    try:
        if os.path.isfile(CONFIG_PATH):
            return True
        return os.path.isdir(f"/sys/class/net/{IFACE}")
    except OSError:
        return False


def _run(args, timeout=12):
    """Запуск команды: всегда возвращает CompletedProcess, не бросает."""
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )


def is_running() -> bool:
    """True, если интерфейс wg0 реально поднят."""
    try:
        result = _run([SUDO, "-n", WG, "show", IFACE], timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def public_ip() -> str:
    """Текущий внешний IP. При включённом VPN — IP точки выхода туннеля."""
    for url in IP_SERVICES:
        try:
            req = Request(url, headers={"User-Agent": "django-vpn/1.0"})
            with urlopen(req, timeout=4) as response:
                value = response.read().decode("utf-8").strip()
            ipaddress.ip_address(value)  # отсечь HTML/мусор в ответе
            return value
        except Exception:
            continue
    return "недоступно"


def _wg_quick(action: str) -> dict:
    if action == "up" and not config_exists():
        return {
            "ok": False,
            "output": f"Нет файла {CONFIG_PATH}. Положите туда конфиг ProtonVPN.",
        }

    try:
        result = _run([SUDO, "-n", WG_QUICK, action, IFACE])
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "output": str(exc)}

    output = (result.stdout + result.stderr).strip()
    return {"ok": result.returncode == 0, "output": output}


def up() -> dict:
    return _wg_quick("up")


def down() -> dict:
    return _wg_quick("down")


def toggle() -> dict:
    """Включить, если выключен; выключить, если включён."""
    return down() if is_running() else up()
