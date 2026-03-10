"""Database engine and session management for FasiTech."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

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
    )
    
    print("🔧 Inicializando banco de dados...")
    SQLModel.metadata.create_all(engine)
    print("✅ Banco de dados inicializado com sucesso!")


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
