"""Database repository functions for saving form submissions."""
from __future__ import annotations

import json
import threading
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import inspect, text
from sqlmodel import Session, select

from backend.infrastructure.database.engine import engine, get_db_session
from backend.infrastructure.database.models import (
    AccSubmission,
    AlertaAcademico,
    CcfSubmission,
    EstagioSubmission,
    PlanoEnsinoSubmission,
    PeriodoSubmissao,
    ProjetosSubmission,
    SocialSubmission,
    TccSubmission,
    RequerimentoTccSubmission,
    AvaliacaoGestaoSubmission,
    LancamentoConceito,
    Funcionario,
)

_alerta_schema_lock = threading.Lock()
_alerta_schema_ready = False
_forms_schema_lock = threading.Lock()
_forms_schema_ready = False
_social_schema_lock = threading.Lock()
_social_schema_ready = False
_req_tcc_schema_lock = threading.Lock()
_req_tcc_schema_ready = False


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


def _ensure_requerimento_tcc_schema_columns() -> None:
    """Garante que todas as colunas adicionadas após a criação inicial da tabela existam."""
    global _req_tcc_schema_ready
    with _req_tcc_schema_lock:
        if _req_tcc_schema_ready:
            return
        inspector = inspect(engine)
        if "requerimento_tcc_submissions" in set(inspector.get_table_names()):
            current = {c["name"] for c in inspector.get_columns("requerimento_tcc_submissions")}
            alterations = [
                ("membro_banca3",  "VARCHAR(255)"),
                ("data_defesa",    "VARCHAR(50)"),
                ("horario_defesa", "VARCHAR(50)"),
                ("local_defesa",   "VARCHAR(255)"),
            ]
            with engine.begin() as conn:
                for col, col_type in alterations:
                    if col not in current:
                        conn.execute(text(
                            f"ALTER TABLE requerimento_tcc_submissions "
                            f"ADD COLUMN {col} {col_type}"
                        ))
        _req_tcc_schema_ready = True


def _ensure_social_schema_columns() -> None:
    global _social_schema_ready
    with _social_schema_lock:
        if _social_schema_ready:
            return

        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        if "social_submissions" not in existing_tables:
            _social_schema_ready = True
            return

        current_columns = {
            col["name"] for col in inspector.get_columns("social_submissions")
        }

        with engine.begin() as conn:
            if "genero" not in current_columns:
                conn.execute(
                    text(
                        "ALTER TABLE social_submissions "
                        "ADD COLUMN genero VARCHAR(50)"
                    )
                )
            if "polo" not in current_columns:
                conn.execute(
                    text(
                        "ALTER TABLE social_submissions "
                        "ADD COLUMN polo VARCHAR(100)"
                    )
                )

        _social_schema_ready = True


def save_tcc_submission(data: Dict[str, Any]) -> int:
    """Upsert de submissão TCC — atualiza se já existe (matricula+componente+polo+periodo)."""
    _ensure_forms_schema_columns()
    with get_db_session() as session:
        existing = session.exec(
            select(TccSubmission).where(
                TccSubmission.matricula == data["registration"],
                TccSubmission.componente == data["componente"],
                TccSubmission.polo == data.get("polo", ""),
                TccSubmission.periodo == data.get("periodo", ""),
            )
        ).first()
        if existing:
            existing.nome = data["name"]
            existing.email = data["email"]
            existing.turma = data["class_group"]
            existing.orientador = data["orientador"]
            existing.titulo = data["titulo"]
            if data.get("anexos"):
                existing.anexos = data["anexos"]
            if data.get("drive_folder_id"):
                existing.drive_folder_id = data["drive_folder_id"]
            session.add(existing)
            session.commit()
            return existing.id
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
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def acc_already_submitted(matricula: str, polo: str, periodo: str) -> bool:
    """Retorna True se o aluno já enviou ACC para este polo+periodo."""
    _ensure_forms_schema_columns()
    with get_db_session() as session:
        return session.exec(
            select(AccSubmission).where(
                AccSubmission.matricula == matricula,
                AccSubmission.polo == polo,
                AccSubmission.periodo == periodo,
            )
        ).first() is not None


def save_acc_submission(data: Dict[str, Any]) -> int:
    """Salva nova submissão ACC. Levanta ValueError se já existir envio para matricula+polo+periodo."""
    _ensure_forms_schema_columns()
    with get_db_session() as session:
        existing = session.exec(
            select(AccSubmission).where(
                AccSubmission.matricula == data["registration"],
                AccSubmission.polo == data.get("polo", ""),
                AccSubmission.periodo == data.get("periodo", ""),
            )
        ).first()
        if existing:
            raise ValueError(
                f"Você já enviou sua ACC para o período {data.get('periodo', '')}. "
                "Não é permitido um segundo envio."
            )
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
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def ccf_already_submitted(matricula: str, polo: str, periodo: str) -> bool:
    """Retorna True se o aluno já enviou CCF para este polo+periodo."""
    with get_db_session() as session:
        return session.exec(
            select(CcfSubmission).where(
                CcfSubmission.matricula == matricula,
                CcfSubmission.polo == polo,
                CcfSubmission.periodo == periodo,
            )
        ).first() is not None


