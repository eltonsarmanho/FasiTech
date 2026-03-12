"""Database repository functions for saving form submissions."""
from __future__ import annotations

import json
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, text
from sqlmodel import Session, select

from src.database.engine import engine, get_db_session
from src.models.db_models import (
    AccSubmission,
    AlertaAcademico,
    EstagioSubmission,
    PlanoEnsinoSubmission,
    ProjetosSubmission,
    SocialSubmission,
    TccSubmission,
    RequerimentoTccSubmission,
    AvaliacaoGestaoSubmission,
)

_alerta_schema_lock = threading.Lock()
_alerta_schema_ready = False
_forms_schema_lock = threading.Lock()
_forms_schema_ready = False


def _ensure_forms_schema_columns() -> None:
    """Garante colunas de polo/período nas tabelas ACC, TCC e Estágio."""
    global _forms_schema_ready
    with _forms_schema_lock:
        if _forms_schema_ready:
            return

        inspector = inspect(engine)
        table_to_columns = {
            "tcc_submissions": {"polo", "periodo"},
            "acc_submissions": {"polo", "periodo"},
            "estagio_submissions": {"polo", "periodo"},
        }
        existing_tables = set(inspector.get_table_names())

        with engine.begin() as conn:
            for table_name, expected_columns in table_to_columns.items():
                if table_name not in existing_tables:
                    continue

                current_columns = {
                    col["name"] for col in inspector.get_columns(table_name)
                }
                if "polo" not in current_columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            "ADD COLUMN polo VARCHAR(100) DEFAULT ''"
                        )
                    )
                if "periodo" not in current_columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            "ADD COLUMN periodo VARCHAR(20) DEFAULT ''"
                        )
                    )

        _forms_schema_ready = True


