"""
Testes de validação do StatusAlunoExtractor com históricos reais.

Cenários cobertos:
  [202016040002] Klebson do Carmo Silva
    - Total Exigido == Total Integralizado (3332h == 3332h)
    - Sem seção de pendentes → deve ser considerado INTEGRALIZADO
    - Nenhuma disciplina MATRICULADO → aluno_matriculado = False

  [202285940010] Milena Lopes Brabo
    - Total Integralizado (3400h) >= Total Exigido (3196h), mas 4 componentes
      obrigatórios pendentes com CH > 0 → NÃO integralizada
    - Nenhuma disciplina MATRICULADO → aluno_matriculado = False

  [202516040022] Henrique Costa Rodrigues
    - Total Integralizado (285h) << Total Exigido (2855h) → NÃO integralizado
    - Tem ao menos uma disciplina com situação MATRICULADO → aluno_matriculado = True
"""

from pathlib import Path

import pytest

from backend.infrastructure.documents.status_extractor import StatusAlunoExtractor

DIR = Path(__file__).parent

PDF_KLEBSON  = DIR / "historico_202016040002.pdf"   # integralizado, sem MATRICULADO
PDF_MILENA   = DIR / "historico_202285940010.pdf"   # pendentes, sem MATRICULADO
PDF_HENRIQUE = DIR / "historico_202516040022.pdf"   # ativo (MATRICULADO), não integralizado


@pytest.fixture(scope="module")
def bytes_klebson() -> bytes:
    return PDF_KLEBSON.read_bytes()


@pytest.fixture(scope="module")
def bytes_milena() -> bytes:
    return PDF_MILENA.read_bytes()


@pytest.fixture(scope="module")
def bytes_henrique() -> bytes:
    return PDF_HENRIQUE.read_bytes()


# ---------------------------------------------------------------------------
# Validação de template SIGAA
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pdf_path", [PDF_KLEBSON, PDF_MILENA, PDF_HENRIQUE])
def test_todos_sao_historicos_sigaa_validos(pdf_path: Path):
    """Os três PDFs devem ser reconhecidos como histórico SIGAA/UFPA válido."""
    StatusAlunoExtractor.validar_documento_historico(pdf_path.read_bytes())


# ---------------------------------------------------------------------------
# aluno_integralizou
# ---------------------------------------------------------------------------

def test_klebson_integralizou(bytes_klebson: bytes):
    """
    Exigido == Integralizado (3332h) e sem seção de pendentes
    → deve retornar True.
    """
    assert StatusAlunoExtractor.aluno_integralizou(bytes_klebson) is True


def test_milena_NAO_integralizou(bytes_milena: bytes):
    """
    Total Integralizado (3400h) >= Total Exigido (3196h), mas há 4
    componentes obrigatórios pendentes com CH > 0 → deve retornar False.
    Bug anterior: retornava True porque Pendente total = 0 h na tabela.
    """
    assert StatusAlunoExtractor.aluno_integralizou(bytes_milena) is False


def test_henrique_NAO_integralizou(bytes_henrique: bytes):
    """
    Total Integralizado (285h) muito abaixo do Exigido (2855h)
    → deve retornar False.
    """
    assert StatusAlunoExtractor.aluno_integralizou(bytes_henrique) is False


# ---------------------------------------------------------------------------
# aluno_matriculado — busca MATRICULADO na seção de componentes
# ---------------------------------------------------------------------------

def test_klebson_NAO_matriculado(bytes_klebson: bytes):
    """Klebson não tem disciplinas com situação MATRICULADO → False."""
    assert StatusAlunoExtractor.aluno_matriculado(bytes_klebson) is False


def test_milena_NAO_matriculado(bytes_milena: bytes):
    """Milena (GRADUANDO) não tem disciplinas com situação MATRICULADO → False."""
    assert StatusAlunoExtractor.aluno_matriculado(bytes_milena) is False


def test_henrique_matriculado(bytes_henrique: bytes):
    """
    Henrique tem ao menos uma disciplina com situação MATRICULADO
    na seção de componentes → deve retornar True.
    """
    assert StatusAlunoExtractor.aluno_matriculado(bytes_henrique) is True


# ---------------------------------------------------------------------------
# Extração de dados
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pdf_path,nome_esperado", [
    (PDF_KLEBSON,  "KLEBSON"),
    (PDF_MILENA,   "MILENA"),
    (PDF_HENRIQUE, "HENRIQUE"),
])
def test_extrair_nome(pdf_path: Path, nome_esperado: str):
    dados = StatusAlunoExtractor.extrair_dados_aluno(pdf_path.read_bytes())
    assert nome_esperado in dados.get("nome", "").upper()


@pytest.mark.parametrize("pdf_path", [PDF_KLEBSON, PDF_MILENA, PDF_HENRIQUE])
def test_extrair_ultimo_periodo(pdf_path: Path):
    periodo = StatusAlunoExtractor.extrair_ultimo_periodo_componente(pdf_path.read_bytes())
    assert periodo, "Período não extraído"
    ano, sem = periodo.split(".")
    assert int(ano) >= 2020
    assert sem in {"1", "2", "3", "4"}

