#!/usr/bin/env python3
"""
Investigação detalhada da base vetorial e vetorização
"""

import sys
import os
from pathlib import Path
import logging

# Setup básico
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("🔍 INVESTIGAÇÃO DETALHADA - BASE VETORIAL E VETORIZAÇÃO")
print("=" * 80)

def investigate_vectorization():
    """Investiga se os dados estão sendo vetorizados corretamente"""
    
    print("\n1️⃣  VERIFICANDO OLLAMA E EMBEDDER")
    print("-" * 60)
    
    # Testar conexão com Ollama
    try:
        import requests
        
        # Verificar se Ollama está rodando
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ Ollama rodando - versão: {version_info.get('version', 'unknown')}")
        else:
            print(f"❌ Ollama responde mas com erro: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ollama não acessível: {e}")
        print("💡 Dica: Execute 'ollama serve' na VM")
    
    # Testar embedder diretamente
    try:
        from agno.knowledge.embedder.ollama import OllamaEmbedder
        
        embedder = OllamaEmbedder(id="nomic-embed-text", dimensions=768)
        print("✅ Embedder criado")
        
        # Testar embedding de um texto simples
        test_text = "Este é um teste de embedding"
        print(f"🧪 Testando embedding do texto: '{test_text}'")
        
        embedding = embedder.get_embedding(test_text)
        if embedding and len(embedding) > 0:
            print(f"✅ Embedding gerado - dimensão: {len(embedding)}")
        else:
            print("❌ Embedding vazio ou nulo")
            
    except Exception as e:
        print(f"❌ Erro no embedder: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n2️⃣  VERIFICANDO ARQUIVO PPC.PDF")
    print("-" * 60)
    
    # Localizar PPC.pdf
    ppc_candidates = [
        Path("/app/src/resources/PPC.pdf"),
        Path.cwd() / "src" / "resources" / "PPC.pdf",
    ]
    
    ppc_file = None
    for candidate in ppc_candidates:
        if candidate.exists():
            size_mb = candidate.stat().st_size / 1024 / 1024
            print(f"✅ PPC encontrado: {candidate} ({size_mb:.2f} MB)")
            ppc_file = candidate
            break
    
    if not ppc_file:
        print("❌ PPC.pdf não encontrado!")
        return False
    
    # Verificar se consegue ler o PDF
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(ppc_file))
        num_pages = len(reader.pages)
        
        # Ler primeira página como teste
        first_page = reader.pages[0]
        text_sample = first_page.extract_text()[:200]
        
        print(f"✅ PDF legível - {num_pages} páginas")
        print(f"📝 Amostra do texto: {text_sample}...")
        
    except Exception as e:
        print(f"❌ Erro ao ler PDF: {e}")
        return False
    
    print("\n3️⃣  VERIFICANDO BASE VETORIAL (LANCEDB)")
    print("-" * 60)
    
    # Localizar diretório de cache
    cache_dir = Path.home() / ".cache" / "fasitech" / "rag"
    db_path = cache_dir / "lancedb"
    
    print(f"📁 Diretório cache: {cache_dir}")
    print(f"🗃️ LanceDB path: {db_path}")
    
    if not db_path.exists():
        print("❌ LanceDB não existe ainda")
    else:
        print("✅ LanceDB existe")
        
        # Investigar conteúdo do LanceDB
        try:
            import lancedb
            
            db = lancedb.connect(str(db_path))
            tables = db.table_names()
            print(f"📊 Tabelas no DB: {tables}")
            
            if "recipes" in tables:
                table = db.open_table("recipes")
                row_count = table.count_rows()
                print(f"📈 Registros na tabela 'recipes': {row_count}")
                
                if row_count > 0:
                    # Mostrar alguns registros
                    sample = table.head(3)
                    print(f"📋 Amostra dos dados:")
                    for i, row in enumerate(sample.to_pylist()):
                        content = row.get('text', 'No text')[:100]
                        print(f"   Registro {i+1}: {content}...")
                else:
                    print("⚠️ Tabela existe mas está vazia!")
            else:
                print("❌ Tabela 'recipes' não encontrada")
                
        except Exception as e:
            print(f"❌ Erro ao investigar LanceDB: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n4️⃣  TESTANDO PROCESSO DE VETORIZAÇÃO COMPLETO")
    print("-" * 60)
    
    try:
        from agno.knowledge.embedder.ollama import OllamaEmbedder
        from agno.vectordb.lancedb import LanceDb, SearchType
        from agno.knowledge.knowledge import Knowledge
        
        # Configurar componentes
        embedder = OllamaEmbedder(id="nomic-embed-text", dimensions=768)
        vector_db = LanceDb(
            table_name="recipes",
            uri=str(db_path),
            embedder=embedder,
            search_type=SearchType.hybrid,
        )
        
        knowledge = Knowledge(vector_db=vector_db, max_results=25)
        
        print("✅ Componentes criados")
        
        # Verificar se precisa carregar dados
        try:
            db = lancedb.connect(str(db_path))
            table = db.open_table("recipes")
            row_count = table.count_rows()
            
            if row_count == 0:
                print("📚 Base vazia - carregando PPC.pdf...")
                print("⏳ Isto pode demorar alguns minutos...")
                
                knowledge.add_content(
                    name="PPC Document",
                    path=str(ppc_file)
                )
                
                # Verificar novamente
                table = db.open_table("recipes")
                new_count = table.count_rows()
                print(f"✅ Carregamento concluído - {new_count} registros adicionados")
                
            else:
                print(f"✅ Base já possui {row_count} registros")
                
        except Exception as e:
            print(f"❌ Erro no carregamento: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n5️⃣  TESTANDO BUSCA VETORIAL")
    print("-" * 60)
    
    try:
        # Testar busca
        query = "objetivo do curso de Sistemas de Informação"
        print(f"🔍 Buscando por: '{query}'")
        
        results = knowledge.search(query=query, num_documents=5)
        
        if results and len(results) > 0:
            print(f"✅ Busca retornou {len(results)} resultados")
            
            for i, result in enumerate(results[:3]):
                content = result.get('text', '')[:150]
                print(f"   Resultado {i+1}: {content}...")
                
        else:
            print("❌ Busca não retornou resultados!")
            return False
            
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n6️⃣  TESTANDO GERAÇÃO DE RESPOSTA")
    print("-" * 60)
    
    try:
        from agno.models.google import Gemini
        from agno.agent import Agent
        from agno.db.sqlite import SqliteDb
        
        # Configurar modelo
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY não encontrada")
            return False
            
        model = Gemini(id="gemini-2.0-flash-exp", api_key=google_api_key)
        print("✅ Modelo Gemini configurado")
        
        # Configurar SQLite
        sqlite_path = cache_dir / "ppc_chat.db"
        db = SqliteDb(db_file=str(sqlite_path))
        print("✅ SQLite configurado")
        
        # Criar agente
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
        print("✅ Agente criado")
        
        # Fazer pergunta de teste
        question = "Qual é o objetivo do curso de Sistemas de Informação?"
        print(f"❓ Pergunta: {question}")
        
        response = agent.run(question)
        
        print(f"✅ Resposta gerada")
        print(f"📝 Resposta: {response.content[:300]}...")
        
        # Analisar resposta
        if "não encontrei" in response.content.lower() or "não consegui" in response.content.lower():
            print("⚠️ PROBLEMA: Resposta indica que não encontrou informação")
            return False
        else:
            print("✅ Resposta contém informação específica!")
            return True
            
    except Exception as e:
        print(f"❌ Erro na geração: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa investigação completa"""
    
    # Configurar logging para debug
    logging.basicConfig(level=logging.DEBUG)
    
    success = investigate_vectorization()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 INVESTIGAÇÃO CONCLUÍDA - RAG FUNCIONANDO!")
    else:
        print("⚠️ INVESTIGAÇÃO CONCLUÍDA - PROBLEMAS IDENTIFICADOS")
    print("=" * 80)
    
    return success

if __name__ == "__main__":
    main()