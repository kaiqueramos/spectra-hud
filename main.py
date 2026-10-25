#!/usr/bin/env python3
"""
Spectra HUD - Camada Cognitiva Visual para Desktop & Jogos.

Atalhos padrão (configuráveis por SPECTRA_HOTKEY / SPECTRA_HOTKEY_BAR):
 - Ctrl + Alt + Espaço        : Varre a tela / Fecha HUD (Toggle)
 - Ctrl + Shift + Espaço      : Barra Central de Comando Global (Toggle)
 - Clique no Card             : Abre a caixa de diálogo para ir a fundo
 - Arrastar o Card            : Reposiciona o card na tela
 - Esc                        : Cancela pergunta / Fecha prompt ativo
"""

import fcntl
import os
import sys
import time
import threading
import queue
import tkinter as tk
from pathlib import Path

from pynput import keyboard

from screen_capture import capture_active_monitor, is_wayland
import ai_client
from ai_client import analyze_screenshot
from overlay import JarvisHUDOverlay


action_queue = queue.Queue()
is_analyzing = False
hud_overlay = None
last_scan_at = 0.0
lock_handle = None

# Atalhos configuráveis (sintaxe do pynput). Ctrl+Space conflita com IDEs.
HOTKEY_SCAN = os.environ.get("SPECTRA_HOTKEY", "<ctrl>+<alt>+<space>")
HOTKEY_BAR = os.environ.get("SPECTRA_HOTKEY_BAR", "<ctrl>+<shift>+<space>")
SCAN_COOLDOWN = 1.2


def acquire_lock():
    """Garante uma única instância por usuário."""
    runtime = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    path = Path(runtime) / f"spectra-hud-{os.getuid()}.lock"
    handle = open(path, "w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[Spectra] Já existe uma instância rodando. Feche a outra primeiro.")
        sys.exit(1)
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def run_scan_worker():
    global is_analyzing
    monitor = None
    print("\n[Spectra] 🛰️ Capturando tela e processando análise ambiental...")
    try:
        img, monitor = capture_active_monitor()
        # O indicador só aparece DEPOIS da captura, então nunca entra no print.
        action_queue.put(("SCAN_START", monitor))
        print(
            f"[Spectra] Captura concluída ({monitor['width']}x{monitor['height']}). Consultando modelo visual..."
        )

        t0 = time.time()
        context_name, insights = analyze_screenshot(img)
        dt = time.time() - t0
        print(
            f"[Spectra] Contexto: '{context_name}' | Resposta em {dt:.2f}s com {len(insights)} ponto(s)."
        )

        if context_name == ai_client.ERROR_CONTEXT and not insights:
            reason = ai_client.LAST_ERROR or "falha na consulta ao modelo"
            action_queue.put(("SCAN_FAIL", monitor, reason))
            return

        if not insights:
            print("[Spectra] Nenhum elemento prioritário detectado.")
            action_queue.put(("SCAN_EMPTY", monitor))
            return

        for idx, item in enumerate(insights, 1):
            print(f"  [{idx}] {item.get('label')}: {item.get('insight')}")

        action_queue.put(("RENDER_INSIGHTS", monitor, img, insights))
    except Exception as e:
        print(f"[Spectra Erro] {e}")
        action_queue.put(("SCAN_FAIL", monitor, str(e)))
    finally:
        is_analyzing = False


def trigger_toggle():
    global is_analyzing, hud_overlay, last_scan_at
    if hud_overlay and (hud_overlay.is_cards_active or hud_overlay.active_prompt):
        print("[Spectra] ✕ Fechando camada HUD.")
        action_queue.put(("CLEAR_HUD",))
        return

    if is_analyzing:
        print("[Spectra] Análise em andamento. Aguarde...")
        return

    now = time.time()
    if now - last_scan_at < SCAN_COOLDOWN:
        print("[Spectra] Aguarde um instante antes de escanear de novo.")
        return

    last_scan_at = now
    is_analyzing = True
    threading.Thread(target=run_scan_worker, daemon=True).start()


