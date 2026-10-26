"""Interface Wayland: painel de resultados normal, sem overlay ancorado."""

from __future__ import annotations

import tkinter as tk
from typing import Any, Callable

import i18n
import theme

MONO = ("DejaVu Sans Mono", 9)
MONO_S = ("DejaVu Sans Mono", 8)
BODY = ("DejaVu Sans", 10)
BODY_B = ("DejaVu Sans", 10, "bold")
COND = ("DejaVu Sans Condensed", 16, "bold")
DIM = "#7a8276"


def _colors() -> dict[str, Any]:
    t = theme.current()
    return t


class WaylandResults:
    def __init__(
        self,
        root: tk.Tk,
        on_ask: Callable[[int], None],
    ):
        self.root = root
        self.on_ask = on_ask
        self.win: tk.Toplevel | None = None
        self._items: list[dict] = []

    def is_open(self) -> bool:
        try:
            return self.win is not None and self.win.winfo_exists()
        except Exception:
            return False

    def item_at(self, index: int) -> dict | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def ask(self, index: int) -> None:
        if 0 <= index < len(self._items):
            self.on_ask(index)

    def show(self, insights: list[dict], meta: dict | None = None) -> None:
        self.close()
        t = _colors()
        self._items = insights
        win = tk.Toplevel(self.root)
        self.win = win
        win.title(i18n.tr("wayland.results_title"))
        try:
            win.attributes("-type", "dialog")
        except tk.TclError:
            pass
        win.configure(bg=t["bg"])
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", self.close)
        win.bind("<Escape>", lambda _e: self.close())
        head = tk.Frame(win, bg=t["bg"])
        head.pack(fill="x", padx=22, pady=(20, 0))
        tk.Label(head, text="SPECTRA", bg=t["bg"], fg=t["text"], font=COND).pack(side="left")
        tk.Label(head, text="/ " + i18n.tr("wayland.results_sub"), bg=t["bg"], fg=t["dim"], font=MONO_S).pack(
            side="left", padx=(8, 0), pady=(6, 0)
        )
        backend = str((meta or {}).get("backend") or "").upper()
        label = f"WAYLAND / {backend}" if backend else "WAYLAND"
        tk.Label(head, text=label, bg=t["bg"], fg=t["accent"], font=MONO_S).pack(
            side="right", pady=(6, 0)
        )

        info = []
        if meta:
            if meta.get("latency") is not None:
                info.append(f"{float(meta['latency']):.1f}s")
            if meta.get("model"):
                info.append(str(meta["model"]))
            usage = meta.get("usage") or {}
            if usage:
                info.append(f"{usage.get('prompt_tokens', 0)} in / {usage.get('completion_tokens', 0)} out")
            cost = meta.get("cost")
            if cost is not None:
                info.append(f"US$ {float(cost):.4f}")
        tk.Label(
            win,
            text="  ·  ".join(info) if info else i18n.tr("wayland.no_meta"),
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(8, 12))

        for index, item in enumerate(insights, 1):
            self._card(win, t, index, item)

        tk.Label(
            win,
            text=i18n.tr("wayland.footer"),
            bg=t["bg"],
            fg=t["dim"],
            font=MONO_S,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(12, 18))

        win.update_idletasks()
        width = 620
        height = max(300, win.winfo_reqheight())
        sw = max(800, self.root.winfo_screenwidth())
        sh = max(600, self.root.winfo_screenheight())
        win.geometry(
            f"{width}x{height}+{max(20, (sw - width) // 2)}+{max(40, (sh - height) // 2)}"
        )
        win.minsize(520, 220)
        win.lift()
        win.focus_force()

    def _card(self, parent, t, index: int, item: dict) -> None:
        color = (
            t["accent"]
            if item.get("kind") == "alerta"
            else (t["success"] if item.get("kind") == "item" else t["muted"])
        )
        frame = tk.Frame(
            parent,
            bg=t["panel"],
            highlightthickness=1,
            highlightbackground=t["line"],
            cursor="hand2",
        )
        frame.pack(fill="x", padx=22, pady=4)
        bar = tk.Frame(frame, bg=color, width=4)
        bar.pack(side="left", fill="y")
        body = tk.Frame(frame, bg=t["panel"])
        body.pack(side="left", fill="both", expand=True, padx=12, pady=9)
        tag = str(item.get("kind") or "info").upper()
        tk.Label(
            body,
            text=f"{tag}  /  {index:02d}",
            bg=t["panel"],
            fg=color,
            font=MONO_S,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            body,
            text=item.get("label") or i18n.tr("wayland.point"),
            bg=t["panel"],
            fg=t["text"],
            font=BODY_B,
            anchor="w",
        ).pack(fill="x", pady=(3, 0))
        tk.Label(
            body,
            text=item.get("insight") or "",
            bg=t["panel"],
            fg=t["text"],
            font=BODY,
            anchor="w",
            justify="left",
            wraplength=530,
        ).pack(fill="x", pady=(3, 0))
        for widget in (frame, bar, body, *body.winfo_children()):
            widget.bind("<Button-1>", lambda _e, i=index - 1: self.on_ask(i))

    def close(self) -> None:
        try:
            if self.win is not None and self.win.winfo_exists():
                self.win.destroy()
        except Exception:
            pass
        self.win = None


