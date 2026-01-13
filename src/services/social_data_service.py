"""
Serviço para acessar e processar dados sociais do banco de dados PostgreSQL.
Inclui cache, paginação, filtros e estatísticas.
"""

from __future__ import annotations

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from functools import wraps
import hashlib
import json
import logging

from sqlmodel import Session, select, text
from src.database.engine import get_db_session, engine
from src.models.db_models import SocialSubmission
from src.models.schemas import (
    DadoSocial, 
    DadosSociaisResponse, 
    EstatisticasSociais,
    FiltrosDadosSociais,
    CorEtnia,
    SimNao,
    TipoRenda,
    TipoDeslocamento,
    TipoTrabalho,
    QualidadeAssistencia,
    FrequenciaSaudeMental,
    FrequenciaEstresse,
    NivelEscolaridade,
    FaixaGastoInternet,
    TipoMoradia,
    AcessoInternet
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache simples em memória
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = timedelta(minutes=30)  # Cache por 30 minutos

# Salt para hash das matrículas (LGPD compliance)
MATRICULA_SALT = "fasitech_lgpd_2025_social_data_hash"


def hash_matricula(matricula: str) -> str:
    """
    Gera hash anônimo da matrícula para conformidade com LGPD.
    
    Args:
        matricula: Matrícula original do estudante
        
    Returns:
        Hash SHA256 da matrícula com salt para anonimização
    """
    if not matricula:
        return ""
    
    # Combinar matrícula com salt e gerar hash
    combined = f"{matricula}_{MATRICULA_SALT}"
    hash_hex = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    # Retornar apenas os primeiros 12 caracteres para identificação única mas anônima
    return f"ANON_{hash_hex[:12].upper()}"


def cache_result(ttl: timedelta = _cache_ttl):
    """Decorator para cache de resultados."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Criar chave do cache
            cache_key = f"{func.__name__}_{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()}"
            
            # Verificar se existe no cache e não expirou
            if cache_key in _cache:
                cached_data = _cache[cache_key]
                if datetime.now() - cached_data['timestamp'] < ttl:
                    logger.info(f"Cache hit para {func.__name__}")
                    return cached_data['data']
            
            # Executar função e armazenar no cache
            result = func(*args, **kwargs)
            _cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            logger.info(f"Cache miss para {func.__name__} - dados armazenados")
            return result
        return wrapper
    return decorator


class SocialDataService:
    """Serviço para gerenciar dados sociais."""

    @staticmethod
    def _parse_datetime(date_value: Any) -> Optional[datetime]:
        """Parse de data/hora - aceita string ou Timestamp."""
        if not date_value or pd.isna(date_value):
            return None
        
        # Se já é um objeto datetime/Timestamp (do pandas), retornar como datetime
        if hasattr(date_value, 'to_pydatetime'):
            return date_value.to_pydatetime()
        elif isinstance(date_value, datetime):
            return date_value
        
        # Se é string, fazer parse
        if isinstance(date_value, str):
            try:
                return datetime.strptime(date_value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    return datetime.strptime(date_value, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    logger.warning(f"Formato de data não reconhecido: {date_value}")
                    return None
        
        logger.warning(f"Tipo de data não reconhecido: {type(date_value)} - {date_value}")
        return None

    @staticmethod
    def _parse_enum_value(value: Any, enum_class) -> Optional[Any]:
        """Parse seguro de valores enum com tratamento de valores especiais."""
        if pd.isna(value) or not value or str(value).lower() in ['null', 'none', '']:
            return None
        
        value_str = str(value).strip()
        
        # Tratamento especial para NULL do banco
        if value_str == 'NULL':
            return None
            
        try:
            return enum_class(value_str)
        except ValueError:
            logger.warning(f"Valor não reconhecido para {enum_class.__name__}: {value_str}")
            return None

    @staticmethod
    def _parse_int_value(value: Any) -> Optional[int]:
        """Parse seguro de valores inteiros."""
        # Se value tiver "Acima de 3", mapear para 3
        if isinstance(value, str) and "Acima de 3" in value:
            return 3
       
        if pd.isna(value) or not value:            
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Valor não numérico: {value}")
            return None

    @staticmethod
    def _parse_gasto_internet(value: Any) -> Optional[FaixaGastoInternet]:
        """Parse especial para gasto de internet - aceita múltiplos formatos."""
        if pd.isna(value) or not value:
            return None
        
        value_str = str(value).strip()
        
        # Tentar direct match com valores do enum
        for enum_value in FaixaGastoInternet:
            if enum_value.value == value_str:
                return enum_value
        
        # Fazer match flexível se o valor veio formatado diferentemente
        try:
            # Tentar encontrar correspondência por padrão
            if "50" in value_str and "150" in value_str:
                return FaixaGastoInternet.DE_50_A_150
            elif "150" in value_str and "200" in value_str:
                return FaixaGastoInternet.DE_150_A_200
            elif "200" in value_str and "Acima" in value_str:
                return FaixaGastoInternet.DE_200_ACIMA
        except Exception as e:
            logger.warning(f"Erro ao fazer parse de gasto_internet: {e}")
        
        return None

    @staticmethod
    @cache_result()
    def _load_raw_data() -> pd.DataFrame:
        """Carrega dados brutos do banco de dados com cache."""
        try:
            logger.info("Carregando dados do banco de dados (social_submissions)")
            
            # Consulta SQL direta no banco de dados
            query = "SELECT * FROM public.social_submissions"
            
            with Session(engine) as session:
                df = pd.read_sql(query, session.connection())
            
            if df.empty:
                logger.warning("Tabela social_submissions vazia")
                return pd.DataFrame()
            
            # Renomear colunas do banco para o formato esperado pelos métodos existentes
            column_mapping = {
                'matricula': 'Matrícula',
                'periodo_referencia': 'Periodo',
                'cor_etnia': 'Cor/Etnia',
                'pcd': 'PCD',
                'tipo_deficiencia': 'Tipo de Deficiência',
                'renda': 'Renda',
                'deslocamento': 'Deslocamento',
                'trabalho': 'Trabalho',
                'assistencia_estudantil': 'Assistência Estudantil',
                'saude_mental': 'Saúde Mental',
                'estresse': 'Estresse',
                'acompanhamento': 'Acompanhamento',
                'escolaridade_pai': 'Escolaridade Pai',
                'escolaridade_mae': 'Escolaridade Mãe',
                'qtd_computador': 'Qtd Computador',
                'qtd_celular': 'Qtd Celular',
                'computador_proprio': 'Computador Próprio',
                'gasto_internet': 'Gasto Internet',
                'acesso_internet': 'Acesso Internet',
                'tipo_moradia': 'Tipo Moradia',
                'submission_date': 'Data/Hora'
            }
            
            df = df.rename(columns=column_mapping)
            
            logger.info(f"Carregados {len(df)} registros do banco de dados")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados do banco de dados: {e}")
            raise Exception(f"Erro ao acessar banco de dados social_submissions: {e}")

    @staticmethod
    def _convert_to_dado_social(row: pd.Series) -> Optional[DadoSocial]:
        """Converte uma linha do DataFrame para o modelo DadoSocial."""
        try:
            # Aplicar hash na matrícula para conformidade com LGPD
            matricula_original = str(row.get('Matrícula', ''))
            matricula_anonima = hash_matricula(matricula_original)
            
            return DadoSocial(
                matricula=matricula_anonima,
                periodo=str(row.get('Periodo', '')),
                cor_etnia=SocialDataService._parse_enum_value(row.get('Cor/Etnia'), CorEtnia),
                pcd=SocialDataService._parse_enum_value(row.get('PCD'), SimNao),
                tipo_deficiencia=str(row.get('Tipo de Deficiência', '')) if pd.notna(row.get('Tipo de Deficiência')) else None,
                renda=SocialDataService._parse_enum_value(row.get('Renda'), TipoRenda),
                deslocamento=SocialDataService._parse_enum_value(row.get('Deslocamento'), TipoDeslocamento),
                trabalho=SocialDataService._parse_enum_value(row.get('Trabalho'), TipoTrabalho),
                assistencia_estudantil=SocialDataService._parse_enum_value(row.get('Assistência Estudantil'), QualidadeAssistencia),
                saude_mental=SocialDataService._parse_enum_value(row.get('Saúde Mental'), FrequenciaSaudeMental),
                estresse=SocialDataService._parse_enum_value(row.get('Estresse'), FrequenciaEstresse),
                acompanhamento=str(row.get('Acompanhamento', '')) if pd.notna(row.get('Acompanhamento')) else None,
                escolaridade_pai=SocialDataService._parse_enum_value(row.get('Escolaridade Pai'), NivelEscolaridade),
                escolaridade_mae=SocialDataService._parse_enum_value(row.get('Escolaridade Mãe'), NivelEscolaridade),
                qtd_computador=SocialDataService._parse_int_value(row.get('Qtd Computador')),
                qtd_celular=SocialDataService._parse_int_value(row.get('Qtd Celular')),
                computador_proprio=SocialDataService._parse_enum_value(row.get('Computador Próprio'), SimNao),
                gasto_internet=SocialDataService._parse_gasto_internet(row.get('Gasto Internet')),
                acesso_internet=SocialDataService._parse_enum_value(row.get('Acesso Internet'), AcessoInternet),
                tipo_moradia=SocialDataService._parse_enum_value(row.get('Tipo Moradia'), TipoMoradia),
                data_hora=SocialDataService._parse_datetime(row.get('Data/Hora'))
            )
        except Exception as e:
            logger.error(f"Erro ao converter linha para DadoSocial: {e}")
            return None

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filtros: FiltrosDadosSociais) -> pd.DataFrame:
        """Aplica filtros aos dados."""
        filtered_df = df.copy()
        
        if filtros.periodo:
            filtered_df = filtered_df[filtered_df['Periodo'] == filtros.periodo]
        
        if filtros.cor_etnia:
            filtered_df = filtered_df[filtered_df['Cor/Etnia'] == filtros.cor_etnia.value]
        
        if filtros.pcd:
            filtered_df = filtered_df[filtered_df['PCD'] == filtros.pcd.value]
        
        if filtros.renda:
            filtered_df = filtered_df[filtered_df['Renda'] == filtros.renda.value]
        
        if filtros.deslocamento:
            filtered_df = filtered_df[filtered_df['Deslocamento'] == filtros.deslocamento.value]
        
        if filtros.trabalho:
            filtered_df = filtered_df[filtered_df['Trabalho'] == filtros.trabalho.value]
        
        if filtros.assistencia_estudantil:
            filtered_df = filtered_df[filtered_df['Assistência Estudantil'] == filtros.assistencia_estudantil.value]
        
        if filtros.tipo_moradia:
            filtered_df = filtered_df[filtered_df['Tipo Moradia'] == filtros.tipo_moradia.value]
        
        return filtered_df

    @staticmethod
    def get_dados_sociais(
        pagina: int = 1,
        por_pagina: int = 20,
        filtros: Optional[FiltrosDadosSociais] = None
    ) -> DadosSociaisResponse:
        """
        Obtém dados sociais com paginação e filtros.
        
        Args:
            pagina: Número da página (base 1)
            por_pagina: Quantidade de registros por página
            filtros: Filtros opcionais
        
        Returns:
            DadosSociaisResponse com dados paginados
        """
        try:
            # Carregar dados brutos
            df = SocialDataService._load_raw_data()
            
            if df.empty:
                return DadosSociaisResponse(
                    dados=[],
                    total=0,
                    pagina=pagina,
                    por_pagina=por_pagina,
                    total_paginas=0
                )
            
            # Aplicar filtros se fornecidos
            if filtros:
                df = SocialDataService._apply_filters(df, filtros)
            
            # Calcular paginação
            total_registros = len(df)
            total_paginas = (total_registros + por_pagina - 1) // por_pagina
            inicio = (pagina - 1) * por_pagina
            fim = inicio + por_pagina
            
            # Obter dados da página atual
            dados_pagina = df.iloc[inicio:fim]
            
            # Converter para modelos Pydantic
            dados_convertidos = []
            for _, row in dados_pagina.iterrows():
                dado = SocialDataService._convert_to_dado_social(row)
                if dado:
                    dados_convertidos.append(dado)
            
            return DadosSociaisResponse(
                dados=dados_convertidos,
                total=total_registros,
                pagina=pagina,
                por_pagina=por_pagina,
                total_paginas=total_paginas
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter dados sociais: {e}")
            raise Exception(f"Erro ao processar dados sociais: {e}")

    @staticmethod
    @cache_result()
    def get_estatisticas() -> EstatisticasSociais:
        """
        Gera estatísticas agregadas dos dados sociais.
        
        Returns:
            EstatisticasSociais com dados estatísticos
        """
        try:
            df = SocialDataService._load_raw_data()
            
            if df.empty:
                return EstatisticasSociais(
                    total_registros=0,
                    distribuicao_cor_etnia={},
                    distribuicao_renda={},
                    percentual_pcd=0.0,
                    percentual_trabalham=0.0,
                    distribuicao_deslocamento={},
                    media_dispositivos={},
                    qualidade_assistencia={}
                )
            
            total_registros = len(df)
            
            # Distribuição por cor/etnia
            dist_cor_etnia = df['Cor/Etnia'].value_counts().to_dict()
            
            # Distribuição por renda
            dist_renda = df['Renda'].value_counts().to_dict()
            
            # Percentual PCD
            pcd_counts = df['PCD'].value_counts()
            percentual_pcd = (pcd_counts.get('Sim', 0) / total_registros * 100) if total_registros > 0 else 0
            
            # Percentual que trabalha
            trabalho_counts = df['Trabalho'].value_counts()
            percentual_trabalham = (trabalho_counts.get('Sim', 0) / total_registros * 100) if total_registros > 0 else 0
            
            # Distribuição por deslocamento
            dist_deslocamento = df['Deslocamento'].value_counts().to_dict()
            
            # Média de dispositivos
            media_dispositivos = {
                'computadores': df['Qtd Computador'].mean() if not df['Qtd Computador'].isna().all() else 0,
                'celulares': df['Qtd Celular'].mean() if not df['Qtd Celular'].isna().all() else 0
            }
            
            # Qualidade da assistência estudantil
            qualidade_assistencia = df['Assistência Estudantil'].value_counts().to_dict()
            
            return EstatisticasSociais(
                total_registros=total_registros,
                distribuicao_cor_etnia=dist_cor_etnia,
                distribuicao_renda=dist_renda,
                percentual_pcd=round(percentual_pcd, 2),
                percentual_trabalham=round(percentual_trabalham, 2),
                distribuicao_deslocamento=dist_deslocamento,
                media_dispositivos=media_dispositivos,
                qualidade_assistencia=qualidade_assistencia
            )
            
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            raise Exception(f"Erro ao gerar estatísticas: {e}")

    @staticmethod
    def clear_cache():
        """Limpa o cache do serviço."""
        global _cache
        _cache.clear()
        logger.info("Cache limpo")

    @staticmethod
    def get_cache_info() -> Dict[str, Any]:
        """Retorna informações sobre o cache."""
        return {
            'total_entries': len(_cache),
            'entries': list(_cache.keys()),
            'ttl_minutes': _cache_ttl.total_seconds() / 60
        }