from unittest.mock import patch, MagicMock
from PIL import Image
import screen_capture


def test_get_mouse_position_success():
    result = MagicMock()
    result.stdout = "x:1234 y:567 screen:0 window:48234506\n"
    with patch("subprocess.run", return_value=result):
        assert screen_capture.get_mouse_position() == (1234, 567)


def test_get_mouse_position_falls_back_to_xlib():
    pointer = MagicMock()
    pointer.root_x = 10
    pointer.root_y = 20
    disp = MagicMock()
    disp.screen.return_value.root.query_pointer.return_value = pointer
    with (
        patch("subprocess.run", side_effect=Exception("xdotool not found")),
        patch("screen_capture.xdisplay.Display", return_value=disp),
    ):
        assert screen_capture.get_mouse_position() == (10, 20)
        disp.close.assert_called_once()


def test_get_mouse_position_none_when_both_fail():
    with (
        patch("subprocess.run", side_effect=Exception("xdotool not found")),
        patch("screen_capture.xdisplay.Display", side_effect=Exception("no display")),
    ):
        assert screen_capture.get_mouse_position() is None


def test_is_wayland(monkeypatch):
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    assert screen_capture.is_wayland() is True
    monkeypatch.setenv("XDG_SESSION_TYPE", "x11")
    assert screen_capture.is_wayland() is False
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert screen_capture.is_wayland() is True


def test_capture_active_monitor_mock():
    mock_monitor = {"left": 0, "top": 0, "width": 10, "height": 10}

    mock_shot = MagicMock()
    mock_shot.size = (10, 10)
    mock_shot.bgra = b"\x00" * (10 * 10 * 4)

    mock_sct = MagicMock()
    mock_sct.monitors = [{"left": 0, "top": 0, "width": 10, "height": 10}, mock_monitor]
    mock_sct.grab.return_value = mock_shot

    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_sct
    mock_context.__exit__.return_value = False

    with (
        patch("screen_capture.get_mouse_position", return_value=(5, 5)),
        patch("mss.mss", return_value=mock_context),
    ):
        img, mon = screen_capture.capture_active_monitor()
        assert isinstance(img, Image.Image)
        assert mon["width"] == 10
        assert mon["height"] == 10
