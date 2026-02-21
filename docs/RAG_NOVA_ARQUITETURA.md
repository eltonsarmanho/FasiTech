# RAG do Diretor Virtual: Arquitetura e Fluxos

Este documento descreve a arquitetura atual do Diretor Virtual (RAG), incluindo o cache semântico e a política de qualidade `candidate/trusted`.

## 1. Objetivo

O módulo RAG responde perguntas sobre documentos oficiais da FASI usando:
- recuperação semântica de trechos relevantes,
- geração de resposta contextual por LLM,
- cache semântico governado por feedback do usuário.

## 2. Componentes

### 2.1 Interface
- **Usuário**: faz perguntas e avalia respostas.
- **`PageDiretorVirtual.py`**: interface Streamlit do chat e coleta de feedback (faces 1..5).

### 2.2 Serviço de Orquestração
- **`ChatbotService` (`src/services/rag_ppc.py`)**:
  - recebe pergunta (`ask_question`),
  - consulta cache semântico,
  - em caso de miss, executa fluxo RAG (retrieval + LLM),
  - registra métricas e histórico,
  - atualiza cache com feedback (`save_to_semantic_cache`).

### 2.3 Base de Conhecimento
- **Documentos fonte**: arquivos `*.md` em `src/resources/`.
- **`documents_hash`**: hash dos documentos (nome + tamanho + mtime), usado para detectar mudanças e invalidar cache antigo.

### 2.4 Camada Vetorial
- **LanceDB `recipes`**: índice vetorial de conteúdo RAG.
- **Embedder**: `OllamaEmbedder` (`nomic-embed-text`) para geração de embeddings.

### 2.5 Geração de Resposta
- **LLM**: Maritaca, Gemini ou fallback HuggingFace.
- Usa contexto recuperado do índice vetorial e instruções do agente.

### 2.6 Persistência de Conversa
- **SQLite `ppc_chat.db`**: histórico por sessão quando persistência está ativa.

### 2.7 Cache Semântico
- **LanceDB `semantic_cache`** com metadados de qualidade:
  - `question_key`, `documents_hash`,
  - `status` (`candidate` ou `trusted`),
  - `avg_rating`, `rating_count`, `confidence_score`,
  - `cached_at`, `last_feedback_at`, `expires_at`.

## 3. Fluxo de Consulta

1. Usuário envia pergunta na UI.
2. `ChatbotService.ask_question()` normaliza e embedda a pergunta.
3. Serviço busca candidatos no `semantic_cache` por similaridade (cosine).
4. Política valida se entrada é elegível para servir resposta:
   - `status=trusted`,
   - similaridade >= `0.90`,
   - `documents_hash` da entrada == hash atual,
   - não expirado por TTL.
5. Se **cache hit**, resposta retorna direto do cache.
6. Se **cache miss**:
   - busca semântica no índice `recipes`,
   - chamada ao LLM com contexto recuperado,
   - resposta retornada ao usuário,
   - histórico salvo em SQLite.

## 4. Fluxo de Feedback e Aprendizado

1. Usuário avalia resposta com nota de 1 a 5.
2. UI chama `save_to_semantic_cache(question, answer, rating)`.
3. Serviço recalcula métricas da entrada (`avg_rating`, `rating_count`, `confidence_score`).
4. Serviço aplica política de status e TTL.
5. Entrada é salva com **upsert** por `question_key + documents_hash`.

## 5. Política de Cache Semântico

### 5.1 Estados
- **`candidate`**: entrada em observação (não serve resposta para usuário).
- **`trusted`**: entrada aprovada para servir resposta em cache.

### 5.2 Regras
- Promoção para `trusted` quando:
  - `rating_count >= 2` **e**
  - `avg_rating >= 4.4`.
- Rebaixamento para `candidate` quando:
  - última avaliação `<= 2`.

### 5.3 TTL
- `trusted`: 30 dias.
- `candidate`: 14 dias.

### 5.4 Invalidação por mudança documental
Quando o conjunto de `.md` muda (`documents_hash` diferente):
- o índice vetorial é reindexado,
- entradas antigas deixam de ser elegíveis para servir respostas.

## 6. Reindexação e Resiliência

- O serviço detecta alteração de documentos via hash.
- Em reindexação, remove a tabela vetorial `recipes` antiga e reconstrói o índice.
- Em caso de corrupção/estado inconsistente do LanceDB, força recriação dos componentes vetoriais.

## 7. Observabilidade

`get_cache_stats()` expõe:
- total de entradas,
- quantidade `trusted`,
- quantidade `candidate`,
- threshold de similaridade.

## 8. Diagramas Relacionados

- Arquitetura de componentes: `Diagrama/RAG.wsd`
- Sequência de execução: `Diagrama/RAD_Sequencia.wsd`

## 9. Benefícios da Política Atual

- Reduz respostas cacheadas de baixa qualidade.
- Evita respostas desatualizadas após mudança de documentos.
- Mantém cache útil com governança por feedback real do usuário.
- Preserva desempenho sem abrir mão de confiabilidade.
