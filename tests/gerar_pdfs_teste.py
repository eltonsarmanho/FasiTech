#!/usr/bin/env python3
"""Gera PDFs de teste (Parecer e Declaração) com logo UFPA."""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.utils.PDFGenerator import gerar_pdf_projetos, gerar_pdf_declaracao_projeto

RESPOSTA = [
    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),  # 0 - timestamp
    "Elton Sarmanho Siqueira",                       # 1 - docente
    "Prof. Dr. Carlos dos Santos Portela",           # 2 - parecerista_1
    "Prof. Dr. João da Silva Oliveira",              # 3 - parecerista_2
    "Laboratório de Inteligência Artificial: Potencializando Habilidades Universitárias com Ambiente Agêntico de IA no Baixo Tocantins",  # 4 - projeto
    "200",                                           # 5 - carga_horaria
    "PIBEX",                                         # 6 - edital
    "Extensão",                                      # 7 - natureza
    "2025",                                          # 8 - ano_edital
    "Novo",                                          # 9 - solicitacao
]

OUT_DIR = ROOT_DIR / "tests" / "output_pdfs"
OUT_DIR.mkdir(exist_ok=True)

parecer = Path(gerar_pdf_projetos(RESPOSTA))
destino_parecer = OUT_DIR / "Teste_Parecer.pdf"
shutil.copyfile(parecer, destino_parecer)
print(f"Parecer gerado:    {destino_parecer}")

declaracao = Path(gerar_pdf_declaracao_projeto(RESPOSTA))
destino_declaracao = OUT_DIR / "Teste_Declaracao.pdf"
shutil.copyfile(declaracao, destino_declaracao)
print(f"Declaracao gerada: {destino_declaracao}")
