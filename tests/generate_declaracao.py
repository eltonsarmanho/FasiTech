#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.PDFGenerator import gerar_pdf_declaracao_projeto


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera PDF de declaração de projeto a partir de dados de entrada."
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help=(
            "Arquivo JSON com os campos: docente, nome_projeto, parecerista1, "
            "parecerista2, carga_horaria, edital, natureza, ano_edital, solicitacao."
        ),
    )
    parser.add_argument("--docente", default="Docente Exemplo")
    parser.add_argument("--nome-projeto", dest="nome_projeto", default="Projeto Exemplo")
    parser.add_argument("--parecerista1", default="Parecerista 1")
    parser.add_argument("--parecerista2", default="Parecerista 2")
    parser.add_argument("--carga-horaria", dest="carga_horaria", default="10")
    parser.add_argument("--edital", default="PIBEX")
    parser.add_argument("--natureza", default="Extensão")
    parser.add_argument("--ano-edital", dest="ano_edital", default=str(datetime.now().year))
    parser.add_argument("--solicitacao", default="Novo")
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho final do PDF gerado. Se omitido, mantém caminho padrão do gerador.",
    )
    return parser


def _load_data(args: argparse.Namespace) -> dict[str, str]:
    data = {
        "docente": args.docente,
        "nome_projeto": args.nome_projeto,
        "parecerista1": args.parecerista1,
        "parecerista2": args.parecerista2,
        "carga_horaria": args.carga_horaria,
        "edital": args.edital,
        "natureza": args.natureza,
        "ano_edital": args.ano_edital,
        "solicitacao": args.solicitacao,
    }

    if args.input_json:
        with args.input_json.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        data.update({k: str(v) for k, v in loaded.items() if v is not None})

    return data


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    data = _load_data(args)

    resposta = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        data["docente"],
        data["parecerista1"],
        data["parecerista2"],
        data["nome_projeto"],
        data["carga_horaria"],
        data["edital"],
        data["natureza"],
        data["ano_edital"],
        data["solicitacao"],
    ]

    caminho_gerado = Path(gerar_pdf_declaracao_projeto(resposta))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(caminho_gerado, args.output)
        caminho_final = args.output
    else:
        caminho_final = caminho_gerado

    print(f"PDF gerado: {caminho_final}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
