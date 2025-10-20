# 📚 Formulário TCC - Implementação Completa

## ✅ Status: **IMPLEMENTADO**

O FormTCC foi completamente implementado seguindo os mesmos padrões do FormACC, com integração completa ao Google Drive, Google Sheets e notificações por e-mail.

---

## 🎯 Funcionalidades Implementadas

### 1. **Interface Visual** ✅
- ✅ Design institucional com gradiente roxo (#1a0d2e → #7c3aed)
- ✅ Logo da FASI centralizada
- ✅ Sidebar completamente oculta
- ✅ Cards informativos com alertas e orientações
- ✅ Layout responsivo de 2 colunas
- ✅ Botão de submissão animado

### 2. **Campos do Formulário** ✅
- ✅ Nome Completo (obrigatório)
- ✅ E-mail (obrigatório, validação com @)
- ✅ Turma (obrigatório, 4 dígitos numéricos)
- ✅ Matrícula (obrigatório)
- ✅ Orientador(a) (obrigatório)
- ✅ Título do TCC (obrigatório)
- ✅ Componente Curricular (TCC 1 ou TCC 2, obrigatório)
- ✅ Upload múltiplo de PDFs (obrigatório)

### 3. **Validações** ✅
- ✅ Todos os campos obrigatórios verificados
- ✅ Email deve conter @
- ✅ Turma: formato numérico, 4 dígitos (ex: 2027, 2026)
- ✅ TCC 1: mínimo 2 arquivos (ANEXO I e II)
- ✅ TCC 2: mínimo 3 arquivos (Declaração + Termo + TCC)
- ✅ Apenas arquivos PDF aceitos
- ✅ Máximo 10 MB por arquivo

### 4. **Integração Google Drive** ✅
- ✅ Estrutura hierárquica: `TCC/{Componente}/{Turma}/{Matrícula}/`
- ✅ Exemplo: `TCC/TCC_2/2027/202712345/Declaracao_Autoria.pdf`
- ✅ Upload com service account
- ✅ Criação automática de pastas
- ✅ Retorna links públicos dos arquivos

### 5. **Integração Google Sheets** ✅
- ✅ Aba: "Respostas TCC"
- ✅ Colunas: Timestamp, Nome, Matrícula, Email, Turma, Componente, Orientador, Título, Arquivos, Quantidade de Anexos
- ✅ Timestamp automático
- ✅ Links clicáveis dos arquivos
- ✅ Contagem de anexos

### 6. **Notificação por E-mail** ✅
- ✅ Assunto personalizado por componente
- ✅ Emoji diferenciado: 📘 TCC 1, 📗 TCC 2
- ✅ Corpo formatado com todos os dados
- ✅ Lista numerada de arquivos com links
- ✅ Envio para múltiplos destinatários
- ✅ Configurável via `secrets.toml`

### 7. **Documentação** ✅
- ✅ Alertas visuais para orientações de TCC 2
- ✅ Links para downloads (Declaração, Termo)
- ✅ Informações sobre estrutura obrigatória do TCC
- ✅ Link para gerar Ficha Catalográfica
- ✅ Arquivo `/docs/TCC_SETUP.md` completo

### 8. **Backend Services** ✅
- ✅ `process_tcc_submission()` em `form_service.py`
- ✅ `sanitize_submission()` atualizado para TCC
- ✅ `append_rows()` com detecção automática ACC/TCC
- ✅ Tratamento de erros robusto

---

## 📁 Arquivos Criados/Modificados

### Novos Arquivos:
1. ✅ `/src/app/pages/FormTCC.py` - Interface completa do formulário
2. ✅ `/docs/TCC_SETUP.md` - Documentação de configuração
3. ✅ `/scripts/setup_tcc_sheet.py` - Script para criar aba na planilha

### Arquivos Modificados:
1. ✅ `/src/services/form_service.py` - Adicionada `process_tcc_submission()`
2. ✅ `/src/services/file_processor.py` - `sanitize_submission()` suporta campos TCC
3. ✅ `/src/services/google_sheets.py` - `append_rows()` detecta ACC vs TCC
4. ✅ `/src/app/main.py` - Card do FormTCC no portal principal

### Configuração:
- ✅ `.streamlit/secrets.toml` - Seção `[tcc]` já configurada

---

## 🚀 Como Usar

### 1. **Configurar a Planilha** (Primeira vez)

Execute o script de setup:

```bash
cd /home/eltonss/Documents/VS\ CODE/FasiTech
source venv/bin/activate
python scripts/setup_tcc_sheet.py
```

Informe o Sheet ID quando solicitado: `1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`

Isso criará a aba **"Respostas TCC"** com formatação e cabeçalhos.

### 2. **Verificar Configuração**

No arquivo `.streamlit/secrets.toml`:

```toml
[tcc]
drive_folder_id = "1lQmh3nV26OUsXhD118qts-QV0-vYieqR"
sheet_id = "1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw"
notification_recipients = ["eltonss@ufpa.br"]
```

### 3. **Iniciar a Aplicação**

```bash
cd /home/eltonss/Documents/VS\ CODE/FasiTech
source venv/bin/activate
streamlit run src/app/main.py
```

### 4. **Acessar o Formulário**

1. Na página principal, clique no card **"Formulário TCC"**
2. Preencha todos os campos obrigatórios
3. Selecione o componente (TCC 1 ou TCC 2)
4. Anexe os arquivos PDF
5. Clique em **"Enviar TCC para Análise"**

---

## 📊 Estrutura de Dados

### Google Drive:
```
TCC/
├── TCC_1/
│   ├── 2027/
│   │   └── 202712345/
│   │       ├── ANEXO_I.pdf
│   │       └── ANEXO_II.pdf
└── TCC_2/
    └── 2027/
        └── 202712345/
            ├── Declaracao_Autoria.pdf
            ├── Termo_Autorizacao.pdf
            └── TCC_Final.pdf
```

### Google Sheets (Aba "Respostas TCC"):

| Timestamp | Nome | Matrícula | Email | Turma | Componente | Orientador | Título | Arquivos | Quantidade de Anexos |
|-----------|------|-----------|-------|-------|------------|------------|--------|----------|---------------------|
| 2025-10-20 14:30:15 | Maria Silva | 202712345 | maria@ufpa.br | 2027 | TCC 2 | Prof. Dr. João | Sistema Web | link1, link2, link3 | 3 |

---

## 📧 Exemplo de E-mail

```
Assunto: ✅ Nova Submissão de TCC 2 Recebida

Olá,

Uma nova resposta foi registrada no formulário de Trabalho de Conclusão de Curso (TCC 2).

📅 Data: 20/10/2025 às 14:30:15
📗 Componente: TCC 2
🎓 Nome: Maria Silva Santos
🔢 Matrícula: 202712345
📧 E-mail: maria.santos@ufpa.br
📌 Turma: 2027
👨‍🏫 Orientador(a): Prof. Dr. João Oliveira
📄 Título: Desenvolvimento de Sistema Web para Gestão Acadêmica

📎 Anexos (3 arquivo(s)): 
    1. Declaracao_Autoria.pdf
       🔗 https://drive.google.com/file/d/xxxxx/view
    2. Termo_Autorizacao.pdf
       🔗 https://drive.google.com/file/d/yyyyy/view
    3. TCC_Final.pdf
       🔗 https://drive.google.com/file/d/zzzzz/view

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Sistema de Automação da FASI
```

---

## 🔗 Links Importantes

### Documentos para TCC 2:
- [Declaração de Autoria](https://drive.google.com/file/d/1Phh2PqZ5WDOdnTtUZIJ9M86ZtY8557nC/view?usp=sharing)
- [Termo de Autorização](https://repositorio.ufpa.br/jspui/files/TermodeAutorizacaoeDeclaracaodeAutoria.pdf)
- [Gerar Ficha Catalográfica](https://bcficat.ufpa.br/)

### Google Cloud:
- Pasta TCC Drive: `https://drive.google.com/drive/folders/1lQmh3nV26OUsXhD118qts-QV0-vYieqR`
- Planilha: `https://docs.google.com/spreadsheets/d/1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`
- Service Account: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com`

---

## 🧪 Teste Rápido

Para testar o formulário:

1. **Dados válidos TCC 1**:
   - Nome: João Silva
   - Email: joao@ufpa.br
   - Turma: 2027
   - Matrícula: 202712345
   - Orientador: Prof. Dr. Carlos Santos
   - Título: Análise de Sistemas Web
   - Componente: TCC 1
   - Anexos: 2 PDFs (ANEXO I e II)

2. **Dados válidos TCC 2**:
   - Nome: Maria Santos
   - Email: maria@ufpa.br
   - Turma: 2026
   - Matrícula: 202612345
   - Orientador: Prof. Dr. João Oliveira
   - Título: Sistema de Gestão Acadêmica
   - Componente: TCC 2
   - Anexos: 3 PDFs (Declaração, Termo, TCC)

---

## ✨ Próximos Passos (Opcional)

- [ ] Adicionar envio de confirmação para o aluno (além dos coordenadores)
- [ ] Criar dashboard de visualização das submissões
- [ ] Implementar status de avaliação (Pendente/Aprovado/Reprovado)
- [ ] Adicionar campo para nota/comentários dos avaliadores
- [ ] Gerar PDF com comprovante de submissão

---

**Implementado por**: GitHub Copilot  
**Data**: 20/10/2025  
**Status**: ✅ Completo e Funcional
