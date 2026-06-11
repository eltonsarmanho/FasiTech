from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
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


@router.get("/dados-sociais/dashboard")
async def get_dashboard(
    polo: Optional[str] = Query(None),
    periodo: Optional[str] = Query(None),
):
    import pandas as pd

    df = SocialDataService._load_raw_data()

    polos: list = []
    periodos: list = []

    if not df.empty:
        polos = sorted(df["Polo"].dropna().unique().tolist())
        periodos = sorted(df["Periodo"].dropna().unique().tolist(), reverse=True)
        if polo:
            df = df[df["Polo"] == polo]
        if periodo:
            df = df[df["Periodo"] == periodo]

    total = len(df)

    if total == 0:
        return {
            "total": 0,
            "pct_pcd": 0.0,
            "pct_assistencia": 0.0,
            "saude_media": None,
            "polos": polos,
            "periodos": periodos,
            "distribuicoes": {k: {} for k in [
                "genero", "cor_etnia", "renda", "moradia", "trabalho",
                "deslocamento", "acesso_internet", "saude_mental",
                "assistencia_estudantil", "escolaridade_pai", "escolaridade_mae",
            ]},
        }

    def dist(col: str) -> dict:
        if col not in df.columns:
            return {}
        return {str(k): int(v) for k, v in df[col].value_counts().items()}

    pcd_count = int((df["PCD"] == "Sim").sum()) if "PCD" in df.columns else 0
    pct_pcd = round(pcd_count / total * 100, 1)

    assist_count = int((df["Assistência Estudantil"] == "Sim").sum()) if "Assistência Estudantil" in df.columns else 0
    pct_assistencia = round(assist_count / total * 100, 1)

    saude_map = {"Muito boa": 5, "Boa": 4, "Regular": 3, "Ruim": 2, "Muito ruim": 1}
    saude_scores = df["Saúde Mental"].map(saude_map).dropna() if "Saúde Mental" in df.columns else pd.Series(dtype=float)
    saude_media = round(float(saude_scores.mean()), 2) if len(saude_scores) > 0 else None

    return {
        "total": total,
        "pct_pcd": pct_pcd,
        "pct_assistencia": pct_assistencia,
        "saude_media": saude_media,
        "polos": polos,
        "periodos": periodos,
        "distribuicoes": {
            "genero": dist("Genero"),
            "cor_etnia": dist("Cor/Etnia"),
            "renda": dist("Renda"),
            "moradia": dist("Tipo Moradia"),
            "trabalho": dist("Trabalho"),
            "deslocamento": dist("Deslocamento"),
            "acesso_internet": dist("Acesso Internet"),
            "saude_mental": dist("Saúde Mental"),
            "assistencia_estudantil": dist("Assistência Estudantil"),
            "escolaridade_pai": dist("Escolaridade Pai"),
            "escolaridade_mae": dist("Escolaridade Mãe"),
        },
    }


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
