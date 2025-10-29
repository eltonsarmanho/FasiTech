"""
Serviço para acessar e processar dados sociais da planilha Google Sheets.
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

from src.services.google_sheets import read_sheet_tab
from src.models.schemas import (
    DadoSocial, 
    DadosSociaisResponse, 
    EstatisticasSociais,
    FiltrosDadosSociais,
    CorEtnia,
    SimNao,
    TipoRenda,
    TipoDeslocamento,
    QualidadeAssistencia,
    FrequenciaSaudeMental,
    FrequenciaEstresse,
    NivelEscolaridade,
    FaixaGastoInternet,
    TipoMoradia
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache simples em memória
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = timedelta(minutes=30)  # Cache por 30 minutos

# ID da planilha social
SOCIAL_SHEET_ID = "1mn9zvNtG-Df_hMCen1M-cWlQl2QtfgFUr0tBg436giE"
SOCIAL_SHEET_TAB = "Pagina1"

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
    def _parse_datetime(date_str: str) -> Optional[datetime]:
        """Parse de string de data/hora."""
        if not date_str or pd.isna(date_str):
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            except ValueError:
                logger.warning(f"Formato de data não reconhecido: {date_str}")
                return None

    @staticmethod
    def _parse_enum_value(value: Any, enum_class) -> Optional[Any]:
        """Parse seguro de valores enum."""
        if pd.isna(value) or not value:
            return None
        try:
            return enum_class(str(value))
        except ValueError:
            logger.warning(f"Valor não reconhecido para {enum_class.__name__}: {value}")
            return None

    @staticmethod
    def _parse_int_value(value: Any) -> Optional[int]:
        """Parse seguro de valores inteiros."""
        if pd.isna(value) or not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"Valor não numérico: {value}")
            return None

    @staticmethod
    @cache_result()
    def _load_raw_data() -> pd.DataFrame:
        """Carrega dados brutos da planilha com cache."""
        try:
            logger.info(f"Carregando dados da planilha {SOCIAL_SHEET_ID}")
            df = read_sheet_tab(SOCIAL_SHEET_ID, SOCIAL_SHEET_TAB)
            
            if df.empty:
                logger.warning("Planilha vazia ou não encontrada")
                return pd.DataFrame()
            
            logger.info(f"Carregados {len(df)} registros da planilha social")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados da planilha: {e}")
            raise Exception(f"Erro ao acessar planilha social: {e}")

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
                trabalho=SocialDataService._parse_enum_value(row.get('Trabalho'), SimNao),
                assistencia_estudantil=SocialDataService._parse_enum_value(row.get('Assistência Estudantil'), QualidadeAssistencia),
                saude_mental=SocialDataService._parse_enum_value(row.get('Saúde Mental'), FrequenciaSaudeMental),
                estresse=SocialDataService._parse_enum_value(row.get('Estresse'), FrequenciaEstresse),
                acompanhamento=str(row.get('Acompanhamento', '')) if pd.notna(row.get('Acompanhamento')) else None,
                escolaridade_pai=SocialDataService._parse_enum_value(row.get('Escolaridade Pai'), NivelEscolaridade),
                escolaridade_mae=SocialDataService._parse_enum_value(row.get('Escolaridade Mãe'), NivelEscolaridade),
                qtd_computador=SocialDataService._parse_int_value(row.get('Qtd Computador')),
                qtd_celular=SocialDataService._parse_int_value(row.get('Qtd Celular')),
                computador_proprio=SocialDataService._parse_enum_value(row.get('Computador Próprio'), SimNao),
                gasto_internet=SocialDataService._parse_enum_value(row.get('Gasto Internet'), FaixaGastoInternet),
                acesso_internet=SocialDataService._parse_enum_value(row.get('Acesso Internet'), SimNao),
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