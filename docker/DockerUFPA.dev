# --- Estágio 1: Builder ---
FROM python:3.11-slim-buster as builder 

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# --- Estágio 2: Final ---
FROM python:3.11-slim-bookworm 

WORKDIR /app

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Instala dependências do sistema (mínimas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Instala Ollama versão CPU-only (sem CUDA para economizar espaço)
# Definir variável para não baixar bibliotecas CUDA
ENV OLLAMA_SKIP_CUDA_CHECK=1
RUN curl --http1.1 -fsSL https://ollama.com/install.sh | OLLAMA_SKIP_CUDA_CHECK=1 sh \
    && rm -rf /tmp/* /var/tmp/*

# Cria diretórios necessários
RUN mkdir -p /home/appuser/.ollama

# Copia código da aplicação
COPY . .

# Cria usuário não-root
RUN useradd --create-home appuser

# Script de inicialização
RUN echo '#!/bin/bash\n\
export OLLAMA_HOST=127.0.0.1:11434\n\
ollama serve &\n\
sleep 5\n\
ollama pull nomic-embed-text || true\n\
exec streamlit run --client.showSidebarNavigation=False src/app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false\n\
' > /app/start.sh && chmod +x /app/start.sh

# Ajusta permissões
RUN chown -R appuser:appuser /home/appuser/.ollama /app/start.sh
RUN mkdir -p /home/appuser/.cache/fasitech/rag && chown -R appuser:appuser /home/appuser/.cache

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["/app/start.sh"]