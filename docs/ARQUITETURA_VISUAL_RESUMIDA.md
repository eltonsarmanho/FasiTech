# Arquitetura FasiTech - Resumo Visual

## 1. Stack do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                       FASITECH PLATFORM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FRONTEND            API                DOMAIN      INFRA        │
│  ─────────           ───                ──────      ─────        │
│  React 18.x          FastAPI 0.100      Python      PostgreSQL   │
│  TypeScript          Pydantic           Clean Arch  15.x         │
│  Tailwind CSS        Async/Await        DDD Pattern SQLModel     │
│  React Query 5.x     JWT Auth           Repositories LangChain   │
│                      Dependency Inject  UseCase     Playwright   │
│                                         Entities    APScheduler  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Arquitetura em 4 Camadas

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PRESENTATION LAYER (APIs RESTful)                               ┃
┃ /api/v1/forms/* | /api/v1/data/* | /api/v1/rag/* | /api/admin/ ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ DOMAIN LAYER (Lógica de Negócio)                               ┃
┃ Services | UseCases | Entities | Repositories (Interfaces)    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ INFRASTRUCTURE LAYER (Implementações Técnicas)                 ┃
┃ Repositories | SIGAA | Database | RAG | Email | Scheduler      ┃
┃ File Processing | Google Drive                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ EXTERNAL SERVICES                                               ┃
┃ SIGAA (UFPA) | Claude API | Google APIs | SMTP Server          ┃
┃ PostgreSQL Database | Vector Store                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## 3. Domínios Principais

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOMÍNIOS DE SERVIÇO                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🎓 SIGAA Domain            📋 Formulários Domain               │
│  ├─ Matricular              ├─ ACC Form                         │
│  ├─ Consolidar              ├─ TCC Form                         │
│  ├─ Dinâmica de expansão    ├─ Estágio Form                    │
│  └─ Automação Playwright    └─ Plano Ensino Form               │
│                                                                  │
│  📊 Database Domain         🤖 RAG Domain                       │
│  ├─ Persistência            ├─ Document Processing             │
│  ├─ Queries                 ├─ LangChain Integration           │
│  ├─ SQLModel ORM            ├─ Vector Store                    │
│  └─ PostgreSQL              └─ Claude API                      │
│                                                                  │
│  📧 Email Domain            ⏰ Scheduler Domain                 │
│  ├─ SMTP Integration        ├─ Alert Jobs                      │
│  ├─ Templates               ├─ Cleanup Jobs                    │
│  └─ Notifications           └─ APScheduler                     │
│                                                                  │
│  🔗 Google Drive Domain     📁 File Processing Domain           │
│  ├─ Sync Files              ├─ DOCX Handler                    │
│  ├─ Share Folders           ├─ PDF Handler                     │
│  └─ API Integration         └─ Excel Handler                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Fluxos Principais

### 4.1 Matrícula e Consolidação
```
Secretário Clica "Matricular"
         ↓
Frontend POST /api/admin/lancamentos/matricular
         ↓
LancamentoService.matricular()
         ↓
Expande: ACC → [ACC I, ACC II, ACC III, ACC IV]
         ↓
Para cada componente → matricular.py (ACC) ou matricular_tcc.py (TCC)
         ↓
Playwright automatiza SIGAA
         ↓
Coleta sucessos + erros
         ↓
Atualiza status database
         ↓
React Query invalida cache
         ↓
Frontend atualiza tabela
         ↓
Secretário vê ✓ (Sim) no status
```

### 4.2 Chat Diretor Virtual (RAG)
```
Aluno faz pergunta no chat
         ↓
Frontend POST /api/v1/rag/diretor-virtual
         ↓
Gera embedding da pergunta
         ↓
Vector Store busca documentos similares
         ↓
LangChain monta contexto
         ↓
Claude API gera resposta citada
         ↓
Frontend exibe resposta + fontes
```

### 4.3 Processamento de Formulário
```
Aluno preenche formulário
         ↓
Frontend valida dados
         ↓
POST /api/v1/forms/acc
         ↓
Validação Pydantic
         ↓
ProcessarACC UseCase
         ↓
Salva em database
         ↓
Email notifica professor
         ↓
Frontend mostra confirmação
```

---

## 5. Estrutura de Arquivos

```
FasiTech/
│
├── backend/
│   ├── domain/                    ← Lógica pura
│   │   ├── entities/
│   │   ├── repositories/          (interfaces)
│   │   └── use_cases/
│   │
│   ├── infrastructure/            ← Implementações
│   │   ├── sigaa/                 (Playwright)
│   │   ├── database/              (SQLModel, PostgreSQL)
│   │   ├── rag/                   (LangChain, Claude)
│   │   ├── email/                 (SMTP)
│   │   ├── scheduler/             (APScheduler)
│   │   ├── file_processing/       (DOCX, PDF)
│   │   └── google/                (Drive, Sheets)
│   │
│   └── presentation/              ← APIs HTTP
│       ├── api/
│       │   ├── v1/
│       │   │   ├── forms/         (ACC, TCC, Est.)
│       │   │   ├── data/          (Queries)
│       │   │   ├── ofertas/       (Disciplinas)
│       │   │   └── rag/           (Chat IA)
│       │   └── admin/             (Painel)
│       └── schemas/               (Pydantic)
│
├── frontend/
│   └── src/
│       ├── features/              ← Componentes React
│       │   ├── lancamento-conceitos/
│       │   ├── acc-form/
│       │   ├── tcc-form/
│       │   └── director-chat/
│       ├── shared/                (Reutilizáveis)
│       └── App.tsx
│
├── docs/                          ← Documentação
│   ├── ARQUITETURA_SISTEMA.md
│   ├── FLUXOS_INTEGRACAO.md
│   ├── COMPONENTES_ARQUITETURA.md
│   └── ARQUITETURA_VISUAL_RESUMIDA.md (este)
│
└── docker-compose.yml             ← Orquestração
```

---

## 6. APIs Disponíveis

### 6.1 Admin - Lançamentos
```
GET    /api/admin/lancamentos                    Listar com filtros
GET    /api/admin/lancamentos/componentes-validos   Lista de componentes
POST   /api/admin/lancamentos/matricular         Matricular no SIGAA
POST   /api/admin/lancamentos/consolidar         Consolidar no SIGAA
PATCH  /api/admin/lancamentos/atualizar-status   Atualizar status manual
```

### 6.2 Formulários
```
POST   /api/v1/forms/acc                          Enviar ACC
POST   /api/v1/forms/tcc                          Enviar TCC
POST   /api/v1/forms/estagio                      Enviar Estágio
POST   /api/v1/forms/plano-ensino                 Enviar Plano
```

### 6.3 Dados
```
GET    /api/v1/data/social-data                   Dados sociais
GET    /api/v1/data/projetos-data                 Projetos
GET    /api/v1/data/tcc-data                      TCCs
```

### 6.4 Ofertas
```
GET    /api/v1/ofertas/disciplinas                Disciplinas
```

### 6.5 RAG
```
POST   /api/v1/rag/diretor-virtual                Chat IA
```

---

## 7. Padrões e Convenções

### Pattern: Component Expansion
```python
# ACC pode ser um componente genérico
COMPONENTES_EXPANDIDOS = {
    "ACC": ["ACC I", "ACC II", "ACC III", "ACC IV"],
    "TCC": ["TCC I", "TCC II"],
}

# Se ACC é enviado, expande para os 4 componentes
# Processa cada um independentemente
# Retorna sucesso/erro para cada um
```

### Pattern: Dynamic Imports
```python
# Seleciona implementação correta
if componente.startswith("TCC"):
    from backend.infrastructure.sigaa.matricular_tcc import executar_fluxo_direto
else:
    from backend.infrastructure.sigaa.matricular import executar_fluxo_direto
```

### Pattern: Repository Pattern
```python
# Define interface em domain/
class ILancamentoRepository(ABC):
    async def atualizar_status(...): pass

# Implementa em infrastructure/
class LancamentoRepository(ILancamentoRepository):
    async def atualizar_status(...):
        # implementação com database
```

### Pattern: React Query
```typescript
// Fetch automático
const { data, isLoading } = useQuery({
    queryKey: ['lancamentos', tipo],
    queryFn: () => apiAuth.get('/api/admin/lancamentos?...')
})

// Mutação com refetch automático
const mutation = useMutation({
    mutationFn: (data) => apiAuth.post('/endpoint', data),
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ['lancamentos'] })
    }
})
```

---

## 8. Status do Sistema

| Componente | Status | Descrição |
|-----------|--------|-----------|
| **Frontend** | ✅ Produção | React + Tailwind, tudo funcional |
| **API REST** | ✅ Produção | FastAPI com todas as rotas |
| **SIGAA Automation** | ⚠️ Uso Manual | Funciona mas SIGAA mudou estrutura |
| **Database** | ✅ Produção | PostgreSQL com SQLModel |
| **RAG (Chat IA)** | ✅ Produção | LangChain + Claude funcionando |
| **Email Service** | ✅ Produção | SMTP configurado |
| **Scheduler** | ✅ Produção | Alertas automáticos |
| **Google Drive Sync** | ✅ Produção | Sincronização de docs |
| **Docker Deploy** | ✅ Produção | VM 72.60.6.113 |

---

## 9. Como Adicionar Nova Funcionalidade

### Exemplo: Nova API `/api/v1/forms/licenca`

```
1. BACKEND - Criar Domain UseCase
   └─ backend/domain/use_cases/processar_licenca.py

2. BACKEND - Criar Infrastructure Repository
   └─ backend/infrastructure/database/repository.py (update)

3. BACKEND - Criar Presentation API
   └─ backend/presentation/api/v1/forms/licenca.py

4. FRONTEND - Criar Componente React
   └─ frontend/src/features/licenca-form/LicencaForm.tsx

5. FRONTEND - Integrar ao App
   └─ frontend/src/App.tsx (adicionar rota)

6. DATABASE - Adicionar modelo
   └─ backend/infrastructure/database/models.py

7. Deploy
   └─ docker-compose up -d --build
```

---

## 10. Princípios de Arquitetura

✅ **Clean Architecture**: Separação clara entre camadas
✅ **DDD (Domain-Driven Design)**: Domínios bem definidos
✅ **Repository Pattern**: Abstração de persistência
✅ **Dependency Injection**: Loosely coupled components
✅ **Async/Await**: Performance em operações I/O
✅ **Error Handling**: Erros estruturados
✅ **Logging**: Rastreamento end-to-end
✅ **Security**: JWT, validação, sanitização
✅ **Scalability**: Preparado para crescimento

---

## 11. Contato e Suporte

- **Desenvolvedor**: eltonsarmanho@gmail.com
- **Projeto**: FasiTech (Portal UFPA/FASI)
- **Documentação Completa**: `/docs/`
- **Servidor**: http://72.60.6.113

---

## 12. Próximas Evoluções

🔮 **Curto Prazo**:
- [ ] Melhorar identificação de componentes SIGAA
- [ ] Adicionar cache de documentos indexados
- [ ] Expandir templates de email

🔮 **Médio Prazo**:
- [ ] Implementar GraphQL
- [ ] Adicionar WebSockets para real-time
- [ ] Message Queue (Redis/RabbitMQ)

🔮 **Longo Prazo**:
- [ ] Microserviços independentes
- [ ] Kubernetes deployment
- [ ] Observabilidade (ELK/DataDog)
- [ ] Análise de dados (BI)