def save_ccf_submission(data: Dict[str, Any]) -> int:
    """Salva nova submissão CCF (PDF gravado em bytea). Levanta ValueError se já existir envio para matricula+polo+periodo."""
    with get_db_session() as session:
        existing = session.exec(
            select(CcfSubmission).where(
                CcfSubmission.matricula == data["registration"],
                CcfSubmission.polo == data.get("polo", ""),
                CcfSubmission.periodo == data.get("periodo", ""),
            )
        ).first()
        if existing:
            raise ValueError(
                f"Você já enviou seu CCF para o período {data.get('periodo', '')}. "
                "Não é permitido um segundo envio."
            )
        submission = CcfSubmission(
            nome=data["name"],
            matricula=data["registration"],
            email=data["email"],
            turma=data["class_group"],
            polo=data.get("polo", ""),
            periodo=data.get("periodo", ""),
            disciplinas=data.get("disciplinas"),
            arquivo_pdf=data["file_bytes"],
            arquivo_nome=data.get("file_name") or "ccf.pdf",
        )
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def update_ccf_resultado(submission_id: int, resumo_texto: str, disciplinas_resultado_json: Optional[str]) -> None:
    """Atualiza o resultado da conferência de disciplinas (extraído pela IA em background)."""
    with get_db_session() as session:
        submission = session.get(CcfSubmission, submission_id)
        if submission is None:
            return
        submission.carga_horaria_total = resumo_texto
        submission.disciplinas_resultado = disciplinas_resultado_json
        session.add(submission)
        session.commit()


def get_ccf_pdf(submission_id: int) -> Optional[tuple[bytes, str]]:
    """Retorna (bytes do PDF, nome do arquivo) de uma submissão CCF."""
    with get_db_session() as session:
        submission = session.get(CcfSubmission, submission_id)
        if submission is None:
            return None
        return submission.arquivo_pdf, submission.arquivo_nome


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


def update_projeto_status(projeto_id: int, novo_status: str) -> bool:
    with get_db_session() as session:
        stmt = select(ProjetosSubmission).where(ProjetosSubmission.id == projeto_id)
        projeto = session.exec(stmt).first()
        if projeto is None:
            return False
        projeto.status = novo_status
        session.add(projeto)
        session.commit()
        return True


def delete_projeto(projeto_id: int) -> bool:
    with get_db_session() as session:
        projeto = session.get(ProjetosSubmission, projeto_id)
        if projeto is None:
            return False
        session.delete(projeto)
        session.commit()
        return True


