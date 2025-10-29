# 🚀 Guia Rápido de Deploy na VM

## 📋 **Pré-requisitos na VM**

Certifique-se de que os seguintes arquivos existem em `/home/ubuntu/appStreamLit/`:

1. ✅ `.env.production` - com `API_BASE_URL=https://www.fasitech.com.br`
2. ✅ `docker-compose.production.yml`
3. ✅ `docker/Dockerfile`
4. ✅ `docker/Dockerfile.api`
5. ✅ `docker/nginx/nginx.conf`

## 🚀 **Deploy Completo (Recomendado)**

### **Passo 1: Enviar código para VM**

```bash
# No seu computador local
rsync -avz --progress \
    --exclude 'venv/' --exclude '.git/' --exclude '__pycache__/' \
    -e "ssh" \
    /home/nees/Documents/VSCodigo/FasiTech/ \
    root@72.60.6.113:/home/ubuntu/appStreamLit
```

### **Passo 2: Deploy com Docker Compose**

```bash
# Conectar na VM
ssh root@72.60.6.113

# Ir para o diretório
cd /home/ubuntu/appStreamLit/

# Deploy completo (API + Streamlit + Nginx)
sudo docker-compose -f docker-compose.production.yml down
sudo docker-compose -f docker-compose.production.yml up -d --build
```

### **Passo 3: Verificar Status**

```bash
# Ver containers rodando
sudo docker-compose -f docker-compose.production.yml ps

# Ver logs em tempo real
sudo docker-compose -f docker-compose.production.yml logs -f

# Testar endpoints
curl http://localhost/api/v1/dados-sociais/download
curl http://localhost/
```

---

## 🔧 **Deploy Manual (Controle Individual)**

Se preferir iniciar cada serviço separadamente:

### **1. Parar containers antigos**
```bash
cd /home/ubuntu/appStreamLit/
sudo docker stop fasi_container fasi_api_container 2>/dev/null
sudo docker rm fasi_container fasi_api_container 2>/dev/null
```

### **2. Iniciar API FastAPI**
```bash
# Construir imagem da API
sudo docker build -f docker/Dockerfile.api -t fasi_api .

# Executar container da API
sudo docker run -d \
  --name fasi_api_container \
  -p 8000:8000 \
  --env-file .env.production \
  --network fasi-net \
  fasi_api
  
# Verificar logs
sudo docker logs -f fasi_api_container
```

### **3. Iniciar Streamlit**
```bash
# Construir imagem do Streamlit
sudo docker build -f docker/Dockerfile -t fasi_app .

# Executar container do Streamlit
sudo docker run -d \
  --name fasi_container \
  -p 8501:8501 \
  --env-file .env.production \
  --network fasi-net \
  fasi_app

# Verificar logs
sudo docker logs -f fasi_container
```

### **4. Nginx (se necessário)**
```bash
sudo docker stop nginx-proxy 2>/dev/null
sudo docker rm nginx-proxy 2>/dev/null

sudo docker run -d \
  --name nginx-proxy \
  -p 80:80 \
  -p 443:443 \
  --network fasi-net \
  -v /home/ubuntu/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /home/ubuntu/certbot/conf:/etc/letsencrypt:ro \
  -v /home/ubuntu/certbot/www:/var/www/certbot:ro \
  nginx
```

---

## 📊 **Comandos Úteis**

### **Logs e Monitoramento**
```bash
# Ver logs da API
sudo docker logs -f fasi_api_container

# Ver logs do Streamlit
sudo docker logs -f fasi_container

# Ver logs do Nginx
sudo docker logs -f nginx-proxy

# Ver últimas 100 linhas
sudo docker logs --tail 100 fasi_api_container
```

### **Gerenciamento de Containers**
```bash
# Listar todos os containers
sudo docker ps -a

# Parar todos os containers do FasiTech
sudo docker stop fasi_container fasi_api_container nginx-proxy

# Remover todos os containers do FasiTech
sudo docker rm fasi_container fasi_api_container nginx-proxy

# Reiniciar apenas a API
sudo docker restart fasi_api_container

# Reiniciar apenas o Streamlit
sudo docker restart fasi_container
```

### **Limpeza e Manutenção**
```bash
# Remover imagens não utilizadas
sudo docker image prune -a

# Remover volumes não utilizados
sudo docker volume prune

# Ver uso de espaço
sudo docker system df

# Limpeza completa (cuidado!)
sudo docker system prune -a --volumes
```

---

## 🧪 **Testes Pós-Deploy**

### **1. Testar Streamlit**
```bash
curl http://localhost:8501
# ou
curl http://www.fasitech.com.br
```

### **2. Testar API**
```bash
# Docs da API
curl http://localhost:8000/docs
# ou
curl http://www.fasitech.com.br/api/docs

# Endpoint de download
curl http://www.fasitech.com.br/api/v1/dados-sociais/download
```

### **3. Testar Downloads**
```bash
# Download CSV
curl -o test.csv http://www.fasitech.com.br/api/v1/dados-sociais/download/csv

# Download Excel
curl -o test.xlsx http://www.fasitech.com.br/api/v1/dados-sociais/download/excel
```

---

## ⚠️ **Troubleshooting**

### **Problema: Container não inicia**
```bash
# Ver logs de erro
sudo docker logs fasi_container
sudo docker logs fasi_api_container

# Verificar variáveis de ambiente
sudo docker exec fasi_container env | grep API_BASE_URL
```

### **Problema: Porta já em uso**
```bash
# Ver o que está usando a porta
sudo lsof -i :8501
sudo lsof -i :8000

# Parar processo
sudo kill -9 <PID>
```

### **Problema: Rede não funciona**
```bash
# Verificar rede
sudo docker network ls
sudo docker network inspect fasi-net

# Recriar rede se necessário
sudo docker network rm fasi-net
sudo docker network create fasi-net
```

---

## 🎯 **Resumo dos Comandos Essenciais**

```bash
# Deploy rápido (tudo de uma vez)
cd /home/ubuntu/appStreamLit/ && \
sudo docker-compose -f docker-compose.production.yml up -d --build

# Ver status
sudo docker-compose -f docker-compose.production.yml ps

# Ver logs
sudo docker-compose -f docker-compose.production.yml logs -f

# Parar tudo
sudo docker-compose -f docker-compose.production.yml down

# Reiniciar tudo
sudo docker-compose -f docker-compose.production.yml restart
```

---

**📞 Em caso de problemas, verifique:**
1. ✅ Arquivo `.env.production` existe e tem `API_BASE_URL` correto
2. ✅ Rede `fasi-net` existe: `sudo docker network ls`
3. ✅ Portas 8000 e 8501 estão livres
4. ✅ Logs dos containers para ver erros