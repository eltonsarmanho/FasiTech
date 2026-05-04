# Plano de Migração: Streamlit → React + FastAPI (Clean Architecture + BFF)

> **Documento de orientação para agente Claude executar a migração.**
> Gerado em: 2026-04-29 | Versão: 1.0

---

## 1. DIAGNÓSTICO DA STACK ATUAL

### 1.1 Tecnologias em Uso

| Camada | Tecnologia Atual | Problema |
|--------|-----------------|----------|
| Frontend | Streamlit (Python) | Não é SPA real, UX limitada, sem componentes reutilizáveis |
| Backend API | FastAPI (parcial, só 2 rotas) | Lógica de negócio misturada no Streamlit |
| Banco de Dados | PostgreSQL + SQLModel | OK — manter e reaproveitar |
| ORM | SQLModel (SQLAlchemy + Pydantic) | OK — manter |
| Infra | Docker + Nginx | OK — adaptar |

### 1.2 Inventário de Páginas Streamlit (src/app/pages/)

| Arquivo | Público-Alvo | Complexidade |
|---------|-------------|--------------|
| `main.py` | Todos | Alta — Portal principal, navegação |
| `FormACC.py` | Discentes | Alta — Upload PDF, Google Drive, Sheets, E-mail, DB |
| `FormTCC.py` | Discentes | Alta — Upload multi-arquivo, validação TCC2, Drive, Sheets, DB |
| `FormEstagio.py` | Discentes | Alta — Upload, Drive, Sheets, DB |
| `FormRequerimentoTCC.py` | Discentes | Média — Formulário dados defesa, DB |
| `FormEmissaoDocumentos.py` | Discentes | Média — Geração de PDF (ReportLab + pyHanko), e-mail |
| `FormSocial.py` | Discentes | Alta — Formulário longo, muitos campos enum |
| `FormAutoAvaliacaoFASI.py` | Discentes | Média — Avaliação gestão, likert scale |
| `FormPlanoEnsino.py` | Docentes | Alta — Upload, Drive, Sheets, DB |
| `FormProjetos.py` | Docentes | Alta — Upload, geração PDF parecer, Drive, DB |
| `FAQ.py` | Todos | Baixa — Conteúdo estático |
| `OfertasDisciplinas.py` | Todos | Média — Leitura Google Sheets |
| `PageDiretorVirtual.py` | Todos | Alta — RAG (LanceDB + Gemini/Ollama) |
| `PageGestorAlertas.py` | Admin | Alta — CRUD alertas, APScheduler, e-mail |
| `PageLancamento.py` | Admin | Alta — SIGAA Playwright, leitura DB |
| `PageDataRequerimentoTCC.py` | Admin/Docente | Média — Visualização dados, gráficos |
| `PageDataDocentesProjetos.py` | Admin/Docente | Média — Visualização dados, gráficos |

### 1.3 Inventário de Serviços (src/services/)

| Serviço | Dependências Externas | Status na Migração |
|---------|----------------------|--------------------|
| `form_service.py` | Drive, Sheets, DB, Email | Refatorar como Use Cases |
| `google_drive.py` | Google Drive API | Manter como Infrastructure |
| `google_sheets.py` | Google Sheets API | Manter como Infrastructure |
| `email_service.py` | SMTP | Manter como Infrastructure |
| `rag_ppc.py` | LanceDB, Gemini, Ollama | Manter como Infrastructure |
| `alert_service.py` | APScheduler, DB, Email | Manter como Infrastructure (background task) |
| `sigaa_Matricular.py` | Playwright, SIGAA | Manter como Infrastructure |
| `sigaa_Consolidar.py` | Playwright, SIGAA | Manter como Infrastructure |
| `sigaa_Matricular_TCC.py` | Playwright, SIGAA | Manter como Infrastructure |
| `sigga_Consolidar_TCC.py` | Playwright, SIGAA | Manter como Infrastructure |
| `acc_processor.py` | Interno | Refatorar como Use Case |
| `document_emission_service.py` | ReportLab, pyHanko | Manter como Infrastructure |
| `gerador_certificado.py` | ReportLab | Manter como Infrastructure |
| `file_processor.py` | PyPDF2, Pillow | Manter como Infrastructure |
| `lancamento_service.py` | DB, SIGAA | Refatorar como Use Case |
| `social_data_service.py` | DB, Sheets | Refatorar como Use Case |

### 1.4 Modelos de Banco de Dados (manter exatamente)

- `tcc_submissions`
- `acc_submissions`
- `projetos_submissions`
- `plano_ensino_submissions`
- `estagio_submissions`
- `lancamento_conceitos`
- `social_submissions`
- `requerimento_tcc_submissions`
- `avaliacao_gestao_submissions`
- `alertas_academicos`

### 1.5 Infraestrutura Atual

```
Docker Compose:
  - fasitech-api-prod (FastAPI :8000)
  - fasitech-streamlit-prod (Streamlit :8501)
  - fasitech-nginx-prod (Nginx :80/:443)

Ambientes:
  - Produção Hostinger: 72.60.6.113 / fasitech.com.br
  - Produção UFPA: 172.16.28.198 / fasitech.cameta.ufpa.br
```

---

## 2. ARQUITETURA ALVO

