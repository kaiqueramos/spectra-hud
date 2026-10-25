"""
Cliente de Visão para o HUD Cognitivo usando deepseek-v4-flash-vision-exp via OpenCode-Go.
Carrega dinamicamente o prompt universal de prompt_system.md e injeta a memória da sessão.
Saída direta, limpa e mastigada para leitura instantânea em tela.
"""

import os
import json
import uuid
import base64
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image
import io

import demo
from session_memory import session

ENV_PATH = Path(__file__).resolve().parent / ".env"
CONFIG = {}
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                CONFIG[k.strip()] = v.strip()


def _setting(name: str, legacy: str = "", default: str = "") -> str:
    """Config: env nova > .env novo > env antiga > .env antigo > default."""
    return (
        os.environ.get(name)
        or CONFIG.get(name)
        or (os.environ.get(legacy) if legacy else "")
        or (CONFIG.get(legacy) if legacy else "")
        or default
    )


API_KEY = _setting("SPECTRA_API_KEY", "OPENCODE_GO_API_KEY")
BASE_URL = _setting(
    "SPECTRA_BASE_URL", "OPENCODE_GO_BASE_URL", "https://opencode.ai/zen/go/v1"
).rstrip("/")
MODEL_NAME = _setting("SPECTRA_MODEL", "MODEL_NAME", "deepseek-v4.1-flash")

DEMO = os.environ.get("SPECTRA_DEMO", "").strip().lower() in ("1", "true", "yes")

PROMPT_FILE = Path(__file__).resolve().parent / "prompt_system.md"

ERROR_CONTEXT = "Erro"
LAST_ERROR = ""  # Último erro de análise/consulta, para o HUD exibir.
VALID_KINDS = ("alerta", "acao", "item", "info")
MAX_INSIGHTS = 3  # Alt+1..3 só alcançam 3 cards.
MAX_INSIGHT_CHARS = 420


def get_system_prompt() -> str:
    if PROMPT_FILE.exists():
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Você é o Spectra. Identifique o que está na tela e dê recomendações ultra diretas e simples em JSON."


def encode_image_to_base64(image: Image.Image, max_dim: int = 1600) -> str:
    img = image.copy()
    if max(img.size) > max_dim:
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def strip_markdown(text: str) -> str:
    """Remove marcação leve para o card ler como texto puro."""
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    return text


def clean_output_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```json.*?```", "", text, flags=re.DOTALL)
    return strip_markdown(text).strip()


def extract_json_payload(text: str) -> dict:
    if not text:
        return {}

    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    return {}


def normalize_box(box) -> list[int] | None:
    """Valida um box_2d [ymin, xmin, ymax, xmax] (0-1000). Devolve None se inválido."""
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        return None
    try:
        ymin, xmin, ymax, xmax = (max(0, min(1000, int(float(v)))) for v in box)
    except (TypeError, ValueError):
        return None
    if ymax <= ymin or xmax <= xmin:
        return None
    return [ymin, xmin, ymax, xmax]


def sanitize_insights(raw) -> list[dict]:
    """Normaliza os insights vindos do modelo: kind válido, box válido ou None, textos str."""
    if not isinstance(raw, list):
        return []

    clean: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = strip_markdown(str(item.get("insight") or "").strip())[:MAX_INSIGHT_CHARS]
        if not text:
            continue
        kind = str(item.get("kind") or "").strip().lower()
        clean.append(
            {
                "box_2d": normalize_box(item.get("box_2d")),
                "kind": kind if kind in VALID_KINDS else "info",
                "label": strip_markdown(str(item.get("label") or "PONTO DE ATENÇÃO").strip())[:60],
                "insight": text,
            }
        )
        if len(clean) >= MAX_INSIGHTS:
            break
    return clean


