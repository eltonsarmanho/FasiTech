#!/usr/bin/env python3
"""
Script de teste para validar o endpoint DELETE de requerimento TCC.
"""

import sys
from backend.infrastructure.database.repository import (
    list_requerimento_tcc_submissions,
    get_requerimento_tcc_submission,
    get_requerimento_tcc_drive_info,
)

def test_delete_endpoint():
    """Testa se as funções necessárias para DELETE funcionam."""

    print("=" * 60)
    print("TESTE: Endpoint DELETE /requerimento-tcc/{submission_id}")
    print("=" * 60)

    # 1. Listar requerimentos
    print("\n1. Listando requerimentos TCC...")
    result = list_requerimento_tcc_submissions(pagina=1, por_pagina=200)
    items = result.get("items", [])
    print(f"   Total de requerimentos: {result.get('total')}")

    if not items:
        print("   ❌ Nenhum requerimento encontrado")
        return False

    # Procurar por IGOR GAIA TAVARES
    igor = next((r for r in items if "IGOR" in r.get("nome_aluno", "").upper()), None)
    if igor:
        submission_id = igor["id"]
        print(f"   ✅ Encontrado: {igor['nome_aluno']} (ID: {submission_id})")
    else:
        # Usar o primeiro requerimento
        submission_id = items[0]["id"]
        print(f"   Usando primeiro requerimento: {items[0]['nome_aluno']} (ID: {submission_id})")

    # 2. Obter detalhes do requerimento
    print(f"\n2. Obtendo detalhes do requerimento {submission_id}...")
    try:
        row = get_requerimento_tcc_submission(submission_id)
        if row:
            print(f"   ✅ Requerimento encontrado: {row.get('nome_aluno')}")
            print(f"      Matrícula: {row.get('matricula')}")
            print(f"      Turma: {row.get('turma')}")
        else:
            print(f"   ❌ Requerimento não encontrado")
            return False
    except Exception as e:
        print(f"   ❌ Erro ao obter requerimento: {e}")
        return False

    # 3. Obter informações de drive
    print(f"\n3. Obtendo informações de drive...")
    try:
        drive_info = get_requerimento_tcc_drive_info(submission_id)
        if drive_info:
            print(f"   ✅ Informações de drive obtidas:")
            print(f"      Root: {drive_info['root']}")
            print(f"      Path: {drive_info['path']}")
        else:
            print(f"   ⚠️ Nenhuma informação de drive encontrada")
            print(f"      (Pode estar OK se não houver TccSubmission relacionado)")
    except Exception as e:
        print(f"   ❌ Erro ao obter informações de drive: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. Testar a importação da função get_tcc_folder_root_id
    print(f"\n4. Testando importação de get_tcc_folder_root_id...")
    try:
        from backend.infrastructure.google.drive import get_tcc_folder_root_id
        folder_id = get_tcc_folder_root_id()
        print(f"   ✅ Função importada e funcionando:")
        print(f"      TCC Folder ID: {folder_id}")
    except Exception as e:
        print(f"   ❌ Erro ao importar ou usar get_tcc_folder_root_id: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 60)
    print("\nO endpoint DELETE deve funcionar corretamente agora.")
    print(f"Teste deletando: DELETE /api/v1/requerimento-tcc/{submission_id}")

    return True

if __name__ == "__main__":
    success = test_delete_endpoint()
    sys.exit(0 if success else 1)
