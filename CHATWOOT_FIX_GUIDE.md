# Guia de Correção — Chatwoot não se comunica com Frontend

## Problemas Identificados

### 1. ❌ **Certificado SSL Incorreto (CRÍTICO)**
**Arquivo:** `docker/nginx/nginx.ufpa.conf` (linhas 187-188)

O Chatwoot estava usando o certificado do **N8N** em vez do seu próprio:
```nginx
ssl_certificate /etc/letsencrypt/live/n8n.fasitech.cameta.ufpa.br/fullchain.pem;  # ❌ ERRADO
```

**Resultado:** Browser rejeita o certificado SSL como inválido, impedindo que o script `sdk.js` seja carregado.

**✅ Corrigido:** Mudado para usar o certificado correto do Chatwoot.

---

### 2. ❌ **Falta de Headers CORS**
O Nginx não estava retornando headers `Access-Control-Allow-Origin` no Chatwoot.

**Resultado:** Requisições cross-origin do frontend para Chatwoot são bloqueadas pelo browser.

**✅ Corrigido:** Adicionados headers CORS na configuração do nginx.

---

### 3. ❌ **Carregamento de SDK Frágil**
O `ChatWidget.tsx` carregava o SDK de forma inadequada (sem tratamento de erro, sem retry).

**✅ Corrigido:** Implementado loading robusto com:
- Promise-based loading
- Retry automático
- Melhor tratamento de erros
- Timeout de 10s

---

### 4. ❌ **SDK não carregava automaticamente**
O widget só aparecia após escalação (`state === 'escalated'`).

**✅ Corrigido:** Adicionado script global no `index.html` que carrega o SDK automaticamente.

---

## Passos para Implementar a Correção

### Passo 1: Certificado SSL para Chatwoot (automático)

O DNS de `chatwoot.fasitech.cameta.ufpa.br` já aponta para o IP público da VM
(mesmo IP usado por `n8n.fasitech.cameta.ufpa.br` e `www.fasitech.com.br`), e a
porta 80 já está acessível — então o desafio HTTP-01 (webroot) do Let's Encrypt
funciona sem passos manuais. **Não use `--preferred-challenges=dns`** (exigiria
criar registros TXT manualmente); o método correto é webroot, igual ao já usado
para os outros domínios deste projeto (ver `docker/nginx/nginx.ufpa.bootstrap.conf`).

O script `scripts/deploy-chatwoot-ufpa.sh` já faz isso automaticamente, reaproveitando
o `scripts/ufpa-issue-cert.sh` que já é usado para `fasitech.cameta.ufpa.br`:
1. Sobe o nginx com `nginx.ufpa.bootstrap.conf` — uma config mínima que só serve o
   desafio ACME (não referencia nenhum certificado, então nunca falha ao subir).
2. Roda o certbot **dentro de um container** (`certbot/certbot`, via `docker run`) —
   não precisa instalar certbot no host.
3. Troca o nginx de volta para a config completa (`nginx.ufpa.conf`) assim que o
   certificado é emitido, e testa/recarrega com `nginx -t` + `nginx -s reload`.

A renovação futura já é coberta pelo cron existente (`scripts/ufpa-renew-cert.sh`),
que renova todos os certificados emitidos — nada extra a configurar.

Se quiser rodar manualmente para depurar (mesmo mecanismo, domínio explícito):

```bash
# Na VM UFPA, na raiz do projeto
DOMAIN=chatwoot.fasitech.cameta.ufpa.br bash scripts/ufpa-issue-cert.sh

# Verificar certificados existentes
sudo ls -la /etc/letsencrypt/live/
```

**IMPORTANTE:** Confirme que existe:
- `/etc/letsencrypt/live/chatwoot.fasitech.cameta.ufpa.br/fullchain.pem`
- `/etc/letsencrypt/live/chatwoot.fasitech.cameta.ufpa.br/privkey.pem`

---

### Passo 2: Fazer Deploy das Alterações

