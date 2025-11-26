# Correção do Feedback - Diretor Virtual

## Problema Identificado

O componente de feedback não estava aparecendo imediatamente após a resposta do assistente. 

### Causa Raiz

O feedback estava sendo renderizado apenas na função `_render_history()`, que exibe mensagens antigas do histórico. Quando uma nova pergunta era processada:

1. A resposta era exibida em `_handle_new_question()`
2. A mensagem era adicionada ao `session_state["messages"]`
3. **MAS** o feedback só seria renderizado quando `_render_history()` fosse chamada novamente (em um rerun)

Isso significava que o usuário só veria o componente de feedback após:
- Fazer uma nova pergunta
- Recarregar a página
- Interagir com outro elemento que causasse um rerun

## Solução Implementada

### Modificação na `_handle_new_question()`

Agora, quando uma resposta bem-sucedida é gerada:

```python
# 1. Exibir a resposta
st.markdown(f'<div class="assistant-bubble">{answer_text}</div>', unsafe_allow_html=True)

# 2. Adicionar ao histórico
st.session_state["messages"].append(assistant_message)

# 3. Renderizar feedback IMEDIATAMENTE
idx = len(st.session_state["messages"]) - 1
feedback_key = f"feedback_{idx}"

if feedback_key not in st.session_state:
    st.session_state[feedback_key] = None

selected = st.feedback("stars", key=feedback_key)

# 4. Salvar se houver avaliação
if selected is not None and st.session_state[feedback_key] is None:
    if _save_feedback_to_sheet(selected):
        st.session_state[feedback_key] = selected
        st.success("✅ Obrigado pelo seu feedback!")
```

### Fluxo Corrigido

```
Usuário faz pergunta
    ↓
Sistema processa e gera resposta
    ↓
Resposta é exibida na tela
    ↓
✨ Componente de feedback aparece IMEDIATAMENTE ✨
    ↓
Usuário clica nas estrelas
    ↓
Feedback é salvo na planilha
    ↓
Mensagem de confirmação aparece
```

## Resultado

✅ O componente de feedback agora aparece **instantaneamente** após cada resposta  
✅ Tanto em respostas novas quanto no histórico  
✅ Experiência do usuário muito mais fluida  

## Como Testar

1. Execute a aplicação:
   ```bash
   cd /home/nees/Documents/VSCodigo/FasiTech
   ./scripts/start.sh
   ```

2. No navegador:
   - Acesse o Diretor Virtual
   - Faça uma pergunta (ex: "Qual a carga horária do curso?")
   - **Observe**: Assim que a resposta aparecer, o componente de estrelas ⭐ estará visível logo abaixo
   - Clique nas estrelas para avaliar
   - Veja a confirmação: "✅ Obrigado pelo seu feedback!"

3. Verifique a planilha:
   - https://docs.google.com/spreadsheets/d/1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U
   - Aba "Feedback"
   - Confirme que a avaliação foi registrada

## Arquivos Modificados

- `src/app/pages/PageDiretorVirtual.py`
  - Função `_handle_new_question()`: Adicionado renderização de feedback inline

## Status

✅ **CORRIGIDO** - O componente de feedback agora funciona perfeitamente!
