# 🚀 Como Executar o FasiTech Forms

## Pré-requisitos

✅ Python 3.11+ instalado  
✅ Arquivo `.env` configurado na raiz do projeto  
✅ Google Sheets e Drive configurados (veja `GOOGLE_SETUP.md`)

## Passo a Passo

### 1. Ativar Ambiente Virtual

```bash
# Se ainda não criou o ambiente virtual
python3 -m venv venv

# Ativar o ambiente
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

O arquivo `.env` já está configurado com:

- ✅ `GOOGLE_CLOUD_CREDENTIALS_BASE64` - Credenciais da conta de serviço
- ✅ `EMAIL_SENDER` - E-mail remetente
- ✅ `EMAIL_PASSWORD` - Senha de app do Gmail

### 4. Configurar Secrets do Streamlit

O arquivo `.streamlit/secrets.toml` já está configurado com:

- ✅ `drive_folder_id` - ID da pasta do Google Drive
- ✅ `sheet_id` - ID da planilha do Google Sheets
- ✅ `notification_recipients` - Lista de e-mails para notificações

### 5. Executar a Aplicação

**Opção A: Script automatizado (Recomendado)**

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Opção B: Manualmente**

```bash
export PYTHONPATH="${PWD}:${PYTHONPATH}"
streamlit run src/app/main.py
```

### 6. Acessar no Navegador

A aplicação estará disponível em:

```
http://localhost:8501
```

## 📋 Testando o Formulário ACC

1. Clique em "Formulário ACC"
2. Preencha os campos:
   - Nome completo
   - Matrícula
   - E-mail institucional
   - Turma
3. Anexe um arquivo PDF (máx 10 MB)
4. Clique em "Enviar para análise"

### O que acontece nos bastidores:

1. ✅ Arquivo é enviado para o Google Drive
2. ✅ Registro é adicionado à planilha do Google Sheets
3. ✅ E-mail de notificação é enviado para coordenação
4. ✅ Confirmação é exibida na tela

## 🔍 Verificando os Resultados

### Google Drive
- Acesse: `https://drive.google.com/drive/folders/17GiNzOq0yWsvDNKlIx5672ya_qviGOto`
- Verifique se o arquivo PDF foi enviado

### Google Sheets
- Acesse: `https://docs.google.com/spreadsheets/d/1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`
- Confirme se uma nova linha foi adicionada com os dados

### E-mail
- Verifique a caixa de entrada de: `eltonss@ufpa.br`
- Deve haver um e-mail com assunto "Nova submissão ACC"

## ⚠️ Troubleshooting

### Erro: "Credenciais não encontradas"
```bash
# Verifique se o .env está no diretório raiz
ls -la .env

# Confirme que GOOGLE_CLOUD_CREDENTIALS_BASE64 está definido
grep GOOGLE_CLOUD_CREDENTIALS_BASE64 .env
```

### Erro: "Permission denied" no Google
- Verifique se compartilhou a planilha/pasta com: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com`
- Veja instruções completas em `GOOGLE_SETUP.md`

### Erro: ModuleNotFoundError
```bash
# Certifique-se de estar no diretório raiz do projeto
cd /home/eltonss/Documents/VS\ CODE/FasiTech

# Configure o PYTHONPATH
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Execute novamente
streamlit run src/app/main.py
```

### E-mail não está sendo enviado
```bash
# Verifique se EMAIL_PASSWORD está configurado
grep EMAIL_PASSWORD .env

# A senha deve ser uma "Senha de app" do Gmail
# Gere em: https://myaccount.google.com/apppasswords
```

## 📊 Logs e Debug

Os logs aparecem no terminal onde você executou o Streamlit:

- ✅ Upload para Drive: `Arquivo 'nome.pdf' enviado com ID: ...`
- ✅ Escrita em Sheets: `1 linha(s) adicionada(s) à planilha`
- ✅ Envio de e-mail: `E-mail enviado com sucesso para: ...`

## 🛑 Parar a Aplicação

Pressione `Ctrl+C` no terminal onde o Streamlit está rodando.

## 🔄 Reiniciar Após Mudanças

Se você modificar o código:

1. Pressione `Ctrl+C` para parar
2. Execute novamente: `./scripts/start.sh` ou `streamlit run src/app/main.py`
3. Ou use o botão "Rerun" no navegador (tecla `R`)
