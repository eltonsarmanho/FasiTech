from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    """Carrega variáveis de ambiente do arquivo .env na raiz do projeto."""
    # Procurar .env no diretório raiz do projeto
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent.parent
    env_path = root_dir / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Variáveis de ambiente carregadas de: {env_path}")
    else:
        print(f"⚠️ Arquivo .env não encontrado em: {env_path}")


# Carregar automaticamente ao importar o módulo
load_environment()
