# Fluxos de Integração entre Domínios

## 1. Fluxo Completo: Matrícula e Consolidação (End-to-End)

```mermaid
sequenceDiagram
    actor User as Secretário
    participant FE as Frontend React
    participant API as FastAPI API
    participant Service as LancamentoService
    participant MatricularMod as matricular.py/TCC
    participant SIGAA as SIGAA System
    participant DB as PostgreSQL
    
    User->>FE: 1. Clica botão "Matricular"<br/>(Matricula: 202285940020, Componente: ACC)
    
    FE->>FE: 2. Valida dados no frontend
    FE->>FE: 3. Mostra "⏳ Processando..."
    FE->>FE: 4. Desabilita botões
    
    FE->>API: 5. POST /api/admin/lancamentos/matricular<br/>{matricula, periodo, polo, componente}
    
    API->>Service: 6. LancamentoService(matricula=..., componente='ACC')
    
    Service->>Service: 7. Valida componente<br/>(ACC é válido)
    
    Service->>Service: 8. _expand_componentes()<br/>ACC → [ACC I, ACC II, ACC III, ACC IV]
    
    loop Para cada componente expandido
        Service->>Service: 9. args = _args_matricular()
        Service->>Service: 10. args.componente = 'ACC I' (iteração 1)
        
        alt TCC?
            Service->>MatricularMod: 11a. Importa matricular_tcc.py
        else ACC
            Service->>MatricularMod: 11b. Importa matricular.py
        end
        
        Service->>MatricularMod: 12. await executar_fluxo_direto(args)
        
        MatricularMod->>SIGAA: 13. Login no SIGAA
        MatricularMod->>SIGAA: 14. Navega: Período → Portal Coord. → Curso
        MatricularMod->>SIGAA: 15. Atividades > Matricular
        MatricularMod->>SIGAA: 16. Busca aluno (202285940020)
        MatricularMod->>SIGAA: 17. Seleciona tipo de atividade
        MatricularMod->>SIGAA: 18. Busca e seleciona componente (ACC I)
        MatricularMod->>SIGAA: 19. Próximo passo
        MatricularMod->>SIGAA: 20. Digita senha
        MatricularMod->>SIGAA: 21. Confirma matricula
        
        SIGAA-->>MatricularMod: 22. ✓ Matrícula confirmada
        MatricularMod-->>Service: 23. Retorna sucesso
        
        Service->>Service: 24. matriculados.append('ACC I')<br/>detalhes.append('SUCESSO: ACC I')
    end
    
    Service-->>API: 25. ResultadoOperacao(sucesso=True,<br/>detalhes=['SUCESSO: ACC I', 'SUCESSO: ACC II', ...])
    
    API->>API: 26. Extrai componentes sucesso
    
    API->>DB: 27. atualizar_status_lancamento()<br/>matricula=202285940020<br/>periodo=2026.1<br/>componente='ACC I'<br/>matriculado=True
    
    DB->>DB: 28. UPDATE lancamento_conceitos<br/>SET matriculado=True<br/>WHERE matricula='...' AND componente='ACC I'
    
    DB-->>API: 29. ✓ Status atualizado (ACC I)
    
    Note over API: Repete 27-29 para ACC II, III, IV
    
    API-->>FE: 30. HTTP 202 Accepted<br/>{message, detalhes, componentes_sucesso}
    
    FE->>FE: 31. Recebe resposta
    FE->>FE: 32. Invalida cache React Query
    FE->>FE: 33. Re-fetcha dados (/api/admin/lancamentos)
    FE->>API: 34. GET /api/admin/lancamentos?tipo_formulario=ACC
    
    API->>DB: 35. get_lancamento_conceitos(tipo_formulario='ACC')
    
    DB-->>API: 36. Retorna rows com matriculado=True
    
    API-->>FE: 37. [rows atualizado]
    
    FE->>FE: 38. Atualiza estado (filtered)
    FE->>FE: 39. Re-renderiza tabela<br/>- Coluna Matriculado: Não → Sim ✓
    FE->>FE: 40. Toast: "Matrícula processada!"
    FE->>FE: 41. Remove "⏳ Processando..."
    FE->>FE: 42. Re-habilita botões
    
    User->>FE: 43. Vê tabela atualizada com ✓ (Sim)
    
    Note over FE,DB: Fluxo Consolidar é idêntico,<br/>diferença: consolidado=True<br/>e conceito validado
```

---

## 2. Fluxo de Atualização Manual de Status

