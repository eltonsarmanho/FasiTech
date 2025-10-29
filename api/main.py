from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging

from api.routes import webhooks, social

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="FasiTech API",
    description="API para acessar dados da plataforma FasiTech",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios específicos
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Middleware de segurança para hosts confiáveis
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Em produção, especificar hosts específicos
)


@app.get("/", tags=["root"])
async def root():
    """Endpoint raiz da API."""
    return JSONResponse(
        content={
            "message": "FasiTech API",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "health": "/health",
                "social_data": "/api/v1/dados-sociais",
                "webhooks": "/api/webhooks"
            }
        }
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Endpoint de verificação de saúde da API."""
    return {
        "status": "ok",
        "message": "FasiTech API funcionando corretamente"
    }


# Incluir rotas
app.include_router(
    webhooks.router, 
    prefix="/api/webhooks", 
    tags=["webhooks"]
)

app.include_router(
    social.router, 
    prefix="/api/v1", 
    tags=["social"]
)


# Handler para erros não tratados
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erro interno do servidor",
            "message": "Entre em contato com o suporte se o problema persistir"
        }
    )
