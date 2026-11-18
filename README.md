# django-vpn

Локальная панель управления WireGuard (`wg0`) на Django + глобальная команда `vpn`.

Проверено на EndeavourOS/Arch: Python 3.14.10, Django 5.2.13 (из pacman).

---

## 1. Системные пакеты

```bash
sudo pacman -Syu
sudo pacman -S wireguard-tools sudo
# openresolv НЕ нужен: уже стоит systemd-resolvconf, он же даёт /usr/bin/resolvconf
# Django уже стоит как python-django
```

`wireguard-tools` в репозитории `extra`, если вдруг не находится — обнови базу:
```bash
sudo pacman -Syy
```

## 2. Конфиг ProtonVPN

На этой машине `/etc/wireguard/` отсутствует — создай его и положи туда файл,
скачанный из личного кабинета ProtonVPN (WireGuard → Download config):

```bash
sudo install -d -m 700 /etc/wireguard
sudo install -m 600 ~/Downloads/protonvpn.conf /etc/wireguard/wg0.conf
sudo wg-quick up wg0     # проверить вручную
sudo wg show wg0
sudo wg-quick down wg0
```

## 3. sudo без пароля только для нужных команд

```bash
# замени kan на своё имя, если отличается
sudo sed -i "s/^kan /$(whoami) /" /home/kan/django-vpn/sudoers.d-vpn-panel
sudo install -m 440 /home/kan/django-vpn/sudoers.d-vpn-panel /etc/sudoers.d/vpn-panel
sudo visudo -c
sudo -n wg show wg0 || echo "wg0 выключен — нормально"
```

## 4. Глобальная команда vpn

```bash
sudo install -m 755 /home/kan/django-vpn/scripts/vpn /usr/local/bin/vpn
vpn status
vpn          # переключить
```

## 5. Запуск панели

```bash
cd /home/kan/django-vpn
source .venv/bin/activate
python manage.py runserver 127.0.0.1:8000
```

Открой http://127.0.0.1:8000

---

## Как это работает

- `vpnpanel/vpn_manager.py` дёргает `sudo -n wg show wg0`, `wg-quick up/down` через `subprocess`.
- Состояние **не сохраняется в БД**: `views.py` читает живой интерфейс при каждом запросе, поэтому `vpn` из терминала и кнопка на сайте всегда синхронны.
- `/status/` отдаёт JSON, JS на странице опрашивает его раз в 10 секунд.
- Внешний IP берётся через `urllib` (ipify → ifconfig.me → icanhazip).

---

## Демо-версия на Vercel

Репозиторий: https://github.com/kadyralievakbar49-maker/django-vpn

Vercel: Import Git Repository → `django-vpn` → Deploy. Django определяется
автоматически (есть manage.py), statics собираются через collectstatic.

Внимание: на Vercel нет root, интерфейса `wg0` и `/etc/wireguard`, поэтому
реальное управление VPN там невозможно. При `VERCEL=1` автоматически включается
демо-режим: кнопка меняет состояние через cookie, на странице есть бейдж
«ДЕМО-РЕЖИМ». Локальная версия управляет настоящим `wg0`.