### 2.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (SPA)                     │
│  Vite + React + TypeScript + TanStack Query + React Hook    │
│  Form + Tailwind CSS + shadcn/ui                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST (JSON + multipart)
┌────────────────────────▼────────────────────────────────────┐
│               BFF — FastAPI (Python)                         │
│  Orquestra chamadas internas, adapta payload para UI         │
│  /api/v1/... (rotas públicas) + /api/admin/... (restritas)  │
└──┬──────────────┬──────────────┬──────────────┬─────────────┘
   │              │              │              │
   ▼              ▼              ▼              ▼
Domain/        Google        PostgreSQL      Background
Use Cases      APIs          (SQLModel)      (APScheduler +
(Python)       (Drive/Sheets) (Alembic)      Playwright/SIGAA)
```

### 2.2 Estrutura de Diretórios Alvo (Clean Architecture)

```
FasiTech/
├── frontend/                        # React SPA (NOVO)
│   ├── src/
│   │   ├── app/                    # Setup geral (Router, Providers)
│   │   ├── features/               # Feature slices
│   │   │   ├── home/
│   │   │   ├── form-acc/
│   │   │   ├── form-tcc/
│   │   │   ├── form-estagio/
│   │   │   ├── form-requerimento-tcc/
│   │   │   ├── form-emissao-docs/
│   │   │   ├── form-social/
│   │   │   ├── form-plano-ensino/
│   │   │   ├── form-projetos/
│   │   │   ├── form-avaliacao/
│   │   │   ├── faq/
│   │   │   ├── ofertas-disciplinas/
│   │   │   ├── diretor-virtual/
│   │   │   ├── gestor-alertas/
│   │   │   ├── lancamento-conceitos/
│   │   │   ├── consulta-requerimento-tcc/
│   │   │   └── consulta-projetos/
│   │   ├── shared/                 # Componentes e utilitários compartilhados
│   │   │   ├── components/ui/      # shadcn/ui components
│   │   │   ├── hooks/
│   │   │   ├── lib/                # api client, formatters
│   │   │   └── types/
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile.frontend
│
├── backend/                         # FastAPI Clean Architecture (REFATORAR)
│   ├── domain/
│   │   ├── entities/               # Pydantic models puros (sem SQLModel)
│   │   │   ├── submission.py
│   │   │   ├── social.py
│   │   │   ├── alerta.py
│   │   │   └── lancamento.py
│   │   ├── repositories/           # Interfaces abstratas (ABC)
│   │   │   ├── submission_repo.py
│   │   │   ├── social_repo.py
│   │   │   └── alerta_repo.py
│   │   └── use_cases/             # Regras de negócio puras
│   │       ├── submit_acc.py
│   │       ├── submit_tcc.py
│   │       ├── submit_estagio.py
│   │       ├── submit_social.py
│   │       ├── submit_projetos.py
│   │       ├── submit_plano_ensino.py
│   │       ├── submit_requerimento_tcc.py
│   │       ├── submit_avaliacao_gestao.py
│   │       ├── emit_document.py
│   │       ├── query_social_data.py
│   │       ├── manage_alertas.py
│   │       └── manage_lancamentos.py
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── models.py           # SQLModel (= src/models/db_models.py atual)
│   │   │   ├── engine.py           # = src/database/engine.py atual
│   │   │   ├── repository.py       # = src/database/repository.py atual
│   │   │   └── migrations/         # Alembic (NOVO)
│   │   ├── google/
│   │   │   ├── drive.py            # = src/services/google_drive.py
│   │   │   └── sheets.py           # = src/services/google_sheets.py
│   │   ├── email/
│   │   │   └── service.py          # = src/services/email_service.py
│   │   ├── rag/
│   │   │   └── rag_ppc.py          # = src/services/rag_ppc.py
│   │   ├── sigaa/
│   │   │   ├── matricular.py       # = src/services/sigaa_Matricular.py
│   │   │   ├── consolidar.py       # = src/services/sigaa_Consolidar.py
│   │   │   ├── matricular_tcc.py
│   │   │   └── consolidar_tcc.py
│   │   ├── documents/
│   │   │   ├── emission.py         # = src/services/document_emission_service.py
│   │   │   └── certificate.py      # = src/services/gerador_certificado.py
│   │   ├── scheduler/
│   │   │   └── alert_scheduler.py  # = src/services/alert_service.py
│   │   └── file_processing/
│   │       └── processor.py        # = src/services/file_processor.py
│   │
│   ├── presentation/               # BFF — FastAPI routes
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── forms/
│   │   │   │   │   ├── acc.py
│   │   │   │   │   ├── tcc.py
│   │   │   │   │   ├── estagio.py
│   │   │   │   │   ├── requerimento_tcc.py
│   │   │   │   │   ├── emissao_documentos.py
│   │   │   │   │   ├── social.py
│   │   │   │   │   ├── plano_ensino.py
│   │   │   │   │   ├── projetos.py
│   │   │   │   │   └── avaliacao_gestao.py
│   │   │   │   ├── data/
│   │   │   │   │   ├── social_data.py   # = api/routes/social.py atual
│   │   │   │   │   ├── requerimento_tcc.py
│   │   │   │   │   └── projetos.py
│   │   │   │   ├── rag/
│   │   │   │   │   └── diretor_virtual.py
│   │   │   │   └── ofertas/
│   │   │   │       └── disciplinas.py
│   │   │   └── admin/
│   │   │       ├── alertas.py
│   │   │       └── lancamentos.py
│   │   ├── dependencies.py         # Auth, DB session injection
│   │   ├── schemas/                # Request/Response Pydantic schemas (BFF layer)
│   │   │   ├── acc_schemas.py
│   │   │   ├── tcc_schemas.py
│   │   │   └── ...
│   │   └── main.py                 # FastAPI app factory
│   │
│   ├── config/
│   │   ├── settings.py             # Pydantic BaseSettings
│   │   └── dev/
│   │       └── config.yaml         # = config/dev/config.yaml atual
│   │
│   └── Dockerfile.backend
│
├── docker/
│   ├── nginx/
│   │   └── nginx.conf              # Atualizar: remover streamlit, add frontend
│   ├── Dockerfile.backend          # = docker/Dockerfile.api refatorado
│   └── Dockerfile.frontend         # NOVO: nginx estático servindo React build
│
├── docker-compose.yml              # Dev
├── docker-compose.production.yml   # Prod (atualizar)
├── docs/
│   └── PLANO_MIGRACAO_REACT_FASTAPI.md  # Este documento
└── .env.example
```

### 2.3 BFF Pattern — Responsabilidades

O FastAPI age como **Backend For Frontend**:
- Agrega múltiplos serviços internos (Drive + DB + Email + Sheets) em uma única chamada
- Adapta payloads para o que o React precisa (não expõe estrutura interna)
- Valida, autentica e autoriza antes de chamar Use Cases
- Serializa/desserializa DTOs na borda do sistema

### 2.4 Fluxo de uma Submissão (Exemplo: FormACC)

```
React FormACC
  → POST /api/v1/forms/acc (multipart/form-data)
    → Presentation Layer (validate schema)
    → Use Case: SubmitACC
        → file_processor.prepare_files()
        → google_drive.upload_files()
        → repository.save_acc_submission()
        → google_sheets.append_rows()  [legado, manter]
        → email_service.send_notification()
    ← 201 Created { id, status, drive_url }
  ← React exibe toast de sucesso
