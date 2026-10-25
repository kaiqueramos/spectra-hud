import i18n


def test_language_switch_and_formatting():
    assert i18n.set_language("en") == "en"
    assert i18n.tr("btn.save") == "SAVE"
    assert i18n.tr("main.points", n=3, latency="1.2") == "3 POINTS · 1.2s"
    assert i18n.set_language("xx") == "pt"
    assert i18n.tr("btn.save") == "SALVAR"


def test_catalogs_have_the_same_keys():
    portuguese = set(i18n.TRANSLATIONS["pt"])
    assert set(i18n.TRANSLATIONS["en"]) == portuguese
    assert set(i18n.TRANSLATIONS["es"]) == portuguese
