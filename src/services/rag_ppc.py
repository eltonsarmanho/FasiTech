"""
Serviço RAG (Retrieval-Augmented Generation) para consulta do PPC do curso.
Este serviço permite fazer perguntas sobre o Projeto Pedagógico do Curso usando IA.
"""

from __future__ import annotations
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from agno.models.google import Gemini

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.models.huggingface import HuggingFace
from dotenv import load_dotenv
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PPCChatbotService:
    """Serviço de chatbot para consultas sobre o PPC do curso."""
    
    _instance: Optional['PPCChatbotService'] = None
    _agent: Optional[Agent] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'PPCChatbotService':
        """Implementa padrão Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço (apenas uma vez)."""
        if not self._initialized:
            # Atributos de estado
            self.model: Optional[HuggingFace] = None
            self.embedder: Optional[OllamaEmbedder] = None
            self.vector_db: Optional[LanceDb] = None
            self.knowledge: Optional[Knowledge] = None
            self.db: Optional[SqliteDb] = None
            self._knowledge_loaded: bool = False
            self._initialized_at: Optional[datetime] = None
            self._last_question_at: Optional[datetime] = None
            self._last_latency: Optional[float] = None
            self._total_questions: int = 0
            self._setup_service()
            self._initialized = True
    
    def _setup_service(self) -> None:
        """Configura todos os componentes do serviço RAG baseado no script funcional."""
        logger.info("=== CONFIGURANDO AGENTE RAG ===")
        
        # Carregar variáveis de ambiente
        load_dotenv(override=True)
        
        # Configurar caminhos
        self.db_url = "./data/lancedb"
        self.sqlite_db_path = "./data/ppc_chat.db"
        self.ppc_file_path = Path(__file__).resolve().parents[1] / "resources" / "PPC.pdf"
        
        # Criar diretórios se não existirem
        Path(self.db_url).parent.mkdir(parents=True, exist_ok=True)
        Path(self.sqlite_db_path).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self._setup_model()
            self._initialized_at = datetime.utcnow()
            logger.info("✅ Agente configurado com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar serviço: {e}")
            raise
    
    def _setup_model(self) -> None:
        """Configura o modelo seguindo exatamente o script funcional."""
        print("=== CONFIGURANDO AGENTE RAG ===")
        print("1. Configurando modelo de linguagem...")

        huggingface_api_key = os.getenv("HF_TOKEN")
        # Configurar Gemini com API key do .env
        google_api_key = os.getenv("GOOGLE_API_KEY")
        model = None
        if google_api_key:  
            try:
                print("   Tentando carregar modelo Gemini...")
                model = Gemini(
                    id="gemini-2.5-flash", 
                    api_key=google_api_key,
                )
                print("✅ Modelo Gemini carregado com sucesso!")
            except Exception as e:
                print(f"   ⚠️  Modelo Gemini não disponível: {str(e)[:80]}...")
        if model is None:
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

        self.model = model

        # Create Ollama embedder
        print("2. Configurando embedder...")
        embedder = OllamaEmbedder(
            id="nomic-embed-text", 
            dimensions=768,
        )

        self.embedder = embedder

        # Create the vector database
        print("3. Configurando banco de dados vetorial...")
        vector_db = LanceDb(
            table_name="recipes",
            uri=self.db_url,
            embedder=embedder,
            search_type=SearchType.hybrid,
        )

        self.vector_db = vector_db

        print("4. Configurando base de conhecimento...")
        knowledge = Knowledge(vector_db=vector_db, max_results=25)

        self.knowledge = knowledge

        # Verificar se o banco vetorial já possui dados
        vector_db_path = f"{self.db_url}/recipes.lance"
        has_existing_data = False

        if os.path.exists(vector_db_path):
            print("📚 Verificando se a base de conhecimento possui dados...")
            try:
                # Verificar se há documentos na tabela
                import lancedb
                db = lancedb.connect(self.db_url)
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
                    path=str(self.ppc_file_path)
                )
                print("✅ Conteúdo do PPC.pdf adicionado com sucesso!")
                has_existing_data = True
            except Exception as e:
                print(f"❌ Erro ao carregar PPC.pdf: {e}")
                print("Continuando sem a base de conhecimento...")

        self._knowledge_loaded = has_existing_data

        print("5. Configurando banco de dados SQLite...")
        # Verificar se o banco SQLite já existe
        sqlite_exists = os.path.exists(self.sqlite_db_path)
        if sqlite_exists:
            print("📊 Banco de dados SQLite já existe, reutilizando...")
        else:
            print("📊 Criando novo banco de dados SQLite...")

        db = SqliteDb(db_file=self.sqlite_db_path)

        self.db = db

        print("6. Criando agente...")
        self._agent = Agent(
            session_id="rag_session", 
            user_id="user",  
            model=model,
            knowledge=knowledge,
            db=db,
        )

        print("✅ Agente configurado com sucesso!")
        print("=" * 50)

    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Executa uma pergunta e retorna um payload estruturado para a interface."""
        if not self._agent:
            raise RuntimeError("Agente não inicializado. Chame initialize() primeiro.")

        normalized_question = (question or "").strip()
        if not normalized_question:
            return {
                "success": False,
                "error": "Pergunta vazia. Por favor, digite uma pergunta sobre o PPC.",
            }

        try:
            logger.info("Pergunta recebida: %s", normalized_question[:150])
            start = time.perf_counter()
            response = self._agent.run(normalized_question)
            latency = time.perf_counter() - start

            answer_text = None
            if hasattr(response, "content") and response.content:
                answer_text = response.content
            elif hasattr(response, "output") and response.output:
                answer_text = response.output

            if answer_text is None:
                raise ValueError("O modelo não retornou conteúdo.")

            if isinstance(answer_text, list):
                # Alguns modelos retornam lista de fragmentos
                answer_text = "\n".join(str(part) for part in answer_text if part)

            answer_text = str(answer_text).strip()
            if not answer_text:
                raise ValueError("Resposta vazia gerada pelo modelo.")

            # Atualizar métricas internas
            self._last_question_at = datetime.utcnow()
            self._last_latency = latency
            self._total_questions += 1

            logger.info("Resposta gerada em %.2fs", latency)
            return {
                "success": True,
                "answer": answer_text,
                "method": "agent",
                "latency": latency,
                "question": normalized_question,
            }

        except Exception as exc:
            logger.exception("Erro ao processar pergunta: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }
    
    def get_conversation_history(self, limit: int = 10) -> list:
        """
        Obtém histórico de conversas.
        
        Args:
            limit: Número máximo de mensagens
            
        Returns:
            Lista de mensagens do histórico
        """
        try:
            if not self._agent or not self._agent.memory:
                return []
            
            # Obter histórico do agente
            messages = self._agent.memory.get_messages(limit=limit)
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', None)
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def clear_conversation(self) -> bool:
        """
        Limpa o histórico de conversas.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if self._agent and self._agent.memory:
                self._agent.memory.clear()
                logger.info("Histórico de conversas limpo")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtém status do serviço.
        
        Returns:
            Dict com informações do status
        """
        return {
            "initialized": self._initialized,
            "initialized_at": self._initialized_at.isoformat() if self._initialized_at else None,
            "model_type": type(self.model).__name__ if self.model else None,
            "knowledge_loaded": bool(self._knowledge_loaded),
            "agent_ready": self._agent is not None,
            "db_path": getattr(self, "db_url", None),
            "ppc_file_exists": self.ppc_file_path.exists() if hasattr(self, "ppc_file_path") else False,
            "total_questions": self._total_questions,
            "last_question_at": self._last_question_at.isoformat() if self._last_question_at else None,
            "last_latency": self._last_latency,
        }


# Função para obter a instância singleton do serviço
def get_ppc_service() -> PPCChatbotService:
    """Obtém a instância singleton do serviço PPC."""
    return PPCChatbotService()