```mermaid
sequenceDiagram
    participant FE as Frontend React
    participant API as FastAPI API
    participant Repo as Repository
    participant DB as PostgreSQL
    
    FE->>FE: 1. Secretário clica no toggle<br/>(Matriculado: Não → Sim)
    
    FE->>API: 2. PATCH /api/admin/lancamentos/atualizar-status<br/>{matricula, periodo, polo, componente,<br/>matriculado: true}
    
    API->>Repo: 3. atualizar_status_lancamento(...,<br/>matriculado=True)
    
    Repo->>DB: 4. Busca registro<br/>WHERE matricula='...' AND<br/>periodo='...' AND polo='...' AND<br/>componente='ACC I'
    
    alt Registro encontrado
        Repo->>DB: 5. UPDATE lancamento_conceitos<br/>SET matriculado=True
        DB-->>Repo: 6. ✓ 1 row updated
        Repo-->>API: 7. Retorna LancamentoConceito atualizado
        API-->>FE: 8. HTTP 200<br/>{matricula, componente, matriculado, consolidado}
        FE->>FE: 9. Atualiza estado local
        FE->>FE: 10. Re-renderiza coluna
        FE->>FE: 11. Toast sucesso
    else Registro não encontrado
        Repo-->>API: 12. Retorna None
        API-->>FE: 13. HTTP 404 Not Found
        FE->>FE: 14. Toast erro
    end
```

---

## 3. Fluxo RAG: Diretor Virtual

```mermaid
sequenceDiagram
    actor User as Aluno/Professor
    participant Chat as Chat Interface
    participant API as FastAPI
    participant Service as DirectorVirtualService
    participant VectorStore as Vector Store (Chroma)
    participant LLM as Claude API
    participant DocProc as Document Processor
    
    Note over Chat,DocProc: === FASE 1: Indexação (Assíncrona) ===
    
    loop Durante deploy ou atualização
        API->>DocProc: 1. Processar documento<br/>(PDF/DOCX)
        DocProc->>DocProc: 2. Extract texto
        DocProc->>DocProc: 3. Chunking (300 tokens)
        DocProc->>Service: 4. Gera embeddings<br/>(Claude API)
        Service->>LLM: 5. POST /embeddings<br/>text='...'
        LLM-->>Service: 6. Retorna vetor embedding
        Service->>VectorStore: 7. Armazena<br/>(chunk_id, embedding, metadata)
        VectorStore-->>Service: 8. ✓ Indexado
    end
    
    Note over Chat,DocProc: === FASE 2: Consulta (Online) ===
    
    User->>Chat: 9. "Qual é o processo de TCC?"
    Chat->>API: 10. POST /api/v1/rag/diretor-virtual<br/>{pergunta: '...', contexto_session: '...'}
    
    API->>Service: 11. ConsultarDirectorVirtual(pergunta)
    
    Service->>Service: 12. Gera embedding da pergunta<br/>(Claude API)
    
    Service->>LLM: 13. POST /embeddings
    LLM-->>Service: 14. Retorna vetor embedding
    
    Service->>VectorStore: 15. Busca similar<br/>(embedding, k=5)
    VectorStore-->>Service: 16. Retorna top-5 chunks relevantes<br/>+ metadados (source, page, etc)
    
    Service->>Service: 17. Monta contexto:<br/>PERGUNTA: {pergunta}<br/>CONTEXTOS: {chunks}
    
    Service->>LLM: 18. POST /messages<br/>system="Você é diretor virtual"<br/>user=contexto<br/>max_tokens=1500
    
    LLM-->>Service: 19. Retorna resposta<br/>com citação de fontes
    
    Service-->>API: 20. {resposta, fontes, confianca}
    
    API-->>Chat: 21. HTTP 200 + resposta
    
    Chat->>Chat: 22. Renderiza resposta
    Chat->>Chat: 23. Exibe fontes como links
    
    User->>Chat: 24. Vê resposta com contexto<br/>de documentos oficiais
```

---

## 4. Fluxo de Processamento de Formulário ACC

