#!/bin/bash

# Script de Deploy — Chatwoot integrado ao FasiTech (VM UFPA)
# Uso: bash scripts/deploy-chatwoot-ufpa.sh

set -e

echo "🚀 FasiTech Chatwoot Deployment Script"
echo "========================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificações pré-deployment
echo -e "${YELLOW}📋 Verificando pré-requisitos...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker e Docker Compose encontrados${NC}"
echo ""

# Parar containers existentes
echo -e "${YELLOW}🛑 Parando containers existentes...${NC}"
docker-compose -f docker-compose.productionUFPA.yml down 2>/dev/null || true
echo -e "${GREEN}✅ Containers parados${NC}"
echo ""

# Build e start dos containers
echo -e "${YELLOW}🔨 Buildando e iniciando containers...${NC}"
docker-compose -f docker-compose.productionUFPA.yml up -d --build

echo -e "${GREEN}✅ Containers iniciados${NC}"
echo ""

# Aguardar inicialização do Chatwoot (pode levar 2-3 minutos)
echo -e "${YELLOW}⏳ Aguardando Chatwoot inicializar (até 3 min)...${NC}"
RETRY=0
MAX_RETRIES=36  # 3 minutos com 5s entre tentativas
while [ $RETRY -lt $MAX_RETRIES ]; do
    if docker-compose -f docker-compose.productionUFPA.yml exec -T chatwoot curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Chatwoot está saudável${NC}"
        break
    fi
    RETRY=$((RETRY+1))
    echo "  Tentativa $RETRY/$MAX_RETRIES..."
    sleep 5
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Chatwoot não iniciou no tempo esperado${NC}"
    echo "Verifique os logs com: docker-compose -f docker-compose.productionUFPA.yml logs chatwoot"
    exit 1
fi

echo ""

# Informações de acesso
echo -e "${GREEN}🎉 Deployment concluído com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📍 URLs de Acesso:${NC}"
echo "  • FasiTech: https://fasitech.cameta.ufpa.br"
echo "  • Chatwoot: https://chatwoot.fasitech.cameta.ufpa.br"
echo ""

echo -e "${YELLOW}🔧 Próximos Passos:${NC}"
echo ""
echo "1️⃣  Acessar Chatwoot e criar Admin User (primeira vez apenas):"
echo "   docker-compose -f docker-compose.productionUFPA.yml exec chatwoot bundle exec rake db:seed"
echo ""
echo "2️⃣  Verificar status dos serviços:"
echo "   docker-compose -f docker-compose.productionUFPA.yml ps"
echo ""
echo "3️⃣  Ver logs em tempo real:"
echo "   docker-compose -f docker-compose.productionUFPA.yml logs -f chatwoot"
echo ""
echo "4️⃣  Testar conectividade (no navegador ou curl):"
echo "   curl -s https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts"
echo ""

echo -e "${YELLOW}📚 Documentação:${NC}"
echo "  • CHATWOOT_DEPLOYMENT_GUIDE.md"
echo "  • CHATWOOT_FIX_GUIDE.md"
echo ""

echo -e "${GREEN}✨ Tudo pronto! Acesse https://chatwoot.fasitech.cameta.ufpa.br${NC}"
