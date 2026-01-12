"""Database models for FasiTech forms."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SubmissionBase(SQLModel):
    """Base model for all submissions."""
    
    submission_date: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )
    status: str = Field(default="recebido", max_length=50)
    # recebido, processado, aprovado, rejeitado, em_analise


class TccSubmission(SubmissionBase, table=True):
    """Model for TCC submissions."""
    
    __tablename__ = "tcc_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(max_length=255)
    matricula: str = Field(max_length=50, index=True)
    email: str = Field(max_length=255, index=True)
    turma: str = Field(max_length=50)  # Ano de ingresso
    orientador: str = Field(max_length=255)
    titulo: str = Field(max_length=500)
    componente: str = Field(max_length=50)  # TCC 1 ou TCC 2
    
    # Anexos (armazenados como JSON ou string delimitada)
    anexos: Optional[str] = Field(default=None)  # Links do Google Drive
    drive_folder_id: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "João Silva",
                "matricula": "202312345",
                "email": "joao@ufpa.br",
                "turma": "2027",
                "orientador": "Prof. Dr. Maria Santos",
                "titulo": "Análise de Sistemas de Informação",
                "componente": "TCC 2",
            }
        }


class AccSubmission(SubmissionBase, table=True):
    """Model for ACC (Atividades Complementares Curriculares) submissions."""
    
    __tablename__ = "acc_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(max_length=255)
    matricula: str = Field(max_length=50, index=True)
    email: str = Field(max_length=255, index=True)
    turma: str = Field(max_length=50)
    semestre: str = Field(max_length=50)
    
    # Informações do arquivo PDF
    arquivo_pdf_link: Optional[str] = Field(default=None)
    drive_file_id: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Maria Oliveira",
                "matricula": "202298765",
                "email": "maria@ufpa.br",
                "turma": "2026",
                "semestre": "2025.1",
            }
        }


class ProjetosSubmission(SubmissionBase, table=True):
    """Model for Projetos (Projects) submissions."""
    
    __tablename__ = "projetos_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    docente: str = Field(max_length=255, index=True)
    parecerista1: str = Field(max_length=255)
    parecerista2: str = Field(max_length=255)
    nome_projeto: str = Field(max_length=500)
    carga_horaria: str = Field(max_length=50)
    edital: str = Field(max_length=255)
    natureza: str = Field(max_length=100)
    ano_edital: str = Field(max_length=10)
    solicitacao: str = Field(max_length=50)  # Novo, Encerramento, Renovação
    
    # Anexos e PDFs gerados
    anexos: Optional[str] = Field(default=None)
    pdf_parecer: Optional[str] = Field(default=None, max_length=500)
    pdf_declaracao: Optional[str] = Field(default=None, max_length=500)
    drive_folder_id: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "docente": "Prof. Dr. João Santos",
                "parecerista1": "Prof. Dr. Ana Costa",
                "parecerista2": "Prof. Dr. Carlos Lima",
                "nome_projeto": "Desenvolvimento de Sistema Web",
                "carga_horaria": "20 horas",
                "edital": "PIBIC 2025",
                "natureza": "Pesquisa",
                "ano_edital": "2025",
                "solicitacao": "Novo",
            }
        }


class PlanoEnsinoSubmission(SubmissionBase, table=True):
    """Model for Plano de Ensino submissions."""
    
    __tablename__ = "plano_ensino_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    professor: str = Field(max_length=255, index=True)
    disciplina: str = Field(max_length=255)
    codigo_disciplina: Optional[str] = Field(default=None, max_length=50)
    periodo_letivo: str = Field(max_length=50)
    carga_horaria: Optional[str] = Field(default=None, max_length=50)
    
    # Anexos
    anexos: Optional[str] = Field(default=None)
    drive_folder_id: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "professor": "Prof. Dr. Pedro Alves",
                "disciplina": "Banco de Dados",
                "codigo_disciplina": "SI101",
                "periodo_letivo": "2025.1",
                "carga_horaria": "60 horas",
            }
        }


class EstagioSubmission(SubmissionBase, table=True):
    """Model for Estágio submissions."""
    
    __tablename__ = "estagio_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str = Field(max_length=255)
    matricula: str = Field(max_length=50, index=True)
    email: str = Field(max_length=255, index=True)
    turma: str = Field(max_length=50)
    orientador: str = Field(max_length=255)
    titulo: str = Field(max_length=500)
    componente: str = Field(max_length=100)  # Plano de Estágio ou Relatório Final
    
    # Anexos
    anexos: Optional[str] = Field(default=None)
    drive_folder_id: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome": "Lucas Ferreira",
                "matricula": "202187654",
                "email": "lucas@ufpa.br",
                "turma": "2025",
                "orientador": "Prof. Dra. Fernanda Costa",
                "titulo": "Desenvolvimento de Aplicações Web",
                "componente": "Relatório Final",
            }
        }


class SocialSubmission(SubmissionBase, table=True):
    """Model for Social/Academic/Health form submissions."""
    
    __tablename__ = "social_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    matricula: str = Field(max_length=50, index=True)
    periodo_referencia: str = Field(max_length=50)
    
    # Dados demográficos
    cor_etnia: Optional[str] = Field(default=None, max_length=100)
    pcd: Optional[str] = Field(default=None, max_length=50)
    tipo_deficiencia: Optional[str] = Field(default=None, max_length=255)
    
    # Dados socioeconômicos
    renda: Optional[str] = Field(default=None, max_length=100)
    deslocamento: Optional[str] = Field(default=None, max_length=100)
    trabalho: Optional[str] = Field(default=None, max_length=100)
    assistencia_estudantil: Optional[str] = Field(default=None, max_length=100)
    
    # Saúde mental
    saude_mental: Optional[str] = Field(default=None, max_length=100)
    estresse: Optional[str] = Field(default=None, max_length=100)
    acompanhamento: Optional[str] = Field(default=None, max_length=100)
    
    # Dados familiares
    escolaridade_pai: Optional[str] = Field(default=None, max_length=100)
    escolaridade_mae: Optional[str] = Field(default=None, max_length=100)
    
    # Recursos tecnológicos
    qtd_computador: Optional[str] = Field(default=None, max_length=50)
    qtd_celular: Optional[str] = Field(default=None, max_length=50)
    computador_proprio: Optional[str] = Field(default=None, max_length=50)
    gasto_internet: Optional[str] = Field(default=None, max_length=100)
    acesso_internet: Optional[str] = Field(default=None, max_length=100)
    tipo_moradia: Optional[str] = Field(default=None, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "matricula": "202276543",
                "periodo_referencia": "2025.(1 e 2)",
                "cor_etnia": "Pardo",
                "pcd": "Não",
            }
        }


class RequerimentoTccSubmission(SubmissionBase, table=True):
    """Model for Requerimento TCC (defesa) submissions."""
    
    __tablename__ = "requerimento_tcc_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nome_aluno: str = Field(max_length=255)
    matricula: str = Field(max_length=50, index=True)
    email: str = Field(max_length=255, index=True)
    telefone: Optional[str] = Field(default=None, max_length=50)
    turma: str = Field(max_length=50)
    orientador: str = Field(max_length=255)
    coorientador: Optional[str] = Field(default=None, max_length=255)
    
    # Trabalho
    titulo_trabalho: str = Field(max_length=500)
    modalidade: str = Field(max_length=255)
    
    # Banca
    membro_banca1: Optional[str] = Field(default=None, max_length=255)
    membro_banca2: Optional[str] = Field(default=None, max_length=255)
    
    # Defesa
    data_defesa: Optional[str] = Field(default=None, max_length=50)
    horario_defesa: Optional[str] = Field(default=None, max_length=50)
    local_defesa: Optional[str] = Field(default=None, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "nome_aluno": "João Silva",
                "matricula": "202312345",
                "email": "joao@ufpa.br",
                "turma": "2027",
                "orientador": "Prof. Dr. Maria Santos",
                "titulo_trabalho": "Análise de Sistemas",
                "modalidade": "Monografia",
            }
        }


class AvaliacaoGestaoSubmission(SubmissionBase, table=True):
    """Model for Avaliação da Gestão FASI submissions."""
    
    __tablename__ = "avaliacao_gestao_submissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Perguntas de satisfação/concordância (texto e valor numérico)
    q1_transparencia: Optional[str] = Field(default=None, max_length=100)
    q1_valor: Optional[int] = Field(default=None)
    
    q2_comunicacao: Optional[str] = Field(default=None, max_length=100)
    q2_valor: Optional[int] = Field(default=None)
    
    q3_acessibilidade: Optional[str] = Field(default=None, max_length=100)
    q3_valor: Optional[int] = Field(default=None)
    
    q4_inclusao: Optional[str] = Field(default=None, max_length=100)
    q4_valor: Optional[int] = Field(default=None)
    
    q5_planejamento: Optional[str] = Field(default=None, max_length=100)
    q5_valor: Optional[int] = Field(default=None)
    
    q6_recursos: Optional[str] = Field(default=None, max_length=100)
    q6_valor: Optional[int] = Field(default=None)
    
    q7_eficiencia: Optional[str] = Field(default=None, max_length=100)
    q7_valor: Optional[int] = Field(default=None)
    
    q8_suporte: Optional[str] = Field(default=None, max_length=100)
    q8_valor: Optional[int] = Field(default=None)
    
    q9_extracurricular: Optional[str] = Field(default=None, max_length=100)
    q9_valor: Optional[int] = Field(default=None)
    
    # Perguntas abertas
    q10_melhorias: Optional[str] = Field(default=None)
    q11_outras_questoes: Optional[str] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "q1_transparencia": "Satisfeito",
                "q1_valor": 4,
                "q2_comunicacao": "Concordo",
                "q2_valor": 4,
            }
        }
