#!/usr/bin/env python3
"""Gera comandos SQL UPDATE para preencher genero por matricula."""

from __future__ import annotations

import argparse
import csv
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


MAPA_GENERO_NOME_EXPLICITO: dict[str, str] = {
    "JOSE": "Masculino",
    "NALBERTH": "Masculino",
    "JOSIELSON": "Masculino",
    "DHEMERSOM": "Masculino",
    "LUCAS": "Masculino",
    "SAMUEL": "Masculino",
    "KLAYTON": "Masculino",
    "LAIZ": "Feminino",
    "NILCILENE": "Feminino",
    "RAILINE": "Feminino",
    "ELIAS": "Masculino",
    "KILDERY": "Masculino",
    "ADDAN": "Masculino",
    "WAYLAN": "Masculino",
    "IVANIEL": "Masculino",
    "JHON": "Masculino",
    "WAGNER": "Masculino",
    "HENRIQUE": "Masculino",
    "ERIK": "Masculino",
    "LAIANE": "Feminino",
    "NICOLE": "Feminino",
    "WENDEL": "Masculino",
    "FELIPE": "Masculino",
    "ALINE": "Feminino",
}


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_genero(value: str | None) -> str | None:
    raw = _clean(value)
    if not raw:
        return None

    key = _normalize_text(raw).casefold().strip()
    if key in {"masculino", "masc", "m"}:
        return "Masculino"
    if key in {"feminino", "feminno", "fem", "f"}:
        return "Feminino"
    return None


def _primeiro_nome(nome: str | None) -> str:
    return _clean(nome).split(" ", 1)[0].upper()


def _inferir_genero_por_nome(
    primeiro_nome: str,
    mapa_nomes_aprendidos: dict[str, str],
) -> str | None:
    if not primeiro_nome:
        return None

    if primeiro_nome in mapa_nomes_aprendidos:
        return mapa_nomes_aprendidos[primeiro_nome]

    if primeiro_nome in MAPA_GENERO_NOME_EXPLICITO:
        return MAPA_GENERO_NOME_EXPLICITO[primeiro_nome]

    # Fallback conservador por sufixo quando nao ha historico no CSV.
    if primeiro_nome.endswith("A"):
        return "Feminino"
    if primeiro_nome.endswith("O"):
        return "Masculino"

    return None


def gerar_updates(input_csv: Path, output_txt: Path) -> tuple[int, int, int, int]:
    """
    Lê o CSV e gera UPDATEs em TXT.

    Retorna:
      - total de matriculas processadas
      - total de linhas sem matricula (ignoradas)
      - total de conflitos de genero para a mesma matricula
      - total de matriculas atualizadas com NULL
    """
    linhas: list[dict[str, str]] = []
    ignoradas = 0
    conflitos = 0
    nulls = 0

    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError("CSV sem cabecalho.")

        if "Matricula" not in reader.fieldnames or "Genero" not in reader.fieldnames:
            raise ValueError("CSV precisa conter as colunas 'Matricula' e 'Genero'.")

        for row in reader:
            matricula = _clean(row.get("Matricula"))
            if not matricula:
                ignoradas += 1
                continue

            linhas.append(
                {
                    "matricula": matricula,
                    "nome": _clean(row.get("Nome")),
                    "genero": _clean(row.get("Genero")),
                }
            )

    aprendizado_por_nome: dict[str, Counter[str]] = defaultdict(Counter)
    for row in linhas:
        genero_norm = _normalize_genero(row["genero"])
        primeiro_nome = _primeiro_nome(row["nome"])
        if genero_norm and primeiro_nome:
            aprendizado_por_nome[primeiro_nome][genero_norm] += 1

    mapa_nomes_aprendidos: dict[str, str] = {}
    for nome, contagem in aprendizado_por_nome.items():
        if len(contagem) == 1:
            mapa_nomes_aprendidos[nome] = next(iter(contagem))
            continue

        masculino = contagem.get("Masculino", 0)
        feminino = contagem.get("Feminino", 0)
        if masculino > feminino:
            mapa_nomes_aprendidos[nome] = "Masculino"
        elif feminino > masculino:
            mapa_nomes_aprendidos[nome] = "Feminino"

    por_matricula: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in linhas:
        por_matricula[row["matricula"]].append(row)

    mapa_genero: dict[str, str | None] = {}
    for matricula, itens in por_matricula.items():
        generos_explicitos = {
            g for g in (_normalize_genero(i["genero"]) for i in itens) if g is not None
        }

        if len(generos_explicitos) > 1:
            conflitos += 1
            mapa_genero[matricula] = None
            nulls += 1
            continue

        if len(generos_explicitos) == 1:
            mapa_genero[matricula] = next(iter(generos_explicitos))
            continue

        genero_inferido: str | None = None
        for item in itens:
            primeiro_nome = _primeiro_nome(item["nome"])
            if not primeiro_nome:
                continue

            candidato = _inferir_genero_por_nome(primeiro_nome, mapa_nomes_aprendidos)
            if candidato is None:
                continue

            if genero_inferido and genero_inferido != candidato:
                genero_inferido = None
                break
            genero_inferido = candidato

        mapa_genero[matricula] = genero_inferido
        if genero_inferido is None:
            nulls += 1

    linhas_sql: list[str] = []
    for matricula in sorted(mapa_genero):
        genero_sql = (
            f"'{_escape_sql(mapa_genero[matricula])}'"
            if mapa_genero[matricula] is not None
            else "NULL"
        )
        linhas_sql.extend(
            [
                "UPDATE public.social_submissions",
                f"\tSET  genero={genero_sql}",
                f"\tWHERE matricula = '{_escape_sql(matricula)}';",
                "",
            ]
        )

    output_txt.write_text("\n".join(linhas_sql).rstrip() + "\n", encoding="utf-8")

    return len(mapa_genero), ignoradas, conflitos, nulls


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera TXT com UPDATE de genero em social_submissions por matricula."
    )
    parser.add_argument(
        "--input",
        default="tests/Buscar_Genero/DadosAgrupados.csv",
        help="Caminho do CSV de entrada.",
    )
    parser.add_argument(
        "--output",
        default="tests/Buscar_Genero/updates_genero.sql.txt",
        help="Caminho do TXT de saida.",
    )

    args = parser.parse_args()
    input_csv = Path(args.input)
    output_txt = Path(args.output)

    if not input_csv.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {input_csv}")

    total, ignoradas, conflitos, nulls = gerar_updates(input_csv, output_txt)

    print(f"Arquivo gerado: {output_txt}")
    print(f"Matriculas processadas: {total}")
    print(f"Linhas ignoradas (sem matricula): {ignoradas}")
    print(f"Conflitos de genero por matricula: {conflitos}")
    print(f"Matriculas com genero NULL: {nulls}")


if __name__ == "__main__":
    main()
