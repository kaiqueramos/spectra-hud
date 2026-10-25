"""Centro de comando / wizard de primeira execução do Spectra."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from typing import Any, Callable

import mss

import ai_client
import config

INK = "#080a08"
PANEL = "#0d110d"
LINE = "#2a3227"
BONE = "#ece8dc"
TEXT = "#c9c6ba"
DIM = "#7a8276"
SIGNAL = "#ff5a1f"
MONO = ("DejaVu Sans Mono", 9)
MONO_B = ("DejaVu Sans Mono", 9, "bold")
BODY = ("DejaVu Sans", 10)
BODY_B = ("DejaVu Sans", 10, "bold")
LABEL = ("DejaVu Sans Mono", 8)


class CommandCenter:
    def __init__(
        self,
        root: tk.Tk,
        on_saved: Callable[[dict[str, Any]], None],
        on_quit: Callable[[], None],
        first_run: bool = False,
    ):
        self.root = root
        self.on_saved = on_saved
        self.on_quit = on_quit
        self.first_run = first_run
        self.cfg = config.load()
        self._test_queue: queue.Queue = queue.Queue()
        self._testing = False

        self.win = tk.Toplevel(root)
        self.win.title("Spectra HUD — Centro de Comando")
        self.win.configure(bg=INK)
        self.win.attributes("-topmost", True)
        self.win.geometry("860x880")
        self.win.minsize(760, 720)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.bind("<Control-s>", lambda _e: self.save())
        self.win.bind("<F5>", lambda _e: self.test_vision())

        monitor = self._target_monitor()
        x = monitor["left"] + max(10, (monitor["width"] - 860) // 2)
        y = monitor["top"] + max(20, (monitor["height"] - 880) // 2)
        self.win.geometry(f"860x880+{x}+{y}")

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
        self.price_in_var = tk.StringVar(
            value=str(price.get("in", "")) if price else ""
        )
        self.price_out_var = tk.StringVar(
            value=str(price.get("out", "")) if price else ""
        )

        self._build()
        self._refresh_meta()
        self.win.after(100, self._poll_test)
        self.win.after(700, self._refresh_meta)
        self.win.update_idletasks()
        print(
            "BTN test", self.test_btn.winfo_rootx(), self.test_btn.winfo_rooty(),
            "size", self.test_btn.winfo_width(), self.test_btn.winfo_height(),
            flush=True,
        )
        self.win.lift()
        self.win.focus_force()

    def _target_monitor(self) -> dict:
        """Monitor sob o cursor (ou o primário) para não abrir no outro display."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors[1:] or [sct.monitors[0]]
                for mon in monitors:
                    if mon.get("is_primary"):
                        return mon
                return monitors[0]
        except Exception:
            return {"left": 0, "top": 0, "width": 1920, "height": 1080}

    # ------------------------------------------------------------------ UI
    def _build(self):
        wrap = tk.Frame(self.win, bg=INK)
        wrap.pack(fill="both", expand=True, padx=28, pady=22)

        head = tk.Frame(wrap, bg=INK)
        head.pack(fill="x")
        tk.Label(
            head,
            text="SPECTRA",
            bg=INK,
            fg=BONE,
            font=("DejaVu Sans Condensed", 20, "bold"),
        ).pack(side="left")
        tk.Label(head, text=" / COMMAND CENTER", bg=INK, fg=DIM, font=MONO).pack(
            side="left", padx=(8, 0), pady=(6, 0)
        )
        tk.Label(
            head,
            text="v0.1.0  ·  X11",
            bg=INK,
            fg=DIM,
            font=LABEL,
        ).pack(side="right", pady=(6, 0))

        if (
            self.first_run
            or not config.has_consent(self.cfg)
            or not config.get_api_key(self.cfg)
        ):
            banner = tk.Frame(
                wrap, bg="#160d07", highlightthickness=1, highlightbackground=SIGNAL
            )
            banner.pack(fill="x", pady=(16, 0))
            tk.Label(
                banner,
                text="Primeira execução: escolha o provedor, cole a chave e teste a visão antes de salvar.",
                bg="#160d07",
                fg=TEXT,
                font=BODY,
                anchor="w",
                padx=12,
                pady=9,
            ).pack(fill="x")

        form = tk.Frame(wrap, bg=INK)
        form.pack(fill="x", pady=(18, 0))
        form.columnconfigure(1, weight=1)

        row = 0
        self._label(form, "PROVEDOR", row)
        menu = tk.OptionMenu(
            form, self.provider_var, *self.provider_labels, command=self._on_provider
        )
        menu.configure(
            bg=PANEL,
            fg=BONE,
            activebackground=PANEL,
            activeforeground=SIGNAL,
            highlightthickness=1,
            highlightbackground=LINE,
            relief="flat",
            font=BODY,
            anchor="w",
            padx=8,
        )
        menu["menu"].configure(
            bg=PANEL,
            fg=BONE,
            activebackground=SIGNAL,
            activeforeground="#080a08",
            font=BODY,
        )
        menu.grid(row=row, column=1, sticky="ew", pady=3)

        row += 1
        self._label(form, "BASE URL", row)
        self._entry(form, self.base_var, row)

        row += 1
        self._label(form, "MODELO", row)
        self._entry(form, self.model_var, row)

        row += 1
        self._label(form, "API KEY", row)
        key_wrap = tk.Frame(form, bg=INK)
        key_wrap.grid(row=row, column=1, sticky="ew", pady=3)
        key_wrap.columnconfigure(0, weight=1)
        self.key_entry = tk.Entry(
            key_wrap,
            textvariable=self.key_var,
            show="•",
            bg=PANEL,
            fg=BONE,
            insertbackground=SIGNAL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=MONO,
            width=40,
        )
        self.key_entry.grid(row=0, column=0, sticky="ew", ipady=5)
        tk.Checkbutton(
            key_wrap,
            text="mostrar",
            variable=self.show_key_var,
            command=self._toggle_key,
            bg=INK,
            fg=DIM,
            selectcolor=INK,
            activebackground=INK,
            activeforeground=BONE,
            font=LABEL,
            highlightthickness=0,
            bd=0,
        ).grid(row=0, column=1, padx=(8, 0))

        row += 1
        consent = tk.Checkbutton(
            form,
            text="Entendo que cada scan envia um JPEG da tela ativa para o provedor escolhido.",
            variable=self.consent_var,
            bg=INK,
            fg=TEXT,
            selectcolor=INK,
            activebackground=INK,
            activeforeground=BONE,
            font=BODY,
            highlightthickness=0,
            bd=0,
            anchor="w",
            justify="left",
            wraplength=560,
        )
        consent.grid(row=row, column=1, sticky="w", pady=(8, 2))

        row += 1
        pause = tk.Checkbutton(
            form,
            text="Iniciar pausado (private mode): nada é capturado até você retomar.",
            variable=self.pause_var,
            bg=INK,
            fg=TEXT,
            selectcolor=INK,
            activebackground=INK,
            activeforeground=BONE,
            font=BODY,
            highlightthickness=0,
            bd=0,
            anchor="w",
        )
        pause.grid(row=row, column=1, sticky="w", pady=2)

        # blocklist
        row += 1
        self._label(form, "BLOQUEIO", row)
        block_wrap = tk.Frame(form, bg=INK)
        block_wrap.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        tk.Label(
            block_wrap,
            text="Se o título da janela ativa contiver um destes termos, o scan é bloqueado (um por linha):",
            bg=INK,
            fg=DIM,
            font=LABEL,
            anchor="w",
        ).pack(fill="x")
        self.block_text = tk.Text(
            block_wrap,
            height=5,
            bg=PANEL,
            fg=TEXT,
            insertbackground=SIGNAL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=MONO,
            padx=8,
            pady=6,
            wrap="word",
        )
        self.block_text.pack(fill="x", pady=(4, 0))
        self.block_text.insert(
            "1.0", "\n".join(self.cfg.get("blocklist") or config.DEFAULT_BLOCKLIST)
        )

        # hotkeys
        row += 1
        self._label(form, "ATALHOS", row)
        hk = tk.Frame(form, bg=INK)
        hk.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        for i, (label, var) in enumerate(
            [
                ("scan", self.hotkey_scan_var),
                ("barra", self.hotkey_bar_var),
                ("centro", self.hotkey_center_var),
                ("pausa", self.hotkey_pause_var),
            ]
        ):
            tk.Label(hk, text=label, bg=INK, fg=DIM, font=LABEL).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2
            )
            tk.Entry(
                hk,
                textvariable=var,
                bg=PANEL,
                fg=TEXT,
                insertbackground=SIGNAL,
                relief="flat",
                highlightthickness=1,
                highlightbackground=LINE,
                font=MONO,
                width=28,
            ).grid(row=i, column=1, sticky="w", pady=2, ipady=4)

        # pricing
        row += 1
        self._label(form, "PREÇO / 1M", row)
        price_wrap = tk.Frame(form, bg=INK)
        price_wrap.grid(row=row, column=1, sticky="w", pady=3)
        tk.Label(price_wrap, text="in $", bg=INK, fg=DIM, font=LABEL).pack(side="left")
        tk.Entry(
            price_wrap,
            textvariable=self.price_in_var,
            bg=PANEL,
            fg=TEXT,
            insertbackground=SIGNAL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=MONO,
            width=10,
        ).pack(side="left", padx=(4, 14), ipady=4)
        tk.Label(price_wrap, text="out $", bg=INK, fg=DIM, font=LABEL).pack(side="left")
        tk.Entry(
            price_wrap,
            textvariable=self.price_out_var,
            bg=PANEL,
            fg=TEXT,
            insertbackground=SIGNAL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=MONO,
            width=10,
        ).pack(side="left", padx=(4, 0), ipady=4)

        # status
        status_wrap = tk.Frame(
            wrap, bg=PANEL, highlightthickness=1, highlightbackground=LINE
        )
        status_wrap.pack(fill="x", pady=(18, 0))
        tk.Label(status_wrap, text="STATUS", bg=PANEL, fg=SIGNAL, font=LABEL).pack(
            anchor="w", padx=12, pady=(9, 0)
        )
        tk.Label(
            status_wrap,
            textvariable=self.meta_var,
            bg=PANEL,
            fg=TEXT,
            font=MONO,
            anchor="w",
            justify="left",
            padx=12,
            pady=4,
        ).pack(fill="x")
        tk.Label(
            status_wrap,
            textvariable=self.status_var,
            bg=PANEL,
            fg=DIM,
            font=MONO,
            anchor="w",
            justify="left",
            padx=12,
        ).pack(fill="x", pady=(0, 9))

        # buttons
        btns = tk.Frame(wrap, bg=INK)
        btns.pack(fill="x", pady=(18, 0))
        self.test_btn = self._button(
            btns, "TESTAR VISÃO", self.test_vision, outline=True
        )
        self.test_btn.pack(side="left")
        self._button(btns, "SALVAR", self.save, primary=True).pack(
            side="left", padx=(10, 0)
        )
        self._button(btns, "ABRIR LOGS", self.open_logs, outline=True).pack(
            side="left", padx=(10, 0)
        )
        self._button(btns, "LIMPAR CACHE", self.clear_cache, outline=True).pack(
            side="left", padx=(10, 0)
        )
        self._button(btns, "SAIR", self.quit, outline=True).pack(side="right")

        foot = tk.Frame(wrap, bg=INK)
        foot.pack(fill="x", pady=(14, 0))
        tk.Label(
            foot,
            text="Dica: o teste envia uma imagem vermelha/azul e confirma se o modelo realmente enxerga.",
            bg=INK,
            fg=DIM,
            font=LABEL,
            anchor="w",
        ).pack(fill="x")

    def _label(self, parent, text, row):
        tk.Label(parent, text=text, bg=INK, fg=DIM, font=LABEL, anchor="w").grid(
            row=row, column=0, sticky="w", padx=(0, 16), pady=(8, 2)
        )

    def _entry(self, parent, var, row):
        tk.Entry(
            parent,
            textvariable=var,
            bg=PANEL,
            fg=BONE,
            insertbackground=SIGNAL,
            relief="flat",
            highlightthickness=1,
            highlightbackground=LINE,
            font=MONO,
            width=48,
        ).grid(row=row, column=1, sticky="ew", pady=3, ipady=5)

    def _button(self, parent, text, command, primary=False, outline=False):
        bg = SIGNAL if primary else PANEL
        fg = "#080a08" if primary else TEXT
        b = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=BONE if primary else LINE,
            activeforeground=INK,
            relief="flat",
            highlightthickness=1,
            highlightbackground=SIGNAL if primary else LINE,
            font=MONO_B,
            padx=14,
            pady=7,
            cursor="hand2",
            bd=0,
        )
        return b

    # ------------------------------------------------------------------ actions
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

    def _toggle_key(self):
        self.key_entry.configure(show="" if self.show_key_var.get() else "•")

    def _form_cfg(self) -> dict[str, Any]:
        cfg = dict(self.cfg)
        cfg["base_url"] = self.base_var.get().strip().rstrip("/")
        cfg["model"] = self.model_var.get().strip()
        cfg["provider"] = config.infer_provider(cfg["base_url"])
        cfg["paused"] = bool(self.pause_var.get())
        cfg["hotkey_scan"] = self.hotkey_scan_var.get().strip()
        cfg["hotkey_bar"] = self.hotkey_bar_var.get().strip()
        cfg["hotkey_center"] = self.hotkey_center_var.get().strip()
        cfg["hotkey_pause"] = self.hotkey_pause_var.get().strip()
        cfg["blocklist"] = [
            line.strip()
            for line in self.block_text.get("1.0", "end").splitlines()
            if line.strip()
        ]
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
        if not self.key_var.get().strip() and config.preset_for(cfg["provider"]).get(
            "needs_key", True
        ):
            self.status_var.set("Informe a API key (ou use Ollama local).")
            return
        if not self.consent_var.get() and not config.has_consent(self.cfg):
            self.status_var.set(
                "Marque o consentimento de envio do screenshot antes de salvar."
            )
            return
        if self.consent_var.get() and not config.has_consent(self.cfg):
            cfg = config.mark_consent(cfg)
        config.save(cfg)
        config.set_api_key(self.key_var.get().strip(), cfg)
        self.cfg = cfg
        ai_client.reload_config(cfg)
        self.on_saved(cfg)
        self.status_var.set("Salvo. Atalhos novos exigem reiniciar o app.")
        self._refresh_meta()
        self.first_run = False
        if self.banner is not None:
            try:
                self.banner.pack_forget()
            except Exception:
                pass
            self.banner = None

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
        self.status_var.set("Testando visão... (pode levar alguns segundos)")

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
                self.test_btn.configure(state="normal")
                prefix = "OK" if ok else "FALHOU"
                self.status_var.set(f"{prefix} · {msg} · {latency:.1f}s")
        except queue.Empty:
            pass
        if self.win.winfo_exists():
            self.win.after(150, self._poll_test)

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
            parts.append(
                f"{usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out"
            )
        cost = meta.get("cost")
        if cost is not None:
            parts.append(f"US$ {cost:.4f}")
        else:
            parts.append("custo: configure preço")
        return "  ·  ".join(parts) if parts else "Sem dados."

    def _refresh_meta(self):
        if not self.win.winfo_exists():
            return
        self.meta_var.set(self._meta_text())
        self.win.after(1000, self._refresh_meta)

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
