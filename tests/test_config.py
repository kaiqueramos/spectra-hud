import keyring
import pytest

import config


@pytest.fixture
def cfg_env(monkeypatch, tmp_path):
    store: dict[str, str] = {}
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path / "cfg")
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "cfg" / "config.json")
    monkeypatch.setattr(config, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(config, "LOG_FILE", tmp_path / "state" / "spectra.log")
    monkeypatch.setattr(config, "_env_file", lambda: {})
    monkeypatch.setattr(config.keyring, "set_password", lambda _s, u, p: store.__setitem__(u, p))
    monkeypatch.setattr(config.keyring, "get_password", lambda _s, u: store.get(u))
    return store


def test_defaults_and_save_roundtrip(cfg_env):
    cfg = config.load()
    assert cfg["provider"] == "opencode-go"
    assert cfg["language"] == "pt"
    assert cfg["animations"] is True
    cfg["model"] = "deepseek-v4.1-flash"
    config.save(cfg)
    assert config.load()["model"] == "deepseek-v4.1-flash"


def test_migration_from_env(cfg_env, monkeypatch):
    monkeypatch.setattr(
        config,
        "_env_file",
        lambda: {
            "SPECTRA_API_KEY": "sk-test",
            "SPECTRA_BASE_URL": "https://api.commandcode.ai/provider/v1",
            "SPECTRA_MODEL": "deepseek/deepseek-v4.1-flash",
        },
    )
    cfg = config.load()
    assert cfg["provider"] == "commandcode"
    assert cfg["model"] == "deepseek/deepseek-v4.1-flash"
    assert config.get_api_key(cfg) == "sk-test"


def test_blocklist(cfg_env):
    cfg = config.load()
    assert config.is_blocked("1Password — Vault", cfg) is True
    assert config.is_blocked("Firefox — Notícias", cfg) is False
    cfg["blocklist"] = ["meu-banco"]
    assert config.is_blocked("Meu-Banco Online", cfg) is True


def test_cost_and_pricing(cfg_env):
    cfg = config.load()
    cfg["pricing"] = {"m": {"in": 1.0, "out": 2.0}}
    assert config.cost_for("m", {"prompt_tokens": 1_000_000, "completion_tokens": 500_000}, cfg) == 2.0
    assert config.cost_for("outro", {"prompt_tokens": 1}, cfg) is None


def test_consent_and_url(cfg_env):
    cfg = config.load()
    assert config.has_consent(cfg) is False
    cfg = config.mark_consent(cfg)
    assert config.has_consent(cfg) is True
    assert config.valid_url("https://api.commandcode.ai/provider/v1") is True
    assert config.valid_url("file:///etc/passwd") is False


def test_runtime_env_override(cfg_env, monkeypatch):
    cfg = config.load()
    monkeypatch.setenv("SPECTRA_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("SPECTRA_MODEL", "qwen2.5vl:7b")
    monkeypatch.setenv("SPECTRA_API_KEY", "ollama")
    rt = config.runtime(cfg)
    assert rt["base_url"] == "http://localhost:11434/v1"
    assert rt["model"] == "qwen2.5vl:7b"
    assert rt["api_key"] == "ollama"


def test_mask_key():
    assert config.mask_key("") == "(não configurada)"
    assert config.mask_key("sk-1234567890") == "sk-1…7890"
