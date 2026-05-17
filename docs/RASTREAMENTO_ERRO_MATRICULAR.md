# Rastreamento Detalhado do Erro na Matriculação SIGAA

## Execução do Teste (2026-05-17 23:50)

### Fluxo Esperado vs Real

#### ✅ Etapas que Funcionaram
1. **Login** - Sucesso
   - URL: `https://sigaa.ufpa.br/sigaa/verTelaLogin.do`
   - Preenchimento de login e senha funcionou
   - Navegação concluída

2. **Calendário de Períodos** - Carregado Corretamente
   - URL: `https://sigaa.ufpa.br/sigaa/calendarios_graduacao_vigentes.jsf`
   - Página carregada com sucesso

#### 🔴 Etapas com Problema

##### 1. **Seleção de Período (2026.1)**
```
WARNING: Período não encontrado com variações. Tentando fallback...
```
- **Esperado**: Encontrar e clicar no link "2026.1" na página de calendário
- **Real**: Período não encontrado com nenhuma variação (2026.1, 2026-1, etc.)
- **Causa Provável**: 
  - O período não está visível na página
  - Ou tem uma formatação diferente da esperada
  - Ou está em um menu/dropdown diferente

##### 2. **Navegação para Busca de Atividade**
- **URL Alcançada**: `https://sigaa.ufpa.br/sigaa/graduacao/registro_atividade/busca_atividade.jsf`
- **URL Esperada**: `https://sigaa.ufpa.br/sigaa/graduacao/registro_atividade/dados_registro.jsf`
- **O que significa**: 
  - A navegação pulou etapas
  - Está na página de BUSCA de atividades em vez de CONFIRMAÇÃO de dados
  - O botão "Próximo" clicado navegou para o lugar errado

##### 3. **Erro Final**
```
ERROR: Esperava dados_registro.jsf mas recebeu: busca_atividade.jsf
Este é o ponto de falha - SIGAA pode ter mudado sua navegação
```

## Análise das Causas Raiz

### Problema 1: Período não Encontrado
**Linha de Log**:
```
[MATRICULAR] Selecionando período: 2026.1
WARNING: Período não encontrado com variações. Tentando fallback...
```

**Investigação Necessária**:
1. Acessar SIGAA manualmente após login
2. Verificar como o período 2026.1 é exibido
3. Encontrar o seletor CSS correto

**Possíveis Soluções**:
- O período pode estar em um `<select>` em vez de links `<a>`
- Pode estar em um formulário diferente
- Pode estar oculto até fazer scroll

### Problema 2: Navegação para URL Errada
**Linha de Log**:
```
[MATRICULAR] Botão de confirmação clicado: True
[MATRICULAR] Aguardando navegação para dados_registro.jsf...
[MATRICULAR] URL final: busca_atividade.jsf
```

**O que significa**:
- O script clicou em um botão que navega para `busca_atividade.jsf` em vez de `dados_registro.jsf`
- Este é um botão diferente do esperado

**Causa Provável**:
- A sequência de navegação SIGAA mudou
- O layout ou nomes de botões podem ter mudado
- O formulário pode ter uma estrutura diferente

## Próximos Passos

### 1. Inspecionar SIGAA Manualmente
```bash
1. Fazer login em https://sigaa.ufpa.br/sigaa/verTelaLogin.do
2. Anotar como o período aparece
3. Rastrear o caminho de navegação até dados_registro.jsf
4. Anotar nomes/IDs de botões em cada etapa
```

### 2. Atualizar os Seletores
- Modificar `variacoes_periodo()` para encontrar o período
- Atualizar seletores de período na página de calendário
- Possivelmente adicionar suporte para `<select>` elementos

### 3. Corrigir Navegação
- Encontrar o botão/formulário correto que leva a `dados_registro.jsf`
- Atualizar seletores em `clicar_primeiro_visivel()`
- Validar navegação esperada

## Comandos para Teste Manual

### Obter Token FASI
```bash
FASI_TOKEN=$(docker exec fasitech-api python3 -c "import os, sys; sys.path.insert(0, '/app'); from backend.config.settings import settings; print(settings.fasi_token)")
echo $FASI_TOKEN
```

### Executar Teste (gera logs detalhados)
```bash
curl -X POST http://localhost:8000/api/admin/lancamentos/matricular \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${FASI_TOKEN}" \
  -d '{
    "matricula": "202285940020",
    "polo": "OEIRAS DO PARÁ",
    "periodo": "2026.1",
    "componente": "ACC I"
  }'
```

### Ver Logs Completos
```bash
docker logs fasitech-api 2>&1 | grep "\[MATRICULAR\]"
```

## Status Atual

| Etapa | Status | URL |
|-------|--------|-----|
| Login | ✅ OK | `verTelaLogin.do` → `calendarios_graduacao_vigentes.jsf` |
| Seleção Período | ❌ FALHA | Período 2026.1 não encontrado |
| Busca Atividade | ⚠️ OK (mas errado) | Navegou para `busca_atividade.jsf` |
| Dados Registro | ❌ FALHA | Nunca chegou em `dados_registro.jsf` |

## Conclusão

O código está funcionando tecnicamente (Playwright está instalado e rodando), mas a **navegação SIGAA mudou**. O script precisa ser ajustado para:
1. Encontrar corretamente o período 2026.1
2. Navegar pelo novo fluxo do SIGAA até `dados_registro.jsf`
