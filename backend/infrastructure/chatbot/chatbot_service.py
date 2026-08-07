"""
Gerenciamento de sessão e lógica do chatbot do Diretor Virtual.

Fluxo de ticket (identificação):
  1. Boas-vindas → pede matrícula
  2. Matrícula → pede nome
  3. Nome → pede e-mail
  4. E-mail → gera ticket TKT-{hash}, exibe menu
  5. Menu: 1=RAG, 2=Secretaria, 3=Diretor, 4=Encerrar

Fluxo de atendimento (pós-ticket):
  MENU --1--> ASKING_QUESTION --pergunta--> RAG
    • resposta direta            → volta ao MENU (com o menu anexado)
    • pedido de esclarecimento   → AWAITING_CLARIFICATION

  Em AWAITING_CLARIFICATION o bot NÃO exibe o menu: a próxima mensagem é lida
  como resposta ao esclarecimento (ex.: "2026.4") e reenviada ao RAG junto com
  a pergunta original. Sem esse estado, "2026.4" caía no parser do menu e era
  lido como a opção "2" (Falar com Secretário), escalando o atendimento por
  engano no meio de uma pergunta.

Reconhecimento de contato (WhatsApp):
  Na abertura, se o telefone já estiver no diretório de contatos conhecidos, o
  bot pergunta "Quem está falando é *Vitor B.*?" em vez de pedir matrícula,
  nome e e-mail de novo. Confirmando, gera um ticket NOVO (é um atendimento
  novo) e vai direto ao menu.

  Regras de segurança, todas estruturais e não apenas política:
    • Nunca preenche identidade sem um "sim" explícito de quem está digitando.
    • O nome exibido é mascarado ("Vitor B."): suficiente para o dono se
      reconhecer, inútil como vazamento para quem não é. Matrícula e e-mail
      jamais aparecem na pergunta de confirmação.
    • Reconhecimento vence em RECONHECIMENTO_VALIDADE_DIAS — fecha a janela de
      número reciclado pela operadora.
    • "Não sou eu" desativa o vínculo; telefone compartilhado para de ser
      oferecido.
    • O handoff para humano diz se a identificação foi automática ou digitada.
    • Telefone só aparece em log mascarado (backend/utils/phone.py).
    • "esquecer meus dados" apaga o vínculo (LGPD art. 18).
  Qualquer falha no diretório degrada para o fluxo manual — nunca para erro.

Padrões de atendimento aplicados:
  • Correspondência estrita de opção de menu (nunca por prefixo do texto).
  • Slot-filling com contexto: a pergunta pendente sobrevive ao esclarecimento.
  • Limite de tentativas (no-match) em todo laço, com saída para atendimento
    humano — nunca um loop infinito de "opção inválida".
  • Comandos de escape globais ("menu", "voltar", "encerrar", "atendente").
  • Fallback de texto livre: uma pergunta digitada no menu é respondida em vez
    de rejeitada como opção inválida.
  • Handoff com contexto: a última pergunta do aluno vai na nota privada da
    equipe que recebe o atendimento.

Nota de arquitetura: `backend/infrastructure/database/engine.py` levanta erro no
import quando `DATABASE_URL` não está no ambiente. Por isso todo acesso ao banco
aqui é import preguiçoso dentro da função, em try/except — igual ao que já se
faz com o RAG e com o Chatwoot.
"""
from __future__ import annotations

import hashlib
import re
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

import logging

logger = logging.getLogger(__name__)


# ── Constantes ────────────────────────────────────────────────────────────────

MENU_TEXT = (
    "\n\nEscolha uma opção:\n"
    "1️⃣  Fazer uma pergunta\n"
    "2️⃣  Falar com Secretário\n"
    "3️⃣  Falar com Diretor\n"
    "4️⃣  Encerrar"
)

CLARIFICATION_HINT = (
    "\n\n_Responda apenas com o período (ex.: *2026.4*), "
    "ou digite *menu* para voltar às opções._"
)

WELCOME_MESSAGE = (
    "Olá! Sou o Diretor Virtual da FASI 🤖\n\n"
    "Posso ajudá-lo com dúvidas sobre matrículas, TCC, ACC, estágio, PPC e normas do curso.\n\n"
    "Para começar, diga sua **matrícula**:"
)

CONFIRMACAO_TEXT = (
    "\n\nEscolha uma opção:\n"
    "1️⃣  Sim, sou eu\n"
    "2️⃣  Não sou eu"
)

