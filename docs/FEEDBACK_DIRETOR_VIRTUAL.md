# Sistema de Feedback do Diretor Virtual

## Visão Geral

O módulo Diretor Virtual agora possui um sistema de feedback integrado que permite aos usuários avaliarem a qualidade das respostas fornecidas pelo assistente de IA.

## Funcionalidades

- **Avaliação por Estrelas**: Os usuários podem avaliar cada resposta do assistente usando um sistema de 1 a 5 estrelas
- **Armazenamento Automático**: As avaliações são salvas automaticamente em uma planilha do Google Sheets
- **Histórico de Feedback**: Todas as avaliações incluem data/hora e pontuação

## Configuração

### 1. Planilha do Google Sheets

A planilha de feedback deve ter a seguinte estrutura:

**Nome da aba**: `Feedback`

**Colunas**:
- `Data`: Data e hora da avaliação (formato: YYYY-MM-DD HH:MM:SS)
- `Avaliação`: Pontuação de 1 a 5 (valores discretos)

### 2. Configuração no secrets.toml

Adicione a seguinte configuração em `.streamlit/secrets.toml`:

```toml
[AvalicaoDiretorVirtual]
sheet_id = "SEU_SHEET_ID_AQUI"
```

**Exemplo**:
```toml
[AvalicaoDiretorVirtual]
sheet_id = "1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U"
```

### 3. Permissões do Google Drive

Certifique-se de que a conta de serviço configurada no projeto tem permissão de **Editor** na planilha de feedback.

## Como Usar

### Para Usuários

1. Após fazer uma pergunta ao Diretor Virtual, aguarde a resposta
2. Logo abaixo da resposta, você verá um componente de avaliação por estrelas
3. Clique na quantidade de estrelas que representa sua satisfação:
   - ⭐ (1 estrela): Muito insatisfeito
   - ⭐⭐ (2 estrelas): Insatisfeito
   - ⭐⭐⭐ (3 estrelas): Neutro
   - ⭐⭐⭐⭐ (4 estrelas): Satisfeito
   - ⭐⭐⭐⭐⭐ (5 estrelas): Muito satisfeito
4. Após selecionar, você verá uma mensagem de confirmação
5. O feedback é registrado automaticamente na planilha

### Para Administradores

#### Acessar os Dados de Feedback

1. Acesse a planilha configurada no `secrets.toml`
2. Navegue até a aba `Feedback`
3. Os dados estarão organizados por data/hora

#### Analisar as Métricas

Você pode usar as seguintes fórmulas no Google Sheets para análise:

**Média de Avaliações**:
```
=AVERAGE(B2:B)
```

**Total de Avaliações**:
```
=COUNTA(B2:B)
```

**Distribuição por Estrelas**:
```
=COUNTIF(B2:B, 1)  // Quantidade de avaliações com 1 estrela
=COUNTIF(B2:B, 2)  // Quantidade de avaliações com 2 estrelas
... e assim por diante
```

## Arquitetura Técnica

### Fluxo de Dados

```
Usuário clica nas estrelas
    ↓
st.feedback("stars") captura o valor (0-4)
    ↓
_save_feedback_to_sheet() converte para (1-5)
    ↓
append_rows() adiciona linha na planilha
    ↓
Confirmação visual para o usuário
```

### Código Principal

**Arquivo**: `src/app/pages/PageDiretorVirtual.py`

**Funções relevantes**:
- `_save_feedback_to_sheet(rating: int)`: Salva o feedback na planilha
- `_render_history()`: Renderiza o histórico e componentes de feedback

### Conversão de Valores

O componente `st.feedback("stars")` retorna valores de **0 a 4**, mas salvamos na planilha como **1 a 5** para melhor compreensão:

```python
rating_saved = rating_streamlit + 1
```

| Streamlit | Planilha |
|-----------|----------|
| 0         | 1        |
| 1         | 2        |
| 2         | 3        |
| 3         | 4        |
| 4         | 5        |

## Troubleshooting

### Erro: "Credenciais do Google não encontradas"

**Solução**: Verifique se a variável `GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64` ou `GOOGLE_CLOUD_CREDENTIALS_BASE64` está configurada no `.env`

### Erro: "Permissão negada ao salvar feedback"

**Solução**: Confirme que a conta de serviço tem permissão de **Editor** na planilha de feedback

### Feedback não está sendo salvo

**Verificações**:
1. Confirme que o `sheet_id` em `secrets.toml` está correto
2. Verifique se a aba `Feedback` existe na planilha
3. Confirme que as colunas `Data` e `Avaliação` existem (exatamente com esses nomes)
4. Verifique os logs do Streamlit para mensagens de erro

### Mensagem de sucesso aparece mas dados não estão na planilha

**Solução**: 
1. Aguarde alguns segundos e recarregue a planilha
2. Verifique se não há filtros ativos na planilha
3. Confirme que você está olhando a aba correta (`Feedback`)

## Exemplos de Uso

### Criar Gráficos de Análise

No Google Sheets, você pode criar:

1. **Gráfico de Pizza**: Distribuição de avaliações
2. **Gráfico de Linha**: Evolução temporal das avaliações
3. **Gráfico de Barras**: Comparação entre diferentes períodos

### Exportar Dados

Para análises mais avançadas:

```python
import pandas as pd
from src.services.google_sheets import read_sheet_tab

df = read_sheet_tab(
    sheet_id="1HDGlJi9Uu2NX7MI0032BwGUWYpzSfNJAQWWsq4UJ07U",
    tab_name="Feedback"
)

# Análise com pandas
print(df['Avaliação'].value_counts())
print(df['Avaliação'].mean())
```

## Próximas Melhorias

- [ ] Adicionar campo de comentário opcional
- [ ] Implementar dashboard de métricas em tempo real
- [ ] Exportar relatórios automáticos
- [ ] Integração com sistema de notificações para avaliações baixas
- [ ] Análise de sentimento nos comentários (quando implementado)

## Referências

- [Documentação do st.feedback](https://docs.streamlit.io/library/api-reference/widgets/st.feedback)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Serviço google_sheets.py](../src/services/google_sheets.py)
