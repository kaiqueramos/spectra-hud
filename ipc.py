"""IPC local entre o app em execução e `spectra-hud --scan`.

Um socket Unix em XDG_RUNTIME_DIR permite que atalhos do desktop (GNOME/KDE)
acionem o app no Wayland, onde `pynput` não vê teclas globais.
"""

from __future__ import annotations

import os
import socket
import threading
from pathlib import Path
from typing import Callable

COMMANDS = {"scan", "show", "pause", "quit", "cancel", "ask"}


def socket_path() -> Path:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR") or "/tmp")
    return runtime / f"spectra-hud-{os.getuid()}.sock"


class Server:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.path = socket_path()
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> bool:
        try:
            if self.path.exists():
                self.path.unlink()
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(self.path))
            os.chmod(self.path, 0o600)
            sock.listen(4)
            sock.settimeout(0.5)
            self._sock = sock
            self._thread = threading.Thread(target=self._serve, name="spectra-ipc", daemon=True)
            self._thread.start()
            return True
        except Exception:
            self.stop()
            return False

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                conn.settimeout(1.0)
                raw = conn.recv(64).decode("utf-8", "replace").strip()
                if raw in COMMANDS:
                    self.callback(raw)
                    conn.sendall(b"ok")
                else:
                    conn.sendall(b"unknown")
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

    def stop(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        try:
            self.path.unlink(missing_ok=True)
        except Exception:
            pass


def send(command: str, timeout: float = 2.0) -> bool:
    """Envia um comando ao app em execução. False se não houver instância."""
    if command not in COMMANDS:
        return False
    path = socket_path()
    if not path.exists():
        return False
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect(str(path))
        sock.sendall(command.encode("utf-8"))
        reply = sock.recv(16)
        return reply == b"ok"
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass
