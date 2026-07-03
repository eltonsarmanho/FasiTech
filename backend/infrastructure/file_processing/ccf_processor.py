"""
Processador de CCF (Componentes Curriculares Flexibilizados)

Diferente do ACC (que soma cargas horárias de certificados avulsos), o CCF
compara uma lista de disciplinas *informadas pelo aluno* contra o conteúdo de
um PDF que pode ser um histórico escolar (com várias tabelas de disciplinas)
ou um conjunto de documentos agregados.

Divisão de responsabilidades:
- O Gemini extrai a lista de disciplinas/componentes curriculares presentes
  no documento (nome + carga horária), em formato de texto estruturado.
- A contagem/conferência (quais disciplinas informadas pelo aluno realmente
  constam no documento) é feita de forma determinística em Python — não
  depende da contagem da IA.
"""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError as exc:
    raise ImportError("python-dotenv not installed. Please install it with 'pip install python-dotenv'.") from exc

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import File

from backend.config.LLMConfig import GEMINI_MODEL_VISION as GEMINI_MODEL

load_dotenv(override=True)

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError("GOOGLE_API_KEY not set. Please add it to your environment or .env file before running.")

LIMIAR_SIMILARIDADE = 0.82

FIM_LISTA_MARCADOR = "FIM_LISTA_DISCIPLINAS"


def _criar_agente_extrator_disciplinas() -> Agent:
    """Cria um agente Gemini especializado em extrair disciplinas de
    históricos escolares ou documentos agregados de CCF."""
    instrucoes = f"""Você é um especialista em ler documentos acadêmicos. O PDF anexado pode ser
UM dos seguintes tipos (identifique qual antes de extrair):

1. HISTÓRICO ESCOLAR: extraia todas as disciplinas/componentes curriculares
   mencionados em qualquer uma das seções abaixo (quando existirem):
   - Disciplinas Cursadas / Dispensadas
   - Disciplinas Cursando / Reprovadas / Abandonos
   - Disciplinas Eletivas Cursadas / Em Curso
   - Disciplinas Optativas Cursadas / Em Curso
   - Falta Cursar
   NÃO inclua itens da seção "Atividade Complementar" (avaliação institucional,
   certificados de eventos, etc.) — apenas disciplinas/componentes curriculares.

2. CERTIFICADOS AVULSOS (um ou mais certificados de cursos/atividades
   mesclados em um único PDF): extraia o nome de cada curso/atividade
   certificado como se fosse uma disciplina.

3. DECLARAÇÕES (documento(s) emitido(s) por instituição declarando que o
   aluno cursou/concluiu uma ou mais disciplinas/componentes): extraia o
   nome de cada disciplina/componente mencionado na declaração.

Para cada disciplina/curso/componente encontrado, extraia o nome exatamente
como aparece no documento e a carga horária (se disponível; use 0 se não houver).

FORMATO DE RESPOSTA (uma linha por disciplina, sem texto adicional):
DISCIPLINA: <nome da disciplina> | CARGA_HORARIA: <número inteiro>

Ao final, na última linha, escreva exatamente:
{FIM_LISTA_MARCADOR}
"""
    try:
        return Agent(
            name="Extrator de Disciplinas CCF",
            model=Gemini(id=GEMINI_MODEL),
            instructions=instrucoes,
            markdown=False,
            debug_mode=False,
        )
    except Exception as e:
        raise RuntimeError(f"Falha ao inicializar agente Gemini: {e}")


def extrair_disciplinas_do_texto(texto: str) -> List[Dict[str, Any]]:
    """Faz o parse da resposta estruturada do agente em uma lista de
    {"nome": str, "carga_horaria": int}."""
    disciplinas: List[Dict[str, Any]] = []
    padrao = re.compile(r"DISCIPLINA:\s*(.+?)\s*\|\s*CARGA_HORARIA:\s*(\d+)", re.IGNORECASE)
    for match in padrao.finditer(texto):
        nome = match.group(1).strip()
        carga = int(match.group(2))
        if nome:
            disciplinas.append({"nome": nome, "carga_horaria": carga})
    return disciplinas


def _normalizar(nome: str) -> str:
    """Normaliza um nome de disciplina para comparação tolerante a acentos,
    caixa, pontuação e anotações entre parênteses (ex.: '(LEGO)', '(MATEMÁTICA)')."""
    nome = re.sub(r"\([^)]*\)", " ", nome)
    nome = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode("ascii")
    nome = re.sub(r"[^a-zA-Z0-9\s]", " ", nome)
    nome = re.sub(r"\s+", " ", nome).strip().upper()
    return nome


