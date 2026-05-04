# FasiTech Forms Platform

Solução moderna de formulários web com Streamlit (frontend) e FastAPI (backend), rodando em VM Linux com integrações para Google Drive, Google Sheets e envio de e-mails. Sistema completo com LGPD, download seguro de dados e API REST documentada. 

## 🚦 Camadas do Sistema

- **Frontend:** Streamlit (UX institucional, formulários, navegação)
- **Backend:** FastAPI (API REST, webhooks, download seguro, LGPD)
- **Banco de Dados:** PostgreSQL (persistência, consultas, relatórios)
- **Proxy:** Nginx (HTTPS, roteamento, SSL Let's Encrypt)
- **Armazenamento:** Google Drive, Google Sheets
- **Notificações:** E-mail institucional

## 🛡️ LGPD & Segurança de Dados

- ✅ **Download seguro** de dados sociais via API FastAPI
- ✅ **Anonimização** dos dados para pesquisa
- ✅ **Controle de acesso** por ambiente (dev/prod)
- ✅ **Armazenamento seguro** no Google Drive institucional
- ✅ **Conformidade LGPD**: Dados sensíveis nunca expostos publicamente
- ✅ **Logs e auditoria** de acessos e downloads

## 🎯 Funcionalidades

- ✅ **Portal centralizado** com múltiplos formulários
- ✅ **Formulário ACC** para atividades complementares curriculares
- ✅ **Formulário TCC** para submissão de trabalhos finais
- ✅ **Formulário Requerimento TCC** para registro de defesa
- ✅ **Formulário Estágio** para envio de documentos de estágio
- ✅ **Formulário Plano de Ensino** aceita qualquer tipo de arquivo (PDF, DOC, DOCX, ODT, imagens, etc)
- ✅ **Formulário Projetos** para submissão de projetos de ensino, pesquisa e extensão
- ✅ **Formulário Social** para coleta de dados socioeconômicos dos estudantes
- ✅ **Consulta de Projetos Docentes** visualização e análise de projetos submetidos com filtros e métricas
- ✅ **Ofertas de Disciplinas** para consulta de grades curriculares e ofertas por período/turma
- ✅ **FAQ** página de perguntas frequentes e suporte
- ✅ **Diretor Virtual (RAG)** chatbot inteligente com busca semântica em documentos PPC
- ✅ **Banco de dados PostgreSQL** para persistência e consulta de dados estruturados
- ✅ **Upload seguro** de arquivos ao Google Drive
- ✅ **Registro automático** em Google Sheets e banco de dados
- ✅ **Notificações por e-mail** para coordenação
- ✅ **UX moderna** com design responsivo e identidade visual institucional

## 📁 Estrutura principal

```text
├── .streamlit/         # Configurações do Streamlit (tema, secrets)
├── config/             # Configurações por ambiente (dev/prod)
├── src/
│   ├── app/
│   │   ├── main.py     # Página principal com links para formulários
│   │   └── pages/      # Páginas individuais:
│   │       ├── FormACC.py              # Formulário ACC
│   │       ├── FormTCC.py              # Formulário TCC
│   │       ├── FormRequerimentoTCC.py  # Requerimento TCC
│   │       ├── FormEstagio.py          # Formulário Estágio
│   │       ├── FormPlanoEnsino.py      # Formulário Plano de Ensino
│   │       ├── FormProjetos.py         # Formulário Projetos
│   │       ├── FormSocial.py           # Formulário Social
│   │       ├── PageDataDocentesProjetos.py # Consulta de Projetos Docentes
│   │       ├── OfertasDisciplinas.py   # Ofertas de Disciplinas
│   │       ├── PageDiretorVirtual.py   # Diretor Virtual (RAG Chatbot)
│   │       └── FAQ.py                  # Página FAQ
│   ├── services/       # Lógica de negócio (Drive, Sheets, Email, RAG)
│   │   ├── form_service.py             # Processamento de formulários
│   │   ├── google_drive.py             # Upload para Google Drive
│   │   ├── google_sheets.py            # Integração Google Sheets
│   │   ├── email_service.py            # Envio de e-mails
│   │   ├── rag_ppc.py                  # Serviço RAG para Diretor Virtual
│   │   └── acc_processor.py            # Processamento ACC específico
│   ├── database/       # Camada de banco de dados
│   │   ├── engine.py                   # Engine SQLModel e sessões
│   │   └── repository.py               # Repositórios e consultas
│   ├── models/         # Schemas Pydantic e modelos SQLModel
│   └── utils/          # Utilitários (validadores, criptografia)
├── api/                # Backend FastAPI (opcional)
├── credentials/        # Credenciais Google divididas por ambiente
├── docker/             # Arquivos de containerização
├── scripts/            # Scripts de deploy e automação
└── tests/              # Suite de testes
```

## 📝 Formulários e páginas disponíveis

- **Formulário ACC**: Upload de certificados consolidados (PDF único, máx 10MB)
- **Formulário TCC**: Submissão de documentos obrigatórios do TCC 1/2
- **Formulário Requerimento TCC**: Registro de banca e dados para defesa
- **Formulário Estágio**: Envio de plano e relatório de estágio
- **Formulário Plano de Ensino**: Aceita qualquer tipo de arquivo (PDF, DOC, DOCX, ODT, imagens, etc)
- **Formulário Projetos**: Submissão de projetos de ensino, pesquisa e extensão
- **Formulário Social**: Coleta de dados socioeconômicos dos estudantes
- **Consulta de Projetos Docentes**: Visualização de projetos submetidos com filtros por docente e natureza, métricas em tempo real
- **Ofertas de Disciplinas**: Consulta de grades curriculares e ofertas por período/turma com visualização colorida por turma
- **FAQ**: Página de perguntas frequentes e suporte aos usuários

## 🤖 Módulo Diretor Virtual (RAG - Retrieval Augmented Generation)

O **Diretor Virtual** é um chatbot inteligente powered by IA que responde perguntas sobre informações do Projeto Pedagógico do Curso (PPC) usando Retrieval Augmented Generation (RAG).

### Características

- ✅ **Busca Semântica**: Encontra respostas relevantes em documentos PDF usando embeddings vetoriais
- ✅ **Modelo IA Avançado**: Google Gemini 2.5-flash para respostas contextualizadas e precisas
- ✅ **Embeddings Locais**: Ollama com modelo nomic-embed-text (768 dimensões) - funciona offline
- ✅ **Sugestões Inteligentes**: Oferece sugestões de perguntas frequentes
- ✅ **Histórico de Conversa**: Mantém contexto entre múltiplas perguntas
- ✅ **Multi-Documento**: Suporta múltiplos PDFs na base de conhecimento
- ✅ **Cache Persistente**: LanceDB para indexação rápida e persistente de documentos

### Arquitetura RAG

```
┌─────────────────────────────────────────────────────────┐
│           Pergunta do Usuário (Texto)                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────▼─────────┐
        │  Ollama Embedder   │  (768-dim vetores)
        │(nomic-embed-text)  │
        └──────────┬─────────┘
                   │
        ┌──────────▼──────────────┐
        │  LanceDB Vector Search  │
        │  (Recuperação de docs)  │
        └──────────┬──────────────┘
                   │
        ┌──────────▼──────────────────────┐
        │  Google Gemini 2.5-flash (IA)   │
        │  Gera resposta contextualizada   │
        └──────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│     Resposta Inteligente com Fonte de Dados        │
└──────────────────────────────────────────────────────┘
```

### Documentos Suportados

Os seguintes documentos podem ser adicionados ao Diretor Virtual:

- **PPC.pdf**: Projeto Pedagógico do Curso (padrão)
- Qualquer outro PDF em `src/resources/` será automaticamente indexado

### Como Usar

#### No Frontend (Streamlit)

```python
# A página PageDiretorVirtual é acessível via main.py
# Interface intuitiva com:
# - Campo de entrada para perguntas
# - Botões de sugestões rápidas
# - Histórico de conversas
# - Display de resposta com fontes citadas
```

#### Como Adicionar Documentos

**Método 1: Script CLI (Recomendado)**

```bash
# Listar documentos atuais
python scripts/add_documents_to_rag.py --list

# Adicionar novo documento
python scripts/add_documents_to_rag.py --add /caminho/para/novo_documento.pdf

# Limpar cache de indexação (força reprocessamento)
python scripts/add_documents_to_rag.py --clear
```

**Método 2: Manual**

1. Copie seu PDF para `src/resources/`
2. Reinicie a aplicação
3. O documento será automaticamente indexado

**Método 3: Em Produção**

```bash
# SSH para o servidor
ssh root@IP_VM

# Copie o documento para o container
docker compose -f docker-compose.production.yml cp seu_documento.pdf streamlit:/app/src/resources/

# Restart para reindexar
docker compose -f docker-compose.production.yml restart streamlit
```

### Gerenciamento de Documentos

Para gerenciar os documentos indexados, consulte [RAG_DOCUMENT_MANAGEMENT.md](./RAG_DOCUMENT_MANAGEMENT.md) que contém:

- Métodos detalhados de adição/remoção de documentos
- Troubleshooting de problemas de indexação
- Monitoramento de status da base de conhecimento
- Best practices para otimização

### Estrutura do Serviço

```python
# src/services/rag_ppc.py
from src.services.rag_ppc import PPCChatbotService

# Inicializar serviço
service = PPCChatbotService()

# Fazer uma pergunta
resposta = service.answer_question("Qual é o objetivo do curso?")
print(resposta)

# Verificar status
status = service.get_status()
print(f"Documentos indexados: {len(status['document_files'])}")
```

### Dependências

- `agno` (v2.2.10+): Framework RAG
- `google-generativeai`: Gemini API
- `lancedb` (v0.25.3+): Vector database
- `ollama`: Embeddings locais
- `streamlit`: Frontend

### Troubleshooting

| Problema | Solução |
|----------|---------|
| "Embedding service not available" | Verifique se Ollama está rodando: `curl http://localhost:11434` |
| Resposta genérica | Adicione mais documentos ao RAG |
| Cache desatualizado | Execute `python scripts/add_documents_to_rag.py --clear` |
| Lentidão em indexação | Reduza tamanho dos PDFs ou processe em background |

## 🚀 Primeiros passos

### 1. Instale as dependências

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Novas dependências:**
> - `openpyxl` (exportação Excel)
> - `pandas` (manipulação de dados)

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

### 5. Execute o backend FastAPI

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Acesse a documentação da API em:
- `https://www.fasitech.com.br/api/docs` (Swagger UI)
- Endpoints de download: `https://www.fasitech.com.br/api/v1/dados-sociais/download`

## 🧪 Testes

```bash
pytest
```

## 🐳 Docker & Deploy

### Desenvolvimento
```bash
cd docker
docker-compose up
```

### Produção
```bash
# Sincronize o código
rsync -avz --progress --exclude 'venv/' --exclude '.git/' --exclude '__pycache__/' \
    -e "ssh" /home/nees/Documents/VSCodigo/FasiTech/ root@IP_VM:/home/ubuntu/appStreamLit

# Rebuild completo
ssh root@IP_VM
cd /home/ubuntu/appStreamLit/
sudo docker-compose -f docker-compose.production.yml up -d --build
```

### Atualização rápida
```bash
# Após alterações em código Python
sudo docker-compose -f docker-compose.production.yml restart streamlit api
```

## 🧩 Arquitetura do Sistema

```mermaid
flowchart TB
    %% Camada do Usuário
    User["👤 Usuário<br/>Docente/Aluno"]
    
    %% Internet & HTTPS
    Internet["🌐 Internet<br/>https://www.fasitech.com.br"]
    
    %% VM Linux
    subgraph VM["🖥️ VM Linux<br/>Server"]
        %% Nginx Proxy
        Nginx["🔐 Nginx<br/>Proxy Reverso<br/>:80 → :443<br/>SSL/TLS"]
        
        %% Containers Docker
        subgraph Containers["� Docker Containers"]
            direction LR
            Streamlit["🎨 Streamlit<br/>Frontend<br/>:8501<br/>• Portal formulários<br/>• UX responsiva<br/>• Navegação"]
            
            API["⚙️ FastAPI<br/>Backend<br/>:8000<br/>• API REST<br/>• Webhooks<br/>• Download seguro"]
            
            Nginx ---|� Route /| Streamlit
            Nginx ---|📡 Route /api| API
        end
    end
    
    %% Processamento
    subgraph Processing["⚙️ Processamento"]
        direction TB
        FormRouter{"� Identificar<br/>Tipo de Formulário"}
        FormACC["� ACC"]
        FormTCC["� TCC"]
        FormEstagio["� Estágio"]
        FormProjetos["� Projetos"]
        FormSocial["👥 Social"]
        FormPlano["📚 Plano Ensino"]
        
        FormRouter --> FormACC
        FormRouter --> FormTCC
        FormRouter --> FormEstagio
        FormRouter --> FormProjetos
        FormRouter --> FormSocial
        FormRouter --> FormPlano
    end
    
    %% Dados Sociais (API)
    subgraph DadosSociais["📊 Dados Sociais (LGPD)"]
        direction TB
        GetData["GET /api/v1/dados-sociais"]
        DownloadCSV["� Download CSV"]
        DownloadXLSX["📥 Download Excel"]
        Anonimizar["🔒 Anonimizar dados"]
        
        GetData --> Anonimizar
        Anonimizar --> DownloadCSV
        Anonimizar --> DownloadXLSX
    end
    
    %% Google Integration
    subgraph Google["☁️ Google Workspace"]
        Drive["🗂️ Google Drive<br/>Armazenamento<br/>de arquivos"]
        Sheets["� Google Sheets<br/>Registro de<br/>submissões"]
    end
    
    %% Notificações
    subgraph Notify["📧 Notificações"]
        Email["📬 Email SMTP<br/>Coordenação<br/>Confirmações"]
    end
    
    %% Fluxo Principal
    User -->|"Preenche"| Internet
    Internet --> Nginx
    
    Streamlit --> FormRouter
    FormRouter --> Processing
    API --> DadosSociais
    
    Processing --> Google
    Processing --> Email
    
    DadosSociais --> Sheets
    FormACC --> Drive
    FormTCC --> Drive
    FormEstagio --> Drive
    FormProjetos --> Drive
    FormSocial --> Drive
    FormPlano --> Drive
    
    %% Endpoints visíveis
    Internet ---|"✅ https://www.fasitech.com.br"| Streamlit
    Internet ---|"✅ https://www.fasitech.com.br/api/docs"| API
    Internet ---|"✅ https://www.fasitech.com.br/api/health"| API
    Internet ---|"✅ https://www.fasitech.com.br/api/v1/dados-sociais"| API
    
    %% Estilos
    classDef user fill:#E1F5FE,stroke:#01579B,stroke-width:3px,color:#000
    classDef vm fill:#FFF3E0,stroke:#E65100,stroke-width:3px,color:#000
    classDef container fill:#E8F5E9,stroke:#1B5E20,stroke-width:2px,color:#000
    classDef processing fill:#E0F2F1,stroke:#004D40,stroke-width:2px,color:#000
    classDef security fill:#FCE4EC,stroke:#880E4F,stroke-width:2px,color:#000
    classDef storage fill:#FFF9C4,stroke:#F57F17,stroke-width:2px,color:#000
    classDef endpoint fill:#E1BEE7,stroke:#4A148C,stroke-width:2px,color:#000
    
    class User user
    class VM vm
    class Streamlit,API container
    class FormRouter,FormACC,FormTCC,FormEstagio,FormProjetos,FormSocial,FormPlano processing
    class GetData,Anonimizar,DownloadCSV,DownloadXLSX security
    class Drive,Sheets storage
    class Internet,Nginx endpoint
```

## 📡 Endpoints Disponíveis

### Frontend (Streamlit)
- **`https://www.fasitech.com.br/`** - Portal principal com navegação
- **`https://www.fasitech.com.br/?page=FormACC`** - Formulário ACC
- **`https://www.fasitech.com.br/?page=FormTCC`** - Formulário TCC
- **`https://www.fasitech.com.br/?page=FormEstagio`** - Formulário Estágio
- **`https://www.fasitech.com.br/?page=FormProjetos`** - Formulário Projetos
- **`https://www.fasitech.com.br/?page=FormSocial`** - Formulário Social
- **`https://www.fasitech.com.br/?page=FormPlanoEnsino`** - Formulário Plano de Ensino
- **`https://www.fasitech.com.br/?page=PageDataDocentesProjetos`** - 📊 Consulta de Projetos Docentes
- **`https://www.fasitech.com.br/?page=OfertasDisciplinas`** - Ofertas de Disciplinas
- **`https://www.fasitech.com.br/?page=PageDiretorVirtual`** - 🤖 Diretor Virtual (RAG Chatbot)
- **`https://www.fasitech.com.br/?page=FAQ`** - Página FAQ

### API FastAPI (Dados Sociais - LGPD)
- **`https://www.fasitech.com.br/api/health`** - Health check
- **`https://www.fasitech.com.br/api/v1/dados-sociais`** - GET dados com filtros
- **`https://www.fasitech.com.br/api/v1/dados-sociais/download?format=csv`** - Download CSV anonimizado
- **`https://www.fasitech.com.br/api/v1/dados-sociais/download?format=xlsx`** - Download Excel anonimizado
- **`https://www.fasitech.com.br/api/v1/dados-sociais/estatisticas`** - Estatísticas agregadas
- **`https://www.fasitech.com.br/api/v1/dados-sociais/opcoes`** - Opções de filtros

### Documentação & Admin
- **`https://www.fasitech.com.br/api/docs`** - Swagger UI (documentação interativa)
- **`https://www.fasitech.com.br/api/redoc`** - ReDoc (documentação alternativa)

## 🎨 Personalização

O tema visual está configurado em `.streamlit/config.toml`:
- Cor primária: `#663399` (roxo institucional)
- Gradientes e sombras seguindo design system
- Logo da instituição: `src/resources/fasiOficial.png`

## 📧 Suporte

Em caso de dúvidas, entre em contato com a equipe de TI ou secretaria acadêmica.
