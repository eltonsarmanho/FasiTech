"""
Gerenciamento de sessão e lógica do chatbot do Diretor Virtual.

Fluxo de ticket:
  1. Boas-vindas → pede matrícula
  2. Matrícula → pede nome
  3. Nome → pede e-mail
  4. E-mail → gera ticket TKT-{hash}, exibe menu
  5. Menu: 1=RAG, 2=Secretaria, 3=Diretor, 4=Encerrar
"""
from __future__ import annotations

import hashlib
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import logging

logger = logging.getLogger(__name__)


# ── Constantes ────────────────────────────────────────────────────────────────

MENU_TEXT = (
    "\n\nEscolha uma opção:\n"
    "1️⃣  Fazer uma pergunta\n"
    "2️⃣  Falar com Secretaria\n"
    "3️⃣  Falar com Diretor\n"
    "4️⃣  Encerrar"
)

SESSION_TTL_SECONDS = 3600  # 1 hora de inatividade expira a sessão


# ── Estado ────────────────────────────────────────────────────────────────────

class ChatState(str, Enum):
    AWAITING_MATRICULA = "awaiting_matricula"
    AWAITING_NOME = "awaiting_nome"
    AWAITING_EMAIL = "awaiting_email"
    MENU = "menu"
    ASKING_QUESTION = "asking_question"
    ESCALATED = "escalated"
    ENDED = "ended"


@dataclass
class ChatSession:
    session_id: str
    state: ChatState = ChatState.AWAITING_MATRICULA
    matricula: Optional[str] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    ticket_id: Optional[str] = None
    chatwoot_conversation_id: Optional[int] = None
    welcomed: bool = False
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_activity = time.time()

    def is_expired(self) -> bool:
        return time.time() - self.last_activity > SESSION_TTL_SECONDS


# ── Registro de sessões (em memória) ─────────────────────────────────────────

_sessions: dict[str, ChatSession] = {}
_sessions_by_conversation: dict[int, ChatSession] = {}


def _cleanup_expired() -> None:
    expired = [sid for sid, s in _sessions.items() if s.is_expired()]
    for sid in expired:
        del _sessions[sid]
    expired_conv = [cid for cid, s in _sessions_by_conversation.items() if s.is_expired()]
    for cid in expired_conv:
        del _sessions_by_conversation[cid]


def get_or_create_session(session_id: Optional[str]) -> ChatSession:
    _cleanup_expired()
    if session_id and session_id in _sessions:
        sess = _sessions[session_id]
        sess.touch()
        return sess
    new_id = str(uuid.uuid4())
    sess = ChatSession(session_id=new_id)
    _sessions[new_id] = sess
    return sess


def get_or_create_session_by_conversation(conversation_id: int) -> tuple[ChatSession, bool]:
    """
    Sessão endereçada pelo conversation_id do Chatwoot (usada pelo webhook —
    o widget nativo do Chatwoot não conhece nosso session_id de UUID).
    Retorna (sessão, criada_agora).
    """
    _cleanup_expired()
    existing = _sessions_by_conversation.get(conversation_id)
    if existing:
        existing.touch()
        return existing, False
    sess = ChatSession(session_id=str(uuid.uuid4()), chatwoot_conversation_id=conversation_id)
    _sessions_by_conversation[conversation_id] = sess
    return sess, True


# ── Validações ───────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# 12 dígitos: 4 primeiros = ano (1990–2099), 8 restantes = sequencial
_MATRICULA_RE = re.compile(r"^(19|20)\d{2}\d{8}$")


def _valid_email(text: str) -> bool:
    return bool(_EMAIL_RE.match(text.strip()))


def _valid_matricula(text: str) -> bool:
    """Aceita exatamente 12 dígitos, onde os 4 primeiros formam um ano razoável."""
    return bool(_MATRICULA_RE.match(text.strip()))


