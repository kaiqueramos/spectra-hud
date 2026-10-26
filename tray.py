"""Ícone de bandeja do Spectra (pystray/AppIndicator)."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from PIL import Image, ImageDraw

import i18n

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

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                i18n.tr("tray.open"),
                lambda: self.dispatch(("COMMAND_CENTER",)),
                default=True,
            ),
            pystray.MenuItem(i18n.tr("tray.scan"), lambda: self.dispatch(("SCAN",))),
            pystray.MenuItem(i18n.tr("tray.ask"), lambda: self.dispatch(("ASK_SCREEN",))),
            pystray.MenuItem(
                i18n.tr("tray.pause"), lambda: self.dispatch(("TOGGLE_PAUSE",))
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(i18n.tr("tray.quit"), lambda: self.dispatch(("QUIT",))),
        )

    def start(self) -> bool:
        if pystray is None:
            log.warning("pystray indisponível; bandeja desativada")
            return False
        try:
            self.icon = pystray.Icon(
                "spectra-hud", _icon_image(), i18n.tr("tray.title"), self._menu()
            )
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

    def refresh(self) -> None:
        """Reconstrói o menu após troca de idioma."""
        if self.icon is None:
            return
        try:
            self.icon.menu = self._menu()
            self.icon.update_menu()
        except Exception:
            pass

    def stop(self) -> None:
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
