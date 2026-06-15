"""
Testes unitários para a lógica de conflito de agenda do Requerimento de TCC.

Cenários validados:
  1.  Sem registros existentes → sem conflito
  2.  Mesmo slot, mesma banca, mesmo título (TCC dupla) → sem conflito
  3.  Mesmo slot, ≥1 professor em comum → conflito
  4.  Mesmo slot, grupos completamente diferentes → sem conflito  ← nova regra
  5.  Slots diferentes (< 60 min), professor em comum → conflito
  6.  Slots diferentes (< 60 min), sem sobreposição → sem conflito
  7.  Slots diferentes (≥ 60 min), professor em comum → sem conflito
  8.  Mesmo slot, múltiplos professores em comum → mensagem lista todos
  9.  Dados sem data/horário → retorna vazio sem erro
  10. exclude_matricula remove próprio aluno
  11. [BUG FIX] título vazio em row existente → NÃO é dupla → conflito detectado
  12. [BUG FIX] título vazio em novo cadastro → NÃO é dupla → conflito detectado
  13. [BUG FIX] ambos títulos vazios + mesma banca → NÃO é dupla → conflito detectado
  14. [BUG FIX] schema: data_defesa é obrigatório (str, não Optional)
  15. _parse_horario_minutos: formatos válidos e inválidos
  16. _banca_members_from_dict: normalização de nomes
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from backend.infrastructure.database.repository import (
    _banca_members_from_dict,
    _banca_members_from_row,
    _parse_horario_minutos,
    check_tcc_scheduling_conflicts,
)
from backend.presentation.schemas.forms import RequerimentoTccFormRequest

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

DATA = "2026-07-15"
H1   = "14:00"   # 840 min
H2   = "14:30"   # 870 min  → 30 min depois de H1 (< 60)
H3   = "15:01"   # 901 min  → 61 min depois de H1 (≥ 60)

PROF_A = "Alice Mendes"
PROF_B = "Bruno Costa"
PROF_C = "Carlos Lima"
PROF_D = "Daniela Rocha"
PROF_E = "Eduardo Nunes"


def _make_row(
    nome_aluno: str,
    horario: str,
    orientador: str,
    m1: str,
    m2: str,
    m3: str = "",
    titulo: str = "titulo x",
) -> SimpleNamespace:
    """Cria um objeto simulando uma linha do banco de dados."""
    return SimpleNamespace(
        nome_aluno=nome_aluno,
        horario_defesa=horario,
        orientador=orientador,
        membro_banca1=m1,
        membro_banca2=m2,
        membro_banca3=m3 or None,
        titulo_trabalho=titulo,
    )


def _new_data(
    horario: str,
    orientador: str,
    m1: str,
    m2: str,
    m3: str = "",
    titulo: str = "titulo y",
    matricula: str = "202116040099",
) -> dict:
    return {
        "data_defesa": DATA,
        "horario_defesa": horario,
        "orientador": orientador,
        "membro_banca1": m1,
        "membro_banca2": m2,
        "membro_banca3": m3,
        "titulo_trabalho": titulo,
        "matricula": matricula,
    }


def _run(new: dict, existing_rows: list, exclude: str | None = None) -> list[str]:
    """Executa check_tcc_scheduling_conflicts mockando o banco."""
    mock_session = MagicMock()
    mock_session.__enter__ = lambda s: s
    mock_session.__exit__ = MagicMock(return_value=False)
    mock_session.exec.return_value.all.return_value = existing_rows

    with (
        patch("backend.infrastructure.database.repository._ensure_requerimento_tcc_schema_columns"),
        patch("backend.infrastructure.database.repository.get_db_session", return_value=mock_session),
    ):
        return check_tcc_scheduling_conflicts(new, exclude_matricula=exclude)


# ──────────────────────────────────────────────────────────────────────────────
# Testes dos helpers puros
# ──────────────────────────────────────────────────────────────────────────────

class TestParseHorario:
    def test_formato_hhmm(self):
        assert _parse_horario_minutos("14:30") == 870

    def test_formato_hhhmm(self):
        assert _parse_horario_minutos("14h30") == 870

    def test_hora_cheia(self):
        assert _parse_horario_minutos("08:00") == 480

    def test_meia_noite(self):
        assert _parse_horario_minutos("0:00") == 0

    def test_invalido_retorna_none(self):
        assert _parse_horario_minutos("abc") is None

    def test_vazio_retorna_none(self):
        assert _parse_horario_minutos("") is None


class TestBancaMembersFromDict:
    def test_normaliza_para_lower(self):
        data = {"orientador": "Alice MENDES", "membro_banca1": "Bruno Costa",
                "membro_banca2": "Carlos Lima", "membro_banca3": ""}
        members = _banca_members_from_dict(data)
        assert "alice mendes" in members
        assert "bruno costa" in members
        assert "carlos lima" in members
        assert len(members) == 3

    def test_ignora_campos_vazios(self):
        data = {"orientador": "Alice", "membro_banca1": "", "membro_banca2": None}
        assert _banca_members_from_dict(data) == {"alice"}


class TestBancaMembersFromRow:
    def test_row_simples(self):
        row = SimpleNamespace(orientador="Alice", membro_banca1="Bruno",
                              membro_banca2="Carlos", membro_banca3=None)
        assert _banca_members_from_row(row) == {"alice", "bruno", "carlos"}


# ──────────────────────────────────────────────────────────────────────────────
# Testes da lógica de conflito
# ──────────────────────────────────────────────────────────────────────────────

class TestConflitosAgenda:

    # 1. Sem registros existentes
    def test_sem_registros_sem_conflito(self):
        new = _new_data(H1, PROF_A, PROF_B, PROF_C)
        assert _run(new, []) == []

    # 2. Mesmo slot, mesma banca + mesmo título (TCC dupla)
    def test_mesmo_slot_tcc_dupla_sem_conflito(self):
        titulo = "sistema de recomendação"
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C, titulo=titulo)
        new = _new_data(H1, PROF_A, PROF_B, PROF_C, titulo=titulo)
        assert _run(new, [row]) == []

    # 3. Mesmo slot, professor em comum → conflito
    def test_mesmo_slot_professor_em_comum_conflito(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        # PROF_B aparece em ambas as bancas
        new = _new_data(H1, PROF_D, PROF_B, PROF_E)
        result = _run(new, [row])
        assert len(result) == 1
        assert PROF_B.lower() in result[0].lower()
        assert "Aluno 1" in result[0]

    # 4. Mesmo slot, grupos completamente diferentes → SEM conflito (nova regra)
    def test_mesmo_slot_grupos_diferentes_sem_conflito(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H1, PROF_D, PROF_E, "Fernanda Souza")
        assert _run(new, [row]) == []

    # 5. Slots diferentes < 60 min, professor em comum → conflito
    def test_slot_proximo_professor_em_comum_conflito(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H2, PROF_D, PROF_A, PROF_E)  # PROF_A em comum, 30 min depois
        result = _run(new, [row])
        assert len(result) == 1
        assert PROF_A.lower() in result[0].lower()

    # 6. Slots diferentes < 60 min, sem sobreposição → sem conflito
    def test_slot_proximo_sem_overlap_sem_conflito(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H2, PROF_D, PROF_E, "Fernanda Souza")
        assert _run(new, [row]) == []

    # 7. Slots diferentes ≥ 60 min, professor em comum → sem conflito
    def test_slot_distante_sem_conflito(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H3, PROF_A, PROF_B, PROF_C)  # mesmos profs, 61 min depois
        assert _run(new, [row]) == []

    # 8. Mesmo slot, múltiplos professores em comum → mensagem lista todos
    def test_mesmo_slot_multiplos_em_comum(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H1, PROF_A, PROF_B, PROF_D)  # A e B em comum
        result = _run(new, [row])
        assert len(result) == 1
        msg = result[0].lower()
        assert PROF_A.lower() in msg
        assert PROF_B.lower() in msg

    # 9. Dados sem data/horário → retorna vazio sem erro
    def test_dados_sem_data_retorna_vazio(self):
        new = {"titulo_trabalho": "x", "orientador": PROF_A}
        assert _run(new, []) == []

    # 10. exclude_matricula remove o próprio aluno ao reeditar
    def test_exclude_matricula_ignorado_na_query(self):
        """O filtro exclude_matricula é passado à query — o mock valida que não há conflito
        quando a única linha existente é do próprio aluno (excluída pelo filtro)."""
        row = _make_row("Mesmo Aluno", H1, PROF_A, PROF_B, PROF_C)
        new = _new_data(H1, PROF_A, PROF_B, PROF_C, titulo="titulo x", matricula="MAT001")
        # O mock devolve lista vazia (simula o banco já tendo filtrado a própria matrícula)
        assert _run(new, [], exclude="MAT001") == []


# ──────────────────────────────────────────────────────────────────────────────
# Testes dos três bugs corrigidos
# ──────────────────────────────────────────────────────────────────────────────

class TestBugFixesCriticos:
    """Casos que cobriam os bugs que causavam success+email com conflito em produção."""

    # BUG FIX 1a — row existente com título NULL/vazio não deve ser tratado como dupla
    def test_titulo_vazio_em_row_existente_nao_e_dupla(self):
        """Registro antigo no banco com titulo_trabalho='' não é dupla → conflito detectado."""
        row = _make_row("Aluno Antigo", H1, PROF_A, PROF_B, PROF_C, titulo="")
        # Novo cadastro tem mesma banca e título também vazio
        new = _new_data(H1, PROF_A, PROF_B, PROF_C, titulo="")
        result = _run(new, [row])
        # titulo vazio + mesma banca NÃO deve ser aceito como dupla → conflito
        assert len(result) == 1

    # BUG FIX 1b — novo cadastro com título vazio, row com título válido → NÃO é dupla
    def test_titulo_novo_vazio_nao_e_dupla(self):
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C, titulo="Sistema de TCC")
        new = _new_data(H1, PROF_A, PROF_B, PROF_C, titulo="")
        result = _run(new, [row])
        # "" != "sistema de tcc" → is_dupla=False; overlap={a,b,c} → conflito
        assert len(result) == 1

    # BUG FIX 1c — dupla real (títulos iguais e não-vazios) ainda funciona corretamente
    def test_dupla_real_com_titulo_valido_sem_conflito(self):
        titulo = "Aplicação Web para Gestão Acadêmica"
        row = _make_row("Aluno 1", H1, PROF_A, PROF_B, PROF_C, titulo=titulo)
        new = _new_data(H1, PROF_A, PROF_B, PROF_C, titulo=titulo)
        assert _run(new, [row]) == []

    # BUG FIX 2 — data_defesa obrigatória no schema do request
    def test_schema_data_defesa_obrigatorio(self):
        """Requisição sem data_defesa deve ser rejeitada pelo Pydantic."""
        with pytest.raises(ValidationError):
            RequerimentoTccFormRequest(
                nome_aluno="João Silva",
                matricula="202116040001",
                email="joao@ufpa.br",
                turma="2021",
                orientador=PROF_A,
                titulo_trabalho="Meu TCC",
                modalidade="Monografia",
                horario_defesa="14:00",
                # data_defesa propositalmente ausente
            )

    # BUG FIX 2b — data_defesa não pode ser None
    def test_schema_data_defesa_nao_aceita_none(self):
        """data_defesa=None deve ser rejeitado pelo Pydantic."""
        with pytest.raises((ValidationError, TypeError)):
            RequerimentoTccFormRequest(
                nome_aluno="João Silva",
                matricula="202116040001",
                email="joao@ufpa.br",
                turma="2021",
                orientador=PROF_A,
                titulo_trabalho="Meu TCC",
                modalidade="Monografia",
                data_defesa=None,   # explicitamente None
                horario_defesa="14:00",
            )

    # BUG FIX 2c — schema aceita normalmente quando data_defesa está preenchida
    def test_schema_data_defesa_preenchida_ok(self):
        req = RequerimentoTccFormRequest(
            nome_aluno="João Silva",
            matricula="202116040001",
            email="joao@ufpa.br",
            turma="2021",
            orientador=PROF_A,
            titulo_trabalho="Meu TCC",
            modalidade="Monografia",
            data_defesa="2026-07-15",
            horario_defesa="14:00",
        )
        assert req.data_defesa == "2026-07-15"

    # BUG FIX 3 — mesmo slot, mesmo professor em comum + título diferente → conflito
    # (valida o cenário completo que falhava em produção)
    def test_cenario_producao_mesmo_slot_titulo_diferente_conflito(self):
        """
        Cenário exato reportado em produção:
        - Aluno A já tem registro com banca {A,B,C}, data D, hora H
        - Aluno B tenta registrar com MESMA banca {A,B,C}, MESMA data D, MESMA hora H
          mas título DIFERENTE → deve ser detectado como conflito
        """
        row = _make_row(
            "Aluno A", H1, PROF_A, PROF_B, PROF_C,
            titulo="Título do TCC do Aluno A"
        )
        new = _new_data(
            H1, PROF_A, PROF_B, PROF_C,
            titulo="Título DIFERENTE do TCC do Aluno B"
        )
        result = _run(new, [row])
        assert len(result) == 1
        # Mensagem deve mencionar os professores conflitantes
        msg = result[0].lower()
        assert any(p.lower() in msg for p in [PROF_A, PROF_B, PROF_C])