SESSION_TTL_SECONDS = 3600  # 1 hora de inatividade expira a sessão

# Quantas vezes o bot re-pergunta antes de oferecer atendimento humano.
MAX_CLARIFICATION_ATTEMPTS = 2
MAX_INVALID_ATTEMPTS = 3

# Depois disso sem atendimento, o vínculo telefone → aluno não é mais oferecido
# e o aluno refaz a identificação completa (que renova o registro).
RECONHECIMENTO_VALIDADE_DIAS = 180


# ── Estado ────────────────────────────────────────────────────────────────────

class ChatState(str, Enum):
    AWAITING_IDENTITY_CONFIRMATION = "awaiting_identity_confirmation"
    AWAITING_MATRICULA = "awaiting_matricula"
    AWAITING_NOME = "awaiting_nome"
    AWAITING_EMAIL = "awaiting_email"
    MENU = "menu"
    ASKING_QUESTION = "asking_question"
    AWAITING_CLARIFICATION = "awaiting_clarification"
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
    # Pergunta que aguarda esclarecimento (slot-filling multi-turno).
    pending_question: Optional[str] = None
    # Última pergunta feita — vai no handoff para a equipe humana.
    last_question: Optional[str] = None
    clarification_attempts: int = 0
    invalid_attempts: int = 0
    # Identidade do contato no canal (WhatsApp: telefone canônico).
    contact_channel: Optional[str] = None
    contact_key: Optional[str] = None
    chatwoot_contact_id: Optional[int] = None
    # Candidato do diretório aguardando confirmação do aluno.
    recognized: Optional[dict] = None
    # True quando a identidade veio do reconhecimento, não foi digitada agora.
    auto_identified: bool = False
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


def reset_session_for_conversation(conversation_id: int) -> ChatSession:
    """
    Descarta a sessão da conversa e devolve uma nova, do zero.

    Usado quando o aluno volta a escrever depois de ter encerrado (opção 4):
    em vez de o bot ficar mudo até o TTL expirar, o atendimento recomeça.

    A identidade do CANAL (telefone/contato do Chatwoot) é preservada — ela não
    pertence ao atendimento, e sim à pessoa —, mas matrícula, nome, e-mail e
    ticket somem: o novo atendimento passa pelo reconhecimento outra vez e
    ganha um ticket novo.
    """
    anterior = _sessions_by_conversation.get(conversation_id)
    sess = ChatSession(session_id=str(uuid.uuid4()), chatwoot_conversation_id=conversation_id)
    if anterior:
        sess.contact_channel = anterior.contact_channel
        sess.contact_key = anterior.contact_key
        sess.chatwoot_contact_id = anterior.chatwoot_contact_id
    _sessions_by_conversation[conversation_id] = sess
    return sess


# ── Normalização de texto ─────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Minúsculas, sem acentos, sem pontuação de borda, espaços colapsados."""
    t = (text or "").strip().lower()
    # Emojis de teclado numérico ("1️⃣") viram o dígito puro.
    t = t.replace("\ufe0f", "").replace("\u20e3", "")
    t = unicodedata.normalize("NFD", t)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .!?,;:*_")


# ── Menu ──────────────────────────────────────────────────────────────────────

# Rótulos que o bot pode emitir por opção (o item 1 muda de texto após a 1ª
# resposta). Usados para reconhecer o payload devolvido pelos quick-replies do
# Chatwoot, que chega como a string inteira ("2 - Falar com Secretário").
_MENU_LABELS: dict[str, tuple[str, ...]] = {
    "1": ("Fazer uma pergunta", "Fazer outra pergunta"),
    "2": ("Falar com Secretário",),
    "3": ("Falar com Diretor",),
    "4": ("Encerrar",),
}

# Sinônimos digitados livremente pelo aluno.
_MENU_SYNONYMS: dict[str, str] = {
    "pergunta": "1", "perguntar": "1", "duvida": "1", "duvidas": "1",
    "outra pergunta": "1", "nova pergunta": "1", "quero perguntar": "1",
    "secretaria": "2", "secretario": "2", "falar com a secretaria": "2",
    "diretor": "3", "direcao": "3", "falar com o diretor": "3",
    # Só encerramentos inequívocos. "não" e "obrigado" ficam de fora de
    # propósito: podem significar "não, isso não respondeu minha dúvida".
    "encerrar": "4", "sair": "4", "finalizar": "4", "tchau": "4",
    "ate logo": "4", "encerrar atendimento": "4",
}