def _valid_nome(text: str) -> bool:
    """Exige pelo menos dois termos com ≥ 2 caracteres cada (nome composto)."""
    partes = [p for p in text.strip().split() if len(p) >= 2]
    return len(partes) >= 2


# ── Geração de ticket ─────────────────────────────────────────────────────────

def _generate_ticket(matricula: str, nome: str, email: str) -> str:
    raw = f"{matricula}|{nome}|{email}|{time.time()}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:8].upper()
    return f"TKT-{h}"


# ── Processador principal ─────────────────────────────────────────────────────

def process_message(session: ChatSession, user_msg: str) -> dict:
    """
    Processa a mensagem do usuário e retorna:
      {
        "response": str,
        "options": list[str] | None,
        "ticket_id": str | None,
        "state": ChatState,
      }
    """
    msg = user_msg.strip()
    result: dict = {
        "response": "",
        "options": None,
        "ticket_id": session.ticket_id,
        "state": session.state,
    }

    # ── AWAITING_MATRICULA ────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_MATRICULA:
        if not _valid_matricula(msg):
            result["response"] = (
                "⚠️ Matrícula inválida. Informe os 12 dígitos da matrícula "
                "(ex: *202116040020*). Os 4 primeiros dígitos devem ser o ano de ingresso."
            )
            return result
        session.matricula = msg.strip()
        session.state = ChatState.AWAITING_NOME
        result["response"] = "Diga seu nome completo."
        result["state"] = session.state
        return result

    # ── AWAITING_NOME ─────────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_NOME:
        if not _valid_nome(msg):
            result["response"] = (
                "⚠️ Por favor, informe seu *nome completo* (nome e sobrenome). "
                "Ex: *Elton Sarmanho*."
            )
            return result
        session.nome = msg.strip()
        session.state = ChatState.AWAITING_EMAIL
        result["response"] = "Diga seu e-mail institucional."
        result["state"] = session.state
        return result

    # ── AWAITING_EMAIL ────────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_EMAIL:
        if not _valid_email(msg):
            result["response"] = (
                "⚠️ E-mail inválido. Por favor, informe um e-mail válido "
                "(ex: *nome@ufpa.br*)."
            )
            return result
        session.email = msg.lower().strip()
        ticket = _generate_ticket(session.matricula, session.nome, session.email)
        session.ticket_id = ticket
        session.state = ChatState.MENU
        result["ticket_id"] = ticket
        result["response"] = (
            f"✅ *Ticket Registrado: {ticket}*\n\n"
            f"Olá, *{session.nome}*! Sua matrícula *{session.matricula}* foi identificada."
            + MENU_TEXT
        )
        result["options"] = [
            "1 - Fazer uma pergunta",
            "2 - Falar com Secretaria",
            "3 - Falar com Diretor",
            "4 - Encerrar",
        ]
        result["state"] = session.state
        return result

    # ── MENU ──────────────────────────────────────────────────────────────────
    if session.state == ChatState.MENU:
        choice = msg.strip()[:1]

        if choice == "1":
            session.state = ChatState.ASKING_QUESTION
            result["response"] = "📚 Qual é sua dúvida? Pode perguntar sobre TCC, ACC, estágio, PPC, matrículas e normas do curso."
            result["state"] = session.state
            return result

        if choice == "2":
            result.update(_escalate(session, team="secretaria"))
            return result

        if choice == "3":
            result.update(_escalate(session, team="diretor"))
            return result

        if choice == "4":
            session.state = ChatState.ENDED
            result["response"] = "Obrigado por utilizar o Diretor Virtual da FASI. Até logo! 👋"
            result["state"] = session.state
            return result

        # Opção inválida
        result["response"] = "Por favor, escolha uma opção válida:" + MENU_TEXT
        result["options"] = [
            "1 - Fazer uma pergunta",
            "2 - Falar com Secretaria",
            "3 - Falar com Diretor",
            "4 - Encerrar",
        ]
        return result

    # ── ASKING_QUESTION ───────────────────────────────────────────────────────
    if session.state == ChatState.ASKING_QUESTION:
        rag_answer = _call_rag(msg)
        session.state = ChatState.MENU
        result["response"] = f"{rag_answer}" + MENU_TEXT
        result["options"] = [
            "1 - Fazer outra pergunta",
            "2 - Falar com Secretaria",
            "3 - Falar com Diretor",
            "4 - Encerrar",
        ]
        result["state"] = session.state
        return result

    # ── ESCALATED / ENDED ─────────────────────────────────────────────────────
    if session.state in (ChatState.ESCALATED, ChatState.ENDED):
        result["response"] = (
            "Sua conversa foi encaminhada. Para iniciar um novo atendimento, recarregue a página."
        )
        return result

    result["response"] = "Estado inválido. Por favor, recarregue a página."
    return result


