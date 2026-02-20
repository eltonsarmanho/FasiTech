#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import BinaryIO, Union


PdfInput = Union[str, os.PathLike, bytes, bytearray, BinaryIO]


class StatusAlunoExtractor:
    _MARCADORES_HISTORICO = (
        r"SIGAA\s*-\s*Sistema\s+Integrado\s+de\s+Gest[aã]o\s+de\s+Atividades\s+Acad[eê]micas",
        r"Hist[oó]rico\s+Acad[eê]mico\s*-\s*Emitido\s+em",
        r"Dados\s+Pessoais",
        r"Dados\s+do\s+V[íi]nculo\s+do\s+Discente",
        r"Para\s+verificar\s+a\s+autenticidade\s+deste\s+documento",
        r"https?://sigaa\.ufpa\.br/sigaa/documentos",
        r"Matr[íi]cula\s*:",
    )

    @staticmethod
    def _pdf_to_text(pdf_input: PdfInput) -> str:
        if isinstance(pdf_input, (str, os.PathLike)):
            return StatusAlunoExtractor._run_pdftotext(Path(pdf_input))

        if isinstance(pdf_input, (bytes, bytearray)):
            return StatusAlunoExtractor._run_pdftotext_bytes(bytes(pdf_input))

        if hasattr(pdf_input, "read"):
            read_position = None
            if hasattr(pdf_input, "tell"):
                try:
                    read_position = pdf_input.tell()
                except Exception:
                    read_position = None

            raw = pdf_input.read()

            if hasattr(pdf_input, "seek"):
                try:
                    pdf_input.seek(read_position if read_position is not None else 0)
                except Exception:
                    pass

            if not isinstance(raw, (bytes, bytearray)):
                raise ValueError("Arquivo de upload inválido: esperado conteúdo binário PDF.")
            return StatusAlunoExtractor._run_pdftotext_bytes(bytes(raw))

        raise TypeError(
            "Tipo de entrada inválido. Use caminho (str/path), bytes ou arquivo de upload (file-like)."
        )

    @staticmethod
    def _run_pdftotext(pdf_path: Path) -> str:
        try:
            proc = subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), "-"],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("Comando 'pdftotext' não encontrado no sistema.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise RuntimeError(f"Falha ao converter PDF em texto: {stderr}") from exc
        return proc.stdout

    @staticmethod
    def _run_pdftotext_bytes(pdf_bytes: bytes) -> str:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            return StatusAlunoExtractor._run_pdftotext(Path(tmp.name))

    @staticmethod
    def documento_historico_valido(pdf_input: PdfInput) -> bool:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        valido, _faltantes = StatusAlunoExtractor._validar_template_historico_texto(texto)
        return valido

    @staticmethod
    def validar_documento_historico(pdf_input: PdfInput) -> None:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)

    @staticmethod
    def _validar_documento_historico_texto(texto: str) -> None:
        valido, faltantes = StatusAlunoExtractor._validar_template_historico_texto(texto)
        if not valido:
            raise ValueError(
                "Documento inválido: o PDF enviado não corresponde ao template de Histórico Acadêmico SIGAA/UFPA."
            )

    @staticmethod
    def _validar_template_historico_texto(texto: str) -> tuple[bool, list[str]]:
        faltantes: list[str] = []
        for marker in StatusAlunoExtractor._MARCADORES_HISTORICO:
            if not re.search(marker, texto, flags=re.IGNORECASE):
                faltantes.append(marker)
        return len(faltantes) == 0, faltantes

    @staticmethod
    def aluno_integralizou(pdf_input: PdfInput) -> bool:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)

        # Captura a linha "Pendente ... Total", pegando o último número (total).
        match = re.search(
            r"^\s*Pendente\s+.*?(\d+)\s*h\s*$",
            texto,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        if not match:
            raise ValueError("Linha 'Pendente' não encontrada na seção de carga horária.")

        pendente_total = int(match.group(1))
        return pendente_total == 0

    @staticmethod
    def aluno_matriculado(pdf_input: PdfInput) -> bool:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)
        return "MATRICULADO" in texto.upper()

    @staticmethod
    def extrair_dados_aluno(pdf_input: PdfInput) -> dict[str, str]:
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)
        return StatusAlunoExtractor._extrair_dados_texto(texto)

    @staticmethod
    def extrair_ultimo_periodo_componente(pdf_input: PdfInput) -> str:
        """
        Extrai o último Ano/Período da seção
        'Componentes Curriculares Cursados/Cursando'.
        """
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)
        return StatusAlunoExtractor._extrair_ultimo_periodo_texto(texto)

    @staticmethod
    def _extrair_ultimo_periodo_texto(texto: str) -> str:
        secao = StatusAlunoExtractor._extrair_secao_componentes(texto)
        if not secao:
            return ""

        periodos = re.findall(r"\b(20\d{2}\.[1-9])\b", secao)
        if not periodos:
            return ""
        return periodos[-1]

    @staticmethod
    def extrair_periodo_matriculado(pdf_input: PdfInput) -> str:
        """
        Extrai o último Ano/Período cuja Situação seja MATRICULADO
        na seção 'Componentes Curriculares Cursados/Cursando'.
        """
        texto = StatusAlunoExtractor._pdf_to_text(pdf_input)
        StatusAlunoExtractor._validar_documento_historico_texto(texto)
        return StatusAlunoExtractor._extrair_periodo_matriculado_texto(texto)

    @staticmethod
    def _extrair_periodo_matriculado_texto(texto: str) -> str:
        secao = StatusAlunoExtractor._extrair_secao_componentes(texto)
        if not secao:
            return ""

        lines = [line.strip() for line in secao.splitlines() if line.strip()]
        period_indices: list[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            match_periodo = re.match(r"^(20\d{2}\.[1-9])\b", line)
            if match_periodo:
                period_indices.append((idx, match_periodo.group(1)))

        if not period_indices:
            return ""

        periodos_matriculados: list[str] = []
        for i, (start_idx, periodo) in enumerate(period_indices):
            end_idx = period_indices[i + 1][0] if i + 1 < len(period_indices) else len(lines)
            bloco = "\n".join(lines[start_idx:end_idx])
            if re.search(r"\bMATRICULADO\b", bloco, flags=re.IGNORECASE):
                periodos_matriculados.append(periodo)

        if periodos_matriculados:
            return periodos_matriculados[-1]

        # Fallback por proximidade: MATRICULADO pode aparecer fora do bloco no texto extraído.
        matriculado_indices = [idx for idx, line in enumerate(lines) if re.search(r"\bMATRICULADO\b", line, re.IGNORECASE)]
        if not matriculado_indices:
            return ""

        ultimo_matriculado_idx = matriculado_indices[-1]
        periodos_anteriores = [periodo for idx, periodo in period_indices if idx <= ultimo_matriculado_idx]
        if periodos_anteriores:
            return periodos_anteriores[-1]
        return ""

    @staticmethod
    def _extrair_secao_componentes(texto: str) -> str:
        inicio_match = re.search(
            r"Componentes\s+Curriculares\s+Cursados/Cursando",
            texto,
            flags=re.IGNORECASE,
        )
        if not inicio_match:
            return ""

        inicio = inicio_match.start()
        fim_match = re.search(
            r"\bLegenda\b|\bCarga\s+Hor[aá]ria\s+Integralizada/Pendente\b",
            texto[inicio:],
            flags=re.IGNORECASE,
        )
        fim = inicio + fim_match.start() if fim_match else len(texto)
        return texto[inicio:fim]

    @staticmethod
    def _extrair_dados_texto(texto: str) -> dict[str, str]:
        cpf = StatusAlunoExtractor._extrair_cpf(texto)
        nome = StatusAlunoExtractor._extrair_nome(texto)
        return {"nome": nome, "cpf": cpf}

    @staticmethod
    def _extrair_cpf(texto: str) -> str:
        match = re.search(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", texto)
        if match:
            return match.group(0)

        match = re.search(r"\b\d{11}\b", texto)
        if match:
            cpf = match.group(0)
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return ""

    @staticmethod
    def _extrair_nome(texto: str) -> str:
        patterns = [
            r"Nome(?:\s+do\s+Aluno)?\s*:\s*([A-ZÀ-Ú][A-ZÀ-Ú\s']{3,})",
            r"Discente\s*:\s*([A-ZÀ-Ú][A-ZÀ-Ú\s']{3,})",
            r"Aluno\s*:\s*([A-ZÀ-Ú][A-ZÀ-Ú\s']{3,})",
        ]

        for pattern in patterns:
            match = re.search(pattern, texto, flags=re.IGNORECASE)
            if match:
                return " ".join(match.group(1).split()).strip()

        lines = [line.strip() for line in texto.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            upper_line = line.upper()
            if "DISCENTE" in upper_line or "NOME" in upper_line:
                for offset in (0, 1):
                    candidate_idx = idx + offset
                    if candidate_idx >= len(lines):
                        continue
                    candidate = lines[candidate_idx].strip()
                    if len(candidate.split()) >= 2 and not re.search(r"\d", candidate):
                        return " ".join(candidate.split())

        return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida status do aluno (integralização e matrícula) a partir de PDF."
    )
    parser.add_argument("pdf", help="Caminho do PDF do histórico acadêmico.")
    args = parser.parse_args()

    integralizou = StatusAlunoExtractor.aluno_integralizou(args.pdf)
    matriculado = StatusAlunoExtractor.aluno_matriculado(args.pdf)
    # Com upload (frontend/backend):

    # StatusAlunoExtractor.aluno_integralizou(file.read())
    # StatusAlunoExtractor.aluno_matriculado(file) (objeto com .read())


    print(f"Integralizou: {integralizou}")
    print(f"Matriculado: {matriculado}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
