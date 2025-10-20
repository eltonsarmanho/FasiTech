# Executando a Aplicação

## Opção 1: Usando o script de inicialização (Recomendado)

```bash
# Do diretório raiz do projeto
./scripts/start.sh
```

## Opção 2: Manualmente com PYTHONPATH

```bash
# Do diretório raiz do projeto
export PYTHONPATH="${PWD}:${PYTHONPATH}"
source venv/bin/activate  # ou .venv/bin/activate
streamlit run src/app/main.py
```

## Opção 3: Via Python diretamente

```bash
# Do diretório raiz do projeto
source venv/bin/activate
python -m streamlit run src/app/main.py
```

## Estrutura de Imports

Os arquivos dentro de `src/app/pages/` adicionam automaticamente o diretório raiz ao `sys.path` para permitir imports do tipo:

```python
from src.services.form_service import process_acc_submission
from src.models.schemas import AccSubmission
```

## Troubleshooting

### ModuleNotFoundError: No module named 'src'

Se você encontrar este erro, certifique-se de:

1. Executar a aplicação do diretório raiz do projeto
2. Usar o script `scripts/start.sh` que configura o PYTHONPATH automaticamente
3. Ou definir manualmente: `export PYTHONPATH="${PWD}:${PYTHONPATH}"`

### Imports não resolvidos no VSCode

Adicione ao `.vscode/settings.json`:

```json
{
    "python.analysis.extraPaths": ["${workspaceFolder}"],
    "python.autoComplete.extraPaths": ["${workspaceFolder}"]
}
```
