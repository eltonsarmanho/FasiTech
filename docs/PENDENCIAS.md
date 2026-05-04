# 📋 Pendências do Sistema FasiTech

## 🔴 Pendências Críticas

### 1. Máscaras de Validação em Formulários

#### 📧 Campo de Email
**Status:** ✅ **CONCLUÍDO**  
**Prioridade:** Alta  
**Descrição:** Adicionar máscara de validação visual para campos de email em todos os formulários.

**Formulários afetados:**
- [x] FormACC.py ✅ **Corrigido** - Regex implementado
- [x] FormTCC.py ✅ **Corrigido** - Regex implementado
- [x] FormRequerimentoTCC.py ✅ **Corrigido** - Regex implementado
- [x] FormEstagio.py ✅ **Já estava correto** - Regex já implementado
- [ ] FormPlanoEnsino.py - N/A (usa radio button)
- [ ] FormProjetos.py - N/A (usa radio button)

**Implementação sugerida:**
```python
import re

def validate_email_input(email: str) -> bool:
    """Valida formato de email em tempo real."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Adicionar no campo:
email = st.text_input(
    "Email *",
    placeholder="exemplo@ufpa.br",
    help="Digite um email válido"
)

if email and not validate_email_input(email):
    st.error("⚠️ Formato de email inválido")
```

---

#### 🎓 Campo Turma
**Status:** ✅ **CONCLUÍDO**  
**Prioridade:** Alta  
**Descrição:** Adicionar máscara de validação para campo Turma (4 dígitos numéricos).

**Formulários afetados:**
- [x] FormACC.py ✅ **Já estava correto** - Validação 4 dígitos OK
- [x] FormTCC.py ✅ **Já estava correto** - Validação 4 dígitos OK
- [x] FormEstagio.py ✅ **Já estava correto** - Regex implementado
- [ ] FormRequerimentoTCC.py - N/A (não possui campo turma)
- [ ] FormPlanoEnsino.py - N/A (não possui campo turma)
- [ ] FormProjetos.py - N/A (não possui campo turma)

**Implementação sugerida:**
```python
# Usar st.text_input com max_chars e validação
turma = st.text_input(
    "Turma *",
    placeholder="2027",
    max_chars=4,
    help="Digite o ano de ingresso (4 dígitos)"
)

if turma and not turma.isdigit():
    st.error("⚠️ Turma deve conter apenas números")
elif turma and len(turma) != 4:
    st.error("⚠️ Turma deve ter exatamente 4 dígitos")
```

---

## 🧪 Testes e Validação Visual

### 2. Revisão Visual de Formulários

#### ✅ FormACC.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo
- [ ] Campos obrigatórios com `*`
- [ ] Validação de email
- [ ] Validação de turma (4 dígitos)
- [ ] Upload de arquivo (PDF)
- [ ] Mensagens de erro claras
- [ ] Processamento com IA funcional
- [ ] Redirecionamento após sucesso
- [ ] Email de notificação

---

#### ✅ FormTCC.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo
- [ ] Radio buttons TCC 1/TCC 2
- [ ] Campos obrigatórios com `*`
- [ ] Validação de email
- [ ] Validação de turma (4 dígitos)
- [ ] Upload múltiplo (mínimo 3 arquivos para TCC 2)
- [ ] Estrutura Drive: TCC 1 ou 2 / Turma / Nome
- [ ] Registro no Google Sheets
- [ ] Email de notificação
- [ ] Redirecionamento após sucesso

---

#### ✅ FormRequerimentoTCC.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo
- [ ] Banca Examinadora FORA do form
- [ ] Orientador SEM opção "Outro:"
- [ ] Membros COM opção "Outro:" + text_input condicional
- [ ] Campos obrigatórios com `*`
- [ ] Validação de email
- [ ] Upload de arquivo (PDF)
- [ ] Registro em aba por ano (2025, 2026, etc.)
- [ ] Email para: aluno + orientador + notification_recipients
- [ ] Redirecionamento após sucesso

---

#### ✅ FormEstagio.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo
- [ ] Radio Plano/Relatório SEM opção vazia
- [ ] Campos obrigatórios com `*`
- [ ] Validação de email (regex)
- [ ] Validação de turma (4 dígitos regex)
- [ ] Upload múltiplo (PDF/DOC/DOCX)
- [ ] Estrutura Drive: Componente / Turma / Arquivos
- [ ] Registro no Google Sheets (9 colunas)
- [ ] Email para: aluno + notification_recipients
- [ ] Redirecionamento após sucesso

---

#### ✅ FormPlanoEnsino.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo
- [ ] Docente FORA do form com "Outro:" condicional
- [ ] Semestre dropdown (2025.4 - 2026.4)
- [ ] Info box amarelo com instruções
- [ ] Upload múltiplo (PDF/DOC/DOCX)
- [ ] Estrutura Drive: Semestre / Arquivos
- [ ] Registro no Google Sheets (4 colunas)
- [ ] Email para: notification_recipients (sem aluno)
- [ ] Redirecionamento após sucesso

---

