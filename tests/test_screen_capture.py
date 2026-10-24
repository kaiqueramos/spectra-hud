from unittest.mock import patch, MagicMock
from PIL import Image
import screen_capture


def test_get_mouse_position_success():
    with patch(
        "subprocess.check_output",
        return_value="x:1234 y:567 screen:0 window:48234506\n",
    ):
        x, y = screen_capture.get_mouse_position()
        assert x == 1234
        assert y == 567


def test_get_mouse_position_fallback_on_error():
    with patch("subprocess.check_output", side_effect=Exception("xdotool not found")):
        x, y = screen_capture.get_mouse_position()
        assert x == 0
        assert y == 0


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
