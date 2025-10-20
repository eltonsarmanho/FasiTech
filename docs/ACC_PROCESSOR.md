# 🤖 ACC Processor - Processamento Inteligente de Certificados

## 📋 Visão Geral

O **AccProcessor** é um agente de IA integrado ao sistema de formulários ACC que automaticamente:

1. ✅ Extrai cargas horárias de certificados em PDF
2. ✅ Processa múltiplas páginas (certificados escaneados ou nativos)
3. ✅ Calcula o total geral de horas
4. ✅ Gera relatório detalhado em TXT
5. ✅ Envia email com análise anexada

## 🎯 Funcionalidades

### Processamento Automático

- **Conversão PDF → Imagens**: Cada página é convertida em alta resolução (300 DPI)
- **Análise com IA**: Gemini 2.5 Flash analisa cada certificado
- **Extração Inteligente**: Reconhece diferentes formatos de carga horária:
  - "40 horas"
  - "40h"
  - "Carga horária: 40h"
  - "40 (quarenta) horas"
  - "CH: 40h"
  - Carga expressa por dia (converte 8h/dia)

### Estrutura de Saída

**Arquivo TXT gerado:**
```
==================================================
ANÁLISE DE CERTIFICADOS ACC
==================================================

Aluno: Maria Santos
Matrícula: 202712345
Data da Análise: 20/10/2025 às 15:30:45

==================================================
RESULTADO DA ANÁLISE
==================================================

PÁGINA 1:
- Atividade: Curso de Python Avançado
- Carga Horária: 40 horas

PÁGINA 2:
- Atividade: Workshop de Machine Learning
- Carga Horária: 20 horas

TOTAL GERAL: 60 horas

==================================================
Documento gerado automaticamente pelo Sistema de Automação da FASI
==================================================
```

## 🔧 Configuração

### Variáveis de Ambiente Necessárias

```env
# API Key do Google Gemini
GOOGLE_API_KEY=sua_api_key_aqui

# Configurações de Email (para envio de resultados)
EMAIL_SENDER=fasicuntins@ufpa.br
EMAIL_PASSWORD=senha_app_gmail
```

### Dependências

```bash
pip install agno
pip install google-generativeai
pip install pdf2image
pip install pillow
pip install python-dotenv
```

**Nota**: No Linux, também instale o `poppler-utils`:
```bash
sudo apt-get install poppler-utils
```

## 💻 Uso

### No Formulário Web

1. Acesse o **Formulário ACC**
2. Preencha os dados do aluno
3. Faça upload do PDF com certificados
4. ✅ **Marque a opção**: "🤖 Processar certificados com IA (recomendado)"
5. Clique em **Enviar para análise**

**O que acontece:**
- PDF é salvo no Drive (estrutura: `ACC/Turma/Matrícula/arquivo.pdf`)
- Certificados são processados pela IA
- Relatório TXT é gerado
- Email é enviado com:
  - Links dos arquivos no Drive
  - Total de carga horária
  - Relatório TXT em anexo

### Via Código Python

```python
from src.services.AccProcessor import processar_certificados_acc

resultado = processar_certificados_acc(
    pdf_path="/caminho/para/certificados.pdf",
    matricula="202712345",
    nome="Maria Santos"
)

print(f"Status: {resultado['status']}")
print(f"Total de páginas: {resultado['total_paginas']}")
print(f"Carga horária: {resultado['total_geral']}")
print(f"Relatório salvo em: {resultado['txt_path']}")
```

## 📧 Email de Notificação

**Assunto:** ✅ Nova Submissão de ACC Recebida

**Corpo:**
```
Olá,

Uma nova resposta foi registrada no formulário de Atividades Curriculares Complementares (ACC).

📅 Data: 20/10/2025 às 15:30:45
🎓 Nome: Maria Santos
🔢 Matrícula: 202712345
📧 E-mail: maria@ufpa.br
📌 Turma: 2027

⏱️  TOTAL GERAL: 60 horas

📎 Anexos: 
    • certificados.pdf: https://drive.google.com/...

🔗 Você pode acessar os anexos através dos links fornecidos.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
```

**Anexo:** `ACC_202712345_20251020_153045.txt` (relatório detalhado)

## 🎯 Fluxo Completo

```
📝 Aluno submete formulário
    ↓
💾 PDF salvo no Drive (ACC/2027/202712345/)
    ↓
🤖 IA processa certificados (Gemini 2.5 Flash)
    ↓
📊 Extrai cargas horárias de cada página
    ↓
📄 Gera relatório TXT
    ↓
📧 Envia email com análise
    ↓
✅ Processo concluído
```

## ⚙️ Detalhes Técnicos

### Modelo de IA Utilizado

- **Modelo**: Google Gemini 2.5 Flash
- **Capacidade**: Multimodal (texto + imagem)
- **Resolução**: 300 DPI para melhor OCR
- **Processamento**: Paralelo de múltiplas imagens

### Armazenamento

- **Imagens temporárias**: `/tmp/acc_images/` (removidas após processamento)
- **Relatórios TXT**: `/tmp/acc_results/` (mantidos para anexo de email)
- **PDFs originais**: Google Drive (`ACC/Turma/Matrícula/`)

### Performance

- **Tempo médio**: 3-5 segundos por página
- **PDF com 10 páginas**: ~30-50 segundos
- **Limite recomendado**: 20 páginas por PDF

## 🐛 Troubleshooting

### Erro: "GOOGLE_API_KEY not set"

**Solução**: Configure a variável no `.env`:
```env
GOOGLE_API_KEY=sua_chave_aqui
```

### Erro: "pdf2image not installed"

**Solução**:
```bash
pip install pdf2image pillow
sudo apt-get install poppler-utils  # Linux
```

### Erro: "Unable to convert PDF to images"

**Solução**: Verifique se o PDF não está corrompido e se o poppler está instalado

### IA não encontra cargas horárias

**Possíveis causas:**
- Certificado em qualidade muito baixa
- Formato de carga horária não reconhecido
- PDF escaneado com resolução inferior a 150 DPI

**Solução**: Re-escanear com resolução mínima de 200 DPI

## 📚 Referências

- [Google Gemini API](https://ai.google.dev/)
- [Agno Framework](https://github.com/agno-agi/agno)
- [pdf2image](https://github.com/Belval/pdf2image)

## 🔒 Segurança

- ✅ PDFs processados localmente antes do envio ao Gemini
- ✅ Imagens temporárias removidas após processamento
- ✅ API keys armazenadas em variáveis de ambiente
- ✅ Relatórios contêm apenas informações do próprio aluno

---

**Desenvolvido pela Equipe FASI Tech** 🤖