```

---

## 3. FASES DE MIGRAÇÃO

> Cada fase deve ser executada e validada antes de iniciar a próxima.
> A estratégia é **Strangler Fig** — o sistema antigo coexiste até a nova stack estar pronta.

---

### FASE 1 — Preparação e Reorganização do Backend (sem breaking changes)

**Objetivo:** Reorganizar o código Python existente na estrutura Clean Architecture sem mudar comportamento. O Streamlit ainda funciona.

**Estimativa:** 3-5 dias

#### 1.1 Criar estrutura de diretórios do backend

```bash
# Criar árvore de diretórios no backend/
mkdir -p backend/domain/{entities,repositories,use_cases}
mkdir -p backend/infrastructure/{database,google,email,rag,sigaa,documents,scheduler,file_processing}
mkdir -p backend/presentation/{api/v1/{forms,data,rag,ofertas},api/admin,schemas}
mkdir -p backend/config
```

#### 1.2 Migrar Infrastructure (copiar e adaptar)

**Ordem de migração da Infrastructure:**

| Arquivo Atual | Destino | Ação |
|---------------|---------|------|
| `src/database/engine.py` | `backend/infrastructure/database/engine.py` | Copiar |
| `src/database/repository.py` | `backend/infrastructure/database/repository.py` | Copiar |
| `src/models/db_models.py` | `backend/infrastructure/database/models.py` | Copiar |
| `src/models/schemas.py` | `backend/presentation/schemas/` (dividir por domínio) | Refatorar |
| `src/services/google_drive.py` | `backend/infrastructure/google/drive.py` | Copiar |
| `src/services/google_sheets.py` | `backend/infrastructure/google/sheets.py` | Copiar |
| `src/services/email_service.py` | `backend/infrastructure/email/service.py` | Copiar |
| `src/services/rag_ppc.py` | `backend/infrastructure/rag/rag_ppc.py` | Copiar |
| `src/services/alert_service.py` | `backend/infrastructure/scheduler/alert_scheduler.py` | Copiar + remover dep. Streamlit |
| `src/services/sigaa_Matricular.py` | `backend/infrastructure/sigaa/matricular.py` | Copiar |
| `src/services/sigaa_Consolidar.py` | `backend/infrastructure/sigaa/consolidar.py` | Copiar |
| `src/services/sigaa_Matricular_TCC.py` | `backend/infrastructure/sigaa/matricular_tcc.py` | Copiar |
| `src/services/sigga_Consolidar_TCC.py` | `backend/infrastructure/sigaa/consolidar_tcc.py` | Copiar |
| `src/services/document_emission_service.py` | `backend/infrastructure/documents/emission.py` | Copiar |
| `src/services/gerador_certificado.py` | `backend/infrastructure/documents/certificate.py` | Copiar |
| `src/services/file_processor.py` | `backend/infrastructure/file_processing/processor.py` | Copiar |
| `src/services/acc_processor.py` | `backend/infrastructure/file_processing/acc_processor.py` | Copiar |
| `src/services/social_data_service.py` | Dividir: repository + use case | Refatorar |
| `src/services/lancamento_service.py` | `backend/domain/use_cases/manage_lancamentos.py` | Refatorar |

**Regra crítica para migração da Infrastructure:** Remover qualquer import de `streamlit` dos serviços. Substituir `st.secrets` por variáveis de ambiente via `os.getenv()` ou `pydantic BaseSettings`.

#### 1.3 Criar Domain Entities

Criar entidades Pydantic puras (sem SQLModel) em `backend/domain/entities/`:

```python
# backend/domain/entities/submission.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AccSubmissionEntity(BaseModel):
    nome: str
    matricula: str
    email: str
    turma: str
    polo: str
    periodo: str
    semestre: str

