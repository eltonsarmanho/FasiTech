from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class AccSubmission(BaseModel):
    name: str
    registration: str
    email: EmailStr
    class_group: str
    file_ids: List[str]


# Enums para dados sociais
class CorEtnia(str, Enum):
    BRANCO = "Branco"
    PARDO = "Pardo"
    PRETO = "Preto"
    AMARELO = "Amarelo"
    INDIGENA = "Indígena"
    QUILOMBOLA = "Quilombola"
    NAO_DECLARADO = "Não declarado"


class SimNao(str, Enum):
    SIM = "Sim"
    NAO = "Não"
    PREFIRO_NAO_RESPONDER = "Prefiro não responder"


class TipoTrabalho(str, Enum):
    """Tipos de situação de trabalho dos estudantes."""
    NAO = "Não"
    SIM_ESTAGIO_REMUNERADO = "Sim, estágio remunerado"
    SIM_ESTAGIO_VOLUNTARIO = "Sim, estágio voluntário"
    SIM_CLT_CONCURSO = "Sim, CLT/Concurso"
    SIM_AUTONOMO_INFORMAL = "Sim, autônomo/informal"


class TipoRenda(str, Enum):
    ATE_1_SALARIO = "Até 1 salário mínimo"
    DE_1_A_3_SALARIOS = "1 a 3 salários mínimos"
    DE_3_A_5_SALARIOS = "3 a 5 salários mínimos"
    ACIMA_5_SALARIOS = "Acima de 5 salários mínimos"
    ACIMA_5_A_10_SALARIOS = "Acima de 5 a 10 salários mínimos"


class TipoDeslocamento(str, Enum):
    BICICLETA_A_PE = "Bicicleta/A pé"
    TRANSPORTE_PUBLICO = "Transporte público (ônibus, trem, metrô, etc.)"
    CARRO_MOTO_PROPRIO = "Carro/Moto próprio"
    TRANSPORTE_APP_TAXI = "Transporte por aplicativo/táxi"
    CARONA_FRETADO = "Carona/Fretado"
    OUTRO = "Outro"


class QualidadeAssistencia(str, Enum):
    SIM = "Sim"
    NAO = "Não"


class FrequenciaSaudeMental(str, Enum):
    MUITO_BOA = "Muito boa"
    BOA = "Boa"
    REGULAR = "Regular"
    RUIM = "Ruim"
    MUITO_RUIM = "Muito ruim"
    PREFIRO_NAO_RESPONDER = "Prefiro não responder"


class FrequenciaEstresse(str, Enum):
    SIM_FREQUENTEMENTE = "Sim, frequentemente"
    SIM_MAIOR_PARTE_TEMPO = "Sim, a maior parte do tempo"
    SIM_OCASIONALMENTE = "Sim, ocasionalmente"
    SIM_NO_PASSADO = "Sim, no passado"
    NUNCA = "Nunca"
    NAO = "Não"


class NivelEscolaridade(str, Enum):
    ANALFABETO = "Analfabeto"
    SEM_ESCOLARIDADE = "Sem escolaridade"
    FUNDAMENTAL_INCOMPLETO = "Ensino Fundamental incompleto"
    FUNDAMENTAL_COMPLETO = "Ensino Fundamental completo"
    MEDIO_INCOMPLETO = "Ensino Médio incompleto"
    MEDIO_COMPLETO = "Ensino Médio completo"
    SUPERIOR_INCOMPLETO = "Ensino Superior incompleto"
    SUPERIOR_COMPLETO = "Ensino Superior completo"
    POS_GRADUACAO = "Pós-graduação"
    NAO_SEI_PREFIRO_NAO_RESPONDER = "Não sei/Prefiro não responder"


class FaixaGastoInternet(str, Enum):
    DE_50_A_150 = "Entre R$ 50,00 a R$ 150,00"
    DE_150_A_200 = "Entre R$ 150,00 a R$ 200,00"
    DE_200_ACIMA = "Acima de R$ 200,00"


class TipoMoradia(str, Enum):
    PROPRIA = "Própria"
    ALUGADA = "Alugada"
    CEDIDA = "Cedida"
    FINANCIADA = "Financiada"
    OUTRA = "Outra"
    PREFIRO_NAO_RESPONDER = "Prefiro não responder"


