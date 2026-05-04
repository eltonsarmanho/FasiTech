# 🔄 Guia de Atualização do Sistema

## 📋 **Fluxo Completo de Atualização**

### **1️⃣ Fazer Alterações no Código (Local)**
```bash
# Editar arquivos necessários no VSCode
# Exemplo: src/app/pages/FormACC.py, src/services/*, etc.
```

---

### **2️⃣ Sincronizar Código para VM**
```bash
# No seu computador local
rsync -avz --progress \
    --exclude 'venv/' --exclude 'env/' --exclude '.venv/' --exclude '.git/' \
    --exclude '.gitignore' --exclude '__pycache__/' --exclude '*.pyc' \
    --exclude '*.pyo' --exclude '*.pyd' --exclude '.Python' --exclude '*.so' \
    --exclude '*.egg' --exclude '*.egg-info/' --exclude 'dist/' \
    --exclude 'build/' --exclude '.pytest_cache/' --exclude '.vscode/' \
    --exclude '.idea/' --exclude '*.log' --exclude '*.key' \
    --exclude '.DS_Store' --exclude 'Thumbs.db' --exclude '*~' \
    -e "ssh" \
    /home/nees/Documents/VSCodigo/FasiTech/ \
    root@72.60.6.113:/home/ubuntu/appStreamLit
```

---

### **3️⃣ Atualizar na VM**

#### **🔹 Opção A: Atualização Rápida (sem rebuild)**
Use quando alterar **apenas código Python** (páginas, serviços, modelos):

```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/

# Reiniciar apenas os containers (sem recompilar)
sudo docker compose -f docker-compose.production.yml restart streamlit
sudo docker compose -f docker-compose.production.yml restart api

# Ver logs em tempo real
sudo docker compose -f docker-compose.production.yml logs -f
```

**⏱️ Tempo:** ~5 segundos

---

#### **🔹 Opção B: Atualização Completa (com rebuild)**
Use quando alterar **Dockerfile, requirements.txt, configurações do sistema**:

```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/

# Rebuild completo (API + Streamlit)
sudo docker compose -f docker-compose.production.yml up -d --build

# Ver logs
sudo docker compose -f docker-compose.production.yml logs -f
```

**⏱️ Tempo:** ~30-60 segundos

---

#### **🔹 Opção C: Atualizar Apenas Nginx**
Use quando alterar **nginx.conf**:

```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/

# Reiniciar apenas o Nginx
sudo docker-compose -f docker-compose.production.yml restart nginx

# Ver logs do Nginx
sudo docker logs -f fasitech-nginx-prod
```

**⏱️ Tempo:** ~2 segundos

---

#### **🔹 Opção D: Atualizar Apenas Streamlit**
Use quando alterar **páginas, formulários, interface**:

```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/

# Reiniciar apenas o Streamlit
sudo docker-compose -f docker-compose.production.yml restart streamlit

# Ver logs do Streamlit
sudo docker logs -f fasitech-streamlit-prod
```

**⏱️ Tempo:** ~5 segundos

---

#### **🔹 Opção E: Atualizar Apenas API**
Use quando alterar **rotas da API, webhooks**:

```bash
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/

# Reiniciar apenas a API
sudo docker-compose -f docker-compose.production.yml restart api

# Ver logs da API
sudo docker logs -f fasitech-api-prod
```

**⏱️ Tempo:** ~5 segundos

---

## 🎯 **Comandos Úteis do Dia a Dia**

### **Ver Status dos Containers**
```bash
sudo docker-compose -f docker-compose.production.yml ps
```

### **Ver Logs de Todos os Serviços**
```bash
# Logs em tempo real
sudo docker-compose -f docker-compose.production.yml logs -f

# Ver últimas 100 linhas
sudo docker-compose -f docker-compose.production.yml logs --tail 100

# Ver logs de um serviço específico
sudo docker logs -f fasitech-streamlit-prod
sudo docker logs -f fasitech-api-prod
sudo docker logs -f fasitech-nginx-prod
```

### **Reiniciar Tudo (Emergência)**
```bash
sudo docker-compose -f docker-compose.production.yml restart
```

### **Parar Tudo**
```bash
sudo docker-compose -f docker-compose.production.yml down
```

