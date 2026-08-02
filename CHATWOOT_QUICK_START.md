# Quick Start — Chatwoot Deployment (VM UFPA)

## ✅ O que foi feito

- ✅ Adicionado Chatwoot + PostgreSQL + Redis ao `docker-compose.productionUFPA.yml`
- ✅ Corrigido certificado SSL no nginx
- ✅ Adicionados headers CORS
- ✅ Melhorado carregamento do SDK no frontend
- ✅ Atualizado `.env.production`

---

## 🚀 Deploy em 3 Passos

### Passo 1: Fazer Commit das Mudanças (Local)

```bash
cd /home/nees/Documents/VSCodigo/FasiTech

git add -A
git status  # Verifique o que será commitado

git commit -m "feat: integrate chatwoot docker service with postgres and redis

- Add chatwoot, postgres-chatwoot, redis-chatwoot services
- Fix nginx SSL certificate for chatwoot subdomain
- Add CORS headers to chatwoot nginx location
- Improve SDK loading in ChatWidget component
- Add chatwoot script to index.html for auto-loading
- Update .env.production with chatwoot configuration"

git push origin main
```

### Passo 2: SSH na VM UFPA e Fazer Pull

```bash
ssh eltonss@172.16.28.198

cd /path/to/fasitech  # Ex: /home/eltonss/FasiTech

git pull origin main
```

### Passo 3: Executar Script de Deploy

```bash
# Opção A: Usar o script automático (RECOMENDADO)
bash scripts/deploy-chatwoot-ufpa.sh

# Opção B: Ou fazer manualmente
docker-compose -f docker-compose.productionUFPA.yml down
docker-compose -f docker-compose.productionUFPA.yml up -d --build

# Aguardar inicialização (2-3 minutos)
docker-compose -f docker-compose.productionUFPA.yml logs -f chatwoot
# Quando vir "ready to accept connections", pressione Ctrl+C
```

---

## 🧪 Verificar se Funcionou

### No Navegador (qualquer lugar)

```javascript
// Abra https://fasitech.cameta.ufpa.br
// Pressione F12 (Console)

// 1. Verificar se SDK do Chatwoot carregou
console.log('SDK:', window.chatwootSDK ? '✅ Carregado' : '❌ Faltando');

// 2. Verificar se widget está disponível
console.log('Widget:', window.$chatwoot ? '✅ Pronto' : '❌ Faltando');

// 3. Abrir widget
window.$chatwoot?.open();
```

### Via Curl (na VM UFPA)

```bash
# Testar API do Chatwoot
curl -s https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts \
  -H "API-TOKEN: RQnCehNGnUYC7yjYxbFrr3t4" | jq .

# Deve retornar JSON com dados, não erro 404/500
```

### Docker Status

```bash
docker-compose -f docker-compose.productionUFPA.yml ps

# Todos os services devem estar "Up"
```

---

## ⚙️ Configurações Importantes

### Variáveis de Ambiente (`.env.production`)

```bash
# Email (Chatwoot usará isso para notificações)
EMAIL_PASSWORD=lzhg zgwc ihbk ypqn  # Já configurado

# Chatwoot
CHATWOOT_API_TOKEN=RQnCehNGnUYC7yjYxbFrr3t4
CHATWOOT_API_URL=http://chatwoot:3000  # URL interna (Docker)
CHATWOOT_ACCOUNT_ID=1
CHATWOOT_TEAM_ID_SECRETARIA=1
CHATWOOT_TEAM_ID_DIRETOR=2
```

### Credenciais do PostgreSQL (Chatwoot)

```
Usuário: chatwoot
Senha: chatwoot_secure_pass_2024
Host: postgres-chatwoot
Banco: chatwoot
```

---

## 🔐 Primeira Configuração (Admin User)

Após o deploy, criar um usuário admin:

```bash
# Na VM UFPA
docker-compose -f docker-compose.productionUFPA.yml exec chatwoot \
  bundle exec rake db:seed

# Ou acessar Chatwoot em https://chatwoot.fasitech.cameta.ufpa.br
# e seguir os passos de criação do admin
```

---

## 📊 Verificar Logs

```bash
# Logs do Chatwoot
docker-compose -f docker-compose.productionUFPA.yml logs -f chatwoot

# Logs do Nginx
docker-compose -f docker-compose.productionUFPA.yml logs -f nginx

# Todos os logs
docker-compose -f docker-compose.productionUFPA.yml logs -f
```

---

## ❌ Se Algo Deu Errado

### Chatwoot retorna 404

```bash
# Verificar se está rodando
docker-compose -f docker-compose.productionUFPA.yml ps chatwoot

# Se não está "Up", ver logs
docker-compose -f docker-compose.productionUFPA.yml logs chatwoot

# Restart
docker-compose -f docker-compose.productionUFPA.yml restart chatwoot
```

### Erro de conectividade com PostgreSQL

```bash
# Verificar postgres
docker-compose -f docker-compose.productionUFPA.yml ps postgres-chatwoot

# Ver logs
docker-compose -f docker-compose.productionUFPA.yml logs postgres-chatwoot

# Verificar credenciais em docker-compose.productionUFPA.yml (linhas ~110-120)
```

### Widget não aparece no frontend

```bash
# Verificar console do navegador (F12)
# Procurar por erros de CORS ou SSL

# Certificado SSL inválido?
curl -s https://chatwoot.fasitech.cameta.ufpa.br | head

# Deve retornar HTML, não erro
```

### Certificado SSL inválido

```bash
# Regenerar certificado (na VM UFPA)
sudo certbot certonly --manual --preferred-challenges=dns \
  -d chatwoot.fasitech.cameta.ufpa.br

# Restart Nginx
docker-compose -f docker-compose.productionUFPA.yml restart nginx
```

---

## 📞 Suporte

**Arquivos de referência:**
- [`docker-compose.productionUFPA.yml`](docker-compose.productionUFPA.yml) — Config do Chatwoot
- [`CHATWOOT_DEPLOYMENT_GUIDE.md`](CHATWOOT_DEPLOYMENT_GUIDE.md) — Guia detalhado
- [`CHATWOOT_FIX_GUIDE.md`](CHATWOOT_FIX_GUIDE.md) — Problemas e soluções

**Documentação oficial:**
- [Chatwoot Docker Docs](https://docs.chatwoot.com/deployment/docker)
- [Chatwoot Installation](https://docs.chatwoot.com/deployment/deployment-guides)

---

## ✨ Pronto!

Após o deploy, você terá:
- ✅ Chat bot com escalação automática
- ✅ Dashboard Chatwoot em `https://chatwoot.fasitech.cameta.ufpa.br`
- ✅ Widget flutuante no FasiTech
- ✅ Banco de dados isolado (não compartilha com FasiTech)
- ✅ Suporte a múltiplas equipes (Secretaria, Diretor)

Qualquer problema, verifique os logs ou leia os guias detalhados acima!
