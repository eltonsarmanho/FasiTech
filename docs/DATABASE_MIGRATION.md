# Migração de Google Sheets para PostgreSQL

Este documento descreve a migração do sistema de armazenamento de dados de Google Sheets para banco de dados PostgreSQL usando SQLModel (ORM).

## 📋 Visão Geral

- **Antes:** Dados salvos em planilhas do Google Sheets
- **Depois:** Dados salvos em banco de dados PostgreSQL
- **ORM:** SQLModel (combina SQLAlchemy + Pydantic)
- **Benefícios:** Maior confiabilidade, estrutura de dados rígida, sem dependência de APIs externas instáveis

## 🗄️ Configuração do Banco de Dados

### Variável de Ambiente

O banco de dados é configurado através da variável de ambiente `DATABASE_URL`:

```bash
# Desenvolvimento (com SSH tunnel)
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech

# Produção (direto na VM UFPA)
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

### Estrutura de Diretórios

```
src/
├── database/
│   ├── __init__.py
│   ├── engine.py         # Configuração do engine e sessões
│   └── repository.py     # Funções para salvar dados
├── models/
│   └── db_models.py      # Modelos SQLModel (tabelas)
```

## 📊 Tabelas Criadas

### 1. tcc_submissions
Armazena submissões de TCC (TCC 1 e TCC 2)

**Campos:**
- id (PK)
- submission_date
- nome, matricula, email, turma
- orientador, titulo, componente
- anexos (links dos arquivos)
- drive_folder_id
- status

### 2. acc_submissions
Armazena submissões de ACC (Atividades Complementares)

**Campos:**
- id (PK)
- submission_date
- nome, matricula, email, turma, semestre
- arquivo_pdf_link
- drive_file_id
- status

### 3. projetos_submissions
Armazena submissões de Projetos (Novo, Renovação, Encerramento)

**Campos:**
- id (PK)
- submission_date
- docente, parecerista1, parecerista2
- nome_projeto, carga_horaria, edital, natureza, ano_edital
- solicitacao (Novo/Renovação/Encerramento)
- anexos, pdf_parecer, pdf_declaracao
- drive_folder_id
- status

### 4. plano_ensino_submissions
Armazena submissões de Planos de Ensino

**Campos:**
- id (PK)
- submission_date
- professor, disciplina, codigo_disciplina
- periodo_letivo, carga_horaria
- anexos
- drive_folder_id
- status

### 5. estagio_submissions
Armazena submissões de Estágio (Plano e Relatório Final)

**Campos:**
- id (PK)
- submission_date
- nome, matricula, email, turma
- orientador, titulo, componente
- anexos
- drive_folder_id
- status

### 6. social_submissions
Armazena submissões do formulário Social/Acadêmico/Saúde

**Campos:**
- id (PK)
- submission_date
- nome, matricula, email, turma
- periodo_referencia
- dados_sociais (JSON)
- status

## 🚀 Instalação

### 1. Instalar dependências

```bash
pip install sqlmodel psycopg2-binary
```

### 2. Configurar variável de ambiente

```bash
export DATABASE_URL="postgresql://postgres:adminadmin@localhost:5432/fasitech"
```

Ou adicione ao arquivo `.env`:

```env
DATABASE_URL=postgresql://postgres:adminadmin@localhost:5432/fasitech
```

### 3. Testar conexão

```bash
python scripts/test_database.py
```

### 4. Inicializar tabelas

As tabelas são criadas automaticamente na primeira execução do sistema através de `init_db()` no `main.py`.

## 📝 Uso

### Salvando dados no banco

```python
from src.database.repository import save_tcc_submission

data = {
    "name": "João Silva",
    "registration": "202312345",
    "email": "joao@ufpa.br",
    "class_group": "2027",
    "orientador": "Prof. Dr. Maria Santos",
    "titulo": "Análise de Sistemas",
    "componente": "TCC 2",
    "anexos": "file1.pdf: http://...\nfile2.pdf: http://...",
    "drive_folder_id": "1abc..."
}

submission_id = save_tcc_submission(data)
print(f"Submissão salva com ID: {submission_id}")
```

### Consultando dados

```python
from src.database.engine import get_db_session
from src.models.db_models import TccSubmission
from sqlmodel import select

with get_db_session() as session:
    # Buscar todos os TCCs
    tccs = session.exec(select(TccSubmission)).all()
    
    # Buscar por matrícula
    tcc = session.exec(
        select(TccSubmission).where(TccSubmission.matricula == "202312345")
    ).first()
    
    # Buscar TCCs de uma turma
    tccs_turma = session.exec(
        select(TccSubmission).where(TccSubmission.turma == "2027")
    ).all()
```

## 🔄 Migração de Dados Existentes

Se você tiver dados nas planilhas do Google Sheets e quiser migrá-los para o banco de dados:

1. Exporte os dados das planilhas para CSV
2. Crie um script de migração que leia o CSV e salve no banco
3. Execute o script

Exemplo de script de migração:

```python
import csv
from src.database.repository import save_tcc_submission

with open('tcc_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data = {
            "name": row['Nome'],
            "registration": row['Matrícula'],
            # ... mapear outros campos
        }
        save_tcc_submission(data)
```

## 🛠️ Troubleshooting

### Erro: "Could not connect to PostgreSQL"

**Solução:**
1. Verifique se o PostgreSQL está rodando
2. Verifique se o SSH tunnel está ativo (desenvolvimento)
3. Verifique as credenciais no `DATABASE_URL`

### Erro: "relation does not exist"

**Solução:**
Execute `init_db()` para criar as tabelas:

```python
from src.database.engine import init_db
init_db()
```

### Erro: "psycopg2 not found"

**Solução:**
```bash
pip install psycopg2-binary
```

## 📦 Backup

### Backup manual

```bash
pg_dump -U postgres -h localhost -d fasitech > backup_fasitech_$(date +%Y%m%d).sql
```

### Restaurar backup

```bash
psql -U postgres -h localhost -d fasitech < backup_fasitech_20260112.sql
```

### Backup automático

Configure um cron job para fazer backup diário:

```bash
0 2 * * * /usr/bin/pg_dump -U postgres -h localhost -d fasitech > /backups/fasitech_$(date +\%Y\%m\%d).sql
```

## 🔮 Próximos Passos

1. ✅ Migração de Google Sheets para PostgreSQL
2. ⏳ Implementar interface de administração para consultar dados
3. ⏳ Criar relatórios e dashboards
4. ⏳ Implementar auditoria de mudanças
5. ⏳ Adicionar índices para otimização de consultas

## 📚 Referências

- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
