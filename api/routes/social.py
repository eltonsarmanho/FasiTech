"""
Rotas da API para dados sociais.
Fornece endpoints para consulta de dados sociais com filtros, paginação e estatísticas.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
import os

from src.services.social_data_service import SocialDataService
from src.models.schemas import (
    DadosSociaisResponse,
    EstatisticasSociais,
    FiltrosDadosSociais,
    CorEtnia,
    SimNao,
    Genero,
    PoloSocial,
    TipoRenda,
    TipoDeslocamento,
    TipoTrabalho,
    QualidadeAssistencia,
    TipoMoradia,
    AcessoInternet
)
from api.dependencies import get_auth_dependency, get_raw_social_read_permission

router = APIRouter()


@router.get(
    "/dados-sociais",
    response_model=DadosSociaisResponse,
    summary="Consultar dados sociais",
    description="Obtém dados sociais dos estudantes com suporte a paginação e filtros avançados.",
    response_description="Lista paginada de dados sociais com metadados de paginação"
)
async def get_dados_sociais(
    pagina: int = Query(1, ge=1, description="Número da página (início em 1)"),
    por_pagina: int = Query(20, ge=1, le=100, description="Registros por página (máximo 100)"),
    periodo: Optional[str] = Query(None, description="Filtrar por período letivo"),
    genero: Optional[Genero] = Query(None, description="Filtrar por gênero"),
    polo: Optional[PoloSocial] = Query(None, description="Filtrar por polo"),
    cor_etnia: Optional[CorEtnia] = Query(None, description="Filtrar por cor/etnia"),
    pcd: Optional[SimNao] = Query(None, description="Filtrar por PCD"),
    renda: Optional[TipoRenda] = Query(None, description="Filtrar por faixa de renda"),
    deslocamento: Optional[TipoDeslocamento] = Query(None, description="Filtrar por meio de deslocamento"),
    trabalho: Optional[TipoTrabalho] = Query(None, description="Filtrar por situação de trabalho"),
    assistencia_estudantil: Optional[QualidadeAssistencia] = Query(None, description="Filtrar por qualidade da assistência estudantil"),
    tipo_moradia: Optional[TipoMoradia] = Query(None, description="Filtrar por tipo de moradia"),
    _: None = Depends(get_auth_dependency)
) -> DadosSociaisResponse:
    """
    Consulta dados sociais dos estudantes com filtros opcionais.
    
    **Parâmetros de Paginação:**
    - `pagina`: Número da página desejada (padrão: 1)
    - `por_pagina`: Quantidade de registros por página (padrão: 20, máximo: 100)
    
    **Filtros Disponíveis:**
    - `periodo`: Período letivo (ex: "2025.(3 e 4)")
    - `cor_etnia`: Cor/etnia do estudante
    - `pcd`: Se é pessoa com deficiência
    - `renda`: Faixa de renda familiar
    - `deslocamento`: Meio de deslocamento principal
    - `trabalho`: Se trabalha atualmente
    - `assistencia_estudantil`: Qualidade da assistência estudantil
    - `tipo_moradia`: Tipo de moradia
    
    **Retorna:**
    - Lista paginada de dados sociais
    - Metadados de paginação (total, páginas, etc.)
    """
    try:
        # Criar objeto de filtros
        filtros = FiltrosDadosSociais(
            periodo=periodo,
            genero=genero,
            polo=polo,
            cor_etnia=cor_etnia,
            pcd=pcd,
            renda=renda,
            deslocamento=deslocamento,
            trabalho=trabalho,
            assistencia_estudantil=assistencia_estudantil,
            tipo_moradia=tipo_moradia
        )
        
        # Obter dados do serviço
        resultado = SocialDataService.get_dados_sociais(
            pagina=pagina,
            por_pagina=por_pagina,
            filtros=filtros
        )

        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar dados sociais: {str(e)}"
        )


@router.get(
    "/_dev/raw-social-data",
    response_model=DadosSociaisResponse,
    summary="Consulta secreta de dados sociais sem anonimização",
    description="Endpoint reservado para DEV externo consultar dados sociais com matrícula original.",
    include_in_schema=False
)
async def get_dados_sociais_raw_dev(
    pagina: int = Query(1, ge=1, description="Número da página (início em 1)"),
    por_pagina: int = Query(20, ge=1, le=100, description="Registros por página (máximo 100)"),
    periodo: Optional[str] = Query(None, description="Filtrar por período letivo"),
    genero: Optional[Genero] = Query(None, description="Filtrar por gênero"),
    polo: Optional[PoloSocial] = Query(None, description="Filtrar por polo"),
    cor_etnia: Optional[CorEtnia] = Query(None, description="Filtrar por cor/etnia"),
    pcd: Optional[SimNao] = Query(None, description="Filtrar por PCD"),
    renda: Optional[TipoRenda] = Query(None, description="Filtrar por faixa de renda"),
    deslocamento: Optional[TipoDeslocamento] = Query(None, description="Filtrar por meio de deslocamento"),
    trabalho: Optional[TipoTrabalho] = Query(None, description="Filtrar por situação de trabalho"),
    assistencia_estudantil: Optional[QualidadeAssistencia] = Query(None, description="Filtrar por assistência estudantil"),
    tipo_moradia: Optional[TipoMoradia] = Query(None, description="Filtrar por tipo de moradia"),
    _: None = Depends(get_raw_social_read_permission)
) -> DadosSociaisResponse:
    """
    Endpoint secreto para consulta não anonimizada.

    Requer API key com permissão `read_raw_social`.
    """
    try:
        filtros = FiltrosDadosSociais(
            periodo=periodo,
            genero=genero,
            polo=polo,
            cor_etnia=cor_etnia,
            pcd=pcd,
            renda=renda,
            deslocamento=deslocamento,
            trabalho=trabalho,
            assistencia_estudantil=assistencia_estudantil,
            tipo_moradia=tipo_moradia
        )

        return SocialDataService.get_dados_sociais(
            pagina=pagina,
            por_pagina=por_pagina,
            filtros=filtros,
            anonymize_matricula=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar dados sociais brutos: {str(e)}"
        )


@router.get(
    "/dados-sociais/estatisticas",
    response_model=EstatisticasSociais,
    summary="Estatísticas dos dados sociais",
    description="Obtém estatísticas agregadas dos dados sociais dos estudantes.",
    response_description="Estatísticas e distribuições dos dados sociais"
)
async def get_estatisticas_sociais(
    _: None = Depends(get_auth_dependency)
) -> EstatisticasSociais:
    """
    Obtém estatísticas agregadas dos dados sociais.
    
    **Retorna estatísticas sobre:**
    - Total de registros
    - Distribuição por cor/etnia
    - Distribuição por faixa de renda
    - Percentual de pessoas com deficiência
    - Percentual que trabalha
    - Distribuição por meio de deslocamento
    - Média de dispositivos por residência
    - Avaliação da qualidade da assistência estudantil
    
    **Dados em Cache:**
    As estatísticas são calculadas e armazenadas em cache por 30 minutos
    para otimizar o desempenho.
    """
    try:
        resultado = SocialDataService.get_estatisticas()
        return resultado
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular estatísticas: {str(e)}"
        )


@router.get(
    "/dados-sociais/opcoes",
    summary="Opções de filtros disponíveis",
    description="Retorna as opções disponíveis para cada campo de filtro.",
    response_description="Dicionário com as opções de filtro por campo"
)
async def get_opcoes_filtros(
    _: None = Depends(get_auth_dependency)
) -> dict:
    """
    Retorna as opções disponíveis para filtros.
    
    **Útil para:**
    - Construir interfaces de usuário dinâmicas
    - Validar valores de filtro
    - Documentar opções disponíveis
    
    **Retorna:**
    Dicionário com as opções para cada tipo de filtro.
    """
    return {
        "genero": [item.value for item in Genero],
        "polo": [item.value for item in PoloSocial],
        "cor_etnia": [item.value for item in CorEtnia],
        "pcd": [item.value for item in SimNao],
        "renda": [item.value for item in TipoRenda],
        "deslocamento": [item.value for item in TipoDeslocamento],
        "trabalho": [item.value for item in TipoTrabalho],
        "assistencia_estudantil": [item.value for item in QualidadeAssistencia],
        "tipo_moradia": [item.value for item in TipoMoradia],
        "acesso_internet": [item.value for item in AcessoInternet]
    }


@router.post(
    "/dados-sociais/cache/clear",
    summary="Limpar cache",
    description="Remove todos os dados em cache, forçando nova consulta na próxima requisição.",
    response_description="Confirmação da limpeza do cache"
)
async def clear_cache(
    _: None = Depends(get_auth_dependency)
) -> JSONResponse:
    """
    Limpa o cache do serviço de dados sociais.
    
    **Uso recomendado:**
    - Quando há suspeita de dados desatualizados
    - Após atualizações na planilha fonte
    - Para debugging
    
    **Efeito:**
    A próxima consulta será feita diretamente na planilha,
    ignorando dados em cache.
    """
    try:
        SocialDataService.clear_cache()
        return JSONResponse(
            status_code=200,
            content={"message": "Cache limpo com sucesso"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao limpar cache: {str(e)}"
        )


@router.get(
    "/dados-sociais/cache/info",
    summary="Informações do cache",
    description="Retorna informações sobre o estado atual do cache.",
    response_description="Detalhes sobre entradas em cache e configurações"
)
async def get_cache_info(
    _: None = Depends(get_auth_dependency)
) -> dict:
    """
    Obtém informações sobre o cache atual.
    
    **Retorna:**
    - Número total de entradas em cache
    - Lista de chaves em cache
    - Tempo de vida (TTL) configurado
    
    **Útil para:**
    - Monitoramento do desempenho
    - Debugging
    - Verificar se o cache está funcionando
    """
    try:
        info = SocialDataService.get_cache_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter informações do cache: {str(e)}"
        )


@router.get(
    "/dados-sociais/health",
    summary="Verificação de saúde",
    description="Verifica se o serviço consegue acessar a planilha de dados sociais.",
    response_description="Status da conexão com a planilha"
)
async def health_check(
    _: None = Depends(get_auth_dependency)
) -> JSONResponse:
    """
    Verifica a saúde do serviço de dados sociais.
    
    **Testa:**
    - Acesso à planilha Google Sheets
    - Funcionamento básico do serviço
    - Conectividade com APIs do Google
    
    **Retorna:**
    - Status OK se tudo funcionando
    - Erro detalhado em caso de problemas
    """
    try:
        # Tentar carregar uma pequena amostra dos dados
        resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=1)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "Serviço funcionando corretamente",
                "total_registros": resultado.total,
                "ultima_verificacao": f"{resultado.dados[0].data_hora}" if resultado.dados else None
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": f"Serviço indisponível: {str(e)}"
            }
        )


@router.get(
    "/dados-sociais/download/csv",
    summary="Download dos dados sociais em CSV",
    description="Baixa todos os dados sociais em formato CSV para análise offline.",
    response_description="Arquivo CSV com todos os dados sociais",
    tags=["download-publico"]
)
async def download_dados_csv():
    """
    Download de todos os dados sociais em formato CSV.
    
    **Formato do arquivo:**
    - Separador: vírgula (,)
    - Codificação: UTF-8
    - Cabeçalhos em português
    - Todos os campos disponíveis (sem Data/Hora)
    
    **Uso:**
    - Análise offline dos dados
    - Importação em Excel/Google Sheets
    - Processamento em R/Python
    
    **Acesso:**
    Endpoint público (não requer autenticação)
    """
    try:
        from fastapi.responses import StreamingResponse
        import pandas as pd
        import io
        from datetime import datetime
        
        # Obter todos os dados (sem paginação)
        resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=1000)
        
        if not resultado.dados:
            raise HTTPException(
                status_code=404,
                detail="Nenhum dado social encontrado"
            )
        
        # Converter para DataFrame (removido Data/Hora)
        dados_dict = []
        for item in resultado.dados:
            dados_dict.append({
                'ID_Anonimo': item.matricula,  # Campo anonimizado para LGPD
                'Período': item.periodo,
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
                'Acompanhamento': item.acompanhamento or '',
                'Escolaridade Pai': item.escolaridade_pai.value if item.escolaridade_pai else '',
                'Escolaridade Mãe': item.escolaridade_mae.value if item.escolaridade_mae else '',
                'Qtd Computador': item.qtd_computador or 0,
                'Qtd Celular': item.qtd_celular or 0,
                'Computador Próprio': item.computador_proprio.value if item.computador_proprio else '',
                'Acesso Internet': item.acesso_internet.value if item.acesso_internet else '',
                'Tipo Moradia': item.tipo_moradia.value if item.tipo_moradia else ''
            })
        
        df = pd.DataFrame(dados_dict)
        
        # Criar arquivo CSV em memória
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"dados_sociais_fasitech_{timestamp}.csv"
        
        # Retornar como download
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type='text/csv',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar arquivo CSV: {str(e)}"
        )


@router.get(
    "/dados-sociais/download/excel",
    summary="Download dos dados sociais em Excel",
    description="Baixa todos os dados sociais em formato Excel (.xlsx) para análise offline.",
    response_description="Arquivo Excel com todos os dados sociais",
    tags=["download-publico"]
)
async def download_dados_excel():
    """
    Download de todos os dados sociais em formato Excel.
    
    **Formato do arquivo:**
    - Formato: Excel (.xlsx)
    - Planilha única com todos os dados
    - Cabeçalhos formatados
    - Filtros automáticos habilitados
    - Data/Hora removida conforme requisição
    
    **Uso:**
    - Análise em Excel
    - Relatórios formatados
    - Dashboards
    
    **Acesso:**
    Endpoint público (não requer autenticação)
    """
    try:
        from fastapi.responses import StreamingResponse
        import pandas as pd
        import io
        from datetime import datetime
        
        # Obter todos os dados (sem paginação)
        resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=1000)
        
        if not resultado.dados:
            raise HTTPException(
                status_code=404,
                detail="Nenhum dado social encontrado"
            )
        
        # Converter para DataFrame (removido Data/Hora)
        dados_dict = []
        for item in resultado.dados:
            dados_dict.append({
                'ID_Anonimo': item.matricula,  # Campo anonimizado para LGPD
                'Período': item.periodo,
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
                'Acompanhamento': item.acompanhamento or '',
                'Escolaridade Pai': item.escolaridade_pai.value if item.escolaridade_pai else '',
                'Escolaridade Mãe': item.escolaridade_mae.value if item.escolaridade_mae else '',
                'Qtd Computador': item.qtd_computador or 0,
                'Qtd Celular': item.qtd_celular or 0,
                'Computador Próprio': item.computador_proprio.value if item.computador_proprio else '',
                'Acesso Internet': item.acesso_internet.value if item.acesso_internet else '',
                'Tipo Moradia': item.tipo_moradia.value if item.tipo_moradia else ''
            })
        
        df = pd.DataFrame(dados_dict)
        
        # Criar arquivo Excel em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados Sociais', index=False)
            
            # Formatação básica
            worksheet = writer.sheets['Dados Sociais']
            
            # Auto-ajustar largura das colunas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Máximo 50 chars
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Adicionar filtros automáticos
            worksheet.auto_filter.ref = worksheet.dimensions
        
        output.seek(0)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"dados_sociais_fasitech_{timestamp}.xlsx"
        
        # Retornar como download
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar arquivo Excel: {str(e)}"
        )


@router.get(
    "/dados-sociais/download",
    response_class=HTMLResponse,
    summary="Página de download dos dados sociais",
    description="Página web simples para download dos dados sociais em CSV ou Excel.",
    tags=["download-publico"],
    include_in_schema=False  # Não incluir na documentação Swagger
)
async def pagina_download():
    """
    Página HTML para download dos dados sociais.
    
    **Funcionalidades:**
    - Interface amigável
    - Download direto em CSV ou Excel
    - Informações sobre os dados disponíveis
    - Responsiva para mobile
    
    **Acesso:**
    Página pública (não requer autenticação)
    """
    try:
        # Caminho para o arquivo HTML
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "templates", 
            "download_page.html"
        )
        
        # Ler o arquivo HTML
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        else:
            # HTML inline caso o arquivo não exista
            html_content = """
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>FasiTech - Dados Sociais</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
                    h1 { color: #333; }
                    .download-btn { display: inline-block; margin: 10px; padding: 15px 30px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
                    .download-btn:hover { background: #0056b3; }
                    .info { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1>FasiTech - Dados Sociais</h1>
                <div class="info">
                    <h3>Dados Disponíveis:</h3>
                    <p>49 registros de estudantes com informações demográficas, socioeconômicas e de bem-estar.</p>
                </div>
                <a href="/api/v1/dados-sociais/download/csv" class="download-btn">📄 Baixar CSV</a>
                <a href="/api/v1/dados-sociais/download/excel" class="download-btn">📊 Baixar Excel</a>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar página de download: {str(e)}"
        )
