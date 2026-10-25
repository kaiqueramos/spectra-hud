"""Centro de comando / wizard do Spectra, com temas e idiomas."""

from __future__ import annotations

import math
import queue
import threading
import tkinter as tk
from typing import Any, Callable

import mss
from Xlib import X
from Xlib import display as xdisplay

import ai_client
import config
import fonts
import i18n
import theme
import widgets
from i18n import SHORT, tr

# Defaults seguros; _apply_fonts() troca pelas melhores fontes instaladas
# quando a janela Tk já existe.
MONO = ("DejaVu Sans Mono", 10)
MONO_S = ("DejaVu Sans Mono", 9)
MONO_B = ("DejaVu Sans Mono", 10, "bold")
BODY = ("DejaVu Sans", 11)
BODY_S = ("DejaVu Sans", 9)
BODY_B = ("DejaVu Sans", 11, "bold")
DISPLAY = ("DejaVu Sans Condensed", 22)
DISPLAY_S = ("DejaVu Sans Condensed", 13)


def _apply_fonts() -> None:
    global MONO, MONO_S, MONO_B, BODY, BODY_S, BODY_B, DISPLAY, DISPLAY_S
    try:
        f = fonts.resolve()
    except Exception:
        return
    MONO = f["mono"]
    MONO_S = f["mono_s"]
    MONO_B = f["mono_b"]
    BODY = f["body"]
    BODY_S = f["body_s"]
    BODY_B = f["body_b"]
    DISPLAY = f["display"]
    DISPLAY_S = f["display_s"]


def _blend(c1: str, c2: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    a = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(a, b))


