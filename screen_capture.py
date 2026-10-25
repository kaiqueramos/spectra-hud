"""
Captura de tela e posição do mouse no X11.

Ordem de resolução do mouse: xdotool (com timeout) e, se falhar, Xlib.
Nenhuma das duas existe no Wayland puro: o app deve falhar antes com uma
mensagem clara (ver `is_wayland`).
"""

import os
import subprocess

import mss
from PIL import Image
from Xlib import display as xdisplay


def is_wayland() -> bool:
    """True quando a sessão é Wayland (não suportado na v0.1)."""
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland" or bool(
        os.environ.get("WAYLAND_DISPLAY")
    )


def get_mouse_position() -> tuple[int, int] | None:
    """Posição global do cursor. None se nenhum backend conseguir responder."""
    try:
        out = subprocess.run(
            ["xdotool", "getmouselocation"],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        ).stdout
        parts = dict(p.split(":", 1) for p in out.strip().split() if ":" in p)
        return int(parts["x"]), int(parts["y"])
    except Exception:
        pass

    try:
        d = xdisplay.Display()
        try:
            pointer = d.screen().root.query_pointer()
            return pointer.root_x, pointer.root_y
        finally:
            d.close()
    except Exception:
        return None


def capture_active_monitor() -> tuple[Image.Image, dict]:
    """Captura o monitor sob o cursor (ou o primário, se não houver mouse)."""
    position = get_mouse_position()
    mx, my = position if position else (None, None)

    with mss.mss() as sct:
        monitors = sct.monitors[1:] or [sct.monitors[0]]
        selected_monitor = None

        if mx is not None and my is not None:
            for monitor in monitors:
                left, top = monitor["left"], monitor["top"]
                right = left + monitor["width"]
                bottom = top + monitor["height"]
                if left <= mx < right and top <= my < bottom:
                    selected_monitor = monitor
                    break

        if not selected_monitor:
            selected_monitor = monitors[0]

        shot = sct.grab(selected_monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return img, selected_monitor
