"""
Serviço de integração com o Chatwoot.

Responsável por criar contatos, conversas e atribuir equipes via REST API do Chatwoot.
Documentação oficial: https://www.chatwoot.com/developers/api

Todas as funções lêem as settings de forma lazy (na chamada, não no import),
para garantir que variáveis de ambiente alteradas após o boot sejam refletidas
e para facilitar testes unitários com mock.
"""
from __future__ import annotations

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


def _cfg() -> tuple[str, int, str]:
    """Retorna (base_url, account_id, token) lendo as settings no momento da chamada."""
    from backend.config.settings import settings
    base = settings.chatwoot_api_url.rstrip("/")
    acct = settings.chatwoot_account_id
    token = settings.chatwoot_api_token
    return base, acct, token


def _headers(token: str) -> dict:
    return {"api_access_token": token, "Content-Type": "application/json"}


def _url(base: str, acct: int, path: str) -> str:
    return f"{base}/api/v1/accounts/{acct}/{path.lstrip('/')}"


def check_connection() -> dict:
    """Verifica conectividade com o Chatwoot. Útil para diagnóstico."""
    base, acct, token = _cfg()
    if not token or not base:
        return {"ok": False, "error": "CHATWOOT_API_TOKEN ou CHATWOOT_API_URL não configurados"}
    try:
        r = httpx.get(
            f"{base}/api/v1/accounts/{acct}/inboxes",
            headers=_headers(token),
            timeout=8,
        )
        r.raise_for_status()
        inboxes = r.json().get("payload", [])
        # Listar equipes
        rt = httpx.get(
            f"{base}/api/v1/accounts/{acct}/teams",
            headers=_headers(token),
            timeout=8,
        )
        rt.raise_for_status()
        teams = rt.json()
        return {
            "ok": True,
            "base_url": base,
            "account_id": acct,
            "inboxes": [{"id": i["id"], "name": i["name"]} for i in inboxes],
            "teams": teams,
        }
    except httpx.ConnectError as exc:
        return {"ok": False, "error": f"Conexão recusada/DNS falhou: {exc}"}
    except httpx.HTTPStatusError as exc:
        return {"ok": False, "error": f"HTTP {exc.response.status_code}: {exc.response.text[:200]}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Contatos ──────────────────────────────────────────────────────────────────

def create_or_get_contact(*, name: str, email: str, phone: Optional[str] = None) -> int:
    """Cria ou busca um contato no Chatwoot. Retorna o contact_id."""
    base, acct, token = _cfg()
    hdrs = _headers(token)

    # Tenta buscar por e-mail primeiro
    try:
        r = httpx.get(
            _url(base, acct, "contacts/search"),
            params={"q": email, "include_contacts": "true"},
            headers=hdrs,
            timeout=10,
        )
        r.raise_for_status()
        items = r.json().get("payload", [])
        if items:
            contact_id = items[0]["id"]
            logger.info("Chatwoot: contato existente encontrado id=%s", contact_id)
            return contact_id
    except Exception as exc:
        logger.warning("Chatwoot: falha ao buscar contato — %s", exc)

    # Cria novo contato
    payload: dict = {"name": name, "email": email}
    if phone:
        payload["phone_number"] = phone

    r = httpx.post(_url(base, acct, "contacts"), json=payload, headers=hdrs, timeout=10)
    r.raise_for_status()
    contact_id = r.json()["id"]
    logger.info("Chatwoot: novo contato criado id=%s email=%s", contact_id, email)
    return contact_id


# ── Conversas ─────────────────────────────────────────────────────────────────

def create_conversation(
    *,
    contact_id: int,
    inbox_id: int,
    additional_attributes: Optional[dict] = None,
) -> int:
    """Cria uma nova conversa e retorna o conversation_id."""
    base, acct, token = _cfg()
    payload: dict = {"contact_id": contact_id, "inbox_id": inbox_id}
    if additional_attributes:
        payload["additional_attributes"] = additional_attributes

    r = httpx.post(
        _url(base, acct, "conversations"),
        json=payload,
        headers=_headers(token),
        timeout=10,
    )
    r.raise_for_status()
    conv_id = r.json()["id"]
    logger.info("Chatwoot: conversa criada id=%s contact=%s inbox=%s", conv_id, contact_id, inbox_id)
    return conv_id


def assign_team(conversation_id: int, team_id: int) -> None:
    """Atribui uma equipe a uma conversa existente."""
    if not team_id:
        logger.warning("Chatwoot: team_id=0, atribuição de equipe ignorada")
        return
    base, acct, token = _cfg()
    r = httpx.post(
        _url(base, acct, f"conversations/{conversation_id}/assignments"),
        json={"team_id": team_id},
        headers=_headers(token),
        timeout=10,
    )
    r.raise_for_status()
    logger.info("Chatwoot: conversa %s atribuída à equipe %s", conversation_id, team_id)


def send_message(conversation_id: int, content: str, *, private: bool = False) -> None:
    """Envia uma mensagem (bot/agente) em uma conversa do Chatwoot."""
    base, acct, token = _cfg()
    payload = {"content": content, "message_type": "outgoing", "private": private}
    r = httpx.post(
        _url(base, acct, f"conversations/{conversation_id}/messages"),
        json=payload,
        headers=_headers(token),
        timeout=10,
    )
    r.raise_for_status()
    logger.info("Chatwoot: mensagem enviada na conversa %s (private=%s)", conversation_id, private)


# ── Helper alto nível ─────────────────────────────────────────────────────────

def escalate_to_team(
    *,
    name: str,
    email: str,
    matricula: str,
    ticket_id: str,
    team_id: int,
    inbox_id: int,
    context_message: str,
) -> int:
    """
    Cria contato + conversa no Chatwoot e atribui à equipe indicada.
    Retorna o conversation_id criado.
    Lança exceção em caso de falha (para o chamador registrar no log).
    """
    contact_id = create_or_get_contact(name=name, email=email)
    conversation_id = create_conversation(
        contact_id=contact_id,
        inbox_id=inbox_id,
        additional_attributes={"matricula": matricula, "ticket_id": ticket_id},
    )
    assign_team(conversation_id, team_id)
    send_message(conversation_id, context_message, private=True)
    return conversation_id
