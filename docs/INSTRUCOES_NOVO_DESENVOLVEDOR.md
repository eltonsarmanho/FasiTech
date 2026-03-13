# 📋 Instruções para Novo Desenvolvedor - FasiTech

Bem-vindo ao projeto FasiTech! Este documento contém tudo que você precisa saber para começar a contribuir.

---

## 🚀 Primeiros Passos

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd FasiTech
```

### 2. Acesse a branch de trabalho
A branch `master` está protegida. Você deve trabalhar exclusivamente na branch `feature/novo-desenvolvedor`:

```bash
git checkout feature/novo-desenvolvedor
```
### 3. Configure o ambiente local
```bash
# Ative o virtual environment
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 4. Teste a configuração
```bash
# Verifique a branch atual
git branch

# Verifique se está na branch correta
# Você deve ver: * feature/novo-desenvolvedor
```

---

## 💻 Workflow de Desenvolvimento

### Antes de começar
1. ✅ Certifique-se de estar na branch correta: `feature/novo-desenvolvedor`
2. ✅ Atualize a branch com as últimas mudanças:
```bash
git pull origin feature/novo-desenvolvedor
```

### Durante o desenvolvimento
```bash
# Faça suas alterações nos arquivos
# ...

# Verifique o status
git status

# Adicione os arquivos modificados
git add .

# Faça commit com mensagem descritiva
git commit -m "Descrição clara do que foi feito"

# Envie para o repositório remoto
git push origin feature/novo-desenvolvedor
```

### Quando terminar uma tarefa
1. Verifique se todos os testes passam
2. Revise suas mudanças
3. Abra um **Pull Request (PR)** via GitHub/GitLab web
4. Aguarde a revisão do líder do projeto

---

## ⚠️ Regras Importantes

- ❌ **NUNCA** faça commit direto na branch `master` - a proteção vai bloquear
- ❌ **NUNCA** force push (`git push -f`) - pode perder histórico
- ✅ **SEMPRE** trabalhe na branch `feature/novo-desenvolvedor`
- ✅ **SEMPRE** faça commits com mensagens claras
- ✅ **SEMPRE** crie um PR para mudanças serem revisadas

---

## 📝 Boas Práticas de Commits

### Formato de mensagem
```
Tipo: Descrição breve em português

Descrição mais detalhada se necessário (opcional)
```

### Exemplos de tipos
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `refactor:` - Refatoração de código
- `docs:` - Alterações em documentação
- `test:` - Testes adicionados ou modificados

### Exemplos bons
```bash
git commit -m "feat: Adicionar autenticação com Google"
git commit -m "fix: Corrigir erro na validação de email"
git commit -m "refactor: Melhorar estrutura de pastas"
```

---

## 🔄 Fluxo Completo de uma Tarefa

```bash
# 1. Atualizar branch local
git checkout feature/novo-desenvolvedor
git pull origin feature/novo-desenvolvedor

# 2. Fazer alterações
# ... editar arquivos ...

# 3. Testar localmente
pytest  # Se houver testes

# 4. Adicionar e commitar
git add .
git commit -m "feat: Descrição da mudança"

# 5. Enviar para remoto
git push origin feature/novo-desenvolvedor

# 6. Criar PR no GitHub/GitLab
# - Acesse o repositório online
# - Clique em "New Pull Request"
# - Selecione feature/novo-desenvolvedor → master
# - Adicione título e descrição
# - Aguarde revisão
```

---

## 🆘 Comandos Úteis

### Ver histórico de commits
```bash
git log --oneline
```

### Ver diferenças das mudanças
```bash
git diff
```

### Desfazer últimas mudanças (antes de push)
```bash
git reset --soft HEAD~1
```

### Atualizar com mudanças da master
```bash
git fetch origin
git rebase origin/master
git push origin feature/novo-desenvolvedor --force-with-lease
```

---

## 📞 Contato e Dúvidas

Se tiver dúvidas:
1. Consulte a documentação do projeto em `/docs`
2. Verifique o `README.md` para mais detalhes
3. Entre em contato com o líder do projeto

---

## 🎯 Checklist Antes de Fazer Push

- [ ] Eu estou na branch `feature/novo-desenvolvedor`?
- [ ] Minhas mudanças funcionam localmente?
- [ ] Escrevi testes (se aplicável)?
- [ ] Mensagem de commit é clara?
- [ ] Não adicionei arquivos confidenciais (senhas, tokens)?
- [ ] Revisei minhas mudanças antes de push?

---

**Última atualização:** 13 de Março de 2026