class TccSubmissionEntity(BaseModel):
    nome: str
    matricula: str
    email: str
    turma: str
    polo: str
    periodo: str
    orientador: str
    titulo: str
    componente: str  # "TCC 1" | "TCC 2"
```

#### 1.4 Criar Use Cases

Cada Use Case recebe injeção de dependência das interfaces de repositório:

```python
# backend/domain/use_cases/submit_acc.py
from dataclasses import dataclass
from typing import Protocol, BinaryIO

class DrivePort(Protocol):
    def upload_files(self, folder_id: str, files: list) -> list[str]: ...

class EmailPort(Protocol):
    def send_notification(self, recipients: list[str], subject: str, body: str) -> None: ...

class AccRepositoryPort(Protocol):
    def save(self, submission: dict) -> int: ...

@dataclass
class SubmitACC:
    drive: DrivePort
    email: EmailPort
    repo: AccRepositoryPort

    def execute(self, data: dict, files: list) -> dict:
        # 1. Processar arquivos
        # 2. Upload Drive
        drive_links = self.drive.upload_files(data["folder_id"], files)
        # 3. Salvar DB
        submission_id = self.repo.save({**data, "anexos": str(drive_links)})
        # 4. Enviar e-mail
        self.email.send_notification(data["recipients"], "ACC recebida", f"ID: {submission_id}")
        return {"id": submission_id, "status": "recebido", "drive_links": drive_links}
```

#### 1.5 Criar Repository Interfaces

```python
# backend/domain/repositories/submission_repo.py
from abc import ABC, abstractmethod

class AccRepositoryInterface(ABC):
    @abstractmethod
    def save(self, data: dict) -> int: ...

    @abstractmethod
    def find_by_matricula(self, matricula: str) -> list: ...
```

#### 1.6 Configuração com Pydantic BaseSettings

```python
# backend/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    google_credentials_base64: str
    google_credentials_fasi_base64: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    api_key: str
    raw_social_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    sigaa_url: str = ""
    sigaa_login: str = ""
    sigaa_senha: str = ""
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 1.7 Inicializar Alembic para migrations

```bash
cd backend
alembic init infrastructure/database/migrations
# Editar alembic.ini e env.py para usar settings.database_url
alembic revision --autogenerate -m "initial_schema"
```

#### Checkpoint Fase 1:
- [ ] Estrutura de diretórios criada
- [ ] Todos os serviços copiados/adaptados sem dependência de Streamlit
- [ ] Use Cases implementados com injeção de dependência
- [ ] Settings via BaseSettings funcionando
- [ ] Alembic configurado e testado

---

### FASE 2 — Exposição Completa via FastAPI (BFF)

**Objetivo:** Criar todos os endpoints FastAPI necessários para o React. O Streamlit ainda existe, mas novos formulários são testados via API diretamente.

**Estimativa:** 5-7 dias

#### 2.1 Atualizar main.py do FastAPI

```python
# backend/presentation/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.infrastructure.scheduler.alert_scheduler import ensure_scheduler_running
from backend.infrastructure.database.engine import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_scheduler_running()
    yield

app = FastAPI(title="FasiTech BFF", version="2.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["https://www.fasitech.com.br", "http://localhost:5173"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Incluir todos os routers
from backend.presentation.api.v1.forms import acc, tcc, estagio, ...
app.include_router(acc.router, prefix="/api/v1/forms", tags=["forms"])
app.include_router(tcc.router, prefix="/api/v1/forms", tags=["forms"])
...
```

#### 2.2 Criar endpoints de formulários

**Padrão de endpoint para formulários com upload:**

```python
# backend/presentation/api/v1/forms/acc.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Annotated
from backend.domain.use_cases.submit_acc import SubmitACC
from backend.presentation.dependencies import get_acc_use_case

router = APIRouter()

@router.post("/acc", status_code=201)
async def submit_acc(
    nome: Annotated[str, Form()],
    matricula: Annotated[str, Form()],
    email: Annotated[str, Form()],
    turma: Annotated[str, Form()],
    polo: Annotated[str, Form()],
    periodo: Annotated[str, Form()],
    semestre: Annotated[str, Form()],
    arquivo_pdf: Annotated[UploadFile, File()],
    use_case: SubmitACC = Depends(get_acc_use_case)
):
    file_bytes = await arquivo_pdf.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(413, "Arquivo excede 50MB")
    return use_case.execute(
        data={"nome": nome, "matricula": matricula, ...},
        files=[{"name": arquivo_pdf.filename, "content": file_bytes}]
    )
```

#### 2.3 Lista completa de endpoints a criar

