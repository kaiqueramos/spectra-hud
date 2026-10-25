"""Tipografia do Spectra.

Escolhe a melhor fonte instalada e cai para DejaVu quando necessário, para o
app continuar legível em qualquer Linux. A fonte de display dá a identidade
sci-fi; o mono vem do FiraCode quando disponível; o corpo usa Ubuntu/Noto.
"""

from __future__ import annotations

import tkinter.font as tkfont

DISPLAY_CANDIDATES = ("Share Tech Mono", "FiraCode Nerd Font", "DejaVu Sans Condensed")
MONO_CANDIDATES = ("FiraCode Nerd Font Mono", "JetBrains Mono", "Ubuntu Mono", "DejaVu Sans Mono")
BODY_CANDIDATES = ("Ubuntu", "Noto Sans", "Inter", "DejaVu Sans")


def _pick(available: set[str], candidates: tuple[str, ...], fallback: str) -> str:
    for family in candidates:
        if family in available:
            return family
    return fallback


def resolve(available: set[str] | None = None) -> dict[str, tuple]:
    """Devolve os font tuples usados pelo centro de comando."""
    if available is None:
        try:
            available = set(tkfont.families())
        except Exception:
            available = set()

    display = _pick(available, DISPLAY_CANDIDATES, "DejaVu Sans")
    mono = _pick(available, MONO_CANDIDATES, "DejaVu Sans Mono")
    body = _pick(available, BODY_CANDIDATES, "DejaVu Sans")

    return {
        "display": (display, 24),
        "display_s": (display, 13),
        "mono": (mono, 10),
        "mono_s": (mono, 9),
        "mono_b": (mono, 10, "bold"),
        "body": (body, 11),
        "body_s": (body, 9),
        "body_b": (body, 11, "bold"),
    }