class CommandCenter:
    def __init__(
        self,
        root: tk.Tk,
        on_saved: Callable[[dict[str, Any]], None],
        on_quit: Callable[[], None],
        first_run: bool = False,
    ):
        _apply_fonts()
        self.root = root
        self.on_saved = on_saved
        self.on_quit = on_quit
        self.first_run = first_run
        self.cfg = config.load()
        self.language = i18n.set_language(self.cfg.get("language", "pt"))
        self.theme_key = self.cfg.get("theme", "spectra")
        theme.set_current(self.theme_key)
        self._test_queue: queue.Queue = queue.Queue()
        self._testing = False
        blocklist = self.cfg.get("blocklist")
        if blocklist is None:
            blocklist = config.DEFAULT_BLOCKLIST
        self._block_cache = "\n".join(blocklist)
        self._drag: tuple[int, int, int, int] | None = None
        self._pulse_phase = 0.0
        self._scan_y = 0.0

        self.provider_keys = list(config.PRESETS.keys())
        self.provider_labels = [config.PRESETS[k]["label"] for k in self.provider_keys]
        current = self.cfg.get("provider", "custom")
        current_label = config.PRESETS.get(current, config.PRESETS["custom"])["label"]

        self.provider_var = tk.StringVar(value=current_label)
        self.base_var = tk.StringVar(value=self.cfg.get("base_url", ""))
        self.model_var = tk.StringVar(value=self.cfg.get("model", ""))
        self.key_var = tk.StringVar(value=config.get_api_key(self.cfg))
        self.consent_var = tk.BooleanVar(value=config.has_consent(self.cfg))
        self.pause_var = tk.BooleanVar(value=bool(self.cfg.get("paused", False)))
        self.animations_var = tk.BooleanVar(value=bool(self.cfg.get("animations", True)))
        self.hotkey_scan_var = tk.StringVar(value=self.cfg.get("hotkey_scan", ""))
        self.hotkey_bar_var = tk.StringVar(value=self.cfg.get("hotkey_bar", ""))
        self.hotkey_center_var = tk.StringVar(value=self.cfg.get("hotkey_center", ""))
        self.hotkey_pause_var = tk.StringVar(value=self.cfg.get("hotkey_pause", ""))
        self.show_key_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="")
        self.meta_var = tk.StringVar(value=self._meta_text())
        self.state_var = tk.StringVar(
            value=tr("common.paused") if self.pause_var.get() else tr("common.ready")
        )
        price = (self.cfg.get("pricing") or {}).get(self.cfg.get("model", ""), {})
        self.price_in_var = tk.StringVar(value=str(price.get("in", "")) if price else "")
        self.price_out_var = tk.StringVar(value=str(price.get("out", "")) if price else "")
        self.sys_vars: dict[str, tk.StringVar] = {}
        self.telemetry_vars: dict[str, tk.StringVar] = {}

        self.win = tk.Toplevel(root)
        self.win.title(tr("app.title"))
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.configure(
                bg=theme.current()["bg"],
                highlightthickness=1,
                highlightbackground=theme.current()["line"],
            )
        except tk.TclError:
            self.win.configure(bg=theme.current()["bg"])
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.bind("<Control-s>", lambda _e: self.save())
        self.win.bind("<F5>", lambda _e: self.test_vision())
        self.win.bind("<Control-t>", lambda _e: self._cycle_theme())
        self.win.bind("<Control-r>", lambda _e: self.reload_yaml())
        self.win.bind("<Button-1>", self._force_x_focus, add="+")

        mon = self._target_monitor()
        w, h = 1060, 1010
        x = mon["left"] + max(10, (mon["width"] - w) // 2)
        y = mon["top"] + max(10, (mon["height"] - h) // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self.win, bg=theme.current()["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw_grid())

        self.body = tk.Frame(self.win, bg=theme.current()["bg"])
        self.body.place(x=26, y=18, relwidth=1, relheight=1, width=-52, height=-36)

        self._render()
        if config.LAST_YAML_ERROR:
            self.status_var.set(
                tr("msg.yaml_error", error=self._yaml_error_text())
            )
        self.win.after(80, self._force_x_focus)
        self.win.after(100, self._poll_test)
        self.win.after(700, self._refresh_meta)
        self.win.after(600, self._pulse)
        self.win.after(120, self._scanline_tick)
        self.win.update_idletasks()
        self._draw_grid()
        self.win.lift()
        self.win.focus_force()

    # ------------------------------------------------------------------ infra
    def _target_monitor(self) -> dict:
        try:
            with mss.mss() as sct:
                monitors = sct.monitors[1:] or [sct.monitors[0]]
                for mon in monitors:
                    if mon.get("is_primary"):
                        return mon
                return monitors[0]
        except Exception:
            return {"left": 0, "top": 0, "width": 1920, "height": 1080}

    def _force_x_focus(self, event=None):
        """Dá foco X real à janela sem moldura (WM não gerencia o foco)."""
        try:
            d = xdisplay.Display()
            xwin = d.create_resource_object("window", self.win.winfo_id())
            d.set_input_focus(xwin, X.RevertToParent, X.CurrentTime)
            d.flush()
            d.close()
        except Exception:
            pass
        if event is None:
            try:
                self.win.focus_force()
                self.win.focus_set()
            except Exception:
                pass

    def _bind_drag(self, widget):
        widget.bind("<ButtonPress-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._on_drag)

    def _start_drag(self, event):
        self._force_x_focus()
        self._drag = (event.x_root, event.y_root, self.win.winfo_x(), self.win.winfo_y())

    def _on_drag(self, event):
        if not self._drag:
            return
        x0, y0, wx, wy = self._drag
        self.win.geometry(f"+{wx + event.x_root - x0}+{wy + event.y_root - y0}")

    def _draw_grid(self):
        t = theme.get(self.theme_key)
        c = self.canvas
        try:
            if not c.winfo_exists():
                return
        except Exception:
            return
        c.delete("grid")
        w, h = c.winfo_width(), c.winfo_height()
        for x in range(0, w, 40):
            c.create_line(x, 0, x, h, fill=t["grid"], tags="grid")
        for y in range(0, h, 40):
            c.create_line(0, y, w, y, fill=t["grid"], tags="grid")
        s = 22
        for x1, y1, x2, y2 in [
            (18, 18, 18 + s, 18),
            (18, 18, 18, 18 + s),
            (w - 18, 18, w - 18 - s, 18),
            (w - 18, 18, w - 18, 18 + s),
            (18, h - 18, 18 + s, h - 18),
            (18, h - 18, 18, h - 18 - s),
            (w - 18, h - 18, w - 18 - s, h - 18),
            (w - 18, h - 18, w - 18, h - 18 - s),
        ]:
            c.create_line(x1, y1, x2, y2, fill=t["accent"], width=1, tags="grid")
        c.create_line(
            0,
            self._scan_y,
            w,
            self._scan_y,
            fill=_blend(t["grid"], t["accent"], 0.28),
            width=1,
            tags=("grid", "scanline"),
        )

    def _scanline_tick(self):
        try:
            if not self.win.winfo_exists():
                return
            items = self.canvas.find_withtag("scanline")
            if items:
                line = items[-1]
                if not self.animations_var.get():
                    self.canvas.itemconfigure(line, state="hidden")
                else:
                    h = max(1, self.canvas.winfo_height())
                    self._scan_y = (self._scan_y + 2.0) % h
                    self.canvas.itemconfigure(line, state="normal")
                    w = self.canvas.winfo_width()
                    self.canvas.coords(line, 0, self._scan_y, w, self._scan_y)
        except Exception:
            pass
        try:
            self.win.after(45, self._scanline_tick)
        except Exception:
            pass

    def _pulse(self):
        try:
            if not self.win.winfo_exists():
                return
            t = theme.get(self.theme_key)
            if not self.animations_var.get():
                color = t["warning"] if self.pause_var.get() else t["accent"]
                self.led.itemconfigure("led", fill=color)
            else:
                self._pulse_phase += 0.18
                wave = 0.5 + 0.5 * math.sin(self._pulse_phase)
                color = t["warning"] if self.pause_var.get() else t["accent"]
                self.led.itemconfigure("led", fill=_blend(t["bg"], color, 0.45 + 0.55 * wave))
        except Exception:
            pass
        try:
            self.win.after(60, self._pulse)
        except Exception:
            pass

    # ------------------------------------------------------------------ render
    def _render(self):
        t = theme.get(self.theme_key)
        theme.set_current(self.theme_key)
        self.win.title(tr("app.title"))
        self.state_var.set(tr("common.paused") if self.pause_var.get() else tr("common.ready"))
        self.win.configure(bg=t["bg"])
        try:
            self.win.configure(highlightbackground=t["line"])
        except tk.TclError:
            pass
        self.canvas.configure(bg=t["bg"])
        self.body.configure(bg=t["bg"])
        for child in self.body.winfo_children():
            child.destroy()

        head = tk.Frame(self.body, bg=t["bg"])
        head.pack(fill="x")
        self._bind_drag(head)

        mark = tk.Canvas(head, width=30, height=30, bg=t["bg"], highlightthickness=0)
        mark.create_line(3, 9, 3, 3, 9, 3, fill=t["accent"], width=2)
        mark.create_line(21, 3, 27, 3, 27, 9, fill=t["accent"], width=2)
        mark.create_line(27, 21, 27, 27, 21, 27, fill=t["accent"], width=2)
        mark.create_line(9, 27, 3, 27, 3, 21, fill=t["accent"], width=2)
        mark.create_rectangle(13, 13, 17, 17, fill=t["accent"], outline="")
        mark.pack(side="left", pady=(2, 0))
        self._bind_drag(mark)

        title = tk.Frame(head, bg=t["bg"])
        title.pack(side="left", padx=(10, 0))
        brand = tk.Label(title, text="SPECTRA", bg=t["bg"], fg=t["text"], font=DISPLAY)
        brand.pack(side="left")
        sub = tk.Label(title, text=tr("app.brand_sub"), bg=t["bg"], fg=t["dim"], font=MONO)
        sub.pack(side="left", padx=(8, 0), pady=(7, 0))
        for widget in (title, brand, sub):
            self._bind_drag(widget)

        right = tk.Frame(head, bg=t["bg"])
        right.pack(side="right")
        self._bind_drag(right)
        self.led = tk.Canvas(right, width=12, height=12, bg=t["bg"], highlightthickness=0)
        self.led.create_oval(2, 2, 10, 10, fill=t["accent"], outline="", tags="led")
        self.led.pack(side="left", padx=(0, 6), pady=(4, 0))
        state = tk.Label(right, textvariable=self.state_var, bg=t["bg"], fg=t["dim"], font=MONO_S)
        state.pack(side="left", padx=(0, 14))
        mode = tr("themes.dark" if t["mode"] == "dark" else "themes.light")
        theme_lbl = tk.Label(
            right,
            text=f"{mode} · {t['name'].upper()}",
            bg=t["bg"],
            fg=t["accent"],
            font=MONO_S,
        )
        theme_lbl.pack(side="left", padx=(0, 14))
        ver = tk.Label(right, text="v0.2.1", bg=t["bg"], fg=t["dim"], font=MONO_S)
        ver.pack(side="left", padx=(0, 8))
        for widget in (state, theme_lbl, ver):
            self._bind_drag(widget)
        tk.Frame(right, bg=t["line"], width=1, height=18).pack(side="left", padx=(0, 8))
        widgets.IconButton(right, "—", self._hide_window, t, bg=t["bg"]).pack(side="left")
        widgets.IconButton(right, "✕", self.close, t, bg=t["bg"]).pack(side="left", padx=(0, 2))

        rule = tk.Frame(self.body, bg=t["line"], height=1)
        rule.pack(fill="x", pady=(12, 0))

        banner = None
        if self.first_run or not config.has_consent(self.cfg) or not config.get_api_key(self.cfg):
            banner = tk.Frame(self.body, bg=t["panel"], highlightthickness=1, highlightbackground=t["accent"])
            banner.pack(fill="x", pady=(10, 0))
            tk.Label(
                banner,
                text=tr("app.first_run"),
                bg=t["panel"],
                fg=t["text"],
                font=MONO_S,
                anchor="w",
                padx=10,
                pady=8,
            ).pack(fill="x")
        self.banner = banner

        content = tk.Frame(self.body, bg=t["bg"])
        content.pack(fill="both", expand=True, pady=(14, 0))
        content.columnconfigure(0, weight=1, minsize=600)
        content.columnconfigure(1, weight=0, minsize=330)
        content.rowconfigure(0, weight=1)

        left = tk.Frame(content, bg=t["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        rightp = tk.Frame(content, bg=t["bg"])
        rightp.grid(row=0, column=1, sticky="nsew")

        self._build_left(left, t)
        self._build_right(rightp, t)

        status = tk.Frame(self.body, bg=t["panel"], highlightthickness=1, highlightbackground=t["line"])
        status.pack(fill="x", pady=(12, 0))
        tk.Label(status, text=tr("status.last_scan"), bg=t["panel"], fg=t["accent"], font=MONO_S).pack(
            anchor="w", padx=10, pady=(6, 0)
        )
        tk.Label(
            status,
            textvariable=self.meta_var,
            bg=t["panel"],
            fg=t["text"],
            font=MONO_S,
            anchor="w",
            justify="left",
            padx=10,
        ).pack(fill="x")
        tk.Label(
            status,
            textvariable=self.status_var,
            bg=t["panel"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
            justify="left",
            padx=10,
        ).pack(fill="x", pady=(0, 6))

        actions = tk.Frame(self.body, bg=t["bg"])
        actions.pack(fill="x", pady=(12, 0))
        self.test_btn = widgets.PillButton(
            actions,
            tr("btn.test_vision"),
            self.test_vision,
            t,
            width=136,
            height=32,
            font=MONO_B,
        )
        self.test_btn.pack(side="left")
        if self._testing:
            self.test_btn.set_enabled(False)
        widgets.PillButton(
            actions,
            tr("btn.save"),
            self.save,
            t,
            primary=True,
            width=102,
            height=32,
            font=MONO_B,
        ).pack(side="left", padx=(8, 0))
        widgets.PillButton(
            actions,
            tr("btn.quit"),
            self.quit,
            t,
            width=80,
            height=32,
            font=MONO_B,
        ).pack(side="right")
        widgets.PillButton(
            actions,
            tr("btn.clear_cache"),
            self.clear_cache,
            t,
            height=32,
            font=MONO_B,
        ).pack(side="right", padx=(0, 8))
        widgets.PillButton(
            actions,
            tr("btn.logs"),
            self.open_logs,
            t,
            height=32,
            font=MONO_B,
        ).pack(side="right", padx=(0, 8))
        widgets.PillButton(
            actions,
            tr("btn.reload"),
            self.reload_yaml,
            t,
            width=112,
            height=32,
            font=MONO_B,
        ).pack(side="right", padx=(0, 8))
        widgets.PillButton(
            actions,
            tr("btn.yaml"),
            self.open_yaml,
            t,
            width=64,
            height=32,
            font=MONO_B,
        ).pack(side="right", padx=(0, 8))

        if banner is not None:
            self.first_run = True
        self._draw_grid()
        self._refresh_system()

    def _build_left(self, parent, t):
        form = parent
        form.columnconfigure(1, weight=1)
        row = 0
        row = self._section(form, tr("section.connection"), row, t)

        self._label(form, tr("field.provider"), row, t)
        menu = tk.OptionMenu(form, self.provider_var, *self.provider_labels, command=self._on_provider)
        menu.configure(
            bg=t["input"],
            fg=t["text"],
            activebackground=t["line"],
            activeforeground=t["accent"],
            highlightthickness=1,
            highlightbackground=t["line"],
            relief="flat",
            font=MONO,
            anchor="w",
            padx=8,
            width=32,
        )
        menu["menu"].configure(
            bg=t["panel"],
            fg=t["text"],
            activebackground=t["accent"],
            activeforeground=t["accent_ink"],
            font=MONO,
        )
        menu.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        for label, var, show in [
            (tr("field.base_url"), self.base_var, ""),
            (tr("field.model"), self.model_var, ""),
            (tr("field.api_key"), self.key_var, "•"),
        ]:
            self._label(form, label, row, t)
            if label == tr("field.api_key"):
                wrap = tk.Frame(form, bg=t["bg"])
                wrap.grid(row=row, column=1, sticky="ew", pady=3)
                wrap.columnconfigure(0, weight=1)
                self.key_entry = tk.Entry(
                    wrap,
                    textvariable=var,
                    show=show,
                    bg=t["input"],
                    fg=t["text"],
                    insertbackground=t["accent"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=t["line"],
                    font=MONO,
                )
                self.key_entry.grid(row=0, column=0, sticky="ew", ipady=5)
                self.show_key_btn = widgets.PillButton(
                    wrap,
                    tr("field.show"),
                    self._toggle_key,
                    t,
                    active=self.show_key_var.get(),
                    width=78,
                    height=27,
                    font=MONO_S,
                )
                self.show_key_btn.grid(row=0, column=1, padx=(8, 0))
            else:
                tk.Entry(
                    form,
                    textvariable=var,
                    bg=t["input"],
                    fg=t["text"],
                    insertbackground=t["accent"],
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=t["line"],
                    font=MONO,
                ).grid(row=row, column=1, sticky="ew", pady=3, ipady=5)
            row += 1

        widgets.Switch(
            form,
            tr("consent.text"),
            self.consent_var,
            self._refresh_system,
            t,
            BODY,
            wraplength=520,
        ).grid(row=row, column=1, sticky="w", pady=(8, 0))
        row += 1
        widgets.Switch(
            form,
            tr("pause.text"),
            self.pause_var,
            self._toggle_pause,
            t,
            BODY,
            wraplength=520,
        ).grid(row=row, column=1, sticky="w", pady=(2, 0))
        row += 1

        row = self._section(form, tr("section.guardrails"), row, t)
        self._label(form, tr("field.blocklist"), row, t)
        block_wrap = tk.Frame(form, bg=t["bg"])
        block_wrap.grid(row=row, column=1, sticky="ew", pady=(4, 0))
        block_wrap.columnconfigure(0, weight=1)
        tk.Label(
            block_wrap,
            text=tr("blocklist.hint"),
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
            justify="left",
            wraplength=540,
        ).grid(row=0, column=0, columnspan=2, sticky="w")
        self.block_text = tk.Text(
            block_wrap,
            height=4,
            bg=t["input"],
            fg=t["text"],
            insertbackground=t["accent"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=t["line"],
            font=MONO_S,
            padx=8,
            pady=6,
            wrap="word",
        )
        self.block_text.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.block_text.insert("1.0", self._block_cache)
        scroll = tk.Scrollbar(
            block_wrap,
            command=self.block_text.yview,
            bg=t["panel"],
            troughcolor=t["bg"],
            activebackground=t["accent"],
            highlightthickness=0,
            bd=0,
            width=10,
        )
        scroll.grid(row=1, column=1, sticky="ns", pady=(4, 0))
        self.block_text.configure(yscrollcommand=scroll.set)
        row += 1

        self._label(form, tr("field.hotkeys"), row, t)
        hk = tk.Frame(form, bg=t["bg"])
        hk.grid(row=row, column=1, sticky="w", pady=(4, 0))
        for i, (label, var) in enumerate(
            [
                (tr("label.scan"), self.hotkey_scan_var),
                (tr("label.bar"), self.hotkey_bar_var),
                (tr("label.center"), self.hotkey_center_var),
                (tr("label.pause"), self.hotkey_pause_var),
            ]
        ):
            tk.Label(hk, text=label, bg=t["bg"], fg=t["dim"], font=MONO_S).grid(
                row=i // 2, column=(i % 2) * 2, sticky="w", padx=(0, 6), pady=2
            )
            tk.Entry(
                hk,
                textvariable=var,
                bg=t["input"],
                fg=t["text"],
                insertbackground=t["accent"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=t["line"],
                font=MONO_S,
                width=25,
            ).grid(row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(0, 12), pady=2, ipady=3)
        row += 1

        row = self._section(form, tr("section.metering"), row, t)
        self._label(form, tr("field.price"), row, t)
        price = tk.Frame(form, bg=t["bg"])
        price.grid(row=row, column=1, sticky="w", pady=3)
        for label, var in [
            (tr("field.price_in"), self.price_in_var),
            (tr("field.price_out"), self.price_out_var),
        ]:
            tk.Label(price, text=label, bg=t["bg"], fg=t["dim"], font=MONO_S).pack(side="left")
            tk.Entry(
                price,
                textvariable=var,
                bg=t["input"],
                fg=t["text"],
                insertbackground=t["accent"],
                relief="flat",
                highlightthickness=1,
                highlightbackground=t["line"],
                font=MONO,
                width=9,
            ).pack(side="left", padx=(4, 14), ipady=4)
        row += 1

        row = self._section(form, tr("section.interface"), row, t)
        self._label(form, tr("interface.language"), row, t)
        langs = tk.Frame(form, bg=t["bg"])
        langs.grid(row=row, column=1, sticky="w", pady=(2, 0))
        for code in ("pt", "en", "es"):
            widgets.PillButton(
                langs,
                SHORT[code],
                lambda c=code: self.set_language(c),
                t,
                active=(code == self.language),
                width=48,
                height=26,
                font=MONO_S,
            ).pack(side="left", padx=(0, 6))
        row += 1
        widgets.Switch(
            form,
            tr("interface.animations"),
            self.animations_var,
            self._animations_changed,
            t,
            BODY_S,
        ).grid(row=row, column=1, sticky="w", pady=(8, 0))
        row += 1
        tk.Label(
            form,
            text=tr("interface.animations_hint"),
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=(0, 2))
        row += 1

        row = self._section(form, tr("section.telemetry"), row, t)
        telemetry = tk.Frame(form, bg=t["panel"], highlightthickness=1, highlightbackground=t["line"])
        telemetry.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self.telemetry_vars = {}
        for i, (key, label) in enumerate(
            [
                ("latency", "telemetry.latency"),
                ("tokens", "telemetry.tokens"),
                ("cost", "telemetry.cost"),
            ]
        ):
            telemetry.columnconfigure(i, weight=1)
            cell = tk.Frame(telemetry, bg=t["panel"])
            cell.grid(row=0, column=i, sticky="ew", padx=10, pady=6)
            tk.Label(cell, text=tr(label), bg=t["panel"], fg=t["dim"], font=MONO_S, anchor="w").pack(
                anchor="w"
            )
            var = tk.StringVar(value="—")
            self.telemetry_vars[key] = var
            tk.Label(
                cell,
                textvariable=var,
                bg=t["panel"],
                fg=t["accent"],
                font=DISPLAY_S,
                anchor="w",
            ).pack(anchor="w")

    def _build_right(self, parent, t):
        parent.columnconfigure(0, weight=1)
        r = self._section(parent, tr("section.preview"), 0, t, grid=True)
        preview = tk.Canvas(
            parent,
            width=310,
            height=174,
            bg=t["panel"],
            highlightthickness=1,
            highlightbackground=t["line"],
        )
        preview.grid(row=r, column=0, sticky="w", pady=(4, 0))
        r += 1
        for x in range(0, 310, 20):
            preview.create_line(x, 0, x, 174, fill=t["grid"])
        for y in range(0, 174, 20):
            preview.create_line(0, y, 310, y, fill=t["grid"])
        preview.create_rectangle(24, 28, 286, 120, fill=t["card"], outline=t["card_line"])
        preview.create_rectangle(24, 28, 286, 48, fill=t["header"], outline=t["card_line"])
        preview.create_rectangle(24, 28, 28, 120, fill=t["accent"], outline="")
        preview.create_text(
            38,
            38,
            text=tr("overlay.kind.alert"),
            fill=t["accent"],
            font=(MONO_S[0], 6),
            anchor="w",
        )
        preview.create_text(276, 38, text="01", fill=t["dim"], font=(MONO_S[0], 6), anchor="e")
        preview.create_text(
            38,
            64,
            text=tr("overlay.preview_card"),
            fill=t["text"],
            font=BODY_S,
            anchor="nw",
        )
        preview.create_text(
            38,
            106,
            text=tr("overlay.card_footer_short"),
            fill=t["dim"],
            font=(MONO_S[0], 5),
            anchor="w",
        )
        mode = tr("themes.dark" if t["mode"] == "dark" else "themes.light")
        preview.create_text(
            24,
            142,
            text=f"{t['name'].upper()} / {mode}",
            fill=t["muted"],
            font=MONO_S,
            anchor="w",
        )
        preview.create_text(
            286,
            142,
            text=tr("main.points", n=3, latency="7.5"),
            fill=t["dim"],
            font=MONO_S,
            anchor="e",
        )

        r = self._section(parent, tr("section.themes"), r, t, grid=True, pady=(14, 0))
        tk.Label(
            parent,
            text=tr("themes.hint"),
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
        ).grid(row=r, column=0, sticky="w", pady=(0, 2))
        r += 1
        themes_frame = tk.Frame(parent, bg=t["bg"])
        themes_frame.grid(row=r, column=0, sticky="ew")
        themes_frame.columnconfigure(0, weight=1)
        themes_frame.columnconfigure(1, weight=1)
        tr_row = 0
        for group, keys in [(tr("themes.dark"), theme.DARK), (tr("themes.light"), theme.LIGHT)]:
            tk.Label(themes_frame, text=group, bg=t["bg"], fg=t["dim"], font=MONO_S).grid(
                row=tr_row, column=0, columnspan=2, sticky="w", pady=(4, 2)
            )
            tr_row += 1
            for i, key in enumerate(keys):
                card = widgets.ThemeCard(
                    themes_frame,
                    key,
                    key == self.theme_key,
                    self.set_theme,
                    t,
                    BODY_S,
                    (MONO_S[0], 7),
                )
                card.grid(row=tr_row + i // 2, column=i % 2, sticky="w", padx=(0, 4), pady=2)
            tr_row += (len(keys) + 1) // 2
        r += 1

        r = self._section(parent, tr("section.system"), r, t, grid=True, pady=(14, 0))
        panel = tk.Frame(parent, bg=t["panel"], highlightthickness=1, highlightbackground=t["line"])
        panel.grid(row=r, column=0, sticky="ew", pady=(4, 0))
        panel.columnconfigure(1, weight=1)
        self.sys_vars = {}
        rows = [
            ("provider", "system.provider"),
            ("credential", "system.credential"),
            ("consent", "system.consent"),
            ("privacy", "system.privacy"),
            ("cache", "system.cache"),
        ]
        for i, (key, label) in enumerate(rows):
            tk.Label(
                panel,
                text=tr(label),
                bg=t["panel"],
                fg=t["dim"],
                font=MONO_S,
                anchor="w",
            ).grid(row=i, column=0, sticky="w", padx=(10, 12), pady=(5 if i == 0 else 2, 0))
            var = tk.StringVar(value="—")
            self.sys_vars[key] = var
            tk.Label(
                panel,
                textvariable=var,
                bg=t["panel"],
                fg=t["text"],
                font=MONO_S,
                anchor="w",
                justify="left",
                wraplength=190,
            ).grid(row=i, column=1, sticky="w", padx=(0, 10), pady=(5 if i == 0 else 2, 0))
        tk.Frame(panel, bg=t["panel"], height=5).grid(row=len(rows), column=0, columnspan=2)

    def _section(self, parent, text, row, t, grid=False, pady=(14, 0)):
        if grid:
            f = tk.Frame(parent, bg=t["bg"])
            f.grid(row=row, column=0, sticky="ew", pady=pady)
            tk.Label(f, text=text, bg=t["bg"], fg=t["accent"], font=MONO_S).pack(side="left")
            tk.Frame(f, bg=t["line"], height=1).pack(
                side="left", fill="x", expand=True, padx=(10, 0), pady=(7, 0)
            )
            return row + 1
        f = tk.Frame(parent, bg=t["bg"])
        f.grid(row=row, column=0, columnspan=2, sticky="ew", pady=pady)
        tk.Label(f, text=text, bg=t["bg"], fg=t["accent"], font=MONO_S).pack(side="left")
        tk.Frame(f, bg=t["line"], height=1).pack(
            side="left", fill="x", expand=True, padx=(10, 0), pady=(7, 0)
        )
        return row + 1

    def _label(self, parent, text, row, t):
        tk.Label(parent, text=text, bg=t["bg"], fg=t["dim"], font=MONO_S, anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 14), pady=(6, 2)
        )

    # ------------------------------------------------------------------ state
    def _meta_text(self):
        meta = getattr(ai_client, "LAST_META", {}) or {}
        if not meta:
            return tr("status.no_scan")
        parts = []
        if meta.get("latency") is not None:
            parts.append(f"{meta['latency']:.1f}s")
        if meta.get("model"):
            parts.append(str(meta["model"]))
        usage = meta.get("usage") or {}
        if usage:
            parts.append(
                tr(
                    "status.tokens",
                    prompt=usage.get("prompt_tokens", 0),
                    completion=usage.get("completion_tokens", 0),
                )
            )
        cost = meta.get("cost")
        parts.append(f"US$ {cost:.4f}" if cost is not None else tr("status.cost_hint"))
        return "  ·  ".join(parts)

    def _refresh_meta(self):
        try:
            if not self.win.winfo_exists():
                return
            self.meta_var.set(self._meta_text())
            self._refresh_system()
            self._refresh_telemetry()
            self.win.after(1000, self._refresh_meta)
        except Exception:
            pass

    def _refresh_system(self):
        if not self.sys_vars:
            return
        try:
            self.sys_vars["provider"].set(self.provider_var.get() or "—")
            key = self.key_var.get().strip()
            if self.cfg.get("api_key_fallback"):
                credential = tr("system.key_file")
            elif key:
                credential = tr("system.keyring")
            else:
                credential = tr("system.missing")
            self.sys_vars["credential"].set(credential)
            self.sys_vars["consent"].set(
                tr("system.registered") if config.has_consent(self.cfg) else tr("system.pending")
            )
            blocks = len([line for line in self._block_cache.splitlines() if line.strip()])
            if self.pause_var.get():
                privacy = tr("system.private_on")
            else:
                privacy = f"{tr('system.private_off')} · {tr('system.blocks', n=blocks)}"
            self.sys_vars["privacy"].set(privacy)
            self.sys_vars["cache"].set(tr("system.cache_value"))
        except Exception:
            pass

    def _refresh_telemetry(self):
        if not self.telemetry_vars:
            return
        meta = getattr(ai_client, "LAST_META", {}) or {}
        latency = meta.get("latency")
        usage = meta.get("usage") or {}
        cost = meta.get("cost")
        try:
            self.telemetry_vars["latency"].set(f"{float(latency):.1f}s" if latency is not None else "—")
            self.telemetry_vars["tokens"].set(
                f"{usage.get('prompt_tokens', 0)}/{usage.get('completion_tokens', 0)}" if usage else "—"
            )
            self.telemetry_vars["cost"].set(f"US$ {float(cost):.4f}" if cost is not None else "—")
        except Exception:
            pass

    def _toggle_pause(self):
        self.cfg["paused"] = bool(self.pause_var.get())
        config.save(self.cfg)
        self.on_saved(self.cfg)
        self._update_led()

    def _update_led(self):
        self.state_var.set(tr("common.paused") if self.pause_var.get() else tr("common.ready"))
        self._refresh_system()
        if getattr(self, "led", None) is not None:
            t = theme.get(self.theme_key)
            try:
                self.led.itemconfigure("led", fill=t["warning"] if self.pause_var.get() else t["accent"])
            except Exception:
                pass

    def _toggle_key(self):
        self.show_key_var.set(not self.show_key_var.get())
        self.key_entry.configure(show="" if self.show_key_var.get() else "•")
        if getattr(self, "show_key_btn", None) is not None:
            self.show_key_btn.set_active(self.show_key_var.get())

    def _cycle_theme(self):
        keys = theme.DARK + theme.LIGHT
        try:
            idx = keys.index(self.theme_key)
        except ValueError:
            idx = 0
        self.set_theme(keys[(idx + 1) % len(keys)])

    def _animations_changed(self):
        self.cfg["animations"] = bool(self.animations_var.get())
        config.save(self.cfg)
        self._scan_y = 0.0

    def _on_provider(self, label: str):
        try:
            key = self.provider_keys[self.provider_labels.index(label)]
        except ValueError:
            key = "custom"
        preset = config.preset_for(key)
        self.base_var.set(preset.get("base_url", ""))
        self.model_var.set(preset.get("model", ""))
        if key == "ollama" and not self.key_var.get().strip():
            self.key_var.set("ollama")
        self.status_var.set(tr("msg.preset", label=preset.get("label")))
        self._refresh_system()

    def _form_cfg(self) -> dict[str, Any]:
        self._block_cache = self.block_text.get("1.0", "end").strip()
        cfg = dict(self.cfg)
        cfg["base_url"] = self.base_var.get().strip().rstrip("/")
        cfg["model"] = self.model_var.get().strip()
        cfg["provider"] = config.infer_provider(cfg["base_url"])
        cfg["paused"] = bool(self.pause_var.get())
        cfg["theme"] = self.theme_key
        cfg["language"] = self.language
        cfg["animations"] = bool(self.animations_var.get())
        cfg["hotkey_scan"] = self.hotkey_scan_var.get().strip()
        cfg["hotkey_bar"] = self.hotkey_bar_var.get().strip()
        cfg["hotkey_center"] = self.hotkey_center_var.get().strip()
        cfg["hotkey_pause"] = self.hotkey_pause_var.get().strip()
        cfg["blocklist"] = [line.strip() for line in self._block_cache.splitlines() if line.strip()]
        model = cfg["model"]
        pin, pout = self.price_in_var.get().strip(), self.price_out_var.get().strip()
        pricing = dict(cfg.get("pricing") or {})
        if pin or pout:
            try:
                pricing[model] = {"in": float(pin or 0), "out": float(pout or 0)}
            except ValueError:
                pricing.pop(model, None)
        else:
            pricing.pop(model, None)
        cfg["pricing"] = pricing
        return cfg

    def save(self):
        cfg = self._form_cfg()
        if not config.valid_url(cfg["base_url"]):
            self.status_var.set(tr("msg.invalid_url"))
            return
        if not cfg["model"]:
            self.status_var.set(tr("msg.model_required"))
            return
        if not self.key_var.get().strip() and config.preset_for(cfg["provider"]).get("needs_key", True):
            self.status_var.set(tr("msg.key_required"))
            return
        if not self.consent_var.get() and not config.has_consent(self.cfg):
            self.status_var.set(tr("msg.consent_required"))
            return
        if self.consent_var.get() and not config.has_consent(self.cfg):
            cfg = config.mark_consent(cfg)
        elif not self.consent_var.get():
            cfg["consent_at"] = None
        config.save(cfg)
        config.set_api_key(self.key_var.get().strip(), cfg)
        self.cfg = cfg
        ai_client.reload_config(cfg)
        self.on_saved(cfg)
        self.first_run = False
        self._render()
        self._draw_grid()
        self.status_var.set(tr("msg.saved"))

    def set_theme(self, key: str):
        if self._testing:
            self.status_var.set(tr("msg.test_wait"))
            return
        self._block_cache = self.block_text.get("1.0", "end").strip()
        self.theme_key = key
        theme.set_current(key)
        self.cfg["theme"] = key
        config.save(self.cfg)
        self.on_saved(self.cfg)
        self._render()
        self._draw_grid()
        self.status_var.set(tr("msg.theme", name=theme.get(key)["name"]))

    def set_language(self, code: str):
        self._block_cache = self.block_text.get("1.0", "end").strip()
        self.language = i18n.set_language(code)
        self.cfg["language"] = self.language
        config.save(self.cfg)
        self.on_saved(self.cfg)
        self._render()
        self._draw_grid()
        self.status_var.set(tr("msg.language", name=i18n.language_name(self.language)))

    def test_vision(self):
        if self._testing:
            return
        base = self.base_var.get().strip().rstrip("/")
        model = self.model_var.get().strip()
        key = self.key_var.get().strip() or ("ollama" if "localhost" in base else "")
        if not config.valid_url(base) or not model:
            self.status_var.set(tr("msg.test_incomplete"))
            return
        self._testing = True
        self.test_btn.set_enabled(False)
        self.status_var.set(tr("msg.testing"))

        def worker():
            try:
                ok, msg, latency = ai_client.test_vision(base, model, key)
                self._test_queue.put((ok, msg, latency))
            except Exception as exc:  # noqa: BLE001
                self._test_queue.put((False, tr("msg.test_error", exc=exc), 0.0))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_test(self):
        try:
            while True:
                ok, msg, latency = self._test_queue.get_nowait()
                self._testing = False
                if not self.win.winfo_exists():
                    return
                try:
                    self.test_btn.set_enabled(True)
                except Exception:
                    pass
                prefix = "OK" if ok else tr("common.failed")
                self.status_var.set(f"{prefix} · {msg} · {latency:.1f}s")
        except queue.Empty:
            pass
        try:
            if self.win.winfo_exists():
                self.win.after(150, self._poll_test)
        except Exception:
            pass

    def _sync_vars(self, cfg: dict[str, Any]) -> None:
        current = cfg.get("provider", "custom")
        self.provider_var.set(
            config.PRESETS.get(current, config.PRESETS["custom"])["label"]
        )
        self.base_var.set(cfg.get("base_url", ""))
        self.model_var.set(cfg.get("model", ""))
        self.key_var.set(config.get_api_key(cfg))
        self.consent_var.set(config.has_consent(cfg))
        self.pause_var.set(bool(cfg.get("paused", False)))
        self.animations_var.set(bool(cfg.get("animations", True)))
        self.hotkey_scan_var.set(cfg.get("hotkey_scan", ""))
        self.hotkey_bar_var.set(cfg.get("hotkey_bar", ""))
        self.hotkey_center_var.set(cfg.get("hotkey_center", ""))
        self.hotkey_pause_var.set(cfg.get("hotkey_pause", ""))
        self.show_key_var.set(False)
        price = (cfg.get("pricing") or {}).get(cfg.get("model", ""), {})
        self.price_in_var.set(str(price.get("in", "")) if price else "")
        self.price_out_var.set(str(price.get("out", "")) if price else "")
        blocklist = cfg.get("blocklist")
        if blocklist is None:
            blocklist = config.DEFAULT_BLOCKLIST
        self._block_cache = "\n".join(blocklist)
        self.state_var.set(
            tr("common.paused") if self.pause_var.get() else tr("common.ready")
        )

    def _yaml_error_text(self) -> str:
        return " ".join(config.LAST_YAML_ERROR.split())[:100]

    def open_yaml(self):
        try:
            import subprocess

            if not config.YAML_FILE.exists():
                config.save(self.cfg)
            subprocess.Popen(["xdg-open", str(config.YAML_FILE)])
        except Exception as exc:  # noqa: BLE001
            self.status_var.set(tr("msg.yaml_open_error", error=exc))

    def reload_yaml(self):
        cfg = config.load()
        if config.LAST_YAML_ERROR:
            self.status_var.set(
                tr("msg.yaml_error", error=self._yaml_error_text())
            )
            return
        self.cfg = cfg
        self.language = i18n.set_language(cfg.get("language", "pt"))
        self.theme_key = cfg.get("theme", "spectra")
        if self.theme_key not in theme.THEMES:
            self.theme_key = "spectra"
        theme.set_current(self.theme_key)
        self._sync_vars(cfg)
        self.on_saved(cfg)
        self._render()
        self._draw_grid()
        self.status_var.set(tr("msg.yaml_reloaded"))

    def open_logs(self):
        try:
            import subprocess

            config.STATE_DIR.mkdir(parents=True, exist_ok=True)
            config.LOG_FILE.touch(exist_ok=True)
            subprocess.Popen(["xdg-open", str(config.LOG_FILE)])
        except Exception as exc:  # noqa: BLE001
            self.status_var.set(tr("msg.log_error", exc=exc))

    def clear_cache(self):
        config.clear_session_cache()
        try:
            from session_memory import session

            session.history.clear()
            session.current_context = "Ambiente Inicial"
            session.last_activity_time = 0.0
            session.save()
        except Exception:
            pass
        self.status_var.set(tr("msg.cache_cleared"))

    def _hide_window(self):
        try:
            self.win.withdraw()
        except Exception:
            pass

    def quit(self):
        self.close()
        self.on_quit()

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
