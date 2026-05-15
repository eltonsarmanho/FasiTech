"""Configuração centralizada dos modelos LLM usados no FasiTech."""
from __future__ import annotations

import os

# Modelo principal — RAG/PPC, Diretor Virtual (texto)
# gemini-2.5-flash: contexto 1M tokens, free tier disponível
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Modelo para extração visual — ACC (PDF/imagem, menor custo)
GEMINI_MODEL_VISION: str = os.getenv("GEMINI_MODEL_VISION", "gemini-2.5-flash-lite")

# Modelo Ollama — fallback local quando GOOGLE_API_KEY não está configurada
OLLAMA_LLM_MODEL: str = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:3b")
