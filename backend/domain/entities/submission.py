from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class AccSubimissionEntity(BaseModel):
    Nome_Completo: str
    Matricula: int
    Email: EmailStr
    Turma: str
    Polo: str
    Periodo: str

class TCCSubimissionEntity(BaseModel):
    Nome_Completo: str
    Matricula: int
    Email: EmailStr
    Turma: str
    Polo: str
    Periodo: str
    Orientador: str
    TituloTCC: str
    Componente: str # "TCC 1 " | "TCC 2"

class EstagioSubimissionEntity(BaseModel):
    Nome_Completo: str
    Matricula: int
    Email: EmailStr
    Turma: str
    Polo: str
    Periodo: str
    OrientadorSupervisor: str
    Titulo: str
    Componente: str # "Estágio I" | "Estágio II"

class RequerimentoTCCSubimissionEntity(BaseModel):
    Nome_Completo: str
    Matricula: int
    Email: EmailStr
    Orientador: str
    Menbro1: str
    MenbroOutro1: Optional[str]
    Menbro2: str
    MenbroOutro2: Optional[str]
    Menbro3: Optional[str]
    MenbroOutro3: Optional[str]
    Titulo: str
    Resumo: str
    PalavrasChave: str
    DataDefesa: datetime
    Modalidade: str

class PlanoEnsinoSubimissionEntity(BaseModel):
    Docente: str
    Semestre: str

class ProjetoSubimissionEntity(BaseModel):
    Solicitacao: str
    Docente: str
    Parecerista1: str
    Parecerista2: str
    NomeProjeto: str
    CargaHoraria: int
    Edital: str
    Natureza: str
    AnoEdital: int