class WaylandAskDialog:
    def __init__(
        self,
        root: tk.Tk,
        title: str,
        subtitle: str,
        on_submit: Callable[[str, "WaylandAskDialog"], None],
    ):
        self.on_submit = on_submit
        t = _colors()
        self.win = tk.Toplevel(root)
        self.win.title(i18n.tr("wayland.ask_title"))
        try:
            self.win.attributes("-type", "dialog")
        except tk.TclError:
            pass
        self.win.configure(bg=t["bg"])
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.close)
        self.win.bind("<Escape>", lambda _e: self.close())
        w, h = 660, 180
        sw, sh = max(800, root.winfo_screenwidth()), max(600, root.winfo_screenheight())
        self.win.geometry(f"{w}x{h}+{max(20, (sw - w) // 2)}+{max(40, (sh - h) // 2)}")

        head = tk.Frame(self.win, bg=t["header"])
        head.pack(fill="x")
        tk.Label(
            head,
            text=f"◈ {title.upper()}",
            bg=t["header"],
            fg=t["accent"],
            font=MONO,
            anchor="w",
            padx=14,
            pady=9,
        ).pack(side="left")
        tk.Label(
            head,
            text=i18n.tr("wayland.esc"),
            bg=t["header"],
            fg=t["dim"],
            font=MONO_S,
            anchor="e",
            padx=14,
        ).pack(side="right")
        tk.Label(
            self.win,
            text=subtitle,
            bg=t["bg"],
            fg=t["muted"],
            font=BODY,
            anchor="w",
            padx=18,
            pady=10,
        ).pack(fill="x")
        self.entry = tk.Entry(
            self.win,
            bg=t["input"],
            fg=t["text"],
            insertbackground=t["accent"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=t["accent"],
            font=("DejaVu Sans", 11),
        )
        self.entry.pack(fill="x", padx=18, ipady=7)
        self.entry.focus_force()
        self.entry.bind("<Return>", lambda _e: self.submit())
        row = tk.Frame(self.win, bg=t["bg"])
        row.pack(fill="x", padx=18, pady=10)
        tk.Button(
            row,
            text=i18n.tr("wayland.send"),
            command=self.submit,
            bg=t["accent"],
            fg=t["accent_ink"],
            relief="flat",
            font=BODY_B,
            padx=14,
            pady=5,
            bd=0,
        ).pack(side="left")
        tk.Button(
            row,
            text=i18n.tr("wayland.close"),
            command=self.close,
            bg=t["panel"],
            fg=t["text"],
            relief="flat",
            font=BODY,
            padx=12,
            pady=5,
            bd=0,
        ).pack(side="left", padx=(8, 0))

    def submit(self) -> None:
        text = self.entry.get().strip()
        if not text:
            self.close()
            return
        self.entry.configure(state="disabled")
        self.on_submit(text, self)

    def show_answer(self, query: str, answer: str) -> None:
        t = _colors()
        for child in self.win.winfo_children():
            child.destroy()
        self.win.geometry("660x300")
        frame = tk.Frame(self.win, bg=t["bg"])
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=f"Q: {query}",
            bg=t["bg"],
            fg=t["dim"],
            font=BODY,
            anchor="w",
            justify="left",
            wraplength=600,
        ).pack(fill="x", padx=18, pady=(12, 4))
        answer_box = tk.Text(
            frame,
            height=6,
            bg=t["panel"],
            fg=t["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=t["line"],
            font=BODY,
            wrap="word",
            padx=12,
            pady=10,
        )
        answer_box.insert("1.0", answer)
        answer_box.configure(state="disabled")
        answer_box.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        tk.Button(
            frame,
            text=i18n.tr("wayland.close"),
            command=self.close,
            bg=t["panel"],
            fg=t["text"],
            relief="flat",
            font=BODY,
            padx=12,
            pady=5,
            bd=0,
        ).pack(anchor="e", padx=18, pady=(0, 12))
        self.win.bind("<Escape>", lambda _e: self.close())
        self.win.update_idletasks()

    def close(self) -> None:
        try:
            self.win.destroy()
        except Exception:
            pass