class AcessoInternet(str, Enum):
    SIM = "Sim"
    NAO = "Não"
    AS_VEZES = "Às vezes"
    PREFIRO_NAO_RESPONDER = "Prefiro não responder"


class DadoSocial(BaseModel):
    """Modelo para um registro individual dos dados sociais."""
    matricula: str = Field(..., description="Matrícula do estudante")
    periodo: str = Field(..., description="Período letivo")
    cor_etnia: Optional[CorEtnia] = Field(None, description="Cor/Etnia do estudante")
    pcd: Optional[SimNao] = Field(None, description="Pessoa com deficiência")
    tipo_deficiencia: Optional[str] = Field(None, description="Tipo de deficiência (se aplicável)")
    renda: Optional[TipoRenda] = Field(None, description="Faixa de renda familiar")
    deslocamento: Optional[TipoDeslocamento] = Field(None, description="Meio de deslocamento principal")
    trabalho: Optional[TipoTrabalho] = Field(None, description="Situação de trabalho atual")
    assistencia_estudantil: Optional[QualidadeAssistencia] = Field(None, description="Qualidade da assistência estudantil")
    saude_mental: Optional[FrequenciaSaudeMental] = Field(None, description="Frequência de problemas de saúde mental")
    estresse: Optional[FrequenciaEstresse] = Field(None, description="Frequência de estresse")
    acompanhamento: Optional[str] = Field(None, description="Tipo de acompanhamento psicológico")
    escolaridade_pai: Optional[NivelEscolaridade] = Field(None, description="Escolaridade do pai")
    escolaridade_mae: Optional[NivelEscolaridade] = Field(None, description="Escolaridade da mãe")
    qtd_computador: Optional[int] = Field(None, description="Quantidade de computadores na residência")
    qtd_celular: Optional[int] = Field(None, description="Quantidade de celulares na residência")
    computador_proprio: Optional[SimNao] = Field(None, description="Possui computador próprio")
    gasto_internet: Optional[FaixaGastoInternet] = Field(None, description="Gasto mensal com internet")
    acesso_internet: Optional[AcessoInternet] = Field(None, description="Tem acesso à internet")
    tipo_moradia: Optional[TipoMoradia] = Field(None, description="Tipo de moradia")
    data_hora: Optional[datetime] = Field(None, description="Data e hora do registro")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DadosSociaisResponse(BaseModel):
    """Response para consulta de dados sociais com paginação."""
    dados: List[DadoSocial] = Field(..., description="Lista de dados sociais")
    total: int = Field(..., description="Total de registros")
    pagina: int = Field(..., description="Página atual")
    por_pagina: int = Field(..., description="Registros por página")
    total_paginas: int = Field(..., description="Total de páginas")


class EstatisticasSociais(BaseModel):
    """Estatísticas agregadas dos dados sociais."""
    total_registros: int = Field(..., description="Total de registros")
    distribuicao_cor_etnia: dict = Field(..., description="Distribuição por cor/etnia")
    distribuicao_renda: dict = Field(..., description="Distribuição por faixa de renda")
    percentual_pcd: float = Field(..., description="Percentual de pessoas com deficiência")
    percentual_trabalham: float = Field(..., description="Percentual que trabalha")
    distribuicao_deslocamento: dict = Field(..., description="Distribuição por meio de deslocamento")
    media_dispositivos: dict = Field(..., description="Média de dispositivos por residência")
    qualidade_assistencia: dict = Field(..., description="Avaliação da assistência estudantil")


class FiltrosDadosSociais(BaseModel):
    """Filtros disponíveis para consulta de dados sociais."""
    periodo: Optional[str] = None
    cor_etnia: Optional[CorEtnia] = None
    pcd: Optional[SimNao] = None
    renda: Optional[TipoRenda] = None
    deslocamento: Optional[TipoDeslocamento] = None
    trabalho: Optional[TipoTrabalho] = None
    assistencia_estudantil: Optional[QualidadeAssistencia] = None
    tipo_moradia: Optional[TipoMoradia] = None


Submission = AccSubmission
