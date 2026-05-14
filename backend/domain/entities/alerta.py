from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class AlertaAcademicoEntity(BaseModel):
    titulo: str
    descricao: str
    data_inicio: str
    data_fim: str
    horario_disparo: str
    destination_type: str = "docentes"
    destination_emails: Optional[str] = None
    ativo: bool = True
