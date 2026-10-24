import json
from unittest.mock import patch, MagicMock
from PIL import Image
import ai_client


def test_clean_output_text_removes_think_tags():
    raw_1 = (
        "<think>O usuário está com dúvida no item X...</think>Esta é a resposta limpa."
    )
    assert ai_client.clean_output_text(raw_1) == "Esta é a resposta limpa."

    raw_2 = "Resposta direta sem tags."
    assert ai_client.clean_output_text(raw_2) == "Resposta direta sem tags."

    raw_3 = (
        '<think>Raciocínio longo...</think>```json\n{"foo": "bar"}\n```Resposta final.'
    )
    assert ai_client.clean_output_text(raw_3) == "Resposta final."


def test_extract_json_payload_formats():
    text_md = """
    Aqui está a análise:
    ```json
    {
      "context": "VS Code - Python",
      "insights": [
        {
          "box_2d": [100, 200, 300, 400],
          "label": "Erro de Sintaxe",
          "insight": "Falta fechar parênteses na linha 42."
        }
      ]
    }
    ```
    """
    res = ai_client.extract_json_payload(text_md)
    assert res.get("context") == "VS Code - Python"
    assert len(res.get("insights", [])) == 1
    assert res["insights"][0]["label"] == "Erro de Sintaxe"

    text_raw = '{"context": "Browser", "insights": [{"label": "Aba", "insight": "Artigo relevante."}]}'
    res2 = ai_client.extract_json_payload(text_raw)
    assert res2.get("context") == "Browser"
    assert len(res2["insights"]) == 1

    assert ai_client.extract_json_payload("Apenas texto puro sem json") == {}


def test_encode_image_to_base64():
    img = Image.new("RGB", (3000, 2000), color="blue")
    b64 = ai_client.encode_image_to_base64(img, max_dim=1000)
    assert isinstance(b64, str)
    assert len(b64) > 100


def test_analyze_screenshot_success_mock():
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": '```json\n{"context": "No Man\'s Sky", "insights": [{"box_2d": [10, 20, 30, 40], "label": "NPC", "insight": "Diálogo importante."}]}\n```',
                    "reasoning_content": "Raciocínio interno...",
                }
            }
        ]
    }

    img = Image.new("RGB", (200, 200), color="red")

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_cm):
        ctx, insights = ai_client.analyze_screenshot(img)
        assert ctx == "No Man's Sky"
        assert len(insights) == 1
        assert insights[0]["label"] == "NPC"


def test_ask_followup_clean_response_mock():
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": "Escolha a segunda opção para garantir a reputação sem risco de combate.",
                    "reasoning_content": "Notas de pensamento que não devem aparecer...",
                }
            }
        ]
    }

    img = Image.new("RGB", (100, 100), color="green")
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_cm):
        ans = ai_client.ask_followup(
            img, {"label": "Opção", "insight": "Dica"}, "Qual escolho?"
        )
        assert (
            ans
            == "Escolha a segunda opção para garantir a reputação sem risco de combate."
        )
        assert "Notas de pensamento" not in ans