```mermaid
sequenceDiagram
    participant FE as Frontend React
    participant API as FastAPI
    participant UseCase as ProcessarACC UseCase
    participant Repo as Repository
    participant DB as PostgreSQL
    participant Email as Email Service
    
    FE->>FE: 1. Preenchimento do formulário<br/>- Matricula<br/>- Nome da atividade<br/>- Data<br/>- Descrição
    
    FE->>FE: 2. Validações frontend<br/>- Campos obrigatórios<br/>- Formatos
    
    FE->>API: 3. POST /api/v1/forms/acc<br/>{matricula, atividade, data, descricao, ...}
    
    API->>API: 4. Validação de autenticação<br/>(JWT token)
    
    API->>API: 5. Validação de schema<br/>(Pydantic)
    
    API->>UseCase: 6. ProcessarACC.executar({form_data})
    
    UseCase->>UseCase: 7. Lógica de negócio<br/>- Verifica se aluno existe<br/>- Valida período<br/>- Calcula horas
    
    UseCase->>Repo: 8. Persiste formulário
    
    Repo->>DB: 9. INSERT INTO lancamento_conceitos_formulario<br/>(matricula, tipo='ACC', dados_json, criado_em)
    
    DB-->>Repo: 10. ID gerado
    
    Repo-->>UseCase: 11. FormularioACC criado
    
    UseCase->>Email: 12. Envia notificação<br/>To: professor@ufpa.br<br/>Subject: "Nova atividade ACC"<br/>Body: detalhes da atividade
    
    Email-->>UseCase: 13. ✓ Email enviado
    
    UseCase-->>API: 14. FormularioACC.to_response()
    
    API-->>FE: 15. HTTP 201 Created<br/>{id, matricula, atividade, status: 'enviado'}
    
    FE->>FE: 16. Atualiza estado
    FE->>FE: 17. Mostra mensagem de sucesso
    FE->>FE: 18. Redireciona para confirmação
    
    FE->>FE: 19. Renderiza tela de sucesso<br/>- ID do formulário<br/>- Próximos passos
    
    FE->>API: 20. GET /api/v1/forms/status/{id}<br/>(polling para status)
    
    Note over FE,DB: Professor acessa painel<br/>para avaliar formulário
```

---

## 5. Fluxo de Scheduler: Geração de Alertas

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler
    participant Job as AlertJob
    participant DB as PostgreSQL
    participant Rule as RuleEngine
    participant Email as Email Service
    
    Note over Scheduler: Trigger: 08:00 todos os dias
    
    Scheduler->>Job: 1. Inicia job<br/>(GerarAlertasAcademicos)
    
    Job->>DB: 2. Busca alunos com status<br/>- Matriculado=True<br/>- Consolidado=False<br/>- Periodo='2026.1'
    
    DB-->>Job: 3. Retorna lista de alunos
    
    loop Para cada aluno
        Job->>Rule: 4. Aplica regras de negócio
        
        alt Consolidado > 30 dias?
            Rule->>Rule: 5. Alerta crítico
        else Consolidado > 15 dias?
            Rule->>Rule: 6. Alerta moderado
        else
            Rule->>Rule: 7. Sem alerta
        end
        
        Rule->>Email: 8. Envia email com template
        Email-->>Rule: 9. ✓ Enviado
        
        Job->>DB: 10. UPDATE alerta_status<br/>SET enviado_em=NOW()
        DB-->>Job: 11. ✓ Registrado
    end
    
    Job-->>Scheduler: 12. Job completado<br/>duracao=45s<br/>alertas_enviados=127
    
    Scheduler->>Scheduler: 13. Log sucesso<br/>[APScheduler] Alerta job concluído
```

---

## 6. Fluxo de Integração Google Drive

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant GoogleService as Google Drive Service
    participant GoogleAPI as Google Drive API
    participant DocProc as Document Processor
    
    FE->>API: 1. POST /api/v1/documents/sync-gdrive<br/>{folder_id, credential_token}
    
    API->>GoogleService: 2. SyncGoogleDrive(folder_id)
    
    GoogleService->>GoogleAPI: 3. Autentica com token
    GoogleAPI-->>GoogleService: 4. ✓ Autenticado
    
    GoogleService->>GoogleAPI: 5. Busca arquivos<br/>files = list(folder_id,<br/>pageSize=100)
    
    GoogleAPI-->>GoogleService: 6. [lista de arquivos]
    
    loop Para cada arquivo (PDF/DOCX)
        GoogleService->>GoogleAPI: 7. Download arquivo<br/>(bytes)
        GoogleAPI-->>GoogleService: 8. Conteúdo arquivo
        
        GoogleService->>DocProc: 9. Processa arquivo<br/>(extract, chunk, embed)
        
        DocProc->>DocProc: 10. Extrai texto
        DocProc->>DocProc: 11. Faz chunking
        DocProc->>DocProc: 12. Gera embeddings
        
        DocProc-->>GoogleService: 13. Chunks com embeddings
        
        GoogleService->>API: 14. Armazena em vector DB
    end
    
    GoogleService-->>API: 15. {total_arquivos, total_chunks, sucesso}
    
    API-->>FE: 16. HTTP 200<br/>Sincronização completa
    
    FE->>FE: 17. Toast de sucesso<br/>"XX documentos indexados"
```

