"""
Alert scheduler service for FasiTech academic alerts.

Manages a background APScheduler that polls the database every minute and
fires alert emails whenever a trigger's scheduled time is reached within its
active date window.
"""
from __future__ import annotations

import atexit
import os
import threading
from datetime import datetime
from typing import List

from backend.utils.datetime_utils import APP_TIMEZONE, now_local

# ---------------------------------------------------------------------------
# Module-level scheduler singleton
# ---------------------------------------------------------------------------
_scheduler = None
_scheduler_lock = threading.Lock()
_TZ = APP_TIMEZONE


def _now_local():
    """Retorna datetime no fuso configurado para os gatilhos."""
    return now_local()


# ---------------------------------------------------------------------------
# Docente email helpers
# ---------------------------------------------------------------------------

def _get_docente_emails() -> List[str]:
    """
    Carrega lista de e-mails dos docentes a partir das settings (env vars).

    Lê de:
    - NOTIFICATION_RECIPIENTS  — CSV de emails
    - PARECERISTAS             — "Nome:email,Nome:email,..." formato
    """
    from backend.config.settings import settings  # noqa: PLC0415

    emails: List[str] = []

    recipients_str = settings.destinatarios or ""
    if recipients_str.strip():
        emails.extend(r.strip() for r in recipients_str.split(",") if r.strip())

    pareceristas_str = settings.pareceristas or ""
    if pareceristas_str:
        for par in pareceristas_str.split(","):
            par = par.strip()
            if ":" in par:
                _, email = par.split(":", 1)
                emails.append(email.strip())

    # Remove duplicatas preservando ordem
    seen: set = set()
    unique: List[str] = []
    for e in emails:
        if e and e not in seen:
            seen.add(e)
            unique.append(e)
    return unique


def _parse_external_emails(raw_emails: str) -> List[str]:
    """
    Converte string de e-mails (separados por ';' ou ',') em lista única.
    """
    if not raw_emails or not raw_emails.strip():
        return []

    normalized = raw_emails.replace(",", ";")
    emails = [email.strip() for email in normalized.split(";") if email.strip()]

    seen: set = set()
    unique: List[str] = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique.append(email)
    return unique


# ---------------------------------------------------------------------------
# Alert dispatch
# ---------------------------------------------------------------------------

def _build_email_body(titulo: str, descricao: str, data_inicio: str,
                      data_fim: str, horario_disparo: str) -> str:
    """Monta o corpo HTML do e-mail de alerta."""
    now_str = _now_local().strftime("%d/%m/%Y %H:%M")
    return (
        f"Olá,\n\n"
        f"Você está recebendo este alerta acadêmico automático da FASI.\n\n"
        f"{'━' * 50}\n"
        f"📢  {titulo}\n"
        f"{'━' * 50}\n\n"
        f"{descricao}\n\n"
        f"{'━' * 50}\n"
        f"📅  Período do alerta : {data_inicio}  →  {data_fim}\n"
        f"🕐  Horário de disparo: {horario_disparo}\n"
        f"📨  Disparado em      : {now_str}\n"
        f"{'━' * 50}\n\n"
        f"Este é um alerta automático do sistema FasiTech.\n\n"
        f"Atenciosamente,\n"
        f"FASI — Faculdade de Sistemas de Informação\n"
    )


def fire_alert(alerta_id: int) -> tuple[bool, str]:
    """
    Dispara manualmente um alerta pelo seu ID.

    Returns:
        (sucesso, mensagem)
    """
    try:
        from backend.infrastructure.database.repository import ensure_alerta_schema_columns  # noqa: PLC0415
        from backend.infrastructure.database.engine import get_db_session  # noqa: PLC0415
        from backend.infrastructure.database.models import AlertaAcademico  # noqa: PLC0415
        from backend.infrastructure.email.service import send_notification  # noqa: PLC0415

        ensure_alerta_schema_columns()

        with get_db_session() as session:
            alerta = session.get(AlertaAcademico, alerta_id)
            if alerta is None:
                return False, "Alerta não encontrado."

            destination_type = (getattr(alerta, "destination_type", None) or "docentes").lower()
            if destination_type == "externos":
                emails = _parse_external_emails(getattr(alerta, "destination_emails", "") or "")
                if not emails:
                    return False, (
                        "Nenhum e-mail externo válido no gatilho. "
                        "Edite e informe e-mails separados por ';'."
                    )
                target_label = "pessoa(s) externa(s)"
            else:
                emails = _get_docente_emails()
                if not emails:
                    return False, (
                        "Nenhum e-mail de docente encontrado. "
                        "Verifique [projetos] no secrets.toml."
                    )
                target_label = "docente(s)"

            subject = f"🔔 Alerta Acadêmico FASI: {alerta.titulo}"
            body = _build_email_body(
                alerta.titulo,
                alerta.descricao,
                alerta.data_inicio,
                alerta.data_fim,
                alerta.horario_disparo,
            )
            send_notification(subject, body, emails)

            # Atualiza registro de último disparo
            alerta.ultimo_disparo = _now_local().strftime("%Y-%m-%d")
            alerta.atualizado_em = datetime.utcnow()
            session.add(alerta)
            session.commit()

        return True, f"Alerta disparado para {len(emails)} {target_label}."

    except Exception as exc:
        return False, f"Erro ao disparar alerta: {exc}"


