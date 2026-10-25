#!/usr/bin/env python3
"""Palco de demonstração do Spectra HUD (1920x1080, X11).

Não faz parte do produto: é uma tela falsa e limpa para gravar o vídeo do hero.
"""

import tkinter as tk

W, H = 1920, 1080
BG = "#0b0e0b"
PANEL = "#0e120e"
LINE = "#2a3227"
TEXT = "#c9c6ba"
DIM = "#7a8276"
BONE = "#ece8dc"
SIGNAL = "#ff5a1f"

root = tk.Tk()
root.overrideredirect(True)
root.geometry(f"{W}x{H}+0+0")
root.configure(bg=BG)
root.attributes("-topmost", True)

canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
canvas.pack(fill="both", expand=True)

# grade
for x in range(0, W, 40):
    canvas.create_line(x, 0, x, H, fill="#111611")
for y in range(0, H, 40):
    canvas.create_line(0, y, W, y, fill="#111611")

# barra superior
canvas.create_rectangle(0, 0, W, 52, fill="#0d110d", outline="")
canvas.create_line(0, 52, W, 52, fill=LINE)
canvas.create_oval(24, 22, 32, 30, fill=SIGNAL, outline="")
canvas.create_text(
    44,
    26,
    text="PAYMENT SERVICE / STAGING",
    fill=DIM,
    font=("DejaVu Sans Mono", 11),
    anchor="w",
)
canvas.create_text(
    W - 24,
    26,
    text="BUILD 4821  ·  PASSING  ·  DISPLAY 1",
    fill=DIM,
    font=("DejaVu Sans Mono", 11),
    anchor="e",
)


def window(x0, y0, x1, y1, title, right=""):
    canvas.create_rectangle(x0, y0, x1, y1, fill=PANEL, outline=LINE)
    canvas.create_rectangle(x0, y0, x1, y0 + 32, fill="#121712", outline=LINE)
    canvas.create_text(
        x0 + 14,
        y0 + 16,
        text=title,
        fill=DIM,
        font=("DejaVu Sans Mono", 10),
        anchor="w",
    )
    if right:
        canvas.create_text(
            x1 - 14,
            y0 + 16,
            text=right,
            fill=DIM,
            font=("DejaVu Sans Mono", 9),
            anchor="e",
        )


# editor
wx0, wy0, wx1, wy1 = 80, 120, 1000, 620
window(wx0, wy0, wx1, wy1, "payment_service.py", "UTF-8")

lines = [
    ("38", "def settle(payment):", TEXT),
    ("39", "    ledger = load(payment.id)", TEXT),
    ("40", "    if ledger.closed:", TEXT),
    ("41", '        return "skipped"', TEXT),
    ("42", "    return payment.user.id", "#ffb394"),
    ("43", "    commit(ledger)", TEXT),
]
y = 180
for number, code, color in lines:
    if number == "42":
        canvas.create_rectangle(
            wx0 + 1, y - 5, wx1 - 1, y + 25, fill="#1a0f09", outline=""
        )
    canvas.create_text(
        wx0 + 24,
        y,
        text=number,
        fill="#4e564b",
        font=("DejaVu Sans Mono", 12),
        anchor="w",
    )
    canvas.create_text(
        wx0 + 64, y, text=code, fill=color, font=("DejaVu Sans Mono", 13), anchor="w"
    )
    y += 30

# diálogo
dx0, dy0, dx1, dy1 = 1250, 700, 1800, 950
window(dx0, dy0, dx1, dy1, "Confirm retry")
canvas.create_text(
    dx0 + 22,
    dy0 + 74,
    text="The previous request timed out.",
    fill=TEXT,
    font=("DejaVu Sans", 15),
    anchor="w",
)
canvas.create_text(
    dx0 + 22,
    dy0 + 104,
    text="Retry the settlement for #1042?",
    fill=DIM,
    font=("DejaVu Sans", 13),
    anchor="w",
)
canvas.create_rectangle(1650, 880, 1750, 920, fill="#1a120c", outline=SIGNAL)
canvas.create_text(
    1700,
    900,
    text="Retry",
    fill=SIGNAL,
    font=("DejaVu Sans", 14, "bold"),
    anchor="center",
)
canvas.create_rectangle(1550, 880, 1630, 920, fill=PANEL, outline="#394134")
canvas.create_text(
    1590, 900, text="Cancel", fill=DIM, font=("DejaVu Sans", 13), anchor="center"
)

# fila
qx0, qy0, qx1, qy1 = 80, 760, 700, 980
window(qx0, qy0, qx1, qy1, "Queue")
rows = [
    ("#1041", "settle", TEXT),
    ("#1042", "settle", TEXT),
    ("#1043", "settle", SIGNAL),
    ("#1044", "retry", TEXT),
]
ry = 812
for ident, action, color in rows:
    canvas.create_text(
        qx0 + 24, ry, text=ident, fill=color, font=("DejaVu Sans Mono", 11), anchor="w"
    )
    canvas.create_text(
        qx1 - 24, ry, text=action, fill=color, font=("DejaVu Sans Mono", 11), anchor="e"
    )
    canvas.create_line(qx0 + 16, ry + 18, qx1 - 16, ry + 18, fill="#1b211a")
    ry += 38

canvas.create_text(
    80,
    1030,
    text="STAGING  ·  NO PRODUCTION DATA",
    fill="#4e564b",
    font=("DejaVu Sans Mono", 9),
    anchor="w",
)

root.mainloop()
