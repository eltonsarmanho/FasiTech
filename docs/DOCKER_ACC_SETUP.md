# Guia Docker - FasiTech ACC Processing

## Problema Atual
O processamento ACC falha no Docker porque:
1. **poppler-utils** não estava instalado na imagem
2. **Dependências Python** podem não estar sendo instaladas corretamente
3. **GOOGLE_API_KEY** não está configurada no container

## ✅ Soluções Implementadas

### 1. Dockerfile Atualizado
```dockerfile
# Instala poppler-utils para pdf2image
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### 2. Requirements.txt Limpo
- Removida duplicata `python-dotenv`
- Todas as dependências ACC incluídas:
  - `pdf2image`
  - `agno`
  - `Pillow`
  - `python-dotenv`

### 3. Script de Atualização
- `scripts/update_docker.sh` automatiza rebuild e restart

## 🚀 Como Atualizar no Servidor

### 1. Fazer rsync com arquivos atualizados
```bash
# No local (já feito)
rsync -avz --progress --exclude 'venv/' --exclude '.env' ... /FasiTech/ root@servidor:/home/ubuntu/appStreamLit
```

### 2. Configurar .env no servidor
```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit

# Criar .env com as variáveis necessárias
cat > .env << EOF
GOOGLE_API_KEY=sua_chave_google_aqui
PYTHONPATH=/app
TZ=America/Sao_Paulo
EOF

# Proteger arquivo
chmod 600 .env
```

### 3. Executar atualização Docker
```bash
cd /home/ubuntu/appStreamLit
chmod +x scripts/update_docker.sh
./scripts/update_docker.sh
```

### 4. Verificar se tudo funcionou
```bash
# Verificar container rodando
sudo docker ps | grep fasi

# Testar dependências ACC
sudo docker exec -it fasi-app python scripts/verificar_dependencias_acc.py

# Ver logs
sudo docker logs -f fasi-app
```

## 🧪 Resultado Esperado

Após a atualização, o teste de dependências deve mostrar:
```
🔍 VERIFICADOR DE DEPENDÊNCIAS ACC
==================================================
🐍 Python: 3.11.x
✅ GOOGLE_API_KEY configurada
✅ pdf2image disponível
✅ poppler-utils encontrado
✅ agno/Gemini disponível
✅ Pillow disponível
✅ python-dotenv disponível
```

## 🐛 Troubleshooting

### Se container não iniciar:
```bash
sudo docker logs fasi-app
```

### Se dependências ainda faltarem:
```bash
# Entrar no container
sudo docker exec -it fasi-app bash

# Verificar instalação manual
pip list | grep -E "pdf2image|agno|pillow"
which pdftoppm
```

### Se erro de API:
```bash
# Verificar .env no container
sudo docker exec -it fasi-app env | grep GOOGLE
```

## 🔄 Comandos Docker Úteis

```bash
# Parar e remover container
sudo docker stop fasi-app && sudo docker rm fasi-app

# Rebuild completo (sem cache)
sudo docker build --no-cache -t fasi-tech -f docker/Dockerfile .

# Executar com logs visíveis
sudo docker run --rm -it --env-file .env fasi-tech

# Entrar no container para debug
sudo docker exec -it fasi-app bash
```

---
*Agora o processamento ACC deve funcionar perfeitamente no Docker! 🎉*