def trigger_central_bar():
    global hud_overlay
    if hud_overlay and hud_overlay.active_prompt:
        action_queue.put(("TOGGLE_CENTRAL", None, None))
        return

    img, monitor = capture_active_monitor()
    action_queue.put(("TOGGLE_CENTRAL", monitor, img))


def trigger_card_shortcut(index: int):
    action_queue.put(("CARD_INPUT", index))


def process_queue(root):
    global hud_overlay
    if hud_overlay:
        hud_overlay.poll_results()

    while not action_queue.empty():
        msg = action_queue.get_nowait()
        action = msg[0]
        try:
            if action == "CLEAR_HUD":
                hud_overlay.clear()

            elif action == "SCAN_START":
                _, monitor = msg
                hud_overlay.scan_start(monitor)

            elif action == "SCAN_EMPTY":
                _, monitor = msg
                hud_overlay.scan_flash(monitor, "NADA RELEVANTE NA TELA", "info", 2.5)

            elif action == "SCAN_FAIL":
                _, monitor, reason = msg
                reason = str(reason)[:140]
                hud_overlay.scan_flash(monitor, f"ERRO: {reason}", "alerta", 6.0)

            elif action == "RENDER_INSIGHTS":
                _, monitor, img, insights = msg
                hud_overlay.render_insights(monitor, img, insights)

            elif action == "TOGGLE_CENTRAL":
                _, monitor, img = msg
                hud_overlay.toggle_central_bar(monitor, img)

            elif action == "CARD_INPUT":
                _, index = msg
                hud_overlay.open_card_prompt(index)
        except Exception as e:
            print(f"[Event Loop Erro] {action}: {e}")

    root.after(50, lambda: process_queue(root))


def main():
    global hud_overlay, lock_handle
    if is_wayland():
        print(
            "[Spectra] Wayland não é suportado na v0.1.\n"
            "Capture e atalhos globais dependem de X11. Use uma sessão X11 "
            "(ou acompanhe o roadmap para suporte a Wayland)."
        )
        sys.exit(1)

    if not ai_client.API_KEY and not ai_client.DEMO:
        print(
            "[Spectra] Chave de API não configurada.\n"
            "Copie .env.example para .env e preencha SPECTRA_API_KEY "
            "(ou defina a variável de ambiente). Para gravar demos sem chave, "
            "use SPECTRA_DEMO=1."
        )
        sys.exit(1)

    lock_handle = acquire_lock()

    print("=" * 65)
    print(" 👁️ SPECTRA HUD - CAMADA COGNITIVA VISUAL ATIVA")
    print(" Atalhos:")
    print(f"   • [{HOTKEY_SCAN}] : Varre a tela / Fecha HUD (Toggle)")
    print(f"   • [{HOTKEY_BAR}] : Comando Global Central (Toggle)")
    print("   • [Clique no Card]       : Aprofunda e pergunta sobre o item")
    print("   • [Arrastar Card]        : Move o card livremente pela tela")
    print("   • [Esc]                  : Fecha prompt ou cancela")
    print(" Pressione Ctrl + C no terminal para encerrar")
    if ai_client.DEMO:
        print(" MODO DEMO ATIVO (SPECTRA_DEMO=1): sem chamadas ao modelo.")
    print("=" * 65)

    try:
        root = tk.Tk()
    except tk.TclError as e:
        print(f"[Spectra] Não foi possível abrir a interface X11: {e}")
        sys.exit(1)

    root.withdraw()
    hud_overlay = JarvisHUDOverlay(root)

    hotkey = keyboard.GlobalHotKeys(
        {
            HOTKEY_SCAN: trigger_toggle,
            HOTKEY_BAR: trigger_central_bar,
            "<alt>+1": lambda: trigger_card_shortcut(1),
            "<alt>+2": lambda: trigger_card_shortcut(2),
            "<alt>+3": lambda: trigger_card_shortcut(3),
        }
    )
    hotkey.start()

    root.after(50, lambda: process_queue(root))
    root.mainloop()


if __name__ == "__main__":
    main()
