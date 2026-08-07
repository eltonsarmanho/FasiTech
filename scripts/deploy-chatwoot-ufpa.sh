#!/usr/bin/env bash

# Script de Deploy — Chatwoot integrado ao FasiTech (VM UFPA)
# Uso: bash scripts/deploy-chatwoot-ufpa.sh
#
# Reaproveita scripts/ufpa-issue-cert.sh (já usado para fasitech.cameta.ufpa.br)
# para emitir o certificado do Chatwoot da mesma forma testada: nginx sobe com
# a config mínima de bootstrap (nginx.ufpa.bootstrap.conf) só para servir o
# desafio ACME, certbot roda via container (não precisa estar instalado no
# host), e depois o nginx volta pra config completa. A renovação automática já
# é coberta pelo cron existente (ufpa-renew-cert.sh via ufpa-install-cert-renew-cron.sh),
# que renova TODOS os certificados emitidos — nada extra a configurar ali.

set -euo pipefail

echo "🚀 FasiTech Chatwoot Deployment Script"
echo "========================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Resolve a raiz do projeto independente de onde o script é chamado
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${YELLOW}📁 Diretório do projeto: ${PROJECT_ROOT}${NC}"

COMPOSE_PROJECT="fasitech"
COMPOSE_FILE="docker-compose.productionUFPA.yml"
CHATWOOT_DOMAIN="chatwoot.fasitech.cameta.ufpa.br"
CERT_DIR="/etc/letsencrypt/live/$CHATWOOT_DOMAIN"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Arquivo $COMPOSE_FILE não encontrado em $PROJECT_ROOT${NC}"
    exit 1
fi

if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Arquivo .env.production não encontrado em $PROJECT_ROOT${NC}"
    echo "   O Chatwoot e a API precisam dele (env_file). Verifique se o repositório está completo."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado — a variável \$EMAIL_PASSWORD usada pelo${NC}"
    echo -e "${YELLOW}   Chatwoot (SMTP) no docker-compose pode não ser resolvida.${NC}"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado${NC}"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}❌ Docker Compose não está instalado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"
echo -e "${GREEN}✅ Docker Compose: $($DOCKER_COMPOSE version | head -1)${NC}"
echo ""

DC() {
    $DOCKER_COMPOSE -p "$COMPOSE_PROJECT" -f "$COMPOSE_FILE" "$@"
}

# ─────────────────────────────────────────────────────────────────────────
# Passo 1 — Certificado SSL do Chatwoot
#
# Se subirmos direto com o nginx.ufpa.conf completo e o certificado do
# Chatwoot ainda não existir, o nginx INTEIRO falha ao iniciar (ssl_certificate
# aponta pra um arquivo inexistente) — derrubando também fasitech.cameta.ufpa.br
# Por isso emitimos o certificado ANTES de subir a stack completa,
# reaproveitando o mesmo fluxo já testado em ufpa-issue-cert.sh.
# ─────────────────────────────────────────────────────────────────────────
if [ -f "$CERT_DIR/fullchain.pem" ]; then
    echo -e "${GREEN}✅ Certificado SSL do Chatwoot já existe em $CERT_DIR${NC}"
else
    echo -e "${YELLOW}🔐 Certificado do Chatwoot ainda não existe — emitindo via scripts/ufpa-issue-cert.sh${NC}"
    echo -e "${YELLOW}   (pré-requisito: DNS de $CHATWOOT_DOMAIN precisa apontar pro IP público desta VM — já confirmado)${NC}"
    echo ""

    if [ ! -x "scripts/ufpa-issue-cert.sh" ]; then
        chmod +x scripts/ufpa-issue-cert.sh
    fi

    if DOMAIN="$CHATWOOT_DOMAIN" APP_DIR="$PROJECT_ROOT" COMPOSE_FILE="$PROJECT_ROOT/$COMPOSE_FILE" \
        bash scripts/ufpa-issue-cert.sh; then
        echo -e "${GREEN}✅ Certificado do Chatwoot emitido com sucesso${NC}"
    else
        echo -e "${RED}❌ Falha ao emitir o certificado do Chatwoot.${NC}"
        echo "   Causas mais comuns:"
        echo "   • DNS de $CHATWOOT_DOMAIN não aponta para o IP público desta VM"
        echo "   • Porta 80 bloqueada por firewall (necessária para o desafio HTTP-01)"
        echo ""
        echo "   O restante do site (fasitech.cameta.ufpa.br) não foi afetado."
        exit 1
    fi
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# Passo 2 — Deploy completo (build + up de todos os serviços, incluindo Chatwoot)
# ─────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}🔨 Buildando e subindo a stack completa...${NC}"
DC up -d --build