def _build_menu_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for digit, labels in _MENU_LABELS.items():
        lookup[digit] = digit
        for label in labels:
            lookup[_normalize(label)] = digit
            # Payload exato dos quick-replies do Chatwoot.
            lookup[_normalize(f"{digit} - {label}")] = digit
    lookup.update(_MENU_SYNONYMS)
    return lookup


_MENU_LOOKUP: dict[str, str] = _build_menu_lookup()

# Pedidos genéricos de atendimento humano (sem dizer qual equipe).
_HUMAN_HANDOFF_TERMS = frozenset({
    "atendente", "humano", "pessoa", "alguem", "suporte", "falar com atendente",
    "falar com alguem", "falar com uma pessoa", "quero falar com um atendente",
    "quero falar com alguem",
})


def _match_menu_option(msg: str) -> Optional[str]:
    """
    Reconhece a opção de menu escolhida — e SÓ ela.

    Correspondência exata sobre a mensagem inteira normalizada. É o que impede
    que "2026.4" (resposta a um esclarecimento) ou "3 disciplinas" virem uma
    escolha de menu, como acontecia com o antigo `msg.strip()[:1]`.
    """
    return _MENU_LOOKUP.get(_normalize(msg))


def _menu_options(first_label: str = "Fazer uma pergunta") -> list[str]:
    return [
        f"1 - {first_label}",
        "2 - Falar com Secretário",
        "3 - Falar com Diretor",
        "4 - Encerrar",
    ]


# ── Confirmação de identidade ─────────────────────────────────────────────────

_CONFIRMACAO_LABELS: dict[str, tuple[str, ...]] = {
    "sim": ("Sim, sou eu",),
    "nao": ("Não sou eu",),
}

_CONFIRMACAO_SYNONYMS: dict[str, str] = {
    "sim": "sim", "s": "sim", "sou eu": "sim", "isso": "sim", "isso mesmo": "sim",
    "confirmo": "sim", "correto": "sim", "exato": "sim", "positivo": "sim",
    "nao": "nao", "n": "nao", "outra pessoa": "nao", "sou outra pessoa": "nao",
    "negativo": "nao", "nao sou": "nao", "errado": "nao",
}


def _build_confirmacao_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for digito, resposta in (("1", "sim"), ("2", "nao")):
        lookup[digito] = resposta
        for label in _CONFIRMACAO_LABELS[resposta]:
            lookup[_normalize(label)] = resposta
            # Payload exato do quick-reply do Chatwoot.
            lookup[_normalize(f"{digito} - {label}")] = resposta
    lookup.update(_CONFIRMACAO_SYNONYMS)
    return lookup


_CONFIRMACAO_LOOKUP: dict[str, str] = _build_confirmacao_lookup()


def _match_sim_nao(msg: str) -> Optional[str]:
    """
    Reconhece "sim"/"não" — por correspondência EXATA da mensagem inteira.

    Mesma regra estrita do menu: é o que impede que um texto qualquer que
    comece com "n" ou "2" seja lido como uma decisão sobre a identidade de
    alguém.
    """
    return _CONFIRMACAO_LOOKUP.get(_normalize(msg))


def _confirmacao_options() -> list[str]:
    return ["1 - Sim, sou eu", "2 - Não sou eu"]


def _nome_para_exibir(nome: str) -> str:
    """
    'Vitor Benedito Ribeiro Batista' → 'Vitor B.'

    O dono real se reconhece; para quem está com o número por acaso (reciclado
    pela operadora, celular emprestado) o vazamento é mínimo.
    """
    partes = [p for p in (nome or "").split() if p]
    if not partes:
        return "você"
    if len(partes) == 1:
        return partes[0]
    return f"{partes[0]} {partes[-1][0].upper()}."


def _looks_like_question(msg: str) -> bool:
    """
    Heurística de fallback de texto livre: no menu, uma frase que claramente é
    uma dúvida é respondida em vez de devolver "opção inválida".
    """
    raw = (msg or "").strip()
    if raw.endswith("?"):
        return True
    return len(raw.split()) >= 4


# ── Comandos de escape globais ────────────────────────────────────────────────

_GLOBAL_COMMANDS: dict[str, str] = {
    "menu": "menu", "voltar": "menu", "opcoes": "menu", "opcao": "menu",
    "cancelar": "menu", "inicio": "menu",
    "encerrar": "encerrar", "sair": "encerrar", "finalizar": "encerrar",
    "tchau": "encerrar",
    # LGPD art. 18 — direito de eliminação, disponível em qualquer ponto.
    "esquecer meus dados": "esquecer", "apagar meus dados": "esquecer",
    "excluir meus dados": "esquecer", "esquecer dados": "esquecer",
    "nao me reconheca": "esquecer",
}


