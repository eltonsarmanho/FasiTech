"""
Testes de validação do StatusAlunoExtractor com o histórico real da aluna
Milena Lopes Brabo (matrícula 202285940010).

Cenário:
  - Obrigatórias Exigido  : 3196 h
  - Obrigatórias Integralizado: 3060 h  (< Exigido → NÃO integralizada)
  - Componentes Obrigatórios Pendentes: 4 (SI05049, SI05050, SI05048, ENADE)
  - Status SIGAA: GRADUANDO (não FORMANDO)
"""

from pathlib import Path

import pytest

from backend.infrastructure.documents.status_extractor import StatusAlunoExtractor

HISTORICO_PDF = Path(__file__).parent / "historico_202016040002.pdf"


@pytest.fixture(scope="module")
def pdf_bytes() -> bytes:
    return HISTORICO_PDF.read_bytes()


# ---------------------------------------------------------------------------
# Validação do template
# ---------------------------------------------------------------------------

def test_valida_documento_historico_nao_lanca(pdf_bytes: bytes):
    """O PDF é reconhecido como histórico SIGAA/UFPA válido."""
    StatusAlunoExtractor.validar_documento_historico(pdf_bytes)  # não deve lançar


# ---------------------------------------------------------------------------
# Integralização – regra corrigida
# ---------------------------------------------------------------------------

def test_aluno_NAO_integralizou(pdf_bytes: bytes):
    """
    Total Integralizado (3400h) >= Total Exigido (3196h) → passa a primeira checagem.
    Bloqueada pela segunda: 4 componentes obrigatórios pendentes com CH > 0
    (SI05049 34h, SI05050 34h, SI05048 68h; ENADE 0h ignorado).
    Bug anterior: método retornava True porque Pendente total = 0 h.
    """
    resultado = StatusAlunoExtractor.aluno_integralizou(pdf_bytes)
    assert resultado is False, (
        "Esperado False: aluna possui componentes obrigatórios pendentes "
        "com carga horária > 0."
    )


# ---------------------------------------------------------------------------
# Matrícula ativa
# ---------------------------------------------------------------------------

def test_aluno_matriculado_retorna_false_para_graduando(pdf_bytes: bytes):
    """
    Status da aluna é GRADUANDO (não MATRICULADO), então aluno_matriculado
    deve retornar False com a implementação atual.
    Nota: o fluxo de Comprovante de Conclusão usa aluno_integralizou, não este método.
    """
    resultado = StatusAlunoExtractor.aluno_matriculado(pdf_bytes)
    assert resultado is False



def test_extrair_ultimo_periodo(pdf_bytes: bytes):
    periodo = StatusAlunoExtractor.extrair_ultimo_periodo_componente(pdf_bytes)
    assert periodo, "Período não extraído"
    ano, sem = periodo.split(".")
    assert int(ano) >= 2022
    assert sem in {"1", "2", "3", "4"}


def test_extrair_periodo_matriculado(pdf_bytes: bytes):
    periodo = StatusAlunoExtractor.extrair_periodo_matriculado(pdf_bytes)
    # Aluna está GRADUANDO, pode não ter período MATRICULADO explícito
    # Apenas verifica que não lança exceção e retorna string
    assert isinstance(periodo, str)
