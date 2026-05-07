from pydantic import BaseModel
from typing import Optional

class FormularioSocioeconomicoEntipy(BaseModel):
    Matricula: str
    Genero: str
    Polo: str
    CorEtnia: str
    PCD: str
    TipoPDC: Optional[str]
    RendaFamiliar: str
    Deslocamento: str
    Trabalho: str
    AssistenciaEstudantil: str
    SaudeMental: str
    Estresse: str
    Acompanhamento: str
    EscolaridadePai: str
    EscolaridadeMae: str
    QtdComputador: str
    QtdCelular: str
    ComputadorProprio: str
    GastoInternet: str
    AcessoInternet: str
    TipoMoradia: str
