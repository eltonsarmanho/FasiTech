from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.presentation.dependencies import get_admin_dependency

router = APIRouter()


class FuncionarioRequest(BaseModel):
    nome: str
    titulo: str                        # Doutorado | Mestrado | Especialista | Graduação
    tipo: str                          # Interno | Externo
    categoria: str = "Docente"         # Docente | Secretaria | Colaborador
    filiacao: Optional[str] = None
    email: Optional[str] = None
    fone: Optional[str] = None         # WhatsApp
    data_aniversario: Optional[str] = None  # YYYY-MM-DD


class FuncionarioUpdateRequest(BaseModel):
    nome: Optional[str] = None
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    filiacao: Optional[str] = None
    email: Optional[str] = None
    fone: Optional[str] = None
    data_aniversario: Optional[str] = None


@router.get("/funcionarios")
async def list_funcionarios_endpoint(
    tipo: Optional[str] = None, _: str = Depends(get_admin_dependency)
):
    try:
        from backend.infrastructure.database.repository import list_funcionarios
        return list_funcionarios(tipo=tipo)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.post("/funcionarios", status_code=201)
async def create_funcionario(data: FuncionarioRequest, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import save_funcionario
        funcionario_id = save_funcionario(data.model_dump())
        return {"id": funcionario_id, "message": "Funcionário criado com sucesso"}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.put("/funcionarios/{funcionario_id}")
async def update_funcionario_endpoint(
    funcionario_id: int, data: FuncionarioUpdateRequest, _: str = Depends(get_admin_dependency)
):
    try:
        from backend.infrastructure.database.repository import update_funcionario
        updated = update_funcionario(
            funcionario_id, {k: v for k, v in data.model_dump().items() if v is not None}
        )
        if not updated:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Funcionário não encontrado")
        return {"message": "Funcionário atualizado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))


@router.delete("/funcionarios/{funcionario_id}", status_code=204)
async def delete_funcionario_endpoint(funcionario_id: int, _: str = Depends(get_admin_dependency)):
    try:
        from backend.infrastructure.database.repository import delete_funcionario
        deleted = delete_funcionario(funcionario_id)
        if not deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Funcionário não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