def list_projetos_submissions(
    pagina: int = 1,
    por_pagina: int = 20,
    natureza: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    with get_db_session() as session:
        query = select(ProjetosSubmission)
        if natureza:
            query = query.where(ProjetosSubmission.natureza == natureza)
        if status:
            query = query.where(ProjetosSubmission.status == status)
        query = query.order_by(ProjetosSubmission.submission_date.desc())

        total = len(session.exec(query).all())
        offset = (pagina - 1) * por_pagina
        rows = session.exec(query.offset(offset).limit(por_pagina)).all()

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "items": [
                {
                    "id": r.id,
                    "docente": r.docente,
                    "nome_projeto": r.nome_projeto,
                    "natureza": r.natureza,
                    "edital": r.edital,
                    "ano_edital": r.ano_edital,
                    "solicitacao": r.solicitacao,
                    "carga_horaria": r.carga_horaria,
                    "parecerista1": r.parecerista1,
                    "parecerista2": r.parecerista2,
                    "status": r.status,
                    "submission_date": r.submission_date.isoformat() if r.submission_date else None,
                    "pdf_parecer": r.pdf_parecer,
                    "pdf_declaracao": r.pdf_declaracao,
                }
                for r in rows
            ],
        }


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
    """Upsert de submissão Estágio — atualiza se já existe (matricula+componente+polo+periodo)."""
    _ensure_forms_schema_columns()
    with get_db_session() as session:
        existing = session.exec(
            select(EstagioSubmission).where(
                EstagioSubmission.matricula == data["matricula"],
                EstagioSubmission.componente == data["componente"],
                EstagioSubmission.polo == data.get("polo", ""),
                EstagioSubmission.periodo == data.get("periodo", ""),
            )
        ).first()
        if existing:
            existing.nome = data["nome"]
            existing.email = data["email"]
            existing.turma = data["turma"]
            existing.orientador = data["orientador"]
            existing.titulo = data["titulo"]
            if data.get("anexos"):
                existing.anexos = data["anexos"]
            if data.get("drive_folder_id"):
                existing.drive_folder_id = data["drive_folder_id"]
            session.add(existing)
            session.commit()
            return existing.id
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
    _ensure_social_schema_columns()

    submission = SocialSubmission(
        matricula=data["matricula"],
        periodo_referencia=data["periodo_referencia"],
        genero=data.get("genero"),
        polo=data.get("polo"),
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


def _parse_horario_minutos(horario: str) -> Optional[int]:
    """Parse 'HH:MM' ou 'HHhMM' para minutos desde meia-noite. None se inválido."""
    import re
    if not horario:
        return None
    m = re.match(r'^(\d{1,2})[h:](\d{0,2})$', horario.strip())
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    return None


def _banca_members_from_dict(data: dict) -> set:
    """Retorna set normalizado dos membros de banca a partir de um dicionário de submissão."""
    fields = ['orientador', 'membro_banca1', 'membro_banca2', 'membro_banca3']
    return {v.strip().lower() for k in fields if (v := data.get(k))}


def _banca_members_from_row(row) -> set:
    """Retorna set normalizado dos membros de banca a partir de um objeto do DB."""
    fields = [row.orientador, row.membro_banca1, row.membro_banca2, row.membro_banca3]
    return {v.strip().lower() for v in fields if v}


def check_tcc_scheduling_conflicts(
    data: Dict[str, Any],
    exclude_matricula: Optional[str] = None,
    exclude_submission_id: Optional[int] = None,
) -> List[str]:
    """
    Verifica conflitos de agenda para defesas de TCC.
    Retorna lista de mensagens de conflito (vazia = sem conflito).

    Política 1: mesmo dia/horário com membro(s) em comum → conflito de slot.
                Grupos completamente diferentes no mesmo slot são permitidos.
    Política 2: membro em outra banca no mesmo dia com diferença < 60 min → conflito de disponibilidade.
    """
    _ensure_requerimento_tcc_schema_columns()
    conflicts: List[str] = []
    data_defesa = data.get("data_defesa")
    horario = data.get("horario_defesa")
    if not data_defesa or not horario:
        return conflicts

    new_min = _parse_horario_minutos(horario)
    new_members = _banca_members_from_dict(data)
    new_titulo = (data.get("titulo_trabalho") or "").strip().lower()

    with get_db_session() as session:
        query = select(RequerimentoTccSubmission).where(
            RequerimentoTccSubmission.data_defesa == data_defesa
        )
        if exclude_submission_id is not None:
            query = query.where(RequerimentoTccSubmission.id != exclude_submission_id)
        if exclude_matricula:
            query = query.where(RequerimentoTccSubmission.matricula != exclude_matricula)
        existing = session.exec(query).all()

        for row in existing:
            ex_members = _banca_members_from_row(row)
            ex_titulo = (row.titulo_trabalho or "").strip().lower()
            ex_min = _parse_horario_minutos(row.horario_defesa or "")
            same_slot = row.horario_defesa == horario

            if same_slot:
                is_dupla = (
                    bool(new_titulo)  # título não pode ser vazio — evita falso positivo
                    and new_titulo == ex_titulo
                    and new_members == ex_members
                    and len(new_members) > 0
                )
                if not is_dupla:
                    overlap = new_members & ex_members
                    if overlap:
                        nomes = ", ".join(sorted(overlap))
                        conflicts.append(
                            f"Conflito no mesmo horário ({data_defesa} às {horario}): "
                            f"o(s) membro(s) '{nomes}' já fazem parte da banca do aluno "
                            f"{row.nome_aluno}. Se você é parceiro(a) neste TCC, "
                            f"use exatamente o mesmo título e os mesmos membros da banca."
                        )
            elif new_min is not None and ex_min is not None:
                if abs(new_min - ex_min) < 60:
                    overlap = new_members & ex_members
                    if overlap:
                        nomes = ", ".join(sorted(overlap))
                        conflicts.append(
                            f"O(s) membro(s) '{nomes}' já estão em outra banca às "
                            f"{row.horario_defesa} em {data_defesa}. "
                            f"O intervalo mínimo entre bancas é de 1 hora."
                        )
    return conflicts


def _serialize_requerimento_tcc_submission(row: RequerimentoTccSubmission) -> Dict[str, Any]:
    return {
        "id": row.id,
        "nome_aluno": row.nome_aluno,
        "matricula": row.matricula,
        "email": row.email,
        "telefone": row.telefone,
        "turma": row.turma,
        "orientador": row.orientador,
        "coorientador": row.coorientador,
        "titulo_trabalho": row.titulo_trabalho,
        "resumo": row.resumo,
        "palavra_chave": row.palavra_chave,
        "modalidade": row.modalidade,
        "membro_banca1": row.membro_banca1,
        "membro_banca2": row.membro_banca2,
        "membro_banca3": getattr(row, "membro_banca3", None),
        "data_defesa": row.data_defesa,
        "horario_defesa": row.horario_defesa,
        "local_defesa": row.local_defesa,
        "status": row.status,
        "submission_date": row.submission_date.isoformat() if row.submission_date else None,
    }


def save_requerimento_tcc_submission(data: Dict[str, Any]) -> tuple[int, bool]:
    """Salva ou atualiza submissão do Requerimento de TCC (upsert por matricula).
    
    Retorna (id, is_new) onde is_new=True indica criação, False indica atualização.
    """
    _ensure_requerimento_tcc_schema_columns()

    fields = dict(
        nome_aluno=data["nome_aluno"],
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
        membro_banca3=data.get("membro_banca3"),
        data_defesa=data.get("data_defesa"),
        horario_defesa=data.get("horario_defesa"),
        local_defesa=data.get("local_defesa"),
    )

    with get_db_session() as session:
        existing = session.exec(
            select(RequerimentoTccSubmission).where(
                RequerimentoTccSubmission.matricula == data["matricula"]
            )
        ).first()

        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing.id, False

        submission = RequerimentoTccSubmission(matricula=data["matricula"], **fields)
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id, True


def update_requerimento_tcc_submission(submission_id: int, data: Dict[str, Any]) -> Optional[int]:
    """Atualiza uma submissão do Requerimento de TCC pelo ID."""
    _ensure_requerimento_tcc_schema_columns()

    fields = dict(
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
        membro_banca3=data.get("membro_banca3"),
        data_defesa=data.get("data_defesa"),
        horario_defesa=data.get("horario_defesa"),
        local_defesa=data.get("local_defesa"),
    )

    with get_db_session() as session:
        submission = session.get(RequerimentoTccSubmission, submission_id)
        if submission is None:
            return None

        duplicate = session.exec(
            select(RequerimentoTccSubmission).where(
                RequerimentoTccSubmission.matricula == data["matricula"],
                RequerimentoTccSubmission.id != submission_id,
            )
        ).first()
        if duplicate:
            raise ValueError("Já existe outro requerimento cadastrado com esta matrícula.")

        for key, value in fields.items():
            setattr(submission, key, value)
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


def get_requerimento_tcc_submission(submission_id: int) -> Optional[Dict[str, Any]]:
    """Retorna uma submissão do Requerimento TCC por ID."""
    _ensure_requerimento_tcc_schema_columns()
    with get_db_session() as session:
        row = session.get(RequerimentoTccSubmission, submission_id)
        if row is None:
            return None
        return _serialize_requerimento_tcc_submission(row)


def list_requerimento_tcc_submissions(
    pagina: int = 1,
    por_pagina: int = 20,
    turma: Optional[str] = None,
) -> Dict[str, Any]:
    _ensure_requerimento_tcc_schema_columns()
    with get_db_session() as session:
        query = select(RequerimentoTccSubmission)
        if turma:
            query = query.where(RequerimentoTccSubmission.turma == turma)
        query = query.order_by(RequerimentoTccSubmission.submission_date.desc())

        total = len(session.exec(query).all())
        offset = (pagina - 1) * por_pagina
        rows = session.exec(query.offset(offset).limit(por_pagina)).all()

        return {
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "items": [_serialize_requerimento_tcc_submission(r) for r in rows],
        }


def delete_requerimento_tcc_submission(submission_id: int) -> bool:
    with get_db_session() as session:
        row = session.exec(
            select(RequerimentoTccSubmission).where(RequerimentoTccSubmission.id == submission_id)
        ).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def get_requerimento_tcc_drive_info(submission_id: int) -> Optional[Dict[str, Any]]:
    """Retorna informações da pasta no Drive associada ao requerimento de TCC."""
    with get_db_session() as session:
        row = session.exec(
            select(RequerimentoTccSubmission).where(RequerimentoTccSubmission.id == submission_id)
        ).first()
        if not row:
            return None
        tcc = session.exec(
            select(TccSubmission).where(TccSubmission.matricula == row.matricula)
        ).first()
        if not tcc:
            return None
        from backend.infrastructure.google.drive import get_tcc_folder_root_id
        root_id = get_tcc_folder_root_id()
        return {
            "type": "folder",
            "root": root_id,
            "path": [tcc.componente, tcc.turma, tcc.nome],
        }


def save_avaliacao_gestao_submission(data: Dict[str, Any]) -> int:
    """
    Salva submissão da Avaliação da Gestão FASI no banco de dados.
    
    Args:
        data: Dicionário com dados do formulário
        
    Returns:
        ID da submissão criada
    """
    submission = AvaliacaoGestaoSubmission(
        periodo=data.get("Periodo"),
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
        q12_fasitech_impacto=data.get("Q12_Fasitech_Impacto"),
        q12_valor=data.get("Q12_Valor"),
        q13_fasitech_funcionalidades=(
            json.dumps(data["Q13_Fasitech_Funcionalidades"], ensure_ascii=False)
            if data.get("Q13_Fasitech_Funcionalidades") is not None
            else None
        ),
    )
    
    with get_db_session() as session:
        session.add(submission)
        session.commit()
        session.refresh(submission)
        return submission.id


_ESCALA_PARA_VALOR: Dict[str, int] = {
    # Satisfação
    "muito insatisfeito": 1,
    "insatisfeito": 2,
    "neutro": 3,
    "satisfeito": 4,
    "muito satisfeito": 5,
    # Concordância
    "discordo totalmente": 1,
    "discordo": 2,
    "concordo": 4,
    "concordo totalmente": 5,
}


def _text_to_valor(text: Optional[str], stored_valor: Optional[int]) -> Optional[int]:
    """Retorna o valor numérico armazenado; se NULL, deriva do texto da resposta."""
    if stored_valor is not None:
        return stored_valor
    if not text:
        return None
    return _ESCALA_PARA_VALOR.get(text.strip().lower())


def list_avaliacao_gestao_submissions(
    pagina: int = 1,
    por_pagina: int = 500,
    periodo: Optional[str] = None,
) -> Dict[str, Any]:
    """Retorna submissões da Avaliação da Gestão FASI (dados objetivos apenas)."""
    from sqlalchemy import func

    with get_db_session() as session:
        stmt = select(AvaliacaoGestaoSubmission)
        if periodo:
            stmt = stmt.where(AvaliacaoGestaoSubmission.periodo == periodo)
        stmt = stmt.order_by(AvaliacaoGestaoSubmission.id.desc())

        total: int = session.exec(
            select(func.count()).select_from(stmt.subquery())
        ).one()

        offset = (pagina - 1) * por_pagina
        rows = session.exec(stmt.offset(offset).limit(por_pagina)).all()

        items = []
        for r in rows:
            funcionalidades = []
            if r.q13_fasitech_funcionalidades:
                try:
                    funcionalidades = json.loads(r.q13_fasitech_funcionalidades)
                except (json.JSONDecodeError, TypeError):
                    funcionalidades = []
            items.append({
                "id": r.id,
                "periodo": r.periodo,
                "q1_valor":  _text_to_valor(r.q1_transparencia,   r.q1_valor),
                "q2_valor":  _text_to_valor(r.q2_comunicacao,     r.q2_valor),
                "q3_valor":  _text_to_valor(r.q3_acessibilidade,  r.q3_valor),
                "q4_valor":  _text_to_valor(r.q4_inclusao,        r.q4_valor),
                "q5_valor":  _text_to_valor(r.q5_planejamento,    r.q5_valor),
                "q6_valor":  _text_to_valor(r.q6_recursos,        r.q6_valor),
                "q7_valor":  _text_to_valor(r.q7_eficiencia,      r.q7_valor),
                "q8_valor":  _text_to_valor(r.q8_suporte,         r.q8_valor),
                "q9_valor":  _text_to_valor(r.q9_extracurricular, r.q9_valor),
                "q12_valor": _text_to_valor(r.q12_fasitech_impacto, r.q12_valor),
                "q13_fasitech_funcionalidades": funcionalidades,
                "submission_date": r.submission_date.isoformat() if r.submission_date else None,
            })

        return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "items": items}


