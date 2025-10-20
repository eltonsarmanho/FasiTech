# 📚 Configuração do Formulário TCC

Este documento explica como configurar e utilizar o Formulário de Submissão de TCC (Trabalho de Conclusão de Curso).

## 📋 Visão Geral

O FormTCC permite que alunos submetam seus trabalhos de conclusão de curso (TCC 1 e TCC 2) com validação automática, armazenamento no Google Drive e notificações por e-mail.

## 🏗️ Estrutura de Pastas no Google Drive

Os arquivos são organizados hierarquicamente:

```
TCC/
├── TCC_1/
│   ├── 2027/
│   │   ├── 202712345/
│   │   │   ├── ANEXO_I.pdf
│   │   │   └── ANEXO_II.pdf
│   │   └── 202712346/
│   │       ├── ANEXO_I.pdf
│   │       └── ANEXO_II.pdf
│   └── 2026/
│       └── ...
└── TCC_2/
    ├── 2027/
    │   └── 202712345/
    │       ├── Declaracao_Autoria.pdf
    │       ├── Termo_Autorizacao.pdf
    │       └── TCC_Final.pdf
    └── 2026/
        └── ...
```

**Estrutura**: `TCC/{Componente}/{Turma}/{Matrícula}/arquivos.pdf`

## 📊 Configuração do Google Sheets

### Criar Aba "Respostas TCC"

Na planilha configurada em `secrets.toml`, crie uma aba chamada **"Respostas TCC"** com os seguintes cabeçalhos:

| Timestamp | Nome | Matrícula | Email | Turma | Componente | Orientador | Título | Arquivos | Quantidade de Anexos |
|-----------|------|-----------|-------|-------|------------|------------|--------|----------|---------------------|

### Colunas:

1. **Timestamp**: Data/hora da submissão (gerado automaticamente)
2. **Nome**: Nome completo do aluno
3. **Matrícula**: Número de matrícula
4. **Email**: E-mail do aluno
5. **Turma**: Ano de ingresso (ex: 2027, 2026)
6. **Componente**: TCC 1 ou TCC 2
7. **Orientador**: Nome do professor orientador
8. **Título**: Título completo do TCC
9. **Arquivos**: Links dos arquivos no Google Drive (separados por vírgula)
10. **Quantidade de Anexos**: Número total de arquivos enviados

## ⚙️ Configuração no secrets.toml

No arquivo `.streamlit/secrets.toml`, configure:

```toml
[tcc]
drive_folder_id = "ID_DA_PASTA_TCC_NO_DRIVE"
sheet_id = "ID_DA_PLANILHA"
notification_recipients = ["coordenador@ufpa.br", "secretaria@ufpa.br"]
```

**Como obter os IDs:**

### Drive Folder ID:
1. Crie uma pasta "TCC" no Google Drive
2. Abra a pasta e copie o ID da URL:
   - URL: `https://drive.google.com/drive/folders/1lQmh3nV26OUsXhD118qts-QV0-vYieqR`
   - ID: `1lQmh3nV26OUsXhD118qts-QV0-vYieqR`
3. Compartilhe a pasta com a service account: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` (permissão de **Editor**)

### Sheet ID:
1. Abra sua planilha no Google Sheets
2. Copie o ID da URL:
   - URL: `https://docs.google.com/spreadsheets/d/1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw/edit`
   - ID: `1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`
3. Compartilhe a planilha com a service account (permissão de **Editor**)

## 📝 Campos do Formulário

### Campos Obrigatórios:

1. **Nome Completo** - Nome do aluno
2. **E-mail** - E-mail válido (deve conter @)
3. **Turma** - Ano de ingresso (4 dígitos numéricos: 2027, 2026, etc.)
4. **Matrícula** - Número de matrícula do aluno
5. **Orientador(a)** - Nome completo do professor orientador
6. **Título do TCC** - Título completo do trabalho
7. **Componente Curricular** - Selecionar "TCC 1" ou "TCC 2"
8. **Anexos** - Arquivos PDF (máximo 10 MB cada)

