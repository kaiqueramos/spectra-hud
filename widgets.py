"""Widgets desenhados em Canvas para o centro de comando."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from typing import Any, Callable

import i18n
import theme


def blend(c1: str, c2: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    a = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(a, b))


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, r: int, **kwargs):
    """Retângulo arredondado via polígono suave."""
    points = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=12, **kwargs)


class PillButton(tk.Canvas):
    """Botão retangular com cantos arredondados, hover e estado ativo."""

    def __init__(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        t: dict[str, Any],
        primary: bool = False,
        active: bool = False,
        width: int | None = None,
        height: int = 32,
        font: tuple | None = None,
    ):
        self.t = t
        self.primary = primary
        self.active = active
        self.command = command
        self.font = font or ("DejaVu Sans Mono", 10, "bold")
        self._enabled = True
        self._hover = False
        self._text = text
        measure = tkfont.Font(font=self.font).measure(text)
        super().__init__(
            parent,
            width=width or max(64, measure + 30),
            height=height,
            bg=t["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=1,
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _e: self.invoke())
        self.bind("<Return>", lambda _e: self.invoke())
        self.bind("<space>", lambda _e: self.invoke())
        self.bind("<FocusIn>", lambda _e: self._draw())
        self.bind("<FocusOut>", lambda _e: self._draw())
        self._draw()

    def _colors(self):
        t = self.t
        if not self._enabled:
            return t["panel"], t["dim"], t["line"]
        if self.primary:
            fill = t["accent"]
            fg = t["accent_ink"]
            outline = t["accent"]
        elif self.active:
            fill = t["panel2"]
            fg = t["accent"]
            outline = t["accent"]
        elif self._hover:
            fill = t["panel2"]
            fg = t["text"]
            outline = t["accent"]
        else:
            fill = t["panel"]
            fg = t["text"]
            outline = t["line"]
        return fill, fg, outline

    def _draw(self):
        self.delete("all")
        fill, fg, outline = self._colors()
        w, h = int(self["width"]), int(self["height"])
        rounded_rect(self, 1, 1, w - 1, h - 1, 9, fill=fill, outline=outline, width=1)
        self.create_text(w // 2, h // 2 + 1, text=self._text, fill=fg, font=self.font)
        if self.focus_get() is self:
            rounded_rect(self, 3, 3, w - 3, h - 3, 7, fill="", outline=self.t["accent"], width=1)

    def _on_enter(self, _e=None):
        self._hover = True
        self._draw()

    def _on_leave(self, _e=None):
        self._hover = False
        self._draw()

    def invoke(self):
        if self._enabled:
            self.command()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def set_text(self, text: str):
        self._text = text
        self._draw()

    def set_active(self, active: bool):
        self.active = active
        self._draw()


class Switch(tk.Frame):
    """Switch deslizante com label clicável."""

    W, H = 52, 26

    def __init__(
        self,
        parent,
        text: str,
        variable: tk.BooleanVar,
        command: Callable[[], None] | None,
        t: dict[str, Any],
        font: tuple,
        wraplength: int = 0,
    ):
        super().__init__(parent, bg=t["bg"])
        self.t = t
        self.variable = variable
        self.command = command
        self._hover = False
        self._knob_x = 5.0
        self._anim_job = None
        self.canvas = tk.Canvas(
            self,
            width=self.W,
            height=self.H,
            bg=t["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=1,
        )
        self.canvas.pack(side="left")
        self.label = tk.Label(
            self,
            text=text,
            bg=t["bg"],
            fg=t["text"],
            font=font,
            anchor="w",
            justify="left",
            wraplength=wraplength or 0,
            cursor="hand2",
        )
        self.label.pack(side="left", padx=(10, 0), pady=(1, 0))
        for widget in (self.canvas, self.label):
            widget.bind("<Button-1>", lambda _e: self.toggle())
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
        self.canvas.bind("<space>", lambda _e: self.toggle())
        self.canvas.bind("<Return>", lambda _e: self.toggle())
        self.canvas.bind("<FocusIn>", lambda _e: self._draw())
        self.canvas.bind("<FocusOut>", lambda _e: self._draw())
        self._draw()

    def _on_enter(self, _e=None):
        self._hover = True
        self._draw()

    def _on_leave(self, _e=None):
        self._hover = False
        self._draw()

    def _draw(self, pos: float | None = None):
        t = self.t
        on = bool(self.variable.get())
        self.canvas.delete("all")
        track = t["accent"] if on else t["panel2"]
        outline = t["accent"] if on else t["line2"]
        if self._hover:
            track = blend(track, t["text"], 0.08)
            outline = t["accent"]
        if self.canvas.focus_get() is self.canvas:
            outline = t["accent"]
        rounded_rect(
            self.canvas, 2, 3, 50, 23, 10,
            fill=track, outline=outline, width=1,
        )
        knob_x = 31.0 if on else 5.0
        if pos is not None:
            knob_x = pos
        self._knob_x = knob_x
        # Sombra curta e knob com folga real dentro do trilho.
        self.canvas.create_oval(
            knob_x + 1, 7, knob_x + 15, 21,
            fill=blend(track, t["bg"], 0.28), outline="",
        )
        self.canvas.create_oval(
            knob_x, 6, knob_x + 14, 20,
            fill=t["text"], outline=blend(t["bg"], t["text"], 0.35), width=1,
        )

    def toggle(self):
        new = not bool(self.variable.get())
        self.variable.set(new)
        self._animate(31.0 if new else 5.0)
        if self.command:
            self.command()

    def _animate(self, target: float):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        start = self._knob_x
        steps = 6

        def step(i: int):
            fraction = 1.0 - (1.0 - i / steps) ** 3
            self._draw(start + (target - start) * fraction)
            if i < steps:
                self._anim_job = self.after(14, lambda: step(i + 1))
            else:
                self._anim_job = None

        step(0)


class ThemeCard(tk.Canvas):
    """Card de tema com amostras de cor, nome, modo e check."""

    W, H = 150, 42

    def __init__(
        self,
        parent,
        key: str,
        selected: bool,
        on_pick: Callable[[str], None],
        t: dict[str, Any],
        font_name: tuple,
        font_mode: tuple,
    ):
        self.key = key
        self.th = theme.get(key)
        self.selected = selected
        self.on_pick = on_pick
        self.t = t
        self.font_name = font_name
        self.font_mode = font_mode
        self._hover = False
        super().__init__(
            parent,
            width=self.W,
            height=self.H,
            bg=t["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _e: self.on_pick(self.key))
        self.bind("<Return>", lambda _e: self.on_pick(self.key))
        self.bind("<space>", lambda _e: self.on_pick(self.key))
        self.configure(takefocus=1)
        self._draw()

    def _on_enter(self, _e=None):
        self._hover = True
        self._draw()

    def _on_leave(self, _e=None):
        self._hover = False
        self._draw()

    def _draw(self):
        th = self.th
        t = self.t
        self.delete("all")
        border = t["accent"] if (self.selected or self._hover) else t["line"]
        bg = th["panel2"] if self._hover else th["panel"]
        rounded_rect(self, 1, 1, self.W - 1, self.H - 1, 8, fill=bg, outline=border, width=1)
        chips = (th["bg"], th["panel2"], th["accent"], th["text"])
        x = 8
        for color in chips:
            self.create_rectangle(x, 12, x + 8, 30, fill=color, outline=th["line2"])
            x += 10
        self.create_text(58, 15, text=th["name"], fill=th["text"], font=self.font_name, anchor="w")
        mode = i18n.tr("themes.dark" if th["mode"] == "dark" else "themes.light")
        self.create_text(58, 30, text=mode, fill=th["muted"], font=self.font_mode, anchor="w")
        if self.selected:
            self.create_text(self.W - 10, 21, text="✓", fill=t["accent"], font=self.font_name, anchor="e")


class IconButton(tk.Canvas):
    """Botão pequeno para a titlebar (fechar/ocultar)."""

    def __init__(
        self,
        parent,
        text: str,
        command: Callable[[], None],
        t: dict[str, Any],
        size: int = 26,
        bg: str | None = None,
    ):
        self.t = t
        self.command = command
        self._hover = False
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=bg or t["header"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._size = size
        self._text = text
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", lambda _e: self.command())
        self._draw()

    def _on_enter(self, _e=None):
        self._hover = True
        self._draw()

    def _on_leave(self, _e=None):
        self._hover = False
        self._draw()

    def _draw(self):
        t = self.t
        self.delete("all")
        if self._hover:
            rounded_rect(self, 1, 1, self._size - 1, self._size - 1, 6, fill=t["accent"], outline="")
            fg = t["accent_ink"]
        else:
            fg = t["muted"]
        self.create_text(
            self._size // 2,
            self._size // 2,
            text=self._text,
            fill=fg,
            font=("DejaVu Sans", 12, "bold"),
        )