# ---------------------------------------------------------------------------
# Consulta de Lançamento de Conceitos
# ---------------------------------------------------------------------------

def _normalize_text(value: Any) -> str:
    """Normaliza texto para comparações simples."""
    if value is None:
        return ""
    return str(value).strip()


def _normalize_for_compare(value: Any) -> str:
    """Normaliza texto para comparação case/acento-insensitive."""
    normalized = unicodedata.normalize("NFKD", _normalize_text(value))
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def _matches_filter(value: Any, selected: Optional[str]) -> bool:
    """Valida se um valor atende ao filtro selecionado."""
    selected_text = _normalize_text(selected)
    if not selected_text or selected_text.lower() == "todos":
        return True
    return _normalize_for_compare(value) == _normalize_for_compare(selected_text)


def _is_tcc1_submission(component_value: Any) -> bool:
    """Retorna True se o componente corresponde ao TCC 1."""
    component_text = _normalize_for_compare(component_value)
    return component_text in {"tcc 1", "tcc1"}


def _normalize_estagio_component(component_value: Any) -> str:
    """Padroniza componente de estágio para labels exibidos na UI."""
    component_text = _normalize_text(component_value)
    lowered = _normalize_for_compare(component_text)

    if lowered.startswith("plano de estagio"):
        return "Plano de Estágio (Estágio I)"
    if lowered.startswith("relatorio final"):
        return "Relatório Final (Estágio II)"
    return component_text


