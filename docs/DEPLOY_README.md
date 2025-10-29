# 🚀 Guia de Deploy - FasiTech para Produção (VM)

## ⚠️ **Problema Identificado e Solucionado**

**Problema**: O link de download (`http://localhost:8000`) não funciona quando hospedado na VM porque o endereço localhost só funciona no desenvolvimento local.

**Solução**: Sistema de URLs dinâmicas com variáveis de ambiente que se adaptam automaticamente ao ambiente (desenvolvimento vs produção).

---

## 🔧 **Alterações Realizadas**

### 1. **Variáveis de Ambiente para URLs**
- ✅ **`.env`**: `API_BASE_URL=http://localhost:8000` (desenvolvimento)
- ✅ **`.env.production`**: `API_BASE_URL=https://www.fasitech.com.br` (produção)

### 2. **Código Dinâmico**
- ✅ **`src/app/main.py`**: Modificado para usar `os.getenv('API_BASE_URL')` em vez de URL hardcoded
- ✅ **Link dinâmico**: Muda automaticamente entre desenvolvimento e produção

### 3. **Configuração Docker**
- ✅ **`docker-compose.yml`**: Para desenvolvimento
- ✅ **`docker-compose.production.yml`**: Para produção na VM
- ✅ **`docker/Dockerfile.api`**: Dockerfile específico para API FastAPI
- ✅ **Nginx**: Proxy reverso para servir tudo na mesma porta

---

## 🏗️ **Arquitetura na VM**

```
Internet → Nginx (porta 80/443) → {
    /              → Streamlit (porta 8501)
    /api/          → FastAPI (porta 8000)
}
```

**Vantagens**:
- ✅ Tudo acessível via `www.fasitech.com.br`
- ✅ Downloads funcionam em `www.fasitech.com.br/api/v1/dados-sociais/download`
- ✅ Sem problemas de CORS ou portas diferentes
- ✅ HTTPS pronto para configurar

---

## 🚀 **Como Fazer o Deploy na VM**

### **Passo 1: Preparar a VM**
```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### **Passo 2: Enviar Código para VM**
```bash
# Via Git (recomendado)
git clone https://github.com/eltonsarmanho/FasiTech.git
cd FasiTech

# Ou via SCP
scp -r . user@vm-ip:/path/to/fasitech/
```

### **Passo 3: Configurar Variáveis de Produção**
```bash
# Editar arquivo de produção
nano .env.production

# Definir URL real da VM
API_BASE_URL=https://www.fasitech.com.br
# (ou http://IP-DA-VM se não tiver domínio)
```

### **Passo 4: Executar Deploy**
```bash
# Executar script de deploy automático
./deploy.sh

# OU manualmente:
docker-compose -f docker-compose.production.yml up -d --build
```

### **Passo 5: Verificar Funcionamento**
```bash
# Verificar containers
docker-compose -f docker-compose.production.yml ps

# Testar endpoints
curl http://localhost/api/v1/dados-sociais/download
curl http://localhost/
```

---

## 🔒 **Configurar HTTPS (Recomendado)**

### **1. Com Let's Encrypt (Gratuito)**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d www.fasitech.com.br -d fasitech.com.br

# Certificados ficam em /etc/letsencrypt/
```

### **2. Modificar nginx.conf**
```bash
# Descomentar seção HTTPS no arquivo
nano docker/nginx/nginx.conf

# Apontar para certificados Let's Encrypt
ssl_certificate /etc/letsencrypt/live/www.fasitech.com.br/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/www.fasitech.com.br/privkey.pem;
```

### **3. Reiniciar com HTTPS**
```bash
# Atualizar docker-compose.production.yml
API_BASE_URL=https://www.fasitech.com.br

# Reiniciar
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d
```

---

## 📋 **Comandos Úteis na VM**

```bash
# Ver logs em tempo real
docker-compose -f docker-compose.production.yml logs -f

# Ver logs de um serviço específico
docker-compose -f docker-compose.production.yml logs -f streamlit
docker-compose -f docker-compose.production.yml logs -f api

# Reiniciar serviços
docker-compose -f docker-compose.production.yml restart

# Parar tudo
docker-compose -f docker-compose.production.yml down

# Atualizar código e reiniciar
git pull
docker-compose -f docker-compose.production.yml up -d --build
```

---

## ✅ **Teste Final na VM**

1. **Streamlit**: `http://www.fasitech.com.br` ✅
2. **API Docs**: `http://www.fasitech.com.br/api/docs` ✅  
3. **Download Page**: `http://www.fasitech.com.br/api/v1/dados-sociais/download` ✅
4. **CSV Download**: `http://www.fasitech.com.br/api/v1/dados-sociais/download/csv` ✅
5. **Excel Download**: `http://www.fasitech.com.br/api/v1/dados-sociais/download/excel` ✅

---

## 🎯 **Resultado Final**

- ✅ **Downloads funcionam** na VM
- ✅ **URL única** para tudo (www.fasitech.com.br)  
- ✅ **LGPD compliant** (dados anonimizados)
- ✅ **Pronto para HTTPS**
- ✅ **Escalável** e containerizado

**🎉 Sistema totalmente funcional para produção!**