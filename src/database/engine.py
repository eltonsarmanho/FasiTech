"""Database engine and session management for FasiTech."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine

# Configuração do banco de dados
# Usa variável de ambiente DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Please set it with your PostgreSQL connection string."
    )

# Configuração de conexão
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Engine do banco de dados
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query debugging
    connect_args=connect_args,
    pool_pre_ping=True,  # Verifica conexão antes de usar
    pool_recycle=3600,   # Recicla conexões a cada hora
)


def init_db() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas.
    
    Deve ser chamado uma vez na inicialização da aplicação.
    """
    from src.models.db_models import (
        TccSubmission,
        AccSubmission,
        ProjetosSubmission,
        PlanoEnsinoSubmission,
        EstagioSubmission,
        SocialSubmission,
        RequerimentoTccSubmission,
        AvaliacaoGestaoSubmission,
        AlertaAcademico,
        LancamentoConceito,
    )
    
    print("🔧 Inicializando banco de dados...")
    SQLModel.metadata.create_all(engine)
    _ensure_additional_columns()
    print("✅ Banco de dados inicializado com sucesso!")


def _ensure_additional_columns() -> None:
    """Aplica ajustes leves de schema em bancos já existentes."""
    inspector = inspect(engine)
    table_columns_map = {
        "tcc_submissions": {
            "polo": "VARCHAR(100) DEFAULT ''",
            "periodo": "VARCHAR(20) DEFAULT ''",
        },
        "acc_submissions": {
            "polo": "VARCHAR(100) DEFAULT ''",
            "periodo": "VARCHAR(20) DEFAULT ''",
        },
        "estagio_submissions": {
            "polo": "VARCHAR(100) DEFAULT ''",
            "periodo": "VARCHAR(20) DEFAULT ''",
        },
        "alertas_academicos": {
            "destination_type": "VARCHAR(20) DEFAULT 'docentes'",
            "destination_emails": "TEXT",
        },
    }
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table_name, columns in table_columns_map.items():
            if table_name not in existing_tables:
                continue
            existing_cols = {
                col["name"] for col in inspector.get_columns(table_name)
            }
            for col_name, ddl in columns.items():
                if col_name not in existing_cols:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN {col_name} {ddl}"
                        )
                    )


def get_session() -> Generator[Session, None, None]:
    """
    Dependência para obter uma sessão do banco de dados.
    
    Yields:
        Session: Sessão ativa do banco de dados
    """
    with Session(engine) as session:
        yield session


def get_db_session() -> Session:
    """
    Obtém uma sessão do banco de dados para uso direto.
    
    Returns:
        Session: Sessão do banco de dados
    """
    return Session(engine)
