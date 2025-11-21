#!/bin/bash
# ============================================
# Script de Configuração de Ambiente FasiTech
# ============================================
# Configura automaticamente o .env para diferentes ambientes

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║   FasiTech Environment Setup Script    ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar se o .env existe
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado${NC}"
    echo -e "Criando a partir de .env.example..."
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env criado com sucesso${NC}"
    else
        echo -e "${RED}❌ .env.example não encontrado!${NC}"
        exit 1
    fi
fi

# Menu de seleção
echo ""
echo "Selecione o ambiente de execução:"
echo ""
echo "1) 💻 Desenvolvimento Local (detecção automática)"
echo "2) 🌐 VM de Produção UFPA (/home/ubuntu/appStreamLit)"
echo "3) 🐳 Container Docker (/app/src/resources)"
echo "4) 📝 Caminho Customizado"
echo "5) ❓ Verificar configuração atual"
echo ""
read -p "Opção [1-5]: " option

case $option in
    1)
        ENV_NAME="Desenvolvimento Local"
        RAG_DIR=""
        API_URL="http://localhost:8000"
        ;;
    2)
        ENV_NAME="VM Produção UFPA"
        RAG_DIR="/home/ubuntu/appStreamLit/src/resources"
        API_URL="https://www.fasitech.com.br"
        ;;
    3)
        ENV_NAME="Container Docker"
        RAG_DIR="/app/src/resources"
        API_URL="http://localhost:8000"
        ;;
    4)
        echo ""
        read -p "Digite o caminho completo para os documentos PDF: " custom_path
        if [ -d "$custom_path" ]; then
            ENV_NAME="Customizado"
            RAG_DIR="$custom_path"
            read -p "URL da API [http://localhost:8000]: " api_url
            API_URL=${api_url:-http://localhost:8000}
        else
            echo -e "${RED}❌ Diretório não existe: $custom_path${NC}"
            exit 1
        fi
        ;;
    5)
        echo ""
        echo -e "${BLUE}📋 Configuração Atual:${NC}"
        echo ""
        
        if grep -q "^RAG_DOCUMENTS_DIR=" .env; then
            current_dir=$(grep "^RAG_DOCUMENTS_DIR=" .env | cut -d'=' -f2)
            if [ -z "$current_dir" ]; then
                echo "  RAG_DOCUMENTS_DIR: (detecção automática)"
            else
                echo "  RAG_DOCUMENTS_DIR: $current_dir"
            fi
        else
            echo "  RAG_DOCUMENTS_DIR: (não configurado - usando detecção automática)"
        fi
        
        if grep -q "^API_BASE_URL=" .env; then
            current_api=$(grep "^API_BASE_URL=" .env | cut -d'=' -f2)
            echo "  API_BASE_URL: $current_api"
        fi
        
        echo ""
        echo -e "${YELLOW}💡 Execute novamente para alterar a configuração${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Opção inválida${NC}"
        exit 1
        ;;
esac

# Backup do .env atual
echo ""
echo -e "${YELLOW}📦 Criando backup do .env...${NC}"
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Atualizar RAG_DOCUMENTS_DIR
if grep -q "^RAG_DOCUMENTS_DIR=" .env; then
    # Substituir linha existente
    sed -i "s|^RAG_DOCUMENTS_DIR=.*|RAG_DOCUMENTS_DIR=$RAG_DIR|g" .env
else
    # Adicionar no final
    echo "" >> .env
    echo "# Configuração RAG (adicionado automaticamente)" >> .env
    echo "RAG_DOCUMENTS_DIR=$RAG_DIR" >> .env
fi

# Atualizar API_BASE_URL
if grep -q "^API_BASE_URL=" .env; then
    sed -i "s|^API_BASE_URL=.*|API_BASE_URL=$API_URL|g" .env
else
    echo "API_BASE_URL=$API_URL" >> .env
fi

# Resumo
echo ""
echo -e "${GREEN}✅ Configuração atualizada com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Resumo:${NC}"
echo "  Ambiente: $ENV_NAME"
if [ -z "$RAG_DIR" ]; then
    echo "  RAG_DOCUMENTS_DIR: (detecção automática)"
else
    echo "  RAG_DOCUMENTS_DIR: $RAG_DIR"
fi
echo "  API_BASE_URL: $API_URL"
echo ""

# Verificar se os PDFs existem (se caminho foi especificado)
if [ -n "$RAG_DIR" ] && [ -d "$RAG_DIR" ]; then
    pdf_count=$(ls -1 "$RAG_DIR"/*.pdf 2>/dev/null | wc -l)
    if [ "$pdf_count" -gt 0 ]; then
        echo -e "${GREEN}✅ Encontrados $pdf_count arquivo(s) PDF no diretório${NC}"
        ls -1 "$RAG_DIR"/*.pdf | while read pdf; do
            echo "   📄 $(basename "$pdf")"
        done
    else
        echo -e "${YELLOW}⚠️  Nenhum arquivo PDF encontrado em: $RAG_DIR${NC}"
    fi
elif [ -z "$RAG_DIR" ]; then
    echo -e "${BLUE}ℹ️  Detecção automática habilitada - o sistema tentará:${NC}"
    echo "   1. <projeto>/src/resources"
    echo "   2. /app/src/resources (Docker)"
fi

echo ""
echo -e "${YELLOW}💡 Dica: Execute 'source .env' ou reinicie a aplicação para aplicar as mudanças${NC}"
echo ""
