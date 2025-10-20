# Configuração para adicionar o diretório raiz ao PYTHONPATH
import sys
from pathlib import Path

# Adicionar diretório raiz do projeto ao sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
