from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.models.huggingface import HuggingFace

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv(override=True)

# Define the database URL where the vector database will be stored
db_url = "./lancedb"

print("=== CONFIGURANDO AGENTE RAG ===")

# Configure the language model
print("1. Configurando modelo de linguagem...")

huggingface_api_key = os.getenv("HF_TOKEN")
model = None

if not huggingface_api_key:
    print("❌ HF_TOKEN não encontrada no arquivo .env")
    raise RuntimeError("HF_TOKEN não encontrada. Configure a variável de ambiente para usar os modelos HuggingFace.")
else:
    print(f"✅ HF_TOKEN carregada: {huggingface_api_key[:10]}...")
    
    # Lista de modelos para tentar (em ordem de preferência)
    models_to_try = [
        ("meta-llama/Llama-3.1-8B-Instruct:featherless-ai", "Llama 3.1 8B (Novita)"),
        ("meta-llama/Meta-Llama-3-8B-Instruct:featherless-ai", "Meta Llama 3 8B (Featherless)"),
        ("mistralai/Mistral-7B-Instruct-v0.2:featherless-ai", "Mistral 7B (Featherless)"),
        
    ]
    
    for model_id, model_name in models_to_try:
        try:
            print(f"   Tentando carregar {model_name}...")
            hf_kwargs = {"api_key": huggingface_api_key}
            provider_suffix = None

            if ":" in model_id:
                base_model_id, provider_suffix = model_id.split(":", 1)
                hf_kwargs["id"] = base_model_id
            else:
                base_model_id = model_id
                hf_kwargs["id"] = base_model_id

            if provider_suffix:
                existing_client_params = hf_kwargs.get("client_params") or {}
                existing_client_params.update({"provider": provider_suffix})
                hf_kwargs["client_params"] = existing_client_params

            model = HuggingFace(**hf_kwargs)
            print(f"✅ {model_name} carregado com sucesso!")
            break
        except Exception as e:
            print(f"   ⚠️  {model_name} não disponível: {str(e)[:80]}...")
            continue
    if model is None:
        raise RuntimeError(
            "Nenhum modelo HuggingFace pôde ser carregado. Verifique o HF_TOKEN ou o provedor configurado."
        )
  

# Create Ollama embedder
print("2. Configurando embedder...")
embedder = OllamaEmbedder(
    id="nomic-embed-text", 
    dimensions=768,
)

# Create the vector database
print("3. Configurando banco de dados vetorial...")
vector_db = LanceDb(
    table_name="recipes",
    uri=db_url,
    embedder=embedder,
    search_type=SearchType.hybrid,
)

print("4. Configurando base de conhecimento...")
knowledge = Knowledge(vector_db=vector_db, max_results=25)

# Verificar se o banco vetorial já possui dados
vector_db_path = f"{db_url}/recipes.lance"
has_existing_data = False

if os.path.exists(vector_db_path):
    print("📚 Verificando se a base de conhecimento possui dados...")
    try:
        # Verificar se há documentos na tabela
        import lancedb
        db = lancedb.connect(db_url)
        table = db.open_table("recipes")
        doc_count = table.count_rows()
        
        if doc_count > 0:
            print(f"✅ Base de conhecimento encontrada com {doc_count} documentos!")
            has_existing_data = True
        else:
            print("⚠️  Base de conhecimento existe mas está vazia")
            has_existing_data = False
            
    except Exception as e:
        print(f"⚠️  Erro ao verificar dados existentes: {e}")
        print("🔄 Recarregando conteúdo...")
        has_existing_data = False

if not has_existing_data:
    print("📚 Carregando conteúdo do PPC.pdf pela primeira vez...")
    print("   Isso pode demorar alguns minutos...")
    
    try:
        # Adicionando o arquivo PPC.pdf
        knowledge.add_content(
            name="PPC Document",
            path="file/PPC.pdf"
        )
        print("✅ Conteúdo do PPC.pdf adicionado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao carregar PPC.pdf: {e}")
        print("Continuando sem a base de conhecimento...")

print("5. Configurando banco de dados SQLite...")
# Verificar se o banco SQLite já existe
sqlite_exists = os.path.exists("data.db")
if sqlite_exists:
    print("📊 Banco de dados SQLite já existe, reutilizando...")
else:
    print("📊 Criando novo banco de dados SQLite...")

db = SqliteDb(db_file="data.db")

print("6. Criando agente...")
agent = Agent(
    session_id="rag_session", 
    user_id="user",  
    model=model,
    knowledge=knowledge,
    db=db,
)

print("✅ Agente configurado com sucesso!")
print("=" * 50)

response = agent.run(
        "Fale sobre histórico do curso de Sistemas de Informação?",
    )
print(response)