def _similaridade(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


@dataclass
class ResultadoConferencia:
    total_informadas: int
    total_confirmadas: int
    detalhes: List[Dict[str, Any]]


def conferir_disciplinas(
    disciplinas_informadas: List[str],
    disciplinas_documento: List[Dict[str, Any]],
    limiar: float = LIMIAR_SIMILARIDADE,
) -> ResultadoConferencia:
    """Confere, de forma determinística, quais disciplinas informadas pelo
    aluno constam no documento (por nome, tolerando pequenas variações)."""
    documento_normalizado = [(item, _normalizar(item["nome"])) for item in disciplinas_documento]

    detalhes: List[Dict[str, Any]] = []
    confirmadas = 0
    for informada in disciplinas_informadas:
        norm_informada = _normalizar(informada)
        melhor_item: Optional[Dict[str, Any]] = None
        melhor_score = 0.0
        for item, norm_doc in documento_normalizado:
            score = 1.0 if norm_informada == norm_doc else _similaridade(norm_informada, norm_doc)
            if score > melhor_score:
                melhor_score = score
                melhor_item = item

        encontrada = melhor_score >= limiar
        if encontrada:
            confirmadas += 1

        detalhes.append({
            "informada": informada,
            "encontrada": encontrada,
            "correspondencia": melhor_item["nome"] if (melhor_item and encontrada) else None,
            "carga_horaria": melhor_item.get("carga_horaria") if (melhor_item and encontrada) else None,
            "score": round(melhor_score, 2),
        })

    return ResultadoConferencia(
        total_informadas=len(disciplinas_informadas),
        total_confirmadas=confirmadas,
        detalhes=detalhes,
    )


def salvar_relatorio_txt(resultado: Dict[str, Any], matricula: str, nome: str, output_dir: str = "/tmp/ccf_results") -> str:
    """Salva um relatório detalhado da conferência em arquivo TXT (anexado ao e-mail)."""
    from datetime import datetime

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"CCF_{matricula}_{timestamp}.txt")

    linhas = [
        "=" * 70,
        "CONFERÊNCIA DE DISCIPLINAS CCF",
        "=" * 70,
        "",
        f"Aluno: {nome}",
        f"Matrícula: {matricula}",
        f"Data da Análise: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}",
        "",
        "=" * 70,
        "DISCIPLINAS INFORMADAS PELO ALUNO",
        "=" * 70,
        "",
    ]
    for item in resultado.get("detalhes", []):
        status = "✅ ENCONTRADA" if item["encontrada"] else "❌ NÃO ENCONTRADA"
        linhas.append(f"- {item['informada']}: {status}")
        if item["encontrada"]:
            linhas.append(f"    Correspondência no documento: {item['correspondencia']} ({item['carga_horaria']}h)")
    linhas.append("")
    linhas.append(resultado.get("resumo_texto", ""))
    linhas.append("")
    linhas.append("=" * 70)
    linhas.append("DISCIPLINAS ENCONTRADAS NO DOCUMENTO (bruto, para conferência manual)")
    linhas.append("=" * 70)
    linhas.append("")
    for item in resultado.get("disciplinas_documento", []):
        linhas.append(f"- {item['nome']} ({item['carga_horaria']}h)")
    linhas.append("")
    linhas.append("=" * 70)
    linhas.append("Documento gerado automaticamente pelo Sistema de Automação da FASI")
    linhas.append("=" * 70)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"📄 Relatório salvo em: {filepath}")
    return filepath


def processar_disciplinas_ccf(
    pdf_path: str,
    matricula: str,
    nome: str,
    disciplinas_informadas: List[str],
) -> Dict[str, Any]:
    """Extrai as disciplinas presentes no PDF (via Gemini) e confere quais das
    disciplinas informadas pelo aluno realmente constam no documento (via
    matching determinístico em Python — a contagem não depende da IA).

    Returns:
        dict com status, total_informadas, total_confirmadas, detalhes,
        resumo_texto e disciplinas_documento (lista bruta extraída do PDF).
    """
    print("\n" + "=" * 70)
    print("📑 PROCESSADOR DE DISCIPLINAS CCF")
    print("=" * 70)
    print(f"📌 Aluno: {nome}")
    print(f"📌 Matrícula: {matricula}")
    print(f"📌 Disciplinas informadas: {disciplinas_informadas}")

    if not disciplinas_informadas:
        # Sem disciplinas para conferir, não há o que a IA compare — pula a
        # chamada ao Gemini (economiza custo/tempo) e sinaliza análise manual.
        print("⏭️  Nenhuma disciplina informada — pulando extração via IA.")
        return {
            "status": "sem_disciplinas",
            "total_informadas": 0,
            "total_confirmadas": 0,
            "detalhes": [],
            "disciplinas_documento": [],
            "resumo_texto": "Aluno não informou disciplinas para conferência automática",
            "txt_path": None,
        }

    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf_path}")

        agent = _criar_agente_extrator_disciplinas()

        prompt = f"""Analise o documento PDF anexado (histórico escolar ou documentos agregados)
do aluno {nome} (Matrícula: {matricula}) e extraia todas as disciplinas/componentes
curriculares conforme as instruções."""

        pdf_file = File(filepath=pdf_path)
        response = agent.run(input=prompt, files=[pdf_file], stream=False)

        print("\n✅ RESPOSTA DO MODELO:")
        print(response.content)

        disciplinas_documento = extrair_disciplinas_do_texto(response.content)
        print(f"\n📚 Disciplinas extraídas do documento: {len(disciplinas_documento)}")

        conferencia = conferir_disciplinas(disciplinas_informadas, disciplinas_documento)
        resumo_texto = (
            f"{conferencia.total_confirmadas} de {conferencia.total_informadas} "
            "disciplinas informadas foram confirmadas no documento"
        )

        print(f"\n🎯 {resumo_texto}")

        resultado = {
            "status": "sucesso",
            "total_informadas": conferencia.total_informadas,
            "total_confirmadas": conferencia.total_confirmadas,
            "detalhes": conferencia.detalhes,
            "disciplinas_documento": disciplinas_documento,
            "resumo_texto": resumo_texto,
        }
        resultado["txt_path"] = salvar_relatorio_txt(resultado, matricula, nome)
        return resultado

    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO no processamento CCF: {type(e).__name__}: {e}")
        return {
            "status": "erro",
            "total_informadas": len(disciplinas_informadas),
            "total_confirmadas": 0,
            "detalhes": [],
            "disciplinas_documento": [],
            "resumo_texto": "⚠️ ERRO no processamento",
            "erro": str(e),
            "tipo_erro": type(e).__name__,
        }
