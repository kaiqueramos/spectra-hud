import json
import urllib.error
from unittest.mock import MagicMock, patch

import ai_client


def test_classify_auth_expired():
    err = urllib.error.HTTPError("http://x", 401, "Unauthorized", {}, None)
    kind, msg = ai_client.classify_error(err)
    assert kind == "auth"
    assert "Chave" in msg


def test_classify_quota():
    err = urllib.error.HTTPError("http://x", 429, "Too Many", {}, None)
    kind, _ = ai_client.classify_error(err)
    assert kind == "quota"


def _response(payload):
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    cm.__exit__.return_value = False
    return cm


def test_test_vision_ok():
    payload = {"choices": [{"message": {"content": "red and blue"}}]}
    with patch("urllib.request.urlopen", return_value=_response(payload)):
        ok, msg, latency = ai_client.test_vision("https://x/v1", "m", "k")
        assert ok is True
        assert "visão OK" in msg
        assert latency >= 0


def test_test_vision_empty():
    payload = {"choices": [{"message": {"content": ""}}]}
    with patch("urllib.request.urlopen", return_value=_response(payload)):
        ok, msg, _ = ai_client.test_vision("https://x/v1", "m", "k")
        assert ok is False
        assert "vazia" in msg
