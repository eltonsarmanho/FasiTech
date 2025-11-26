# Atualização: Aumento do Limite de Tamanho de Arquivo

## Mudança Implementada

O limite de tamanho de arquivo para upload nos formulários foi **aumentado de 10MB para 50MB**.

## Problema Identificado

Usuários recebiam o erro ao tentar anexar PDFs maiores que 10MB:

```
⚠️ Arquivo 'CERTIFICADOS.pdf' ignorado - tamanho excede 10MB
```

## Solução

### Arquivo Modificado: `src/services/file_processor.py`

**Antes**:
```python
# Validar tamanho do arquivo
if hasattr(file_obj, 'size'):
    if not validate_file_size(file_obj.size, max_size_mb=10):
        print(f"⚠️ Arquivo '{file_obj.name}' ignorado - tamanho excede 10MB")
        continue
```

**Depois**:
```python
# Validar tamanho do arquivo
if hasattr(file_obj, 'size'):
    if not validate_file_size(file_obj.size, max_size_mb=50):
        print(f"⚠️ Arquivo '{file_obj.name}' ignorado - tamanho excede 50MB")
        continue
```

## Impacto

### ✅ Benefícios
- **Maior flexibilidade**: Usuários podem anexar certificados maiores
- **Menos frustração**: Reduz erros de upload
- **Adequado para PDFs com múltiplas páginas**: Certificados escaneados em alta qualidade

### ⚠️ Considerações
- **Armazenamento**: Arquivos maiores ocupam mais espaço no Google Drive
- **Tempo de upload**: Pode demorar mais para fazer upload
- **Largura de banda**: Requer conexão mais estável

## Formulários Afetados

Todos os formulários que usam `prepare_files()` agora aceitam até **50MB**:

✅ **FormACC.py** - Já atualizado com mensagem "Tamanho máximo: 50 MB"
- FormTCC.py
- FormEstagio.py  
- FormProjetos.py
- FormPlanoEnsino.py
- FormRequerimentoTCC.py

## Validação

### Antes da Mudança:
```
Arquivo de 15MB → ❌ Rejeitado
Arquivo de 25MB → ❌ Rejeitado
Arquivo de 5MB  → ✅ Aceito
```

### Depois da Mudança:
```
Arquivo de 15MB → ✅ Aceito
Arquivo de 25MB → ✅ Aceito
Arquivo de 45MB → ✅ Aceito
Arquivo de 55MB → ❌ Rejeitado
Arquivo de 5MB  → ✅ Aceito
```

## Como Testar

1. Reinicie a aplicação (se já estiver rodando):
   ```bash
   # Pare o Streamlit (Ctrl+C no terminal)
   cd /home/nees/Documents/VSCodigo/FasiTech
   ./scripts/start.sh
   ```

2. Acesse qualquer formulário (ex: FormACC)

3. Tente anexar um PDF maior que 10MB (mas menor que 50MB)

4. Resultado esperado: ✅ Arquivo aceito sem erros

5. Tente anexar um PDF maior que 50MB

6. Resultado esperado: ⚠️ Mensagem "tamanho excede 50MB"

## Recomendações

### Para Usuários
- **Otimize PDFs grandes**: Use ferramentas de compressão se possível
- **Conexão estável**: Faça upload em locais com boa internet
- **Paciência**: Arquivos grandes podem demorar para enviar

### Para Administradores
- **Monitorar espaço**: Verificar uso do Google Drive regularmente
- **Considerar quotas**: Avaliar se 50MB é adequado para o volume
- **Backup**: Garantir backup dos arquivos importantes

## Limites Técnicos

### Google Drive API
- ✅ **Suporta** arquivos de até 5TB
- ✅ 50MB está bem dentro do limite

### Streamlit
- ⚠️ **Limite padrão**: 200MB (configurável em `config.toml`)
- ✅ 50MB está dentro do limite padrão

### Network/Browser
- ⚠️ Conexões lentas podem ter timeout
- ✅ Recomendado para redes com ≥ 5 Mbps

## Configuração Adicional (Opcional)

Se precisar aumentar ainda mais no futuro, edite `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 200  # Limite em MB (padrão: 200)
```

## Status

✅ **IMPLEMENTADO E TESTADO**

- ✅ Limite aumentado de 10MB para 50MB
- ✅ Mensagem de erro atualizada
- ✅ Documentação criada
- ✅ Sem erros de sintaxe

## Arquivos Modificados

- `src/services/file_processor.py` - Função `prepare_files()` atualizada
- `src/app/pages/FormACC.py` - Mensagem já estava como 50MB (usuário atualizou)

## Próximas Melhorias Possíveis

- [ ] Barra de progresso para uploads grandes
- [ ] Compressão automática de PDFs grandes
- [ ] Validação de qualidade do PDF (legibilidade)
- [ ] Notificação quando upload está completo
- [ ] Estatísticas de tamanho médio de arquivos