# ---------------------------------------------------------------------------
# Scheduler job
# ---------------------------------------------------------------------------

def _check_and_fire_alerts() -> None:
    """
    Job executado a cada minuto pelo scheduler.

    Para cada alerta ativo cujo horário bate com o horário atual e a data de
    hoje está dentro do intervalo configurado, dispara o e-mail (uma vez por dia).
    """
    try:
        from backend.infrastructure.database.repository import ensure_alerta_schema_columns  # noqa: PLC0415
        from backend.infrastructure.database.engine import get_db_session  # noqa: PLC0415
        from backend.infrastructure.database.models import AlertaAcademico  # noqa: PLC0415
        from backend.infrastructure.email.service import send_notification  # noqa: PLC0415
        from sqlmodel import select  # noqa: PLC0415

        ensure_alerta_schema_columns()

        now = _now_local()
        today_str = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        with get_db_session() as session:
            alertas = session.exec(
                select(AlertaAcademico).where(AlertaAcademico.ativo == True)  # noqa: E712
            ).all()

            for alerta in alertas:
                # Verifica se hoje está dentro do intervalo de datas
                if not (alerta.data_inicio <= today_str <= alerta.data_fim):
                    continue

                # Verifica se o horário bate (exato no minuto)
                if alerta.horario_disparo != current_time:
                    continue

                # Verifica se já foi disparado hoje
                if alerta.ultimo_disparo == today_str:
                    continue

                destination_type = (getattr(alerta, "destination_type", None) or "docentes").lower()
                if destination_type == "externos":
                    emails = _parse_external_emails(
                        getattr(alerta, "destination_emails", "") or ""
                    )
                    if not emails:
                        print(
                            f"⚠️ Alerta '{alerta.titulo}': "
                            "nenhum e-mail externo válido configurado."
                        )
                        continue
                    target_label = "pessoa(s) externa(s)"
                else:
                    emails = _get_docente_emails()
                    if not emails:
                        print(
                            f"⚠️ Alerta '{alerta.titulo}': "
                            "nenhum e-mail de docente encontrado."
                        )
                        continue
                    target_label = "docente(s)"

                subject = f"🔔 Alerta Acadêmico FASI: {alerta.titulo}"
                body = _build_email_body(
                    alerta.titulo,
                    alerta.descricao,
                    alerta.data_inicio,
                    alerta.data_fim,
                    alerta.horario_disparo,
                )
                send_notification(subject, body, emails)

                alerta.ultimo_disparo = today_str
                alerta.atualizado_em = datetime.utcnow()
                session.add(alerta)
                session.commit()

                print(
                    f"✅ Alerta '{alerta.titulo}' disparado para "
                    f"{len(emails)} {target_label} às {current_time}."
                )

    except Exception as exc:
        print(f"❌ Erro no job de alertas acadêmicos: {exc}")


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def ensure_scheduler_running() -> None:
    """
    Garante que o BackgroundScheduler está em execução (singleton por processo).

    Seguro para ser chamado múltiplas vezes (re-renders do Streamlit) — o
    scheduler só é iniciado uma vez por processo graças ao lock e à flag global.

    Usa trigger ``cron`` (minuto=*) em vez de ``interval`` para garantir que o
    job dispare exatamente no segundo :00 de cada minuto, sem acúmulo de deriva.
    Também executa uma verificação imediata ao iniciar, para não perder alertas
    cujo horário cai dentro do minuto de inicialização do processo.
    """
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            return  # Já rodando

        try:
            from apscheduler.schedulers.background import BackgroundScheduler  # noqa: PLC0415
            from apscheduler.triggers.cron import CronTrigger  # noqa: PLC0415

            _scheduler = BackgroundScheduler(timezone=_TZ)
            _scheduler.add_job(
                _check_and_fire_alerts,
                trigger=CronTrigger(minute="*", timezone=_TZ),
                id="check_academic_alerts",
                replace_existing=True,
                max_instances=1,
                # Tolera até 30s de atraso antes de descartar a execução
                misfire_grace_time=30,
            )
            _scheduler.start()

            # Encerrar graciosamente ao sair
            atexit.register(_shutdown_scheduler)

            print("✅ Scheduler de Alertas Acadêmicos iniciado (cron: todo minuto).")

            # Verificação imediata: captura alertas cujo horário coincide com
            # o minuto em que o processo acabou de subir.
            _check_and_fire_alerts()

        except Exception as exc:
            print(f"❌ Falha ao iniciar scheduler de alertas: {exc}")


def _shutdown_scheduler() -> None:
    """Para o scheduler ao encerrar o processo."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        try:
            _scheduler.shutdown(wait=False)
            print("🛑 Scheduler de Alertas Acadêmicos encerrado.")
        except Exception:
            pass
