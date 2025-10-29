# 🔒 Configuração SSL/HTTPS para www.fasitech.com.br

## 📋 Pré-requisitos

1. **Domínio configurado** - DNS apontando para o servidor
2. **Nginx instalado** no servidor
3. **Certbot** (Let's Encrypt) instalado

## 🚀 Passos para Configurar HTTPS

### 1. **Instalar Certbot (no servidor)**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### 2. **Obter Certificado SSL**
```bash
# Gerar certificado para o domínio
sudo certbot --nginx -d fasitech.com.br -d www.fasitech.com.br

# Responder às perguntas:
# - Email para notificações
# - Aceitar termos de uso
# - Compartilhar email (opcional)
# - Redirecionar HTTP para HTTPS (recomendado: Yes)
```

### 3. **Verificar Renovação Automática**
```bash
# Testar renovação
sudo certbot renew --dry-run

# Ver status dos certificados
sudo certbot certificates
```

### 4. **Configurar Cron para Renovação Automática**
```bash
# Adicionar ao crontab
sudo crontab -e

# Adicionar linha para renovar certificados às 2h da manhã diariamente
0 2 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

## 🌐 URLs Finais Após SSL

### **Site Principal (Streamlit)**
```
https://www.fasitech.com.br/
```

### **API FastAPI**
```
https://www.fasitech.com.br/api/
https://www.fasitech.com.br/api/health
https://www.fasitech.com.br/api/dados-sociais
https://www.fasitech.com.br/api/dados-sociais/estatisticas
```

### **Documentação da API**
```
https://www.fasitech.com.br/api/docs     (Swagger UI)
https://www.fasitech.com.br/api/redoc    (ReDoc)
```

## 🧪 Exemplos de Uso da API

### **Via curl**
```bash
# Health check
curl "https://www.fasitech.com.br/api/health"

# Dados sociais (com autenticação)
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "https://www.fasitech.com.br/api/dados-sociais?pagina=1&por_pagina=10"

# Estatísticas
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "https://www.fasitech.com.br/api/dados-sociais/estatisticas"

# Filtros avançados
curl -H "Authorization: Bearer fasitech_api_2024_social_data" \
     "https://www.fasitech.com.br/api/dados-sociais?cor_etnia=Pardo&trabalho=Sim"
```

### **Via JavaScript (Frontend)**
```javascript
// Função para buscar dados sociais
async function buscarDadosSociais(pagina = 1, filtros = {}) {
    const params = new URLSearchParams({
        pagina: pagina,
        por_pagina: 20,
        ...filtros
    });
    
    const response = await fetch(`https://www.fasitech.com.br/api/dados-sociais?${params}`, {
        headers: {
            'Authorization': 'Bearer fasitech_api_2024_social_data',
            'Content-Type': 'application/json'
        }
    });
    
    if (!response.ok) {
        throw new Error(`Erro: ${response.status}`);
    }
    
    return await response.json();
}

// Exemplo de uso
buscarDadosSociais(1, { cor_etnia: 'Pardo', trabalho: 'Sim' })
    .then(dados => {
        console.log(`Total de registros: ${dados.total}`);
        console.log('Dados:', dados.dados);
    })
    .catch(error => console.error('Erro:', error));
```

### **Via Python (Cliente)**
```python
import requests

# Configuração
API_BASE = "https://www.fasitech.com.br/api"
API_KEY = "fasitech_api_2024_social_data"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Buscar dados sociais
response = requests.get(f"{API_BASE}/dados-sociais", headers=headers, params={
    "pagina": 1,
    "por_pagina": 10,
    "cor_etnia": "Pardo"
})

if response.status_code == 200:
    dados = response.json()
    print(f"Total de registros: {dados['total']}")
    for registro in dados['dados']:
        print(f"Matrícula: {registro['matricula']}, Período: {registro['periodo']}")
else:
    print(f"Erro: {response.status_code} - {response.text}")
```

## 🔧 Troubleshooting SSL

### **Problema: Certificado não funciona**
```bash
# Verificar configuração Nginx
sudo nginx -t

# Ver logs do Nginx
sudo tail -f /var/log/nginx/error.log

# Verificar certificado
openssl s_client -connect www.fasitech.com.br:443 -servername www.fasitech.com.br
```

### **Problema: Renovação automática não funciona**
```bash
# Testar renovação manualmente
sudo certbot renew --dry-run

# Ver logs do certbot
sudo journalctl -u certbot
```

## 📊 Monitoramento

### **Verificar se tudo está funcionando**
```bash
# Status dos serviços
sudo systemctl status nginx
sudo systemctl status fasitech-api

# Logs da API
sudo tail -f /var/log/fasitech/api.log

# Teste de conectividade
curl -I https://www.fasitech.com.br/api/health
```