def save_tcc_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de TCC no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    _ensure_forms_schema_columns()

    submission = TccSubmission(
        nome=data["name"],
        matricula=data["registration"],
        email=data["email"],
        turma=data["class_group"],
        polo=data.get("polo", ""),
        periodo=data.get("periodo", ""),
        orientador=data["orientador"],
        titulo=data["titulo"],
        componente=data["componente"],
        anexos=data.get("anexos"),
        drive_folder_id=data.get("drive_folder_id"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_acc_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de ACC no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    _ensure_forms_schema_columns()

    submission = AccSubmission(
        nome=data["name"],
        matricula=data["registration"],
        email=data["email"],
        turma=data["class_group"],
        polo=data.get("polo", ""),
        periodo=data.get("periodo", ""),
        semestre=data["semester"],
        arquivo_pdf_link=data.get("file_link"),
        drive_file_id=data.get("drive_file_id"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_projetos_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de Projeto no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = ProjetosSubmission(
        docente=data["docente"],
        parecerista1=data["parecerista1"],
        parecerista2=data["parecerista2"],
        nome_projeto=data["nome_projeto"],
        carga_horaria=data["carga_horaria"],
        edital=data["edital"],
        natureza=data["natureza"],
        ano_edital=data["ano_edital"],
        solicitacao=data["solicitacao"],
        anexos=data.get("anexos"),
        pdf_parecer=data.get("pdf_parecer"),
        pdf_declaracao=data.get("pdf_declaracao"),
        drive_folder_id=data.get("drive_folder_id"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_plano_ensino_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de Plano de Ensino no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = PlanoEnsinoSubmission(
        professor=data["professor"],
        disciplina=data["disciplina"],
        codigo_disciplina=data.get("codigo_disciplina"),
        periodo_letivo=data["periodo_letivo"],
        carga_horaria=data.get("carga_horaria"),
        anexos=data.get("anexos"),
        drive_folder_id=data.get("drive_folder_id"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_estagio_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de Estágio no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    _ensure_forms_schema_columns()

    submission = EstagioSubmission(
        nome=data["nome"],
        matricula=data["matricula"],
        email=data["email"],
        turma=data["turma"],
        polo=data.get("polo", ""),
        periodo=data.get("periodo", ""),
        orientador=data["orientador"],
        titulo=data["titulo"],
        componente=data["componente"],
        anexos=data.get("anexos"),
        drive_folder_id=data.get("drive_folder_id"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_social_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão do formulário Social no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = SocialSubmission(
        matricula=data["matricula"],
        periodo_referencia=data["periodo_referencia"],
        cor_etnia=data.get("cor_etnia"),
        pcd=data.get("pcd"),
        tipo_deficiencia=data.get("tipo_deficiencia"),
        renda=data.get("renda"),
        deslocamento=data.get("deslocamento"),
        trabalho=data.get("trabalho"),
        assistencia_estudantil=data.get("assistencia_estudantil"),
        saude_mental=data.get("saude_mental"),
        estresse=data.get("estresse"),
        acompanhamento=data.get("acompanhamento"),
        escolaridade_pai=data.get("escolaridade_pai"),
        escolaridade_mae=data.get("escolaridade_mae"),
        qtd_computador=data.get("qtd_computador"),
        qtd_celular=data.get("qtd_celular"),
        computador_proprio=data.get("computador_proprio"),
        gasto_internet=data.get("gasto_internet"),
        acesso_internet=data.get("acesso_internet"),
        tipo_moradia=data.get("tipo_moradia"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_requerimento_tcc_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão do Requerimento de TCC (defesa) no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = RequerimentoTccSubmission(
        nome_aluno=data["nome_aluno"],
        matricula=data["matricula"],
        email=data["email"],
        telefone=data.get("telefone"),
        turma=data["turma"],
        orientador=data["orientador"],
        coorientador=data.get("coorientador"),
        titulo_trabalho=data["titulo_trabalho"],
        resumo=data.get("resumo"),
        palavra_chave=data.get("palavra_chave"),
        modalidade=data["modalidade"],
        membro_banca1=data.get("membro_banca1"),
        membro_banca2=data.get("membro_banca2"),
        data_defesa=data.get("data_defesa"),
        horario_defesa=data.get("horario_defesa"),
        local_defesa=data.get("local_defesa"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def save_avaliacao_gestao_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão da Avaliação da Gestão FASI no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = AvaliacaoGestaoSubmission(
        q1_transparencia=data.get("Q1_Transparencia"),
        q1_valor=data.get("Q1_Valor"),
        q2_comunicacao=data.get("Q2_Comunicacao"),
        q2_valor=data.get("Q2_Valor"),
        q3_acessibilidade=data.get("Q3_Acessibilidade"),
        q3_valor=data.get("Q3_Valor"),
        q4_inclusao=data.get("Q4_Inclusao"),
        q4_valor=data.get("Q4_Valor"),
        q5_planejamento=data.get("Q5_Planejamento"),
        q5_valor=data.get("Q5_Valor"),
        q6_recursos=data.get("Q6_Recursos"),
        q6_valor=data.get("Q6_Valor"),
        q7_eficiencia=data.get("Q7_Eficiencia"),
        q7_valor=data.get("Q7_Valor"),
        q8_suporte=data.get("Q8_Suporte"),
        q8_valor=data.get("Q8_Valor"),
        q9_extracurricular=data.get("Q9_Extracurricular"),
        q9_valor=data.get("Q9_Valor"),
        q10_melhorias=data.get("Q10_Melhorias"),
        q11_outras_questoes=data.get("Q11_Outras_Questoes"),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


# ---------------------------------------------------------------------------
# AlertaAcademico CRUD
# ---------------------------------------------------------------------------

def _ensure_alerta_schema_columns() -> None:
    """Garante colunas novas de destino de e-mail na tabela de alertas."""
    global _alerta_schema_ready
    with _alerta_schema_lock:
        if _alerta_schema_ready:
            return

        inspector = inspect(engine)
        if "alertas_academicos" not in inspector.get_table_names():
            return

        columns = {col["name"] for col in inspector.get_columns("alertas_academicos")}

        with engine.begin() as conn:
            if "destination_type" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE alertas_academicos "
                        "ADD COLUMN destination_type VARCHAR(20) DEFAULT 'docentes'"
                    )
                )
            if "destination_emails" not in columns:
                conn.execute(
                    text(
                        "ALTER TABLE alertas_academicos "
                        "ADD COLUMN destination_emails TEXT"
                    )
                )
            conn.execute(
                text(
                    "UPDATE alertas_academicos "
                    "SET destination_type = 'docentes' "
                    "WHERE destination_type IS NULL OR destination_type = ''"
                )
            )

        _alerta_schema_ready = True


def ensure_alerta_schema_columns() -> None:
    """API pública para garantir schema de alertas atualizado."""
    _ensure_alerta_schema_columns()

def create_alerta(data: Dict[str, Any]) -> int:
    """
    Cria um novo gatilho de alerta acadêmico no banco de dados.

    Args:
        data: Dicionário com titulo, descricao, data_inicio, data_fim, horario_disparo.

    Returns:
        ID do alerta criado.
    """
    _ensure_alerta_schema_columns()

    alerta = AlertaAcademico(
        titulo=data["titulo"],
        descricao=data["descricao"],
        data_inicio=data["data_inicio"],
        data_fim=data["data_fim"],
        horario_disparo=data["horario_disparo"],
        destination_type=data.get("destination_type", "docentes"),
        destination_emails=data.get("destination_emails"),
        ativo=data.get("ativo", True),
    )

    with get_db_session() as session:
        session.add(alerta)
        session.commit()
        session.refresh(alerta)
        return alerta.id


def get_all_alertas() -> List[AlertaAcademico]:
    """Retorna todos os gatilhos de alerta acadêmico."""
    _ensure_alerta_schema_columns()
    with get_db_session() as session:
        alertas = session.exec(
            select(AlertaAcademico).order_by(AlertaAcademico.criado_em.desc())
        ).all()
        # Detach objects from session to avoid lazy-load issues
        return [AlertaAcademico(**a.model_dump()) for a in alertas]


def get_alerta_by_id(alerta_id: int) -> Optional[AlertaAcademico]:
    """Retorna um alerta pelo ID."""
    _ensure_alerta_schema_columns()
    with get_db_session() as session:
        alerta = session.get(AlertaAcademico, alerta_id)
        if alerta is None:
            return None
        return AlertaAcademico(**alerta.model_dump())


def update_alerta(alerta_id: int, data: Dict[str, Any]) -> bool:
    """
    Atualiza um gatilho de alerta acadêmico.

    Args:
        alerta_id: ID do alerta.
        data: Campos a atualizar.

    Returns:
        True se atualizado com sucesso, False caso não encontrado.
    """
    _ensure_alerta_schema_columns()
    with get_db_session() as session:
        alerta = session.get(AlertaAcademico, alerta_id)
        if alerta is None:
            return False
        for field, value in data.items():
            if hasattr(alerta, field) and value is not None:
                setattr(alerta, field, value)
        alerta.atualizado_em = datetime.utcnow()
        session.add(alerta)
        session.commit()
        return True


def delete_alerta(alerta_id: int) -> bool:
    """
    Remove um gatilho de alerta acadêmico.

    Returns:
        True se removido, False caso não encontrado.
    """
    _ensure_alerta_schema_columns()
    with get_db_session() as session:
        alerta = session.get(AlertaAcademico, alerta_id)
        if alerta is None:
            return False
        session.delete(alerta)
        session.commit()
        return True
