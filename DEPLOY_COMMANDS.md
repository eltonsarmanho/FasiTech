# 🚀 Deploy Chatwoot — Copie e Cole na VM UFPA

## Passo 1: SSH e Pull (Execute na VM UFPA)

```bash
ssh eltonss@172.16.28.198

# Navegue até o projeto (ajuste o caminho conforme necessário)
cd /home/eltonss/FasiTech

# Ou se estiver em outro diretório:
# cd /path/to/FasiTech

# Faça o pull das mudanças
git pull origin main
```

## Passo 2: Execute o Script de Deploy (RECOMENDADO)

```bash
# Dar permissão de execução (primeira vez)
chmod +x scripts/deploy-chatwoot-ufpa.sh

# Executar o script
bash scripts/deploy-chatwoot-ufpa.sh

# Isso fará:
# ✅ Verificar Docker/Docker-Compose
# ✅ Parar containers existentes
# ✅ Build das imagens
# ✅ Iniciar todos os containers
# ✅ Aguardar Chatwoot ficar saudável
# ✅ Mostrar URLs de acesso
```

## Passo 3: Verificar Status (Se optar por fazer manualmente)

Se preferir fazer sem o script:

```bash
# Parar containers
docker compose -p fasitech -f docker-compose.productionUFPA.yml down

# Build e iniciar (pode levar 5-10 minutos)
docker compose -p fasitech -f docker-compose.productionUFPA.yml up -d --build

# Aguardar inicialização
docker compose -p fasitech -f docker-compose.productionUFPA.yml logs -f chatwoot

# Quando aparecer "ready to accept connections", pressione Ctrl+C
```

## Passo 4: Criar Admin User (Primeira vez apenas)

```bash
# Entrar no container do Chatwoot
docker compose -p fasitech -f docker-compose.productionUFPA.yml exec chatwoot bash

# Dentro do container, executar seed:
bundle exec rake db:chatwoot_prepare

# Sair do container (Ctrl+D ou exit)
```

## Passo 5: Testar (Execute em qualquer lugar)

```bash
# Testar API do Chatwoot
curl -s https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts \
  -H "API-TOKEN: RQnCehNGnUYC7yjYxbFrr3t4"

# Deveria retornar JSON (não 404/500)
```

## Passo 6: Verificar no Navegador

1. Abra: https://fasitech.cameta.ufpa.br
2. Pressione F12 (Developer Console)
3. Cole no console:
```javascript
console.log('SDK carregado?', window.chatwootSDK ? '✅ Sim' : '❌ Não');
window.$chatwoot?.open();
```

## ⚠️ Se Algo dar Errado

```bash
# Ver logs do Chatwoot
docker compose -p fasitech -f docker-compose.productionUFPA.yml logs chatwoot

# Ver todos os logs
docker compose -p fasitech -f docker-compose.productionUFPA.yml logs -f

# Restart específico
docker compose -p fasitech -f docker-compose.productionUFPA.yml restart chatwoot

# Status dos containers
docker compose -p fasitech -f docker-compose.productionUFPA.yml ps

# Parar tudo
docker compose -p fasitech -f docker-compose.productionUFPA.yml down
```

## 📚 Documentação de Referência

Leia se tiver dúvidas:

```bash
# Quick start (mais rápido)
cat CHATWOOT_QUICK_START.md

# Guia completo
cat CHATWOOT_DEPLOYMENT_GUIDE.md

# Troubleshooting
cat CHATWOOT_FIX_GUIDE.md
```

---

**Pronto! Após esses passos, Chatwoot estará funcionando! 🎉**
