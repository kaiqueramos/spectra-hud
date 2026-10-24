"""
Módulo de Overlay do HUD Cognitivo para o X11.
Suporta:
 - Drag-and-drop livre (clicar e arrastar o card para reposicionar).
 - Clique simples abre a caixa de pergunta sem disparar o drag.
 - Tipografia refinada, layout com cabeçalho e rodapé separados (zero sobreposição).
"""

import time
import math
import tkinter as tk
import tkinter.font as tkfont
import threading
from Xlib import display, X
from PIL import Image

import ai_client


# Identidade visual por tipo de ponto (campo "kind" devolvido pelo modelo).
KIND_STYLES = {
    "alerta": {"accent": "#F87171", "border": "#DC2626", "icon": "⚠", "tag": "ALERTA"},
    "acao": {"accent": "#34D399", "border": "#059669", "icon": "▶", "tag": "AÇÃO"},
    "item": {"accent": "#FBBF24", "border": "#D97706", "icon": "◆", "tag": "ITEM"},
    "info": {"accent": "#38BDF8", "border": "#0284C7", "icon": "●", "tag": "INFO"},
}


def get_kind_style(kind: str | None) -> dict:
    return KIND_STYLES.get(kind or "info", KIND_STYLES["info"])


def blend_hex(c1: str, c2: str, t: float) -> str:
    """Interpola duas cores #RRGGBB (t=0 -> c1, t=1 -> c2)."""
    a = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i : i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(x + (y - x) * t) for x, y in zip(a, b)]
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def box_to_pixels(
    box, monitor: dict, min_size: int = 24
) -> tuple[int, int, int, int] | None:
    """
    Converte box_2d [ymin, xmin, ymax, xmax] (0-1000) em (x, y, w, h) na tela.
    Devolve None se o box for nulo/inválido. Garante tamanho mínimo e limita ao monitor.
    """
    norm = ai_client.normalize_box(box)
    if norm is None:
        return None

    mon_x = monitor.get("left", 0)
    mon_y = monitor.get("top", 0)
    mon_w = monitor.get("width", 1920)
    mon_h = monitor.get("height", 1080)

    ymin, xmin, ymax, xmax = norm
    x1 = mon_x + int(xmin * mon_w / 1000)
    y1 = mon_y + int(ymin * mon_h / 1000)
    x2 = mon_x + int(xmax * mon_w / 1000)
    y2 = mon_y + int(ymax * mon_h / 1000)

    # Tamanho mínimo, crescendo a partir do centro.
    if x2 - x1 < min_size:
        cx = (x1 + x2) // 2
        x1, x2 = cx - min_size // 2, cx + min_size // 2
    if y2 - y1 < min_size:
        cy = (y1 + y2) // 2
        y1, y2 = cy - min_size // 2, cy + min_size // 2

    x1, y1 = max(mon_x, x1), max(mon_y, y1)
    x2, y2 = min(mon_x + mon_w, x2), min(mon_y + mon_h, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return x1, y1, x2 - x1, y2 - y1


def request_ewmh_focus(win):
    """Garante foco de teclado no GNOME Mutter via _NET_ACTIVE_WINDOW."""
    try:
        win.update_idletasks()
        xid = win.winfo_id()
        d = display.Display()
        xwin = d.create_resource_object("window", xid)
        root_win = d.screen().root
        net_active_window = d.intern_atom("_NET_ACTIVE_WINDOW")

        event = display.event.ClientMessage(
            window=xwin,
            client_type=net_active_window,
            data=(32, [1, X.CurrentTime, 0, 0, 0]),
        )
        root_win.send_event(
            event, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask
        )
        d.flush()
    except Exception as e:
        print(f"[EWMH Focus] {e}")


def rects_overlap(
    r1: tuple[int, int, int, int], r2: tuple[int, int, int, int], margin: int = 15
) -> bool:
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return not (
        x1 + w1 + margin <= x2
        or x2 + w2 + margin <= x1
        or y1 + h1 + margin <= y2
        or y2 + h2 + margin <= y1
    )


class CardWidget:
    """Card profissional flutuante, arrastável e interativo."""

    def __init__(
        self,
        parent_root,
        index: int,
        insight: dict,
        rect: tuple[int, int, int, int],
        on_click_callback,
    ):
        self.parent_root = parent_root
        self.index = index
        self.insight = insight
        self.on_click_callback = on_click_callback
        self.style = get_kind_style(insight.get("kind"))

        x, y, w, h = rect
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # Estados de drag
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.has_dragged = False

        self.win = tk.Toplevel(parent_root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.96)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        # Cores: acento e borda dependem do tipo do ponto; o resto é fixo.
        self.PRIMARY_ACCENT = self.style["accent"]
        self.BORDER_COLOR = self.style["border"]
        self.BG_DARK = "#0F172A"  # Slate 900
        self.HEADER_BG = "#1E293B"  # Slate 800
        self.FOOTER_BG = "#131E31"  # Slate mais escuro
        self.TEXT_COLOR = "#F8FAFC"  # Slate 50
        self.SUBTEXT_COLOR = "#94A3B8"  # Slate 400

        self.canvas = tk.Canvas(
            self.win,
            width=w,
            height=h,
            bg=self.BG_DARK,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR,
            cursor="fleur",
        )
        self.canvas.pack(fill="both", expand=True)

        self.render_base()

        # Eventos para Drag-and-drop e Clique
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def render_base(self):
        self.canvas.delete("all")
        raw_label = self.insight.get("label", "PONTO DE ATENÇÃO").upper()
        # Trunca título se for excessivamente longo para garantir elegância
        if len(raw_label) > 28:
            label = raw_label[:25] + "..."
        else:
            label = raw_label

        text = self.insight.get("insight", "")

        # 1. Cabeçalho limpo (ícone de arraste, tipo, título e tag do tipo)
        self.canvas.create_rectangle(0, 0, self.w, 28, fill=self.HEADER_BG, outline="")
        self.canvas.create_text(
            12,
            14,
            text="⠿",
            font=("DejaVu Sans", 11),
            fill=self.SUBTEXT_COLOR,
            anchor="w",
        )
        self.canvas.create_text(
            28,
            14,
            text=f"{self.style['icon']} [{self.index}] {label}",
            font=("DejaVu Sans", 9, "bold"),
            fill=self.PRIMARY_ACCENT,
            anchor="w",
        )
        self.canvas.create_text(
            self.w - 12,
            14,
            text=self.style["tag"],
            font=("DejaVu Sans", 7, "bold"),
            fill=self.SUBTEXT_COLOR,
            anchor="e",
        )

        # 2. Corpo do Insight no meio (com respiro e sem sobreposição)
        self.canvas.create_text(
            14,
            38,
            text=text,
            font=("DejaVu Sans", 10),
            fill=self.TEXT_COLOR,
            width=self.w - 28,
            anchor="nw",
        )

        # 3. Rodapé dedicado para a ação (separado na base do card)
        footer_y = self.h - 22
        self.canvas.create_rectangle(
            0, footer_y, self.w, self.h, fill=self.FOOTER_BG, outline=""
        )
        self.canvas.create_line(0, footer_y, self.w, footer_y, fill="#1E293B", width=1)
        self.canvas.create_text(
            12,
            footer_y + 11,
            text="CLIQUE P/ PERGUNTAR  •  ARRASTE P/ MOVER",
            font=("DejaVu Sans", 7, "bold"),
            fill=self.SUBTEXT_COLOR,
            anchor="w",
        )

        # 4. Faixa lateral na cor do tipo (identificação instantânea)
        self.canvas.create_rectangle(
            0, 0, 4, self.h, fill=self.PRIMARY_ACCENT, outline=""
        )

    def on_press(self, event):
        self.drag_start_x = event.x_root - self.x
        self.drag_start_y = event.y_root - self.y
        self.has_dragged = False

    def on_motion(self, event):
        new_x = event.x_root - self.drag_start_x
        new_y = event.y_root - self.drag_start_y

        if abs(new_x - self.x) > 4 or abs(new_y - self.y) > 4:
            self.has_dragged = True
            self.x = new_x
            self.y = new_y
            self.win.geometry(f"+{new_x}+{new_y}")

    def on_release(self, event):
        if not self.has_dragged:
            self.on_click_callback(self.index)

    def update_insight(self, new_text: str):
        self.insight["insight"] = new_text
        approx_lines = max(3, len(new_text) // 38 + 3)
        new_h = approx_lines * 20 + 60
        self.h = new_h
        self.win.geometry(f"{self.w}x{new_h}+{self.x}+{self.y}")
        self.canvas.config(height=new_h)
        self.render_base()


def compute_card_position(
    target: tuple[int, int, int, int] | None,
    card_w: int,
    card_h: int,
    monitor: dict,
    placed: list[tuple[int, int, int, int]],
) -> tuple[int, int]:
    """
    Escolhe onde colocar o card: ao lado do elemento (direita, esquerda, abaixo, acima),
    sem cobrir o próprio elemento nem outros cards. Sem elemento (target=None), usa uma
    coluna na borda direita do monitor.
    """
    mon_x = monitor.get("left", 0)
    mon_y = monitor.get("top", 0)
    mon_w = monitor.get("width", 1920)
    mon_h = monitor.get("height", 1080)

    def clamp(cx: int, cy: int) -> tuple[int, int]:
        cx = max(mon_x + 10, min(cx, mon_x + mon_w - card_w - 10))
        cy = max(mon_y + 25, min(cy, mon_y + mon_h - card_h - 25))
        return cx, cy

    if target is not None:
        tx, ty, tw, th = target
        raw = [
            (tx + tw + 20, ty),
            (tx - card_w - 20, ty),
            (tx, ty + th + 20),
            (tx, ty - card_h - 20),
        ]
    else:
        col_x = mon_x + mon_w - card_w - 30
        step = card_h + 15
        raw = []
        y = mon_y + 60
        while y + card_h <= mon_y + mon_h - 25:
            raw.append((col_x, y))
            y += step
        if not raw:
            raw = [(col_x, mon_y + 60)]

    candidates = [clamp(cx, cy) for cx, cy in raw]

    def free_of_cards(c: tuple[int, int]) -> bool:
        rect = (c[0], c[1], card_w, card_h)
        return not any(rects_overlap(rect, r) for r in placed)

    def free_of_target(c: tuple[int, int]) -> bool:
        if target is None:
            return True
        return not rects_overlap((c[0], c[1], card_w, card_h), target, margin=8)

    for c in candidates:
        if free_of_cards(c) and free_of_target(c):
            return c
    for c in candidates:
        if free_of_cards(c):
            return c

    if placed:
        last_x, last_y, _, last_h = placed[-1]
        best_x, best_y = last_x, last_y + last_h + 15
        if best_y + card_h > mon_y + mon_h - 25:
            best_y = mon_y + 35
            best_x = max(mon_x + 10, best_x - card_w - 20)
        return best_x, best_y
    return candidates[0]


def _make_edge_window(parent_root, x: int, y: int, w: int, h: int, color: str):
    win = tk.Toplevel(parent_root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.attributes("-alpha", 0.92)
    win.configure(bg=color)
    win.geometry(f"{w}x{h}+{x}+{y}")
    return win


class ElementHighlight:
    """Moldura fina na cor do tipo + selo numerado em volta do elemento apontado pelo card."""

    THICKNESS = 2
    BADGE_W = 24
    BADGE_H = 18

    def __init__(
        self,
        parent_root,
        index: int,
        kind: str | None,
        rect: tuple[int, int, int, int],
        on_click_callback,
        top_limit: int = 0,
    ):
        style = get_kind_style(kind)
        accent = style["accent"]
        x, y, w, h = rect
        t = self.THICKNESS

        edges = [
            (x, y, w, t),  # topo
            (x, y + h - t, w, t),  # base
            (x, y, t, h),  # esquerda
            (x + w - t, y, t, h),  # direita
        ]
        self.wins = [
            _make_edge_window(parent_root, ex, ey, ew, eh, accent)
            for ex, ey, ew, eh in edges
        ]

        # Selo numerado acima do canto superior esquerdo (ou dentro, se não houver espaço).
        by = y - self.BADGE_H if y - self.BADGE_H >= top_limit else y
        badge = _make_edge_window(
            parent_root, x, by, self.BADGE_W, self.BADGE_H, accent
        )
        label = tk.Label(
            badge,
            text=str(index),
            bg=accent,
            fg="#0F172A",
            font=("DejaVu Sans", 9, "bold"),
            cursor="hand2",
        )
        label.pack(fill="both", expand=True)
        label.bind("<ButtonRelease-1>", lambda e: on_click_callback(index))
        self.wins.append(badge)

    def destroy(self):
        for win in self.wins:
            try:
                win.destroy()
            except Exception:
                pass
        self.wins.clear()


class ScanIndicator:
    """Pílula no topo do monitor: 'escaneando' pulsando com cronômetro, ou mensagem curta (erro/aviso)."""

    H = 34
    BG = "#0F172A"

    def __init__(self, parent_root):
        self.root = parent_root
        self.win = None
        self.canvas = None
        self._dot = None
        self._text_id = None
        self._label = ""
        self._accent = KIND_STYLES["info"]["accent"]
        self._t0 = 0.0
        self._tick_job = None
        self._hide_job = None

    def _build(self, monitor: dict | None, text: str, reserve: str, kind: str):
        self.hide()
        style = get_kind_style(kind)
        self._accent = style["accent"]
        self._label = text

        font = tkfont.Font(family="DejaVu Sans", size=9, weight="bold")
        w = font.measure(reserve) + 60
        if monitor:
            mon_x, mon_y = monitor.get("left", 0), monitor.get("top", 0)
            mon_w = monitor.get("width", 1920)
        else:
            mon_x, mon_y, mon_w = 0, 0, self.root.winfo_screenwidth()
        x = mon_x + (mon_w - w) // 2
        y = mon_y + 24

        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.95)
        self.win.geometry(f"{w}x{self.H}+{x}+{y}")

        self.canvas = tk.Canvas(
            self.win,
            width=w,
            height=self.H,
            bg=self.BG,
            highlightthickness=1,
            highlightbackground=style["border"],
        )
        self.canvas.pack(fill="both", expand=True)
        cy = self.H // 2
        self._dot = self.canvas.create_oval(
            16, cy - 5, 26, cy + 5, fill=self._accent, outline=""
        )
        self._text_id = self.canvas.create_text(
            38,
            cy,
            text=text,
            font=("DejaVu Sans", 9, "bold"),
            fill="#F8FAFC",
            anchor="w",
        )

    def show_scanning(self, monitor: dict | None):
        label = "ESCANEANDO TELA…"
        self._build(monitor, label, f"{label}  999s", "info")
        self._t0 = time.time()
        self._tick()

    def _tick(self):
        if not self.win:
            return
        elapsed = time.time() - self._t0
        phase = (math.sin(elapsed * 6) + 1) / 2
        dim = blend_hex(self.BG, self._accent, 0.25)
        try:
            self.canvas.itemconfigure(self._dot, fill=blend_hex(dim, self._accent, phase))
            self.canvas.itemconfigure(
                self._text_id, text=f"{self._label}  {int(elapsed)}s"
            )
        except tk.TclError:
            return
        self._tick_job = self.root.after(50, self._tick)

    def flash(
        self,
        monitor: dict | None,
        text: str,
        kind: str = "info",
        seconds: float = 3.0,
    ):
        text = text if len(text) <= 70 else text[:67] + "..."
        self._build(monitor, text, text, kind)
        self._hide_job = self.root.after(int(seconds * 1000), self.hide)

    def hide(self):
        for job in (self._tick_job, self._hide_job):
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
        self._tick_job = None
        self._hide_job = None
        if self.win is not None:
            try:
                self.win.destroy()
            except Exception:
                pass
        self.win = None
        self.canvas = None


class PromptDialog:
    """Caixa de comando moderna com digitação instantânea e posicionamento dinâmico sem sobreposição."""

    def __init__(
        self,
        parent_root,
        title: str,
        subtitle: str,
        callback_submit,
        callback_close=None,
    ):
        self.callback_submit = callback_submit
        self.callback_close = callback_close

        self.win = tk.Toplevel(parent_root)
        self.win.title("PROMPT")
        self.win.attributes("-topmost", True)
        self.win.attributes("-type", "dialog")
        self.win.configure(bg="#0F172A")

        w, h = 680, 125
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        cx = (sw - w) // 2
        cy = max(180, (sh - h) // 3)
        self.win.geometry(f"{w}x{h}+{cx}+{cy}")

        self.canvas = tk.Canvas(
            self.win, bg="#0F172A", highlightthickness=1, highlightbackground="#38BDF8"
        )
        self.canvas.pack(fill="both", expand=True)

        self.canvas.create_rectangle(0, 0, w, 32, fill="#1E293B", outline="")
        self.canvas.create_text(
            16,
            16,
            text=f"◈ {title.upper()}",
            font=("DejaVu Sans", 9, "bold"),
            fill="#38BDF8",
            anchor="w",
        )
        self.canvas.create_text(
            w - 16,
            16,
            text="[ESC FECHA • ENTER ENVIA]",
            font=("DejaVu Sans", 7, "bold"),
            fill="#94A3B8",
            anchor="e",
        )

        self.canvas.create_text(
            16, 48, text=subtitle, font=("DejaVu Sans", 9), fill="#CBD5E1", anchor="w"
        )

        self.entry = tk.Entry(
            self.win,
            bg="#1E293B",
            fg="#F8FAFC",
            insertbackground="#38BDF8",
            font=("DejaVu Sans", 11),
            relief="flat",
            highlightthickness=1,
            highlightbackground="#0284C7",
        )
        self.entry.place(x=16, y=68, width=w - 32, height=36)

        self.win.update_idletasks()
        self.win.lift()
        self.entry.focus_force()
        request_ewmh_focus(self.win)

        self.entry.bind("<Return>", lambda e: self.submit())
        self.win.bind("<Escape>", lambda e: self.close())
        self.entry.bind("<Escape>", lambda e: self.close())

    def submit(self):
        text = self.entry.get().strip()
        if not text:
            self.close()
            return
        self.entry.config(state="disabled")
        self.canvas.create_text(
            16,
            114,
            text="◈ Processando com contexto visual e histórico...",
            font=("DejaVu Sans", 8, "italic"),
            fill="#34D399",
            anchor="w",
        )
        self.callback_submit(text, self)

    def show_response(self, query: str, answer: str):
        self.canvas.delete("all")
        if self.entry:
            self.entry.destroy()
            self.entry = None

        full_text = f'Q: "{query}"\n\nRESPOSTA: {answer}'
        approx_lines = max(4, len(full_text) // 55 + 5)
        new_h = approx_lines * 20 + 65
        w = 680

        sw = self.win.winfo_screenwidth()
        cx = (sw - w) // 2
        cy = 160
        self.win.geometry(f"{w}x{new_h}+{cx}+{cy}")

        self.canvas.create_rectangle(0, 0, w, 32, fill="#1E293B", outline="")
        self.canvas.create_text(
            16,
            16,
            text="◈ ANÁLISE DETALHADA",
            font=("DejaVu Sans", 9, "bold"),
            fill="#38BDF8",
            anchor="w",
        )
        self.canvas.create_text(
            w - 16,
            16,
            text="[ESC P/ FECHAR]",
            font=("DejaVu Sans", 7, "bold"),
            fill="#94A3B8",
            anchor="e",
        )

        self.canvas.create_text(
            18,
            50,
            text=full_text,
            font=("DejaVu Sans", 10),
            fill="#F8FAFC",
            width=w - 36,
            anchor="nw",
        )

        self.win.bind("<Escape>", lambda e: self.close())
        self.win.focus_force()
        request_ewmh_focus(self.win)

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass
        if self.callback_close:
            self.callback_close()


class JarvisHUDOverlay:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cards: list[CardWidget] = []
        self.highlights: list[ElementHighlight] = []
        self.indicator = ScanIndicator(root)
        self.active_prompt: PromptDialog | None = None
        self.current_image: Image.Image | None = None
        self.is_cards_active = False

    def scan_start(self, monitor_info: dict | None):
        self.indicator.show_scanning(monitor_info)

    def scan_flash(
        self,
        monitor_info: dict | None,
        text: str,
        kind: str = "info",
        seconds: float = 3.0,
    ):
        self.indicator.flash(monitor_info, text, kind, seconds)

    def clear(self):
        if self.active_prompt:
            try:
                self.active_prompt.close()
            except Exception:
                pass
            self.active_prompt = None

        for c in self.cards:
            try:
                c.win.destroy()
            except Exception:
                pass
        self.cards.clear()

        for h in self.highlights:
            h.destroy()
        self.highlights.clear()
        self.is_cards_active = False

    def toggle_central_bar(self, monitor_info: dict, screenshot_image: Image.Image):
        if self.active_prompt:
            self.active_prompt.close()
            self.active_prompt = None
            return

        self.current_image = screenshot_image

        def _on_submit(query, dialog):
            def _worker():
                ans = ai_client.ask_followup(screenshot_image, None, query)
                self.root.after(0, lambda: dialog.show_response(query, ans))

            threading.Thread(target=_worker, daemon=True).start()

        self.active_prompt = PromptDialog(
            self.root,
            title="COMANDO COGNITIVO GLOBAL",
            subtitle="Faça uma pergunta sobre a tela atual:",
            callback_submit=_on_submit,
            callback_close=lambda: setattr(self, "active_prompt", None),
        )

    def render_insights(
        self, monitor_info: dict, screenshot_image: Image.Image, insights: list[dict]
    ):
        self.clear()
        self.indicator.hide()
        self.current_image = screenshot_image
        self.is_cards_active = True

        y_offset = monitor_info.get("top", 0)
        placed_rects: list[tuple[int, int, int, int]] = []

        for idx, item in enumerate(insights, 1):
            target = box_to_pixels(item.get("box_2d"), monitor_info)

            card_w = 380
            text = item.get("insight", "")
            approx_lines = max(2, len(text) // 36 + 2)
            card_h = approx_lines * 20 + 60

            best_x, best_y = compute_card_position(
                target, card_w, card_h, monitor_info, placed_rects
            )
            placed_rects.append((best_x, best_y, card_w, card_h))

            # Moldura primeiro, para o card ficar por cima dela.
            if target is not None:
                self.highlights.append(
                    ElementHighlight(
                        self.root,
                        idx,
                        item.get("kind"),
                        target,
                        self.open_card_prompt,
                        top_limit=y_offset,
                    )
                )

            card = CardWidget(
                self.root,
                idx,
                item,
                (best_x, best_y, card_w, card_h),
                on_click_callback=self.open_card_prompt,
            )
            self.cards.append(card)

    def open_card_prompt(self, index: int):
        idx = index - 1
        if not (0 <= idx < len(self.cards)):
            return

        target_card = self.cards[idx]
        label = target_card.insight.get("label", "PONTO")

        if self.active_prompt:
            self.active_prompt.close()

        def _on_submit(query, dialog):
            def _worker():
                ans = ai_client.ask_followup(
                    self.current_image, target_card.insight, query
                )
                self.root.after(
                    0, lambda: self._apply_card_answer(target_card, query, ans, dialog)
                )

            threading.Thread(target=_worker, daemon=True).start()

        self.active_prompt = PromptDialog(
            self.root,
            title=f"PERGUNTA SOBRE [{label.upper()}]",
            subtitle=f"Foco selecionado: {label}. Digite sua dúvida:",
            callback_submit=_on_submit,
            callback_close=lambda: setattr(self, "active_prompt", None),
        )

    def _apply_card_answer(
        self, target_card: CardWidget, query: str, answer: str, dialog: PromptDialog
    ):
        dialog.close()
        self.active_prompt = None
        target_card.update_insight(f'Q: "{query}"\n\nRESPOSTA: {answer}')