#### ✅ FormProjetos.py
**Status:** ⏳ A testar  
**Itens de verificação:**
- [ ] Layout responsivo e compacto
- [ ] Solicitação FORA do form (info boxes dinâmicos)
- [ ] Docente, Pareceristas FORA do form
- [ ] Edital com "Outro:" condicional FORA do form
- [ ] Campos Informações do Projeto FORA do form
- [ ] Apenas Anexos e Botão DENTRO do form
- [ ] Espaçamento vertical otimizado
- [ ] Validação: pareceristas diferentes
- [ ] Upload múltiplo (PDF/DOC/DOCX, até 10)
- [ ] **Geração automática de PDFs** (Parecer + Declaração)
- [ ] Estrutura Drive: Edital / Ano / Docente / Solicitação
- [ ] Registro no Google Sheets (11 colunas)
- [ ] Email para: notification_recipients + docente + parecerista1 + parecerista2
- [ ] PDFs anexados ao email
- [ ] Redirecionamento após sucesso

---

## 📊 Integração e Backend

### 3. Google Sheets - Detecção de Formato

**Status:** ✅ Implementado  
**Prioridade de detecção:**
1. "Título do trabalho" → Requerimento TCC (13 colunas)
2. "Nome do Parecerista 1" → Projetos (11 colunas)
3. "Nome do Docente Responsável" → Plano (4 colunas)
4. "Orientador ou Supervisor" → Estágio (9 colunas)
5. "Componente" → TCC (9 colunas)
6. Default → ACC (6-7 colunas)

**Ação:** Testar cada formulário e verificar se os dados são salvos nas colunas corretas.

---

### 4. Google Drive - Estrutura de Pastas

**Status:** ✅ Implementado  

**Estruturas por formulário:**
- **ACC:** `Pasta Raiz / Arquivos`
- **TCC:** `TCC 1 ou TCC 2 / Turma / Nome do Aluno / Arquivos`
- **Requerimento TCC:** `Pasta Raiz / Arquivos` (sem subpastas)
- **Estágio:** `Componente Curricular / Turma / Arquivos`
- **Plano:** `Semestre / Arquivos`
- **Projetos:** `Edital / Ano do Edital / Nome do Docente / Solicitação / Arquivos`

**Ação:** Testar upload em cada formulário e verificar hierarquia de pastas.

---

## 🐛 Bugs Conhecidos

### 5. Possíveis Problemas

**Status:** ⚠️ Monitorar

- [ ] **BytesIO para PDFs gerados** - Verificar se upload funciona corretamente em Projetos
- [ ] **Validação de campos** - Testar todos os cenários de erro
- [ ] **Email duplicado** - Verificar se proteção contra duplicatas funciona
- [ ] **Caracteres especiais** - Testar nomes com acentos/símbolos
- [ ] **Tamanho de arquivos** - Validar limite de 10MB por arquivo
- [ ] **Conexão Google APIs** - Testar timeout e retry

---

## 📝 Melhorias Futuras

### 6. Features Opcionais

**Prioridade:** Baixa

- [ ] Dashboard de estatísticas
- [ ] Histórico de submissões por usuário
- [ ] Notificações in-app
- [ ] Export de relatórios
- [ ] Integração com SIGAA
- [ ] Assinatura digital nos PDFs
- [ ] Versionamento de documentos
- [ ] Sistema de aprovação workflow

---

## 🚀 Deploy e Infraestrutura

### 7. Preparação para Produção

**Status:** ⏳ Pendente

- [ ] **Dockerfile corrigido** ✅ (requirements.txt path)
- [ ] **Rsync para VM** ✅ (comando corrigido)
- [ ] Testar build no ambiente de produção
- [ ] Configurar variáveis de ambiente
- [ ] Backup automático do Sheets
- [ ] Monitoramento de erros (Sentry?)
- [ ] Logs estruturados
- [ ] SSL/HTTPS configurado
- [ ] Rate limiting para APIs

---

## 📅 Cronograma Sugerido

### Sprint 1 - Validações ✅ **CONCLUÍDA**

- [x] Implementar máscara de email em todos os forms ✅
- [x] Implementar máscara de turma (4 dígitos) ✅
- [x] Validação visual em tempo real ✅
- [x] Remover checkbox de IA do FormACC ✅
- [x] Processamento IA sempre ativo (background) ✅
- [x] Redirecionamento automático após 4 segundos ✅
- [x] Email resiliente (envia mesmo se IA falhar) ✅

### Sprint 2 - Testes (3 dias)
- [ ] Testar FormACC end-to-end
- [ ] Testar FormTCC end-to-end
- [ ] Testar FormRequerimentoTCC end-to-end
- [ ] Testar FormEstagio end-to-end
- [ ] Testar FormPlanoEnsino end-to-end
- [ ] Testar FormProjetos end-to-end

### Sprint 3 - Deploy (1 dia)
- [ ] Build Docker na VM
- [ ] Deploy com rsync
- [ ] Testes em produção
- [ ] Documentação final

---

## 👥 Responsáveis

- **Desenvolvimento:** Equipe de Desenvolvimento
- **Testes:** QA / Usuários piloto
- **Deploy:** DevOps / Infraestrutura
- **Validação:** Coordenação FASI

---

## 📞 Contato

**Dúvidas ou problemas:** eltonss@ufpa.br

---

**Última atualização:** 22/10/2025  
**Versão do documento:** 1.0
