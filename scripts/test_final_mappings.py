"""
Script final para testar todos os mapeamentos corrigidos.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.services.social_data_service import SocialDataService

def test_mappings():
    print("=" * 80)
    print("TESTE FINAL DE MAPEAMENTOS CORRIGIDOS")
    print("=" * 80)
    
    try:
        # Obter amostra de dados
        resultado = SocialDataService.get_dados_sociais(pagina=1, por_pagina=10)
        
        print(f"\n✅ Serviço funcionando - {resultado.total} registros totais")
        print(f"\n📋 Testando mapeamento dos primeiros 10 registros:\n")
        
        # Contadores para validação
        trabalho_mapeado = 0
        acesso_internet_mapeado = 0
        cor_etnia_mapeada = 0
        deslocamento_mapeado = 0
        estresse_mapeado = 0
        escolaridade_pai_mapeada = 0
        escolaridade_mae_mapeada = 0
        tipo_moradia_mapeada = 0
        
        for i, dado in enumerate(resultado.dados, 1):
            print(f"Registro {i}:")
            print(f"  - Matrícula: {dado.matricula}")
            print(f"  - Trabalho: {dado.trabalho.value if dado.trabalho else '❌ VAZIO'}")
            print(f"  - Acesso Internet: {dado.acesso_internet.value if dado.acesso_internet else '❌ VAZIO'}")
            print(f"  - Cor/Etnia: {dado.cor_etnia.value if dado.cor_etnia else '❌ VAZIO'}")
            print(f"  - Deslocamento: {dado.deslocamento.value if dado.deslocamento else '❌ VAZIO'}")
            print(f"  - Estresse: {dado.estresse.value if dado.estresse else '❌ VAZIO'}")
            print(f"  - Escolaridade Pai: {dado.escolaridade_pai.value if dado.escolaridade_pai else '❌ VAZIO'}")
            print(f"  - Escolaridade Mãe: {dado.escolaridade_mae.value if dado.escolaridade_mae else '❌ VAZIO'}")
            print(f"  - Tipo Moradia: {dado.tipo_moradia.value if dado.tipo_moradia else '❌ VAZIO'}")
            print()
            
            # Contadores
            if dado.trabalho:
                trabalho_mapeado += 1
            if dado.acesso_internet:
                acesso_internet_mapeado += 1
            if dado.cor_etnia:
                cor_etnia_mapeada += 1
            if dado.deslocamento:
                deslocamento_mapeado += 1
            if dado.estresse:
                estresse_mapeado += 1
            if dado.escolaridade_pai:
                escolaridade_pai_mapeada += 1
            if dado.escolaridade_mae:
                escolaridade_mae_mapeada += 1
            if dado.tipo_moradia:
                tipo_moradia_mapeada += 1
        
        # Resultados
        total_registros = len(resultado.dados)
        print("=" * 80)
        print("RESUMO DO MAPEAMENTO:")
        print("=" * 80)
        print(f"✅ Trabalho mapeado: {trabalho_mapeado}/{total_registros} ({trabalho_mapeado/total_registros*100:.1f}%)")
        print(f"✅ Acesso Internet mapeado: {acesso_internet_mapeado}/{total_registros} ({acesso_internet_mapeado/total_registros*100:.1f}%)")
        print(f"✅ Cor/Etnia mapeada: {cor_etnia_mapeada}/{total_registros} ({cor_etnia_mapeada/total_registros*100:.1f}%)")
        print(f"✅ Deslocamento mapeado: {deslocamento_mapeado}/{total_registros} ({deslocamento_mapeado/total_registros*100:.1f}%)")
        print(f"✅ Estresse mapeado: {estresse_mapeado}/{total_registros} ({estresse_mapeado/total_registros*100:.1f}%)")
        print(f"✅ Escolaridade Pai mapeada: {escolaridade_pai_mapeada}/{total_registros} ({escolaridade_pai_mapeada/total_registros*100:.1f}%)")
        print(f"✅ Escolaridade Mãe mapeada: {escolaridade_mae_mapeada}/{total_registros} ({escolaridade_mae_mapeada/total_registros*100:.1f}%)")
        print(f"✅ Tipo Moradia mapeada: {tipo_moradia_mapeada}/{total_registros} ({tipo_moradia_mapeada/total_registros*100:.1f}%)")
        
        # Verificar se todos os campos estão 100% mapeados
        if all([
            trabalho_mapeado == total_registros,
            acesso_internet_mapeado == total_registros,
            cor_etnia_mapeada == total_registros,
            deslocamento_mapeado == total_registros,
            estresse_mapeado == total_registros,
            escolaridade_pai_mapeada == total_registros,
            escolaridade_mae_mapeada == total_registros,
            tipo_moradia_mapeada == total_registros
        ]):
            print("\n🎉 SUCESSO! Todos os campos problemáticos estão 100% mapeados!")
        else:
            print("\n⚠️ Alguns campos ainda têm valores vazios. Verifique os enums.")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mappings()
