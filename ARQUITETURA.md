# 📐 Arquitetura do FasiTech

Bem-vindo! Este arquivo serve como **ponto de entrada** para entender a arquitetura do FasiTech.

## 🎯 Escolha Seu Nível

### 👶 **Iniciante - Quero entender rápido**
Comece com: **[Arquitetura Visual Resumida](./docs/ARQUITETURA_VISUAL_RESUMIDA.md)**

📋 Conteúdo:
- Stack do sistema em 30 segundos
- Arquitetura em 4 camadas
- 8 domínios principais
- Fluxos principais em ASCII
- Estrutura de arquivos simplificada
- Tempo: ~10 minutos

---

### 🎓 **Desenvolvedor - Quero ver tudo integrado**
Comece com: **[Arquitetura do Sistema](./docs/ARQUITETURA_SISTEMA.md)**

📊 Conteúdo:
- Diagrama Mermaid completo interativo
- Todas as camadas (Frontend → API → Domain → Infrastructure → External)
- Detalhamento de cada domínio
- Stack tecnológico por camada
- Organização de código
- Responsabilidades por domínio
- Tempo: ~20 minutos

---

### 🔬 **Arquiteto - Quero entender os fluxos**
Comece com: **[Fluxos de Integração](./docs/FLUXOS_INTEGRACAO.md)**

🔄 Conteúdo:
- 10 fluxos sequenciais detalhados com Mermaid
  - Matrícula e Consolidação (end-to-end)
  - Atualização Manual de Status
  - RAG: Diretor Virtual
  - Processamento de Formulário
  - Scheduler: Alertas
  - Google Drive Sync
  - Deploy pipeline
- Matriz de dependências
- Estado da aplicação (React Query)
- Tabela de rotas da API
- Tempo: ~30 minutos

---

### 🧩 **Engenheiro - Preciso entender componentes**
Comece com: **[Componentes da Arquitetura](./docs/COMPONENTES_ARQUITETURA.md)**

🔧 Conteúdo:
- Diagrama de componentes interconectados
- 5 funcionalidades principais decompostas
- Matriz de responsabilidades
- Padrões de integração
- Fluxo de dados entre componentes
- Como adicionar nova funcionalidade
- Tempo: ~25 minutos

---

## 🗺️ Mapa Visual Completo

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  ARQUITETURA_VISUAL_RESUMIDA.md (10 min) ⭐ COMECE AQUI    │
│  └─ Visão geral rápida                                     │
│                                                              │
│  ARQUITETURA_SISTEMA.md (20 min)                           │
│  └─ Diagrama integrado completo com Mermaid               │
│  └─ Detalhamento de cada domínio                           │
│                                                              │
│  FLUXOS_INTEGRACAO.md (30 min)                             │
│  └─ 10 sequências detalhadas                               │
│  └─ Matriz de dependências                                 │
│                                                              │
│  COMPONENTES_ARQUITETURA.md (25 min)                       │
│  └─ 5 funcionalidades decompostas                          │
│  └─ Padrões de integração                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Qual Documento Ler?

| Seu Objetivo | Documento | Tempo |
|---|---|---|
| **Entender a visão geral** | VISUAL_RESUMIDA | 10min |
| **Ver tudo junto integrado** | ARQUITETURA_SISTEMA | 20min |
| **Entender fluxos de dados** | FLUXOS_INTEGRACAO | 30min |
| **Decompor funcionalidades** | COMPONENTES_ARQUITETURA | 25min |
| **Implementar novo domínio** | Todos + código | 1-2h |
| **Troubleshooting de erro** | FLUXOS_INTEGRACAO | 15min |
| **Onboarding de novo dev** | VISUAL_RESUMIDA → ARQUITETURA_SISTEMA | 30min |

---

## 📚 Estrutura dos Documentos

### 1️⃣ ARQUITETURA_VISUAL_RESUMIDA.md
```
├─ Stack do Sistema
├─ Arquitetura em 4 Camadas
├─ Domínios Principais
├─ Fluxos Principais (3 principais)
├─ Estrutura de Arquivos
├─ APIs Disponíveis
├─ Padrões e Convenções
├─ Status do Sistema
├─ Como Adicionar Funcionalidade
├─ Princípios de Arquitetura
└─ Próximas Evoluções
```

