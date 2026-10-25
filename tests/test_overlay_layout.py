from overlay import (
    blend_hex,
    box_to_pixels,
    compute_card_position,
    get_kind_style,
    rects_overlap,
)

MON = {"left": 0, "top": 0, "width": 1920, "height": 1080}


def test_rects_overlap_colliding():
    # Dois retângulos com sobreposição clara
    r1 = (100, 100, 200, 100)
    r2 = (150, 120, 200, 100)
    assert rects_overlap(r1, r2) is True


def test_rects_overlap_separated_horizontal():
    # Retângulos separados horizontalmente
    r1 = (100, 100, 100, 100)
    r2 = (250, 100, 100, 100)
    assert rects_overlap(r1, r2, margin=15) is False


def test_rects_overlap_separated_vertical():
    # Retângulos separados verticalmente
    r1 = (100, 100, 100, 100)
    r2 = (100, 250, 100, 100)
    assert rects_overlap(r1, r2, margin=15) is False


def test_rects_overlap_margin_sensitivity():
    # Retângulos quase encostados (distância 10px, margem requer 15px)
    r1 = (100, 100, 100, 100)
    r2 = (210, 100, 100, 100)
    assert rects_overlap(r1, r2, margin=15) is True
    # Com margem 5px, eles não colidem
    assert rects_overlap(r1, r2, margin=5) is False


def test_box_to_pixels_converts_and_offsets_monitor():
    mon = {"left": 1920, "top": 100, "width": 1000, "height": 500}
    # [ymin, xmin, ymax, xmax] = 20%..60% vertical, 10%..50% horizontal
    assert box_to_pixels([200, 100, 600, 500], mon) == (2020, 200, 400, 200)


def test_box_to_pixels_null_or_invalid_returns_none():
    assert box_to_pixels(None, MON) is None
    assert box_to_pixels([0, 0, 0, 0], MON) is None
    assert box_to_pixels([1, 2, 3], MON) is None


def test_box_to_pixels_enforces_min_size_and_stays_in_monitor():
    x, y, w, h = box_to_pixels([500, 500, 501, 501], MON, min_size=24)
    assert w >= 23 and h >= 23
    # Elemento colado no canto não pode sair do monitor
    x, y, w, h = box_to_pixels([0, 0, 2, 2], MON, min_size=24)
    assert x >= 0 and y >= 0 and x + w <= 1920 and y + h <= 1080


def test_compute_card_position_prefers_right_of_target():
    target = (200, 300, 100, 50)
    x, y = compute_card_position(target, 380, 100, MON, [])
    assert x == 320  # x2 + 20
    assert y == 300


def test_compute_card_position_never_covers_target_when_avoidable():
    # Elemento encostado na borda direita: card vai para a esquerda
    target = (1700, 300, 200, 60)
    x, y = compute_card_position(target, 380, 100, MON, [])
    assert not rects_overlap((x, y, 380, 100), target, margin=0)


def test_compute_card_position_avoids_placed_cards():
    target = (200, 300, 100, 50)
    first = compute_card_position(target, 380, 100, MON, [])
    placed = [(first[0], first[1], 380, 100)]
    second = compute_card_position(target, 380, 100, MON, placed)
    assert not rects_overlap((second[0], second[1], 380, 100), placed[0])


def test_compute_card_position_uses_side_column_when_target_blocks_all():
    # Alvo gigante cobre direita, esquerda, acima e abaixo.
    target = (100, 100, 1700, 900)
    x, y = compute_card_position(target, 380, 100, MON, [])
    assert x in (MON["width"] - 380 - 30, 30)
    assert not rects_overlap((x, y, 380, 100), (10, 10, 380, 100))


def test_compute_card_position_without_target_stacks_on_right_column():
    x1, y1 = compute_card_position(None, 380, 100, MON, [])
    assert x1 == 1920 - 380 - 30
    placed = [(x1, y1, 380, 100)]
    x2, y2 = compute_card_position(None, 380, 100, MON, placed)
    assert x2 == x1 and y2 > y1
    assert not rects_overlap((x2, y2, 380, 100), placed[0])


def test_kind_styles_and_fallback():
    assert get_kind_style("alerta")["tag"] == "ALERTA"
    assert get_kind_style("desconhecido")["tag"] == "INFO"
    assert get_kind_style(None)["tag"] == "INFO"


def test_blend_hex():
    assert blend_hex("#000000", "#FFFFFF", 0) == "#000000"
    assert blend_hex("#000000", "#FFFFFF", 1) == "#FFFFFF"
    assert blend_hex("#000000", "#FFFFFF", 0.5) == "#808080"
