# Expansão Automática de Componentes ACC e TCC

## Resumo da Feature

Quando um aluno está cadastrado como "ACC" (sem número), o sistema agora automaticamente:

- **Matricula** em ACC I, ACC II, ACC III e ACC IV (sequencialmente)
- **Consolida** em ACC I, ACC II, ACC III e ACC IV (sequencialmente com mesmo conceito)

Mesma lógica para "TCC" que expande para "TCC I" e "TCC II".

## Comportamento

### Antes (ERRO)
```
POST /api/admin/lancamentos/matricular
{
  "matricula": "201916040001",
  "componente": "ACC"  ← Erro 400: componente inválido
}
```

### Depois (SUCESSO)
```
POST /api/admin/lancamentos/matricular
{
  "matricula": "201916040001",
  "componente": "ACC"  ← Expande para ACC I, II, III, IV
}

Resposta:
{
  "message": "Matrícula de 201916040001 em ACC I, ACC II, ACC III, ACC IV ...",
  "detalhes": [...]  ← Erros individuais (se houver)
}
```

## Componentes Válidos

| Input | Expande Para | Descrição |
|-------|-------------|-----------|
| `ACC` | ACC I, ACC II, ACC III, ACC IV | Atividades Complementares (todos os 4) |
| `ACC I` | ACC I | Apenas ACC I |
| `ACC II` | ACC II | Apenas ACC II |
| `ACC III` | ACC III | Apenas ACC III |
| `ACC IV` | ACC IV | Apenas ACC IV |
| `TCC` | TCC I, TCC II | Trabalho de Conclusão (ambos) |
| `TCC I` | TCC I | Apenas TCC I |
| `TCC II` | TCC II | Apenas TCC II |

## Endpoint de Referência

```bash
GET /api/admin/lancamentos/componentes-validos

Resposta:
{
  "componentes": [
    "ACC",
    "ACC I",
    "ACC II",
    "ACC III",
    "ACC IV",
    "TCC",
    "TCC I",
    "TCC II"
  ],
  "componentes_expandidos": {
    "ACC": ["ACC I", "ACC II", "ACC III", "ACC IV"],
    "TCC": ["TCC I", "TCC II"]
  },
  "descricao": "Componentes válidos para matrícula no SIGAA...",
  "notas": [
    "ACC → matricula/consolida em ACC I, ACC II, ACC III, ACC IV",
    "TCC → matricula/consolida em TCC I, TCC II",
    "Componentes específicos (ACC I, TCC I, etc.) são processados diretamente"
  ]
}
```

## Exemplos de Uso

### 1. Matricular em ACC (todos os 4)
```bash
curl -X POST http://localhost:8000/api/admin/lancamentos/matricular \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "matricula": "201916040001",
    "polo": "CAMETÁ",
    "periodo": "2026.2",
    "componente": "ACC"
  }'
```

**Resposta esperada**:
```json
{
  "message": "Matrícula de 201916040001 em ACC I, ACC II, ACC III, ACC IV (polo: CAMETÁ | período: 2026.2) concluída com sucesso.",
  "detalhes": []
}
```

### 2. Consolidar ACC com conceito "E"
```bash
curl -X POST http://localhost:8000/api/admin/lancamentos/consolidar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "matricula": "201916040001",
    "polo": "CAMETÁ",
    "periodo": "2026.2",
    "componente": "ACC",
    "conceito": "E"
  }'
```

### 3. Matricular apenas em ACC II
```bash
curl -X POST http://localhost:8000/api/admin/lancamentos/matricular \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "matricula": "201916040001",
    "polo": "CAMETÁ",
    "periodo": "2026.2",
    "componente": "ACC II"  ← Não expande, processa direto
  }'
```

## Resultado Parcial (Sucesso com Erros)

Se alguns componentes falham, o sistema retorna **sucesso** com lista de erros:

```json
{
  "message": "Matrícula de 201916040001 em ACC I, ACC II (polo: CAMETÁ | período: 2026.2) concluída com sucesso.\n⚠️ Componentes com erro: ACC III: Timeout na navegação; ACC IV: ...",
  "detalhes": [
    "ACC III: Timeout na navegação",
    "ACC IV: ..."
  ]
}
```

**Status HTTP**: `202 Accepted` (sucesso parcial)

Se **todos** falham:

**Status HTTP**: `500 Internal Server Error` (falha total)

## Logs de Execução

Cada componente expandido gera seus próprios logs:

```
[MATRICULAR_SERVICE] Componentes a matricular: ['ACC I', 'ACC II', 'ACC III', 'ACC IV']
[MATRICULAR_SERVICE] Processando: ACC I
[MATRICULAR] [1/9] Verificando Playwright...
[MATRICULAR] [2/9] Iniciando login...
...
[MATRICULAR_SERVICE] ✓ ACC I matriculado com sucesso
[MATRICULAR_SERVICE] Processando: ACC II
...
```

## Implementação Técnica

### Arquivo: `lancamento_service.py`

```python
COMPONENTES_EXPANDIDOS = {
    "ACC": ["ACC I", "ACC II", "ACC III", "ACC IV"],
    "TCC": ["TCC I", "TCC II"],
}

def _expand_componentes(self) -> list[str]:
    if self.componente in self.COMPONENTES_EXPANDIDOS:
        return self.COMPONENTES_EXPANDIDOS[self.componente]
    return [self.componente]

async def matricular(self) -> ResultadoOperacao:
    componentes = self._expand_componentes()
    for componente_spec in componentes:
        try:
            # ... executa para cada componente
        except Exception:
            # ... registra erro mas continua
```

## Casos de Uso

### Fluxo Típico

1. **Período 2026.1 - ACC**
   ```
   Usuário clica "Matricular" com componente ACC
   → Sistema matricula ACC I, II, III, IV
   ```

2. **Período 2026.1 - ACC (Consolidação)**
   ```
   Usuário clica "Consolidar" com componente ACC, conceito E
   → Sistema consolida ACC I, II, III, IV com conceito E
   ```

3. **Período 2026.2 - ACC + TCC**
   ```
   Matricular ACC → expande e matricula 4 componentes
   Matricular TCC (com orientador) → expande e matricula 2 componentes
   ```

## Notas Importantes

- ⚠️ **Sequencial**: ACC I é processado, depois ACC II, depois ACC III, depois ACC IV
- ⚠️ **Independente**: Se ACC I falha, ACC II continua sendo tentado
- ⚠️ **Mesmo Conceito**: Todos os ACC recebem o mesmo conceito na consolidação
- ⚠️ **Orientador**: Se for TCC, orientador é usado para todos os TCCs
- ✅ **Específico**: ACC I (com número) não expande, é processado como único

## FAQ

**P: E se eu quiser matricular apenas ACC I, não todos os 4?**
A: Use `"componente": "ACC I"` no lugar de `"componente": "ACC"`

**P: Todos recebem o mesmo conceito?**
A: Sim. Se você consolida ACC com conceito "E", todos (ACC I, II, III, IV) recebem "E"

**P: E se um falhar, os outros continuam?**
A: Sim, o sistema tenta todos mesmo que alguns falhem

**P: Posso usar com TCC também?**
A: Sim! "TCC" expande para "TCC I" e "TCC II"
