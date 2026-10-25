"""
Memória de sessão com TTL deslizante (1 hora).

A leitura do resumo NÃO renova o TTL. Só interação real (scan ou pergunta)
conta como atividade, e o cache fica em XDG_STATE_HOME com permissão 600.
"""

import json
import os
import time
from pathlib import Path


def default_state_file() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
    return Path(base) / "spectra-hud" / "session.json"


class SessionMemory:
    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.last_activity_time = 0.0
        self.history: list[dict] = []
        self.current_context: str = "Ambiente Inicial"
        self.storage_file = default_state_file()
        self.load()

    def _expire_if_needed(self) -> bool:
        """Limpa o histórico se o TTL venceu. Não renova o contador."""
        now = time.time()
        if self.last_activity_time > 0 and (
            now - self.last_activity_time > self.ttl_seconds
        ):
            print(
                f"[Memória] ⏳ TTL de {self.ttl_seconds // 60} min expirado por inatividade. Resetando histórico."
            )
            self.history.clear()
            self.current_context = "Ambiente Inicial"
            self.last_activity_time = 0.0
            return True
        return False

    def touch(self):
        """Marca atividade agora e persiste."""
        self._expire_if_needed()
        self.last_activity_time = time.time()
        self.save()

    def _record(self, item: dict):
        self._expire_if_needed()
        self.last_activity_time = time.time()
        self.history.append(item)
        if len(self.history) > 10:
            self.history = self.history[-10:]
        self.save()

    def record_scan(self, detected_context: str, insights: list[dict]):
        self.current_context = detected_context
        self._record(
            {
                "timestamp": time.time(),
                "type": "scan",
                "context": detected_context,
                "insights": [
                    {"label": i.get("label"), "insight": i.get("insight")}
                    for i in insights
                ],
            }
        )

    def record_interaction(self, question: str, answer: str, target_label: str = ""):
        self._record(
            {
                "timestamp": time.time(),
                "type": "qa",
                "target": target_label,
                "question": question,
                "answer": answer,
            }
        )

    def get_context_summary(self) -> str:
        """Resumo para o modelo. Ler aqui não mantém a sessão viva."""
        self._expire_if_needed()
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
            self.storage_file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            data = {
                "last_activity_time": self.last_activity_time,
                "current_context": self.current_context,
                "history": self.history,
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.chmod(self.storage_file, 0o600)
        except Exception:
            pass

    def load(self):
        try:
            if self.storage_file.exists():
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.last_activity_time = data.get("last_activity_time", 0.0)
                self.current_context = data.get("current_context", "Ambiente Inicial")
                self.history = data.get("history", [])
                # Expirado? limpa. Válido? não renova o contador.
                self._expire_if_needed()
        except Exception:
            pass


# Singleton da sessão
session = SessionMemory(ttl_seconds=3600)
