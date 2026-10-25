import tempfile
import time
from pathlib import Path

from session_memory import SessionMemory


def test_session_memory_initial_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionMemory(ttl_seconds=3600)
        sm.storage_file = Path(tmpdir) / "test_session.json"
        sm.history.clear()
        sm.last_activity_time = 0.0

        assert sm.get_context_summary() == ""
        assert len(sm.history) == 0


def test_session_memory_record_scan():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionMemory(ttl_seconds=3600)
        sm.storage_file = Path(tmpdir) / "test_session.json"
        sm.history.clear()

        insights = [
            {"label": "Inimigo", "insight": "Alvo hostil com escudo ativo."},
            {"label": "Recurso", "insight": "Minério de Cobre raro."},
        ]
        sm.record_scan("No Man's Sky", insights)

        assert len(sm.history) == 1
        assert sm.current_context == "No Man's Sky"
        assert sm.history[0]["type"] == "scan"
        assert len(sm.history[0]["insights"]) == 2

        summary = sm.get_context_summary()
        assert "No Man's Sky" in summary
        assert "Inimigo" in summary


def test_session_memory_sliding_ttl_reset():
    with tempfile.TemporaryDirectory() as tmpdir:
        # TTL curto de 10 segundos para o teste
        sm = SessionMemory(ttl_seconds=10)
        sm.storage_file = Path(tmpdir) / "test_session.json"
        sm.history.clear()

        sm.record_interaction("Como vencer?", "Use granadas.", "Boss")
        assert len(sm.history) == 1

        # Simula avanço de tempo de 5 segundos (< 10s TTL): deve manter
        sm.last_activity_time = time.time() - 5
        sm.touch()
        assert len(sm.history) == 1

        # Simula inatividade de 15 segundos (> 10s TTL): deve expirar e resetar
        sm.last_activity_time = time.time() - 15
        summary = sm.get_context_summary()
        assert summary == ""
        assert len(sm.history) == 0


def test_session_memory_sliding_renewal_near_expiry():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionMemory(ttl_seconds=3600)
        sm.storage_file = Path(tmpdir) / "test_session.json"
        sm.history.clear()

        sm.record_interaction("Dúvida", "Resposta", "Item")
        # Simula que faltavam 10 segundos para 1 hora (passaram 3590 segundos)
        sm.last_activity_time = time.time() - 3590

        # Nova interação renova para 1 hora cheia
        sm.record_interaction("Nova dúvida", "Nova resposta", "Item 2")
        assert len(sm.history) == 2
        # Verifica se o timestamp foi atualizado para agora
        assert abs(time.time() - sm.last_activity_time) < 2


def test_summary_read_does_not_renew_ttl():
    with tempfile.TemporaryDirectory() as tmpdir:
        sm = SessionMemory(ttl_seconds=3600)
        sm.storage_file = Path(tmpdir) / "test_session.json"
        sm.history.clear()

        sm.record_interaction("Pergunta", "Resposta", "Alvo")
        stale = time.time() - 120
        sm.last_activity_time = stale
        sm.get_context_summary()

        assert sm.last_activity_time == stale


def test_session_memory_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = Path(tmpdir) / "test_session.json"
        sm1 = SessionMemory(ttl_seconds=3600)
        sm1.storage_file = storage
        sm1.history.clear()

        sm1.record_interaction("Pergunta", "Resposta", "Alvo")

        # Cria nova instância apontando para o mesmo arquivo
        sm2 = SessionMemory(ttl_seconds=3600)
        sm2.storage_file = storage
        sm2.load()

        assert len(sm2.history) == 1
        assert sm2.history[0]["question"] == "Pergunta"
