"""Configuração persistente, segredos e presets de provedor do Spectra."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import keyring
from keyring.errors import KeyringError

try:
    import yaml
except Exception:  # PyYAML é opcional em runtime; o JSON continua funcionando
    yaml = None

APP = "spectra-hud"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")) / APP
CONFIG_FILE = CONFIG_DIR / "config.json"
YAML_FILE = CONFIG_DIR / "config.yaml"
LAST_YAML_ERROR = ""
YAML_HEADER = """# Spectra HUD — configuration
# Edit with the app stopped, or use Reload YAML in the command center.
# The API key stays in the system keyring; SPECTRA_API_KEY overrides it.
# consent: true records LGPD consent; false revokes it.
"""
STATE_DIR = (
    Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")) / APP
)
LOG_FILE = STATE_DIR / "spectra.log"

PRESETS: dict[str, dict[str, Any]] = {
    "opencode-go": {
        "label": "OpenCode Go",
        "base_url": "https://opencode.ai/zen/go/v1",
        "model": "deepseek-v4.1-flash",
        "needs_key": True,
    },
    "opencode-zen": {
        "label": "OpenCode Zen (free)",
        "base_url": "https://opencode.ai/zen/v1",
        "model": "deepseek-v4.1-flash-free",
        "needs_key": True,
    },
    "commandcode": {
        "label": "CommandCode",
        "base_url": "https://api.commandcode.ai/provider/v1",
        "model": "deepseek/deepseek-v4.1-flash",
        "needs_key": True,
    },
    "ollama": {
        "label": "Ollama (local)",
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5vl:7b",
        "needs_key": False,
    },
    "custom": {
        "label": "Custom / OpenAI-compatible",
        "base_url": "",
        "model": "",
        "needs_key": True,
    },
}

DEFAULT_BLOCKLIST = [
    "1password",
    "bitwarden",
    "keepass",
    "lastpass",
    "dashlane",
    "password",
    "senha",
    "banco",
    "banking",
    "nubank",
    "itau",
    "itaú",
    "bradesco",
    "santander",
    "caixa economica",
    "caixa econômica",
    "picpay",
    "mercado pago",
]

DEFAULTS: dict[str, Any] = {
    "provider": "opencode-go",
    "base_url": "https://opencode.ai/zen/go/v1",
    "model": "deepseek-v4.1-flash",
    "hotkey_scan": "<ctrl>+<alt>+<space>",
    "hotkey_bar": "<ctrl>+<shift>+<space>",
    "hotkey_center": "<ctrl>+<alt>+c",
    "hotkey_pause": "<ctrl>+<alt>+p",
    "paused": False,
    "theme": "spectra",
    "language": "pt",
    "animations": True,
    "blocklist": DEFAULT_BLOCKLIST,
    "consent_at": None,
    "pricing": {},
    "api_key_fallback": "",
}


def _env_file() -> dict[str, str]:
    path = Path(__file__).resolve().parent / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    except Exception:
        pass
    return values


def infer_provider(base_url: str) -> str:
    base = (base_url or "").lower()
    if "commandcode.ai" in base:
        return "commandcode"
    if "opencode.ai/zen/go" in base:
        return "opencode-go"
    if "opencode.ai/zen" in base:
        return "opencode-zen"
    if "localhost" in base or "127.0.0.1" in base:
        return "ollama"
    return "custom"


def _to_yaml(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": cfg.get("provider", ""),
        "base_url": cfg.get("base_url", ""),
        "model": cfg.get("model", ""),
        "language": cfg.get("language", "pt"),
        "theme": cfg.get("theme", "spectra"),
        "animations": bool(cfg.get("animations", True)),
        "paused": bool(cfg.get("paused", False)),
        "consent": bool(cfg.get("consent_at")),
        "blocklist": list(cfg.get("blocklist") or []),
        "hotkeys": {
            "scan": cfg.get("hotkey_scan", ""),
            "bar": cfg.get("hotkey_bar", ""),
            "center": cfg.get("hotkey_center", ""),
            "pause": cfg.get("hotkey_pause", ""),
        },
        "pricing": dict(cfg.get("pricing") or {}),
    }


def _from_yaml(data: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in ("provider", "base_url", "model", "language", "theme"):
        if key in data and data[key] is not None:
            out[key] = str(data[key])
    for key in ("animations", "paused"):
        if key in data:
            out[key] = bool(data[key])
    if "blocklist" in data:
        value = data["blocklist"]
        if isinstance(value, str):
            out["blocklist"] = [line.strip() for line in value.splitlines() if line.strip()]
        elif isinstance(value, list):
            out["blocklist"] = [str(item) for item in value]
    if "pricing" in data and isinstance(data["pricing"], dict):
        out["pricing"] = data["pricing"]
    hotkeys = data.get("hotkeys")
    if isinstance(hotkeys, dict):
        for name in ("scan", "bar", "center", "pause"):
            if name in hotkeys and hotkeys[name] is not None:
                out[f"hotkey_{name}"] = str(hotkeys[name])
    for name in ("scan", "bar", "center", "pause"):
        flat = f"hotkey_{name}"
        if flat in data and data[flat] is not None:
            out[flat] = str(data[flat])
    if "consent" in data:
        if data["consent"]:
            out["consent_at"] = current.get("consent_at") or datetime.now(timezone.utc).isoformat()
        else:
            out["consent_at"] = None
    return out


def load() -> dict[str, Any]:
    global LAST_YAML_ERROR
    LAST_YAML_ERROR = ""
    cfg = json.loads(json.dumps(DEFAULTS))  # deep copy
    has_json = CONFIG_FILE.exists()
    if has_json:
        try:
            data = json.loads(CONFIG_FILE.read_text())
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass

    has_yaml = YAML_FILE.exists()
    if has_yaml:
        if yaml is None:
            LAST_YAML_ERROR = "PyYAML não instalado"
        else:
            try:
                data = yaml.safe_load(YAML_FILE.read_text()) or {}
                if not isinstance(data, dict):
                    raise ValueError("a raiz do YAML precisa ser um mapa")
                cfg.update(_from_yaml(data, cfg))
            except Exception as exc:
                LAST_YAML_ERROR = f"{type(exc).__name__}: {exc}"
                logging.getLogger("spectra.config").warning(
                    "YAML inválido em %s: %s", YAML_FILE, exc
                )

    if not has_json and not has_yaml:
        cfg = _migrate_env(cfg)

    if os.environ.get("SPECTRA_HOTKEY"):
        cfg["hotkey_scan"] = os.environ["SPECTRA_HOTKEY"]
    if os.environ.get("SPECTRA_HOTKEY_BAR"):
        cfg["hotkey_bar"] = os.environ["SPECTRA_HOTKEY_BAR"]
    return cfg


def _migrate_env(cfg: dict[str, Any]) -> dict[str, Any]:
    env = _env_file()
    base = (
        env.get("SPECTRA_BASE_URL")
        or env.get("OPENCODE_GO_BASE_URL")
        or cfg["base_url"]
    )
    model = env.get("SPECTRA_MODEL") or env.get("MODEL_NAME") or cfg["model"]
    key = env.get("SPECTRA_API_KEY") or env.get("OPENCODE_GO_API_KEY") or ""
    cfg["base_url"] = base
    cfg["model"] = model
    cfg["provider"] = infer_provider(base)
    if key:
        _store_key(key, cfg)
    save(cfg)
    return cfg


def save(cfg: dict[str, Any]) -> None:
    global LAST_YAML_ERROR
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    except Exception:
        return
    try:
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
        os.chmod(tmp, 0o600)
        tmp.replace(CONFIG_FILE)
    except Exception:
        pass

    if yaml is None:
        return
    try:
        tmp = YAML_FILE.with_name(YAML_FILE.name + ".tmp")
        text = YAML_HEADER + yaml.safe_dump(
            _to_yaml(cfg), sort_keys=False, allow_unicode=True, default_flow_style=False
        )
        tmp.write_text(text)
        os.chmod(tmp, 0o600)
        tmp.replace(YAML_FILE)
        LAST_YAML_ERROR = ""
    except Exception as exc:
        LAST_YAML_ERROR = f"{type(exc).__name__}: {exc}"
        logging.getLogger("spectra.config").warning("falha ao salvar YAML: %s", exc)


def _store_key(key: str, cfg: dict[str, Any]) -> None:
    try:
        keyring.set_password(APP, "api_key", key)
        cfg["api_key_fallback"] = ""
    except (KeyringError, Exception):
        cfg["api_key_fallback"] = key


def set_api_key(key: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load()
    _store_key(key, cfg)
    save(cfg)
    return cfg


def get_api_key(cfg: dict[str, Any] | None = None) -> str:
    env = os.environ.get("SPECTRA_API_KEY")
    if env:
        return env
    try:
        stored = keyring.get_password(APP, "api_key")
        if stored:
            return stored
    except (KeyringError, Exception):
        pass
    return (cfg or load()).get("api_key_fallback", "")


def runtime(cfg: dict[str, Any] | None = None) -> dict[str, str]:
    cfg = cfg or load()
    base = os.environ.get("SPECTRA_BASE_URL") or cfg.get("base_url", "")
    model = os.environ.get("SPECTRA_MODEL") or cfg.get("model", "")
    return {
        "base_url": base.rstrip("/"),
        "model": model,
        "api_key": get_api_key(cfg),
        "provider": infer_provider(base),
    }


def preset_for(provider: str) -> dict[str, Any]:
    return PRESETS.get(provider, PRESETS["custom"])


def is_blocked(title: str, cfg: dict[str, Any] | None = None) -> bool:
    if not title:
        return False
    lowered = title.lower()
    patterns = (cfg or load()).get("blocklist")
    if patterns is None:
        patterns = DEFAULT_BLOCKLIST
    return any(str(p).lower() in lowered for p in patterns if str(p).strip())


def has_consent(cfg: dict[str, Any] | None = None) -> bool:
    return bool((cfg or load()).get("consent_at"))


def mark_consent(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load()
    cfg["consent_at"] = datetime.now(timezone.utc).isoformat()
    save(cfg)
    return cfg


def cost_for(
    model: str, usage: dict[str, Any] | None, cfg: dict[str, Any] | None = None
) -> float | None:
    if not usage:
        return None
    price = ((cfg or load()).get("pricing") or {}).get(model)
    if not price:
        return None
    try:
        return (
            float(usage.get("prompt_tokens", 0)) * float(price.get("in", 0))
            + float(usage.get("completion_tokens", 0)) * float(price.get("out", 0))
        ) / 1_000_000
    except (TypeError, ValueError):
        return None


def mask_key(key: str) -> str:
    if not key:
        return "(não configurada)"
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}…{key[-4:]}"


def clear_session_cache() -> None:
    try:
        (STATE_DIR / "session.json").unlink(missing_ok=True)
    except Exception:
        pass


def valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", url or ""))
