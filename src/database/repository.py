"""Database repository functions for saving form submissions."""
from __future__ import annotations

import json
from typing import Any, Dict

from sqlmodel import Session

from src.database.engine import get_db_session
from src.models.db_models import (
    AccSubmission,
    EstagioSubmission,
    PlanoEnsinoSubmission,
    ProjetosSubmission,
    SocialSubmission,
    TccSubmission,
    RequerimentoTccSubmission,
    AvaliacaoGestaoSubmission,
)


def save_tcc_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão de TCC no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = TccSubmission(
        nome=data["name"],
        matricula=data["registration"],
        email=data["email"],
        turma=data["class_group"],
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
    submission = AccSubmission(
        nome=data["name"],
        matricula=data["registration"],
        email=data["email"],
        turma=data["class_group"],
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
    submission = EstagioSubmission(
        nome=data["nome"],
        matricula=data["matricula"],
        email=data["email"],
        turma=data["turma"],
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
