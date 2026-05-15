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
from backend.config.LLMConfig import GEMINI_MODEL, OLLAMA_LLM_MODEL
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

# Similaridade mínima (cosseno) para considerar a pergunta dentro do domínio dos documentos.
# Aplicada quando a pergunta já contém pelo menos uma palavra-chave acadêmica.
MIN_DOMAIN_RELEVANCE_THRESHOLD = 0.50
# Limiar mais estrito aplicado quando a pergunta NÃO contém nenhuma palavra-chave do domínio.
# Evita que perguntas genéricas em português (ex: "Qual a capital do Brasil?") passem pela
# semelhança superficial de idioma.
MIN_DOMAIN_RELEVANCE_NO_KEYWORD_THRESHOLD = 0.72

# Palavras-chave que sinalizam que a pergunta pertence ao domínio acadêmico.
# Basta UMA palavra-chave para aplicar o limiar padrão (mais permissivo).
_DOMAIN_KEYWORDS: frozenset = frozenset({
    "disciplina", "matéria", "componente", "ementa", "ementário",
    "curso", "grade", "currículo", "ppc", "projeto pedagógico",
    "tcc", "trabalho de conclusão", "monografia",
    "acc", "acg", "atividade complementar",
    "matrícula", "inscrição", "trancamento", "cancelamento",
    "professor", "docente", "orientador", "coordenador",
    "carga horária", "crédito", "horas", "semestre", "período",
    "formatura", "colação", "diploma", "certificado",
    "estágio", "supervisão",
    "regulamento", "regimento", "resolução", "norma",
    "aprovação", "reprovação", "nota", "média", "frequência", "presença",
    "fasi", "ufpa", "universidade", "faculdade",
    "sistemas de informação", "computação", "informática",
    "extensão", "pesquisa", "ensino",
    "coordenação", "colegiado", "câmara",
    "obrigatória", "optativa", "eletiva",
    "pré-requisito", "prerequisito",
    "avaliação", "prova", "trabalho",
    "bolsa", "auxílio", "monitoria",
    "coleta", "histórico", "boletim",
    "faq", "dúvida", "pergunta frequente",
})


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
            Path.cwd() / "resources",
            Path(__file__).resolve().parents[3] / "resources",
            Path("/app/resources"),  # Container path
        ]
        
        for resource_dir in resource_dirs:
            if resource_dir.exists():
                md_files = _list_markdown_files(resource_dir)
                if md_files:
                    logger.info(f"✅ Documentos encontrados em: {resource_dir}")
                    for md_file in md_files:
                        logger.info(f"   📄 {md_file.name}")
                    return md_files
        
        # Fallback: nenhum documento encontrado
        logger.warning("⚠️  Nenhum arquivo .md encontrado. Configure RAG_DOCUMENTS_DIR corretamente.")
        return []
    
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

        google_api_key = os.getenv("GOOGLE_API_KEY")

        if google_api_key:
            print(f"   Usando Gemini: {GEMINI_MODEL}")
            self.model = Gemini(id=GEMINI_MODEL, api_key=google_api_key)
            print(f"✅ Modelo Gemini '{GEMINI_MODEL}' configurado com sucesso!")
        else:
            from agno.models.ollama import Ollama
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            ollama_model = OLLAMA_LLM_MODEL
            print(f"   Usando Ollama local: {ollama_model} (host: {ollama_host})")
            self.model = Ollama(id=ollama_model, host=ollama_host)
            print(f"✅ Modelo Ollama '{ollama_model}' configurado com sucesso!")

        # Create Ollama embedder
        print("2. Configurando embedder...")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.embedder = OllamaEmbedder(
            id="nomic-embed-text",
            dimensions=768,
            host=ollama_host,
        )
        print(f"✅ OllamaEmbedder configurado (host: {ollama_host})")

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
            knowledge_local = Knowledge(vector_db=vector_db_local, max_results=15)
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
                existing_files = [f for f in self.document_files if f.exists()]
                if not existing_files:
                    raise FileNotFoundError(
                        f"Nenhum documento encontrado nos caminhos: {[str(f) for f in self.document_files]}\n"
                        f"Cwd: {Path.cwd()}\nFile module dir: {Path(__file__).resolve().parent}"
                    )

                self._index_documents_fine_grained(existing_files)
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

            if not embedding:
                return None

            # Normalizar embedding para garantir consistência (norma L2 = 1)
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm

            result = embedding_array.tolist()
            return result if result else None
            
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
            if not question_embedding:
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
            "Se nao encontrar informacao especifica, diga claramente que nao encontrou. Não invente informações (Ex: Atividades Complementares de Graduação (ACG)).",
            "Seja preciso e cite detalhes relevantes do PPC quando possivel.",
            "IMPORTANTE: Responda APENAS perguntas relacionadas ao curso de Sistemas de Informação, PPC, TCC, ACC/ACG, estágio, regulamentos, regimento interno, grade curricular e demais documentos acadêmicos oficiais disponíveis. "
            "Se a pergunta for claramente fora desse escopo (ex: curiosidades gerais, geografia, ciências, cultura popular, entretenimento), recuse educadamente dizendo que só pode responder sobre os documentos acadêmicos do curso.",
        ]
        # knowledge é omitido propositalmente: usamos RAG manual (_retrieve_context)
        # para evitar dependência de tool-calling, que varia por modelo.
        return Agent(
            session_id=session_id,
            user_id="user",
            instructions=prompt_instructions,
            model=self.model,
            db=self.db,
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

    @staticmethod
    def _split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
        """Divide texto em chunks sobrepostos respeitando quebras de parágrafo."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current = ""
        for para in paragraphs:
            # Parágrafo maior que chunk_size vira chunks individuais por frase
            if len(para) > chunk_size:
                sentences = para.replace(". ", ".\n").split("\n")
                for sent in sentences:
                    if len(current) + len(sent) + 2 > chunk_size and current:
                        chunks.append(current.strip())
                        current = current[-overlap:] + " " + sent
                    else:
                        current = (current + " " + sent).strip() if current else sent
            else:
                if len(current) + len(para) + 2 > chunk_size and current:
                    chunks.append(current.strip())
                    current = current[-overlap:] + "\n\n" + para
                else:
                    current = (current + "\n\n" + para).strip() if current else para
        if current.strip():
            chunks.append(current.strip())
        return [c for c in chunks if len(c) > 50]

    def _index_documents_fine_grained(
        self,
        files: List[Path],
        chunk_size: int = 800,
        overlap: int = 150,
    ) -> None:
        """Indexa documentos com chunking fino (800 chars / 150 overlap) direto no LanceDB."""
        import lancedb
        import uuid

        db = lancedb.connect(self.db_url)

        # Garante que a tabela existe com o esquema correto
        try:
            table = db.open_table("recipes")
        except Exception:
            table = None

        all_rows: List[dict] = []

        for doc_file in files:
            doc_name = f"{doc_file.stem} Document"
            text = doc_file.read_text(encoding="utf-8", errors="ignore")
            chunks = self._split_into_chunks(text, chunk_size, overlap)
            print(f"   📄 {doc_file.name}: {len(chunks)} chunks (chunk_size={chunk_size})")

            for i, chunk in enumerate(chunks):
                embedding = self._get_question_embedding(chunk)
                if not embedding:
                    continue
                # Normalizar
                arr = np.array(embedding, dtype=np.float32)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm

                payload = json.dumps({
                    "name": doc_name,
                    "meta_data": {"chunk": i + 1, "chunk_size": len(chunk), "source": doc_file.name},
                    "content": chunk,
                }, ensure_ascii=False)

                all_rows.append({
                    "vector": arr.tolist(),
                    "id": str(uuid.uuid4()),
                    "payload": payload,
                })

        if not all_rows:
            raise ValueError("Nenhum chunk gerado — verifique os documentos.")

        if table is not None:
            table.add(all_rows)
        else:
            import pyarrow as pa
            schema = pa.schema([
                pa.field("vector", pa.list_(pa.float32(), list_size=768)),
                pa.field("id", pa.string()),
                pa.field("payload", pa.string()),
            ])
            db.create_table("recipes", data=all_rows, schema=schema)

        total = len(all_rows)
        print(f"✅ Reindexação concluída: {total} chunks inseridos no LanceDB.")

    # Siglas do domínio → termos completos para expansão de query
    _ACRONYM_MAP: Dict[str, str] = {
        "ACC":  "Atividade Curricular Complementar atividades complementares ACG extracurricular",
        "ACG":  "Atividade Curricular Complementar atividades complementares ACC extracurricular",
        "TCC":  "Trabalho de Conclusão de Curso monografia",
        "PPC":  "Projeto Pedagógico do Curso currículo",
        "TCC":  "Trabalho de Conclusão de Curso monografia pesquisa científica",
        "UFPA": "Universidade Federal do Pará",
        "FASI": "Faculdade de Sistemas de Informação",
        "CH":   "carga horária horas",
        "SI":   "Sistemas de Informação",
    }

    def _expand_query(self, question: str) -> str:
        """Adiciona termos completos ao lado das siglas para melhorar a recuperação."""
        expanded = question
        q_upper = question.upper()
        for acronym, expansion in self._ACRONYM_MAP.items():
            if acronym in q_upper:
                expanded = f"{expanded} {expansion}"
        return expanded

    _PT_STOP_WORDS = {
        "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "ao", "aos", "às", "um", "uma", "uns", "umas", "que", "ou", "por",
        "para", "com", "sem", "sua", "seu", "ele", "ela", "não", "mas",
        "são", "como", "ser", "ter", "foi", "tem", "mais", "qual", "quais",
        "sobre", "entre", "quando", "onde", "isso", "esta", "esse", "este",
    }

    def _keyword_search(self, question: str, table, top_k: int = 5) -> List[str]:
        """Busca por palavras-chave no payload como complemento ao semântico."""
        try:
            expanded = self._expand_query(question)
            raw_words = [w.strip(".,?!:;()[]").lower() for w in expanded.split()]
            keywords = [
                w for w in raw_words
                if len(w) >= 3 and w not in self._PT_STOP_WORDS
            ]
            df = table.to_pandas()
            scored: List[tuple[int, str]] = []
            for _, row in df.iterrows():
                p = json.loads(row["payload"]) if isinstance(row["payload"], str) else row["payload"]
                content = p.get("content", "")
                content_lower = content.lower()
                score = sum(1 for kw in keywords if kw in content_lower)
                if score > 0:
                    scored.append((score, content))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [c for _, c in scored[:top_k]]
        except Exception:
            return []

    def _retrieve_context(self, question: str, top_k: int = 10) -> List[str]:
        """Busca semântica + keyword, com expansão de siglas académicas."""
        try:
            if not self._knowledge_loaded or self.vector_db is None:
                return []

            expanded_question = self._expand_query(question)
            question_embedding = self._get_question_embedding(expanded_question)
            if not question_embedding:
                return []

            import lancedb
            db = lancedb.connect(self.db_url)
            table = db.open_table("recipes")

            # Busca semântica
            semantic_results = []
            for kwargs in [{"metric": "cosine"}, {}]:
                try:
                    search = table.search(question_embedding)
                    if "metric" in kwargs:
                        search = search.metric(kwargs["metric"])
                    semantic_results = search.limit(top_k).to_list()
                    break
                except Exception:
                    continue

            # Extrair conteúdo dos resultados semânticos
            seen: set = set()
            chunks: List[str] = []

            def _extract(r: dict) -> str:
                content = r.get("content") or r.get("text") or ""
                if not content:
                    payload = r.get("payload")
                    p = json.loads(payload) if isinstance(payload, str) else (payload or {})
                    content = p.get("content", "")
                return content.strip()

            for r in semantic_results:
                c = _extract(r)
                if c and c not in seen:
                    seen.add(c)
                    chunks.append(c)

            # Sempre complementar com keyword search (os melhores vão para o início)
            keyword_chunks = self._keyword_search(question, table, top_k=5)
            keyword_new = [c for c in keyword_chunks if c and c not in seen]
            # Inserir keyword chunks no início para priorizar correspondências exatas
            for c in reversed(keyword_new):
                seen.add(c)
                chunks.insert(0, c)

            return chunks[:top_k + 5]
        except Exception as e:
            logger.warning("⚠️ Erro ao recuperar contexto: %s", e)
            return []

    @staticmethod
    def _question_has_domain_keyword(question: str) -> bool:
        """Retorna True se a pergunta contiver ao menos uma palavra-chave do domínio acadêmico."""
        q_lower = question.lower()
        return any(kw in q_lower for kw in _DOMAIN_KEYWORDS)

    def _is_question_in_domain(self, question: str) -> tuple[bool, float]:
        """
        Verifica se a pergunta é relevante para o domínio dos documentos carregados.

        Estratégia em duas camadas:
        1. Detecção de palavras-chave acadêmicas → ajusta limiar (permissivo ou estrito).
        2. Busca vetorial na tabela recipes → calcula score combinado (melhor + média dos top-3).

        O score combinado precisa superar o limiar correspondente ao tipo de pergunta.
        Em caso de falha técnica, loga o erro explicitamente e permite a passagem.
        """
        try:
            if not self._knowledge_loaded or self.vector_db is None or self.embedder is None:
                logger.warning(
                    "⚠️ Verificação de domínio ignorada: serviço não está totalmente inicializado."
                )
                return True, 1.0

            # --- Camada 1: palavras-chave -----------------------------------------
            has_keyword = self._question_has_domain_keyword(question)
            effective_threshold = (
                MIN_DOMAIN_RELEVANCE_THRESHOLD
                if has_keyword
                else MIN_DOMAIN_RELEVANCE_NO_KEYWORD_THRESHOLD
            )
            logger.info(
                "🔑 Palavras-chave do domínio: %s → limiar efetivo=%.0f%%",
                "SIM" if has_keyword else "NÃO",
                effective_threshold * 100,
            )

            # --- Camada 2: busca vetorial -----------------------------------------
            question_embedding = self._get_question_embedding(question)
            if not question_embedding:
                logger.warning("⚠️ Embedding não gerado. Verificação de domínio ignorada.")
                return True, 1.0

            import lancedb

            try:
                db = lancedb.connect(self.db_url)
            except Exception as e:
                logger.error("❌ Falha ao conectar no LanceDB para verificação de domínio: %s", e)
                return True, 1.0

            try:
                table = db.open_table("recipes")
            except Exception as e:
                logger.error("❌ Tabela 'recipes' não encontrada para verificação de domínio: %s", e)
                return True, 1.0

            # Tenta cosine primeiro; tabelas hybrid podem não suportar override de métrica
            results = None
            for attempt, kwargs in enumerate([
                {"metric": "cosine"},
                {},  # fallback: métrica padrão da tabela
            ]):
                try:
                    search = table.search(question_embedding)
                    if "metric" in kwargs:
                        search = search.metric(kwargs["metric"])
                    results = search.limit(5).to_list()
                    logger.debug(
                        "Busca vetorial (tentativa %d, metric=%s) retornou %d resultados.",
                        attempt + 1,
                        kwargs.get("metric", "default"),
                        len(results),
                    )
                    break
                except Exception as e:
                    logger.warning(
                        "⚠️ Busca vetorial (tentativa %d, metric=%s) falhou: %s",
                        attempt + 1,
                        kwargs.get("metric", "default"),
                        e,
                    )

            if results is None:
                logger.error("❌ Todas as tentativas de busca vetorial falharam. Pergunta permitida por padrão.")
                return True, 1.0

            if not results:
                logger.info("❌ Nenhum chunk retornado. Pergunta considerada fora do domínio.")
                return False, 0.0

            distances = [float(r.get("_distance", 1.0)) for r in results]
            best_distance = min(distances)
            avg_distance = sum(distances[:3]) / min(3, len(distances))

            best_similarity = max(0.0, min(1.0, 1.0 - best_distance))
            avg_similarity = max(0.0, min(1.0, 1.0 - avg_distance))

            # Score combinado: 40% melhor + 60% média (penaliza quando só 1 chunk é bom)
            combined_score = best_similarity * 0.4 + avg_similarity * 0.6
            is_in_domain = combined_score >= effective_threshold

            logger.info(
                "🎯 Domínio: best=%.1f%% avg=%.1f%% combined=%.1f%% threshold=%.0f%% → %s | '%s...'",
                best_similarity * 100,
                avg_similarity * 100,
                combined_score * 100,
                effective_threshold * 100,
                "✅ IN_DOMAIN" if is_in_domain else "🚫 OUT_OF_DOMAIN",
                question[:60],
            )

            return is_in_domain, combined_score

        except Exception as e:
            logger.error("❌ Erro inesperado em _is_question_in_domain: %s", e, exc_info=True)
            return True, 1.0  # Fail-open: não bloquear o serviço por bug interno

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
            
            # 2. Cache MISS - Verificar se a pergunta pertence ao domínio dos documentos
            is_in_domain, domain_similarity = self._is_question_in_domain(normalized_question)
            if not is_in_domain:
                logger.info(
                    "🚫 Pergunta fora do domínio (similaridade=%.2f%%). Recusada: '%s...'",
                    domain_similarity * 100,
                    normalized_question[:60],
                )
                return {
                    "success": False,
                    "error": "out_of_domain",
                    "message": (
                        "Desculpe, só consigo responder perguntas relacionadas aos documentos "
                        "acadêmicos disponíveis, como o PPC, regulamentos, TCC, ACG e FAQ do "
                        "curso de Sistemas de Informação. "
                        "Sua pergunta não parece estar relacionada a esse conteúdo."
                    ),
                    "domain_similarity": domain_similarity,
                    "question": normalized_question,
                }

            # 3. Dentro do domínio - RAG manual: busca chunks + injeção no prompt
            context_chunks = self._retrieve_context(normalized_question)
            context_text = "\n\n---\n\n".join(context_chunks) if context_chunks else ""

            if context_text:
                augmented_prompt = (
                    "Use EXCLUSIVAMENTE os trechos abaixo para responder. "
                    "Se a informação não estiver nos trechos, diga claramente que não encontrou.\n\n"
                    f"TRECHOS DOS DOCUMENTOS:\n{context_text}\n\n"
                    f"PERGUNTA: {normalized_question}"
                )
            else:
                augmented_prompt = (
                    f"Responda com base nos documentos acadêmicos do curso de Sistemas de Informação da FASI/UFPA.\n"
                    f"PERGUNTA: {normalized_question}"
                )

            agent = self._get_agent(session_id)
            response = agent.run(augmented_prompt, stream=stream)
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
                answer_text = "\n".join(str(part) for part in answer_text if part)

            answer_text = str(answer_text).strip()
            if not answer_text:
                raise ValueError("Resposta vazia gerada pelo modelo.")

            answer_text = self._post_process_answer(answer_text)
            sources = []

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