**Formulários (POST multipart):**
- `POST /api/v1/forms/acc`
- `POST /api/v1/forms/tcc` (com validação TCC1/TCC2)
- `POST /api/v1/forms/estagio`
- `POST /api/v1/forms/requerimento-tcc`
- `POST /api/v1/forms/emissao-documentos`
- `POST /api/v1/forms/social`
- `POST /api/v1/forms/plano-ensino`
- `POST /api/v1/forms/projetos`
- `POST /api/v1/forms/avaliacao-gestao`

**Dados/Consultas (GET):**
- `GET /api/v1/dados-sociais` (já existe — manter)
- `GET /api/v1/dados-sociais/estatisticas` (já existe — manter)
- `GET /api/v1/dados-sociais/download/csv` (já existe — manter)
- `GET /api/v1/dados-sociais/download/excel` (já existe — manter)
- `GET /api/v1/requerimento-tcc` (listar registros)
- `GET /api/v1/requerimento-tcc/{id}`
- `GET /api/v1/projetos` (listar projetos docentes)
- `GET /api/v1/ofertas-disciplinas` (lê Google Sheets)

**RAG:**
- `POST /api/v1/diretor-virtual/chat` (`{"mensagem": "..."}` → `{"resposta": "..."}`)

**Admin (requer API key):**
- `GET /api/admin/alertas`
- `POST /api/admin/alertas`
- `PUT /api/admin/alertas/{id}`
- `DELETE /api/admin/alertas/{id}`
- `GET /api/admin/lancamentos`
- `POST /api/admin/lancamentos/matricular`
- `POST /api/admin/lancamentos/consolidar`

#### 2.4 Autenticação e Autorização

```python
# backend/presentation/dependencies.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from backend.config.settings import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def get_auth_dependency(api_key: str = Security(api_key_header)):
    """Bearer token simples para rotas protegidas."""
    token = (api_key or "").removeprefix("Bearer ").strip()
    if token != settings.api_key:
        raise HTTPException(401, "Token inválido")
    return token

async def get_admin_dependency(api_key: str = Security(api_key_header)):
    """Admin only — verificar lista de tokens admin."""
    token = (api_key or "").removeprefix("Bearer ").strip()
    if token not in settings.admin_api_keys:
        raise HTTPException(403, "Acesso restrito")
    return token
```

#### 2.5 Endpoint RAG (Diretor Virtual)

```python
# backend/presentation/api/v1/rag/diretor_virtual.py
from fastapi import APIRouter
from pydantic import BaseModel
from backend.infrastructure.rag.rag_ppc import get_rag_response

router = APIRouter()

class ChatRequest(BaseModel):
    mensagem: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    resposta: str
    fontes: list[str] = []

@router.post("/diretor-virtual/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    resposta, fontes = await get_rag_response(request.mensagem, request.session_id)
    return ChatResponse(resposta=resposta, fontes=fontes)
```

#### Checkpoint Fase 2:
- [ ] Todos os endpoints implementados
- [ ] Testados via Swagger UI (/docs)
- [ ] Upload de arquivos funcionando (até 50MB)
- [ ] RAG respondendo via API
- [ ] Alertas CRUD funcionando
- [ ] Download CSV/Excel funcionando

---

### FASE 3 — Criação do Frontend React

**Objetivo:** Criar o SPA React que consome a API FastAPI.

**Estimativa:** 10-15 dias

#### 3.1 Setup do projeto React

```bash
cd frontend/
npm create vite@latest . -- --template react-ts
npm install
npm install @tanstack/react-query @tanstack/react-router
npm install react-hook-form @hookform/resolvers zod
npm install axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn@latest init
```

#### 3.2 Dependências essenciais

```json
{
  "dependencies": {
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5",
    "@tanstack/react-router": "^1",
    "react-hook-form": "^7",
    "@hookform/resolvers": "^3",
    "zod": "^3",
    "axios": "^1",
    "react-hot-toast": "^2",
    "lucide-react": "^0.400"
  },
  "devDependencies": {
    "vite": "^5",
    "typescript": "^5",
    "@vitejs/plugin-react": "^4",
    "tailwindcss": "^3",
    "autoprefixer": "^10",
    "@types/react": "^18"
  }
}
```

#### 3.3 Configuração do API Client

```typescript
// frontend/src/shared/lib/api-client.ts
import axios from 'axios'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
  timeout: 30_000,
})

// Para endpoints protegidos
export const apiClientAuth = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})
apiClientAuth.interceptors.request.use((config) => {
  const token = localStorage.getItem('api_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
```

#### 3.4 Ordem de implementação das features (prioridade)

**Sprint 1 — Core (formulários principais discentes):**
1. `home/` — Portal principal com cards navegáveis
2. `form-acc/` — Formulário ACC (upload PDF)
3. `form-tcc/` — Formulário TCC (validação TCC1/TCC2)
4. `form-estagio/` — Formulário Estágio
5. `form-social/` — Formulário Social (muitos campos)

**Sprint 2 — Complementos discentes + docentes:**
6. `form-requerimento-tcc/` — Requerimento TCC
7. `form-emissao-docs/` — Emissão de Documentos
8. `form-plano-ensino/` — Plano de Ensino
9. `form-projetos/` — Projetos
10. `form-avaliacao/` — Avaliação Gestão

