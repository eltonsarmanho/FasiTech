"""
Configuração compartilhada da suíte de testes.

`backend/infrastructure/database/engine.py` levanta `ValueError` já no import se
`DATABASE_URL` não estiver no ambiente. Qualquer módulo de teste que importe o
repositório — mesmo que depois mocke tudo — falha na COLETA por causa disso.

Hoje isso só não acontece por sorte de ordem alfabética: `test_maritalk.py` é
coletado antes de `test_tcc_scheduling.py` e chama `load_dotenv()` no import,
populando a variável de passagem. Rodar `test_tcc_scheduling.py` sozinho falha.

Aqui damos um SQLite descartável como padrão. `setdefault` preserva um
`DATABASE_URL` exportado de propósito (ex.: teste de integração apontado para um
Postgres real), então isto não sequestra nada.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "fasitech_pytest.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TEST_DB}")
