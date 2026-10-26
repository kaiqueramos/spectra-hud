#!/usr/bin/env python3
"""
Spectra HUD - Camada Cognitiva Visual para Desktop & Jogos.

X11: overlay ancorado e atalhos globais via pynput.
Wayland: captura via portal/comandos, atalhos via atalho do sistema chamando
`spectra-hud --scan`, resultados em painel normal e tray.
"""

import argparse
import logging
import os
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from logging.handlers import RotatingFileHandler
from pathlib import Path

import ai_client
import config
import i18n
import ipc
import theme
from ai_client import analyze_screenshot
from overlay import JarvisHUDOverlay
from results import WaylandAskDialog, WaylandResults
from screen_capture import capture_active_monitor, get_active_window_title, is_wayland
from settings import CommandCenter
from tray import SpectraTray

log = logging.getLogger("spectra")

action_queue: queue.Queue = queue.Queue()
is_analyzing = False
hud_overlay = None
wayland_ui: WaylandResults | None = None
wayland_ask: WaylandAskDialog | None = None
wayland_image = None
app_root = None
command_center = None
tray = None
ipc_server = None
startup_action: str | None = None
cfg = dict(config.DEFAULTS)
paused = False
last_scan_at = 0.0
lock_handle = None
wayland = False
SCAN_COOLDOWN = 1.2

IPC_ACTIONS = {
    "scan": ("SCAN",),
    "show": ("COMMAND_CENTER",),
    "ask": ("ASK_SCREEN",),
    "pause": ("TOGGLE_PAUSE",),
    "quit": ("QUIT",),
    "cancel": ("CANCEL_SCAN",),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="spectra-hud",
        description="Screen-aware AI HUD for Linux/X11 and Wayland.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--scan", action="store_true", help="scan the screen")
    group.add_argument("--ask", action="store_true", help="ask about the screen")
    group.add_argument("--show", action="store_true", help="open the command center")
    group.add_argument("--pause", action="store_true", help="toggle private mode")
    group.add_argument("--cancel", action="store_true", help="cancel the current scan")
    group.add_argument("--quit", action="store_true", help="quit the running app")
    return parser.parse_args(argv)


def _requested_command(args: argparse.Namespace) -> str | None:
    for name in ("scan", "ask", "show", "pause", "cancel", "quit"):
        if getattr(args, name):
            return name
    return None


def setup_logging() -> None:
    try:
        config.STATE_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        handler = RotatingFileHandler(config.LOG_FILE, maxBytes=1_000_000, backupCount=3)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        root.addHandler(handler)
    except Exception:
        pass


def dispatch(msg: tuple) -> None:
    action_queue.put(msg)


