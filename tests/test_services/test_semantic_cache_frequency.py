"""Testes do cache semântico do ChatbotService (rag_ppc.py) com promoção por
FREQUÊNCIA de repetição — não há rating/avaliação do usuário no produto.

A instância é criada com `object.__new__` para pular `_setup_service()` (que
exige Ollama, modelos LLM etc.) e testar isoladamente a lógica de cache:
build/upsert de entrada, busca por similaridade, elegibilidade de serving e as
salvaguardas (invalidação por `documents_hash`, expiração por TTL).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
import pytest

from backend.infrastructure.rag.rag_ppc import (
    SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD,
    ChatbotService,
)


class _DeterministicEmbedder:
    """Fake com a mesma interface do OllamaEmbedder (método get_embedding)."""

    # Vetores próximos (cos_sim >= 0.90) simulam 3 redações da MESMA pergunta,
    # como no exemplo real: "Quantas horas sao ACC?" / "Qual a carga horária de
    # ACC?" / "Carga horária de ACC?". "mensalidade" fica ortogonal (assunto
    # diferente, não deve contar como repetição nem ser servido do cache).
    _VECTORS = {
        "qual a carga horaria de acc": [1.0, 0.0, 0.0],
        "quantas horas sao acc": [0.99, 0.01, 0.0],
        "quantas horas de acc sao necessarias": [0.99, 0.01, 0.0],
        "carga horaria de acc": [0.98, 0.0, 0.02],
        "qual o valor da mensalidade": [0.0, 1.0, 0.0],
    }
    id = "fake-embedder"

    @staticmethod
    def _normalize_key(text: str) -> str:
        import unicodedata

        no_accents = "".join(
            c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
        )
        cleaned = "".join(c for c in no_accents if c.isalnum() or c.isspace())
        return " ".join(cleaned.lower().split())

    def get_embedding(self, text: str) -> List[float]:
        key = self._normalize_key(text)
        # Match exato primeiro; senão o known_key mais longo contido na pergunta
        # (evita que uma chave curta como "carga horaria de acc" capture por
        # engano uma pergunta mais longa que contenha esse trecho).
        if key in self._VECTORS:
            return self._VECTORS[key]
        for known_key in sorted(self._VECTORS, key=len, reverse=True):
            if known_key in key:
                return self._VECTORS[known_key]
        return [0.0, 0.0, 1.0]


@pytest.fixture
def service(tmp_path) -> ChatbotService:
    """ChatbotService com só o cache semântico inicializado (sem LLM/Ollama)."""
    svc = object.__new__(ChatbotService)
    svc.db_url = str(tmp_path / "lancedb")
    svc.embedder = _DeterministicEmbedder()
    svc.document_files = []
    # documents_hash vazio é tratado como inválido por _is_cache_entry_serving_eligible
    # (safeguard real: nunca servir do cache se não há documentos carregados).
    # Fixamos um hash não vazio para simular documentos indexados.
    svc._get_current_documents_hash = lambda: "test-documents-hash-v1"
    svc._setup_semantic_cache()
    return svc


def test_first_occurrence_is_candidate_and_not_served(service: ChatbotService):
    entry = service._track_question_frequency(
        "Qual a carga horária de ACC?", "A carga horária de ACC é de 200 horas."
    )
    assert entry["status"] == "candidate"
    assert entry["hit_count"] == 1

    # Candidate não é servido do cache mesmo com pergunta idêntica.
    assert service._search_cache("Qual a carga horária de ACC?") is None


def test_promotion_to_trusted_after_repeated_questions(service: ChatbotService):
    question = "Qual a carga horária de ACC?"
    answer = "A carga horária de ACC é de 200 horas."

    for expected_count in range(1, SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD):
        entry = service._track_question_frequency(question, answer)
        assert entry["hit_count"] == expected_count
        assert entry["status"] == "candidate"
        assert service._search_cache(question) is None

    # N-ésima repetição cruza o limiar -> trusted -> passa a ser servido do cache.
    entry = service._track_question_frequency(question, answer)
    assert entry["hit_count"] == SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD
    assert entry["status"] == "trusted"

    cached = service._search_cache(question)
    assert cached is not None
    assert cached["answer"] == answer

    # Paráfrase também deve ser servida (busca por similaridade vetorial).
    cached_paraphrase = service._search_cache("Quantas horas de ACC são necessárias?")
    assert cached_paraphrase is not None
    assert cached_paraphrase["answer"] == answer


def test_paraphrases_share_the_same_frequency_counter(service: ChatbotService):
    """Reproduz o caso do usuário: 3 redações diferentes da mesma pergunta.

    "Quantas horas sao ACC?" / "Qual a carga horária de ACC?" / "Carga horária
    de ACC?" têm question_key exatos DIFERENTES, mas devem contar para o MESMO
    contador de frequência (via similaridade vetorial), promovendo a entrada a
    trusted na 3ª pergunta mesmo com 3 textos distintos.
    """
    answer = "A carga horária de ACC é de 200 horas."

    entry1 = service._track_question_frequency("Quantas horas sao ACC?", answer)
    assert entry1["hit_count"] == 1
    assert entry1["status"] == "candidate"

    entry2 = service._track_question_frequency("Qual a carga horária de ACC?", answer)
    assert entry2["hit_count"] == 2
    assert entry2["status"] == "candidate"
    # Mesma entrada (mesma question_key) sendo atualizada, não uma nova linha.
    assert entry2["question_key"] == entry1["question_key"]

    entry3 = service._track_question_frequency("Carga horária de ACC?", answer)
    assert entry3["hit_count"] == 3
    assert entry3["status"] == "trusted"
    assert entry3["question_key"] == entry1["question_key"]

    # Só deve existir UMA linha no cache para as 3 redações.
    df = service._cache_table.to_pandas()
    assert len(df) == 1

    cached = service._search_cache("Quantas horas sao ACC?")
    assert cached is not None
    assert cached["answer"] == answer


def test_unrelated_question_is_not_served_from_cache(service: ChatbotService):
    question = "Qual a carga horária de ACC?"
    answer = "A carga horária de ACC é de 200 horas."
    for _ in range(SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD):
        service._track_question_frequency(question, answer)

    assert service._search_cache("Qual o valor da mensalidade?") is None


def test_safeguard_documents_hash_invalidates_trusted_entry(service: ChatbotService, monkeypatch):
    question = "Qual a carga horária de ACC?"
    answer = "A carga horária de ACC é de 200 horas."
    for _ in range(SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD):
        service._track_question_frequency(question, answer)

    assert service._search_cache(question) is not None

    # Simula reindexação dos documentos (hash muda) -> entrada trusted antiga
    # não deve mais ser servida, mesmo com similaridade 100%.
    monkeypatch.setattr(service, "_get_current_documents_hash", lambda: "outro-hash-de-documentos")
    assert service._search_cache(question) is None


def test_safeguard_ttl_expiration_invalidates_trusted_entry(service: ChatbotService):
    question = "Qual a carga horária de ACC?"
    answer = "A carga horária de ACC é de 200 horas."
    for _ in range(SEMANTIC_CACHE_FREQUENCY_PROMOTION_THRESHOLD):
        service._track_question_frequency(question, answer)

    assert service._search_cache(question) is not None

    # Força a entrada trusted a já ter expirado (TTL vencido).
    df = service._cache_table.to_pandas()
    row = df.iloc[0].to_dict()
    row["expires_at"] = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    service._cache_table.delete(f"question_key = '{row['question_key']}'")
    service._cache_table.add([row])

    assert service._search_cache(question) is None


def test_sliding_ttl_is_renewed_on_each_repetition(service: ChatbotService):
    question = "Qual a carga horária de ACC?"
    answer = "A carga horária de ACC é de 200 horas."

    service._track_question_frequency(question, answer)
    df = service._cache_table.to_pandas()
    first_expires_at = df.iloc[0]["expires_at"]

    # Repetição subsequente deve empurrar expires_at para mais longe no futuro.
    import time

    time.sleep(0.01)
    service._track_question_frequency(question, answer)
    df = service._cache_table.to_pandas()
    second_expires_at = df.iloc[0]["expires_at"]

    assert second_expires_at > first_expires_at