### **Iniciar Tudo**
```bash
sudo docker-compose -f docker-compose.production.yml up -d
```

---

## 📊 **Matriz de Decisão: Qual Comando Usar?**

| **O que você alterou?** | **Comando necessário** | **Tempo** |
|-------------------------|------------------------|-----------|
| Página Streamlit (`.py` em `src/app/pages/`) | `restart streamlit` | 5s |
| Serviço/lógica (`src/services/`, `src/models/`) | `restart streamlit` e `restart api` | 10s |
| Rota da API (`api/routes/`) | `restart api` | 5s |
| `requirements.txt` ou dependências | `up -d --build` | 60s |
| `Dockerfile` ou `Dockerfile.api` | `up -d --build` | 60s |
| `nginx.conf` | `restart nginx` | 2s |
| `docker-compose.production.yml` | `down` + `up -d` | 30s |
| Configuração `.env.production` | `restart` (todos) | 15s |
| Arquivos de credenciais/config | `restart` (todos) | 15s |

---

## 🚨 **Troubleshooting**

### **Problema: Site não atualizou após restart**
```bash
# Fazer rebuild forçado
sudo docker-compose -f docker-compose.production.yml up -d --force-recreate --build
```

### **Problema: Erro 502 Bad Gateway**
```bash
# Verificar se API e Streamlit estão rodando
sudo docker-compose -f docker-compose.production.yml ps

# Ver logs de erro
sudo docker-compose -f docker-compose.production.yml logs
```

### **Problema: Container não inicia**
```bash
# Ver logs de erro específicos
sudo docker logs fasitech-streamlit-prod
sudo docker logs fasitech-api-prod

# Verificar health checks
sudo docker inspect fasitech-api-prod | grep -A 10 Health
```

### **Problema: Porta ocupada**
```bash
# Ver o que está usando a porta
sudo lsof -i :80
sudo lsof -i :443
sudo lsof -i :8501
sudo lsof -i :8000

# Parar tudo e reiniciar
sudo docker-compose -f docker-compose.production.yml down
sudo docker-compose -f docker-compose.production.yml up -d
```

### **Problema: Rede não funciona**
```bash
# Verificar rede
sudo docker network ls
sudo docker network inspect appstreamlit_fasitech-network

# Recriar tudo (último recurso)
sudo docker-compose -f docker-compose.production.yml down
sudo docker-compose -f docker-compose.production.yml up -d
```

---

## 🎯 **Fluxo de Atualização Recomendado (95% dos casos)**

```bash
# 1. No seu computador (sincronizar)
rsync -avz --progress --exclude 'venv/' --exclude '.git/' --exclude '__pycache__/' \
    -e "ssh" /home/nees/Documents/VSCodigo/FasiTech/ root@72.60.6.113:/home/ubuntu/appStreamLit

# 2. Na VM (reiniciar serviços)
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit/
sudo docker-compose -f docker-compose.production.yml restart streamlit api

# 3. Verificar (ver logs)
sudo docker-compose -f docker-compose.production.yml logs -f streamlit
```

**Pressione `Ctrl+C` para sair dos logs.**

---

## 📝 **Checklist Pós-Atualização**

- [ ] Acessar https://www.fasitech.com.br e verificar se carrega
- [ ] Testar um formulário (ex: FormACC)
- [ ] Verificar se a API está respondendo: `curl https://www.fasitech.com.br/api/health`
- [ ] Verificar logs para erros: `sudo docker-compose -f docker-compose.production.yml logs --tail 50`
- [ ] Testar download de dados: https://www.fasitech.com.br/api/v1/dados-sociais/download

---

## 🔐 **Renovação de Certificado SSL (Certbot)**

O certificado SSL expira a cada 90 dias. Para renovar:

```bash
ssh root@72.60.6.113

# Renovar certificado
sudo certbot renew

# Reiniciar Nginx para aplicar novo certificado
cd /home/ubuntu/appStreamLit/
sudo docker-compose -f docker-compose.production.yml restart nginx
```

**Dica:** Configure um cronjob para renovação automática!

---

**📞 Dúvidas?** Consulte o `GUIA_DEPLOY_VM.md` para informações detalhadas de deploy.