**Sprint 3 — Funcionalidades avançadas:**
11. `diretor-virtual/` — Chat com RAG (streaming preferível)
12. `faq/` — FAQ (pode ser estático)
13. `ofertas-disciplinas/` — Tabela de ofertas
14. `consulta-requerimento-tcc/` — Visualização dados
15. `consulta-projetos/` — Visualização projetos

**Sprint 4 — Admin:**
16. `gestor-alertas/` — CRUD alertas (com guard de autenticação)
17. `lancamento-conceitos/` — Lançamento SIGAA (com guard)

#### 3.5 Padrão de componente de formulário

```typescript
// frontend/src/features/form-acc/FormACC.tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import { apiClient } from '@/shared/lib/api-client'

const accSchema = z.object({
  nome: z.string().min(3, 'Nome obrigatório'),
  matricula: z.string().regex(/^\d{11,13}$/, 'Matrícula inválida'),
  email: z.string().email('E-mail inválido'),
  turma: z.string().min(4),
  polo: z.enum(['CAMETÁ', 'OEIRAS DO PARÁ', ...]),
  periodo: z.string(),
  semestre: z.string(),
  arquivo_pdf: z.instanceof(FileList).refine(
    files => files[0]?.size <= 50 * 1024 * 1024, 'Arquivo máximo: 50MB'
  ),
})

type AccFormData = z.infer<typeof accSchema>

export function FormACC() {
  const form = useForm<AccFormData>({ resolver: zodResolver(accSchema) })

  const mutation = useMutation({
    mutationFn: async (data: AccFormData) => {
      const formData = new FormData()
      Object.entries(data).forEach(([k, v]) => {
        if (k === 'arquivo_pdf') formData.append(k, (v as FileList)[0])
        else formData.append(k, v as string)
      })
      return apiClient.post('/api/v1/forms/acc', formData)
    },
    onSuccess: () => toast.success('ACC enviada com sucesso!'),
    onError: () => toast.error('Erro ao enviar. Tente novamente.'),
  })

  return (
    <form onSubmit={form.handleSubmit(d => mutation.mutate(d))}>
      {/* campos shadcn/ui */}
    </form>
  )
}
```

#### 3.6 Identidade Visual

Manter identidade visual atual (cores do Streamlit):
```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#7c3aed', 600: '#6d28d9' },
        institutional: { dark: '#1a0d2e', mid: '#2d1650', light: '#4a1d7a' },
      },
      backgroundImage: {
        'institutional-gradient': 'linear-gradient(135deg, #1a0d2e 0%, #2d1650 50%, #4a1d7a 100%)',
        'card-gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      },
    },
  },
}
```

#### 3.7 Roteamento

```typescript
// frontend/src/app/router.tsx
import { createBrowserRouter } from 'react-router-dom'
// OU com TanStack Router:

export const routes = [
  { path: '/', element: <HomePage /> },
  { path: '/acc', element: <FormACC /> },
  { path: '/tcc', element: <FormTCC /> },
  { path: '/estagio', element: <FormEstagio /> },
  { path: '/requerimento-tcc', element: <FormRequerimentoTCC /> },
  { path: '/emissao-documentos', element: <FormEmissaoDocumentos /> },
  { path: '/social', element: <FormSocial /> },
  { path: '/plano-ensino', element: <FormPlanoEnsino /> },
  { path: '/projetos', element: <FormProjetos /> },
  { path: '/avaliacao-gestao', element: <FormAvaliacaoGestao /> },
  { path: '/faq', element: <FAQ /> },
  { path: '/ofertas', element: <OfertasDisciplinas /> },
  { path: '/diretor-virtual', element: <DiretorVirtual /> },
  { path: '/admin/alertas', element: <GestorAlertas /> },
  { path: '/admin/lancamentos', element: <LancamentoConceitos /> },
  { path: '/consulta/requerimento-tcc', element: <ConsultaRequerimentoTCC /> },
  { path: '/consulta/projetos', element: <ConsultaProjetos /> },
]
```

#### Checkpoint Fase 3:
- [ ] Vite + React + TypeScript configurado
- [ ] Tailwind + shadcn/ui funcionando
- [ ] API client configurado com variáveis de ambiente
- [ ] Todos os formulários implementados e testados manualmente
- [ ] Identidade visual reproduzida
- [ ] Build de produção gerando sem erros (`npm run build`)

---

### FASE 4 — Docker e Infraestrutura

**Objetivo:** Substituir container Streamlit por container React + adaptar Nginx.

**Estimativa:** 2-3 dias

#### 4.1 Dockerfile Frontend

```dockerfile
# frontend/Dockerfile.frontend
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve com Nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# frontend/nginx-spa.conf (SPA fallback)
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### 4.2 Atualizar docker-compose.production.yml

```yaml
# docker-compose.production.yml (nova versão)
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: backend/Dockerfile.backend
    container_name: fasitech-api-prod
    expose:
      - "8000"
    env_file: .env.production
    volumes:
      - ./credentials:/app/credentials:ro
      - ./config:/app/config:ro
      - lancedb_data:/app/lancedb
      - ollama_data:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - fasitech-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend
    container_name: fasitech-frontend-prod
    expose:
      - "80"
    restart: unless-stopped
    networks:
      - fasitech-network

  nginx:
    image: nginx:alpine
    container_name: fasitech-nginx-prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /home/ubuntu/certbot/conf:/etc/nginx/ssl:ro
      - /home/ubuntu/certbot/www:/var/www/certbot:ro
    depends_on:
      - api
      - frontend
    restart: unless-stopped
    networks:
      - fasitech-network

