# FasiTech Forms Platform

Solução moderna de formulários web com Streamlit e backend FastAPI, rodando em EC2, com integrações para Google Drive, Google Sheets e envio de e-mails.

## 🎯 Funcionalidades

- ✅ **Portal centralizado** com múltiplos formulários
- ✅ **Formulário ACC** para atividades complementares curriculares
- ✅ **Upload seguro** de arquivos PDF ao Google Drive
- ✅ **Registro automático** em Google Sheets
- ✅ **Notificações por e-mail** para coordenação
- ✅ **UX moderna** com design responsivo e identidade visual institucional

## 📁 Estrutura principal

```text
├── .streamlit/         # Configurações do Streamlit (tema, secrets)
├── config/             # Configurações por ambiente (dev/prod)
├── src/
│   ├── app/
│   │   ├── main.py     # Página principal com links para formulários
│   │   └── pages/      # Formulários individuais
│   ├── services/       # Lógica de negócio (Drive, Sheets, Email)
│   ├── models/         # Schemas Pydantic
│   └── utils/          # Utilitários (validadores, criptografia)
├── api/                # Backend FastAPI (opcional)
├── credentials/        # Credenciais Google divididas por ambiente
├── docker/             # Arquivos de containerização
├── scripts/            # Scripts de deploy e automação
└── tests/              # Suite de testes
```

## 🚀 Primeiros passos

### 1. Instale as dependências

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

### 2. Configure os secrets do Streamlit

O arquivo `.streamlit/secrets.toml` já foi criado com valores padrão. Edite-o conforme necessário:

```bash
# Edite o arquivo com suas credenciais reais
nano .streamlit/secrets.toml
```

Estrutura do arquivo:

```toml
[acc]
drive_folder_id = "seu-folder-id-do-google-drive"
sheet_id = "seu-spreadsheet-id"
notification_recipients = ["coordenacao@fasitech.edu.br"]
```

> **Nota:** O arquivo `secrets.toml` está no `.gitignore` e não será commitado ao repositório.

### 3. Adicione credenciais do Google

Coloque o arquivo JSON da conta de serviço do Google em:
- `credentials/dev/service-account-dev.json` (desenvolvimento)
- `credentials/prod/service-account-prod.json` (produção)

### 4. Execute a aplicação

**Opção A: Usando o script de inicialização (Recomendado)**

```bash
# Torna o script executável (apenas na primeira vez)
chmod +x scripts/start.sh

# Execute
./scripts/start.sh
```

**Opção B: Manualmente**

```bash
# Configure o PYTHONPATH e execute
export PYTHONPATH="${PWD}:${PYTHONPATH}"
streamlit run src/app/main.py
```

A aplicação estará disponível em `http://localhost:8501`

### 5. (Opcional) Execute o backend FastAPI

```bash
uvicorn api.main:app --reload --port 8000
```

## 🧪 Testes

```bash
pytest
```

## 🐳 Docker

### Desenvolvimento
```bash
cd docker
docker-compose up
```

### Produção
```bash
docker build -f docker/Dockerfile.prod -t fasitech-forms .
docker run -p 8501:8501 -p 8000:8000 fasitech-forms
```

## 📝 Formulários disponíveis

### Formulário ACC
- Upload de certificados consolidados (PDF único, máx 10MB)
- Validação de matrícula e dados do aluno
- Integração automática com Google Drive e Sheets
- Notificação para coordenação acadêmica

## 🎨 Personalização

O tema visual está configurado em `.streamlit/config.toml`:
- Cor primária: `#663399` (roxo institucional)
- Gradientes e sombras seguindo design system
- Logo da instituição: `src/resources/fasiOficial.png`

## 📧 Suporte

Em caso de dúvidas, entre em contato com a equipe de TI ou secretaria acadêmica.
