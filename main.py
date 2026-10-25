#!/usr/bin/env python3
"""
Spectra HUD - Camada Cognitiva Visual para Desktop & Jogos.

Atalhos padrão (configuráveis no centro de comando):
 - Ctrl + Alt + Espaço        : Varre a tela / Fecha HUD
 - Ctrl + Shift + Espaço      : Barra Central de Comando
 - Ctrl + Alt + C             : Centro de Comando
 - Ctrl + Alt + P             : Pausar / retomar (private mode)
 - Alt + 1..3                 : Abre o card
 - Esc                        : Fecha prompt
"""

import logging
import os
import queue
import sys
import threading
import time
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pynput import keyboard

import ai_client
import config
from ai_client import analyze_screenshot
from overlay import JarvisHUDOverlay
from screen_capture import capture_active_monitor, get_active_window_title, is_wayland
from settings import CommandCenter
from tray import SpectraTray

log = logging.getLogger("spectra")

action_queue: queue.Queue = queue.Queue()
is_analyzing = False
hud_overlay = None
app_root = None
command_center = None
tray = None
cfg = dict(config.DEFAULTS)
paused = False
last_scan_at = 0.0
lock_handle = None
SCAN_COOLDOWN = 1.2


def setup_logging() -> None:
    try:
        config.STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        handler = RotatingFileHandler(
            config.LOG_FILE, maxBytes=1_000_000, backupCount=3
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
    except Exception:
        pass


def dispatch(msg: tuple) -> None:
    action_queue.put(msg)


def flash(text: str, kind: str = "info", seconds: float = 2.5) -> None:
    """Enfileira o flash: seguro para chamar de threads (atalhos/scan)."""
    action_queue.put(("FLASH", text, kind, seconds))


def acquire_lock():
    import fcntl

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


def toggle_pause() -> None:
    global paused
    paused = not paused
    cfg["paused"] = paused
    config.save(cfg)
    flash("PAUSADO" if paused else "ATIVO", "alerta" if paused else "info", 2)
    log.info("paused=%s", paused)


def on_saved(new_cfg: dict) -> None:
    global cfg, paused
    cfg = new_cfg
    paused = bool(cfg.get("paused", False))
    ai_client.reload_config(cfg)
    if tray is not None and tray.icon is not None:
        try:
            tray.icon.update_menu()
        except Exception:
            pass
    log.info("config salva provider=%s model=%s", cfg.get("provider"), cfg.get("model"))


def open_center(first_run: bool = False) -> None:
    global command_center
    try:
        if command_center is not None and command_center.win.winfo_exists():
            command_center.win.lift()
            command_center.win.focus_force()
            return
    except Exception:
        pass
    command_center = CommandCenter(
        app_root,
        on_saved=on_saved,
        on_quit=quit_app,
        first_run=first_run,
    )


def quit_app() -> None:
    global tray
    if tray is not None:
        tray.stop()
    try:
        if app_root is not None:
            app_root.quit()
    except Exception:
        pass


def run_scan_worker():
    global is_analyzing
    monitor = None
    if paused:
        flash("PAUSADO · retome no centro de comando", "alerta", 2.5)
        is_analyzing = False
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        flash("CONFIGURE E CONSINTA ANTES DE ESCANEAR", "alerta", 4)
        is_analyzing = False
        return

    title = get_active_window_title()
    if config.is_blocked(title, cfg):
        log.info("scan bloqueado pela blocklist: %s", title)
        action_queue.put(("SCAN_BLOCKED", title))
        is_analyzing = False
        return

    print("\n[Spectra] Capturando tela e processando análise ambiental...")
    try:
        ai_client.reset_cancel()
        img, monitor = capture_active_monitor()
        action_queue.put(("SCAN_START", monitor))
        print(f"[Spectra] Captura concluída ({monitor['width']}x{monitor['height']}).")

        t0 = time.time()
        context_name, insights = analyze_screenshot(img)
        dt = time.time() - t0
        meta = dict(ai_client.LAST_META or {})
        meta.setdefault("latency", dt)

        if ai_client.was_cancelled():
            action_queue.put(("SCAN_CANCELED",))
            return

        print(
            f"[Spectra] Contexto: '{context_name}' | {dt:.1f}s | {len(insights)} ponto(s)"
        )
        if context_name == ai_client.ERROR_CONTEXT and not insights:
            reason = ai_client.LAST_ERROR or "falha na consulta ao modelo"
            action_queue.put(("SCAN_FAIL", monitor, reason, ai_client.LAST_ERROR_KIND))
            return

        if not insights:
            action_queue.put(("SCAN_EMPTY", monitor))
            return

        action_queue.put(("RENDER_INSIGHTS", monitor, img, insights, meta))
        log.info(
            "scan ok model=%s latency=%.2fs insights=%d",
            meta.get("model"),
            dt,
            len(insights),
        )
    except Exception as e:
        kind, msg = ai_client.classify_error(e)
        log.exception("scan falhou: %s", e)
        action_queue.put(("SCAN_FAIL", monitor, msg, kind))
    finally:
        is_analyzing = False


def trigger_toggle():
    global is_analyzing, hud_overlay, last_scan_at
    if hud_overlay and (hud_overlay.is_cards_active or hud_overlay.active_prompt):
        action_queue.put(("CLEAR_HUD",))
        return

    if paused:
        flash("PAUSADO", "alerta", 2)
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        flash("CONFIGURE O SPECTRA", "alerta", 3)
        return

    if is_analyzing:
        ai_client.cancel_scan()
        flash("CANCELANDO…", "alerta", 1.5)
        return

    now = time.time()
    if now - last_scan_at < SCAN_COOLDOWN:
        flash("AGUARDE UM INSTANTE", "info", 1.5)
        return

    last_scan_at = now
    is_analyzing = True
    threading.Thread(target=run_scan_worker, daemon=True).start()


def trigger_central_bar():
    global hud_overlay
    if paused:
        flash("PAUSADO", "alerta", 2)
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        return
    if hud_overlay and hud_overlay.active_prompt:
        action_queue.put(("TOGGLE_CENTRAL", None, None))
        return
    title = get_active_window_title()
    if config.is_blocked(title, cfg):
        action_queue.put(("SCAN_BLOCKED", title))
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

            elif action == "FLASH":
                _, text, kind, seconds = msg
                hud_overlay.scan_flash(None, text, kind, seconds)

            elif action == "SCAN_START":
                _, monitor = msg
                hud_overlay.scan_start(monitor)

            elif action == "SCAN_EMPTY":
                _, monitor = msg
                hud_overlay.scan_flash(monitor, "NADA RELEVANTE NA TELA", "info", 2.5)

            elif action == "SCAN_FAIL":
                _, monitor, reason, kind = msg
                reason = str(reason)[:160]
                hud_overlay.scan_flash(monitor, f"ERRO: {reason}", "alerta", 7.0)

            elif action == "SCAN_BLOCKED":
                _, title = msg
                short = (title or "janela ativa")[:48]
                hud_overlay.scan_flash(
                    None, f"TELA SENSÍVEL: {short} · SCAN BLOQUEADO", "alerta", 7.0
                )

            elif action == "SCAN_CANCELED":
                hud_overlay.clear()
                hud_overlay.scan_flash(None, "CANCELADO", "info", 2.0)

            elif action == "RENDER_INSIGHTS":
                _, monitor, img, insights, meta = msg
                hud_overlay.render_insights(monitor, img, insights)
                latency = float(meta.get("latency", 0.0) or 0.0)
                text = f"{len(insights)} PONTOS · {latency:.1f}s"
                cost = meta.get("cost")
                if cost is not None:
                    text += f" · US$ {cost:.4f}"
                hud_overlay.scan_flash(monitor, text, "info", 2.8)

            elif action == "TOGGLE_CENTRAL":
                _, monitor, img = msg
                hud_overlay.toggle_central_bar(monitor, img)

            elif action == "CARD_INPUT":
                _, index = msg
                hud_overlay.open_card_prompt(index)

            elif action == "COMMAND_CENTER":
                open_center()

            elif action == "TOGGLE_PAUSE":
                toggle_pause()

            elif action == "SCAN":
                trigger_toggle()

            elif action == "QUIT":
                quit_app()

        except Exception as e:
            log.exception("event loop action=%s: %s", action, e)
            print(f"[Event Loop Erro] {action}: {e}")

    root.after(50, lambda: process_queue(root))


def main():
    global hud_overlay, lock_handle, cfg, paused, app_root, tray

    setup_logging()
    cfg = config.load()
    paused = bool(cfg.get("paused", False))
    ai_client.reload_config(cfg)

    if is_wayland():
        print(
            "[Spectra] Wayland não é suportado na v0.1.\n"
            "Capture e atalhos globais dependem de X11. Use uma sessão X11."
        )
        sys.exit(1)

    lock_handle = acquire_lock()

    print("=" * 65)
    print(" 👁️ SPECTRA HUD - CAMADA COGNITIVA VISUAL ATIVA")
    print(f"   scan  : {cfg.get('hotkey_scan')}")
    print(f"   barra : {cfg.get('hotkey_bar')}")
    print(f"   centro: {cfg.get('hotkey_center')}")
    print(f"   pausa : {cfg.get('hotkey_pause')}")
    print(" Pressione Ctrl + C no terminal para encerrar")
    if ai_client.DEMO:
        print(" MODO DEMO ATIVO (SPECTRA_DEMO=1): sem chamadas ao modelo.")
    print("=" * 65)

    try:
        app_root = tk.Tk()
    except tk.TclError as e:
        print(f"[Spectra] Não foi possível abrir a interface X11: {e}")
        sys.exit(1)

    app_root.withdraw()
    hud_overlay = JarvisHUDOverlay(app_root)

    tray = SpectraTray(dispatch, lambda: paused)
    tray.start()

    hotkeys = {
        cfg.get("hotkey_scan", "<ctrl>+<alt>+<space>"): trigger_toggle,
        cfg.get("hotkey_bar", "<ctrl>+<shift>+<space>"): trigger_central_bar,
        cfg.get("hotkey_center", "<ctrl>+<alt>+c"): lambda: action_queue.put(
            ("COMMAND_CENTER",)
        ),
        cfg.get("hotkey_pause", "<ctrl>+<alt>+p"): lambda: action_queue.put(
            ("TOGGLE_PAUSE",)
        ),
        "<alt>+1": lambda: trigger_card_shortcut(1),
        "<alt>+2": lambda: trigger_card_shortcut(2),
        "<alt>+3": lambda: trigger_card_shortcut(3),
    }
    hotkeys = {k: v for k, v in hotkeys.items() if k}
    try:
        listener = keyboard.GlobalHotKeys(hotkeys)
        listener.start()
    except Exception as e:
        log.exception("falha ao registrar atalhos: %s", e)
        print(f"[Spectra] Falha nos atalhos: {e}")

    first_run = not ai_client.DEMO and (
        not config.has_consent(cfg) or not config.get_api_key(cfg)
    )
    if first_run:
        app_root.after(500, lambda: open_center(first_run=True))

    app_root.after(50, lambda: process_queue(app_root))
    app_root.mainloop()


if __name__ == "__main__":
    main()
