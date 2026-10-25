import fonts


def test_resolve_prefers_installed_fonts():
    resolved = fonts.resolve({"Share Tech Mono", "FiraCode Nerd Font Mono", "Ubuntu"})
    assert resolved["display"][0] == "Share Tech Mono"
    assert resolved["mono"][0] == "FiraCode Nerd Font Mono"
    assert resolved["body"][0] == "Ubuntu"
    assert resolved["mono"][1] >= 10


def test_resolve_falls_back_safely():
    resolved = fonts.resolve(set())
    assert resolved["display"][0] == "DejaVu Sans"
    assert resolved["mono"][0] == "DejaVu Sans Mono"
    assert resolved["body"][0] == "DejaVu Sans"