def _match_global_command(msg: str) -> Optional[str]:
    """
    Comandos válidos em qualquer ponto do atendimento (pós-ticket).

    Só casam com a mensagem inteira, para não sequestrar perguntas legítimas
    que contenham a palavra (ex.: "qual o prazo para sair do curso?").
    """
    norm = _normalize(msg)
    if norm in _HUMAN_HANDOFF_TERMS:
        return "atendente"
    return _GLOBAL_COMMANDS.get(norm)


# ── Período letivo ────────────────────────────────────────────────────────────

_PERIOD_RE = re.compile(r"\b(20\d{2})\s*[./\-]\s*([1-4])\b")


def _extract_period(text: str) -> Optional[str]:
    """Extrai um período letivo no formato canônico 'AAAA.N' (ex.: '2026.4')."""
    m = _PERIOD_RE.search(text or "")
    if not m:
        return None
    return f"{m.group(1)}.{m.group(2)}"


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


# ── Helpers de resposta ───────────────────────────────────────────────────────

def _with_menu(session: ChatSession, text: str, first_label: str = "Fazer uma pergunta") -> dict:
    """Devolve ao menu, anexando o texto do menu e as quick-replies."""
    session.state = ChatState.MENU
    session.invalid_attempts = 0
    return {
        "response": text + MENU_TEXT,
        "options": _menu_options(first_label),
        "ticket_id": session.ticket_id,
        "state": session.state,
    }


# ── Diretório de contatos conhecidos ──────────────────────────────────────────
#
# Estas quatro funções são as ÚNICAS que tocam o banco. São módulo-level de
# propósito: os testes as substituem por dublês sem precisar de DATABASE_URL.
# Todas falham em silêncio — reconhecer é um bônus, não um requisito.

def _dentro_da_janela(registro: dict) -> bool:
    """
    O vínculo ainda vale? Passados RECONHECIMENTO_VALIDADE_DIAS sem atendimento,
    não oferecemos reconhecimento — é a defesa contra número reciclado pela
    operadora. O fluxo manual roda e renova o registro sozinho.
    """
    ultimo = registro.get("ultimo_atendimento_em")
    if not isinstance(ultimo, datetime):
        return False
    return datetime.utcnow() - ultimo <= timedelta(days=RECONHECIMENTO_VALIDADE_DIAS)


def _buscar_contato_conhecido(session: ChatSession) -> Optional[dict]:
    """Procura a identidade já confirmada para o contato desta sessão."""
    if not session.contact_key or not session.contact_channel:
        return None  # widget do site (sem telefone): fluxo idêntico ao de sempre
    try:
        from backend.infrastructure.database.repository import (
            buscar_chatbot_contato_conhecido,
        )
        from backend.utils.phone import variantes_telefone

        chaves = (
            variantes_telefone(session.contact_key)
            if session.contact_channel == "whatsapp"
            else [session.contact_key]
        )
        registro = buscar_chatbot_contato_conhecido(session.contact_channel, chaves)
    except Exception as exc:
        logger.warning("Diretório de contatos indisponível (%s) — seguindo manual", exc)
        return None

    if not registro:
        return None
    if not _dentro_da_janela(registro):
        logger.info(
            "Contato conhecido porém vencido (>%d dias) — pedindo identificação completa",
            RECONHECIMENTO_VALIDADE_DIAS,
        )
        return None
    return registro


def _registrar_identificacao(session: ChatSession, *, origem: str = "chatbot") -> None:
    """Memoriza o vínculo contato → aluno após uma identificação manual."""
    if not session.contact_key or not session.contact_channel:
        return
    try:
        from backend.infrastructure.database.repository import (
            upsert_chatbot_contato_conhecido,
        )
        upsert_chatbot_contato_conhecido(
            canal=session.contact_channel,
            chave=session.contact_key,
            matricula=session.matricula,
            nome=session.nome,
            email=session.email,
            chatwoot_contact_id=session.chatwoot_contact_id,
            ticket_id=session.ticket_id,
            origem=origem,
        )
        logger.info("Contato memorizado para atendimentos futuros (ticket=%s)", session.ticket_id)
    except Exception as exc:
        logger.warning("Falha ao memorizar contato (ticket=%s): %s", session.ticket_id, exc)


