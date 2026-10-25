"""Respostas fixas do modo demo (SPECTRA_DEMO=1).

Usado para gravar vídeos e screenshots sem chamar o modelo. As caixas
correspondem ao palco de `tools/demo_stage.py` em 1920x1080.
"""

CONTEXT = "Editor / Python"

INSIGHTS = [
    {
        "box_2d": [278, 52, 306, 510],
        "kind": "alerta",
        "label": "Erro de null",
        "insight": "Linha 42: user pode ser null. O build falha aqui.",
    },
    {
        "box_2d": [815, 859, 852, 911],
        "kind": "acao",
        "label": "Retry",
        "insight": "Escolha Retry. O rascunho é mantido.",
    },
    {
        "box_2d": [815, 52, 852, 354],
        "kind": "item",
        "label": "Duplicata",
        "insight": "#1043 é duplicata. Pule.",
    },
]

ANSWER = "O ledger pode fechar antes do user ser carregado. Guarde o acesso."