def _lancamento_key(row: Dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        _normalize_text(row.get("matricula")),
        _normalize_text(row.get("periodo")),
        _normalize_text(row.get("polo")),
        _normalize_text(row.get("componente")),
    )


def _deduplicate_lancamento_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicados com base em matrícula, período, polo e componente."""
    unique_map: Dict[tuple[str, str, str, str], Dict[str, Any]] = {}
    for row in rows:
        key = _lancamento_key(row)
        if not all(key):
            continue
        if key not in unique_map:
            unique_map[key] = row
    return list(unique_map.values())


def _sync_lancamento_conceitos(
    session: Session,
    source_rows: List[Dict[str, Any]],
) -> Dict[tuple[str, str, str, str], LancamentoConceito]:
    """Sincroniza dados-base na tabela lancamento_conceitos."""
    keys = {_lancamento_key(row) for row in source_rows if all(_lancamento_key(row))}
    if not keys:
        return {}

    componentes = sorted({key[3] for key in keys})
    existing_records = session.exec(
        select(LancamentoConceito).where(LancamentoConceito.componente.in_(componentes))
    ).all()

    existing_map: Dict[tuple[str, str, str, str], LancamentoConceito] = {
        (
            _normalize_text(item.matricula),
            _normalize_text(item.periodo),
            _normalize_text(item.polo),
            _normalize_text(item.componente),
        ): item
        for item in existing_records
    }

    created = False
    for row in source_rows:
        key = _lancamento_key(row)
        if not all(key) or key in existing_map:
            continue

        new_row = LancamentoConceito(
            matricula=key[0],
            periodo=key[1],
            polo=key[2],
            componente=key[3],
            matriculado=False,
            consolidado=False,
        )
        session.add(new_row)
        existing_map[key] = new_row
        created = True

    if created:
        session.commit()
        for value in existing_map.values():
            session.refresh(value)

    return existing_map


def get_lancamento_conceitos(
    tipo_formulario: str,
    turma: Optional[str] = None,
    polo: Optional[str] = None,
    periodo: Optional[str] = None,
    componente_estagio: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retorna dados para Lançamento de Conceitos com filtros aplicados.

    Regras:
    - TCC: retorna apenas submissões de componente TCC 1.
    - Estágio: pode filtrar por componente (Plano de Estágio ou Relatório Final).
    """
    tipo = _normalize_text(tipo_formulario).upper()
    if not tipo:
        return []

    with get_db_session() as session:
        if tipo == "ACC":
            registros = session.exec(select(AccSubmission)).all()
            source_rows = [
                {
                    "tipo_formulario": "ACC",
                    "matricula": _normalize_text(item.matricula),
                    "turma": _normalize_text(item.turma),
                    "polo": _normalize_text(item.polo),
                    "periodo": _normalize_text(item.periodo),
                    "componente": "ACC",
                }
                for item in registros
            ]
        elif tipo == "TCC":
            registros = session.exec(select(TccSubmission)).all()
            source_rows = [
                {
                    "tipo_formulario": "TCC",
                    "matricula": _normalize_text(item.matricula),
                    "turma": _normalize_text(item.turma),
                    "polo": _normalize_text(item.polo),
                    "periodo": _normalize_text(item.periodo),
                    "orientador": _normalize_text(item.orientador),
                    "componente": "TCC 1",
                }
                for item in registros
                if _is_tcc1_submission(item.componente)
            ]
        elif tipo in {"ESTAGIO", "ESTÁGIO"}:
            registros = session.exec(select(EstagioSubmission)).all()
            source_rows = []
            for item in registros:
                componente_label = _normalize_estagio_component(item.componente)
                if not _matches_filter(componente_label, componente_estagio):
                    continue
                source_rows.append(
                    {
                        "tipo_formulario": "ESTAGIO",
                        "matricula": _normalize_text(item.matricula),
                        "turma": _normalize_text(item.turma),
                        "polo": _normalize_text(item.polo),
                        "periodo": _normalize_text(item.periodo),
                        "componente": componente_label,
                    }
                )
        elif tipo == "CCF":
            registros = session.exec(select(CcfSubmission)).all()
            source_rows = [
                {
                    "tipo_formulario": "CCF",
                    "matricula": _normalize_text(item.matricula),
                    "turma": _normalize_text(item.turma),
                    "polo": _normalize_text(item.polo),
                    "periodo": _normalize_text(item.periodo),
                    "componente": "CCF",
                    "submissao_id": item.id,
                }
                for item in registros
            ]
        else:
            return []

        source_rows = _deduplicate_lancamento_rows(source_rows)
        lancamentos_map = _sync_lancamento_conceitos(session, source_rows)

    filtered_rows = [
        row
        for row in source_rows
        if _matches_filter(row.get("turma"), turma)
        and _matches_filter(row.get("polo"), polo)
        and _matches_filter(row.get("periodo"), periodo)
    ]

    rows_with_status: List[Dict[str, Any]] = []
    for row in filtered_rows:
        entry = lancamentos_map.get(_lancamento_key(row))
        rows_with_status.append(
            {
                **row,
                "id": getattr(entry, "id", None),
                "matriculado": bool(getattr(entry, "matriculado", False)),
                "consolidado": bool(getattr(entry, "consolidado", False)),
            }
        )

    return sorted(
        rows_with_status,
        key=lambda row: (
            row.get("periodo", ""),
            row.get("polo", ""),
            row.get("matricula", ""),
        ),
    )


