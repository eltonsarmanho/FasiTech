#!/usr/bin/env python3
"""
Teste isolado do RAG - Debug passo a passo
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
import traceback

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Adicionar projeto ao path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("DEBUG RAG - TESTE ISOLADO PASSO A PASSO")
print("=" * 80)
print(f"🕒 Iniciado em: {datetime.now()}")
print(f"📂 Diretório atual: {Path.cwd()}")
print(f"🐍 Python: {sys.version}")
print(f"📁 PROJECT_ROOT: {PROJECT_ROOT}")

def test_imports():
    """Testa imports das dependências uma por uma"""
    print("\n" + "="*60)
    print("1️⃣  TESTE DE IMPORTS")
    print("="*60)
    
    imports_to_test = [
        ("os", "os"),
        ("pathlib", "from pathlib import Path"),
        ("datetime", "from datetime import datetime"),
        ("dotenv", "from dotenv import load_dotenv"),
        ("agno.models.google", "from agno.models.google import Gemini"),
        ("agno.agent", "from agno.agent import Agent"),
        ("agno.db.sqlite", "from agno.db.sqlite import SqliteDb"),
        ("agno.knowledge.embedder.ollama", "from agno.knowledge.embedder.ollama import OllamaEmbedder"),
        ("agno.knowledge.knowledge", "from agno.knowledge.knowledge import Knowledge"),
        ("agno.vectordb.lancedb", "from agno.vectordb.lancedb import LanceDb, SearchType"),
        ("agno.models.huggingface", "from agno.models.huggingface import HuggingFace"),
        ("lancedb", "import lancedb"),
    ]
    
    failed_imports = []
    
    for name, import_cmd in imports_to_test:
        try:
            exec(import_cmd)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            failed_imports.append(name)
    
    if failed_imports:
        print(f"\n⚠️  ERRO: {len(failed_imports)} imports falharam!")
        return False
    else:
        print(f"\n✅ Todos os {len(imports_to_test)} imports OK!")
        return True

def test_env_vars():
    """Testa variáveis de ambiente"""
    print("\n" + "="*60)
    print("2️⃣  TESTE DE VARIÁVEIS DE AMBIENTE")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    env_vars = {
        "HF_TOKEN": os.getenv("HF_TOKEN"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
        "MARITALK_API_KEY": os.getenv("MARITALK_API_KEY"),
    }
    
    for var_name, var_value in env_vars.items():
        status = "✅" if var_value else "❌"
        value_display = f"{var_value[:10]}..." if var_value else "Não definida"
        print(f"{status} {var_name}: {value_display}")
    
    has_any_key = any(env_vars.values())
    if not has_any_key:
        print("\n⚠️  ERRO: Nenhuma API key encontrada!")
        return False
    
    print(f"\n✅ Pelo menos uma API key disponível!")
    return True

def test_ppc_file():
    """Testa localização do arquivo PPC.pdf"""
    print("\n" + "="*60)
    print("3️⃣  TESTE DO ARQUIVO PPC.PDF")
    print("="*60)
    
    candidates = [
        PROJECT_ROOT / "src" / "resources" / "PPC.pdf",
        Path("/app/src/resources/PPC.pdf"),
        Path.cwd() / "src" / "resources" / "PPC.pdf",
    ]
    
    ppc_found = None
    for candidate in candidates:
        exists = candidate.exists()
        if exists:
            size = f"{candidate.stat().st_size / 1024 / 1024:.2f} MB"
            print(f"✅ {candidate} ({size})")
            if ppc_found is None:
                ppc_found = candidate
        else:
            print(f"❌ {candidate}")
    
    if ppc_found:
        print(f"\n✅ PPC.pdf encontrado: {ppc_found}")
        return str(ppc_found)
    else:
        print(f"\n⚠️  ERRO: PPC.pdf não encontrado!")
        return None

def test_cache_dir():
    """Testa criação do diretório de cache"""
    print("\n" + "="*60)
    print("4️⃣  TESTE DO DIRETÓRIO DE CACHE")
    print("="*60)
    
    cache_dir = Path.home() / ".cache" / "fasitech" / "rag"
    
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Cache criado: {cache_dir}")
        
        # Testar permissões de escrita
        test_file = cache_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print(f"✅ Permissões de escrita OK")
        
        return str(cache_dir)
    except Exception as e:
        print(f"❌ Erro ao criar cache: {e}")
        return None

def test_model_creation():
    """Testa criação do modelo"""
    print("\n" + "="*60)
    print("5️⃣  TESTE DE CRIAÇÃO DO MODELO")
    print("="*60)
    
    try:
        from agno.models.google import Gemini
        from agno.models.huggingface import HuggingFace
        
        # Tentar Gemini primeiro
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            print("🔍 Testando Gemini...")
            try:
                model = Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key)
                print("✅ Modelo Gemini criado com sucesso!")
                return model
            except Exception as e:
                print(f"❌ Gemini falhou: {e}")
        
        # Fallback para HuggingFace
        print("🔍 Testando HuggingFace...")
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            try:
                model = HuggingFace(
                    id="microsoft/Phi-3.5-mini-instruct",
                    api_key=hf_token,
                    base_url="https://api-inference.huggingface.co/models"
                )
                print("✅ Modelo HuggingFace criado com sucesso!")
                return model
            except Exception as e:
                print(f"❌ HuggingFace falhou: {e}")
        
        print("❌ Nenhum modelo pôde ser criado")
        return None
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        traceback.print_exc()
        return None

def test_embedder():
    """Testa criação do embedder"""
    print("\n" + "="*60)
    print("6️⃣  TESTE DO EMBEDDER")
    print("="*60)
    
    try:
        from agno.knowledge.embedder.ollama import OllamaEmbedder
        
        embedder = OllamaEmbedder(
            id="nomic-embed-text", 
            dimensions=768,
        )
        print("✅ Embedder Ollama criado com sucesso!")
        return embedder
        
    except Exception as e:
        print(f"❌ Erro ao criar embedder: {e}")
        traceback.print_exc()
        return None

def test_vectordb(cache_dir, embedder):
    """Testa criação do banco vetorial"""
    print("\n" + "="*60)
    print("7️⃣  TESTE DO BANCO VETORIAL")
    print("="*60)
    
    try:
        from agno.vectordb.lancedb import LanceDb, SearchType
        
        db_url = f"{cache_dir}/lancedb"
        
        vector_db = LanceDb(
            table_name="recipes",
            uri=db_url,
            embedder=embedder,
            search_type=SearchType.hybrid,
        )
        print(f"✅ LanceDB criado: {db_url}")
        return vector_db
        
    except Exception as e:
        print(f"❌ Erro ao criar LanceDB: {e}")
        traceback.print_exc()
        return None

def test_knowledge_loading(vector_db, ppc_file):
    """Testa carregamento da base de conhecimento"""
    print("\n" + "="*60)
    print("8️⃣  TESTE DE CARREGAMENTO DO PPC")
    print("="*60)
    
    try:
        from agno.knowledge.knowledge import Knowledge
        
        knowledge = Knowledge(vector_db=vector_db, max_results=25)
        
        # Verificar se já existe
        try:
            import lancedb
            db = lancedb.connect(vector_db.uri)
            table = db.open_table("recipes")
            doc_count = table.count_rows()
            
            if doc_count > 0:
                print(f"✅ Base existente com {doc_count} documentos")
                return knowledge
        except:
            print("ℹ️  Nenhuma base existente encontrada")
        
        # Carregar PPC
        print("📚 Carregando PPC.pdf...")
        knowledge.add_content(
            name="PPC Document",
            path=ppc_file
        )
        print("✅ PPC.pdf carregado com sucesso!")
        return knowledge
        
    except Exception as e:
        print(f"❌ Erro ao carregar PPC: {e}")
        traceback.print_exc()
        return None

def test_question(model, knowledge, cache_dir):
    """Testa pergunta ao RAG"""
    print("\n" + "="*60)
    print("9️⃣  TESTE DE PERGUNTA")
    print("="*60)
    
    try:
        from agno.agent import Agent
        from agno.db.sqlite import SqliteDb
        
        # SQLite
        sqlite_path = f"{cache_dir}/ppc_chat.db"
        db = SqliteDb(db_file=sqlite_path)
        
        # Agente
        agent = Agent(
            session_id="test_session",
            model=model,
            knowledge=knowledge,
            storage=db,
            instructions=[
                "Você é um assistente especializado no Projeto Pedagógico do Curso (PPC) de Sistemas de Informação.",
                "Responda sempre com base no conteúdo do PPC fornecido.",
                "Se não encontrar informação específica, diga claramente que não encontrou.",
                "Seja preciso e cite detalhes relevantes do PPC quando possível."
            ]
        )
        
        # Pergunta de teste
        question = "Qual é o objetivo do curso de Sistemas de Informação?"
        print(f"❓ Pergunta: {question}")
        print("🤖 Processando...")
        
        start_time = datetime.now()
        response = agent.run(question)
        end_time = datetime.now()
        
        latency = (end_time - start_time).total_seconds()
        
        print(f"✅ Resposta recebida em {latency:.2f}s")
        print(f"📝 Resposta: {response.content[:200]}...")
        
        # Verificar se resposta contém informação real
        if "não encontrei" in response.content.lower() or "não consegui" in response.content.lower():
            print("⚠️  PROBLEMA: Resposta indica que não encontrou informação")
            return False
        else:
            print("✅ Resposta contém informação sobre o curso!")
            return True
        
    except Exception as e:
        print(f"❌ Erro ao fazer pergunta: {e}")
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes em sequência"""
    
    tests = [
        ("Imports", test_imports),
        ("Variáveis de Ambiente", test_env_vars),
        ("Arquivo PPC", test_ppc_file),
        ("Diretório de Cache", test_cache_dir),
        ("Modelo", test_model_creation),
        ("Embedder", test_embedder),
    ]
    
    results = {}
    
    # Executar testes iniciais
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                print(f"\n❌ FALHA no teste: {test_name}")
                return False
        except Exception as e:
            print(f"\n💥 ERRO CRÍTICO no teste {test_name}: {e}")
            traceback.print_exc()
            return False
    
    # Testes que dependem de resultados anteriores
    try:
        cache_dir = results["Diretório de Cache"]
        embedder = results["Embedder"]
        model = results["Modelo"]
        ppc_file = results["Arquivo PPC"]
        
        # Teste VectorDB
        vector_db = test_vectordb(cache_dir, embedder)
        if not vector_db:
            return False
        
        # Teste Knowledge
        knowledge = test_knowledge_loading(vector_db, ppc_file)
        if not knowledge:
            return False
        
        # Teste final
        success = test_question(model, knowledge, cache_dir)
        
        print("\n" + "="*80)
        if success:
            print("🎉 TODOS OS TESTES PASSARAM! RAG FUNCIONANDO CORRETAMENTE!")
        else:
            print("⚠️  RAG INICIALIZADO MAS NÃO ENCONTRA INFORMAÇÕES DO PPC")
        print("="*80)
        
        return success
        
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO nos testes avançados: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n💥 ERRO FATAL: {e}")
        traceback.print_exc()