def _registrar_confirmacao(session: ChatSession) -> None:
    """Renova a janela de validade após o aluno confirmar que é ele."""
    if not session.contact_key or not session.contact_channel:
        return
    try:
        from backend.infrastructure.database.repository import (
            registrar_confirmacao_chatbot_contato,
        )
        registrar_confirmacao_chatbot_contato(
            session.contact_channel, session.contact_key, ticket_id=session.ticket_id
        )
    except Exception as exc:
        logger.warning("Falha ao registrar confirmação de contato: %s", exc)


def _desativar_contato(session: ChatSession) -> None:
    """Desliga o vínculo — "não sou eu" ou "esquecer meus dados"."""
    if not session.contact_key or not session.contact_channel:
        return
    try:
        from backend.infrastructure.database.repository import (
            desativar_chatbot_contato_conhecido,
        )
        desativar_chatbot_contato_conhecido(session.contact_channel, session.contact_key)
        logger.info("Vínculo de contato desativado a pedido do usuário")
    except Exception as exc:
        logger.warning("Falha ao desativar vínculo de contato: %s", exc)


def _espelhar_no_chatwoot(session: ChatSession) -> None:
    """
    Copia matrícula e ticket para os atributos do contato no Chatwoot, para o
    atendente enxergar no painel. Conveniência — a fonte da verdade é o banco.
    """
    if not session.chatwoot_contact_id or not session.matricula:
        return
    try:
        from backend.infrastructure.chatwoot.chatwoot_service import update_contact_attributes
        update_contact_attributes(
            session.chatwoot_contact_id,
            custom_attributes={
                "matricula": session.matricula,
                "ultimo_ticket": session.ticket_id or "",
                "identificado_em": datetime.utcnow().isoformat(timespec="seconds"),
            },
        )
    except Exception as exc:
        logger.warning("Falha ao espelhar atributos no Chatwoot: %s", exc)


# ── Abertura do atendimento ───────────────────────────────────────────────────