def notify(text: str, seconds: float = 3.0) -> None:
    """Notificação desktop para o modo Wayland, onde não há overlay."""
    if not wayland:
        return
    try:
        subprocess.Popen(
            [
                "notify-send",
                "-a",
                "Spectra HUD",
                "-t",
                str(max(1000, int(seconds * 1000))),
                text[:220],
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        print(f"[Spectra] {text}")


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
        print(f"[Spectra] {i18n.tr('main.instance')}")
        sys.exit(1)
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def toggle_pause() -> None:
    global paused
    paused = not paused
    cfg["paused"] = paused
    config.save(cfg)
    flash(
        i18n.tr("main.paused") if paused else i18n.tr("main.active"),
        "alerta" if paused else "info",
        2,
    )
    log.info("paused=%s", paused)


def on_saved(new_cfg: dict) -> None:
    global cfg, paused
    cfg = new_cfg
    paused = bool(cfg.get("paused", False))
    i18n.set_language(cfg.get("language", "pt"))
    theme.set_current(cfg.get("theme", "spectra"))
    ai_client.reload_config(cfg)
    if tray is not None:
        tray.refresh()
    log.info("config salva provider=%s model=%s", cfg.get("provider"), cfg.get("model"))


def open_center(first_run: bool = False) -> None:
    global command_center, wayland_ask
    try:
        if hud_overlay is not None:
            hud_overlay.clear()
        if wayland_ui is not None:
            wayland_ui.close()
        if wayland_ask is not None:
            wayland_ask.close()
            wayland_ask = None
    except Exception:
        pass
    try:
        if command_center is not None and command_center.win.winfo_exists():
            command_center.win.deiconify()
            command_center.win.lift()
            command_center.win.focus_force()
            command_center._force_x_focus()
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
    global tray, ipc_server, wayland_ask
    if ipc_server is not None:
        ipc_server.stop()
        ipc_server = None
    if wayland_ui is not None:
        wayland_ui.close()
    if wayland_ask is not None:
        wayland_ask.close()
        wayland_ask = None
    if tray is not None:
        tray.stop()
    try:
        if app_root is not None:
            app_root.quit()
    except Exception:
        pass


def _request_ask_screen() -> None:
    if not wayland:
        trigger_central_bar()
        return
    if paused:
        flash(i18n.tr("main.paused"), "alerta", 2)
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        return

    def worker():
        try:
            img, monitor = capture_active_monitor()
            action_queue.put(("OPEN_ASK", img, monitor))
        except Exception as exc:  # noqa: BLE001
            action_queue.put(("SCAN_FAIL", None, str(exc), "wayland"))

    threading.Thread(target=worker, daemon=True).start()


def _wayland_card_ask(index: int) -> None:
    if wayland_ui is None or wayland_image is None:
        return
    item = wayland_ui.item_at(index)
    if item is not None:
        open_wayland_ask(item, wayland_image)


def open_wayland_ask(item: dict | None, image) -> None:
    global wayland_ask
    if wayland_ask is not None:
        try:
            wayland_ask.close()
        except Exception:
            pass
    if item is not None:
        label = item.get("label") or i18n.tr("wayland.point")
        title = i18n.tr("overlay.card_prompt", label=str(label).upper())
        subtitle = i18n.tr("overlay.card_subtitle", label=label)
    else:
        title = i18n.tr("overlay.prompt_title")
        subtitle = i18n.tr("overlay.prompt_subtitle")

    def submit(question: str, dialog: WaylandAskDialog) -> None:
        def worker():
            answer = ai_client.ask_followup(image, item, question)
            action_queue.put(("WAYLAND_ANSWER", dialog, question, answer))

        threading.Thread(target=worker, daemon=True).start()

    wayland_ask = WaylandAskDialog(app_root, title, subtitle, submit)


def run_scan_worker():
    global is_analyzing
    monitor = None
    if paused:
        flash(i18n.tr("main.paused_hint"), "alerta", 2.5)
        is_analyzing = False
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        flash(i18n.tr("main.configure_first"), "alerta", 4)
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

        print(f"[Spectra] Contexto: '{context_name}' | {dt:.1f}s | {len(insights)} ponto(s)")
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
    global is_analyzing, hud_overlay, last_scan_at, wayland_ask
    if wayland:
        if wayland_ask is not None:
            try:
                wayland_ask.close()
            except Exception:
                pass
            wayland_ask = None
            return
        if wayland_ui is not None and wayland_ui.is_open():
            wayland_ui.close()
            return
    elif hud_overlay and (hud_overlay.is_cards_active or hud_overlay.active_prompt):
        action_queue.put(("CLEAR_HUD",))
        return

    if paused:
        flash(i18n.tr("main.paused"), "alerta", 2)
        return
    if not ai_client.DEMO and not config.has_consent(cfg):
        action_queue.put(("COMMAND_CENTER",))
        flash(i18n.tr("main.configure"), "alerta", 3)
        return

    if is_analyzing:
        ai_client.cancel_scan()
        flash(i18n.tr("main.canceling"), "alerta", 1.5)
        return

    now = time.time()
    if now - last_scan_at < SCAN_COOLDOWN:
        flash(i18n.tr("main.wait"), "info", 1.5)
        return

    last_scan_at = now
    is_analyzing = True
    threading.Thread(target=run_scan_worker, daemon=True).start()


def trigger_central_bar():
    global hud_overlay
    if wayland:
        _request_ask_screen()
        return
    if paused:
        flash(i18n.tr("main.paused"), "alerta", 2)
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
    if wayland and wayland_ui is not None:
        wayland_ui.ask(index - 1)
        return
    action_queue.put(("CARD_INPUT", index))


def process_queue(root):
    global hud_overlay, wayland_ui, wayland_ask, wayland_image
    if hud_overlay:
        hud_overlay.poll_results()

    while not action_queue.empty():
        msg = action_queue.get_nowait()
        action = msg[0]
        try:
            if action == "CLEAR_HUD":
                if wayland:
                    if wayland_ui is not None:
                        wayland_ui.close()
                    if wayland_ask is not None:
                        wayland_ask.close()
                        wayland_ask = None
                else:
                    hud_overlay.clear()

            elif action == "FLASH":
                _, text, kind, seconds = msg
                if wayland:
                    notify(text, seconds)
                else:
                    hud_overlay.scan_flash(None, text, kind, seconds)

            elif action == "SCAN_START":
                _, monitor = msg
                if wayland:
                    if wayland_ui is not None:
                        wayland_ui.close()
                    notify(i18n.tr("overlay.scanning"), 2.5)
                else:
                    hud_overlay.scan_start(monitor)

            elif action == "SCAN_EMPTY":
                _, monitor = msg
                if wayland:
                    notify(i18n.tr("main.nothing"), 2.5)
                else:
                    hud_overlay.scan_flash(monitor, i18n.tr("main.nothing"), "info", 2.5)

            elif action == "SCAN_FAIL":
                _, monitor, reason, kind = msg
                reason = str(reason)[:160]
                if wayland:
                    if monitor is None:
                        notify(i18n.tr("main.wayland_capture", reason=reason), 8)
                    else:
                        notify(i18n.tr("main.error", reason=reason), 8)
                else:
                    hud_overlay.scan_flash(monitor, i18n.tr("main.error", reason=reason), "alerta", 7.0)

            elif action == "SCAN_BLOCKED":
                _, title = msg
                short = (title or "janela ativa")[:48]
                if wayland:
                    notify(i18n.tr("main.blocked", title=short), 6)
                else:
                    hud_overlay.scan_flash(None, i18n.tr("main.blocked", title=short), "alerta", 7.0)

            elif action == "SCAN_CANCELED":
                if wayland:
                    notify(i18n.tr("main.canceled"), 2)
                else:
                    hud_overlay.clear()
                    hud_overlay.scan_flash(None, i18n.tr("main.canceled"), "info", 2.0)

            elif action == "RENDER_INSIGHTS":
                _, monitor, img, insights, meta = msg
                if wayland:
                    wayland_image = img
                    meta["backend"] = monitor.get("backend") if monitor else None
                    if wayland_ui is not None:
                        wayland_ui.show(insights, meta)
                else:
                    hud_overlay.render_insights(monitor, img, insights)
                    latency = float(meta.get("latency", 0.0) or 0.0)
                    text = i18n.tr("main.points", n=len(insights), latency=f"{latency:.1f}")
                    cost = meta.get("cost")
                    if cost is not None:
                        text += f" · US$ {cost:.4f}"
                    hud_overlay.scan_flash(monitor, text, "info", 2.8)

            elif action == "TOGGLE_CENTRAL":
                _, monitor, img = msg
                if wayland:
                    open_wayland_ask(None, img)
                elif hud_overlay is not None:
                    hud_overlay.toggle_central_bar(monitor, img)

            elif action == "OPEN_ASK":
                _, img, _monitor = msg
                open_wayland_ask(None, img)

            elif action == "ASK_SCREEN":
                _request_ask_screen()

            elif action == "WAYLAND_ANSWER":
                _, dialog, query, answer = msg
                try:
                    dialog.show_answer(query, answer)
                except Exception as exc:  # noqa: BLE001
                    log.exception("falha ao exibir resposta Wayland: %s", exc)

            elif action == "CARD_INPUT":
                _, index = msg
                if wayland and wayland_ui is not None:
                    wayland_ui.ask(index - 1)
                else:
                    hud_overlay.open_card_prompt(index)

            elif action == "CANCEL_SCAN":
                ai_client.cancel_scan()
                flash(i18n.tr("main.canceling"), "alerta", 1.5)

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


def _describe_wayland() -> None:
    print(f"[Spectra] {i18n.tr('main.wayland_mode')}")
    print("   scan  : spectra-hud --scan")
    print("   ask   : spectra-hud --ask")
    print("   center: spectra-hud --show")
    print("   tray  : Spectra HUD")


def _install_ipc() -> None:
    global ipc_server
    ipc_server = ipc.Server(lambda cmd: action_queue.put(IPC_ACTIONS[cmd]))
    if not ipc_server.start():
        log.warning("IPC local indisponível")


def main():
    global hud_overlay, lock_handle, cfg, paused, app_root, tray, wayland, wayland_ui
    global startup_action

    args = parse_args()
    requested = _requested_command(args)
    if requested:
        if ipc.send(requested):
            print(f"[Spectra] {i18n.tr('main.command_sent')}")
            return
        if requested not in ("scan", "ask", "show"):
            print(f"[Spectra] {i18n.tr('main.not_running')}")
            return
        startup_action = requested

    setup_logging()
    cfg = config.load()
    paused = bool(cfg.get("paused", False))
    i18n.set_language(cfg.get("language", "pt"))
    theme.set_current(cfg.get("theme", "spectra"))
    ai_client.reload_config(cfg)
    wayland = is_wayland()

    lock_handle = acquire_lock()

    print("=" * 65)
    print(f" {i18n.tr('main.start_title')}")
    if wayland:
        _describe_wayland()
    else:
        print(f"   {i18n.tr('label.scan')}  : {cfg.get('hotkey_scan')}")
        print(f"   {i18n.tr('label.bar')} : {cfg.get('hotkey_bar')}")
        print(f"   {i18n.tr('label.center')}: {cfg.get('hotkey_center')}")
        print(f"   {i18n.tr('label.pause')} : {cfg.get('hotkey_pause')}")
    print(f" {i18n.tr('main.start_hint')}")
    if ai_client.DEMO:
        print(f" {i18n.tr('main.demo')}")
    print("=" * 65)

    try:
        app_root = tk.Tk()
    except tk.TclError as e:
        print(f"[Spectra] Não foi possível abrir a interface: {e}")
        sys.exit(1)

    app_root.withdraw()
    if wayland:
        hud_overlay = None
        wayland_ui = WaylandResults(app_root, _wayland_card_ask)
    else:
        hud_overlay = JarvisHUDOverlay(app_root)

    tray = SpectraTray(dispatch, lambda: paused)
    tray.start()
    _install_ipc()

    if not wayland:
        from pynput import keyboard

        hotkeys = {
            cfg.get("hotkey_scan", "<ctrl>+<alt>+<space>"): trigger_toggle,
            cfg.get("hotkey_bar", "<ctrl>+<shift>+<space>"): trigger_central_bar,
            cfg.get("hotkey_center", "<ctrl>+<alt>+c"): lambda: action_queue.put(("COMMAND_CENTER",)),
            cfg.get("hotkey_pause", "<ctrl>+<alt>+p"): lambda: action_queue.put(("TOGGLE_PAUSE",)),
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

    first_run = not ai_client.DEMO and (not config.has_consent(cfg) or not config.get_api_key(cfg))
    if first_run:
        app_root.after(500, lambda: open_center(first_run=True))

    if startup_action == "scan":
        app_root.after(800, trigger_toggle)
    elif startup_action == "ask":
        app_root.after(800, _request_ask_screen)
    elif startup_action == "show":
        app_root.after(600, lambda: action_queue.put(("COMMAND_CENTER",)))

    app_root.after(50, lambda: process_queue(app_root))
    app_root.mainloop()


if __name__ == "__main__":
    main()
