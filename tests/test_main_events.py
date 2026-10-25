import queue
import tkinter as tk
from unittest.mock import MagicMock

import pytest

import config
import main


@pytest.fixture(autouse=True)
def _ready(monkeypatch):
    cfg = dict(config.DEFAULTS)
    cfg["consent_at"] = "test"
    cfg["blocklist"] = []
    monkeypatch.setattr(main, "cfg", cfg)
    monkeypatch.setattr(main, "paused", False)
    monkeypatch.setattr(main, "get_active_window_title", lambda: "")
    monkeypatch.setattr(main.ai_client, "DEMO", False)
    monkeypatch.setattr(main.ai_client, "LAST_ERROR_KIND", "")
    while not main.action_queue.empty():
        main.action_queue.get_nowait()


def test_main_process_queue_clear_hud():
    root = MagicMock()
    mock_overlay = MagicMock()
    main.hud_overlay = mock_overlay

    main.action_queue.put(("CLEAR_HUD",))
    main.process_queue(root)

    mock_overlay.clear.assert_called_once()


def test_main_process_queue_render_insights():
    root = MagicMock()
    mock_overlay = MagicMock()
    main.hud_overlay = mock_overlay

    mon = {"left": 0, "top": 0, "width": 1920, "height": 1080}
    img = MagicMock()
    insights = [{"label": "Teste", "insight": "OK"}]

    main.action_queue.put(("RENDER_INSIGHTS", mon, img, insights, {"latency": 1.2}))
    main.process_queue(root)

    mock_overlay.render_insights.assert_called_once_with(mon, img, insights)


def test_main_trigger_toggle_closes_active():
    mock_overlay = MagicMock()
    mock_overlay.is_cards_active = True
    mock_overlay.active_prompt = None
    main.hud_overlay = mock_overlay

    # Limpa fila
    while not main.action_queue.empty():
        main.action_queue.get_nowait()

    main.trigger_toggle()
    msg = main.action_queue.get_nowait()
    assert msg == ("CLEAR_HUD",)


def _drain_queue():
    while not main.action_queue.empty():
        main.action_queue.get_nowait()


def test_main_process_queue_scan_indicator_events():
    root = MagicMock()
    mock_overlay = MagicMock()
    main.hud_overlay = mock_overlay
    mon = {"left": 0, "top": 0, "width": 1920, "height": 1080}
    _drain_queue()

    main.action_queue.put(("SCAN_START", mon))
    main.action_queue.put(("SCAN_EMPTY", mon))
    main.action_queue.put(("SCAN_FAIL", mon, "HTTP 401", "auth"))
    main.process_queue(root)

    mock_overlay.scan_start.assert_called_once_with(mon)
    calls = mock_overlay.scan_flash.call_args_list
    assert calls[0].args[1] == "NADA RELEVANTE NA TELA"
    assert calls[1].args[1] == "ERRO: HTTP 401"
    assert calls[1].args[2] == "alerta"


def test_run_scan_worker_reports_api_failure(monkeypatch):
    mon = {"left": 0, "top": 0, "width": 100, "height": 100}
    monkeypatch.setattr(main, "capture_active_monitor", lambda: (MagicMock(), mon))
    monkeypatch.setattr(main, "analyze_screenshot", lambda img: ("Erro", []))
    monkeypatch.setattr(main.ai_client, "LAST_ERROR", "timeout")
    _drain_queue()

    main.is_analyzing = True
    main.run_scan_worker()

    assert main.action_queue.get_nowait() == ("SCAN_START", mon)
    assert main.action_queue.get_nowait() == ("SCAN_FAIL", mon, "timeout", "")
    assert main.is_analyzing is False


def test_run_scan_worker_empty_result(monkeypatch):
    mon = {"left": 0, "top": 0, "width": 100, "height": 100}
    monkeypatch.setattr(main, "capture_active_monitor", lambda: (MagicMock(), mon))
    monkeypatch.setattr(main, "analyze_screenshot", lambda img: ("Desktop", []))
    _drain_queue()

    main.run_scan_worker()

    assert main.action_queue.get_nowait() == ("SCAN_START", mon)
    assert main.action_queue.get_nowait() == ("SCAN_EMPTY", mon)