### 2️⃣ ARQUITETURA_SISTEMA.md
```
├─ Visão Integrada (Diagrama Mermaid)
├─ Domínios de Serviço Detalhados
│  ├─ Presentation Layer (7 APIs)
│  ├─ Domain Layer (Entities, Use Cases, Repositories)
│  └─ Infrastructure Layer (7 domínios)
├─ Fluxos de Dados Principais (3)
├─ Stack Tecnológico
├─ Dependências e Fluxos de Controle
├─ Organização de Código
├─ Responsabilidades por Domínio
├─ CI/CD Pipeline
└─ Configuração de Ambiente
```

### 3️⃣ FLUXOS_INTEGRACAO.md
```
├─ Fluxo 1: Matrícula e Consolidação (Sequence Diagram)
├─ Fluxo 2: Atualização Manual de Status (Sequence Diagram)
├─ Fluxo 3: RAG - Diretor Virtual (Sequence Diagram)
├─ Fluxo 4: Processamento de Formulário ACC (Sequence Diagram)
├─ Fluxo 5: Scheduler - Geração de Alertas (Sequence Diagram)
├─ Fluxo 6: Google Drive Sync (Sequence Diagram)
├─ Fluxo 7: Matriz de Dependências (Dependency Graph)
├─ Fluxo 8: Estado da Aplicação (React Query)
├─ Fluxo 9: Deploy Pipeline
├─ Fluxo 10: Rotas da API Completa (Tabela)
└─ Observações Importantes (Padrões)
```

### 4️⃣ COMPONENTES_ARQUITETURA.md
```
├─ Visão Geral (Component Diagram)
├─ Funcionalidade 1: Lançamento de Conceitos
├─ Funcionalidade 2: Processamento de Formulários
├─ Funcionalidade 3: RAG - Diretor Virtual
├─ Funcionalidade 4: Scheduler - Alertas
├─ Funcionalidade 5: Google Drive Sync
├─ Matriz de Responsabilidades
├─ Padrões de Integração (4)
├─ Fluxo de Dados entre Componentes
└─ Como Adicionar Funcionalidade
```

---

## 🔑 Conceitos-Chave Explicados