# ── RAG ───────────────────────────────────────────────────────────────────────

def _call_rag(question: str) -> str:
    try:
        from backend.infrastructure.rag.rag_ppc import get_service
        service = get_service()
        result = service.ask_question(question)
        if result.get("success"):
            return result["answer"]
        return result.get("message") or result.get("error") or "Não foi possível responder."
    except Exception as exc:
        logger.error("Erro ao chamar RAG: %s", exc)
        return "⚠️ O assistente de perguntas está temporariamente indisponível. Tente novamente em instantes."


# ── Escalação para Chatwoot ───────────────────────────────────────────────────

def _escalate(session: ChatSession, team: str) -> dict:
    from backend.config.settings import settings

    team_names = {"secretaria": "Secretaria", "diretor": "Direção"}
    team_label = team_names.get(team, team.capitalize())

    team_id = (
        settings.chatwoot_team_id_secretaria
        if team == "secretaria"
        else settings.chatwoot_team_id_diretor
    )

    context = (
        f"📋 Novo atendimento via Diretor Virtual\n"
        f"Ticket: {session.ticket_id}\n"
        f"Matrícula: {session.matricula}\n"
        f"Nome: {session.nome}\n"
        f"E-mail: {session.email}\n"
        f"Solicitação: Falar com {team_label}"
    )

    try:
        from backend.infrastructure.chatwoot.chatwoot_service import escalate_to_team
        conv_id = escalate_to_team(
            name=session.nome,
            email=session.email,
            matricula=session.matricula,
            ticket_id=session.ticket_id,
            team_id=team_id,
            inbox_id=settings.chatwoot_inbox_id_chatweb,
            context_message=context,
        )
        session.chatwoot_conversation_id = conv_id
        session.state = ChatState.ESCALATED
        logger.info(
            "Escalação bem-sucedida: ticket=%s equipe=%s conv_chatwoot=%s",
            session.ticket_id, team, conv_id,
        )
        response = (
            f"✅ Sua solicitação foi encaminhada para a **{team_label}**!\n\n"
            f"🎫 Ticket: *{session.ticket_id}*\n"
            f"Em breve um(a) atendente entrará em contato pelo e-mail *{session.email}*.\n\n"
            "Para nova dúvida, inicie um novo atendimento."
        )
    except Exception as exc:
        logger.error(
            "FALHA ao escalar para Chatwoot (equipe=%s ticket=%s url=%s): %s",
            team, session.ticket_id,
            __import__('os').getenv('CHATWOOT_API_URL', '?'),
            exc,
            exc_info=True,
        )
        session.state = ChatState.ESCALATED
        response = (
            f"✅ Sua solicitação para falar com a **{team_label}** foi registrada.\n\n"
            f"🎫 Ticket: *{session.ticket_id}*\n"
            "Em breve um(a) atendente entrará em contato. Para nova dúvida, inicie um novo atendimento."
        )

    return {
        "response": response,
        "options": None,
        "ticket_id": session.ticket_id,
        "state": session.state,
    }