### Validações Específicas:

#### TCC 1:
- **Mínimo**: 2 arquivos (ANEXO I e ANEXO II das Diretrizes)
- Formatos aceitos: PDF
- Tamanho máximo: 10 MB por arquivo

#### TCC 2:
- **Mínimo**: 3 arquivos obrigatórios:
  1. **Declaração de Autoria** - [Download](https://drive.google.com/file/d/1Phh2PqZ5WDOdnTtUZIJ9M86ZtY8557nC/view?usp=sharing)
  2. **Termo de Autorização** - [Download](https://repositorio.ufpa.br/jspui/files/TermodeAutorizacaoeDeclaracaodeAutoria.pdf)
  3. **TCC Final** - Versão completa do trabalho
- Formatos aceitos: PDF
- Tamanho máximo: 10 MB por arquivo

## 📄 Estrutura Obrigatória do TCC

Independentemente do formato (memorial, artigo, relatório), o TCC deve incluir **nessa ordem**:

1. **Capa**
2. **Contracapa**
3. **Ficha Catalográfica** - Gerar em: https://bcficat.ufpa.br/
4. **Folha de Assinatura da Banca** (Obrigatório)

## 📧 Notificação por E-mail

Após a submissão bem-sucedida, os destinatários configurados recebem um e-mail com:

- Data/hora da submissão
- Dados do aluno (Nome, Matrícula, E-mail, Turma)
- Componente Curricular (TCC 1 ou TCC 2)
- Nome do Orientador
- Título do TCC
- Lista numerada de arquivos com links clicáveis do Google Drive
- Quantidade total de arquivos enviados

### Exemplo de E-mail:

```
✅ Nova Submissão de TCC 2 Recebida

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

## 🔒 Segurança e Privacidade

- Todos os dados são criptografados em trânsito (HTTPS/TLS)
- Credenciais de acesso armazenadas em base64 no `.env`
- Arquivos armazenados em pastas privadas do Google Drive
- Service account com permissões mínimas necessárias
- `.streamlit/secrets.toml` excluído do Git (via `.gitignore`)

## 🚀 Fluxo de Processamento

```
1. Aluno preenche formulário
   ↓
2. Validações no frontend (Streamlit)
   - Campos obrigatórios
   - Formato de e-mail
   - Turma numérica (4 dígitos)
   - Quantidade de arquivos (TCC 2 >= 3)
   - Tipo de arquivo (PDF)
   - Tamanho (≤ 10 MB)
   ↓
3. Processamento (form_service.py)
   - Sanitização de dados
   - Upload para Google Drive
   - Criação de estrutura hierárquica
   ↓
4. Registro no Google Sheets
   - Adiciona linha com timestamp
   - Inclui links dos arquivos
   ↓
5. Envio de e-mail
   - Notifica destinatários configurados
   - Inclui todos os dados e links
   ↓
6. Confirmação ao aluno
   - Mensagem de sucesso
   - Resumo da submissão
```

## 🛠️ Troubleshooting

### Erro: "Configurações TCC não encontradas"
**Solução**: Verifique se `.streamlit/secrets.toml` contém a seção `[tcc]` com todos os campos obrigatórios.

### Erro: "404 Not Found" ao acessar Drive
**Solução**: Compartilhe a pasta TCC com a service account `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` com permissão de **Editor**.

### Erro: "TCC 2 requer no mínimo 3 arquivos"
**Solução**: Para TCC 2, anexe os 3 arquivos obrigatórios: Declaração de Autoria, Termo de Autorização e TCC Final.

### Erro: "Turma deve ter 4 dígitos"
**Solução**: Informe o ano de ingresso com 4 dígitos (ex: 2027, 2026, 2025).

## 📞 Suporte

Para dúvidas ou problemas:
- E-mail: eltonss@ufpa.br
- Documentação: `/docs/`

---

**Última atualização**: 20/10/2025
**Versão**: 1.0.0
