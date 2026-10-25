"""Centro de comando / wizard do Spectra, com temas dark e light."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from typing import Any, Callable

import mss

import ai_client
import config
import fonts
import theme

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
        self.theme_key = self.cfg.get("theme", "spectra")
        theme.set_current(self.theme_key)
        self._test_queue: queue.Queue = queue.Queue()
        self._testing = False
        self._block_cache = "\n".join(self.cfg.get("blocklist") or config.DEFAULT_BLOCKLIST)
        self._led_on = True

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
        self.hotkey_scan_var = tk.StringVar(value=self.cfg.get("hotkey_scan", ""))
        self.hotkey_bar_var = tk.StringVar(value=self.cfg.get("hotkey_bar", ""))
        self.hotkey_center_var = tk.StringVar(value=self.cfg.get("hotkey_center", ""))
        self.hotkey_pause_var = tk.StringVar(value=self.cfg.get("hotkey_pause", ""))
        self.status_var = tk.StringVar(value="")
        self.meta_var = tk.StringVar(value=self._meta_text())
        self.show_key_var = tk.BooleanVar(value=False)
        price = (self.cfg.get("pricing") or {}).get(self.cfg.get("model", ""), {})
        self.price_in_var = tk.StringVar(value=str(price.get("in", "")) if price else "")
        self.price_out_var = tk.StringVar(value=str(price.get("out", "")) if price else "")

        self.win = tk.Toplevel(root)
        self.win.title("Spectra HUD — Command Center")
        self.win.configure(bg=theme.current()["bg"])
        self.win.attributes("-topmost", True)
        self.win.minsize(900, 820)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.bind("<Control-s>", lambda _e: self.save())
        self.win.bind("<F5>", lambda _e: self.test_vision())
        self.win.bind("<Control-t>", lambda _e: self._cycle_theme())

        mon = self._target_monitor()
        w, h = 1060, 900
        x = mon["left"] + max(10, (mon["width"] - w) // 2)
        y = mon["top"] + max(20, (mon["height"] - h) // 2)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        self.canvas = tk.Canvas(self.win, bg=theme.current()["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw_grid())

        self.body = tk.Frame(self.win, bg=theme.current()["bg"])
        self.body.place(x=26, y=20, relwidth=1, relheight=1, width=-52, height=-40)

        self._render()
        self.win.after(100, self._poll_test)
        self.win.after(700, self._refresh_meta)
        self.win.after(600, self._pulse)
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

    def _draw_grid(self):
        t = theme.get(self.theme_key)
        c = self.canvas
        if not c.winfo_exists():
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

    def _pulse(self):
        if not self.win.winfo_exists():
            return
        try:
            if self.pause_var.get():
                self.led.itemconfigure("led", fill=theme.get(self.theme_key)["warning"])
            else:
                self._led_on = not self._led_on
                t = theme.get(self.theme_key)
                self.led.itemconfigure("led", fill=t["accent"] if self._led_on else t["line2"])
        except Exception:
            pass
        self.win.after(700, self._pulse)

    # ------------------------------------------------------------------ render
    def _render(self):
        t = theme.get(self.theme_key)
        theme.set_current(self.theme_key)
        self.win.configure(bg=t["bg"])
        self.canvas.configure(bg=t["bg"])
        self.body.configure(bg=t["bg"])
        for child in self.body.winfo_children():
            child.destroy()

        head = tk.Frame(self.body, bg=t["bg"])
        head.pack(fill="x")

        mark = tk.Canvas(head, width=30, height=30, bg=t["bg"], highlightthickness=0)
        mark.create_line(3, 9, 3, 3, 9, 3, fill=t["accent"], width=2)
        mark.create_line(21, 3, 27, 3, 27, 9, fill=t["accent"], width=2)
        mark.create_line(27, 21, 27, 27, 21, 27, fill=t["accent"], width=2)
        mark.create_line(9, 27, 3, 27, 3, 21, fill=t["accent"], width=2)
        mark.create_rectangle(13, 13, 17, 17, fill=t["accent"], outline="")
        mark.pack(side="left", pady=(2, 0))

        title = tk.Frame(head, bg=t["bg"])
        title.pack(side="left", padx=(10, 0))
        tk.Label(title, text="SPECTRA", bg=t["bg"], fg=t["text"], font=DISPLAY).pack(side="left")
        tk.Label(title, text="/ COMMAND CENTER", bg=t["bg"], fg=t["dim"], font=MONO).pack(
            side="left", padx=(8, 0), pady=(7, 0)
        )

        right = tk.Frame(head, bg=t["bg"])
        right.pack(side="right")
        self.led = tk.Canvas(right, width=12, height=12, bg=t["bg"], highlightthickness=0)
        self.led.create_oval(2, 2, 10, 10, fill=t["accent"], outline="", tags="led")
        self.led.pack(side="left", padx=(0, 6), pady=(4, 0))
        state = "PAUSED" if self.pause_var.get() else "READY"
        tk.Label(right, text=state, bg=t["bg"], fg=t["dim"], font=MONO_S).pack(side="left", padx=(0, 14))
        tk.Label(
            right,
            text=f"{t['mode'].upper()} · {t['name'].upper()}",
            bg=t["bg"],
            fg=t["accent"],
            font=MONO_S,
        ).pack(side="left", padx=(0, 14))
        tk.Label(right, text="v0.1.0", bg=t["bg"], fg=t["dim"], font=MONO_S).pack(side="left")

        rule = tk.Frame(self.body, bg=t["line"], height=1)
        rule.pack(fill="x", pady=(12, 0))

        banner = None
        if self.first_run or not config.has_consent(self.cfg) or not config.get_api_key(self.cfg):
            banner = tk.Frame(self.body, bg=t["panel"], highlightthickness=1, highlightbackground=t["accent"])
            banner.pack(fill="x", pady=(10, 0))
            tk.Label(
                banner,
                text="FIRST RUN  /  escolha o provedor, cole a chave, teste a visão e aceite o consentimento.",
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
        tk.Label(status, text="LAST SCAN", bg=t["panel"], fg=t["accent"], font=MONO_S).pack(
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
        self.test_btn = self._button(actions, "TESTAR VISÃO", self.test_vision, t, primary=False)
        self.test_btn.pack(side="left")
        if self._testing:
            self.test_btn.configure(state="disabled")
        self._button(actions, "SALVAR", self.save, t, primary=True).pack(side="left", padx=(8, 0))
        self._button(actions, "LOGS", self.open_logs, t).pack(side="right")
        self._button(actions, "LIMPAR CACHE", self.clear_cache, t).pack(side="right", padx=(0, 8))
        self._button(actions, "SAIR", self.quit, t).pack(side="right", padx=(0, 8))

        if banner is not None:
            self.first_run = True

    def _build_left(self, parent, t):
        form = parent
        form.columnconfigure(1, weight=1)
        row = 0
        row = self._section(form, "01 / CONNECTION", row, t)

        self._label(form, "PROVIDER", row, t)
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
            ("BASE URL", self.base_var, ""),
            ("MODELO", self.model_var, ""),
            ("API KEY", self.key_var, "•"),
        ]:
            self._label(form, label, row, t)
            if label == "API KEY":
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
                tk.Checkbutton(
                    wrap,
                    text="mostrar",
                    variable=self.show_key_var,
                    command=self._toggle_key,
                    bg=t["bg"],
                    fg=t["dim"],
                    selectcolor=t["panel"],
                    activebackground=t["bg"],
                    activeforeground=t["text"],
                    font=MONO_S,
                    highlightthickness=0,
                    bd=0,
                ).grid(row=0, column=1, padx=(8, 0))
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

        cons = tk.Checkbutton(
            form,
            text="Consinto em enviar um JPEG da tela ativa para o provedor escolhido.",
            variable=self.consent_var,
            bg=t["bg"],
            fg=t["text"],
            selectcolor=t["panel"],
            activebackground=t["bg"],
            activeforeground=t["text"],
            font=BODY,
            highlightthickness=0,
            bd=0,
            anchor="w",
            wraplength=560,
        )
        cons.grid(row=row, column=1, sticky="w", pady=(8, 0))
        row += 1
        tk.Checkbutton(
            form,
            text="Iniciar pausado (private mode): nada é capturado até retomar.",
            variable=self.pause_var,
            command=self._update_led,
            bg=t["bg"],
            fg=t["text"],
            selectcolor=t["panel"],
            activebackground=t["bg"],
            activeforeground=t["text"],
            font=BODY,
            highlightthickness=0,
            bd=0,
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=(2, 0))
        row += 1

        row = self._section(form, "02 / GUARDRAILS", row, t)
        self._label(form, "BLOCKLIST", row, t)
        block_wrap = tk.Frame(form, bg=t["bg"])
        block_wrap.grid(row=row, column=1, sticky="ew", pady=(4, 0))
        block_wrap.columnconfigure(0, weight=1)
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
        self.block_text.grid(row=0, column=0, sticky="ew")
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
        scroll.grid(row=0, column=1, sticky="ns")
        self.block_text.configure(yscrollcommand=scroll.set)
        row += 1

        self._label(form, "ATALHOS", row, t)
        hk = tk.Frame(form, bg=t["bg"])
        hk.grid(row=row, column=1, sticky="w", pady=(4, 0))
        for i, (label, var) in enumerate(
            [
                ("scan", self.hotkey_scan_var),
                ("barra", self.hotkey_bar_var),
                ("centro", self.hotkey_center_var),
                ("pausa", self.hotkey_pause_var),
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

        row = self._section(form, "03 / METERING", row, t)
        self._label(form, "PREÇO / 1M", row, t)
        price = tk.Frame(form, bg=t["bg"])
        price.grid(row=row, column=1, sticky="w", pady=3)
        for label, var in [("in $", self.price_in_var), ("out $", self.price_out_var)]:
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

    def _build_right(self, parent, t):
        self._section(parent, "04 / PREVIEW", 0, t, grid=True)
        preview = tk.Canvas(
            parent,
            width=310,
            height=174,
            bg=t["panel"],
            highlightthickness=1,
            highlightbackground=t["line"],
        )
        preview.grid(row=1, column=0, sticky="w", pady=(4, 0))
        for x in range(0, 310, 20):
            preview.create_line(x, 0, x, 174, fill=t["grid"])
        for y in range(0, 174, 20):
            preview.create_line(0, y, 310, y, fill=t["grid"])
        preview.create_rectangle(24, 28, 286, 120, fill=t["card"], outline=t["card_line"])
        preview.create_rectangle(24, 28, 286, 48, fill=t["header"], outline=t["card_line"])
        preview.create_rectangle(24, 28, 28, 120, fill=t["accent"], outline="")
        preview.create_text(38, 38, text="ALERTA", fill=t["accent"], font=(MONO_S[0], 6), anchor="w")
        preview.create_text(276, 38, text="01", fill=t["dim"], font=(MONO_S[0], 6), anchor="e")
        preview.create_text(
            38,
            64,
            text="O retorno sai antes do commit.\nO ledger nunca é gravado.",
            fill=t["text"],
            font=BODY_S,
            anchor="nw",
        )
        preview.create_text(
            38, 106, text="CLIQUE P/ PERGUNTAR", fill=t["dim"], font=(MONO_S[0], 5), anchor="w"
        )
        preview.create_text(
            24,
            142,
            text=f"{t['name'].upper()} / {t['mode'].upper()}",
            fill=t["muted"],
            font=MONO_S,
            anchor="w",
        )
        preview.create_text(286, 142, text="3 PONTOS · 7.5s", fill=t["dim"], font=MONO_S, anchor="e")

        self._section(parent, "05 / THEMES", 2, t, grid=True, pady=(14, 0))
        tk.Label(
            parent,
            text="Ctrl+T cicla · aplica no HUD e no centro",
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(0, 2))
        themes_frame = tk.Frame(parent, bg=t["bg"])
        themes_frame.grid(row=4, column=0, sticky="ew", pady=(0, 0))
        themes_frame.columnconfigure(0, weight=1)
        themes_frame.columnconfigure(1, weight=1)
        r = 0
        for group, keys in [("DARK", theme.DARK), ("LIGHT", theme.LIGHT)]:
            tk.Label(themes_frame, text=group, bg=t["bg"], fg=t["dim"], font=MONO_S).grid(
                row=r, column=0, columnspan=2, sticky="w", pady=(4, 2)
            )
            r += 1
            for i, key in enumerate(keys):
                self._theme_button(themes_frame, key, r + i // 2, i % 2, t)
            r += (len(keys) + 1) // 2

    def _theme_button(self, parent, key: str, row: int, col: int, t):
        th = theme.get(key)
        selected = key == self.theme_key
        btn = tk.Button(
            parent,
            text=f"■  {th['name']}",
            command=lambda k=key: self.set_theme(k),
            bg=th["panel"],
            fg=th["accent"],
            activebackground=th["panel2"],
            activeforeground=th["accent"],
            highlightthickness=1,
            highlightbackground=t["accent"] if selected else t["line"],
            relief="flat",
            anchor="w",
            font=BODY_S,
            padx=8,
            pady=4,
            cursor="hand2",
            bd=0,
        )
        btn.grid(row=row, column=col, sticky="ew", padx=(0, 6), pady=2)

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

    def _button(self, parent, text, command, t, primary=False):
        bg = t["accent"] if primary else t["panel"]
        fg = t["accent_ink"] if primary else t["text"]
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=t["text"] if primary else t["line"],
            activeforeground=t["bg"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=t["accent"] if primary else t["line"],
            font=MONO_B,
            padx=13,
            pady=7,
            cursor="hand2",
            bd=0,
        )

    # ------------------------------------------------------------------ state
    def _meta_text(self):
        meta = getattr(ai_client, "LAST_META", {}) or {}
        if not meta:
            return "Nenhum scan ainda nesta sessão."
        parts = []
        if meta.get("latency") is not None:
            parts.append(f"{meta['latency']:.1f}s")
        if meta.get("model"):
            parts.append(str(meta["model"]))
        usage = meta.get("usage") or {}
        if usage:
            parts.append(f"{usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out")
        cost = meta.get("cost")
        parts.append(f"US$ {cost:.4f}" if cost is not None else "custo: configure preço")
        return "  ·  ".join(parts)

    def _refresh_meta(self):
        if not self.win.winfo_exists():
            return
        self.meta_var.set(self._meta_text())
        self.win.after(1000, self._refresh_meta)

    def _update_led(self):
        if getattr(self, "led", None) is not None:
            t = theme.get(self.theme_key)
            self.led.itemconfigure("led", fill=t["warning"] if self.pause_var.get() else t["accent"])

    def _toggle_key(self):
        self.key_entry.configure(show="" if self.show_key_var.get() else "•")

    def _cycle_theme(self):
        keys = theme.DARK + theme.LIGHT
        try:
            idx = keys.index(self.theme_key)
        except ValueError:
            idx = 0
        self.set_theme(keys[(idx + 1) % len(keys)])

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
        self.status_var.set(f"Preset: {preset.get('label')}")

    def _form_cfg(self) -> dict[str, Any]:
        self._block_cache = self.block_text.get("1.0", "end").strip()
        cfg = dict(self.cfg)
        cfg["base_url"] = self.base_var.get().strip().rstrip("/")
        cfg["model"] = self.model_var.get().strip()
        cfg["provider"] = config.infer_provider(cfg["base_url"])
        cfg["paused"] = bool(self.pause_var.get())
        cfg["theme"] = self.theme_key
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
            self.status_var.set("Base URL inválida. Use http:// ou https://.")
            return
        if not cfg["model"]:
            self.status_var.set("Informe o modelo.")
            return
        if not self.key_var.get().strip() and config.preset_for(cfg["provider"]).get("needs_key", True):
            self.status_var.set("Informe a API key (ou use Ollama local).")
            return
        if not self.consent_var.get() and not config.has_consent(self.cfg):
            self.status_var.set("Marque o consentimento antes de salvar.")
            return
        if self.consent_var.get() and not config.has_consent(self.cfg):
            cfg = config.mark_consent(cfg)
        config.save(cfg)
        config.set_api_key(self.key_var.get().strip(), cfg)
        self.cfg = cfg
        ai_client.reload_config(cfg)
        self.on_saved(cfg)
        self.first_run = False
        self.status_var.set("Salvo. Atalhos novos exigem reiniciar o app.")
        self._render()

    def set_theme(self, key: str):
        if self._testing:
            self.status_var.set("Aguarde o teste terminar para trocar o tema.")
            return
        self._block_cache = self.block_text.get("1.0", "end").strip()
        self.theme_key = key
        theme.set_current(key)
        self.cfg["theme"] = key
        config.save(self.cfg)
        self.on_saved(self.cfg)
        self._render()
        self._draw_grid()
        self.status_var.set(f"Tema: {theme.get(key)['name']}")

    def test_vision(self):
        if self._testing:
            return
        base = self.base_var.get().strip().rstrip("/")
        model = self.model_var.get().strip()
        key = self.key_var.get().strip() or ("ollama" if "localhost" in base else "")
        if not config.valid_url(base) or not model:
            self.status_var.set("Preencha base URL e modelo antes do teste.")
            return
        self._testing = True
        self.test_btn.configure(state="disabled")
        self.status_var.set("Testando visão...")

        def worker():
            try:
                ok, msg, latency = ai_client.test_vision(base, model, key)
                self._test_queue.put((ok, msg, latency))
            except Exception as exc:  # noqa: BLE001
                self._test_queue.put((False, f"Erro no teste: {exc}", 0.0))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_test(self):
        try:
            while True:
                ok, msg, latency = self._test_queue.get_nowait()
                self._testing = False
                if not self.win.winfo_exists():
                    return
                try:
                    self.test_btn.configure(state="normal")
                except Exception:
                    pass
                self.status_var.set(f"{'OK' if ok else 'FALHOU'} · {msg} · {latency:.1f}s")
        except queue.Empty:
            pass
        if self.win.winfo_exists():
            self.win.after(150, self._poll_test)

    def open_logs(self):
        try:
            import subprocess

            config.STATE_DIR.mkdir(parents=True, exist_ok=True)
            config.LOG_FILE.touch(exist_ok=True)
            subprocess.Popen(["xdg-open", str(config.LOG_FILE)])
        except Exception as exc:  # noqa: BLE001
            self.status_var.set(f"Não consegui abrir o log: {exc}")

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
        self.status_var.set("Cache de sessão limpo.")

    def quit(self):
        self.close()
        self.on_quit()

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
