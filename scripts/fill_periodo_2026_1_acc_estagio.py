"""Script temporário para preencher `periodo` com 2026.1.

Regra:
- Atualizar para `2026.1` quando:
  1) registro for ACC E polo em {OEIRAS DO PARÁ, LIMOEIRO DO AJURU}
  2) registro for Estágio de Relatório Final E polo em {OEIRAS DO PARÁ, LIMOEIRO DO AJURU}

Tabelas afetadas:
- acc_submissions
- estagio_submissions

Uso:
- Simulação (sem gravar): python scripts/fill_periodo_2026_1_acc_estagio.py
- Aplicar alterações:     python scripts/fill_periodo_2026_1_acc_estagio.py --apply
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.env_loader import load_environment

load_environment()

from sqlmodel import select

from src.database.engine import get_db_session
from src.models.db_models import AccSubmission, EstagioSubmission

TARGET_PERIODO = "2026.1"
TARGET_POLOS = {"oeiras do para", "limoeiro do ajuru"}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _norm(value: Any) -> str:
    text = _safe_text(value)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower().strip()


def _is_target_polo(polo: Any) -> bool:
    return _norm(polo) in TARGET_POLOS


def _is_relatorio_final(componente: Any) -> bool:
    comp = _norm(componente)
    return comp.startswith("relatorio final")


def _update_acc(records: Iterable[AccSubmission]) -> tuple[int, int]:
    total = 0
    updated = 0

    for row in records:
        total += 1
        if not _is_target_polo(row.polo):
            continue
        if _safe_text(row.periodo) == TARGET_PERIODO:
            continue
        row.periodo = TARGET_PERIODO
        updated += 1

    return total, updated


def _update_estagio(records: Iterable[EstagioSubmission]) -> tuple[int, int]:
    total = 0
    updated = 0

    for row in records:
        total += 1
        if not _is_target_polo(row.polo):
            continue
        if not _is_relatorio_final(row.componente):
            continue
        if _safe_text(row.periodo) == TARGET_PERIODO:
            continue
        row.periodo = TARGET_PERIODO
        updated += 1

    return total, updated


def main() -> int:
    parser = argparse.ArgumentParser(description="Preencher período 2026.1 para ACC/Estágio por regra")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica alterações no banco. Sem esta flag, roda em simulação.",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("PREENCHIMENTO DE PERIODO (2026.1) - ACC E ESTAGIO RELATORIO FINAL")
    print("=" * 72)

    with get_db_session() as session:
        acc_rows = session.exec(select(AccSubmission)).all()
        estagio_rows = session.exec(select(EstagioSubmission)).all()

        acc_total, acc_updated = _update_acc(acc_rows)
        est_total, est_updated = _update_estagio(estagio_rows)

        if args.apply:
            session.commit()
            print("\n✅ Alterações salvas com sucesso.")
        else:
            session.rollback()
            print("\nℹ️ Simulação concluída. Nenhuma alteração foi gravada.")

    print(f"\nACC: total={acc_total} | atualizados={acc_updated}")
    print(f"Estágio (Relatório Final): total={est_total} | atualizados={est_updated}")
    print(f"Total atualizados: {acc_updated + est_updated}")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
