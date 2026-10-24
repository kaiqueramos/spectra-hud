import ai_client


def test_normalize_box_valid_and_clamped():
    assert ai_client.normalize_box([100, 200, 300, 400]) == [100, 200, 300, 400]
    assert ai_client.normalize_box([-50, 10, 1500, 900]) == [0, 10, 1000, 900]
    assert ai_client.normalize_box(["10", "20.7", 30, 40]) == [10, 20, 30, 40]


def test_normalize_box_invalid():
    assert ai_client.normalize_box(None) is None
    assert ai_client.normalize_box([1, 2, 3]) is None
    assert ai_client.normalize_box("abc") is None
    assert ai_client.normalize_box([0, 0, 0, 0]) is None
    assert ai_client.normalize_box([300, 10, 100, 50]) is None  # ymax <= ymin
    assert ai_client.normalize_box([1, "x", 3, 4]) is None


def test_sanitize_insights_defaults_and_kind():
    raw = [
        {"label": "A", "insight": "Faça X.", "kind": "ALERTA", "box_2d": [1, 2, 30, 40]},
        {"insight": "Sem kind e sem box."},
        {"label": "C", "insight": "Kind inválido.", "kind": "banana", "box_2d": None},
    ]
    out = ai_client.sanitize_insights(raw)
    assert [i["kind"] for i in out] == ["alerta", "info", "info"]
    assert out[0]["box_2d"] == [1, 2, 30, 40]
    assert out[1]["box_2d"] is None
    assert out[1]["label"] == "PONTO DE ATENÇÃO"


def test_sanitize_insights_drops_garbage_and_limits():
    raw = ["texto", None, {"insight": ""}, {"insight": None}]
    raw += [{"insight": f"ponto {i}"} for i in range(6)]
    out = ai_client.sanitize_insights(raw)
    assert len(out) == ai_client.MAX_INSIGHTS
    assert out[0]["insight"] == "ponto 0"
    assert ai_client.sanitize_insights("não é lista") == []
