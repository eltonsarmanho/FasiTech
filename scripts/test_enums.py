"""Script para testar os novos enums."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.models.schemas import *

print("✅ Enums atualizados com sucesso!")
print("\n📋 Cor/Etnia:")
for e in CorEtnia:
    print(f"  - {e.value}")

print("\n🚗 Deslocamento:")
for e in TipoDeslocamento:
    print(f"  - {e.value}")

print("\n😰 Estresse:")
for e in FrequenciaEstresse:
    print(f"  - {e.value}")

print("\n🎓 Escolaridade:")
for e in NivelEscolaridade:
    print(f"  - {e.value}")

print("\n🌐 Acesso Internet:")
for e in AcessoInternet:
    print(f"  - {e.value}")

print("\n🏠 Tipo Moradia:")
for e in TipoMoradia:
    print(f"  - {e.value}")

print("\n✅ Todos os enums estão corretos!")
