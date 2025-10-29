# Soluções para Erro 413 - Request Entity Too Large

## Problema
O erro `AxiosError: Request failed with status code 413` indica que o arquivo PDF é muito grande para o servidor aceitar.

## Soluções Implementadas

### 1. ✅ Streamlit - Aumentar Limite de Upload
```toml
# .streamlit/config.toml
[server]
maxUploadSize = 200  # 200MB (era sem limite definido)
```

### 2. ✅ Aplicação - Validação Melhorada
```python
# FormACC.py
MAX_FILE_SIZE_MB = 50  # Aumentado de 10MB para 50MB
```

### 3. 🔧 Nginx - Configuração do Servidor
```nginx
# nginx.conf ou virtual host
server {
    client_max_body_size 200M;
    client_body_timeout 300s;
    client_header_timeout 300s;
    client_body_buffer_size 128k;
}
```

### 4. 🔧 Apache - Se Usando Apache
```apache
# .htaccess ou virtual host
LimitRequestBody 209715200  # 200MB
```

## Como Aplicar no Servidor

### 1. Subir Arquivos Atualizados
```bash
rsync -avz /home/nees/Documents/VSCodigo/FasiTech/ user@servidor:/home/ubuntu/appStreamLit/
```

### 2. Configurar Nginx (Hostinger)
```bash
# Editar arquivo de configuração nginx
sudo nano /etc/nginx/sites-available/default

# Adicionar dentro do bloco server:
client_max_body_size 200M;
client_body_timeout 300s;

# Reiniciar nginx
sudo systemctl restart nginx
```

### 3. Reiniciar Streamlit
```bash
# Parar processo atual
pkill -f streamlit

# Iniciar novamente
cd /home/ubuntu/appStreamLit
python -m streamlit run src/app/main.py --server.port 8501 &
```

### 4. Testar Upload
1. Acesse a aplicação
2. Tente fazer upload do mesmo PDF que deu erro
3. Monitore logs para confirmar sucesso

## Limites Configurados

| Componente | Limite Anterior | Limite Atual |
|------------|----------------|--------------|
| FormACC.py | 10MB | 50MB |
| Streamlit config | Padrão (~200MB) | 200MB explícito |
| Nginx | Padrão (1MB) | 200MB |

## Verificação de Problemas

### Executar Diagnóstico
```bash
cd /home/ubuntu/appStreamLit
python scripts/verificar_dependencias_acc.py
```

### Verificar Logs Nginx
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Testar Manualmente
```bash
# Verificar tamanho do arquivo de teste
ls -lh /caminho/para/arquivo.pdf

# Se arquivo > 50MB, considere compressão:
# Use ferramentas online ou:
# gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed.pdf input.pdf
```

## Próximos Passos

1. **Imediato**: Aplicar configuração nginx e reiniciar serviços
2. **Teste**: Fazer upload do PDF que deu erro 413
3. **Monitoramento**: Acompanhar logs durante teste
4. **Backup**: Se necessário, implementar compressão automática de PDF

---
*Status: Configurações implementadas, aguardando aplicação no servidor*