echo -e "${GREEN}✅ Containers iniciados${NC}"
echo ""

sleep 3
if [ "$(docker inspect -f '{{.State.Running}}' fasitech-nginx-prod 2>/dev/null)" != "true" ]; then
    echo -e "${RED}❌ O container do nginx não está rodando. Logs:${NC}"
    docker logs --tail 50 fasitech-nginx-prod 2>&1 || true
    exit 1
fi
echo -e "${GREEN}✅ Nginx está rodando com a config completa (HTTPS do Chatwoot ativo)${NC}"
echo ""

# Aguardar inicialização do Chatwoot (pode levar 2-3 minutos na primeira vez)
echo -e "${YELLOW}⏳ Aguardando Chatwoot inicializar (até 3 min)...${NC}"
RETRY=0
MAX_RETRIES=36
CHATWOOT_HEALTHY=false
while [ $RETRY -lt $MAX_RETRIES ]; do
    if DC exec -T chatwoot curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Chatwoot está saudável${NC}"
        CHATWOOT_HEALTHY=true
        break
    fi
    RETRY=$((RETRY+1))
    echo "  Tentativa $RETRY/$MAX_RETRIES..."
    sleep 5
done

if [ "$CHATWOOT_HEALTHY" = false ]; then
    echo -e "${RED}❌ Chatwoot não iniciou no tempo esperado${NC}"
    echo "Verifique os logs com: $DOCKER_COMPOSE -p $COMPOSE_PROJECT -f $COMPOSE_FILE logs chatwoot"
    exit 1
fi
echo ""

echo -e "${GREEN}🎉 Deployment concluído com sucesso!${NC}"
echo ""
echo -e "${YELLOW}📍 URLs de Acesso:${NC}"
echo "  • FasiTech: https://fasitech.cameta.ufpa.br"
echo "  • Chatwoot: https://chatwoot.fasitech.cameta.ufpa.br"
echo ""

echo -e "${YELLOW}🔧 Próximos Passos:${NC}"
echo ""
echo "1️⃣  Acessar Chatwoot e criar Admin User (primeira vez apenas):"
echo "   $DOCKER_COMPOSE -p $COMPOSE_PROJECT -f $COMPOSE_FILE exec chatwoot bundle exec rake db:chatwoot_prepare"
echo ""
echo "2️⃣  Verificar status dos serviços:"
echo "   $DOCKER_COMPOSE -p $COMPOSE_PROJECT -f $COMPOSE_FILE ps"
echo ""
echo "3️⃣  Ver logs em tempo real:"
echo "   $DOCKER_COMPOSE -p $COMPOSE_PROJECT -f $COMPOSE_FILE logs -f chatwoot"
echo ""
echo "4️⃣  Testar conectividade (no navegador ou curl):"
echo "   curl -s https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts"
echo ""
echo -e "${YELLOW}ℹ️  A renovação do certificado já é automática via o cron existente${NC}"
echo -e "${YELLOW}   (scripts/ufpa-renew-cert.sh) — nada extra a configurar.${NC}"
echo ""

echo -e "${GREEN}✨ Tudo pronto! Acesse https://chatwoot.fasitech.cameta.ufpa.br${NC}"