def analyze_screenshot(image: Image.Image) -> tuple[str, list[dict]]:
    global LAST_ERROR
    if DEMO:
        time.sleep(1.1)
        session.record_scan(demo.CONTEXT, demo.INSIGHTS)
        return demo.CONTEXT, demo.INSIGHTS

    session.touch()
    b64_img = encode_image_to_base64(image)
    system_prompt = get_system_prompt()
    memory_summary = session.get_context_summary()

    user_instructions = (
        "Analise a captura atual.\n"
        "1. Identifique o ambiente/jogo/aplicativo.\n"
        "2. Levante de 1 a 3 pontos com instruções ULTRA DIRETAS e mastigadas (1 a 2 frases curtas dizendo o que fazer ou o que significa).\n"
    )
    if memory_summary:
        user_instructions += f"\n{memory_summary}\n"
    user_instructions += (
        "\nFinalize estritamente com o bloco JSON: ```json "
        '{ "context": "...", "insights": [ { "box_2d": [ymin, xmin, ymax, xmax] ou null, '
        '"kind": "alerta|acao|item|info", "label": "...", "insight": "..." } ] } ```'
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "spectra-hud/0.1.0",
        "x-opencode-session": str(uuid.uuid4()),
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_instructions},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 3000,
    }

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            raw_bytes = resp.read()
            if hasattr(raw_bytes, "decode"):
                raw_text = raw_bytes.decode("utf-8")
            else:
                raw_text = str(raw_bytes)
            data = json.loads(raw_text)
            choice = data["choices"][0]["message"]
            content = choice.get("content") or ""
            reasoning = choice.get("reasoning_content") or ""

            if reasoning:
                first_lines = "\n".join(reasoning.strip().splitlines()[:2])
                print(f"[Análise Rápida] {first_lines}...")

            res = extract_json_payload(content)
            if not res or "insights" not in res:
                res = extract_json_payload(reasoning)

            detected_context = res.get("context", "Ambiente Identificado")
            insights = sanitize_insights(res.get("insights", []))

            session.record_scan(detected_context, insights)
            return detected_context, insights
    except Exception as e:
        LAST_ERROR = str(e)
        print(f"[Erro de Análise Visual] {e}")
        return ERROR_CONTEXT, []


def ask_followup(
    image: Image.Image, context_insight: dict | None, question: str
) -> str:
    session.touch()
    target_label = context_insight.get("label", "Geral") if context_insight else "Geral"

    if DEMO:
        time.sleep(0.8)
        session.record_interaction(question, demo.ANSWER, target_label)
        return demo.ANSWER

    b64_img = encode_image_to_base64(image)
    memory_summary = session.get_context_summary()

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "spectra-hud/0.1.0",
        "x-opencode-session": str(uuid.uuid4()),
    }

    target_label = context_insight.get("label", "Geral") if context_insight else "Geral"
    context_text = ""
    if context_insight:
        context_text = (
            f"Foco do usuário:\n"
            f"- Tópico: {context_insight.get('label')}\n"
            f"- Observação atual: {context_insight.get('insight')}\n\n"
        )

    user_prompt = f'{context_text}PERGUNTA:\n"{question}"\n\n'
    if memory_summary:
        user_prompt += f"{memory_summary}\n\n"
    user_prompt += (
        "DIRETRIZ DE RESPOSTA:\n"
        "- Responda de forma ULTRA DIRETA, SIMPLES e MASTIGADA em Português do Brasil.\n"
        "- Máximo de 2 a 3 frases curtas.\n"
        "- Vá direto ao ponto: diga o que escolher, o que fazer ou a resposta exata sem enrolação nem jargões.\n"
        "- Nunca inclua notas de raciocínio, entregue apenas o texto final."
    )

    system_instruction = (
        "Você é o Spectra. Sua missão é dar respostas mastigadas, práticas e instantâneas ao usuário. "
        "Sem enrolação, sem parágrafos longos, direto ao que ele precisa fazer ou entender."
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"},
                    },
                ],
            },
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            raw_bytes = resp.read()
            if hasattr(raw_bytes, "decode"):
                raw_text = raw_bytes.decode("utf-8")
            else:
                raw_text = str(raw_bytes)
            data = json.loads(raw_text)
            choice = data["choices"][0]["message"]

            content = choice.get("content") or ""
            content = clean_output_text(content)

            if not content:
                raw_reasoning = choice.get("reasoning_content") or ""
                paragraphs = [
                    p.strip() for p in raw_reasoning.split("\n\n") if p.strip()
                ]
                if paragraphs:
                    content = paragraphs[-1]
                else:
                    content = raw_reasoning[:300]

            session.record_interaction(question, content, target_label)
            return content
    except Exception as e:
        global LAST_ERROR
        LAST_ERROR = str(e)
        print(f"[Erro de Consulta] {e}")
        return "Erro na consulta. Tente de novo."