---

## 7. Matriz de Dependências entre Domínios

```mermaid
graph LR
    subgraph "Domain Layer"
        DL["Domain<br/>(Entities, Use Cases<br/>Repositories)"]
    end

    subgraph "Infrastructure"
        SIGAA["SIGAA<br/>(Playwright)"]
        DB["Database<br/>(PostgreSQL)"]
        RAG["RAG<br/>(LangChain)"]
        Email["Email<br/>(SMTP)"]
        Scheduler["Scheduler<br/>(APScheduler)"]
        Google["Google<br/>(Drive/Sheets)"]
        FileProc["File Processing<br/>(PDF/DOCX)"]
    end

    subgraph "External"
        SIGAA_EXT["SIGAA System"]
        Claude["Claude API"]
        Gmail["Gmail/SMTP"]
        GoogleEXT["Google APIs"]
    end

    DL -->|uses| SIGAA
    DL -->|uses| DB
    DL -->|uses| RAG
    DL -->|uses| Email
    DL -->|uses| Scheduler

    SIGAA -->|interacts| SIGAA_EXT
    RAG -->|calls| Claude
    RAG -->|uses| FileProc
    RAG -->|uses| Google
    
    Email -->|uses| Gmail
    Google -->|calls| GoogleEXT
    Scheduler -->|triggers| Email
    Scheduler -->|reads| DB

    FileProc -->|processes| RAG
    Google -->|syncs| FileProc

    style DL fill:#e8f5e9,stroke:#1b5e20
    style SIGAA fill:#fce4ec,stroke:#880e4f
    style DB fill:#eceff1,stroke:#263238
    style RAG fill:#fce4ec,stroke:#880e4f
    style Email fill:#fce4ec,stroke:#880e4f
    style Scheduler fill:#fce4ec,stroke:#880e4f
    style Google fill:#fce4ec,stroke:#880e4f
    style FileProc fill:#fce4ec,stroke:#880e4f
```

---

## 8. Estado da Aplicação (React Query)

```
┌─────────────────────────────────────────────────────────────┐
│             REACT QUERY CACHE STATE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  queryKey: ['lancamentos', tipo]                            │
│  ├─ status: 'loading' | 'error' | 'success'                │
│  ├─ data: Array<LancamentoConceito>                        │
│  ├─ error: HTTPException | null                            │
│  └─ isStale: boolean (revalidar?)                          │
│                                                              │
│  mutationKey: 'matricular'                                 │
│  ├─ status: 'idle' | 'pending' | 'success' | 'error'      │
│  ├─ isPending: boolean                                     │
│  └─ data: ResultadoOperacao                                │
│                                                              │
│  mutationKey: 'consolidar'                                 │
│  └─ (mesma estrutura)                                      │
│                                                              │
│  mutationKey: 'atualizarStatus'                            │
│  └─ (mesma estrutura)                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘

FLUXO:
1. useQuery(['lancamentos', tipo]) → fetch dados
2. Exibe tabela com dados
3. Usuário clica botão "Matricular"
4. matricularMutation.mutate(row) → POST request
5. Enquanto isPending:
   - Mostra loader
   - Desabilita botões
   - Exibe "⏳ Processando..."
6. onSuccess:
   - Toast sucesso
   - queryClient.invalidateQueries(['lancamentos'])
   - useQuery refetch automático
   - Tabela atualizada
7. onError:
   - Toast erro
   - Cache mantém dados antigos
```

---

## 9. Fluxo de Deploy

```
┌────────────────────────────────────────────────────────────┐
│  1. Developer commits to main branch                        │
└────────────────┬───────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────────┐
│  2. GitHub Actions triggers CI pipeline                    │
│     ├─ Run linters (Python/TypeScript)                     │
│     ├─ Run tests (pytest/Jest)                            │
│     ├─ Build Docker images                                │
│     │  ├─ fasitech-api:latest                             │
│     │  └─ fasitech-frontend:latest                        │
│     └─ Push to registry                                   │
└────────────────┬───────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────────┐
│  3. Production Deployment (Manual trigger)                 │
│     ├─ ssh ubuntu@72.60.6.113                             │
│     ├─ cd /home/ubuntu/appStreamLit/                      │
│     ├─ git pull origin main                               │
│     ├─ docker-compose -f docker-compose.production.yml \  │
│     │   pull && up -d --build                             │
│     ├─ Database migrations (auto)                         │
│     └─ Health checks                                      │
└────────────────┬───────────────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────────────┐
│  4. Verify Deployment                                      │
│     ├─ curl http://72.60.6.113:8000/health                │
│     ├─ curl http://72.60.6.113/                           │
│     └─ Check logs: docker-compose logs -f api             │
└────────────────────────────────────────────────────────────┘
```

