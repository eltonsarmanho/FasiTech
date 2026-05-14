from __future__ import annotations

import os
import re
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from reportlab.pdfgen import canvas

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


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


def _resolver_caminho_serpro() -> Path | None:
    """Resolve caminho da imagem do selo SERPRO (opcional)."""
    env_path = os.getenv("SERPRO_SIGNATURE_IMAGE")
    candidates = [
        Path(env_path).expanduser() if env_path else None,
        Path(__file__).resolve().parents[1] / "resources" / "serpro.png",
        Path.cwd() / "src" / "resources" / "serpro.png",
        Path("/app/src/resources/serpro.png"),
    ]

    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


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


def _agora_brasilia() -> datetime:
    """Retorna horário atual ajustado para Brasília."""
    if ZoneInfo is not None:
        return datetime.now(timezone.utc).astimezone(ZoneInfo("America/Sao_Paulo"))
    # Fallback para ambientes sem zoneinfo
    return datetime.utcnow() - timedelta(hours=3)


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
    issuer_name = "ICP-Brasil"
    cert_tipo = "ICP-Brasil"
    referencia = str(cert.serial_number)
    titular = common_name
    try:
        common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except Exception:
        pass

    try:
        issuer_name = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    except Exception:
        pass

    try:
        cert_tipo = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
    except Exception:
        pass

    try:
        ou_value = cert.subject.get_attributes_for_oid(NameOID.ORGANIZATIONAL_UNIT_NAME)[0].value
        match_ref = re.search(r"refer[eê]ncia\s+(\d+)", ou_value, flags=re.IGNORECASE)
        if match_ref:
            referencia = match_ref.group(1)
    except Exception:
        pass

    titular = common_name.split(":")[0].strip()
    serial = hex(cert.serial_number)[2:].upper()
    serial_curto = serial[-16:] if len(serial) > 16 else serial
    return {
        "common_name": common_name,
        "serial": serial_curto,
        "titular": titular,
        "issuer_name": issuer_name,
        "cert_tipo": cert_tipo,
        "referencia": referencia,
    }


def _aplicar_assinatura_visual(
    caminho_pdf: Path,
    dados_cert: dict[str, str],
    texto_assinatura: str,
    *,
    anchor_x: float | None = None,
    anchor_y: float | None = None,
) -> None:
    """Aplica selo visual com layout leve usando a imagem SERPRO."""
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

        # Selo visual ancorado acima da linha do diretor (escala reduzida em 50%).
        scale = 0.5

        def s(value: float) -> float:
            return value * scale

        assinatura_largura = s(390)
        assinatura_altura = s(90)
        base_x = (anchor_x - (assinatura_largura / 2)) if anchor_x else (largura - assinatura_largura - 54)
        base_y = (anchor_y + s(8)) if anchor_y else 78
        assinatura_x = max(36, min(base_x, largura - assinatura_largura - 36))
        assinatura_y = max(36, min(base_y, altura - assinatura_altura - 36))

        c = canvas.Canvas(str(overlay_path), pagesize=(largura, altura))
        c.setFillColorRGB(0.96, 0.97, 0.99)
        c.setStrokeColorRGB(0.60, 0.71, 0.86)
        c.setLineWidth(1)
        c.roundRect(assinatura_x, assinatura_y, assinatura_largura, assinatura_altura, s(7), stroke=1, fill=1)

        logo_box_w = s(76)
        logo_box_h = assinatura_altura - s(16)
        logo_box_x = assinatura_x + s(8)
        logo_box_y = assinatura_y + s(8)
        c.setStrokeColorRGB(0.86, 0.89, 0.95)
        c.setFillColorRGB(0.96, 0.97, 0.99)
        c.rect(logo_box_x, logo_box_y, logo_box_w, logo_box_h, stroke=1, fill=1)

        serpro_img = _resolver_caminho_serpro()
        if serpro_img:
            c.drawImage(
                str(serpro_img),
                logo_box_x + s(8),
                logo_box_y + s(8),
                width=s(60),
                height=logo_box_h - s(16),
                preserveAspectRatio=True,
                mask="auto",
            )

        texto_x = logo_box_x + logo_box_w + s(12)
        c.setFillColorRGB(0.05, 0.30, 0.66)
        c.setFont("Helvetica-Bold", s(12))
        c.drawString(texto_x, assinatura_y + s(68), "ASSINATURA ELETRÔNICA")

        c.setFillColorRGB(0.1, 0.15, 0.25)
        c.setFont("Helvetica", s(8.7))
        c.drawString(texto_x, assinatura_y + s(52), f"Documento assinado eletronicamente por {dados_cert['titular'][:42]}")
        c.drawString(
            texto_x,
            assinatura_y + s(39),
            f"Em {_agora_brasilia().strftime('%d/%m/%Y %H:%M:%S')} (horário oficial de Brasília)",
        )
        c.drawString(
            texto_x,
            assinatura_y + s(26),
            f"Certificado: {dados_cert['cert_tipo'][:16]} | {dados_cert['issuer_name'][:40]}",
        )
        c.drawString(
            texto_x,
            assinatura_y + s(13),
            f"Referência: {dados_cert['referencia']}",
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
                        box=(0, 0, 0, 0),
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
    anchor_x: float | None = None,
    anchor_y: float | None = None,
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

    _aplicar_assinatura_visual(
        destino,
        dados_certificado,
        texto_assinatura,
        anchor_x=anchor_x,
        anchor_y=anchor_y,
    )
    assinatura_criptografica_ok = _aplicar_assinatura_criptografica(
        destino,
        caminho_certificado,
        senha_certificado,
    )
    if not assinatura_criptografica_ok:
        print("⚠️ pyhanko não disponível; aplicado somente bloco visual da assinatura do certificado.")

    return str(destino)
