"""Captura de tela no Wayland.

O X11 não existe aqui: a captura passa pelo XDG Desktop Portal (Screenshot)
ou por ferramentas do compositor. O resultado é a tela inteira; não há
coordenadas globais para escolher o monitor sob o mouse.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

from PIL import Image

LAST_ERROR = ""
LAST_BACKEND = ""


def _portal_screenshot(timeout: float = 20.0) -> Image.Image:
    """Pede um screenshot ao org.freedesktop.portal.Screenshot."""
    global LAST_BACKEND
    try:
        from gi.repository import Gio, GLib
    except Exception as exc:  # pragma: no cover - depends on system GI
        raise RuntimeError("PyGObject/GIO não disponível") from exc

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    if bus is None:
        raise RuntimeError("sem sessão D-Bus")

    token = f"spectra_{os.getpid()}_{int(time.time() * 1000)}"
    unique = bus.get_unique_name() or ""
    sender = unique[1:] if unique.startswith(":") else unique
    request_path = f"/org/freedesktop/portal/desktop/request/{sender.replace('.', '_')}/{token}"

    loop = GLib.MainLoop()
    response: dict = {}

    def on_response(_conn, _sender, _path, _iface, _signal, params):
        code, results = params.unpack()
        response["code"] = code
        response["results"] = results
        loop.quit()

    subscription = bus.signal_subscribe(
        "org.freedesktop.portal.Desktop",
        "org.freedesktop.portal.Request",
        "Response",
        request_path,
        None,
        Gio.DBusSignalFlags.NONE,
        on_response,
    )

    proxy = Gio.DBusProxy.new_sync(
        bus,
        Gio.DBusProxyFlags.NONE,
        None,
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.portal.Screenshot",
        None,
    )
    options = {
        "handle_token": GLib.Variant("s", token),
        "interactive": GLib.Variant("b", False),
        "modal": GLib.Variant("b", False),
    }

    timer: dict[str, int | None] = {"id": None}

    def timed_out():
        timer["id"] = None
        loop.quit()
        return False

    timer["id"] = GLib.timeout_add_seconds(int(timeout), timed_out)
    try:
        proxy.call_sync(
            "Screenshot",
            GLib.Variant("(sa{sv})", ("", options)),
            Gio.DBusCallFlags.NONE,
            int(timeout * 1000),
            None,
        )
        loop.run()
    finally:
        if timer["id"]:
            GLib.source_remove(timer["id"])
        bus.signal_unsubscribe(subscription)

    if response.get("code") != 0:
        raise RuntimeError("screenshot cancelado ou negado pelo portal")
    results = response.get("results") or {}
    uri = results.get("uri")
    if hasattr(uri, "unpack"):
        uri = uri.unpack()
    if not uri:
        raise RuntimeError("portal não retornou o arquivo")
    path = Path(unquote(urlparse(str(uri)).path))
    with Image.open(path) as img:
        LAST_BACKEND = "portal"
        return img.convert("RGB").copy()


def _command_capture() -> Image.Image:
    """Fallback por compositor, para quando o portal não está disponível."""
    global LAST_BACKEND
    candidates = [
        ("grim", ["grim"]),
        ("gnome-screenshot", ["gnome-screenshot", "-f"]),
        ("spectacle", ["spectacle", "-b", "-n", "-o"]),
    ]
    workdir = Path(tempfile.mkdtemp(prefix="spectra-shot-"))
    try:
        for name, base in candidates:
            if shutil.which(name) is None:
                continue
            out = workdir / f"{name}.png"
            cmd = [*base, str(out)]
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=20,
                )
                if out.exists() and out.stat().st_size > 0:
                    with Image.open(out) as img:
                        LAST_BACKEND = name
                        return img.convert("RGB").copy()
            except Exception:
                continue
        raise RuntimeError(
            "nenhum backend de captura Wayland funcionou "
            "(tente xdg-desktop-portal, grim, gnome-screenshot ou spectacle)"
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def capture_wayland() -> tuple[Image.Image, dict]:
    """Captura a tela inteira via portal ou comando do compositor."""
    global LAST_ERROR
    errors: list[str] = []

    # wlroots: grim direto é mais rápido e não abre picker.
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if shutil.which("grim") and ("sway" in desktop or "hyprland" in desktop):
        try:
            img = _command_capture()
            return img, {
                "left": 0, "top": 0, "width": img.width, "height": img.height,
                "backend": LAST_BACKEND,
            }
        except Exception as exc:
            errors.append(f"grim: {exc}")

    try:
        img = _portal_screenshot()
        return img, {
            "left": 0, "top": 0, "width": img.width, "height": img.height,
            "backend": LAST_BACKEND,
        }
    except Exception as exc:
        errors.append(f"portal: {exc}")

    try:
        img = _command_capture()
        return img, {
            "left": 0, "top": 0, "width": img.width, "height": img.height,
            "backend": LAST_BACKEND,
        }
    except Exception as exc:
        errors.append(f"comando: {exc}")

    LAST_ERROR = " | ".join(errors)
    raise RuntimeError(LAST_ERROR)
