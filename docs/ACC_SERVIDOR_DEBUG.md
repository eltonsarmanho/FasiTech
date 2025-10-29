# Solução para Problemas de Processamento ACC no Servidor

## Problema Identificado
O processamento de ACC funciona localmente mas falha no servidor Hostinger, provavelmente devido a dependências ausentes ou configuração incorreta.

## Diagnóstico

### 1. Execute o Script de Verificação
```bash
cd /home/ubuntu/appStreamLit
python scripts/verificar_dependencias_acc.py
```

### 2. Possíveis Causas

#### A. Dependências Ausentes
```bash
# 1. Instalar dependências Python
pip install python-dotenv pdf2image pillow agno

# 2. CRÍTICO: Instalar poppler-utils (sistema)
sudo apt-get update
sudo apt-get install -y poppler-utils

# 3. Verificar se poppler foi instalado
which pdftoppm
pdftoppm -h
```

#### B. Variáveis de Ambiente
```bash
# Verificar se GOOGLE_API_KEY está configurada
echo $GOOGLE_API_KEY

# Se não estiver, adicionar ao .env:
echo "GOOGLE_API_KEY=sua_chave_aqui" >> .env
```

#### C. Problemas de Memória
```bash
# Verificar memória disponível
free -h

# Se pouca memória, ajustar thread_count no código
# (já reduzido de 4 para 2 threads)
```

#### D. Permissões de Sistema
```bash
# Verificar permissões no diretório temporário
ls -la /tmp/
mkdir -p /tmp/acc_images
chmod 755 /tmp/acc_images
```

## Melhorias Implementadas

### 1. Logs Detalhados
- ✅ Verificação de dependências no início
- ✅ Logs de cada etapa do processamento
- ✅ Detalhes sobre arquivos e tamanhos
- ✅ Identificação específica de erros

### 2. Tratamento de Erros Robusto
- ✅ Try-catch em todas as etapas críticas
- ✅ Retorno estruturado com status de erro
- ✅ Limpeza de arquivos temporários mesmo com erro
- ✅ Logs específicos para cada tipo de falha

### 3. Otimizações para Servidor
- ✅ Redução de threads (4→2) para economia de memória
- ✅ Verificação de tamanho de arquivos
- ✅ Validação de arquivos antes do processamento

## Como Testar

### 1. Teste Local (Funcionando)
```bash
cd /home/nees/Documents/VSCodigo/FasiTech
python -c "
from src.services.acc_processor import processar_certificados_acc
resultado = processar_certificados_acc('caminho/para/teste.pdf', '123456789012', 'Teste')
print(resultado)
"
```

### 2. Teste no Servidor
```bash
cd /home/ubuntu/appStreamLit
python scripts/verificar_dependencias_acc.py
```

### 3. Teste via Interface Web
1. Acesse o formulário ACC
2. Faça upload de um PDF de teste
3. Monitore os logs do Streamlit
4. Verifique se recebe email com resultado

## Logs para Monitorar

### No Terminal do Streamlit:
```
🔍 Verificando dependências...
✓ GOOGLE_API_KEY configurada
✓ pdf2image disponível
✓ agno/Gemini disponível
📄 Convertendo PDF para imagens...
🤖 Inicializando agente de extração...
⚙️ Processando certificados com Gemini...
✅ RESULTADO DA ANÁLISE:
```

### Se Houver Erro:
```
❌ ERRO CRÍTICO no processamento ACC:
   Tipo: ImportError
   Mensagem: No module named 'pdf2image'
```

## Comandos de Emergência

### Se pdf2image não funcionar (ERRO ATUAL):
```bash
# Ubuntu/Debian (HOSTINGER)
sudo apt-get update
sudo apt-get install -y poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils

# Verificar se poppler está no PATH
which pdftoppm
which pdfinfo
echo $PATH

# Testar instalação
python -c "from pdf2image import convert_from_path; print('PDF2Image OK')"

# Se ainda der erro, verificar log completo
python -c "
import pdf2image
import shutil
print('pdftoppm path:', shutil.which('pdftoppm'))
print('pdfinfo path:', shutil.which('pdfinfo'))
"
```

### Se agno não funcionar:
```bash
pip install --upgrade agno
pip install google-generativeai
```

### Se faltar memória:
```bash
# Verificar uso de memória
top
htop

# Reiniciar aplicação se necessário
pkill -f streamlit
```

## Contato para Suporte
- Execute o script de verificação primeiro
- Copie os logs completos do erro
- Inclua saída do comando `pip list | grep -E "pdf2image|agno|pillow"`

---
*Documento atualizado em: Outubro 2025*