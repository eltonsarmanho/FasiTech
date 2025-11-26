# Atualização: Pergunta e Resposta no Feedback

## Implementação Concluída ✅

Agora o sistema de feedback salva **4 informações** na planilha:

1. **Data** - Timestamp do feedback
2. **Avaliação** - Nota de 1 a 5 estrelas
3. **Pergunta** - A pergunta feita pelo usuário
4. **Resposta** - A resposta dada pelo assistente

## Estrutura da Planilha

### Antes (2 colunas):
| A - Data | B - Avaliação |
|----------|---------------|
| 2025-11-26 17:05:08 | 5 |

### Depois (4 colunas):
| A - Data | B - Avaliação | C - Pergunta | D - Resposta |
|----------|---------------|--------------|--------------|
| 2025-11-26 17:29:58 | 5 | Qual a carga horária do curso? | O curso de Sistemas de Informação tem uma carga horária total de 3.060 horas... |

## Benefícios da Mudança

✅ **Contexto completo**: Agora é possível entender **o que** foi avaliado  
✅ **Análise qualitativa**: Identificar quais tipos de perguntas recebem melhores/piores avaliações  
✅ **Melhoria contínua**: Analisar respostas que receberam avaliações baixas  
✅ **Relatórios detalhados**: Gerar relatórios com contexto completo  
✅ **Rastreabilidade**: Saber exatamente qual interação foi avaliada  

## Alterações Técnicas

### 1. Função `_save_feedback_to_sheet()`

**Antes**:
```python
def _save_feedback_to_sheet(rating: int) -> bool:
    # ...
    values = [[timestamp, str(avaliacao)]]
    # ...
    range='Feedback!A:B'
```

**Depois**:
```python
def _save_feedback_to_sheet(rating: int, pergunta: str = "", resposta: str = "") -> bool:
    # ...
    values = [[timestamp, str(avaliacao), pergunta, resposta]]
    # ...
    range='Feedback!A:D'  # 4 colunas agora
```

### 2. Chamadas da Função

#### Em `_render_history()`:
```python
# Buscar a pergunta anterior (mensagem do usuário)
pergunta = ""
if idx > 0 and st.session_state["messages"][idx - 1]["role"] == "user":
    pergunta = st.session_state["messages"][idx - 1]["content"]

resposta = message.get("content", "")

if _save_feedback_to_sheet(selected, pergunta, resposta):
    st.session_state[feedback_saved_key] = True
    st.rerun()
```

#### Em `_handle_new_question()`:
```python
# A pergunta e resposta já estão disponíveis no contexto
if _save_feedback_to_sheet(selected, question, answer_text):
    st.session_state[feedback_saved_key] = True
    st.success("✅ Feedback registrado com sucesso!")
    st.rerun()
```

## Scripts Atualizados

### 1. `scripts/test_feedback_save.py`
- Agora testa com 4 colunas
- Inclui pergunta e resposta de exemplo

### 2. `scripts/setup_feedback_sheet.py`
- Cria aba com 4 colunas
- Cabeçalhos: Data | Avaliação | Pergunta | Resposta
- Teste de inserção com dados completos

## Como Testar

### 1. Atualizar os cabeçalhos da planilha existente

Se a aba "Feedback" já existir, você precisa adicionar manualmente as colunas C e D:

1. Acesse: https://docs.google.com/spreadsheets/d/1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U
2. Aba "Feedback"
3. Adicione na célula **C1**: `Pergunta`
4. Adicione na célula **D1**: `Resposta`

Ou execute o script de setup novamente (irá recriar a aba):
```bash
cd /home/nees/Documents/VSCodigo/FasiTech
./venv/bin/python scripts/setup_feedback_sheet.py
```

### 2. Testar o salvamento

```bash
./venv/bin/python scripts/test_feedback_save.py
```

Resultado esperado:
```
✅ SUCESSO! Feedback salvo na planilha!
   Data: 2025-11-26 17:29:58
   Avaliação: 5 estrelas
   Pergunta: Qual a carga horária do curso?
   Resposta: O curso de Sistemas de Informação tem uma carga horária tota...
```

### 3. Testar na aplicação

1. Execute: `./scripts/start.sh`
2. Acesse o Diretor Virtual
3. Faça uma pergunta
4. Avalie a resposta
5. Clique em "Confirmar Avaliação"
6. Verifique a planilha

## Exemplo de Dados Salvos

```
Data                | Avaliação | Pergunta                              | Resposta
--------------------|-----------|---------------------------------------|------------------------------------------
2025-11-26 17:30:15 | 5         | Qual a carga horária do curso?       | O curso de Sistemas de Informação tem...
2025-11-26 17:32:40 | 4         | Quais disciplinas do primeiro período?| As disciplinas do 1º período são...
2025-11-26 17:35:22 | 3         | Como funciona o TCC?                 | O TCC é desenvolvido em duas etapas...
```

## Análises Possíveis

Com os novos dados, você pode:

### 1. Identificar Temas Problemáticos
```sql
-- Perguntas com avaliações baixas (≤2)
SELECT Pergunta, AVG(Avaliação) as Media
FROM Feedback
WHERE Avaliação <= 2
GROUP BY Pergunta
```

### 2. Melhores Respostas
```sql
-- Respostas mais bem avaliadas
SELECT Pergunta, Resposta, Avaliação
FROM Feedback
WHERE Avaliação = 5
ORDER BY Data DESC
LIMIT 10
```

### 3. Taxa de Satisfação por Tema
```
- Perguntas sobre "carga horária": 4.5 de média
- Perguntas sobre "TCC": 4.2 de média
- Perguntas sobre "disciplinas": 4.8 de média
```

### 4. Análise Temporal
```
- Manhã (6h-12h): média 4.3
- Tarde (12h-18h): média 4.5
- Noite (18h-24h): média 4.1
```

## Arquivos Modificados

✅ `src/app/pages/PageDiretorVirtual.py`
   - Função `_save_feedback_to_sheet()`: Novos parâmetros e 4 colunas
   - `_render_history()`: Extrai pergunta e resposta do histórico
   - `_handle_new_question()`: Usa pergunta e resposta do contexto

✅ `scripts/test_feedback_save.py`
   - Teste com 4 colunas

✅ `scripts/setup_feedback_sheet.py`
   - Cria aba com 4 colunas
   - Cabeçalhos completos
   - Teste de inserção atualizado

## Status

✅ **IMPLEMENTADO E TESTADO**

- ✅ Função atualizada para 4 colunas
- ✅ Chamadas atualizadas em ambos os locais
- ✅ Scripts de teste funcionando
- ✅ Dados sendo salvos corretamente
- ✅ Teste automatizado passando

## Próximos Passos

- [ ] Dashboard de análise de feedback
- [ ] Alertas para avaliações baixas
- [ ] Relatório semanal de satisfação
- [ ] Análise de sentimento nas respostas
- [ ] Identificação automática de temas problemáticos
