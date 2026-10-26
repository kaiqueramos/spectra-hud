import subprocess
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

import wayland_capture


def test_command_capture_uses_grim(monkeypatch, tmp_path):
    monkeypatch.setattr(wayland_capture.shutil, "which", lambda name: "/usr/bin/grim" if name == "grim" else None)

    def fake_run(cmd, **kwargs):
        Image.new("RGB", (8, 6), (20, 30, 40)).save(Path(cmd[-1]))
        return MagicMock(returncode=0)

    monkeypatch.setattr(wayland_capture.subprocess, "run", fake_run)
    img = wayland_capture._command_capture()
    assert img.size == (8, 6)
    assert wayland_capture.LAST_BACKEND == "grim"


def test_capture_wayland_prefers_portal(monkeypatch):
    monkeypatch.setattr(wayland_capture.shutil, "which", lambda _name: None)
    monkeypatch.setattr(wayland_capture, "_portal_screenshot", lambda: Image.new("RGB", (12, 9)))
    monkeypatch.setattr(wayland_capture, "LAST_BACKEND", "portal")
    img, monitor = wayland_capture.capture_wayland()
    assert img.size == (12, 9)
    assert monitor["width"] == 12
    assert monitor["backend"] == "portal"


def test_capture_wayland_reports_failures(monkeypatch):
    monkeypatch.setattr(wayland_capture.shutil, "which", lambda _name: None)
    monkeypatch.setattr(
        wayland_capture, "_portal_screenshot",
        lambda: (_ for _ in ()).throw(RuntimeError("no portal")),
    )
    monkeypatch.setattr(
        wayland_capture, "_command_capture",
        lambda: (_ for _ in ()).throw(RuntimeError("no command")),
    )
    try:
        wayland_capture.capture_wayland()
    except RuntimeError as exc:
        assert "portal" in str(exc) and "comando" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")
