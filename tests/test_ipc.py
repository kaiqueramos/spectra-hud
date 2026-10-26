import ipc


def test_server_and_send(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    received = []
    server = ipc.Server(received.append)
    assert server.start() is True
    try:
        assert ipc.send("scan") is True
        assert received == ["scan"]
        assert ipc.send("bogus") is False
    finally:
        server.stop()
    assert not ipc.socket_path().exists()


def test_send_without_server(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    assert ipc.send("scan") is False
