from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse

from backend.infrastructure.database.social_data_service import SocialDataService

router = APIRouter()


def _build_rows(dados):
    rows = []
    for item in dados:
        rows.append({
            'ID_Anonimo': item.matricula,
            'Período': item.periodo,
            'Genero': item.genero.value if item.genero else '',
            'Polo': item.polo.value if item.polo else '',
            'Cor/Etnia': item.cor_etnia.value if item.cor_etnia else '',
            'PCD': item.pcd.value if item.pcd else '',
            'Tipo de Deficiência': item.tipo_deficiencia or '',
            'Renda': item.renda.value if item.renda else '',
            'Deslocamento': item.deslocamento.value if item.deslocamento else '',
            'Trabalho': item.trabalho.value if item.trabalho else '',
            'Assistência Estudantil': item.assistencia_estudantil.value if item.assistencia_estudantil else '',
            'Gasto Internet': item.gasto_internet.value if item.gasto_internet else '',
            'Saúde Mental': item.saude_mental.value if item.saude_mental else '',
            'Estresse': item.estresse.value if item.estresse else '',
            'Tipo Moradia': item.tipo_moradia.value if item.tipo_moradia else '',
            'Acesso Internet': item.acesso_internet.value if item.acesso_internet else '',
        })
    return rows


@router.get("/dados-sociais/download", response_class=HTMLResponse, include_in_schema=False)
async def pagina_download():
    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>FasiTech — Dados Sociais</title>
  <style>
    body{font-family:Arial,sans-serif;max-width:700px;margin:60px auto;text-align:center;color:#333}
    h1{color:#1a3c6e}
    .btn{display:inline-block;margin:10px;padding:14px 28px;background:#1a3c6e;color:#fff;
         text-decoration:none;border-radius:6px;font-size:15px}
    .btn:hover{background:#0f2549}
    .info{background:#f4f6fb;padding:20px;border-radius:8px;margin:24px 0;text-align:left}
  </style>
</head>
<body>
  <h1>Dados Sociais — FASI/UFPA</h1>
  <div class="info">
    <p>Dados socioeconômicos dos discentes, anonimizados conforme LGPD.</p>
  </div>
  <a href="/api/v1/dados-sociais/download/csv" class="btn">📄 Baixar CSV</a>
  <a href="/api/v1/dados-sociais/download/excel" class="btn">📊 Baixar Excel</a>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/dados-sociais/download/csv")
async def download_csv():
    import pandas as pd
    resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=2000)
    df = pd.DataFrame(_build_rows(resultado.dados))
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding='utf-8')
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={"Content-Disposition": f"attachment; filename=dados_sociais_{ts}.csv"},
    )


@router.get("/dados-sociais/download/excel")
async def download_excel():
    import pandas as pd
    resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=2000)
    df = pd.DataFrame(_build_rows(resultado.dados))
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Dados Sociais', index=False)
        ws = writer.sheets['Dados Sociais']
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or '')) for c in col) + 2, 50
            )
        ws.auto_filter.ref = ws.dimensions
    buf.seek(0)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    return StreamingResponse(
        buf,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment; filename=dados_sociais_{ts}.xlsx"},
    )