def update_lancamento_conceitos_status(
    updates: List[Dict[str, Any]],
) -> tuple[int, int]:
    """
    Atualiza status de matrícula/consolidação em lancamento_conceitos.

    Args:
        updates: lista com itens no formato:
            {"id": int, "matriculado": bool, "consolidado": bool}

    Returns:
        (atualizados, ignorados)
    """
    if not updates:
        return 0, 0

    updated_count = 0
    ignored_count = 0

    with get_db_session() as session:
        for item in updates:
            item_id = item.get("id")
            if not item_id:
                ignored_count += 1
                continue

            registro = session.get(LancamentoConceito, int(item_id))
            if registro is None:
                ignored_count += 1
                continue

            registro.matriculado = bool(item.get("matriculado", False))
            registro.consolidado = bool(item.get("consolidado", False))
            session.add(registro)
            updated_count += 1

        session.commit()

    return updated_count, ignored_count


def atualizar_status_lancamento(
    matricula: str,
    periodo: str,
    polo: str,
    componente: str,
    matriculado: Optional[bool] = None,
    consolidado: Optional[bool] = None,
) -> Optional[LancamentoConceito]:
    """
    Atualiza manualmente o status de matriculado e/ou consolidado para um lançamento específico.

    Args:
        matricula: Matrícula do aluno
        periodo: Período acadêmico (ex: "2026.1")
        polo: Nome do polo
        componente: Componente (ACC I, TCC I, etc.)
        matriculado: Novo status de matriculado (opcional)
        consolidado: Novo status de consolidado (opcional)

    Returns:
        LancamentoConceito atualizado ou None se não encontrado
    """
    with get_db_session() as session:
        stmt = select(LancamentoConceito).where(
            LancamentoConceito.matricula == matricula,
            LancamentoConceito.periodo == periodo,
            LancamentoConceito.polo == polo,
            LancamentoConceito.componente == componente,
        )
        registro = session.exec(stmt).first()

        if registro is None:
            return None

        if matriculado is not None:
            registro.matriculado = matriculado
        if consolidado is not None:
            registro.consolidado = consolidado

        session.add(registro)
        session.commit()
        session.refresh(registro)

    return registro


def delete_lancamento_conceitos(ids: List[int]) -> tuple[int, int]:
    """
    Remove registros de lancamento_conceitos pelos IDs.

    Returns:
        (removidos, ignorados)
    """
    if not ids:
        return 0, 0

    deleted_count = 0
    ignored_count = 0

    with get_db_session() as session:
        for item_id in ids:
            registro = session.get(LancamentoConceito, int(item_id))
            if registro is None:
                ignored_count += 1
                continue
            session.delete(registro)
            deleted_count += 1

        session.commit()

    return deleted_count, ignored_count


def get_lancamento_source_drive_info(
    tipo_formulario: str,
    matricula: str,
    periodo: str,
    polo: str,
    componente: str,
) -> Optional[Dict[str, Any]]:
    """Retorna info de Drive da submissão-fonte sem deletar nada.

    Retorno:
        {"type": "folder", "root": str, "path": [str, ...]}  para TCC/Estágio
        {"type": "file",   "item_id": str}                   para ACC
        None se não encontrado
    """
    tipo = _normalize_text(tipo_formulario).upper()
    mat = _normalize_text(matricula)
    per = _normalize_text(periodo)
    pol = _normalize_text(polo)
    comp = _normalize_text(componente)

    with get_db_session() as session:
        if tipo == "ACC":
            source = session.exec(
                select(AccSubmission).where(
                    AccSubmission.matricula == mat,
                    AccSubmission.periodo == per,
                    AccSubmission.polo == pol,
                )
            ).first()
            if source:
                from backend.config.settings import settings as _settings
                root = _settings.acc_folder_id
                if root:
                    # Estrutura: root / turma / matricula
                    return {"type": "folder", "root": root, "path": [source.turma, source.matricula]}

        elif tipo == "TCC":
            source_rows = session.exec(
                select(TccSubmission).where(
                    TccSubmission.matricula == mat,
                    TccSubmission.periodo == per,
                    TccSubmission.polo == pol,
                )
            ).all()
            for source in source_rows:
                if _is_tcc1_submission(source.componente) and source.drive_folder_id:
                    return {
                        "type": "folder",
                        "root": source.drive_folder_id,
                        "path": [source.componente, source.turma, source.nome],
                    }

        elif tipo in {"ESTAGIO", "ESTÁGIO"}:
            source_rows = session.exec(
                select(EstagioSubmission).where(
                    EstagioSubmission.matricula == mat,
                    EstagioSubmission.periodo == per,
                    EstagioSubmission.polo == pol,
                )
            ).all()
            for source in source_rows:
                if _normalize_estagio_component(source.componente) == comp and source.drive_folder_id:
                    return {
                        "type": "folder",
                        "root": source.drive_folder_id,
                        "path": [source.componente, source.turma, source.matricula],
                    }

    return None


