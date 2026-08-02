# Guia de Deploy do Chatwoot — FasiTech

> ⚠️ **Status: Opção 1 já foi implementada** no `docker-compose.productionUFPA.yml`
> (serviços `chatwoot`, `postgres-chatwoot`, `redis-chatwoot` já existem no arquivo,
> com `SECRET_KEY_BASE` e senha do Postgres reais — diferentes dos placeholders
> mostrados no passo 1.1 abaixo, que ficou aqui só como referência histórica).
> Para deploy, use `bash scripts/deploy-chatwoot-ufpa.sh` (ver `DEPLOY_COMMANDS.md`
> ou `CHATWOOT_QUICK_START.md`) em vez de repetir os passos manuais desta seção.

## Problema Original (histórico)

**Chatwoot estava retornando 404** → o serviço não existia na VM UFPA.

O Nginx estava configurado para fazer proxy para `http://chatwoot:3000`, mas:
- ❌ Não havia container Chatwoot rodando
- ❌ Não havia serviço Chatwoot definido no `docker-compose.productionUFPA.yml`

---

## 2 Opções de Solução (histórico — Opção 1 foi a escolhida e já está aplicada)

### **Opção 1: Chatwoot via Docker Compose** ✅ ESCOLHIDA E JÁ APLICADA
Integrar Chatwoot como serviço Docker junto com o projeto.

**Vantagens:**
- Simples de manter
- Reutiliza a mesma rede Docker
- Facilita backups e migrations

**Passos:**

#### 1.1 Adicionar Chatwoot ao `docker-compose.productionUFPA.yml`

Adicione antes da seção `networks`:

```yaml
  # Chatwoot — Live Chat
  chatwoot:
    image: chatwoot/chatwoot:latest
    container_name: fasitech-chatwoot-prod
    environment:
      - RAILS_ENV=production
      - SECRET_KEY_BASE=your-secret-key-base-here
      - FRONTEND_URL=https://chatwoot.fasitech.cameta.ufpa.br
      - MAILER_SENDER_NAME=FasiTech
      - MAILER_SENDER_EMAIL=fasicuntins@ufpa.br
      - SMTP_ADDRESS=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USERNAME=fasicuntins@ufpa.br
      - SMTP_PASSWORD=${EMAIL_PASSWORD}
      - SMTP_AUTHENTICATION=login
      - SMTP_ENABLE_STARTTLS_AUTO=true
      - DATABASE_URL=postgresql://chatwoot:chatwoot_pass@postgres-chatwoot:5432/chatwoot
      - REDIS_URL=redis://redis-chatwoot:6379
    depends_on:
      - postgres-chatwoot
      - redis-chatwoot
    restart: unless-stopped
    networks:
      - fasitech-network
    volumes:
      - chatwoot_storage:/app/storage

  # PostgreSQL para Chatwoot
  postgres-chatwoot:
    image: postgres:15-alpine
    container_name: fasitech-postgres-chatwoot-prod
    environment:
      - POSTGRES_USER=chatwoot
      - POSTGRES_PASSWORD=chatwoot_pass
      - POSTGRES_DB=chatwoot
    restart: unless-stopped
    volumes:
      - postgres_chatwoot_data:/var/lib/postgresql/data
    networks:
      - fasitech-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatwoot"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis para Chatwoot
  redis-chatwoot:
    image: redis:7-alpine
    container_name: fasitech-redis-chatwoot-prod
    restart: unless-stopped
    volumes:
      - redis_chatwoot_data:/data
    networks:
      - fasitech-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### 1.2 Adicionar volumes no final do arquivo

```yaml
volumes:
  # ... volumes existentes ...
  chatwoot_storage:
  postgres_chatwoot_data:
  redis_chatwoot_data:
```

#### 1.3 Gerar SECRET_KEY_BASE

```bash
docker run --rm chatwoot/chatwoot:latest bundle exec rails secret
# Copie a saída e substitua em RAILS_ENV acima
```

#### 1.4 Deploy

```bash
# SSH na VM UFPA
ssh eltonss@172.16.28.198

# Pull das mudanças
cd /path/to/project
git pull

# Rebuild e restart
docker compose -p fasitech -f docker-compose.productionUFPA.yml down
docker compose -p fasitech -f docker-compose.productionUFPA.yml up -d --build