---

## 10. Tabela de Rotas da API Completa

### `/api/v1/forms/` - Formulários
| Método | Rota | Função | Status |
|--------|------|--------|--------|
| POST | `/acc` | Submeter ACC | ✅ |
| POST | `/tcc` | Submeter TCC | ✅ |
| POST | `/estagio` | Submeter Estágio | ✅ |
| POST | `/plano-ensino` | Submeter Plano | ✅ |
| POST | `/projetos` | Submeter Projeto | ✅ |

### `/api/v1/data/` - Dados
| Método | Rota | Função | Status |
|--------|------|--------|--------|
| GET | `/social-data` | Dados sociais | ✅ |
| GET | `/projetos-data` | Lista projetos | ✅ |
| GET | `/tcc-data` | Lista TCC | ✅ |

### `/api/v1/ofertas/` - Ofertas
| Método | Rota | Função | Status |
|--------|------|--------|--------|
| GET | `/disciplinas` | Lista disciplinas | ✅ |

### `/api/v1/rag/` - RAG
| Método | Rota | Função | Status |
|--------|------|--------|--------|
| POST | `/diretor-virtual` | Chat com IA | ✅ |

### `/api/admin/` - Administração
| Método | Rota | Função | Status |
|--------|------|--------|--------|
| GET | `/lancamentos` | Listar lançamentos | ✅ |
| GET | `/lancamentos/componentes-validos` | Lista de componentes | ✅ |
| POST | `/lancamentos/matricular` | Matricular | ✅ |
| POST | `/lancamentos/consolidar` | Consolidar | ✅ |
| PATCH | `/lancamentos/atualizar-status` | Atualizar status | ✅ |
| GET | `/alertas` | Listar alertas | ✅ |

---

## Observações Importantes

### 1. **Padrão de Componente Expandido**
```python
# Input: ACC
# Expandir: ACC → [ACC I, ACC II, ACC III, ACC IV]
# Processar: Cada componente individualmente
# Resultado: Matrícula/Consolidação de todos os 4

COMPONENTES_EXPANDIDOS = {
    "ACC": ["ACC I", "ACC II", "ACC III", "ACC IV"],
    "TCC": ["TCC I", "TCC II"],
}
```

### 2. **Dynamic Imports**
```python
# Seleciona o módulo correto baseado no tipo
if componente_spec.startswith("TCC"):
    from backend.infrastructure.sigaa.matricular_tcc import executar_fluxo_direto
else:
    from backend.infrastructure.sigaa.matricular import executar_fluxo_direto
```

### 3. **Automatic Status Update**
```python
# Após executar a automação, atualiza status na DB
componentes_sucesso = [
    d.replace("SUCESSO: ", "") 
    for d in resultado.detalhes 
    if d.startswith("SUCESSO:")
]

for comp in componentes_sucesso:
    atualizar_status_lancamento(
        matricula=data.matricula,
        periodo=data.periodo,
        polo=data.polo,
        componente=comp,
        matriculado=True  # ou consolidado=True
    )
```

### 4. **Error Handling**
```python
# Coleta erros sem parar o processamento
erros = []
for componente in componentes:
    try:
        # executar
    except Exception as exc:
        erros.append(f"{componente}: {exc}")

# Retorna sucesso parcial mesmo com erros
if matriculados:  # se pelo menos 1 sucesso
    return ResultadoOperacao(
        sucesso=True,
        mensagem=f"...{len(matriculados)} sucesso(s)",
        detalhes=erros + [f"SUCESSO: {c}" for c in matriculados]
    )
```

### 5. **React Query Invalidation**
```typescript
// Invalida cache para forçar refetch
queryClient.invalidateQueries({ queryKey: ['lancamentos'] })

// useQuery automático refetch
const { data, isLoading } = useQuery({
    queryKey: ['lancamentos', tipo],
    queryFn: () => fetch data,
})
```

---

## Conclusão

A arquitetura FasiTech segue **Clean Architecture** com separação clara entre:
- **Domain**: Lógica pura de negócio
- **Infrastructure**: Implementações técnicas
- **Presentation**: APIs e interfaces

Cada **domínio de serviço** (SIGAA, RAG, Database, etc.) é independente e se comunica através de interfaces bem definidas, permitindo:
✅ Testabilidade
✅ Escalabilidade
✅ Manutenibilidade
✅ Integração futura de novos domínios
