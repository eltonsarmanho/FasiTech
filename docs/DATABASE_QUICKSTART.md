# 🚀 Guia Rápido - Banco de Dados FasiTech

## ✅ Status Atual

- ✅ Banco de dados `fasitech` criado
- ✅ 6 tabelas criadas e funcionando:
  - `tcc_submissions`
  - `acc_submissions`
  - `projetos_submissions`
  - `plano_ensino_submissions`
  - `estagio_submissions`
  - `social_submissions`

## 🔧 Scripts Disponíveis

### 1. Criar Banco de Dados
```bash
python scripts/create_database.py
```

### 2. Testar Conexão
```bash
python scripts/test_database.py
```

### 3. SSH Tunnel (se necessário)
```bash
./scripts/setup_ssh_tunnel.sh
```

## 💾 Sistema Atual

### Você tem PostgreSQL LOCAL rodando
A porta 5432 já está em uso localmente, o que significa que você tem PostgreSQL instalado e rodando na sua máquina. **Não precisa de SSH tunnel para desenvolvimento local!**

### Configuração Atual
```
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

## 📝 Consultar Dados

### Via Python
```python
from src.database.engine import get_db_session
from src.models.db_models import TccSubmission
from sqlmodel import select

with get_db_session() as session:
    # Listar todos os TCCs
    tccs = session.exec(select(TccSubmission)).all()
    for tcc in tccs:
        print(f"{tcc.nome} - {tcc.titulo}")
```

### Via Terminal (psql)
```bash
# Conectar ao banco
psql -h localhost -U postgres -d fasitech

# Listar tabelas
\dt

# Ver dados de uma tabela
SELECT * FROM tcc_submissions;

# Sair
\q
```

## 🎯 Próximos Passos

1. ✅ Banco criado e tabelas prontas
2. ⏳ Testar submissão de um formulário
3. ⏳ Verificar se os dados são salvos corretamente
4. ⏳ Criar interface de administração para consultar dados

## 🔄 Para Deploy (Produção)

Quando for fazer deploy na VM da UFPA, a configuração será a mesma:

```bash
# No servidor de produção
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

Apenas certifique-se de:
1. Criar o banco: `python scripts/create_database.py`
2. Executar a aplicação normalmente

## 📊 Estrutura das Tabelas

Todas as tabelas têm:
- `id` (chave primária)
- `submission_date` (data/hora da submissão)
- `status` (recebido, processado, aprovado, etc)
- Campos específicos de cada formulário

## 🛠️ Troubleshooting

### "Connection refused"
PostgreSQL não está rodando:
```bash
sudo systemctl start postgresql
```

### "Authentication failed"
Senha incorreta. Verifique o DATABASE_URL

### "Database does not exist"
Execute:
```bash
python scripts/create_database.py
```
