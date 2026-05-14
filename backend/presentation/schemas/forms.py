from __future__ import annotations
from pydantic import BaseModel, EmailStr
from typing import Optional


class SubmissionResult(BaseModel):
    id: int
    status: str
    message: str
    drive_links: list[str] = []


class AccFormRequest(BaseModel):
    nome: str
    matricula: str
    email: EmailStr
    turma: str
    polo: str
    periodo: str
    semestre: str


class TccFormRequest(BaseModel):
    nome: str
    matricula: str
    email: EmailStr
    turma: str
    polo: str
    periodo: str
    orientador: str
    titulo: str
    componente: str


class EstagioFormRequest(BaseModel):
    nome: str
    matricula: str
    email: EmailStr
    turma: str
    polo: str
    periodo: str
    orientador: str
    titulo: str
    componente: str


class RequerimentoTccFormRequest(BaseModel):
    nome_aluno: str
    matricula: str
    email: EmailStr
    telefone: Optional[str] = None
    turma: str
    orientador: str
    coorientador: Optional[str] = None
    titulo_trabalho: str
    resumo: Optional[str] = None
    palavra_chave: Optional[str] = None
    modalidade: str
    membro_banca1: Optional[str] = None
    membro_banca2: Optional[str] = None
    data_defesa: Optional[str] = None
    horario_defesa: Optional[str] = None
    local_defesa: Optional[str] = None


class SocialFormRequest(BaseModel):
    matricula: str
    periodo_referencia: str
    genero: Optional[str] = None
    polo: Optional[str] = None
    cor_etnia: Optional[str] = None
    pcd: Optional[str] = None
    tipo_deficiencia: Optional[str] = None
    renda: Optional[str] = None
    deslocamento: Optional[str] = None
    trabalho: Optional[str] = None
    assistencia_estudantil: Optional[str] = None
    saude_mental: Optional[str] = None
    estresse: Optional[str] = None
    acompanhamento: Optional[str] = None
    escolaridade_pai: Optional[str] = None
    escolaridade_mae: Optional[str] = None
    qtd_computador: Optional[str] = None
    qtd_celular: Optional[str] = None
    computador_proprio: Optional[str] = None
    gasto_internet: Optional[str] = None
    acesso_internet: Optional[str] = None
    tipo_moradia: Optional[str] = None


class PlanoEnsinoFormRequest(BaseModel):
    professor: str
    disciplina: str
    codigo_disciplina: Optional[str] = None
    periodo_letivo: str
    carga_horaria: Optional[str] = None


class ProjetosFormRequest(BaseModel):
    docente: str
    parecerista1: str
    parecerista2: str
    nome_projeto: str
    carga_horaria: str
    edital: str
    natureza: str
    ano_edital: str
    solicitacao: str


class AvaliacaoGestaoFormRequest(BaseModel):
    q1_transparencia: Optional[str] = None
    q1_valor: Optional[int] = None
    q2_comunicacao: Optional[str] = None
    q2_valor: Optional[int] = None
    q3_acessibilidade: Optional[str] = None
    q3_valor: Optional[int] = None
    q4_inclusao: Optional[str] = None
    q4_valor: Optional[int] = None
    q5_planejamento: Optional[str] = None
    q5_valor: Optional[int] = None
    q6_recursos: Optional[str] = None
    q6_valor: Optional[int] = None
    q7_eficiencia: Optional[str] = None
    q7_valor: Optional[int] = None
    q8_suporte: Optional[str] = None
    q8_valor: Optional[int] = None
    q9_extracurricular: Optional[str] = None
    q9_valor: Optional[int] = None
    q10_melhorias: Optional[str] = None
    q11_outras_questoes: Optional[str] = None


class EmissaoDocumentosFormRequest(BaseModel):
    nome: str
    matricula: str
    email: EmailStr
    tipo_documento: str
    polo: Optional[str] = None
    turma: Optional[str] = None


class ChatRequest(BaseModel):
    mensagem: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    resposta: str
    fontes: list[str] = []


class AlertaRequest(BaseModel):
    titulo: str
    descricao: str
    data_inicio: str
    data_fim: str
    horario_disparo: str
    destination_type: str = "docentes"
    destination_emails: Optional[str] = None
    ativo: bool = True
