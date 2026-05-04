#!/usr/bin/env python3
"""
Script para verificar a configuração do PPC e base de dados RAG.
"""

import sys
from pathlib import Path
import os

# Adicionar projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 70)
print("VERIFICAÇÃO DO SETUP DO RAG")
print("=" * 70)

# 1. Verificar arquivo PPC
print("\n1️⃣  VERIFICANDO ARQUIVO PPC.pdf")
print("-" * 70)

ppc_candidates = [
    PROJECT_ROOT / "src" / "resources" / "PPC.pdf",
    Path.cwd() / "src" / "resources" / "PPC.pdf",
    Path("/home/ubuntu/appStreamLit/src/resources/PPC.pdf"),
]

ppc_found = None
for candidate in ppc_candidates:
    exists = candidate.exists()
    size = f"{candidate.stat().st_size / 1024 / 1024:.2f} MB" if exists else "N/A"
    status = "✅" if exists else "❌"
    print(f"{status} {candidate} ({size})")
    if exists and ppc_found is None:
        ppc_found = candidate

if ppc_found:
    print(f"\n✅ PPC.pdf localizado: {ppc_found}")
else:
    print("\n❌ PPC.pdf NÃO ENCONTRADO em nenhum caminho!")

# 2. Verificar diretório de cache
print("\n2️⃣  VERIFICANDO DIRETÓRIO DE CACHE")
print("-" * 70)

cache_dir = Path.home() / ".cache" / "fasitech" / "rag"
cache_dir.mkdir(parents=True, exist_ok=True)
print(f"📁 Diretório de cache: {cache_dir}")
print(f"✅ Permissões: OK")

# 3. Verificar banco de dados
print("\n3️⃣  VERIFICANDO BANCO DE DADOS")
print("-" * 70)

db_url = str(cache_dir / "lancedb")
sqlite_db = str(cache_dir / "ppc_chat.db")

print(f"📊 LanceDB URI: {db_url}")
print(f"📊 SQLite DB: {sqlite_db}")

# 4. Tentar inicializar o serviço
print("\n4️⃣  TESTANDO INICIALIZAÇÃO DO SERVIÇO RAG")
print("-" * 70)

try:
    from src.services.rag_ppc import ChatbotService
    
    print("Inicializando PPCChatbotService...")
    service = ChatbotService()
    
    status = service.get_status()
    print(f"\n✅ Serviço inicializado com sucesso!")
    print(f"   Model Type: {status.get('model_type')}")
    print(f"   Knowledge Loaded: {status.get('knowledge_loaded')}")
    print(f"   Total Questions: {status.get('total_questions')}")
    
except Exception as e:
    print(f"❌ Erro ao inicializar serviço: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("VERIFICAÇÃO CONCLUÍDA")
print("=" * 70)
