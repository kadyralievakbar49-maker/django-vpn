"""Views панели управления VPN.

Локально (есть /etc/wireguard/wg0.conf) — реальное управление через subprocess.
На Vercel (нет интерфейса wg0 и root) — автоматически демо-режим: состояние
хранится в cookie браузера, поэтому кнопка полностью рабочая и интерактивная.
"""

import os

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import vpn_manager

DEMO_COOKIE = "vpn_demo_state"
DEMO_IP = "203.0.113.42"

# На Vercel переменная VERCEL=1 выставляется автоматически — там включается
# демо-режим. Локально остаётся настоящее управление wg0.
DEMO_MODE = os.environ.get("DEMO_MODE", "0") == "1" or os.environ.get("VERCEL") == "1"


def _demo_on(request):
    return request.COOKIES.get(DEMO_COOKIE, "off") == "on"


def _snapshot(request):
    if DEMO_MODE:
        return {
            "status": _demo_on(request),
            "ip": DEMO_IP,
            "iface": vpn_manager.IFACE,
            "config_exists": True,
            "demo": True,
        }
    return {
        "status": vpn_manager.is_running(),
        "ip": vpn_manager.public_ip(),
        "iface": vpn_manager.IFACE,
        "config_exists": vpn_manager.config_exists(),
        "demo": False,
    }


def index(request):
    """Каждый запрос читает живое состояние системы — отсюда синхронизация."""
    return render(request, "vpnpanel/index.html", _snapshot(request))


@require_POST
def toggle(request):
    if DEMO_MODE:
        new_state = "off" if _demo_on(request) else "on"
        response = redirect("vpnpanel:index")
        response.set_cookie(
            DEMO_COOKIE,
            new_state,
            max_age=60 * 60 * 24,
            samesite="Lax",
        )
        messages.success(request, "Демо: состояние переключено")
        return response

    result = vpn_manager.toggle()
    if result["ok"]:
        messages.success(request, "Состояние VPN изменено")
    else:
        messages.error(request, f"Ошибка: {result['output']}")
    return redirect("vpnpanel:index")


def status_api(request):
    """Лёгкий JSON для фонового опроса страницы."""
    snapshot = _snapshot(request)
    return JsonResponse(
        {
            "running": snapshot["status"],
            "ip": snapshot["ip"],
            "config_exists": snapshot["config_exists"],
            "demo": snapshot["demo"],
        }
    )
