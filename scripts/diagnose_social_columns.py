"""
Script para diagnosticar os nomes exatos das colunas na planilha social
e verificar valores de exemplo para cada campo problemático.
"""

import sys
from pathlib import Path

# Adicionar diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.services.google_sheets import read_sheet_tab
import pandas as pd

SOCIAL_SHEET_ID = "1mn9zvNtG-Df_hMCen1M-cWlQl2QtfgFUr0tBg436giE"
SOCIAL_SHEET_TAB = "Pagina1"

def diagnose_columns():
    """Diagnostica os nomes exatos das colunas e valores de exemplo."""
    
    print("=" * 80)
    print("DIAGNÓSTICO DA PLANILHA SOCIAL")
    print("=" * 80)
    
    try:
        # Carregar dados
        print(f"\n📊 Carregando dados de: {SOCIAL_SHEET_ID} - Aba: {SOCIAL_SHEET_TAB}")
        df = read_sheet_tab(SOCIAL_SHEET_ID, SOCIAL_SHEET_TAB)
        
        print(f"\n✅ Dados carregados com sucesso!")
        print(f"📈 Total de linhas: {len(df)}")
        print(f"📋 Total de colunas: {len(df.columns)}")
        
        # Mostrar todas as colunas
        print("\n" + "=" * 80)
        print("COLUNAS ENCONTRADAS NA PLANILHA:")
        print("=" * 80)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. [{col}]")
        
        # Campos problemáticos relatados
        campos_problematicos = [
            'Estresse',
            'Escolaridade Pai',
            'Escolaridade Mãe',
            'Acesso Internet',
            'Tipo Moradia',
            'Cor/Etnia',
            'Deslocamento'
        ]
        
        print("\n" + "=" * 80)
        print("ANÁLISE DOS CAMPOS PROBLEMÁTICOS:")
        print("=" * 80)
        
        for campo in campos_problematicos:
            print(f"\n🔍 Campo: [{campo}]")
            
            # Verificar variações do nome
            possibilidades = [
                campo,
                campo.lower(),
                campo.upper(),
                campo.replace(' ', ''),
                campo.replace('/', '_'),
                campo.replace('/', ' '),
            ]
            
            encontrado = False
            for poss in possibilidades:
                if poss in df.columns:
                    print(f"   ✅ Encontrado como: [{poss}]")
                    print(f"   📊 Valores únicos: {df[poss].nunique()}")
                    print(f"   📝 Valores nulos: {df[poss].isna().sum()} ({df[poss].isna().sum()/len(df)*100:.1f}%)")
                    print(f"   🔢 Exemplos de valores:")
                    
                    # Mostrar valores únicos (primeiros 10)
                    valores_unicos = df[poss].dropna().unique()[:10]
                    for v in valores_unicos:
                        print(f"      - [{v}]")
                    
                    encontrado = True
                    break
            
            if not encontrado:
                print(f"   ❌ Não encontrado! Possíveis variações testadas:")
                for poss in possibilidades:
                    print(f"      - [{poss}]")
                
                # Sugerir colunas similares
                colunas_similares = [col for col in df.columns if campo.lower() in col.lower() or col.lower() in campo.lower()]
                if colunas_similares:
                    print(f"   💡 Colunas com nomes similares:")
                    for col in colunas_similares:
                        print(f"      - [{col}]")
        
        # Verificar uma amostra completa dos dados
        print("\n" + "=" * 80)
        print("AMOSTRA DE DADOS (primeiras 3 linhas):")
        print("=" * 80)
        print(df.head(3).to_string())
        
        # Verificar tipos de dados
        print("\n" + "=" * 80)
        print("TIPOS DE DADOS:")
        print("=" * 80)
        print(df.dtypes)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_columns()
