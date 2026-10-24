"""
Módulo de captura de tela rápida usando mss e detecção do monitor sob o cursor do mouse.
"""

import subprocess
import mss
from PIL import Image


def get_mouse_position() -> tuple[int, int]:
    """Obtém as coordenadas X, Y do cursor do mouse via xdotool."""
    try:
        out = subprocess.check_output(["xdotool", "getmouselocation"], text=True)
        # Formato: x:1234 y:567 screen:0 window:12345
        parts = dict(p.split(":", 1) for p in out.strip().split() if ":" in p)
        return int(parts["x"]), int(parts["y"])
    except Exception:
        return (0, 0)


def capture_active_monitor() -> tuple[Image.Image, dict]:
    """
    Captura o monitor onde o cursor do mouse está localizado no momento.
    Retorna a imagem PIL e os dados do monitor (top, left, width, height).
    """
    mx, my = get_mouse_position()

    with mss.mss() as sct:
        # monitors[0] é a tela combinada. Os monitores individuais são de 1 em diante.
        selected_monitor = None
        for m in sct.monitors[1:]:
            left, top = m["left"], m["top"]
            right = left + m["width"]
            bottom = top + m["height"]
            if left <= mx < right and top <= my < bottom:
                selected_monitor = m
                break

        if not selected_monitor:
            # Fallback para o monitor primário se o cursor estiver fora
            selected_monitor = (
                sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            )

        shot = sct.grab(selected_monitor)
        img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return img, selected_monitor
