import theme

REQUIRED = [
    "bg", "panel", "panel2", "header", "line", "line2", "text", "muted",
    "dim", "accent", "accent_ink", "grid", "input", "card", "card_line",
]


def test_catalog_has_five_dark_and_five_light():
    assert len(theme.DARK) == 5
    assert len(theme.LIGHT) == 5
    for key in theme.DARK + theme.LIGHT:
        palette = theme.get(key)
        assert palette["mode"] in ("dark", "light")
        for token in REQUIRED:
            assert palette[token].startswith("#")
            assert len(palette[token]) == 7


def test_set_current_and_fallback():
    old = theme.current()
    try:
        assert theme.set_current("paper")["mode"] == "light"
        assert theme.current()["name"] == "Paper"
        assert theme.get("does-not-exist")["name"] == "Spectra"
        assert theme.get(None)["name"] == "Spectra"
    finally:
        theme.set_current(old["name"].lower() if old["name"] != "Spectra" else "spectra")
