"""
Gerenciador de Sessão com Memória Contínua e TTL Deslizante (1 Hora).
Se houver interação dentro de 1h, o cronômetro reinicia para 1h cheia.
Se passar 1h inativo, o contexto histórico é limpo automaticamente.
"""

import time
import json
from pathlib import Path


class SessionMemory:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.last_activity_time = 0.0
        self.history: list[dict] = []
        self.current_context: str = "Ambiente Inicial"
        self.storage_file = Path(__file__).resolve().parent / ".session_cache.json"
        self.load()

    def _check_ttl(self):
        """Se passou mais de 1h desde a última atividade, reinicia a memória."""
        now = time.time()
        if self.last_activity_time > 0 and (
            now - self.last_activity_time > self.ttl_seconds
        ):
            print(
                f"[Memória] ⏳ TTL de {self.ttl_seconds // 60} min expirado por inatividade. Resetando histórico."
            )
            self.history.clear()
            self.current_context = "Ambiente Inicial"
        # Renova o tempo de atividade para a nova interação
        self.last_activity_time = now

    def touch(self):
        """Reinicia o cronômetro para 1 hora a partir de agora."""
        self._check_ttl()
        self.save()

    def record_scan(self, detected_context: str, insights: list[dict]):
        self._check_ttl()
        self.current_context = detected_context

        summary = {
            "timestamp": time.time(),
            "type": "scan",
            "context": detected_context,
            "insights": [
                {"label": i.get("label"), "insight": i.get("insight")} for i in insights
            ],
        }
        self.history.append(summary)

        # Mantém histórico enxuto (últimos 10 eventos) para economizar payload e focar no relevante
        if len(self.history) > 10:
            self.history = self.history[-10:]
        self.save()

    def record_interaction(self, question: str, answer: str, target_label: str = ""):
        self._check_ttl()
        interaction = {
            "timestamp": time.time(),
            "type": "qa",
            "target": target_label,
            "question": question,
            "answer": answer,
        }
        self.history.append(interaction)
        if len(self.history) > 10:
            self.history = self.history[-10:]
        self.save()

    def get_context_summary(self) -> str:
        """Monta um resumo contextual para a IA saber o que vem acontecendo na sessão."""
        self._check_ttl()
        if not self.history:
            return ""

        lines = ["HISTÓRICO RECENTE DA SESSÃO DO USUÁRIO (ÚLTIMA HORA):"]
        for item in self.history[-4:]:
            if item["type"] == "scan":
                lines.append(f"• Cenário anterior: {item['context']}")
                for ins in item["insights"][:2]:
                    lines.append(
                        f"   - Observado: {ins['label']} -> {ins['insight'][:90]}..."
                    )
            elif item["type"] == "qa":
                lines.append(
                    f"• Dúvida anterior sobre [{item['target']}]: '{item['question']}'"
                )
                lines.append(f"   Resposta dada: {item['answer'][:110]}...")

        return "\n".join(lines)

    def save(self):
        try:
            data = {
                "last_activity_time": self.last_activity_time,
                "current_context": self.current_context,
                "history": self.history,
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.last_activity_time = data.get("last_activity_time", 0.0)
                    self.current_context = data.get(
                        "current_context", "Ambiente Inicial"
                    )
                    self.history = data.get("history", [])
                    # Verifica se o cache carregado já passou de 1h
                    self._check_ttl()
        except Exception:
            pass


# Singleton da sessão
session = SessionMemory(ttl_seconds=3600)
