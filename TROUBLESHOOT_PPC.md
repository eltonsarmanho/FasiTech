# Solução: PPC.pdf não está sendo carregado

## Problema
O RAG está retornando "Não encontrei informações sobre..." porque:
1. O arquivo `PPC.pdf` não foi sincronizado corretamente para a VM, OU
2. A base de dados vetorial (LanceDB) foi criada vazia

## Solução

### 1. Verificar se PPC.pdf está na VM

```bash
# SSH na VM
ssh root@72.60.6.113

# Verificar arquivo
ls -lh /home/ubuntu/appStreamLit/src/resources/PPC.pdf

# Se não existir, fazer sync novamente
# (Do seu computador local)
rsync -avz --progress src/resources/PPC.pdf root@72.60.6.113:/home/ubuntu/appStreamLit/src/resources/
```

### 2. Limpar base de dados antiga e recarregar

```bash
# Na VM, remover cache antigo
rm -rf ~/.cache/fasitech/

# Executar script de verificação
cd /home/ubuntu/appStreamLit
python verify_ppc_setup.py
```

### 3. Se ainda assim não funcionar

O script agora:
- ✅ Procura PPC.pdf em múltiplos caminhos
- ✅ Mostra erro claro se arquivo não encontrado
- ✅ Loga cwd (current working directory) para debug
- ✅ Cria cache em `~/.cache/fasitech/rag/` (com permissões corretas)

## Debug

Execute o script de verificação que foi criado:

```bash
python /home/ubuntu/appStreamLit/verify_ppc_setup.py
```

Ele vai mostrar:
1. Se PPC.pdf foi encontrado
2. Localização exata do arquivo
3. Status da inicialização do serviço
4. Erros específicos (se houver)

## Arquivos Modificados

- `src/services/rag_ppc.py`: Melhorado tratamento de caminhos e logging
- `verify_ppc_setup.py`: Script novo para debug e verificação

## Próximos Passos

1. Execute o script de verificação
2. Compartilhe a saída
3. Se necessário, faça sync novamente do arquivo PPC.pdf
