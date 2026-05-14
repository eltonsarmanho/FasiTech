from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException, status
from backend.config.settings import settings

router = APIRouter()
_URL_RE = re.compile(r'https?://\S+')


_BOOL_TRUE = {'true', 'sim', 'confirmado', 'ok', '1', 'yes'}
_BOOL_FALSE = {'false', 'não', 'nao', 'pendente', '0', 'no'}


def _cell_value(val, col_name: str = '') -> dict:
    s = str(val).strip() if val is not None else ''
    if s in ('nan', 'None', 'NaN'):
        s = ''
    if col_name == 'Plano de Ensino':
        sl = s.lower()
        if sl in _BOOL_TRUE:
            return {"text": '✅', "url": None}
        if sl in _BOOL_FALSE:
            return {"text": '❌', "url": None}
    m = _URL_RE.search(s)
    if m:
        return {"text": s[:m.start()].strip() or m.group(), "url": m.group()}
    return {"text": s, "url": None}


@router.get("/ofertas-disciplinas")
async def get_ofertas_disciplinas():
    sheet_id = settings.ofertas_sheet_id
    if not sheet_id:
        return {"abas_oferta": [], "abas_grade": [], "mensagem": "Planilha não configurada"}
    try:
        from backend.infrastructure.google.sheets import get_sheet_tabs, read_sheet_tab
        tabs = get_sheet_tabs(sheet_id)
        if not tabs:
            return {"abas_oferta": [], "abas_grade": [], "mensagem": "Nenhuma aba encontrada na planilha"}

        abas_oferta: list = []
        abas_grade: list = []

        for tab_name in tabs:
            try:
                df = read_sheet_tab(sheet_id, tab_name)
                df.dropna(how='all', inplace=True)
                if df.empty:
                    continue
                colunas = list(df.columns)
                rows = [{col: _cell_value(row.get(col), col) for col in colunas} for _, row in df.iterrows()]
                tab_data = {"aba": tab_name, "colunas": colunas, "dados": rows}
                if tab_name[0].isdigit() or tab_name.lower().startswith("grade"):
                    abas_grade.append(tab_data)
                else:
                    abas_oferta.append(tab_data)
            except Exception:
                continue

        return {"abas_oferta": abas_oferta, "abas_grade": abas_grade}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Erro ao carregar ofertas: {e}")
