# Configuração do Google Drive e Sheets para ACC

## ⚠️ IMPORTANTE: Compartilhamento com Conta de Serviço

**O erro mais comum é esquecer de compartilhar os recursos com a conta de serviço!**

Conta de serviço do projeto:
```
contaufpafasi@servicoweb-453121.iam.gserviceaccount.com
```

---

## 1️⃣ Configuração da Pasta no Google Drive

### Passos para Compartilhar a Pasta

A pasta do Google Drive (ID: `17GiNzOq0yWsvDNKlIx5672ya_qviGOto`) **DEVE** estar compartilhada com a conta de serviço:

1. **Acesse diretamente a pasta**: 
   - URL: `https://drive.google.com/drive/folders/17GiNzOq0yWsvDNKlIx5672ya_qviGOto`
   - Ou navegue até a pasta no Google Drive

2. **Compartilhe a pasta**:
   - Clique com botão direito na pasta > **Compartilhar**
   - Ou clique no ícone de pessoa com "+" no canto superior direito

3. **Adicione a conta de serviço**:
   - Cole o e-mail: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com`
   - Pressione Enter

4. **Defina a permissão**:
   - Selecione **Editor** (não "Visualizador"!)
   - Isso permite que o sistema salve arquivos na pasta

5. **Finalize sem notificar**:
   - ⚠️ **DESMARQUE** a opção "Notificar pessoas"
   - Clique em **Compartilhar** ou **Concluído**

### Verificando o Compartilhamento

Para confirmar que está correto:
- Abra a pasta no Drive
- Clique no ícone de pessoa (compartilhamento)
- Você deve ver: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` com permissão "Editor"

---

## 2️⃣ Configuração da Planilha Google Sheets

### Estrutura da Planilha

A planilha do Google Sheets deve ter a seguinte estrutura na primeira aba (Sheet1):

| Coluna A | Coluna B | Coluna C | Coluna D | Coluna E | Coluna F |
|----------|----------|----------|----------|----------|----------|
| **Timestamp** | **Nome** | **Matrícula** | **Email** | **Turma** | **Arquivos** |
| 2025-01-20 10:30:00 | João Silva | 202312345 | joao@email.com | ADS 4º | file-id-123 |

### Passos para Configuração

#### 1. Acessar a Planilha

- Acesse diretamente: `https://docs.google.com/spreadsheets/d/1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`
- Ou acesse [Google Sheets](https://sheets.google.com) e localize a planilha

#### 2. Adicionar Cabeçalhos

Na primeira linha (linha 1), adicione os seguintes cabeçalhos:

```
A1: Timestamp
B1: Nome
C1: Matrícula
D1: Email
E1: Turma
F1: Arquivos
```

#### 3. Compartilhar com a Conta de Serviço

**OBRIGATÓRIO** para que o sistema possa escrever dados:

1. Clique em **Compartilhar** (botão verde no canto superior direito)

2. Adicione o e-mail da conta de serviço:
   ```
   contaufpafasi@servicoweb-453121.iam.gserviceaccount.com
   ```

3. Defina a permissão como **Editor** (não "Visualizador"!)

4. **DESMARQUE** a opção "Notificar pessoas"

5. Clique em **Compartilhar** ou **Concluído**

#### 4. Verificar a Primeira Aba

- Certifique-se de que a primeira aba se chama `Sheet1`
- Se tiver outro nome, renomeie-a para `Sheet1`
- Ou atualize o código em `google_sheets.py` para usar o nome correto

### Verificando o Compartilhamento

Para confirmar:
- Abra a planilha
- Clique em **Compartilhar**
- Você deve ver: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` com permissão "Editor"

---

## 3️⃣ Testando a Integração

Após compartilhar **TANTO a pasta quanto a planilha**, teste:

1. **Execute a aplicação**:
   ```bash
   streamlit run src/app/main.py
   ```

2. **Acesse o Formulário ACC**

3. **Preencha e envie um teste**

4. **Verifique os resultados**:
   - ✅ Arquivo PDF apareceu na pasta do Drive
   - ✅ Registro foi adicionado à planilha
   - ✅ E-mail de notificação foi recebido

---

## 🔧 Troubleshooting

### ❌ Erro: "File not found: 17GiNzOq..."

**Causa**: A pasta não está compartilhada com a conta de serviço

**Solução**:
1. Acesse: `https://drive.google.com/drive/folders/17GiNzOq0yWsvDNKlIx5672ya_qviGOto`
2. Compartilhe com: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com`
3. Permissão: **Editor**

### ❌ Erro: "Permission denied" ou "Spreadsheet not found"

**Causa**: A planilha não está compartilhada com a conta de serviço

**Solução**:
1. Abra: `https://docs.google.com/spreadsheets/d/1QtSUY5oyYdaVDBPnRuFOxJQDuL8Y73B-pt_e24Y0yGw`
2. Clique em **Compartilhar**
3. Adicione: `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com`
4. Permissão: **Editor**

### ❌ Dados não aparecem na planilha

**Possíveis causas**:
- Nome da aba não é `Sheet1` → Renomeie para `Sheet1`
- Cabeçalhos não estão na linha 1 → Adicione os cabeçalhos
- Confira os logs no terminal para mensagens de erro específicas

### ❌ E-mails não estão sendo enviados

**Verificar**:
- Confirme que o `EMAIL_PASSWORD` no `.env` é uma senha de aplicativo (não a senha da conta)
- Teste o login manualmente em `smtp.gmail.com`

---

## 📋 Checklist Final

Antes de usar o sistema em produção, confirme:

- [ ] Pasta do Drive compartilhada com `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` (Editor)
- [ ] Planilha compartilhada com `contaufpafasi@servicoweb-453121.iam.gserviceaccount.com` (Editor)
- [ ] Primeira aba da planilha se chama `Sheet1`
- [ ] Cabeçalhos estão na linha 1 da planilha
- [ ] `.env` tem `GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64` configurado
- [ ] `.env` tem `EMAIL_SENDER` e `EMAIL_PASSWORD` configurados
- [ ] `.streamlit/secrets.toml` tem os IDs corretos
- [ ] Teste realizado com sucesso (arquivo + planilha + e-mail)

---

## 🔐 Segurança

**Nunca compartilhe**:
- O arquivo `.env` (contém credenciais)
- O conteúdo de `GOOGLE_CLOUD_CREDENTIALS_FASI_BASE64`
- A senha de aplicativo do e-mail

**Git**:
- `.env` e `.streamlit/secrets.toml` estão no `.gitignore`
- Não faça commit de credenciais no repositório
