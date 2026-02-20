from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from reportlab.pdfgen import canvas


def _resolver_caminho_certificado() -> Path:
    """Resolve caminho do certificado PFX em ambiente local/VM."""
    env_path = os.getenv("CERTIFICADO_PFX_PATH")
    candidates = [
        Path(env_path).expanduser() if env_path else None,
        Path(__file__).resolve().parents[1] / "resources" / "certificado.pfx",
        Path.cwd() / "src" / "resources" / "certificado.pfx",
        Path("/app/src/resources/certificado.pfx"),
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Certificado PFX não encontrado. Configure CERTIFICADO_PFX_PATH "
        "ou garanta o arquivo src/resources/certificado.pfx."
    )


def _normalizar_senha(senha: str | None) -> str | None:
    if senha is None:
        return None
    senha = senha.strip()
    if (senha.startswith('"') and senha.endswith('"')) or (senha.startswith("'") and senha.endswith("'")):
        senha = senha[1:-1].strip()
    return senha or None


def _obter_senha_certificado() -> str:
    """
    Retorna a senha do certificado.
    Padrão do projeto: 1234.
    """
    senha_env = _normalizar_senha(os.getenv("CERTIFICADO_PFX_PASSWORD"))
    return senha_env or "1234"


def _ler_dados_certificado(caminho_certificado: Path, senha: str | None) -> dict[str, str]:
    """Lê dados do certificado para compor bloco visual da assinatura."""
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.x509.oid import NameOID
    except ImportError as exc:
        raise RuntimeError("Biblioteca 'cryptography' não disponível para leitura do certificado.") from exc

    password_bytes = senha.encode("utf-8") if senha else None
    key, cert, _additional = pkcs12.load_key_and_certificates(caminho_certificado.read_bytes(), password_bytes)

    if key is None or cert is None:
        raise ValueError("Certificado PFX inválido ou sem chave privada.")

    common_name = "Certificado ICP-Brasil"
    try:
        common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except Exception:
        pass

    serial = hex(cert.serial_number)[2:].upper()
    serial_curto = serial[-16:] if len(serial) > 16 else serial
    return {"common_name": common_name, "serial": serial_curto}


def _aplicar_assinatura_visual(caminho_pdf: Path, dados_cert: dict[str, str], texto_assinatura: str) -> None:
    """Aplica bloco visual da assinatura acima da linha do diretor."""
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError as exc:
            raise RuntimeError("Biblioteca PyPDF2/pypdf não disponível para assinatura visual.") from exc

    reader = PdfReader(str(caminho_pdf))
    writer = PdfWriter()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_overlay:
        overlay_path = Path(tmp_overlay.name)

    try:
        ultima_pagina = reader.pages[-1]
        largura = float(ultima_pagina.mediabox.width)
        altura = float(ultima_pagina.mediabox.height)

        # Posição acima da linha de assinatura do diretor.
        assinatura_x = 70
        assinatura_y = 238

        c = canvas.Canvas(str(overlay_path), pagesize=(largura, altura))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(assinatura_x, assinatura_y + 12, "ASSINATURA DIGITAL")
        c.setFont("Helvetica", 8)
        c.drawString(assinatura_x, assinatura_y, texto_assinatura)
        c.drawString(assinatura_x, assinatura_y - 11, f"Titular: {dados_cert['common_name']}")
        c.drawString(assinatura_x, assinatura_y - 22, f"Serial: {dados_cert['serial']}")
        c.drawString(
            assinatura_x,
            assinatura_y - 33,
            f"Carimbo de tempo: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        c.save()

        overlay_reader = PdfReader(str(overlay_path))
        overlay_page = overlay_reader.pages[0]

        for idx, page in enumerate(reader.pages):
            if idx == len(reader.pages) - 1:
                page.merge_page(overlay_page)
            writer.add_page(page)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_signed:
            temp_signed_path = Path(tmp_signed.name)

        with temp_signed_path.open("wb") as out_file:
            writer.write(out_file)

        temp_signed_path.replace(caminho_pdf)
    finally:
        if overlay_path.exists():
            overlay_path.unlink()


def _aplicar_assinatura_criptografica(caminho_pdf: Path, caminho_certificado: Path, senha: str | None) -> bool:
    """
    Tenta aplicar assinatura criptográfica no PDF usando o PFX.
    Retorna True em caso de sucesso; False se pyhanko não estiver disponível.
    """
    try:
        from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
        from pyhanko.sign import fields, signers
    except ImportError:
        return False

    passphrase = senha.encode("utf-8") if senha else None
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_out:
        signed_tmp_path = Path(tmp_out.name)

    try:
        try:
            signer = signers.SimpleSigner.load_pkcs12(str(caminho_certificado), passphrase=passphrase)
        except TypeError:
            signer = signers.SimpleSigner.load_pkcs12(pfx_file=str(caminho_certificado), passphrase=passphrase)

        with caminho_pdf.open("rb") as input_fp:
            writer = IncrementalPdfFileWriter(input_fp)
            sig_field_name = "AssinaturaFASI"

            try:
                fields.append_signature_field(
                    writer,
                    fields.SigFieldSpec(
                        sig_field_name=sig_field_name,
                        box=(65, 235, 315, 285),
                        on_page=-1,
                    ),
                )
            except Exception:
                # Campo já existente em reprocessamentos.
                pass

            pdf_signer = signers.PdfSigner(
                signers.PdfSignatureMetadata(
                    field_name=sig_field_name,
                    reason="Documento institucional FASI/UFPA",
                    location="Cametá",
                ),
                signer=signer,
            )
            with signed_tmp_path.open("wb") as output_fp:
                pdf_signer.sign_pdf(writer, output=output_fp)

        signed_tmp_path.replace(caminho_pdf)
        return True
    finally:
        if signed_tmp_path.exists():
            signed_tmp_path.unlink(missing_ok=True)


def assinar_pdf(
    caminho_pdf: str,
    *,
    caminho_saida: str | None = None,
    texto_assinatura: str = "Assinado digitalmente com certificado ICP-Brasil",
) -> str:
    """
    Assina o PDF com base no certificado PFX:
    1) bloco visual com dados do certificado (acima da linha do diretor);
    2) assinatura criptográfica, quando pyhanko estiver disponível.
    """
    origem = Path(caminho_pdf)
    if not origem.exists():
        raise FileNotFoundError(f"PDF não encontrado para assinatura: {caminho_pdf}")

    destino = Path(caminho_saida) if caminho_saida else origem
    if origem != destino:
        shutil.copyfile(origem, destino)

    caminho_certificado = _resolver_caminho_certificado()
    senha_certificado = _obter_senha_certificado()

    try:
        dados_certificado = _ler_dados_certificado(caminho_certificado, senha_certificado)
    except Exception:
        # Fallback para senha padrão institucional em caso de env incorreta.
        if senha_certificado != "1234":
            senha_certificado = "1234"
            dados_certificado = _ler_dados_certificado(caminho_certificado, senha_certificado)
        else:
            raise

    _aplicar_assinatura_visual(destino, dados_certificado, texto_assinatura)
    assinatura_criptografica_ok = _aplicar_assinatura_criptografica(
        destino,
        caminho_certificado,
        senha_certificado,
    )
    if not assinatura_criptografica_ok:
        print("⚠️ pyhanko não disponível; aplicado somente bloco visual da assinatura do certificado.")

    return str(destino)