def start_session(session: ChatSession) -> dict:
    """
    Abre o atendimento: oferece reconhecimento se o contato já for conhecido,
    senão manda as boas-vindas de sempre.

    Retorna o mesmo formato de `process_message`, mais um "action" para o log
    do webhook.
    """
    registro = _buscar_contato_conhecido(session)

    if not registro:
        return {
            "response": WELCOME_MESSAGE,
            "options": None,
            "ticket_id": None,
            "state": session.state,
            "action": "boas-vindas enviadas",
        }

    session.recognized = registro
    session.state = ChatState.AWAITING_IDENTITY_CONFIRMATION
    session.invalid_attempts = 0
    logger.info("Contato reconhecido — pedindo confirmação de identidade")

    return {
        "response": (
            "Olá! Sou o Diretor Virtual da FASI 🤖\n\n"
            f"Quem está falando é *{_nome_para_exibir(registro['nome'])}*?"
            + CONFIRMACAO_TEXT
        ),
        "options": _confirmacao_options(),
        "ticket_id": None,
        "state": session.state,
        "action": "reconhecimento oferecido",
    }


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

    # ── Comando de eliminação de dados (LGPD), válido em qualquer estado ──────
    if _match_global_command(msg) == "esquecer":
        _desativar_contato(session)
        session.recognized = None
        session.auto_identified = False
        session.matricula = session.nome = session.email = None
        session.state = ChatState.AWAITING_MATRICULA
        session.invalid_attempts = 0
        result["response"] = (
            "🗑️ Pronto! Removi o vínculo deste contato com seus dados — "
            "não vou mais reconhecer você automaticamente.\n\n"
            "Para seguir com o atendimento, diga sua *matrícula*:"
        )
        result["state"] = session.state
        return result

    # ── AWAITING_IDENTITY_CONFIRMATION ────────────────────────────────────────
    # O contato já é conhecido e o bot perguntou "quem está falando é X?".
    # Só um "sim" explícito preenche a identidade — nunca há preenchimento
    # automático silencioso.
    if session.state == ChatState.AWAITING_IDENTITY_CONFIRMATION:
        resposta = _match_sim_nao(msg)

        if resposta == "sim":
            candidato = session.recognized or {}
            session.matricula = candidato.get("matricula")
            session.nome = candidato.get("nome")
            session.email = candidato.get("email")
            session.auto_identified = True
            session.recognized = None
            session.invalid_attempts = 0
            # Atendimento novo ⇒ ticket novo, mesmo gerador do fluxo manual.
            session.ticket_id = _generate_ticket(
                session.matricula, session.nome, session.email
            )
            _registrar_confirmacao(session)
            _espelhar_no_chatwoot(session)
            logger.info(
                "Identidade confirmada pelo aluno — ticket novo %s", session.ticket_id
            )
            # Só o primeiro nome na saudação; matrícula e e-mail não são ecoados.
            return _with_menu(
                session,
                f"✅ *Ticket Registrado: {session.ticket_id}*\n\n"
                f"Que bom te ver de novo, *{session.nome.split()[0]}*! "
                "Já tenho seus dados neste atendimento.",
            )

        if resposta == "nao":
            _desativar_contato(session)
            session.recognized = None
            session.auto_identified = False
            session.invalid_attempts = 0
            session.state = ChatState.AWAITING_MATRICULA
            result["response"] = (
                "Sem problema! Vamos começar do zero.\n\n"
                "Para começar, diga sua *matrícula*:"
            )
            result["state"] = session.state
            return result

        # No-match: repara com limite — nunca um laço infinito.
        session.invalid_attempts += 1
        if session.invalid_attempts >= MAX_INVALID_ATTEMPTS:
            session.recognized = None
            session.invalid_attempts = 0
            session.state = ChatState.AWAITING_MATRICULA
            result["response"] = (
                "Vamos fazer da forma tradicional.\n\n"
                "Para começar, diga sua *matrícula*:"
            )
            result["state"] = session.state
            return result
        result["response"] = (
            f"Não entendi *{msg[:40]}*. Responda *1* para sim ou *2* para não."
            + CONFIRMACAO_TEXT
        )
        result["options"] = _confirmacao_options()
        return result

    # ── AWAITING_MATRICULA ────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_MATRICULA:
        if not _valid_matricula(msg):
            session.invalid_attempts += 1
            result["response"] = (
                "⚠️ Matrícula inválida. Informe os 12 dígitos da matrícula "
                "(ex: *202116040020*). Os 4 primeiros dígitos devem ser o ano de ingresso."
            )
            if session.invalid_attempts >= MAX_INVALID_ATTEMPTS:
                result["response"] += (
                    "\n\n💡 A matrícula está no seu comprovante do SIGAA, "
                    "somente números e sem pontos ou traços."
                )
            return result
        session.matricula = msg.strip()
        session.invalid_attempts = 0
        session.state = ChatState.AWAITING_NOME
        result["response"] = "Diga seu nome completo."
        result["state"] = session.state
        return result

    # ── AWAITING_NOME ─────────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_NOME:
        if not _valid_nome(msg):
            session.invalid_attempts += 1
            result["response"] = (
                "⚠️ Por favor, informe seu *nome completo* (nome e sobrenome). "
                "Ex: *Elton Sarmanho*."
            )
            if session.invalid_attempts >= MAX_INVALID_ATTEMPTS:
                result["response"] += (
                    "\n\n💡 Use o nome como está registrado no SIGAA, "
                    "com pelo menos nome e sobrenome."
                )
            return result
        session.nome = msg.strip()
        session.invalid_attempts = 0
        session.state = ChatState.AWAITING_EMAIL
        result["response"] = "Diga seu e-mail institucional."
        result["state"] = session.state
        return result

    # ── AWAITING_EMAIL ────────────────────────────────────────────────────────
    if session.state == ChatState.AWAITING_EMAIL:
        if not _valid_email(msg):
            session.invalid_attempts += 1
            result["response"] = (
                "⚠️ E-mail inválido. Por favor, informe um e-mail válido "
                "(ex: *nome@ufpa.br*)."
            )
            if session.invalid_attempts >= MAX_INVALID_ATTEMPTS:
                result["response"] += (
                    "\n\n💡 Precisamos de um e-mail válido para enviar a resposta "
                    "do seu atendimento. Pode ser o e-mail institucional ou pessoal."
                )
            return result
        session.email = msg.lower().strip()
        session.invalid_attempts = 0
        ticket = _generate_ticket(session.matricula, session.nome, session.email)
        session.ticket_id = ticket
        session.state = ChatState.MENU
        # É aqui que o diretório se alimenta: o aluno acabou de informar os três
        # dados, então este contato passa a ser reconhecível no próximo contato.
        _registrar_identificacao(session)
        _espelhar_no_chatwoot(session)
        result["ticket_id"] = ticket
        result["response"] = (
            f"✅ *Ticket Registrado: {ticket}*\n\n"
            f"Olá, *{session.nome}*! Sua matrícula *{session.matricula}* foi identificada."
            + MENU_TEXT
        )
        result["options"] = _menu_options()
        result["state"] = session.state
        return result

    # ── MENU ──────────────────────────────────────────────────────────────────
    if session.state == ChatState.MENU:
        first_label = "Fazer outra pergunta" if session.last_question else "Fazer uma pergunta"
        choice = _match_menu_option(msg)

        if choice == "1":
            session.state = ChatState.ASKING_QUESTION
            session.invalid_attempts = 0
            result["response"] = (
                "📚 Qual é sua dúvida? Pode perguntar sobre TCC, ACC, estágio, PPC, "
                "matrículas e normas do curso."
            )
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

        # Pedido genérico de humano: pergunta para qual equipe, em vez de chutar.
        if _match_global_command(msg) == "atendente":
            result["response"] = (
                "Claro! Com quem você prefere falar? Escolha *2* para a Secretaria "
                "ou *3* para a Direção." + MENU_TEXT
            )
            result["options"] = _menu_options(first_label)
            return result

        # Fallback de texto livre: o aluno digitou a dúvida direto no menu.
        if _looks_like_question(msg):
            logger.info("Menu: texto livre reconhecido como pergunta (ticket=%s)", session.ticket_id)
            return _answer_question(session, msg, result)

        # No-match: repara pedindo a opção, sem nunca escalar por engano.
        session.invalid_attempts += 1
        if session.invalid_attempts >= MAX_INVALID_ATTEMPTS:
            result["response"] = (
                f"Ainda não entendi *{msg[:40]}*. Se preferir falar com uma pessoa, "
                "escolha *2* (Secretaria) ou *3* (Direção)." + MENU_TEXT
            )
        else:
            result["response"] = (
                f"Não entendi *{msg[:40]}*. Responda com o número da opção "
                "(1, 2, 3 ou 4) — ou escreva sua dúvida que eu tento responder." + MENU_TEXT
            )
        result["options"] = _menu_options(first_label)
        return result

    # ── ASKING_QUESTION ───────────────────────────────────────────────────────
    if session.state == ChatState.ASKING_QUESTION:
        command = _match_global_command(msg)
        if command == "menu":
            return _with_menu(session, "Sem problema! Voltando ao menu.")
        if command == "encerrar":
            session.state = ChatState.ENDED
            result["response"] = "Obrigado por utilizar o Diretor Virtual da FASI. Até logo! 👋"
            result["state"] = session.state
            return result
        if command == "atendente":
            result.update(_escalate(session, team="secretaria"))
            return result

        return _answer_question(session, msg, result)

    # ── AWAITING_CLARIFICATION ────────────────────────────────────────────────
    # O bot pediu um dado que faltava (hoje: o período letivo). A mensagem aqui
    # é a resposta a esse pedido — NUNCA uma opção de menu.
    if session.state == ChatState.AWAITING_CLARIFICATION:
        command = _match_global_command(msg)
        if command == "menu":
            session.pending_question = None
            session.clarification_attempts = 0
            return _with_menu(session, "Sem problema! Voltando ao menu.", "Fazer outra pergunta")
        if command == "encerrar":
            session.state = ChatState.ENDED
            result["response"] = "Obrigado por utilizar o Diretor Virtual da FASI. Até logo! 👋"
            result["state"] = session.state
            return result
        if command == "atendente":
            session.pending_question = None
            result.update(_escalate(session, team="secretaria"))
            return result

        pending = session.pending_question or msg
        period = _extract_period(msg)
        merged = f"{pending} (período letivo: {period})" if period else f"{pending} {msg}"

        logger.info(
            "Esclarecimento recebido (ticket=%s tentativa=%d periodo=%s)",
            session.ticket_id, session.clarification_attempts, period,
        )

        rag = _call_rag(merged, session_id=session.session_id)

        if rag["needs_clarification"]:
            if session.clarification_attempts < MAX_CLARIFICATION_ATTEMPTS:
                session.clarification_attempts += 1
                result["response"] = (
                    "Ainda não consegui identificar o período letivo. "
                    + rag["answer"]
                    + CLARIFICATION_HINT
                )
                result["state"] = session.state
                return result
            # Esgotou as tentativas: oferece caminho humano em vez de insistir.
            session.pending_question = None
            session.clarification_attempts = 0
            return _with_menu(
                session,
                "Não consegui identificar o período letivo da sua dúvida. "
                "A Secretaria consegue te responder com precisão — escolha a opção *2*.",
                "Fazer outra pergunta",
            )

        session.pending_question = None
        session.clarification_attempts = 0
        return _with_menu(session, rag["answer"], "Fazer outra pergunta")

    # ── ESCALATED / ENDED ─────────────────────────────────────────────────────
    if session.state in (ChatState.ESCALATED, ChatState.ENDED):
        result["response"] = (
            "Sua conversa foi encaminhada. Para iniciar um novo atendimento, recarregue a página."
        )
        return result

    result["response"] = "Estado inválido. Por favor, recarregue a página."
    return result


