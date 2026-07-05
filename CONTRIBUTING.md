# 🤝 Guia de Contribuição — FasiTech

Obrigado por considerar contribuir ao FasiTech! Este documento descreve como colaborar mantendo conformidade com nossa licença e práticas acadêmicas responsáveis.

---

## ⚖️ Conformidade com Licença

**ANTES DE CONTRIBUIR**, você **DEVE** ler e aceitar a [Licença de Uso Restrito com Proteção Acadêmica](./LICENSE.md).

Ao enviar uma pull request, você confirma que:

✅ O código é sua criação original ou devidamente atribuído  
✅ Você não está incluindo código de outras fontes sem crédito  
✅ Você não está reproduzindo código de projetos proprietários  
✅ Você entende que suas contribuições ficarão sob **a mesma licença** deste projeto  
✅ Você **NÃO** usará este código para fins comerciais sem autorização do proprietário  
✅ Você reconhece Elton Sarmanho Siqueira como proprietário original  

---

## 🎯 Como Contribuir

### 1. Fork e Branch

```bash
# Clone seu fork
git clone https://github.com/seu-usuario/FasiTech.git
cd FasiTech

# Crie uma branch com nome descritivo
git checkout -b feat/sua-feature
# ou
git checkout -b fix/seu-bug
```

**Convenção de nomes**:
- `feat/`: nova funcionalidade
- `fix/`: correção de bug
- `refactor/`: reorganização de código
- `docs/`: alterações de documentação
- `test/`: testes
- `chore/`: manutenção/limpeza

---

### 2. Faça Suas Alterações

#### Código

- Siga o padrão de código do projeto
- Adicione testes para funcionalidades novas
- Documente mudanças significativas
- Remova código morto

#### Licença

**Inclua o header de licença em arquivos novos**:

```python
# FasiTech — Portal Acadêmico UFPA/FASI
# Licença: Licença de Uso Restrito com Proteção Acadêmica v1.0
# Copyright © 2024-2026 Faculdade de Sistemas de Informação (FASI) — UFPA
# Modificações por: [SEU NOME], [DATA]
# Proibido uso comercial sem autorização explícita.
```

```tsx
// FasiTech — Portal Acadêmico UFPA/FASI
// Licença: Licença de Uso Restrito com Proteção Acadêmica v1.0
// Copyright © 2024-2026 Faculdade de Sistemas de Informação (FASI) — UFPA
// Modificações por: [SEU NOME], [DATA]
// Proibido uso comercial sem autorização explícita.
```

---

### 3. Commit com Mensagem Clara

```bash
git add .
git commit -m "feat: adiciona formulário CCF com validação de disciplinas

- Implementa validação de pré-requisitos
- Integra com Google Sheets para rastreamento
- Adiciona testes unitários
- Documenta fluxo de aprovação"
```

**Formato**:
- 1ª linha: tipo e descrição breve (máx 70 caracteres)
- Linhas subsequentes: detalhes, quebras de linha para cada ponto

---

### 4. Push e Pull Request

```bash
git push origin feat/sua-feature
```

**Acesse GitHub** e crie uma Pull Request com:

**Título**: Descrição concisa da mudança

**Descrição**:
```markdown
## 📝 Descrição
Breve explicação do que foi feito e por quê.

## 🔍 Tipo de Mudança
- [ ] Bugfix (correção sem quebra de compatibilidade)
- [ ] Feature (nova funcionalidade)
- [ ] Breaking change (muda comportamento existente)
- [ ] Docs (atualização de documentação)

## ✅ Checklist
- [ ] Testei as mudanças localmente
- [ ] Adicionei testes (se aplicável)
- [ ] Atualizei documentação
- [ ] Removi código morto
- [ ] Li e aceito a LICENSE.md
- [ ] Meu código não inclui terceiros sem crédito
- [ ] Não há uso comercial não autorizado

## 🧪 Como Testar
1. Passo para reproduzir mudança
2. Resultado esperado
3. Resultado obtido

## 📸 Screenshots (se aplicável)
[Anexar imagens de UI changes]
```

---

## 🛑 Verificações Obrigatórias

Antes de enviar seu PR, certifique-se que:

### Código
- [ ] Sem erros de linting
- [ ] Sem code smells flagrados pelo SonarQube
- [ ] Testes passando localmente
- [ ] TypeScript sem erros de type-check

```bash
# Frontend
cd frontend && npm run lint && npm run type-check && npm test

# Backend
python -m pytest backend/tests --cov=backend
```

### Documentação
- [ ] README atualizado (se muda rotas/features)
- [ ] Swagger/OpenAPI documentado (se novo endpoint)
- [ ] Componentes exportados no `index.ts` (se novo componente)
- [ ] `.env.example` atualizado (se novas variáveis)

### Conformidade
- [ ] Header de licença em novos arquivos
- [ ] Sem código de terceiros sem atribuição
- [ ] Sem credentials commitadas (`.env`, chaves API)
- [ ] Sem logs de debug
- [ ] Sem arquivos temporários ou IDE-specific

---

## 📋 Revisão do PR

A equipe revisará seu PR considerando:

### Funcionalidade
- ✅ A feature foi implementada corretamente?
- ✅ Casos extremos estão tratados?
- ✅ Performance é aceitável?

### Código
- ✅ Segue convenções do projeto?
- ✅ É legível e manutenível?
- ✅ Não introduz breaking changes?

### Testes
- ✅ Coverage adequado?
- ✅ Testes cobrem casos de erro?

### Conformidade
- ✅ Respeita a licença?
- ✅ Sem violação de propriedade intelectual?

Se forem solicitadas mudanças, faça e faça push na mesma branch (o PR será atualizado automaticamente).

---

## 🚫 Comportamento Inaceitável

**Não serão aceitas contribuições que**:

❌ Incluam código de terceiros sem crédito/licença apropriada  
❌ Implementem recursos para uso comercial não autorizado  
❌ Violem privacidade ou segurança de dados (LGPD)  
❌ Contenham linguagem ofensiva ou discriminação  
❌ Sejam triviais (typo fixing sem contexto maior)  
❌ Duplicarem PRs abertas  
❌ Ignorem a licença ou guidelines  

Violações resultarão em **bloqueio da conta** e possível **denúncia legal**.

---

## 💰 Uso Comercial

Se você quer usar FasiTech em um **projeto comercial** ou SaaS:

1. **NÃO** use código direto do repositório sem autorização
2. **Envie email** para `eltonsarmanho@gmail.com`
3. **Apresente sua proposta** comercial
4. **Negocie termos** de licença pagando
5. **Obtenha permissão escrita** antes de usar

Uso comercial não autorizado resultará em:
- Ação civil com multa de R$ 5.000 a R$ 100.000
- Ação criminal conforme Lei 9.610/98
- Bloqueio de repositórios

---

## 📚 Recursos Úteis

- [Licença Completa](./LICENSE.md)
- [Arquitetura do Sistema](./docs/ARQUITETURA_SISTEMA.md)
- [Fluxos de Integração](./docs/FLUXOS_INTEGRACAO.md)
- [FastAPI Docs](https://www.fasitech.com.br/docs)

---

## ❓ Dúvidas?

- Abra uma **issue** com tag `question`
- Envie email para `eltonsarmanho@gmail.com`
- Verifique se está documentado em [docs/](./docs/)

---

## ✨ Agradecimentos

Obrigado por contribuir com responsabilidade! Sua colaboração mantém FasiTech inovador e ético. 🎓

**Versão**: 1.0 — Data: 05/07/2026

© 2024-2026 FasiTech — FASI/UFPA. Todos os direitos reservados.