# Aguardar inicialização (pode levar 2-3 min)
docker compose -p fasitech -f docker-compose.productionUFPA.yml logs -f chatwoot

# Criar admin user (primeira vez)
docker compose -p fasitech -f docker-compose.productionUFPA.yml exec chatwoot bundle exec rake db:chatwoot_prepare
```

#### 1.5 Verificar se está rodando

```bash
curl -s https://chatwoot.fasitech.cameta.ufpa.br | head -20
# Deveria retornar HTML, não 404
```

---

### **Opção 2: Chatwoot Externo (Cloud/VPS Separada)**
Se Chatwoot já está rodando em outro servidor.

**Vantagens:**
- Menor uso de recursos da VM UFPA
- Independente do deploy FasiTech

**Passos:**

#### 2.1 Verificar se está rodando

```bash
# Substituir URL pela URL real do Chatwoot
curl -s https://seu-chatwoot-server.com/api/v1/accounts \
  -H "API-TOKEN: RQnCehNGnUYC7yjYxbFrr3t4" | jq .
```

#### 2.2 Atualizar configuração no `.env.production`

```bash
# Mude de:
CHATWOOT_API_URL=http://chatwoot:3000

# Para:
CHATWOOT_API_URL=https://seu-chatwoot-server.com
```

#### 2.3 Remover configuração de proxy no Nginx

Se não vai usar URL interna, pode remover o proxy do Chatwoot do `nginx.ufpa.conf`:

```nginx
# Remova esta seção se Chatwoot é externo:
server {
    listen 443 ssl;
    server_name chatwoot.fasitech.cameta.ufpa.br;
    # ...
    location / {
        proxy_pass http://chatwoot:3000;  # ← Remove isso
    }
}
```

Ou deixe apenas como proxy reverso seguro:

```nginx
# Mantenha como proxy reverso para o Chatwoot externo
location / {
    proxy_pass https://seu-chatwoot-server.com;
    proxy_set_header Host seu-chatwoot-server.com;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto https;
}
```

#### 2.4 Deploy

```bash
git add .env.production docker/nginx/nginx.ufpa.conf
git commit -m "fix: update chatwoot url to external server"
git push

# Na VM:
cd /path/to/project
git pull
docker compose -p fasitech -f docker-compose.productionUFPA.yml restart nginx
```

---

## Qual Escolher?

| Aspecto | Opção 1 (Docker) | Opção 2 (Externo) |
|--------|------------------|------------------|
| **Simplicidade** | Médio | Fácil |
| **Recursos** | 🔴 Usa mais (Postgres + Redis) | 🟢 Mínimo |
| **Manutenção** | Incluída no projeto | Terceiro gerencia |
| **Backup** | Fácil (volumes Docker) | Depende do provedor |
| **Escalabilidade** | Limitado à VM | Ilimitado |

**Recomendação:** Se a VM UFPA tem recursos (RAM, CPU), use **Opção 1** para manter tudo integrado. Senão, use **Opção 2**.

---

## Testes Pós-Deploy

```javascript
// No console do navegador (F12)

// 1. Verificar se página carrega
fetch('https://chatwoot.fasitech.cameta.ufpa.br')
  .then(r => console.log('Status:', r.status))
  .catch(e => console.error('Erro:', e));

// 2. Verificar se SDK carrega
console.log('SDK:', window.chatwootSDK ? '✅' : '❌');

// 3. Abrir widget
window.$chatwoot?.open();

// 4. API healthcheck
fetch('https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts', {
  headers: { 'API-TOKEN': 'RQnCehNGnUYC7yjYxbFrr3t4' }
}).then(r => r.json()).then(d => console.log('API:', d));
```

---

## Troubleshooting

### "Failed to fetch" ou 404
→ Chatwoot não está rodando. Verifique com `docker ps` ou `curl`.

### "Connection refused"
→ Chatwoot rodando mas proxy errado. Verifique `nginx.ufpa.conf`.

### "SSL certificate error"
→ Certificado inválido. Gere novo com Let's Encrypt.

### SDK não aparece
→ Verifique console (F12) para erros de CORS.

---

## Referências

- [Chatwoot Docker Setup](https://docs.chatwoot.com/deployment/docker)
- [Chatwoot Production Deployment](https://docs.chatwoot.com/deployment/deployment-guides)