# ── Pergunta → RAG ────────────────────────────────────────────────────────────

def _answer_question(session: ChatSession, question: str, result: dict) -> dict:
    """
    Envia a pergunta ao RAG e decide o próximo estado.

    Se o RAG pedir um esclarecimento, a conversa entra em AWAITING_CLARIFICATION
    e o menu NÃO é exibido — assim a resposta do aluno ("2026.4") é lida como o
    dado que faltava, e não como a opção "2" do menu.
    """
    session.last_question = question
    rag = _call_rag(question, session_id=session.session_id)

    if rag["needs_clarification"]:
        session.pending_question = question
        session.clarification_attempts = 1
        session.state = ChatState.AWAITING_CLARIFICATION
        logger.info(
            "RAG pediu esclarecimento (ticket=%s): mantendo contexto da pergunta",
            session.ticket_id,
        )
        result["response"] = rag["answer"] + CLARIFICATION_HINT
        result["options"] = None
        result["state"] = session.state
        return result

    return _with_menu(session, rag["answer"], "Fazer outra pergunta")


def _call_rag(question: str, session_id: Optional[str] = None) -> dict:
    """
    Consulta o RAG e devolve {"answer": str, "needs_clarification": bool}.

    O flag `needs_clarification` vem do detector de ambiguidade temporal do
    `rag_ppc` e é o que permite ao fluxo distinguir "resposta" de "pergunta de
    volta" — antes ele era descartado, e o pedido de esclarecimento era tratado
    como resposta final.
    """
    try:
        from backend.infrastructure.rag.rag_ppc import get_service
        service = get_service()
        result = service.ask_question(question, session_id=session_id)
        if result.get("success"):
            return {
                "answer": result["answer"],
                "needs_clarification": bool(result.get("needs_clarification")),
            }
        return {
            "answer": result.get("message") or result.get("error") or "Não foi possível responder.",
            "needs_clarification": False,
        }
    except Exception as exc:
        logger.error("Erro ao chamar RAG: %s", exc)
        return {
            "answer": "⚠️ O assistente de perguntas está temporariamente indisponível. Tente novamente em instantes.",
            "needs_clarification": False,
        }


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
    # Procedência da identificação: o atendente PRECISA saber se a matrícula foi
    # digitada neste atendimento ou herdada de um reconhecimento de contato.
    if session.auto_identified:
        context += "\nIdentificação: automática (contato reconhecido e confirmado pelo aluno)"
    else:
        context += "\nIdentificação: manual (informada neste atendimento)"
    if session.contact_channel == "whatsapp" and session.contact_key:
        from backend.utils.phone import mascarar_telefone
        context += f"\nCanal: WhatsApp ({mascarar_telefone(session.contact_key)})"

    # Handoff com contexto: o atendente já abre a conversa sabendo o que o aluno
    # perguntou ao bot, sem precisar pedir de novo.
    if session.last_question:
        context += f"\nÚltima pergunta ao bot: {session.last_question}"
    if session.pending_question:
        context += "\n⚠️ Pergunta ficou sem resposta (esclarecimento não concluído)."

    try:
        if session.chatwoot_conversation_id:
            # Sessão originada de um webhook do Chatwoot (widget do site ou WhatsApp):
            # já existe uma conversa em andamento — apenas atribui a equipe e
            # avisa nela, em vez de criar uma segunda conversa duplicada.
            from backend.infrastructure.chatwoot.chatwoot_service import assign_team, send_message
            assign_team(session.chatwoot_conversation_id, team_id)
            send_message(session.chatwoot_conversation_id, context, private=True)
            conv_id = session.chatwoot_conversation_id
        else:
            # Sessão originada do endpoint REST genérico (sem conversa Chatwoot prévia):
            # cria contato + conversa novos, como antes.
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