def delete_lancamento_conceitos_with_source(records: List[Dict[str, Any]]) -> tuple[int, int]:
    """
    Remove o registro do lançamento e a submissão-fonte correspondente.

    Cada item deve conter:
        id, tipo_formulario, matricula, periodo, polo, componente
    """
    if not records:
        return 0, 0

    deleted_count = 0
    ignored_count = 0

    with get_db_session() as session:
        for item in records:
            item_id = item.get("id")
            tipo_formulario = _normalize_text(item.get("tipo_formulario")).upper()
            matricula = _normalize_text(item.get("matricula"))
            periodo = _normalize_text(item.get("periodo"))
            polo = _normalize_text(item.get("polo"))
            componente = _normalize_text(item.get("componente"))

            registro = session.get(LancamentoConceito, int(item_id)) if item_id else None
            source_deleted = False

            if tipo_formulario == "ACC":
                source_rows = session.exec(
                    select(AccSubmission).where(
                        AccSubmission.matricula == matricula,
                        AccSubmission.periodo == periodo,
                        AccSubmission.polo == polo,
                    )
                ).all()
                for source in source_rows:
                    session.delete(source)
                    source_deleted = True
            elif tipo_formulario == "TCC":
                source_rows = session.exec(
                    select(TccSubmission).where(
                        TccSubmission.matricula == matricula,
                        TccSubmission.periodo == periodo,
                        TccSubmission.polo == polo,
                    )
                ).all()
                for source in source_rows:
                    if componente == "TCC 1" and _is_tcc1_submission(source.componente):
                        session.delete(source)
                        source_deleted = True
            elif tipo_formulario == "ESTAGIO":
                source_rows = session.exec(
                    select(EstagioSubmission).where(
                        EstagioSubmission.matricula == matricula,
                        EstagioSubmission.periodo == periodo,
                        EstagioSubmission.polo == polo,
                    )
                ).all()
                for source in source_rows:
                    if _normalize_estagio_component(source.componente) == componente:
                        session.delete(source)
                        source_deleted = True
            elif tipo_formulario == "CCF":
                source_rows = session.exec(
                    select(CcfSubmission).where(
                        CcfSubmission.matricula == matricula,
                        CcfSubmission.periodo == periodo,
                        CcfSubmission.polo == polo,
                    )
                ).all()
                for source in source_rows:
                    session.delete(source)
                    source_deleted = True

            if registro is not None:
                session.delete(registro)
                deleted_count += 1
            elif source_deleted:
                deleted_count += 1
            else:
                ignored_count += 1

        session.commit()

    return deleted_count, ignored_count


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


# ---------------------------------------------------------------------------
# Períodos de Submissão (TCC / ACC / Estágio)
# ---------------------------------------------------------------------------

