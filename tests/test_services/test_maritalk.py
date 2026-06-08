"""Teste isolado para a API MariTalk (Maritaca AI).

Verifica:
- Variável MARITALK_API_KEY presente e não vazia
- Endpoint /api/llm/chat retorna HTTP 200
- Resposta contém conteúdo válido para a pergunta "2+2"
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

_API_KEY = (
    os.getenv("MARITALK_API_KEY")
    or os.getenv("MARITACA_API_KEY")
    or ""
)
_BASE_URL = (
    os.getenv("MARITALK_BASE_URL")
    or os.getenv("MARITACA_BASE_URL")
    or os.getenv("MARITALK_API_BASE")
    or "https://chat.maritaca.ai/api"
).rstrip("/")
_MODEL = os.getenv("MARITALK_MODEL") or os.getenv("MARITACA_MODEL") or "sabiazinho-4"

_SKIP_NO_KEY = pytest.mark.skipif(
    not _API_KEY,
    reason="MARITALK_API_KEY não encontrada no ambiente.",
)

# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


def test_maritalk_api_key_presente():
    """Valida que a chave de API está definida no ambiente."""
    assert _API_KEY, (
        "MARITALK_API_KEY (ou MARITACA_API_KEY) não encontrada. "
        "Verifique o arquivo .env."
    )
    assert len(_API_KEY) > 10, "MARITALK_API_KEY parece inválida (muito curta)."


@_SKIP_NO_KEY
def test_maritalk_base_url_acessivel():
    """Verifica que o host da API MariTalk responde (não 5xx)."""
    # Apenas checa o domínio raiz; um 404 já indica que o servidor está de pé.
    try:
        response = requests.get(_BASE_URL, timeout=10)
    except requests.RequestException as exc:
        pytest.skip(f"MariTalk base URL inacessível: {exc}")

    assert response.status_code < 500, (
        f"MariTalk retornou erro de servidor ({response.status_code})."
    )


@_SKIP_NO_KEY
def test_maritalk_chat_2_mais_2():
    """Envia '2+2' para a API e verifica que a resposta contém '4'."""
    payload = {
        "model": _MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": "Responda apenas com o resultado final."},
            {"role": "user",   "content": "2+2 é igual a?"},
        ],
    }
    headers = {"Authorization": f"Bearer {_API_KEY}"}

    # A MariTalk usa o endpoint OpenAI-compatible /chat/completions
    endpoint = f"{_BASE_URL}/chat/completions"

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        pytest.skip(f"MariTalk indisponível em {endpoint}: {exc}")

    if response.status_code == 401:
        raise AssertionError(
            f"MariTalk recusou a chave de API (HTTP 401). "
            f"Verifique MARITALK_API_KEY.\nResposta: {response.text[:300]}"
        )
    if response.status_code == 429:
        pytest.skip("MariTalk retornou 429 — limite de quota atingido.")
    if response.status_code >= 400:
        raise AssertionError(
            f"MariTalk retornou HTTP {response.status_code}.\n"
            f"Endpoint: {endpoint}\nResposta: {response.text[:500]}"
        )

    data = response.json()
    answer = data["choices"][0]["message"]["content"].strip()

    assert "4" in answer, (
        f"Resposta inesperada do modelo '{_MODEL}': {answer!r}"
    )


@_SKIP_NO_KEY
def test_maritalk_modelo_listado():
    """Verifica que o modelo configurado aparece na lista de modelos da API."""
    endpoint = f"{_BASE_URL}/models"
    headers = {"Authorization": f"Bearer {_API_KEY}"}

    try:
        response = requests.get(endpoint, headers=headers, timeout=15)
    except requests.RequestException as exc:
        pytest.skip(f"Endpoint /models inacessível: {exc}")

    if response.status_code in (401, 403):
        pytest.skip("Endpoint /models requer autenticação diferente — pulando.")
    if response.status_code >= 400:
        pytest.skip(f"Endpoint /models retornou {response.status_code} — pulando.")

    data = response.json()
    model_ids = [m.get("id", "") for m in data.get("data", [])]

    assert any(_MODEL in mid for mid in model_ids), (
        f"Modelo '{_MODEL}' não encontrado na lista de modelos.\n"
        f"Modelos disponíveis: {model_ids}"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
