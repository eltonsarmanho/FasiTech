"""Script temporário para preencher coluna `polo` a partir da matrícula.

Regra:
- Matrícula: ANO(4) + COD_LOCAL(3) + POSICAO
- COD_LOCAL == 856 -> LIMOEIRO DO AJURU
- COD_LOCAL == 859 -> OEIRAS DO PARÁ
- Outros códigos -> CAMETÁ

Tabelas afetadas:
- acc_submissions
- tcc_submissions
- estagio_submissions

Uso:
- Simulação (sem gravar): python scripts/fill_polo_from_matricula.py
- Aplicar alterações:     python scripts/fill_polo_from_matricula.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.env_loader import load_environment

load_environment()

from src.database.engine import get_db_session
from src.models.db_models import AccSubmission, EstagioSubmission, TccSubmission
from sqlmodel import select


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_location_code(matricula: Any) -> str | None:
    """Extrai código de localização (3 dígitos após os 4 dígitos do ano)."""
    matricula_text = _normalize_text(matricula)
    if not re.fullmatch(r"\d{7,}", matricula_text):
        return None
    return matricula_text[4:7]


def _resolve_polo_from_matricula(matricula: Any) -> str | None:
    code = _extract_location_code(matricula)
    if code is None:
        return None
    if code == "856":
        return "LIMOEIRO DO AJURU"
    if code == "859":
        return "OEIRAS DO PARÁ"
    return "CAMETÁ"


def _update_table_records(
    records: Iterable[Any],
    table_label: str,
    *,
    apply_changes: bool,
) -> tuple[int, int, int]:
    """Atualiza registros de uma tabela.

    Returns:
        (total, atualizados, invalidos)
    """
    total = 0
    updated = 0
    invalid = 0

    for record in records:
        total += 1
        novo_polo = _resolve_polo_from_matricula(getattr(record, "matricula", None))
        if novo_polo is None:
            invalid += 1
            continue

        polo_atual = _normalize_text(getattr(record, "polo", ""))
        if polo_atual == novo_polo:
            continue

        setattr(record, "polo", novo_polo)
        updated += 1

    modo = "APLICAÇÃO" if apply_changes else "SIMULAÇÃO"
    print(f"[{modo}] {table_label}: total={total} | atualizados={updated} | matriculas_invalidas={invalid}")
    return total, updated, invalid


def main() -> int:
    parser = argparse.ArgumentParser(description="Preencher polo a partir da matrícula")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica alterações no banco. Sem esta flag, roda em simulação.",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("PREENCHIMENTO TEMPORÁRIO DE POLO POR MATRÍCULA")
    print("=" * 72)

    with get_db_session() as session:
        acc_records = session.exec(select(AccSubmission)).all()
        tcc_records = session.exec(select(TccSubmission)).all()
        estagio_records = session.exec(select(EstagioSubmission)).all()

        totals = []
        totals.append(_update_table_records(acc_records, "acc_submissions", apply_changes=args.apply))
        totals.append(_update_table_records(tcc_records, "tcc_submissions", apply_changes=args.apply))
        totals.append(_update_table_records(estagio_records, "estagio_submissions", apply_changes=args.apply))

        total_rows = sum(item[0] for item in totals)
        total_updates = sum(item[1] for item in totals)
        total_invalid = sum(item[2] for item in totals)

        if args.apply:
            session.commit()
            print("\n✅ Alterações salvas com sucesso.")
        else:
            session.rollback()
            print("\nℹ️ Simulação concluída. Nenhuma alteração foi gravada.")

    print(f"\nResumo geral: total={total_rows} | atualizados={total_updates} | matriculas_invalidas={total_invalid}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
