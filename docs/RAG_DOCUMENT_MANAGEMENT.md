# 📚 Guia de Gerenciamento de Documentos RAG

Este guia explica como adicionar, remover e gerenciar documentos no banco vetorial do RAG do FasiTech.

## 🔧 Como Adicionar Novos Documentos

### Método 1: Usando o Script Automático (Recomendado)

```bash
# 1. Listar documentos atuais
python scripts/add_documents_to_rag.py --list

# 2. Adicionar novo documento
python scripts/add_documents_to_rag.py --add caminho/para/documento.pdf

# 3. Limpar cache para reprocessar
python scripts/add_documents_to_rag.py --clear

# 4. Reiniciar containers (se em produção)
ssh root@72.60.6.113 "cd /home/ubuntu/appStreamLit && sudo docker compose -f docker-compose.production.yml restart streamlit"
```

### Método 2: Manual

```bash
# 1. Copiar PDF para src/resources/
cp meu_documento.pdf src/resources/

# 2. Limpar cache vetorial
rm -rf ~/.cache/fasitech/rag/

# 3. Próxima inicialização do RAG irá reprocessar todos os documentos
```

## 📁 Estrutura de Arquivos

```
src/resources/
├── PPC.pdf                    # Documento principal (atual)
├── manual_usuario.pdf         # Exemplo de novo documento
├── regimento_interno.pdf      # Exemplo de novo documento  
└── politicas_academicas.pdf   # Exemplo de novo documento
```

## 🔄 Como o Sistema Funciona

### Detecção Automática
O RAG agora procura **todos os arquivos PDF** em `src/resources/` automaticamente:

```python
# O sistema busca em:
src/resources/*.pdf              # Todos os PDFs
```

### Processamento
1. **Primeira execução**: Todos os PDFs são indexados (pode demorar)
2. **Cache**: Banco vetorial é salvo em `~/.cache/fasitech/rag/`
3. **Execuções seguintes**: Usa cache existente (rápido)
4. **Novos documentos**: Requer limpeza do cache

### Banco Vetorial
- **Local**: `~/.cache/fasitech/rag/lancedb/`
- **Embeddings**: Ollama (nomic-embed-text) 768 dimensões
- **Busca**: Semântica por similaridade
- **LLM**: Gemini para gerar respostas contextuais

## 🧹 Gerenciamento de Cache

### Quando Limpar o Cache
- ✅ Adicionou novos documentos
- ✅ Modificou documentos existentes  
- ✅ Removeu documentos
- ✅ Mudou configurações do embedder
- ✅ Sistema retornando respostas desatualizadas

### Como Limpar
```bash
# Opção 1: Script automático
python scripts/add_documents_to_rag.py --clear

# Opção 2: Manual
rm -rf ~/.cache/fasitech/rag/

# Opção 3: No servidor
sshpass -p "xxx" ssh root@72.60.6.113 "sudo docker compose -f /home/ubuntu/appStreamLit/docker-compose.production.yml exec streamlit rm -rf /home/appuser/.cache/fasitech/rag/"
```

## 📊 Tipos de Documentos Suportados

### Formatos
- ✅ **PDF**: Formato principal (recomendado)
- ❌ **Word**: Não suportado diretamente
- ❌ **TXT**: Não suportado diretamente  
- ❌ **HTML**: Não suportado diretamente

### Conversão para PDF
```bash
# Word para PDF (usando LibreOffice)
libreoffice --headless --convert-to pdf documento.docx --outdir src/resources/

# Texto para PDF (usando pandoc)
pandoc documento.txt -o src/resources/documento.pdf
```

## 🔍 Verificação de Funcionamento

### Teste Rápido
```bash
# No servidor de produção
ssh root@72.60.6.113 "cd /home/ubuntu/appStreamLit && sudo docker compose -f docker-compose.production.yml exec -T streamlit python3 -c \"
import sys; sys.path.insert(0, '/app')
from src.services.rag_ppc import PPCChatbotService
service = PPCChatbotService()
status = service.get_status()
print(f'Documentos: {status.get(\\\"document_files\\\")}')
print(f'Knowledge loaded: {status.get(\\\"knowledge_loaded\\\")}')
\""
```

### Teste Completo
```python
# Testar pergunta específica do novo documento
response = service.ask_question("Qual informação está no [nome do novo documento]?")
print(response.get('answer'))
```

## 🚨 Troubleshooting

### Problema: "Documento não aparece nas respostas"
**Solução**:
1. Verificar se PDF está em `src/resources/`
2. Limpar cache: `--clear`
3. Reiniciar RAG
4. Aguardar reprocessamento (pode demorar)

### Problema: "Erro de permissão no cache"
**Solução**:
```bash
# Corrigir permissões
sudo chown -R $USER:$USER ~/.cache/fasitech/
chmod -R 755 ~/.cache/fasitech/
```

### Problema: "RAG muito lento após novos documentos"
**Causa**: Muitos documentos ou documentos muito grandes  
**Solução**:
1. Otimizar PDFs (remover imagens desnecessárias)
2. Dividir documentos grandes em seções
3. Considerar usar apenas documentos essenciais

## 📈 Monitoramento

### Logs do RAG
```bash
# Ver logs detalhados
sudo docker compose -f docker-compose.production.yml logs streamlit | grep rag_ppc
```

### Métricas
- **Número de documentos**: Status do serviço
- **Tempo de resposta**: Latência das consultas  
- **Qualidade**: Análise de keywords nas respostas

## 🎯 Boas Práticas

### Nomenclatura de Arquivos
```bash
# ✅ Bom
PPC_Sistemas_Informacao_2024.pdf
Manual_Usuario_Sistema_v2.pdf  
Regimento_Interno_Atualizado.pdf

# ❌ Evitar
documento (1).pdf
file.pdf
temp_doc_final_v3_FINAL.pdf
```

### Organização
- Manter poucos documentos essenciais
- Atualizar regularmente
- Remover documentos obsoletos
- Testar após mudanças

### Performance
- PDFs otimizados (< 10MB cada)
- Máximo 10-15 documentos
- Limpar cache regularmente
- Monitorar tempo de resposta

---

## 📞 Suporte

Em caso de dúvidas:
1. Verificar logs: `docker compose logs streamlit`
2. Testar script: `python scripts/add_documents_to_rag.py --list`
3. Limpar e reprocessar: `--clear`
4. Reiniciar containers se necessário