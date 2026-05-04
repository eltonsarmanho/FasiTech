from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo


APP_TIMEZONE = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Belem"))


def now_local() -> datetime:
    """Retorna o horário atual no fuso configurado da aplicação."""
    return datetime.now(APP_TIMEZONE)


def format_local_datetime(fmt: str = "%d/%m/%Y às %H:%M:%S") -> str:
    """Formata o horário atual no fuso configurado da aplicação."""
    return now_local().strftime(fmt)
