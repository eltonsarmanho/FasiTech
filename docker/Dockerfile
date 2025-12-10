# --- Estágio 1: Builder ---
# Usamos uma imagem Python completa para instalar as dependências de forma eficiente.
FROM python:3.11-slim-buster as builder 

# Define o diretório de trabalho
WORKDIR /app

# Instala as dependências em um local separado para facilitar a cópia
RUN pip install --upgrade pip
COPY requirements.txt .
# --wheel-dir cria "wheels" pré-compilados, otimizando a instalação no próximo estágio.
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt


# --- Estágio 2: Final ---
# Usamos uma imagem "slim" leve para a imagem final, reduzindo o tamanho.
FROM python:3.11-slim-bookworm 

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# --- MUDANÇA PRINCIPAL: Instalar dependências como root ---
# Copia as dependências pré-compiladas do estágio de build.
COPY --from=builder /app/wheels /wheels
# Agora isso funcionará, pois estamos instalando wheels de 3.11 com um pip de 3.11
RUN pip install --no-cache /wheels/*

# Instala dependências do sistema necessárias:
# - curl: necessário para o HEALTHCHECK e Ollama
# - poppler-utils: necessário para pdf2image converter PDFs para imagens
# - wget: necessário para baixar Ollama
# É importante limpar o cache do apt para manter a imagem pequena.
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Instala Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Cria diretórios necessários para o Ollama
RUN mkdir -p /home/appuser/.ollama

# Copia todo o restante do código da aplicação para o contêiner.
# Copiamos o código APÓS instalar as dependências para aproveitar o cache do Docker.
COPY . .

# Cria um usuário não-root para executar a aplicação. É uma prática de segurança crucial.
RUN useradd --create-home appuser

# Criar script de inicialização que inicia Ollama e Streamlit (como root)
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Garantir que diretórios de cache existam e tenham permissões corretas\n\
mkdir -p /home/appuser/.cache/fasitech/rag/lancedb\n\
\n\
# Iniciar Ollama em background\n\
export OLLAMA_HOST=127.0.0.1:11434\n\
ollama serve &\n\
sleep 5\n\
\n\
# Baixar modelo embedder se não existir\n\
ollama pull nomic-embed-text || true\n\
\n\
# Iniciar Streamlit\n\
exec streamlit run --client.showSidebarNavigation=False src/app/main.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false\n\
' > /app/start.sh && chmod +x /app/start.sh

# Ajustar permissões do Ollama para o usuário não-root
RUN chown -R appuser:appuser /home/appuser/.ollama
RUN chmod +x /usr/local/bin/ollama
RUN chown appuser:appuser /app/start.sh

# Criar diretório cache para o RAG com permissões completas
# Inclui subdiretórios para LanceDB e SQLite
RUN mkdir -p /home/appuser/.cache/fasitech/rag/lancedb && \
    chown -R appuser:appuser /home/appuser/.cache && \
    chmod -R 755 /home/appuser/.cache

# --- MUDANÇA PRINCIPAL: Mudar para o usuário não-root no final ---
# Mude para o usuário não-root DEPOIS que tudo estiver instalado e copiado.
USER appuser

# Expõe a porta que a aplicação vai usar.
EXPOSE 8501

# Adiciona uma verificação de saúde (HEALTHCHECK)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando para iniciar a aplicação.
CMD ["/app/start.sh"]