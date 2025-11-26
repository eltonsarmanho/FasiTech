# Sistema de Feedback - Guia Rápido

## ✅ Implementação Concluída

O sistema de feedback foi implementado com sucesso na página do Diretor Virtual!

## 🚀 Como Testar

### 1. Configurar a Planilha

Execute o script de configuração:

```bash
cd /home/nees/Documents/VSCodigo/FasiTech
python scripts/setup_feedback_sheet.py
```

Este script irá:
- ✅ Verificar se a planilha está acessível
- ✅ Criar a aba "Feedback" (se não existir)
- ✅ Adicionar os cabeçalhos "Data" e "Avaliação"
- ✅ Inserir um feedback de teste

### 2. Executar a Aplicação

```bash
cd /home/nees/Documents/VSCodigo/FasiTech
./scripts/start.sh
```

### 3. Testar o Feedback

1. Acesse a página do Diretor Virtual no navegador
2. Faça uma pergunta ao assistente (ex: "Qual a carga horária do curso?")
3. Aguarde a resposta
4. Você verá um componente de avaliação por estrelas (⭐) abaixo da resposta
5. Clique em uma das estrelas para avaliar (1-5)
6. Aparecerá uma mensagem: "✅ Obrigado pelo seu feedback!"

### 4. Verificar os Dados

Acesse a planilha:
```
https://docs.google.com/spreadsheets/d/1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U
```

Navegue até a aba **"Feedback"** e verifique se os dados estão sendo salvos corretamente.

## 📊 Estrutura dos Dados

| Data | Avaliação |
|------|-----------|
| 2025-11-26 10:30:45 | 5 |
| 2025-11-26 11:15:22 | 4 |
| 2025-11-26 14:20:10 | 3 |

## 🎯 Funcionalidades Implementadas

- ✅ Componente de avaliação por estrelas (`st.feedback("stars")`)
- ✅ Salvamento automático em Google Sheets
- ✅ Timestamp de cada avaliação
- ✅ Conversão correta de valores (0-4 → 1-5)
- ✅ Feedback visual de confirmação
- ✅ Integração com `secrets.toml`
- ✅ Tratamento de erros
- ✅ Documentação completa

## 📁 Arquivos Modificados/Criados

### Modificados
- `src/app/pages/PageDiretorVirtual.py`: Implementação do feedback

### Criados
- `docs/FEEDBACK_DIRETOR_VIRTUAL.md`: Documentação completa
- `scripts/setup_feedback_sheet.py`: Script de configuração
- `docs/FEEDBACK_QUICKSTART.md`: Este guia

### Configuração
- `.streamlit/secrets.toml`: Já contém a configuração necessária:
  ```toml
  [AvalicaoDiretorVirtual]
  sheet_id = "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U"
  ```

## 🔧 Troubleshooting

### Erro de permissão
- Verifique se a conta de serviço tem acesso à planilha
- Execute novamente `scripts/setup_feedback_sheet.py`

### Feedback não aparece
- Verifique se está fazendo perguntas (não apenas vendo a mensagem de boas-vindas)
- O feedback só aparece para respostas do assistente

### Dados não salvam
- Confirme que o `sheet_id` está correto em `secrets.toml`
- Verifique se a aba "Feedback" existe
- Execute o script de setup novamente

## 📚 Documentação Completa

Para mais detalhes, consulte:
- [FEEDBACK_DIRETOR_VIRTUAL.md](./FEEDBACK_DIRETOR_VIRTUAL.md)

## 🎉 Pronto!

O sistema está pronto para uso em produção. Todos os feedbacks dos usuários serão automaticamente registrados na planilha para análise posterior.