def list_periodos_submissao(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna todos os períodos cadastrados, opcionalmente filtrados por tipo."""
    with get_db_session() as session:
        query = select(PeriodoSubmissao)
        if tipo:
            query = query.where(PeriodoSubmissao.tipo == tipo.lower())
        query = query.order_by(PeriodoSubmissao.tipo, PeriodoSubmissao.numero)
        rows = session.exec(query).all()
        return [
            {
                "id": r.id,
                "tipo": r.tipo,
                "numero": r.numero,
                "data_inicio": r.data_inicio,
                "data_fim": r.data_fim,
                "semestre": r.semestre,
            }
            for r in rows
        ]


def get_periodos_ativos_para_data(tipo: str, data: str) -> List[Dict[str, Any]]:
    """Retorna períodos do tipo dado onde data_inicio <= data <= data_fim."""
    periodos = list_periodos_submissao(tipo=tipo)
    return [p for p in periodos if p["data_inicio"] <= data <= p["data_fim"]]


def save_periodo_submissao(data: Dict[str, Any]) -> int:
    """Cria um novo período de submissão. Retorna o ID criado."""
    periodo = PeriodoSubmissao(
        tipo=data["tipo"].lower(),
        numero=int(data["numero"]),
        data_inicio=data["data_inicio"],
        data_fim=data["data_fim"],
        semestre=data.get("semestre"),
    )
    with get_db_session() as session:
        session.add(periodo)
        session.commit()
        session.refresh(periodo)
        return periodo.id


def update_periodo_submissao(periodo_id: int, data: Dict[str, Any]) -> bool:
    """Atualiza campos de um período existente. Retorna True se encontrado."""
    with get_db_session() as session:
        row = session.exec(
            select(PeriodoSubmissao).where(PeriodoSubmissao.id == periodo_id)
        ).first()
        if row is None:
            return False
        if "tipo" in data:
            row.tipo = data["tipo"].lower()
        if "numero" in data:
            row.numero = int(data["numero"])
        if "data_inicio" in data:
            row.data_inicio = data["data_inicio"]
        if "data_fim" in data:
            row.data_fim = data["data_fim"]
        if "semestre" in data:
            row.semestre = data["semestre"]
        session.add(row)
        session.commit()
        return True


def delete_periodo_submissao(periodo_id: int) -> bool:
    """Remove um período de submissão. Retorna True se encontrado."""
    with get_db_session() as session:
        row = session.exec(
            select(PeriodoSubmissao).where(PeriodoSubmissao.id == periodo_id)
        ).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Funcionários (cadastro de docentes/colaboradores)
# ---------------------------------------------------------------------------

def _funcionario_to_dict(r: Funcionario) -> Dict[str, Any]:
    return {
        "id": r.id,
        "nome": r.nome,
        "filiacao": r.filiacao,
        "titulo": r.titulo,
        "tipo": r.tipo,
        "categoria": r.categoria,
        "email": r.email,
        "fone": r.fone,
        "data_aniversario": r.data_aniversario,
        "diretor_faculdade": bool(r.diretor_faculdade),
        "coordenador_estagio": bool(r.coordenador_estagio),
        "representante_docente": bool(r.representante_docente),
    }


def list_funcionarios(tipo: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna todos os funcionários, opcionalmente filtrados por tipo."""
    with get_db_session() as session:
        query = select(Funcionario)
        if tipo:
            query = query.where(Funcionario.tipo == tipo)
        query = query.order_by(Funcionario.nome)
        rows = session.exec(query).all()
        return [_funcionario_to_dict(r) for r in rows]


def save_funcionario(data: Dict[str, Any]) -> int:
    """Cria um novo funcionário. Retorna o ID criado."""
    funcionario = Funcionario(
        nome=data["nome"],
        filiacao=data.get("filiacao"),
        titulo=data["titulo"],
        tipo=data["tipo"],
        categoria=data.get("categoria", "Docente"),
        email=data.get("email"),
        fone=data.get("fone"),
        data_aniversario=data.get("data_aniversario"),
        diretor_faculdade=bool(data.get("diretor_faculdade", False)),
        coordenador_estagio=bool(data.get("coordenador_estagio", False)),
        representante_docente=bool(data.get("representante_docente", False)),
    )
    with get_db_session() as session:
        session.add(funcionario)
        session.commit()
        session.refresh(funcionario)
        return funcionario.id


def update_funcionario(funcionario_id: int, data: Dict[str, Any]) -> bool:
    """Atualiza campos de um funcionário existente. Retorna True se encontrado."""
    with get_db_session() as session:
        row = session.exec(
            select(Funcionario).where(Funcionario.id == funcionario_id)
        ).first()
        if row is None:
            return False
        for campo in (
            "nome", "filiacao", "titulo", "tipo", "categoria", "email", "fone",
            "data_aniversario", "diretor_faculdade", "coordenador_estagio",
            "representante_docente",
        ):
            if campo in data:
                setattr(row, campo, data[campo])
        session.add(row)
        session.commit()
        return True


def delete_funcionario(funcionario_id: int) -> bool:
    """Remove um funcionário. Retorna True se encontrado."""
    with get_db_session() as session:
        row = session.exec(
            select(Funcionario).where(Funcionario.id == funcionario_id)
        ).first()
        if row is None:
            return False
        session.delete(row)
        session.commit()
        return True


def get_funcionario_emails(
    categoria: Optional[str] = None, tipo: Optional[str] = None
) -> List[str]:
    """Retorna e-mails de funcionários, filtrando por categoria/tipo (opcionais).

    Ignora registros sem e-mail. Remove duplicatas preservando a ordem alfabética
    de nome (ordem garantida por list_funcionarios).
    """
    funcionarios = list_funcionarios(tipo=tipo)
    if categoria:
        funcionarios = [f for f in funcionarios if (f.get("categoria") or "") == categoria]
    seen: set = set()
    emails: List[str] = []
    for f in funcionarios:
        email = (f.get("email") or "").strip()
        if email and email.lower() not in seen:
            seen.add(email.lower())
            emails.append(email)
    return emails


def get_funcionario_emails_by_cargo(cargo: str) -> List[str]:
    """Retorna e-mails de funcionários que possuem o cargo/função indicado.

    ``cargo`` deve ser uma das flags: 'diretor_faculdade', 'coordenador_estagio'
    ou 'representante_docente'. Ignora registros sem e-mail.
    """
    if cargo not in ("diretor_faculdade", "coordenador_estagio", "representante_docente"):
        raise ValueError(f"Cargo inválido: {cargo}")
    seen: set = set()
    emails: List[str] = []
    for f in list_funcionarios():
        if not f.get(cargo):
            continue
        email = (f.get("email") or "").strip()
        if email and email.lower() not in seen:
            seen.add(email.lower())
            emails.append(email)
    return emails


def get_funcionario_emails_by_nomes(nomes: List[str]) -> List[str]:
    """Resolve uma lista de nomes de funcionários para os e-mails cadastrados.

    Casamento por nome normalizado (trim + case-insensitive). Nomes sem
    correspondência ou sem e-mail são silenciosamente ignorados. Retorna
    e-mails únicos preservando a ordem dos nomes informados.
    """
    alvos = [(n or "").strip().lower() for n in nomes if n and n.strip()]
    if not alvos:
        return []
    todos = list_funcionarios()
    indice = {
        (f.get("nome") or "").strip().lower(): (f.get("email") or "").strip()
        for f in todos
    }
    seen: set = set()
    emails: List[str] = []
    for alvo in alvos:
        email = indice.get(alvo, "")
        if email and email.lower() not in seen:
            seen.add(email.lower())
            emails.append(email)
    return emails