### **Component Expansion Pattern**
```python
# ACC pode ser genérico ou específico
Input: "ACC"  →  Expand: ["ACC I", "ACC II", "ACC III", "ACC IV"]
                 Process each independently
                 Return success/error for each
```
📖 Visto em: [FLUXOS_INTEGRACAO.md](./docs/FLUXOS_INTEGRACAO.md#padrão-1-service--multiple-repositories)

### **Dynamic Module Imports**
```python
# Seleciona implementação baseado no tipo
if componente.startswith("TCC"):
    from backend.infrastructure.sigaa.matricular_tcc import ...
else:
    from backend.infrastructure.sigaa.matricular import ...
```
📖 Visto em: [FLUXOS_INTEGRACAO.md](./docs/FLUXOS_INTEGRACAO.md#padrão-2-dynamic-module-import)

### **Repository Pattern**
```python
# Domain define interface
# Infrastructure implementa
# Desacoplamento perfeito
```
📖 Visto em: [COMPONENTES_ARQUITETURA.md](./docs/COMPONENTES_ARQUITETURA.md#por-camada)

### **React Query with Mutations**
```typescript
// Fetch + Cache + Refetch automático
useQuery(['lancamentos'], ...)
useMutation(..., { onSuccess: () => invalidate() })
```
📖 Visto em: [FLUXOS_INTEGRACAO.md](./docs/FLUXOS_INTEGRACAO.md#padrão-3-react-query-with-mutations)

---

## 🚀 Quick Links

| Documento | Diagrama Principal | Tipo |
|-----------|-------------------|------|
| [VISUAL_RESUMIDA](./docs/ARQUITETURA_VISUAL_RESUMIDA.md) | ASCII Art | Resumo |
| [ARQUITETURA_SISTEMA](./docs/ARQUITETURA_SISTEMA.md) | Mermaid Graph TB | Visão Geral |
| [FLUXOS_INTEGRACAO](./docs/FLUXOS_INTEGRACAO.md) | Mermaid Sequence (10x) | Detalhado |
| [COMPONENTES_ARQUITETURA](./docs/COMPONENTES_ARQUITETURA.md) | Mermaid Graph LR | Componentes |

---

## 💡 Exemplos de Uso

### Cenário 1: "Secretário clica Matricular"
👉 Leia: [Fluxo 1: Matrícula](./docs/FLUXOS_INTEGRACAO.md#1-fluxo-completo-matrícula-e-consolidação-end-to-end)
⏱️ Tempo: 5 minutos

### Cenário 2: "Aluno pergunta para o Diretor Virtual"
👉 Leia: [Fluxo 3: RAG](./docs/FLUXOS_INTEGRACAO.md#3-fluxo-rag-diretor-virtual-chat-com-ia)
⏱️ Tempo: 5 minutos

### Cenário 3: "Adicionar novo domínio/API"
👉 Leia: [Como Adicionar](./docs/ARQUITETURA_VISUAL_RESUMIDA.md#9-como-adicionar-nova-funcionalidade)
⏱️ Tempo: 10 minutos

### Cenário 4: "Erro em produção - rastrear problema"
👉 Leia: [Todos os Fluxos](./docs/FLUXOS_INTEGRACAO.md)
⏱️ Tempo: 20 minutos

---

## 🎬 Começar Agora

```bash
# Option 1: Leitura rápida (10 min)
cat docs/ARQUITETURA_VISUAL_RESUMIDA.md

# Option 2: Visualização integrada (20 min)
cat docs/ARQUITETURA_SISTEMA.md

# Option 3: Entender fluxos (30 min)
cat docs/FLUXOS_INTEGRACAO.md

# Option 4: Estudar componentes (25 min)
cat docs/COMPONENTES_ARQUITETURA.md
```

---

## 📝 Índice de Conteúdo (Todos os Documentos)

### VISUAL_RESUMIDA.md
- ✅ Stack do Sistema
- ✅ Arquitetura em 4 Camadas
- ✅ 8 Domínios Principais
- ✅ 3 Fluxos Principais
- ✅ Estrutura de Arquivos
- ✅ APIs Disponíveis (26 endpoints)
- ✅ Padrões e Convenções
- ✅ Status do Sistema
- ✅ Princípios de Arquitetura
- ✅ Próximas Evoluções

### ARQUITETURA_SISTEMA.md
- ✅ Diagrama Mermaid completo
- ✅ Detalhamento de cada domínio
- ✅ 3 Presentation Layers
- ✅ Domain Layer + Use Cases
- ✅ 7 Infrastructure Domains
- ✅ Stack Tecnológico (13 tecnologias)
- ✅ CI/CD Pipeline
- ✅ Configuração por Ambiente

### FLUXOS_INTEGRACAO.md
- ✅ 10 Sequence Diagrams detalhados
- ✅ Fluxo End-to-End de Matrícula
- ✅ Fluxo de Atualização de Status
- ✅ Fluxo RAG com Cache
- ✅ Fluxo de Processamento de Formulário
- ✅ Fluxo de Scheduler
- ✅ Fluxo de Google Drive
- ✅ Matriz de Dependências
- ✅ Deploy Pipeline
- ✅ Tabela de Rotas (26 endpoints)

### COMPONENTES_ARQUITETURA.md
- ✅ Component Diagram completo
- ✅ 5 Funcionalidades decompostas
- ✅ 5 Detalhes por funcionalidade
- ✅ Matriz de Responsabilidades
- ✅ 4 Padrões de Integração
- ✅ Fluxo de Dados
- ✅ Como Adicionar Funcionalidade

---

## 🔗 Localização dos Arquivos

```
FasiTech/
├── ARQUITETURA.md (este arquivo) ← Você está aqui
└── docs/
    ├── README.md (com links para arquitetura)
    ├── ARQUITETURA_SISTEMA.md ← Comece aqui se desenvolvedor
    ├── FLUXOS_INTEGRACAO.md ← Comece aqui se arquiteto
    ├── COMPONENTES_ARQUITETURA.md ← Comece aqui se engenheiro
    └── ARQUITETURA_VISUAL_RESUMIDA.md ← Comece aqui se iniciante
```

---

## 👥 Para Quem É?

| Perfil | Comece Por | Depois Leia |
|--------|-----------|-------------|
| **Iniciante no projeto** | VISUAL_RESUMIDA | ARQUITETURA_SISTEMA |
| **Frontend Developer** | COMPONENTES_ARQUITETURA | FLUXOS_INTEGRACAO |
| **Backend Developer** | ARQUITETURA_SISTEMA | FLUXOS_INTEGRACAO |
| **Arquiteto/Tech Lead** | ARQUITETURA_SISTEMA | Todos |
| **DevOps/SRE** | FLUXOS_INTEGRACAO (Deploy) | ARQUITETURA_SISTEMA |
| **QA/Tester** | FLUXOS_INTEGRACAO | COMPONENTES_ARQUITETURA |
| **Product Manager** | VISUAL_RESUMIDA | Nenhum outro necessário |

---

## 🎓 Roteiros de Aprendizado

### 🎯 Roteiro 1: Developer Onboarding (2 horas)
1. ARQUITETURA_VISUAL_RESUMIDA.md (10 min)
2. ARQUITETURA_SISTEMA.md (20 min)
3. Explorar código local (30 min)
4. FLUXOS_INTEGRACAO.md - Ler funcionalidade do seu domínio (20 min)
5. Executar localmente e testar (40 min)

### 🏗️ Roteiro 2: Entender Arquitetura Completa (3 horas)
1. VISUAL_RESUMIDA.md (10 min)
2. ARQUITETURA_SISTEMA.md (20 min)
3. FLUXOS_INTEGRACAO.md (30 min)
4. COMPONENTES_ARQUITETURA.md (25 min)
5. Revisar diagramas e fazer anotações (15 min)
6. Explorar código fonte (60 min)

### 🚀 Roteiro 3: Adicionar Nova Funcionalidade (4 horas)
1. VISUAL_RESUMIDA - Seção "Como Adicionar" (10 min)
2. COMPONENTES_ARQUITETURA - Ver exemplo de funcionalidade (15 min)
3. FLUXOS_INTEGRACAO - Estudar fluxo parecido (20 min)
4. ARQUITETURA_SISTEMA - Revisar layer relevante (15 min)
5. Implementar funcionalidade (3 horas)

---

## ✅ Checklist: Você Entendeu a Arquitetura?

Depois de ler os documentos, consegue responder?

- [ ] O que é Clean Architecture e como FasiTech a implementa?
- [ ] Quais são os 8 domínios principais?
- [ ] Como matrícula flui de Frontend → Database?
- [ ] O que é Component Expansion Pattern?
- [ ] Como RAG funciona end-to-end?
- [ ] Qual é a stack tecnológico?
- [ ] Como React Query se integra com o backend?
- [ ] O que é Repository Pattern e por quê usar?
- [ ] Como adicionar uma nova API?
- [ ] Qual é o fluxo de deploy?

**Se respondeu ✅ para 8+**: Parabéns! Você domina a arquitetura 🎉

---

## 📞 Precisa de Ajuda?

- **Entender diagrama específico**: Procure o arquivo e a seção
- **Entender um fluxo**: Vá para FLUXOS_INTEGRACAO.md
- **Entender uma funcionalidade**: Vá para COMPONENTES_ARQUITETURA.md
- **Visão completa**: Vá para ARQUITETURA_SISTEMA.md
- **Resumo rápido**: Vá para VISUAL_RESUMIDA.md

---

## 🎉 Última Coisa

Todos os diagramas usam **Mermaid** e podem ser visualizados no GitHub ou usando ferramentas online como [mermaid.live](https://mermaid.live).

Se visualizar em VS Code, instale a extensão "Markdown Preview Mermaid Support".

---

**Criado em**: 17 de Maio de 2026  
**Stack**: FasiTech v2.0 - Clean Architecture + DDD  
**Documentação**: Completa e atualizada ✅
