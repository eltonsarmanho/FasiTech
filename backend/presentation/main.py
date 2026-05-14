from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from backend.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        from backend.infrastructure.database.engine import init_db
        init_db()
        logger.info("Banco de dados inicializado.")
    except Exception as e:
        logger.warning(f"Banco de dados não inicializado: {e}")

    try:
        from backend.infrastructure.scheduler.alert_scheduler import ensure_scheduler_running
        ensure_scheduler_running()
        logger.info("Scheduler de alertas iniciado.")
    except Exception as e:
        logger.warning(f"Scheduler não iniciado: {e}")

    yield
    # Shutdown (sem ação necessária)


app = FastAPI(
    title="FasiTech BFF API",
    description="Backend For Frontend — Portal Acadêmico FASI/UFPA",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — permite React dev server e domínio de produção
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://www.fasitech.com.br",
    "https://fasitech.com.br",
    "http://fasitech.cameta.ufpa.br",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# ── Routers ──────────────────────────────────────────────────────────────────
from backend.presentation.api.v1.forms import (
    acc, tcc, estagio, requerimento_tcc,
    emissao_documentos, social, plano_ensino,
    projetos, avaliacao_gestao,
)
from backend.presentation.api.v1.data import social_data, requerimento_tcc_data, projetos_data
from backend.presentation.api.v1.rag import diretor_virtual
from backend.presentation.api.v1.ofertas import disciplinas
from backend.presentation.api.v1 import config as config_router
from backend.presentation.api.admin import alertas, lancamentos

# Formulários
app.include_router(acc.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(tcc.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(estagio.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(requerimento_tcc.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(emissao_documentos.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(social.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(plano_ensino.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(projetos.router, prefix="/api/v1/forms", tags=["Formulários"])
app.include_router(avaliacao_gestao.router, prefix="/api/v1/forms", tags=["Formulários"])

# Config pública
app.include_router(config_router.router, prefix="/api/v1", tags=["Config"])

# Dados / Consultas
app.include_router(social_data.router, prefix="/api/v1", tags=["Dados Sociais"])
app.include_router(requerimento_tcc_data.router, prefix="/api/v1", tags=["Consultas"])
app.include_router(projetos_data.router, prefix="/api/v1", tags=["Consultas"])

# RAG
app.include_router(diretor_virtual.router, prefix="/api/v1", tags=["Diretor Virtual"])

# Ofertas
app.include_router(disciplinas.router, prefix="/api/v1", tags=["Ofertas"])

# Admin (restrito)
app.include_router(alertas.router, prefix="/api/admin", tags=["Admin"])
app.include_router(lancamentos.router, prefix="/api/admin", tags=["Admin"])


# ── Endpoints base ────────────────────────────────────────────────────────────
@app.get("/", tags=["root"])
async def root():
    return {"message": "FasiTech BFF API v2.0", "docs": "/docs"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "2.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Erro interno do servidor"},
    )
