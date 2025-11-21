# 🔧 Guia de Configuração Multi-Ambiente

Este guia explica como configurar o FasiTech para funcionar em diferentes ambientes (desenvolvimento local, VM de produção, containers Docker).

## 📋 Índice

- [Variável RAG_DOCUMENTS_DIR](#variável-rag_documents_dir)
- [Configuração por Ambiente](#configuração-por-ambiente)
- [Detecção Automática](#detecção-automática)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Variável RAG_DOCUMENTS_DIR

A variável `RAG_DOCUMENTS_DIR` controla onde o sistema RAG (Diretor Virtual) busca os documentos PDF para indexação.

### Comportamento

1. **Prioridade 1**: Usa `RAG_DOCUMENTS_DIR` se configurada no `.env`
2. **Prioridade 2**: Fallback automático para caminhos conhecidos:
   - `<projeto>/src/resources` (relativo ao projeto)
   - `/app/src/resources` (container Docker)

### Quando Configurar

| Ambiente | Precisa Configurar? | Motivo |
|----------|---------------------|---------|
| **Desenvolvimento Local** | ❌ Não | Detecção automática funciona |
| **VM de Produção** | ✅ Sim | Caminho absoluto diferente |
| **Container Docker** | ❌ Não | Fallback `/app/src/resources` |

---

## ⚙️ Configuração por Ambiente

### 1. Desenvolvimento Local (Windows/Linux/Mac)

**Opção A: Detecção Automática (Recomendado)**

```bash
# .env
RAG_DOCUMENTS_DIR=
# ou simplesmente não definir a variável
```

O sistema automaticamente encontrará os PDFs em `src/resources/`.

**Opção B: Caminho Relativo Explícito**

```bash
# .env
RAG_DOCUMENTS_DIR=src/resources
```

**Opção C: Caminho Absoluto**

```bash
# .env (Linux/Mac)
RAG_DOCUMENTS_DIR=/home/usuario/projetos/FasiTech/src/resources

# .env (Windows)
RAG_DOCUMENTS_DIR=C:\Users\usuario\projetos\FasiTech\src\resources
```

---

### 2. VM de Produção (UFPA)

**Configuração Obrigatória**

```bash
# .env na VM
RAG_DOCUMENTS_DIR=/home/ubuntu/appStreamLit/src/resources
```

**Por quê?**
- A VM usa caminho absoluto diferente do desenvolvimento
- Garante que o serviço encontre os PDFs independente do diretório de execução

---

### 3. Container Docker

**Não precisa configurar**

```bash
# .env
RAG_DOCUMENTS_DIR=
# ou deixar vazio
```

O fallback automático usa `/app/src/resources` que é o caminho padrão do container.

**Se quiser explicitar:**

```bash
# .env
RAG_DOCUMENTS_DIR=/app/src/resources
```

---

## 🔍 Detecção Automática

### Como Funciona

Quando `RAG_DOCUMENTS_DIR` está vazio ou não definida, o sistema tenta (em ordem):

1. `<projeto>/src/resources` (relativo ao arquivo `rag_ppc.py`)
2. `<cwd>/src/resources` (relativo ao diretório atual)
3. `/app/src/resources` (caminho padrão do Docker)

### Logs de Detecção

Você verá no console:

```
✅ Documentos encontrados em: /path/to/src/resources
   📄 PPC.pdf
   📄 RegulamentoTCC.pdf
```

Ou se houver problema:

```
⚠️  RAG_DOCUMENTS_DIR existe mas não contém PDFs: /caminho/errado
⚠️  Nenhum PDF encontrado. Usando fallback: /caminho/default/PPC.pdf
```

---

## 🐛 Troubleshooting

### Problema: "Nenhum PDF encontrado"

**Solução 1: Verificar se PDFs existem**

```bash
# Local
ls -la src/resources/*.pdf

# VM
ls -la /home/ubuntu/appStreamLit/src/resources/*.pdf

# Docker
docker compose exec streamlit ls -la /app/src/resources/*.pdf
```

**Solução 2: Configurar caminho explícito**

```bash
# Encontre o caminho correto
pwd
# Ex: /home/usuario/projetos/FasiTech

# Configure no .env
echo "RAG_DOCUMENTS_DIR=$(pwd)/src/resources" >> .env
```

---

### Problema: "RAG_DOCUMENTS_DIR existe mas não contém PDFs"

**Causa**: Caminho configurado está correto mas vazio

**Solução**:

```bash
# Copie os PDFs para o diretório
cp /caminho/dos/pdfs/*.pdf /caminho/configurado/

# Ou atualize RAG_DOCUMENTS_DIR para apontar para o diretório correto
```

---

### Problema: Funciona localmente mas não na VM

**Causa**: `.env` local usa caminho relativo

**Solução na VM**:

```bash
# Edite o .env na VM
nano /home/ubuntu/appStreamLit/.env

# Adicione/Atualize:
RAG_DOCUMENTS_DIR=/home/ubuntu/appStreamLit/src/resources

# Reinicie o serviço
sudo docker compose -f docker-compose.production.yml restart streamlit
```

---

### Problema: Múltiplos ambientes no mesmo repositório

**Cenário**: Você desenvolve localmente e faz deploy na VM

**Solução: Use arquivo .env separado**

```bash
# .env.local (desenvolvimento)
RAG_DOCUMENTS_DIR=

# .env.production (VM)
RAG_DOCUMENTS_DIR=/home/ubuntu/appStreamLit/src/resources

# No deploy, use o arquivo correto
cp .env.production .env
```

**Ou use variável de ambiente do sistema**:

```bash
# No servidor, configure permanentemente
echo 'export RAG_DOCUMENTS_DIR=/home/ubuntu/appStreamLit/src/resources' >> ~/.bashrc
source ~/.bashrc
```

---

## 📝 Resumo de Melhores Práticas

### ✅ Faça

- ✅ Use detecção automática em desenvolvimento local
- ✅ Configure caminho absoluto em produção/VM
- ✅ Teste localmente antes de fazer deploy
- ✅ Documente o caminho usado em cada ambiente
- ✅ Verifique logs de inicialização do RAG

### ❌ Evite

- ❌ Usar caminhos relativos em produção
- ❌ Hardcoded paths no código
- ❌ Commitar `.env` com caminhos específicos
- ❌ Assumir que o diretório sempre existe

---

## 🔗 Referências

- Código fonte: [`src/services/rag_ppc.py`](../src/services/rag_ppc.py) - Método `_find_document_files()`
- Exemplo de configuração: [`.env.example`](../.env.example)
- Documentação RAG: [`RAG_DOCUMENT_MANAGEMENT.md`](./RAG_DOCUMENT_MANAGEMENT.md)

---

## 💡 Dica Pro

Para facilitar o desenvolvimento em múltiplos ambientes, crie um script:

```bash
#!/bin/bash
# scripts/setup_env.sh

ENV_TYPE=${1:-local}

case $ENV_TYPE in
  local)
    echo "RAG_DOCUMENTS_DIR=" > .env.tmp
    ;;
  vm)
    echo "RAG_DOCUMENTS_DIR=/home/ubuntu/appStreamLit/src/resources" > .env.tmp
    ;;
  docker)
    echo "RAG_DOCUMENTS_DIR=/app/src/resources" > .env.tmp
    ;;
  *)
    echo "Uso: ./setup_env.sh [local|vm|docker]"
    exit 1
    ;;
esac

# Merge com .env existente
cat .env.tmp >> .env
rm .env.tmp

echo "✅ Ambiente configurado para: $ENV_TYPE"
```

**Uso:**

```bash
# Desenvolvimento
./scripts/setup_env.sh local

# Antes de deploy
./scripts/setup_env.sh vm
```
