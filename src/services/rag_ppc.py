"""
Serviço RAG (Retrieval-Augmented Generation) para consulta do PPC do curso.
Este serviço permite fazer perguntas sobre o Projeto Pedagógico do Curso usando IA.
"""

from __future__ import annotations
import os
import shutil
import logging
import hashlib
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta, timezone
from agno.models.google import Gemini

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType
from agno.models.huggingface import HuggingFace
from agno.models.openai import OpenAILike
from agno.knowledge.embedder.google import GeminiEmbedder

from dotenv import load_dotenv
import time
import numpy as np

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do cache semântico
# Apenas entradas "trusted" podem ser servidas para o usuário.
SEMANTIC_CACHE_SIMILARITY_THRESHOLD = 0.90
SEMANTIC_CACHE_TABLE_NAME = "semantic_cache"
SEMANTIC_CACHE_TRUSTED_MIN_AVG_RATING = 4.4
SEMANTIC_CACHE_MIN_RATINGS_FOR_PROMOTION = 2
SEMANTIC_CACHE_TTL_DAYS_TRUSTED = 30
SEMANTIC_CACHE_TTL_DAYS_CANDIDATE = 14


class ChatbotService:
    """Serviço de chatbot para consultas sobre o PPC do curso."""
    
    _instance: Optional['ChatbotService'] = None
    _agent: Optional[Agent] = None
    _initialized: bool = False
    
    def __new__(cls, persist_history: bool = True) -> 'ChatbotService':
        """Implementa padrão Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, persist_history: bool = True):
        """
        Inicializa o serviço (apenas uma vez).
        
        Args:
            persist_history: Se True, armazena histórico de conversas em SQLite.
                           Se False, usa apenas memória RAM (mais rápido, sem persistência).
        """
        if not self._initialized:
            # Atributos de estado
            self.model: Optional[HuggingFace] = None
            self.embedder: Optional[OllamaEmbedder] = None
            self.vector_db: Optional[LanceDb] = None
            self.knowledge: Optional[Knowledge] = None
            self.db: Optional[SqliteDb] = None
            self.persist_history: bool = persist_history
            self._knowledge_loaded: bool = False
            self._initialized_at: Optional[datetime] = None
            self._last_question_at: Optional[datetime] = None
            self._last_latency: Optional[float] = None
            self._total_questions: int = 0
            self._setup_service()
            self._initialized = True
    
    def _find_document_files(self) -> List[Path]:
        """
        Encontra todos os documentos Markdown na pasta resources.
        Usa variável de ambiente RAG_DOCUMENTS_DIR se configurada.
        Suporta detecção automática de ambiente (local vs VM).
        """
        def _list_markdown_files(resource_dir: Path) -> List[Path]:
            """Lista arquivos .md de forma determinística."""
            md_files = list(resource_dir.glob("*.md")) + list(resource_dir.glob("*.MD"))
            return sorted(md_files, key=lambda p: p.name.lower())

        # Prioridade 1: Variável de ambiente configurável (para produção)
        env_dir = os.getenv("RAG_DOCUMENTS_DIR")
        if env_dir and env_dir.strip():
            resource_dir = Path(env_dir.strip())
            if resource_dir.exists():
                md_files = _list_markdown_files(resource_dir)
                if md_files:
                    logger.info(f"✅ Documentos encontrados (via RAG_DOCUMENTS_DIR): {resource_dir}")
                    for md_file in md_files:
                        logger.info(f"   📄 {md_file.name}")
                    return md_files
                else:
                    logger.warning(f"⚠️  RAG_DOCUMENTS_DIR existe mas não contém arquivos .md: {resource_dir}")
        
        # Prioridade 2: Busca padrão em possíveis diretórios
        resource_dirs = [
            Path.cwd() / "src" / "resources",
            Path(__file__).resolve().parents[2] / "src" / "resources",
            Path("/app/src/resources"),  # Container path
            Path("/home/ubuntu/appStreamLit/src/resources"),  # VM path
        ]
        
        for resource_dir in resource_dirs:
            if resource_dir.exists():
                md_files = _list_markdown_files(resource_dir)
                if md_files:
                    logger.info(f"✅ Documentos encontrados em: {resource_dir}")
                    for md_file in md_files:
                        logger.info(f"   📄 {md_file.name}")
                    return md_files
        
        # Fallback: se não encontrar nenhum, usar PPC_Docling.md padrão
        default_path = Path(__file__).resolve().parents[2] / "src" / "resources" / "PPC_Docling.md"
        logger.warning(f"⚠️  Nenhum arquivo .md encontrado. Usando fallback: {default_path}")
        return [default_path]
    
    def _compute_documents_hash(self, document_files: List[Path]) -> str:
        """
        Calcula hash dos documentos para detectar mudanças.
        Hash baseado em: nome do arquivo + tamanho + data de modificação
        """
        hash_data = []
        for doc_file in sorted(document_files, key=lambda x: x.name):
            if doc_file.exists():
                stat = doc_file.stat()
                hash_data.append(f"{doc_file.name}:{stat.st_size}:{stat.st_mtime}")
        
        combined = "|".join(hash_data)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _should_reindex_documents(self, document_files: List[Path], cache_dir: Path) -> bool:
        """
        Verifica se os documentos precisam ser reindexados.
        Retorna True se houver mudanças ou se o hash não existir.
        """
        hash_file = cache_dir / "documents_hash.json"
        current_hash = self._compute_documents_hash(document_files)
        
        if not hash_file.exists():
            logger.info("🔄 Hash de documentos não encontrado. Indexação necessária.")
            return True
        
        try:
            with open(hash_file, 'r') as f:
                cached_data = json.load(f)
                cached_hash = cached_data.get('hash', '')
                
            if cached_hash != current_hash:
                logger.info("🔄 Documentos modificados detectados. Reindexação necessária.")
                return True
            else:
                logger.info("✅ Documentos não modificados. Usando cache existente.")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️  Erro ao ler hash de cache: {e}. Forçando reindexação.")
            return True
    
    def _save_documents_hash(self, document_files: List[Path], cache_dir: Path):
        """Salva o hash atual dos documentos para futuras verificações."""
        hash_file = cache_dir / "documents_hash.json"
        current_hash = self._compute_documents_hash(document_files)
        
        try:
            with open(hash_file, 'w') as f:
                json.dump({
                    'hash': current_hash,
                    'timestamp': datetime.utcnow().isoformat(),
                    'documents': [str(f.name) for f in document_files]
                }, f, indent=2)
            logger.info(f"💾 Hash de documentos salvo: {current_hash[:8]}...")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao salvar hash: {e}")
    
    def _setup_service(self) -> None:
        """Configura todos os componentes do serviço RAG baseado no script funcional."""
        logger.info("=== CONFIGURANDO AGENTE RAG ===")
        
        # Carregar variáveis de ambiente
        load_dotenv(override=True)
        
        # Configurar caminhos - usar diretório de cache ou temp se ./data não tiver permissões
        data_dir = Path.home() / ".cache" / "fasitech" / "rag"
        
        # Criar diretórios com tratamento de erro para permissões
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback para diretório temporário se não tiver permissão
            import tempfile
            data_dir = Path(tempfile.gettempdir()) / "fasitech" / "rag"
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"⚠️  Usando diretório temporário: {data_dir}")
        
        self.db_url = str(data_dir / "lancedb")
        self.sqlite_db_path = str(data_dir / "ppc_chat.db")
        
        # Localizar documentos Markdown
        self.document_files = self._find_document_files()
        
        logger.info(f"📁 Usando diretório de dados: {data_dir}")
        logger.info(f"📄 Documentos encontrados: {[f.name for f in self.document_files]}")
        
        # Criar diretórios se não existirem
        try:
            Path(self.db_url).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.warning(f"⚠️  Não foi possível criar diretório LanceDB: {self.db_url}")
        
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

        # Carregar variáveis de ambiente
        huggingface_api_key = os.getenv("HF_TOKEN")
        # google_api_key = os.getenv("GOOGLE_API_KEY")
        maritaca_api_key = os.getenv("MARITALK_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")
        model = None
        if maritaca_api_key and model is None:
            try:
                print("   Tentando carregar modelo Maritaca...")
                model = OpenAILike(
                        id="sabia-4",
                        name="Maritaca Sabia 4",
                        api_key=maritaca_api_key,
                        base_url="https://chat.maritaca.ai/api",
                        temperature=0 )
                print("✅ Modelo Maritaca carregado com sucesso!")
            except Exception as e:
                model = None
                print(f"   ⚠️  Modelo Maritaca não disponível: {str(e)[:80]}...")
        
        # Se model é nulo usa google model
        if google_api_key and model is None:  
            try:
                print("   Tentando carregar modelo Gemini...")
                model = Gemini(
                    id="gemini-2.5-flash", 
                    api_key=google_api_key,
                )
                print("✅ Modelo Gemini carregado com sucesso!")
            except Exception as e:
                model = None
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
        # O host padrão é localhost:11434, que funciona perfeitamente
        # já que Ollama está rodando no mesmo container
        self.embedder = OllamaEmbedder(
            id="nomic-embed-text", 
            dimensions=768
        )

        #self.embedder = GeminiEmbedder(dimensions=768)

        # Verificar se precisa reindexar documentos usando sistema de hash
        cache_dir = Path(self.db_url).parent
        should_reindex = self._should_reindex_documents(self.document_files, cache_dir)

        vector_db_path = Path(self.db_url) / "recipes.lance"
        has_existing_data = False

        def _cleanup_vector_table_files() -> None:
            """Remove artefatos físicos da tabela recipes para evitar handles corrompidos."""
            if not vector_db_path.exists():
                return
            try:
                if vector_db_path.is_dir():
                    shutil.rmtree(vector_db_path)
                else:
                    vector_db_path.unlink()
                print("🗑️ Tabela vetorial recipes removida para reindexação limpa.")
            except Exception as cleanup_err:
                logger.warning(f"⚠️  Falha ao limpar arquivos da tabela vetorial: {cleanup_err}")

        if should_reindex:
            _cleanup_vector_table_files()

        def _build_vector_components() -> tuple[LanceDb, Knowledge]:
            """Cria componentes vetoriais com handles novos."""
            vector_db_local = LanceDb(
                table_name="recipes",
                uri=self.db_url,
                embedder=self.embedder,
                search_type=SearchType.hybrid,
            )
            knowledge_local = Knowledge(vector_db=vector_db_local, max_results=20)
            return vector_db_local, knowledge_local

        # Create the vector database
        print("3. Configurando banco de dados vetorial...")
        vector_db, knowledge = _build_vector_components()
        self.vector_db = vector_db

        print("4. Configurando base de conhecimento...")
        self.knowledge = knowledge

        if vector_db_path.exists() and not should_reindex:
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
                print("🔄 Detectada possível corrupção da tabela vetorial. Recriando tabela...")
                _cleanup_vector_table_files()
                vector_db, knowledge = _build_vector_components()
                self.vector_db = vector_db
                self.knowledge = knowledge
                has_existing_data = False
        elif should_reindex:
            print("🔄 Documentos modificados ou novos detectados. Reindexação necessária.")
            has_existing_data = False

        if not has_existing_data:
            print("📚 Carregando/Reindexando documentos...")
            print("   Isso pode demorar alguns minutos...")
            
            try:
                # Verificar se pelo menos um arquivo existe
                existing_files = [f for f in self.document_files if f.exists()]
                if not existing_files:
                    raise FileNotFoundError(
                        f"Nenhum documento encontrado nos caminhos: {[str(f) for f in self.document_files]}\n"
                        f"Cwd: {Path.cwd()}\n"
                        f"File module dir: {Path(__file__).resolve().parent}"
                    )
                
                # Adicionando todos os documentos encontrados
                for doc_file in existing_files:
                    self.knowledge.add_content(
                        name=f"{doc_file.stem} Document",
                        path=str(doc_file)
                    )
                    print(f"✅ Documento {doc_file.name} adicionado com sucesso!")
                
                # Salvar hash dos documentos após indexação bem-sucedida
                self._save_documents_hash(existing_files, cache_dir)
                has_existing_data = True
            except FileNotFoundError as fe:
                print(f"❌ ERRO: {fe}")
                logger.error(f"Arquivo PPC não encontrado: {fe}")
                print("⚠️  Continuando sem a base de conhecimento...")
            except Exception as e:
                print(f"❌ Erro ao carregar documentos: {e}")
                logger.error(f"Erro ao carregar documentos: {e}")
                print("⚠️  Continuando sem a base de conhecimento...")

        self._knowledge_loaded = has_existing_data

        # 5. Configurar SQLite apenas se persist_history=True
        db = None
        if self.persist_history:
            print("5. Configurando banco de dados SQLite (histórico persistente)...")
            sqlite_exists = os.path.exists(self.sqlite_db_path)
            if sqlite_exists:
                print("📊 Banco de dados SQLite já existe, reutilizando...")
            else:
                print("📊 Criando novo banco de dados SQLite...")
            db = SqliteDb(db_file=self.sqlite_db_path)
            self.db = db
        else:
            print("5. SQLite desabilitado (persist_history=False). Usando apenas memória RAM.")
            self.db = None

        print("6. Agente será inicializado sob demanda por sessão.")
        self._agent = None  # Removido agente único global

        # 7. Inicializar cache semântico
        print("7. Configurando cache semântico...")
        self._setup_semantic_cache()

        print("✅ Serviço configurado com sucesso!")
        print("=" * 50)

    def _setup_semantic_cache(self) -> None:
        """
        Configura a tabela de cache semântico no LanceDB.
        Armazena perguntas anteriores com seus embeddings e respostas.
        Verifica compatibilidade dos embeddings existentes.
        """
        try:
            import lancedb
            
            self._cache_db = lancedb.connect(self.db_url)
            
            # Verificar se a tabela já existe
            existing_tables = self._cache_db.table_names()
            
            if SEMANTIC_CACHE_TABLE_NAME not in existing_tables:
                # Criar tabela com schema inicial (será criada no primeiro insert)
                logger.info("📦 Tabela de cache semântico será criada no primeiro uso.")
                self._cache_table = None
            else:
                self._cache_table = self._cache_db.open_table(SEMANTIC_CACHE_TABLE_NAME)
                cache_count = self._cache_table.count_rows()
                required_columns = {
                    "question",
                    "answer",
                    "vector",
                    "question_key",
                    "documents_hash",
                    "status",
                    "avg_rating",
                    "rating_count",
                    "confidence_score",
                    "cached_at",
                    "last_feedback_at",
                    "expires_at",
                }
                
                # Verificar schema mínimo esperado para a nova política de cache.
                try:
                    df = self._cache_table.to_pandas()
                    if not required_columns.issubset(set(df.columns)):
                        logger.warning("⚠️ Cache semântico com schema antigo detectado. Recriando tabela...")
                        self._cache_db.drop_table(SEMANTIC_CACHE_TABLE_NAME)
                        self._cache_table = None
                        logger.info("🗑️ Cache semântico antigo removido para migração de schema.")
                        return
                except Exception as schema_err:
                    logger.warning(f"⚠️ Erro ao validar schema do cache: {schema_err}. Recriando...")
                    self._cache_db.drop_table(SEMANTIC_CACHE_TABLE_NAME)
                    self._cache_table = None
                    return

                if cache_count > 0:
                    try:
                        df = self._cache_table.to_pandas()
                        # Verificar compatibilidade dos embeddings (norma deve ser ~1.0 para vetores normalizados)
                        sample_vector = np.array(df.iloc[0]["vector"])
                        norm = np.linalg.norm(sample_vector)
                        
                        # Se a norma não for aproximadamente 1.0, os embeddings são incompatíveis
                        if not np.isclose(norm, 1.0, atol=0.1):
                            logger.warning(f"⚠️ Embeddings do cache são incompatíveis (norma={norm:.4f}). Limpando cache...")
                            self._cache_db.drop_table(SEMANTIC_CACHE_TABLE_NAME)
                            self._cache_table = None
                            logger.info("🗑️ Cache semântico antigo removido. Será recriado com novos embeddings.")
                        else:
                            logger.info(f"✅ Cache semântico carregado com {cache_count} entradas (embeddings compatíveis).")
                    except Exception as check_err:
                        logger.warning(f"⚠️ Erro ao verificar cache: {check_err}. Recriando...")
                        self._cache_db.drop_table(SEMANTIC_CACHE_TABLE_NAME)
                        self._cache_table = None
                else:
                    logger.info(f"✅ Cache semântico carregado (vazio).")
                
        except Exception as e:
            logger.warning(f"⚠️  Erro ao configurar cache semântico: {e}")
            self._cache_db = None
            self._cache_table = None

    def _get_question_embedding(self, question: str) -> Optional[List[float]]:
        """
        Gera embedding para uma pergunta usando o embedder configurado.
        Os embeddings são normalizados para garantir consistência na busca por cosseno.
        """
        try:
            if self.embedder is None:
                return None
            
            # GeminiEmbedder usa método get_embedding
            if hasattr(self.embedder, 'get_embedding'):
                embedding = self.embedder.get_embedding(question)
            elif hasattr(self.embedder, 'embed'):
                embedding = self.embedder.embed(question)
            else:
                logger.warning("Embedder não possui método de embedding conhecido.")
                return None
            
            # Converter para numpy array se necessário
            if hasattr(embedding, 'tolist'):
                embedding = embedding.tolist()
            
            # Normalizar embedding para garantir consistência (norma L2 = 1)
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            
            return embedding_array.tolist()
            
        except Exception as e:
            logger.warning(f"Erro ao gerar embedding: {e}")
            return None

    def _get_current_documents_hash(self) -> str:
        """Retorna hash dos documentos atualmente ativos no serviço."""
        if not hasattr(self, "document_files"):
            return ""
        existing_files = [f for f in self.document_files if f.exists()]
        if not existing_files:
            return ""
        return self._compute_documents_hash(existing_files)

    @staticmethod
    def _normalize_question_for_key(question: str) -> str:
        """Normaliza pergunta para geração de chave estável."""
        return " ".join((question or "").strip().split()).lower()

    @staticmethod
    def _safe_parse_iso_datetime(value: Any) -> Optional[datetime]:
        """Converte string ISO em datetime UTC com tolerância a formatos inválidos."""
        if not value or not isinstance(value, str):
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def _compute_cache_confidence(self, avg_rating: float, rating_count: int) -> float:
        """
        Calcula score de confiança [0,1] combinando qualidade média e volume de avaliações.
        """
        rating_factor = max(0.0, min(1.0, (avg_rating - 1.0) / 4.0))
        volume_factor = max(0.0, min(1.0, rating_count / SEMANTIC_CACHE_MIN_RATINGS_FOR_PROMOTION))
        return round(rating_factor * volume_factor, 4)

    def _compute_cache_status(self, avg_rating: float, rating_count: int, last_rating: int) -> str:
        """
        Determina status da entrada: candidate ou trusted.
        """
        if last_rating <= 2:
            return "candidate"
        if (
            rating_count >= SEMANTIC_CACHE_MIN_RATINGS_FOR_PROMOTION
            and avg_rating >= SEMANTIC_CACHE_TRUSTED_MIN_AVG_RATING
        ):
            return "trusted"
        return "candidate"

    def _build_cache_entry(
        self,
        question: str,
        answer: str,
        question_embedding: List[float],
        rating: int,
        existing_entry: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Monta payload canônico da entrada de cache semântico."""
        now_utc = datetime.now(timezone.utc)
        documents_hash = self._get_current_documents_hash()
        question_key = hashlib.sha256(
            self._normalize_question_for_key(question).encode("utf-8")
        ).hexdigest()

        previous_count = int(existing_entry.get("rating_count", 0)) if existing_entry else 0
        previous_avg = float(existing_entry.get("avg_rating", 0.0)) if existing_entry else 0.0
        new_count = previous_count + 1
        new_avg = ((previous_avg * previous_count) + float(rating)) / new_count if new_count > 0 else float(rating)
        status = self._compute_cache_status(new_avg, new_count, rating)

        ttl_days = (
            SEMANTIC_CACHE_TTL_DAYS_TRUSTED
            if status == "trusted"
            else SEMANTIC_CACHE_TTL_DAYS_CANDIDATE
        )
        expires_at = (now_utc + timedelta(days=ttl_days)).isoformat()

        return {
            "question": question,
            "answer": answer,
            "vector": question_embedding,
            "question_key": question_key,
            "documents_hash": documents_hash,
            "status": status,
            "avg_rating": round(new_avg, 4),
            "rating_count": int(new_count),
            "confidence_score": self._compute_cache_confidence(new_avg, new_count),
            "cached_at": existing_entry.get("cached_at") if existing_entry else now_utc.isoformat(),
            "last_feedback_at": now_utc.isoformat(),
            "expires_at": expires_at,
        }

    def _find_cache_entry_by_question_key(
        self, question_key: str, documents_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Busca entrada exata por chave de pergunta e versão dos documentos.
        """
        try:
            if self._cache_table is None:
                return None

            df = self._cache_table.to_pandas()
            if df.empty:
                return None
            if "question_key" not in df.columns or "documents_hash" not in df.columns:
                return None

            filtered = df[(df["question_key"] == question_key) & (df["documents_hash"] == documents_hash)]
            if filtered.empty:
                return None

            if "last_feedback_at" in filtered.columns:
                filtered = filtered.sort_values(by="last_feedback_at", ascending=False, na_position="last")

            return filtered.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Erro ao buscar entrada por question_key: {e}")
            return None

    def _upsert_cache_entry(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Insere ou atualiza uma entrada de cache usando question_key + documents_hash.
        """
        try:
            if self._cache_db is None:
                return False

            if self._cache_table is None:
                import lancedb

                self._cache_table = self._cache_db.create_table(
                    SEMANTIC_CACHE_TABLE_NAME,
                    data=[cache_entry],
                    mode="overwrite",
                )
                logger.info("📦 Tabela de cache semântico criada.")
                return True

            question_key = str(cache_entry.get("question_key", ""))
            documents_hash = str(cache_entry.get("documents_hash", ""))
            if question_key and documents_hash:
                self._cache_table.delete(
                    f"question_key = '{question_key}' AND documents_hash = '{documents_hash}'"
                )
            self._cache_table.add([cache_entry])
            return True
        except Exception as e:
            logger.warning(f"Erro no upsert do cache: {e}")
            return False

    def _is_cache_entry_serving_eligible(
        self, entry: Dict[str, Any], similarity: float, current_documents_hash: str
    ) -> bool:
        """
        Verifica se a entrada pode ser usada para responder diretamente do cache.
        """
        if similarity < SEMANTIC_CACHE_SIMILARITY_THRESHOLD:
            return False

        if entry.get("status") != "trusted":
            return False

        entry_documents_hash = entry.get("documents_hash", "")
        if not entry_documents_hash or entry_documents_hash != current_documents_hash:
            return False

        expires_at = self._safe_parse_iso_datetime(entry.get("expires_at"))
        if expires_at is None:
            return False
        if expires_at < datetime.now(timezone.utc):
            return False

        return True

    def _search_cache(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Busca no cache por uma pergunta semanticamente similar.
        
        Args:
            question: Pergunta do usuário
            
        Returns:
            Dict com resposta cacheada se similaridade >= threshold, None caso contrário
        """
        try:
            if self._cache_table is None or self._cache_db is None:
                return None
            
            # Gerar embedding da pergunta atual (já normalizado)
            question_embedding = self._get_question_embedding(question)
            if question_embedding is None:
                return None
            
            # Buscar no cache usando similaridade de cosseno
            # metric="cosine" retorna distância de cosseno: distance = 1 - cosine_similarity
            results = self._cache_table.search(question_embedding).metric("cosine").limit(20).to_list()
            
            if not results:
                return None

            current_documents_hash = self._get_current_documents_hash()
            for candidate in results:
                cosine_distance = candidate.get("_distance", 1.0)
                similarity = max(0.0, min(1.0, 1 - cosine_distance))
                logger.info(
                    "🔍 Cache candidate: distância=%.4f, similaridade=%.2f%%, status=%s",
                    cosine_distance,
                    similarity * 100,
                    candidate.get("status", "unknown"),
                )

                if not self._is_cache_entry_serving_eligible(
                    candidate,
                    similarity,
                    current_documents_hash=current_documents_hash,
                ):
                    continue

                logger.info(
                    "🎯 Cache HIT (trusted)! Similaridade: %.2f%% para pergunta: '%s...'",
                    similarity * 100,
                    question[:50],
                )
                return {
                    "answer": candidate.get("answer", ""),
                    "original_question": candidate.get("question", ""),
                    "similarity": similarity,
                    "cached_at": candidate.get("cached_at", ""),
                    "status": candidate.get("status", "candidate"),
                    "avg_rating": float(candidate.get("avg_rating", 0.0) or 0.0),
                    "rating_count": int(candidate.get("rating_count", 0) or 0),
                }

            logger.info(
                "❌ Cache MISS. Nenhuma entrada trusted elegível (threshold: %.0f%%).",
                SEMANTIC_CACHE_SIMILARITY_THRESHOLD * 100,
            )
            return None
                
        except Exception as e:
            logger.warning(f"Erro ao buscar no cache: {e}")
            return None

    def _save_to_cache(self, question: str, answer: str, rating: int) -> bool:
        """
        Registra feedback no cache semântico com política candidate/trusted.
        
        Args:
            question: Pergunta original
            answer: Resposta gerada pelo modelo
            rating: Avaliação de 1 a 5
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            if self._cache_db is None:
                return False

            if rating < 1 or rating > 5:
                logger.warning(f"Avaliação inválida para cache semântico: {rating}")
                return False
            
            # Gerar embedding da pergunta
            question_embedding = self._get_question_embedding(question)
            if question_embedding is None:
                return False

            question_key = hashlib.sha256(
                self._normalize_question_for_key(question).encode("utf-8")
            ).hexdigest()
            documents_hash = self._get_current_documents_hash()
            existing_entry = self._find_cache_entry_by_question_key(question_key, documents_hash)

            cache_entry = self._build_cache_entry(
                question=question,
                answer=answer,
                question_embedding=question_embedding,
                rating=rating,
                existing_entry=existing_entry,
            )

            saved = self._upsert_cache_entry(cache_entry)
            if saved:
                logger.info(
                    "💾 Cache atualizado: status=%s, avg=%.2f, count=%d, pergunta='%s...'",
                    cache_entry["status"],
                    cache_entry["avg_rating"],
                    cache_entry["rating_count"],
                    question[:50],
                )
            return saved
            
        except Exception as e:
            logger.warning(f"Erro ao salvar no cache: {e}")
            return False

    def save_to_semantic_cache(self, question: str, answer: str, rating: Optional[int] = None) -> bool:
        """
        Método público para registrar feedback no cache semântico.
        
        Args:
            question: Pergunta original
            answer: Resposta gerada pelo modelo
            rating: Avaliação do usuário (1-5). Se omitido, assume 5 para compatibilidade.
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        logger.info(f"🔄 Tentando salvar no cache semântico: '{question[:50]}...'")
        
        # Verificar se o cache está habilitado
        if self._cache_db is None:
            logger.warning("⚠️ Cache semântico não está habilitado (_cache_db é None)")
            return False
        
        # Normalizar a pergunta antes de salvar (strip simples)
        normalized_question = (question or "").strip()
        if not normalized_question:
            logger.warning("⚠️ Pergunta vazia após normalização")
            return False

        normalized_answer = (answer or "").strip()
        if not normalized_answer:
            logger.warning("⚠️ Resposta vazia após normalização")
            return False

        try:
            normalized_rating = int(rating) if rating is not None else 5
        except (TypeError, ValueError):
            logger.warning("⚠️ Avaliação inválida recebida para cache: %s", rating)
            return False
        if normalized_rating < 1 or normalized_rating > 5:
            logger.warning("⚠️ Avaliação fora do intervalo permitido (1-5): %s", normalized_rating)
            return False
            
        result = self._save_to_cache(normalized_question, normalized_answer, normalized_rating)
        
        if result:
            logger.info("✅ Feedback registrado no cache semântico com sucesso!")
        else:
            logger.warning("❌ Falha ao registrar feedback no cache semântico")
        
        return result

    def _get_agent(self, session_id: str) -> Agent:
        """
        Cria ou recupera um agente para uma sessão específica.
        """
        if not session_id:
            session_id = "default_session"
        # Agente nao deve inventar informação para o usuario
        # Agente nao deve inventar informação para o usuario    
        prompt_instructions = [
            "Você é um assistente virtual especializado em fornecer informações precisas sobre o Projeto Pedagógico do Curso (PPC) de Sistemas de Informação.",
            "As respostas devem ser baseadas nas informações fornecidas pelo PPC oficial e outros documentos oficiais.",
            "Se nao encontrar informacao especifica, diga claramente que nao encontrou. Não invente informações (Ex: Atvidades Complementares de Graduação (ACG)).",
            "Seja preciso e cite detalhes relevantes do PPC quando possivel."
        ]
        return Agent(
            session_id=session_id, 
            user_id="user",  
            instructions=prompt_instructions,
            model=self.model,
            enable_user_memories=True,
            knowledge=self.knowledge,
            db=self.db,  # Pode ser None se persist_history=False
        )
    
    def _post_process_answer(self, answer_text: str) -> str:
        """
        Pós-processamento da resposta do modelo.
        Remove markdown redundante e normaliza formatação.
        """
        # Remover múltiplas linhas em branco
        import re
        answer_text = re.sub(r'\n{3,}', '\n\n', answer_text)
        
        # Remover espaços extras no início/fim de linhas
        lines = [line.rstrip() for line in answer_text.split('\n')]
        answer_text = '\n'.join(lines)
        
        # Normalizar citações de markdown excessivas
        answer_text = re.sub(r'```markdown\n?(.*?)\n?```', r'\1', answer_text, flags=re.DOTALL)
        
        return answer_text.strip()
    
    def _extract_sources(self, response: Any) -> List[str]:
        """
        Extrai fontes/documentos utilizados na resposta.
        """
        sources = []
        
        # Tentar extrair de diferentes estruturas de resposta
        if hasattr(response, 'documents') and response.documents:
            for doc in response.documents:
                if hasattr(doc, 'name') and doc.name:
                    sources.append(doc.name)
                elif hasattr(doc, 'metadata') and doc.metadata:
                    source = doc.metadata.get('source', doc.metadata.get('name', ''))
                    if source:
                        sources.append(source)
        
        # Remover duplicatas mantendo ordem
        seen = set()
        unique_sources = []
        for source in sources:
            if source not in seen:
                seen.add(source)
                unique_sources.append(source)
        
        return unique_sources
    
    def ask_question(self, question: str, session_id: str = None, stream: bool = False) -> Dict[str, Any]:
        """
        Executa uma pergunta e retorna um payload estruturado para a interface.
        
        Fluxo:
        1. Verifica no cache semântico se há entrada trusted similar e válida
        2. Se encontrar, retorna resposta do cache
        3. Se não encontrar, chama o modelo
        
        Args:
            question: Pergunta do usuário
            session_id: ID da sessão do usuário (obrigatório para isolamento)
            stream: Se True, habilita streaming (futuro suporte)
            
        Returns:
            Dict com resposta, latência, fontes e metadados
        """
        if not self._initialized:
            raise RuntimeError("Serviço não inicializado. Chame initialize() primeiro.")

        normalized_question = (question or "").strip()
        if not normalized_question:
            return {
                "success": False,
                "error": "Pergunta vazia. Por favor, digite uma pergunta sobre o PPC.",
            }

        try:
            logger.info("Pergunta recebida: %s (Session: %s)", normalized_question[:150], session_id)
            start = time.perf_counter()
            
            # 1. Verificar cache semântico primeiro
            cached_result = self._search_cache(normalized_question)
            if cached_result:
                latency = time.perf_counter() - start
                self._last_question_at = datetime.utcnow()
                self._last_latency = latency
                self._total_questions += 1
                
                return {
                    "success": True,
                    "answer": cached_result["answer"],
                    "method": "cache",
                    "latency": latency,
                    "question": normalized_question,
                    "cache_info": {
                        "original_question": cached_result["original_question"],
                        "similarity": cached_result["similarity"],
                        "cached_at": cached_result["cached_at"],
                        "status": cached_result.get("status"),
                        "avg_rating": cached_result.get("avg_rating"),
                        "rating_count": cached_result.get("rating_count"),
                    }
                }
            
            # 2. Cache MISS - Obter agente para a sessão e chamar modelo
            agent = self._get_agent(session_id)
            
            # Executar pergunta no agente
            response = agent.run(normalized_question, stream=stream)
            latency = time.perf_counter() - start

            # Extrair resposta de texto
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

            # Pós-processamento da resposta
            answer_text = self._post_process_answer(answer_text)
            
            # Extrair fontes utilizadas
            sources = self._extract_sources(response)

            # Atualizar métricas internas
            self._last_question_at = datetime.utcnow()
            self._last_latency = latency
            self._total_questions += 1

            logger.info("Resposta gerada em %.2fs (processamento incluído)", latency)
            
            # NOTA: O cache semântico é alimentado pelo feedback do usuário
            # via save_to_semantic_cache(question, answer, rating).
            
            result = {
                "success": True,
                "answer": answer_text,
                "method": "agent",
                "latency": latency,
                "question": normalized_question,
            }
            
            # Adicionar fontes se encontradas
            if sources:
                result["sources"] = sources
                logger.info(f"Fontes utilizadas: {', '.join(sources)}")
            
            return result

        except Exception as exc:
            logger.exception("Erro ao processar pergunta: %s", exc)
            return {
                "success": False,
                "error": str(exc),
            }
    
    def get_conversation_history(self, session_id: str = None, limit: int = 10) -> list:
        """
        Obtém histórico de conversas.
        
        Args:
            session_id: ID da sessão
            limit: Número máximo de mensagens
            
        Returns:
            Lista de mensagens do histórico
        """
        try:
            agent = self._get_agent(session_id)
            if not agent:
                return []
            
            # Tentar obter histórico de diferentes formas (compatibilidade com versões do agno)
            messages = []
            if hasattr(agent, "memory") and agent.memory:
                messages = agent.memory.get_messages(limit=limit)
            elif hasattr(agent, "memory_manager") and agent.memory_manager:
                # Tentar métodos comuns de memory_manager
                if hasattr(agent.memory_manager, "get_messages"):
                    messages = agent.memory_manager.get_messages(limit=limit)
                elif hasattr(agent.memory_manager, "get_history"):
                    messages = agent.memory_manager.get_history(limit=limit)
            elif hasattr(agent, "get_chat_history"):
                messages = agent.get_chat_history()
                # Aplicar limite manualmente se necessário
                if limit and isinstance(messages, list):
                    messages = messages[-limit:]
            
            # Se messages for generator ou iterator, converter para lista
            if not isinstance(messages, list):
                messages = list(messages)

            return [
                {
                    "role": getattr(msg, "role", "unknown"),
                    "content": getattr(msg, "content", str(msg)),
                    "timestamp": getattr(msg, 'timestamp', None)
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def clear_conversation(self, session_id: str = None) -> bool:
        """
        Limpa o histórico de conversas.
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            agent = self._get_agent(session_id)
            if agent:
                if hasattr(agent, "memory") and agent.memory:
                    agent.memory.clear()
                elif hasattr(agent, "memory_manager") and agent.memory_manager:
                     if hasattr(agent.memory_manager, "clear"):
                        agent.memory_manager.clear()
                elif hasattr(agent, "clear_memory"):
                    agent.clear_memory()
                
                logger.info(f"Histórico de conversas limpo para sessão {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return False

    def clear_semantic_cache(self) -> bool:
        """
        Limpa o cache semântico (todas as perguntas/respostas cacheadas).
        
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            if self._cache_db is not None:
                # Dropar e recriar a tabela
                existing_tables = self._cache_db.table_names()
                if SEMANTIC_CACHE_TABLE_NAME in existing_tables:
                    self._cache_db.drop_table(SEMANTIC_CACHE_TABLE_NAME)
                    self._cache_table = None
                    logger.info("🗑️ Cache semântico limpo com sucesso.")
                    return True
            return False
        except Exception as e:
            logger.error(f"Erro ao limpar cache semântico: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache semântico.
        """
        try:
            if self._cache_table is not None:
                count = self._cache_table.count_rows()
                trusted_entries = 0
                candidate_entries = 0
                try:
                    df = self._cache_table.to_pandas()
                    if "status" in df.columns:
                        trusted_entries = int((df["status"] == "trusted").sum())
                        candidate_entries = int((df["status"] == "candidate").sum())
                except Exception:
                    pass
                return {
                    "enabled": True,
                    "entries": count,
                    "trusted_entries": trusted_entries,
                    "candidate_entries": candidate_entries,
                    "similarity_threshold": SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
                }
            return {
                "enabled": self._cache_db is not None,
                "entries": 0,
                "trusted_entries": 0,
                "candidate_entries": 0,
                "similarity_threshold": SEMANTIC_CACHE_SIMILARITY_THRESHOLD,
            }
        except Exception:
            return {"enabled": False, "entries": 0, "trusted_entries": 0, "candidate_entries": 0}

    def get_status(self) -> Dict[str, Any]:
        """
        Obtém status do serviço.
        
        Returns:
            Dict com informações do status e configurações
        """
        cache_stats = self.get_cache_stats()
        return {
            "initialized": self._initialized,
            "initialized_at": self._initialized_at.isoformat() if self._initialized_at else None,
            "model_type": type(self.model).__name__ if self.model else None,
            "knowledge_loaded": bool(self._knowledge_loaded),
            "agent_ready": True, # Sempre pronto sob demanda
            "db_path": getattr(self, "db_url", None),
            "persist_history": self.persist_history,
            "sqlite_enabled": self.db is not None,
            "semantic_cache": cache_stats,
            "max_results": self.knowledge.max_results if self.knowledge else None,
            "document_files": [f.name for f in self.document_files] if hasattr(self, "document_files") else [],
            "documents_exist": any(f.exists() for f in self.document_files) if hasattr(self, "document_files") else False,
            "total_questions": self._total_questions,
            "last_question_at": self._last_question_at.isoformat() if self._last_question_at else None,
            "last_latency": self._last_latency,
            "avg_latency": self._last_latency / max(self._total_questions, 1) if self._last_latency else None,
        }


# Função para obter a instância singleton do serviço
def get_service(persist_history: bool = True) -> ChatbotService:
    """
    Obtém a instância singleton do serviço PPC.
    
    Args:
        persist_history: Se True, mantém histórico em SQLite (padrão).
                        Se False, usa apenas RAM (mais rápido).
    """
    return ChatbotService(persist_history=persist_history)


# Alias para compatibilidade com código legado
PPCChatbotService = ChatbotService
