"""Ícone de bandeja do Spectra (pystray/AppIndicator)."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from PIL import Image, ImageDraw

log = logging.getLogger("spectra.tray")

try:
    import pystray
except Exception:  # pragma: no cover - optional dependency
    pystray = None  # type: ignore[assignment]


def _icon_image() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (8, 10, 8, 255))
    d = ImageDraw.Draw(img)
    orange = (255, 90, 31, 255)
    bone = (236, 232, 220, 255)
    d.rectangle([10, 10, 54, 54], outline=orange, width=3)
    d.rectangle([28, 28, 36, 36], fill=bone)
    return img


class SpectraTray:
    def __init__(
        self,
        dispatch: Callable[[tuple], None],
        is_paused: Callable[[], bool],
    ):
        self.dispatch = dispatch
        self.is_paused = is_paused
        self.icon: Any = None
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        if pystray is None:
            log.warning("pystray indisponível; bandeja desativada")
            return False
        try:
            menu = pystray.Menu(
                pystray.MenuItem(
                    "Abrir centro de comando",
                    lambda: self.dispatch(("COMMAND_CENTER",)),
                    default=True,
                ),
                pystray.MenuItem("Escanear agora", lambda: self.dispatch(("SCAN",))),
                pystray.MenuItem(
                    "Pausar / retomar", lambda: self.dispatch(("TOGGLE_PAUSE",))
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", lambda: self.dispatch(("QUIT",))),
            )
            self.icon = pystray.Icon("spectra-hud", _icon_image(), "Spectra HUD", menu)
            self._thread = threading.Thread(
                target=self.icon.run, name="spectra-tray", daemon=True
            )
            self._thread.start()
            log.info("bandeja iniciada")
            return True
        except Exception as exc:  # pragma: no cover - backend-specific
            log.warning("falha ao iniciar bandeja: %s", exc)
            self.icon = None
            return False

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