```bash
# 1. Commit das mudanças
git add docker/nginx/nginx.ufpa.conf frontend/index.html frontend/src/features/diretor-virtual/ChatWidget.tsx
git commit -m "fix: chatwoot ssl certificate and cors headers, improve sdk loading"

# 2. Push para produção
git push origin main

# 3. SSH na VM UFPA
ssh eltonss@172.16.28.198

# 4. Pull das alterações
cd /home/eltonss/FasiTech  # Ou o diretório do seu projeto
git pull origin main

# 5. Rebuild e restart dos containers
docker-compose -f docker-compose.productionUFPA.yml down
docker-compose -f docker-compose.productionUFPA.yml up -d --build

# 6. Verificar status
docker-compose -f docker-compose.productionUFPA.yml ps
docker-compose -f docker-compose.productionUFPA.yml logs nginx
```

---

### Passo 3: Testar Conectividade

**No navegador, abra o console (F12) e execute:**

```javascript
// 1. Verificar se SDK está carregado
console.log('SDK disponível?', window.chatwootSDK ? 'SIM ✅' : 'NÃO ❌');

// 2. Testar acesso ao endpoint do Chatwoot
fetch('https://chatwoot.fasitech.cameta.ufpa.br/api/v1/accounts', {
  headers: { 'Accept': 'application/json' }
}).then(r => r.text().then(t => console.log('Chatwoot status:', r.status, t)))
  .catch(e => console.error('Erro:', e));

// 3. Se SDK está carregado, abrir o widget
if (window.$chatwoot) {
  window.$chatwoot.open();
  console.log('Widget aberto ✅');
} else {
  console.log('$chatwoot não disponível ❌');
}
```

---

## Checklist de Verificação

- [ ] Certificado SSL do Chatwoot existe e é válido
- [ ] Nginx foi reloadado após mudanças em `nginx.ufpa.conf`
- [ ] Frontend foi rebuilt e deployado
- [ ] Widget aparece automaticamente na página
- [ ] Console do navegador não mostra erros de certificado
- [ ] Console mostra `SDK disponível? SIM ✅`
- [ ] Widget abre quando clicado no botão flutuante
- [ ] Ao escalar para humano, Chatwoot recebe a conversa

---

## Possíveis Erros Remanescentes

### "Failed to fetch" ou "net::ERR_CERT_AUTHORITY_INVALID"
→ Certificado SSL está inválido. Verifique os arquivos em `/etc/letsencrypt/live/chatwoot.fasitech.cameta.ufpa.br/`.

### "Cross-Origin Request Blocked"
→ Headers CORS não estão sendo retornados. Verifique se o nginx recarregou após as mudanças:
```bash
docker-compose -f docker-compose.productionUFPA.yml restart nginx
```

### "window.chatwootSDK is undefined"
→ SDK ainda não foi carregado. Verifique:
- URL do SDK em `CHATWOOT_BASE_URL` está correta
- Certificado SSL está válido
- Chatwoot está rodando em `chatwoot:3000`

### Widget não abre quando clicado
→ Verifique se `window.$chatwoot` está definido:
```javascript
console.log('$chatwoot:', window.$chatwoot);
```

---

## Referência de Configuração

**Tokens e URLs (do widget fornecido):**
- Base URL: `https://chatwoot.fasitech.cameta.ufpa.br`
- Website Token: `oUy6xunsEJMzcXDvzscMHj7M`
- Tipo: `standard`
- Posição: `right`

Essas valores estão codificados em:
1. `frontend/index.html` (global)
2. `frontend/src/features/diretor-virtual/ChatWidget.tsx` (componente)

Se precisar atualizar o token ou URL, altere em ambos os arquivos.

---

## Documentação Útil

- [Chatwoot SDK Documentation](https://www.chatwoot.com/docs/product/channels/api/pre-chat-forms)
- [Nginx CORS Configuration](https://enable-cors.org/server_nginx.html)
- [Let's Encrypt Certificate Management](https://certbot.eff.org/)

