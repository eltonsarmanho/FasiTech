# 🗄️ Status dos Bancos de Dados

## ✅ Bancos Criados

### 1. Local (Desenvolvimento)
- **Host:** localhost
- **Porta:** 5432
- **Banco:** fasitech
- **Status:** ✅ Criado e funcionando
- **Tabelas:** 6 tabelas criadas
- **Script:** `python scripts/create_database.py`

### 2. Hostinger (Produção)
- **Host:** 72.60.6.113
- **Porta:** 5432
- **Banco:** fasitech
- **Status:** ✅ Criado e funcionando
- **Script:** `./scripts/create_remote_database.sh`

### 3. VM UFPA (Futura Migração)
- **Host:** 172.16.28.198
- **Porta:** 5432
- **Banco:** fasitech
- **Status:** ⏳ Aguardando criação
- **Script:** `./scripts/create_remote_database_ufpa.sh`

## 📋 Scripts Disponíveis

### Desenvolvimento Local
```bash
# Criar banco de dados local
python scripts/create_database.py

# Testar conexão e criar tabelas
python scripts/test_database.py
```

### Produção (Hostinger)
```bash
# Criar banco remoto
./scripts/create_remote_database.sh

# Após deploy, as tabelas são criadas automaticamente
```

### VM UFPA (Quando migrar)
```bash
# Criar banco remoto
./scripts/create_remote_database_ufpa.sh
```

## 🔄 Migração Completa de Google Sheets → PostgreSQL

### ✅ O que já está pronto:

1. **Modelos de dados** - 6 tabelas mapeadas ([src/models/db_models.py](../src/models/db_models.py))
2. **Repositório** - Funções para salvar dados ([src/database/repository.py](../src/database/repository.py))
3. **Integração** - form_service.py atualizado para salvar no banco
4. **Bancos criados:**
   - ✅ Local (desenvolvimento)
   - ✅ Hostinger (produção)
   - ⏳ VM UFPA (futura)

### 📊 Tabelas do Sistema

```
tcc_submissions              - Submissões de TCC (TCC 1 e 2)
acc_submissions              - Submissões de ACC
projetos_submissions         - Projetos (Novo/Renovação/Encerramento)
plano_ensino_submissions     - Planos de Ensino
estagio_submissions          - Estágios (Plano e Relatório)
social_submissions           - Dados Sociais/Saúde
```

## 🚀 Deploy e Configuração

### Ambiente Local (.env ou secrets.toml)
```ini
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

### Ambiente Produção - Hostinger
```ini
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

### Ambiente Produção - VM UFPA
```ini
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

> **Nota:** Todas as configurações usam `localhost` porque o PostgreSQL roda no mesmo servidor da aplicação.

## 🔍 Verificar Dados

### Via Python
```python
from src.database.engine import get_db_session
from src.models.db_models import TccSubmission
from sqlmodel import select

with get_db_session() as session:
    tccs = session.exec(select(TccSubmission)).all()
    print(f"Total de TCCs: {len(tccs)}")
```

### Via Terminal (psql)

**Local:**
```bash
psql -h localhost -U postgres -d fasitech
SELECT COUNT(*) FROM tcc_submissions;
\q
```

**Remoto (Hostinger):**
```bash
ssh root@72.60.6.113
sudo -u postgres psql -d fasitech
SELECT COUNT(*) FROM tcc_submissions;
\q
```

**Remoto (VM UFPA):**
```bash
ssh eltonss@172.16.28.198
sudo -u postgres psql -d fasitech
SELECT COUNT(*) FROM tcc_submissions;
\q
```

## 📝 Próximos Passos

1. ✅ Banco local criado
2. ✅ Banco Hostinger criado
3. ⏳ Testar submissão de formulário (TCC ou ACC)
4. ⏳ Verificar se dados foram salvos corretamente
5. ⏳ Deploy na Hostinger com nova configuração
6. ⏳ Criar interface de administração para consultar dados

## 🛠️ Troubleshooting

### "Connection refused"
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Se não estiver, iniciar
sudo systemctl start postgresql
```

### "Database does not exist"
```bash
# Local
python scripts/create_database.py

# Hostinger
./scripts/create_remote_database.sh

# VM UFPA
./scripts/create_remote_database_ufpa.sh
```

### Verificar logs de erro
```bash
# Local
tail -f /var/log/postgresql/postgresql-*.log

# Remoto
ssh root@72.60.6.113 "sudo tail -f /var/log/postgresql/postgresql-*.log"
```

## 📚 Documentação Completa

- [DATABASE_QUICKSTART.md](DATABASE_QUICKSTART.md) - Guia rápido
- [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) - Guia completo da migração