networks:
  fasitech-network:
    driver: bridge

volumes:
  lancedb_data:
  ollama_data:
```

#### 4.3 Atualizar Nginx

```nginx
# docker/nginx/nginx.conf (nova versão)
upstream api_backend {
    server api:8000;
}

upstream frontend_backend {
    server frontend:80;
}

server {
    listen 443 ssl;
    http2 on;
    server_name www.fasitech.com.br fasitech.com.br;

    ssl_certificate /etc/nginx/ssl/live/fasitech.com.br/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/fasitech.com.br/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    # API FastAPI (BFF)
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # React SPA (tudo mais)
    location / {
        proxy_pass http://frontend_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name www.fasitech.com.br fasitech.com.br;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://$server_name$request_uri; }
}
```

#### Checkpoint Fase 4:
- [ ] Container frontend buildando corretamente
- [ ] docker-compose.production.yml atualizado
- [ ] nginx.conf atualizado e testado localmente
- [ ] SPA routing funcionando (F5 em rota direta não quebra)
- [ ] Upload de arquivo funcionando passando pelo Nginx (limit 100M)

---

### FASE 5 — Migração de Dados e Testes de Regressão

**Objetivo:** Garantir que nenhum dado seja perdido e que todos os fluxos estão OK.

**Estimativa:** 2-3 dias

#### 5.1 Validação do banco de dados

```bash
# Verificar que todas as tabelas existem e têm dados
psql -h 72.60.6.113 -U postgres -d fasitech -c '\dt'
psql -h 72.60.6.113 -U postgres -d fasitech -c 'SELECT COUNT(*) FROM acc_submissions;'
psql -h 72.60.6.113 -U postgres -d fasitech -c 'SELECT COUNT(*) FROM tcc_submissions;'
psql -h 72.60.6.113 -U postgres -d fasitech -c 'SELECT COUNT(*) FROM social_submissions;'
```

#### 5.2 Checklist de regressão por formulário

Para cada formulário, testar manualmente:
- [ ] Formulário renderiza corretamente no React
- [ ] Validação client-side (Zod) funcionando
- [ ] Submit enviando para API corretamente
- [ ] Arquivo sendo salvo no Google Drive
- [ ] Registro salvo no PostgreSQL
- [ ] E-mail de notificação enviado
- [ ] Toast de sucesso exibido no React

#### 5.3 Testes de regressão da API

```bash
# Testar cada endpoint
curl -X POST http://localhost:8000/api/v1/forms/acc \
  -F "nome=Teste Silva" \
  -F "matricula=20230123456" \
  -F "email=teste@ufpa.br" \
  -F "turma=2026" \
  -F "polo=CAMETÁ" \
  -F "periodo=2026.1" \
  -F "semestre=2025.2" \
  -F "arquivo_pdf=@/tmp/test.pdf"
```

#### 5.4 Período de coexistência (opcional)

Se necessário, manter o Streamlit em `/legacy` temporariamente:

```nginx
# Streamlit em rota legado (transição suave)
location /legacy/ {
    proxy_pass http://streamlit_backend/;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

---

### FASE 6 — Deploy e Go-Live

**Objetivo:** Deploy em produção com zero downtime.

**Estimativa:** 1 dia

#### 6.1 Deploy em Hostinger

```bash
# 1. Sincronizar código
rsync -avz --progress \
  --exclude 'node_modules/' --exclude 'lancedb/' --exclude 'venv/' \
  --exclude '.git/' --exclude '__pycache__/' --exclude '*.pyc' \
  -e "ssh" \
  /home/nees/Documents/VSCodigo/FasiTech/ \
  root@72.60.6.113:/home/ubuntu/appStreamLit

# 2. No servidor — deploy com rolling update
ssh root@72.60.6.113
cd /home/ubuntu/appStreamLit

# 3. Build novo frontend
docker compose -f docker-compose.production.yml build frontend

# 4. Restart com zero-downtime (nginx absorve)
docker compose -f docker-compose.production.yml up -d --no-deps --build api
docker compose -f docker-compose.production.yml up -d --no-deps frontend
docker compose -f docker-compose.production.yml restart nginx

# 5. Remover container Streamlit (só depois de validar)
docker compose -f docker-compose.production.yml stop streamlit
docker rm fasitech-streamlit-prod
```

#### 6.2 Monitoramento pós-deploy

```bash
# Verificar logs em tempo real
docker logs -f fasitech-api-prod
docker logs -f fasitech-frontend-prod
docker logs -f fasitech-nginx-prod

# Health check
curl https://www.fasitech.com.br/health
```

---

## 4. RESTRIÇÕES E DECISÕES TÉCNICAS

### 4.1 O que MANTER sem mudanças

| Componente | Razão |
|-----------|-------|
| PostgreSQL | Funciona bem, sem razão para trocar |
| SQLModel ORM | Modelos de DB bem definidos |
| Lógica de SIGAA (Playwright) | Complexo, específico da UFPA — só expor via API |
| LanceDB + Ollama | RAG funcionando — só encapsular |
| Google Drive/Sheets | Integração necessária — só mover para Infrastructure |
| APScheduler | Alertas funcionando — migrar para lifespan do FastAPI |
| Certificados SSL Certbot | Infraestrutura não muda |
| Variáveis de ambiente (.env) | Apenas adicionar `VITE_API_URL` para o frontend |

### 4.2 O que REMOVER

| Componente | Razão |
|-----------|-------|
| Streamlit | Substituído pelo React |
| `src/app/` (todas as pages) | Substituídas pelos componentes React |
| `st.secrets` | Substituído por `os.getenv()` / BaseSettings |
| `streamlit-feedback` | Substituído por componente React nativo |

### 4.3 Decisões de Design

1. **Sem autenticação JWT complexa** — manter API key simples para admin. React guarda token no localStorage.
2. **Sem Redux** — TanStack Query é suficiente para estado servidor. React state local para formulários.
3. **shadcn/ui** — componentes acessíveis e customizáveis sem overhead de biblioteca grande.
4. **Upload via multipart/form-data** — não converter para base64. Nginx limit 100M é suficiente.
5. **RAG sem streaming no primeiro momento** — retornar resposta completa. Streaming pode ser adicionado depois com SSE.
6. **Sem banco de dados separado para sessões** — sem autenticação de usuário final, apenas API keys para admin.

---

## 5. VARIÁVEIS DE AMBIENTE (atualizar .env.example)

```bash
# Banco de Dados
DATABASE_URL=postgresql://postgres:senha@localhost:5432/fasitech

# Google APIs
GOOGLE_CLOUD_CREDENTIALS_BASE64=<base64_do_json_credenciais>
GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64=<base64_do_json_credenciais_fasi>

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email@gmail.com
SMTP_PASSWORD=senha_app

# API Keys
API_KEY=<token_para_endpoints_protegidos>
RAW_SOCIAL_API_KEY=<token_dados_brutos>
ADMIN_API_KEYS=<csv_de_tokens_admin>

# AI/RAG
GEMINI_API_KEY=<chave_gemini>
OPENAI_API_KEY=<chave_openai>
OLLAMA_BASE_URL=http://localhost:11434

# SIGAA
SIGAA_URL=<url_sigaa>
SIGAA_LOGIN=<login_sigaa>
SIGAA_SENHA=<senha_sigaa>

# App
ENVIRONMENT=production
API_BASE_URL=https://www.fasitech.com.br

# Frontend (arquivo frontend/.env)
VITE_API_URL=https://www.fasitech.com.br
```

---

## 6. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| SIGAA muda sua interface web | Média | Alto | Playwright é frágil; testar após cada deploy |
| Google API quota excedida | Baixa | Médio | Implementar rate limiting no Use Case |
| Upload de 50MB via Nginx | Baixa | Médio | `client_max_body_size 100M` já configurado |
| RAG sem resposta (Ollama offline) | Média | Médio | Fallback para Gemini/OpenAI já existe |
| Quebra de schema DB | Baixa | Alto | Alembic com migrations versionadas |
| CORS bloqueando frontend | Baixa | Alto | Configurar `allow_origins` com domínio exato em prod |

---

## 7. COMANDOS RÁPIDOS PARA O AGENTE

```bash
# Criar estrutura de diretórios (Fase 1)
mkdir -p backend/{domain/{entities,repositories,use_cases},infrastructure/{database/migrations,google,email,rag,sigaa,documents,scheduler,file_processing},presentation/{api/{v1/{forms,data,rag,ofertas},admin},schemas},config}

# Instalar dependências do backend
pip install fastapi uvicorn[standard] sqlmodel psycopg2-binary pydantic-settings alembic

# Inicializar React (Fase 3)
cd frontend && npm create vite@latest . -- --template react-ts
npm install @tanstack/react-query react-hook-form @hookform/resolvers zod axios react-hot-toast lucide-react
npm install -D tailwindcss postcss autoprefixer
npx shadcn@latest init

# Rodar backend em dev
uvicorn backend.presentation.main:app --reload --port 8000

# Rodar frontend em dev
cd frontend && npm run dev -- --port 5173

# Build produção
cd frontend && npm run build
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
```

---

## 8. CHECKLIST FINAL PRÉ-GO-LIVE

- [ ] Todos os formulários testados manualmente (submit completo)
- [ ] Google Drive recebendo arquivos corretamente
- [ ] E-mails sendo enviados corretamente
- [ ] RAG respondendo perguntas sobre o PPC
- [ ] Alertas acadêmicos sendo disparados no horário
- [ ] Download CSV/Excel funcionando
- [ ] SIGAA automação testada (lançamento conceitos)
- [ ] SSL renovação automática (certbot) não afetada
- [ ] Backup do banco antes do go-live
- [ ] Monitoramento de logs configurado
- [ ] URL da VM UFPA testada (fasitech.cameta.ufpa.br)
- [ ] URL Hostinger testada (fasitech.com.br)
- [ ] Container Streamlit removido após validação

---

*Documento gerado com base na análise completa do código fonte em 2026-04-29.*
*Stack atual: Streamlit + FastAPI parcial | Stack alvo: React + FastAPI Clean Architecture + BFF*
